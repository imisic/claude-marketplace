#!/usr/bin/env bash
# publish_gate.sh: every lexical leak layer in one run, before anything goes public.
#
#   publish_gate.sh --repo DIR --ref REF --identity EMAIL [--also PATH]... [--no-private]
#
# REF is what will actually be pushed, so the tree at REF and every blob and
# commit message reachable from it get scanned. --also adds shipped artifacts
# that are not that tree: an unzipped download bundle, an export of site copy.
#
# Why one script: each layer catches something the others cannot. The tree scan
# misses old commits, the history scan misses a bundle built from somewhere
# else, and neither sees a commit made under the wrong email. Layers that have
# to be remembered get skipped.
#
# The contextual pass (references/patterns.md, "manual review") still needs a
# reader. This script only makes the mechanical part impossible to forget.
#
# Exit 0 clean, 1 findings, 2 bad invocation.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
SKILL="$(dirname "$HERE")"
PRIVATE="${LEAK_SCAN_PRIVATE:-$HOME/.config/leak-scan/private-terms}"

repo="" ref="" identity="" no_private=0
also=()
while [ $# -gt 0 ]; do
  case "$1" in
    --repo) repo="$2"; shift 2 ;;
    --ref) ref="$2"; shift 2 ;;
    --identity) identity="$2"; shift 2 ;;
    --also) also+=("$2"); shift 2 ;;
    --no-private) no_private=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done
[ -n "$repo" ] && [ -n "$ref" ] && [ -n "$identity" ] || {
  echo "usage: $0 --repo DIR --ref REF --identity EMAIL [--also PATH]... [--no-private]" >&2; exit 2; }
git -C "$repo" rev-parse --verify -q "$ref^{commit}" >/dev/null || { echo "no such ref: $ref" >&2; exit 2; }

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
fail=0
step() { printf '\n== %s\n' "$1"; }
bad() { echo "FAIL: $1"; fail=1; }

step "1/6 private layer"
if [ -s "$PRIVATE" ]; then
  echo "$(grep -cvE '^\s*(#|$)' "$PRIVATE") rule(s) in $PRIVATE"
elif [ "$no_private" = 1 ]; then
  echo "WARNING: no private layer; only generic shapes will be caught"
else
  # Without your own names and terms the scan passes everything that matters.
  echo "no private layer at $PRIVATE; create one (see SKILL.md) or pass --no-private" >&2
  exit 2
fi

scan() {  # scan LABEL PATH
  if python3 "$HERE/leak_scan.py" "$2" --severity medium > "$work/scan.txt" 2>&1; then
    echo "$1: clean"
  else
    grep -A1 -E '^\[' "$work/scan.txt" | grep -v '^--' | sed "s|$work/||"
    bad "$1: findings above"
  fi
}

step "2/6 tree at $ref"
mkdir -p "$work/tree"
git -C "$repo" archive "$ref" | tar -x -C "$work/tree"
scan "tree" "$work/tree"
for p in "${also[@]}"; do scan "also $(basename "$p")" "$p"; done

step "3/6 history reachable from $ref"
# One extract of every text blob, rather than `git log -S` per rule: with a
# generated layer of thousands of names, a per-term loop never finishes.
: > "$work/history.txt"
git -C "$repo" rev-list --objects "$ref" | awk '{print $1}' | sort -u | while read -r o; do
  [ "$(git -C "$repo" cat-file -t "$o")" = blob ] || continue
  git -C "$repo" cat-file -p "$o" | grep -qIm1 . && git -C "$repo" cat-file -p "$o" >> "$work/history.txt" || true
done
git -C "$repo" log "$ref" --format='%B%n%an %ae%n%cn %ce' >> "$work/history.txt"
echo "$(git -C "$repo" rev-list --count "$ref") commit(s), $(wc -c < "$work/history.txt") bytes"
scan "history" "$work/history.txt"

step "4/6 commit identities"
others="$(git -C "$repo" log "$ref" --format='%ae%n%ce' | sort -u | grep -vxF "$identity" || true)"
if [ -n "$others" ]; then bad "identities other than $identity: $(echo "$others" | tr '\n' ' ')"; else echo "all commits by $identity"; fi

step "5/6 gitleaks"
if command -v docker >/dev/null && docker image inspect ghcr.io/gitleaks/gitleaks:latest >/dev/null 2>&1; then
  for target in tree history.txt; do
    if docker run --rm --network none -u "$(id -u)" -v "$work:/w:ro" -v "$SKILL/references/gitleaks.toml:/c.toml:ro" \
        ghcr.io/gitleaks/gitleaks:latest dir "/w/$target" -c /c.toml --no-banner --redact >"$work/gl.txt" 2>&1; then
      echo "$target: clean"
    else
      grep -E 'RuleID|File|Line:' "$work/gl.txt" | sed 's|/w/||'; bad "gitleaks: $target"
    fi
  done
elif command -v gitleaks >/dev/null; then
  for target in tree history.txt; do
    gitleaks dir "$work/$target" -c "$SKILL/references/gitleaks.toml" --no-banner --redact >"$work/gl.txt" 2>&1 \
      && echo "$target: clean" || { grep -E 'RuleID|File|Line:' "$work/gl.txt"; bad "gitleaks: $target"; }
  done
else
  echo "SKIPPED: install gitleaks, or docker pull ghcr.io/gitleaks/gitleaks:latest"
  fail=1
fi

step "6/6 binaries for a human to open"
find "$work/tree" "${also[@]}" -type f 2>/dev/null | while read -r f; do
  grep -qI . "$f" 2>/dev/null || [ ! -s "$f" ] || echo "  $f" | sed "s|$work/tree/||"
done

echo
if [ "$fail" = 0 ]; then
  echo "GATE: lexical, history, identity and gitleaks layers clean. The contextual pass is still yours."
else
  echo "GATE: FAILED"
fi
exit "$fail"
