#!/usr/bin/env bash
# Compute the review scope and the numbers the report's Coverage line needs.
#
# Every project review skill calls this instead of carrying its own shell arithmetic, so a scope bug fixed here is fixed everywhere and two projects never disagree about what "since the last review" means. Mode resolution mirrors the engine's scope section, in this order:
#
#   --base <ref>          range              an explicit base always wins
#   uncommitted changes   working-tree       the state the user is looking at, untracked (non-ignored) files included
#   capture log present   since-last-review  newest `date` in .claude/reviews/review-issues.jsonl names when the last run looked; the newest commit before it is the base
#   no capture log        since-last-review  last 24 hours of commits, said so in `note`
#   nothing in range      empty
#
# --full reports mode `full` but still resolves the recent half above, because a whole-tree run still reads the recent diff line by line and needs to know which files that is.
#
# Read-only. Exit 0 on success, 2 when not inside a git repo or on a bad argument, with one line on stderr.
#
# Usage: review-scope.sh [--base <ref>] [--full] [--json]
set -euo pipefail

LOG=.claude/reviews/review-issues.jsonl

base_arg=""
full=0
json=0
while [ $# -gt 0 ]; do
  case "$1" in
    --base) [ $# -ge 2 ] || { echo "review-scope: --base needs a ref" >&2; exit 2; }; base_arg=$2; shift 2 ;;
    --full) full=1; shift ;;
    --json) json=1; shift ;;
    -h|--help) sed -n '2,17p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) echo "review-scope: unknown argument: $1" >&2; exit 2 ;;
  esac
done

# Resolve from the repo root so the capture log path and the file list are root-relative no matter where the caller stands.
top=$(git rev-parse --show-toplevel 2>/dev/null) || { echo "review-scope: not inside a git repository" >&2; exit 2; }
cd "$top"
git rev-parse --verify -q HEAD >/dev/null || { echo "review-scope: repository has no commits yet" >&2; exit 2; }

mode=""
base=""
base_date=""
note=""
range_mode="range"   # how `git diff` is invoked: range (<base>...HEAD) or worktree (HEAD)

# Newest capture date. Blank or malformed rows and rows without a date are skipped rather than fatal, same policy as review_loop_health.py: one bad line must not silently turn every review into a 24-hour one.
last_review_date() {
  [ -f "$LOG" ] || return 0
  python3 - "$LOG" <<'PY'
import json, sys
newest = ""
for line in open(sys.argv[1], encoding="utf-8", errors="replace"):
    line = line.strip()
    if not line:
        continue
    try:
        d = json.loads(line).get("date")
    except (ValueError, AttributeError):
        continue
    if isinstance(d, str) and d > newest:
        newest = d
print(newest)
PY
}

resolve_since_last_review() {
  mode="since-last-review"
  local since
  since=$(last_review_date)
  if [ -n "$since" ]; then
    base_date=$since
    # git fills a bare date with the current clock time, so `--before=2026-09-30` would move with the hour of day. Pin it to midnight: deterministic, and the review day's own commits get re-read rather than skipped.
    case "$since" in [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]) since="$since 00:00" ;; esac
  else
    since="24 hours ago"
    note="no capture log at $LOG, using the last 24 hours of commits"
  fi
  base=$(git rev-list -1 --before="$since" HEAD)
  if [ -z "$base" ]; then
    # Every commit is newer than the date, so the whole history is in scope. The root commit is the oldest base `<base>...HEAD` accepts; its own files are the one thing this leaves out, so say so.
    base=$(git rev-list --max-parents=0 HEAD | tail -1)
    note="${note:+$note; }no commit older than $since, base is the root commit and its own files are not in the diff"
  fi
}

# Untracked, non-ignored files. An untracked nested repository is listed as `dir/`: it is not a file of this repo, and `cat` on it used to abort the whole run with exit 123.
untracked_files() { git ls-files --others --exclude-standard -z | { grep -zv '/$' || true; }; }

if [ -n "$base_arg" ]; then
  base=$(git rev-parse --verify -q "${base_arg}^{commit}") || { echo "review-scope: --base $base_arg is not a commit" >&2; exit 2; }
  mode="range"
elif [ -n "$(git diff --name-only HEAD)" ] || [ -n "$(untracked_files | tr -d '\0')" ]; then
  # Untracked files count as changes: `git diff HEAD` leaves out a brand-new file, so a review of new code used to come back `empty`. Ignored files stay out (--exclude-standard), and nothing is staged.
  mode="working-tree"
  base="HEAD"
  range_mode="worktree"
else
  resolve_since_last_review
fi

if [ "$range_mode" = worktree ]; then
  mapfile -d '' files < <(git diff --name-only -z HEAD)
  mapfile -d '' untracked < <(untracked_files)
  diff_bytes=$(git diff HEAD | wc -c)
  if [ ${#untracked[@]} -gt 0 ]; then
    files+=("${untracked[@]}")
    # A new file's diff is its whole content, so its size stands in for diff bytes (minus a few header lines, close enough for the Coverage line).
    diff_bytes=$((diff_bytes + $(printf '%s\0' "${untracked[@]}" | xargs -0 cat -- | wc -c)))
    note="${note:+$note; }${#untracked[@]} untracked file(s) included, not staged"
  fi
else
  mapfile -d '' files < <(git diff --name-only -z "$base"...HEAD)
  diff_bytes=$(git diff "$base"...HEAD | wc -c)
fi

if [ "$full" = 1 ]; then
  note="${note:+$note; }recent half is $mode from ${base_date:-$base}"
  mode="full"
elif [ ${#files[@]} -eq 0 ] && [ "$mode" = since-last-review ]; then
  mode="empty"
fi

if [ "$json" = 1 ]; then
  # Fields ride on env vars and the file list on stdin, NUL-separated, so a path with a quote or a newline cannot break the JSON.
  printf '%s\0' "${files[@]+"${files[@]}"}" | MODE=$mode BASE=$base BASE_DATE=$base_date DIFF_BYTES=$diff_bytes NOTE=$note python3 -c '
import json, os, sys
raw = sys.stdin.buffer.read().decode("utf-8", "surrogateescape")
files = [f for f in raw.split("\0") if f]
print(json.dumps({
    "mode": os.environ["MODE"],
    "base": os.environ["BASE"],
    "base_date": os.environ["BASE_DATE"] or None,
    "files": files,
    "file_count": len(files),
    "diff_bytes": int(os.environ["DIFF_BYTES"]),
    "note": os.environ["NOTE"] or None,
}, indent=2, ensure_ascii=False))'
else
  echo "mode: $mode"
  echo "base: $base"
  echo "base_date: $base_date"
  echo "file_count: ${#files[@]}"
  echo "diff_bytes: $diff_bytes"
  echo "note: $note"
  echo "files:"
  for f in "${files[@]+"${files[@]}"}"; do echo "  $f"; done
fi
