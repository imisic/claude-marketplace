#!/bin/bash
# Regression test for seed-defects.py. Builds a throwaway repo under mktemp -d, asserts every
# plant guard refuses with exit 2 and leaves the tree byte-identical, then runs a full
# plant, verify, score, restore cycle. Prints FAILED and exits 1 on any broken assertion, so a
# guard that quietly stops working breaks this script instead of reading as a pass. Touches
# nothing outside the two temp dirs. Run it after editing the harness.
set -u
H="$(cd "$(dirname "$0")/../scripts" && pwd)/seed-defects.py"
R=$(mktemp -d)
OUT=$(mktemp -d)   # deliberately outside the repo: the escape target for the traversal case
trap 'rm -rf "$R" "$OUT"' EXIT
FAIL=0

fail() { FAIL=$((FAIL + 1)); echo "   FAIL: $*"; }
ok() { echo "   ok: $*"; }
commits() { git -C "$R" rev-list --count HEAD; }

# A guard passes only if it exits 2, says REFUSED, and adds no commit. The commit check is the
# "writes nothing" half, which nothing tested before.
expect_refusal() {
  local label=$1; shift
  local before after out rc bad=0
  before=$(commits)
  out=$(python3 "$H" "$@" 2>&1); rc=$?
  after=$(commits)
  echo "$label"
  [ "$rc" -eq 2 ] || { fail "exit $rc, want 2"; bad=1; }
  grep -q REFUSED <<<"$out" || { fail "no REFUSED in output: $(head -1 <<<"$out")"; bad=1; }
  [ "$before" = "$after" ] || { fail "commit count went $before to $after"; bad=1; }
  [ "$bad" -eq 0 ] && ok "refused, exit 2, still $after commit(s)"
}

expect_eq() {
  local label=$1 got=$2 want=$3
  if [ "$got" = "$want" ]; then ok "$label = $want"; else fail "$label = $got, want $want"; fi
}

mkdir -p "$R/app" "$R/pkg"
printf '<?php\n\nfunction existingHelper(string $s): string\n{\n    return trim($s);\n}\n' > "$R/app/Helpers.php"
printf '"""Existing."""\n\n\ndef existing_helper(v: str) -> str:\n    return v.strip()\n' > "$R/pkg/service.py"
printf '<?php\n\nfunction outsideVictim(): void\n{\n}\n' > "$OUT/victim.php"
VICTIM_BEFORE=$(md5sum "$OUT/victim.php" | cut -d' ' -f1)
git -C "$R" init -q -b main .
git -C "$R" config user.email t@t
git -C "$R" config user.name t
git -C "$R" add -A
git -C "$R" commit -qm init

expect_refusal "1) plant on main (protected):" --plant --repo "$R" --ids php-01 --target app/Helpers.php

git -C "$R" switch -qc benchmark/p
echo "x" >> "$R/app/Helpers.php"
expect_refusal "2) plant on scratch branch, dirty tree:" --plant --repo "$R" --ids php-01 --target app/Helpers.php
git -C "$R" checkout -q -- app/Helpers.php

git -C "$R" switch -qc feature/x
expect_refusal "3) plant on a plain branch, clean tree:" --plant --repo "$R" --ids php-01 --target app/Helpers.php

git -C "$R" checkout -q --detach
expect_refusal "4) plant on detached HEAD:" --plant --repo "$R" --ids php-01 --target app/Helpers.php
git -C "$R" switch -q benchmark/p

# The traversal case: an absolute --target whose .. climbs out of the repo. relative_to is
# lexical, so this used to pass containment and the file was written before git add noticed.
# Assert the file outside is untouched, not just that the exit code is 2.
expect_refusal "5) plant into an absolute --target that escapes the repo:" \
  --plant --repo "$R" --ids php-01 --target "$R/../$(basename "$OUT")/victim.php"
expect_eq "victim md5 outside the repo" "$(md5sum "$OUT/victim.php" | cut -d' ' -f1)" "$VICTIM_BEFORE"
expect_eq "state file after refusal" "$([ -e "$R/.git/seed-defects-state.json" ] && echo present || echo absent)" "absent"

echo "6) plant on the scratch branch (should succeed):"
python3 "$H" --plant --repo "$R" --ids php-01,py-01,py-02 --target app/Helpers.php pkg/service.py
expect_eq "plant exit" "$?" "0"
expect_eq "commits after plant" "$(commits)" "4"

expect_refusal "7) plant again over an existing state file:" --plant --repo "$R" --ids php-01 --target app/Helpers.php

echo "8) verify:"
python3 "$H" --verify --repo "$R" | tail -1
python3 "$H" --verify --repo "$R" >/dev/null
expect_eq "verify exit" "$?" "0"

python3 - "$R" <<'PY'
import json, sys
st = json.load(open(f"{sys.argv[1]}/.git/seed-defects-state.json"))
by_id = {e["id"]: e for e in st["planted"]}
php, py2 = by_id["php-01"], by_id["py-02"]
with open(f"{sys.argv[1]}/hit.jsonl", "w") as fh:
    fh.write(json.dumps({"file": php["file"], "line": php["defect_line"],
                         "category": php["category"]}) + "\n")
# py-02's own first line. Before the window fix this scored as a HIT for py-01, whose
# unclamped window reached past the separator into py-02's block.
with open(f"{sys.argv[1]}/neighbour.jsonl", "w") as fh:
    fh.write(json.dumps({"file": py2["file"], "line": py2["start_line"],
                         "category": py2["category"]}) + "\n")
PY

echo "9) score one true hit out of three planted:"
SCORE=$(python3 "$H" --score "$R/hit.jsonl" --repo "$R")
grep -E '^HIT|^MISS|^recall|^precision' <<<"$SCORE"
if grep -q "^HIT     php-01" <<<"$SCORE"; then ok "php-01 scored HIT"; else fail "php-01 not scored HIT"; fi
if grep -qE '^recall +1/3' <<<"$SCORE"; then ok "recall 1/3"; else fail "recall line is not 1/3"; fi

echo "10) a finding on py-02's own line is not credited to py-01:"
NEIGH=$(python3 "$H" --score "$R/neighbour.jsonl" --repo "$R" --match file-line)
grep -E '^HIT' <<<"$NEIGH"
if grep -q "^HIT     py-02" <<<"$NEIGH"; then ok "credited to py-02"; else fail "py-02 did not get its own finding"; fi
if grep -q "^HIT     py-01" <<<"$NEIGH"; then fail "py-01 stole the neighbour's finding"; else ok "py-01 stayed a MISS"; fi

echo "11) score against a path that does not exist:"
MISSING=$(python3 "$H" --score "$OUT/nope.jsonl" --repo "$R" 2>&1)
expect_eq "missing findings file exit" "$?" "2"
if grep -q Traceback <<<"$MISSING"; then fail "traceback instead of a clean refusal"; else ok "clean refusal, no traceback"; fi

rm -f "$R/hit.jsonl" "$R/neighbour.jsonl"
echo "12) restore:"
python3 "$H" --restore --repo "$R"
expect_eq "restore exit" "$?" "0"
expect_eq "commits after restore" "$(commits)" "1"
expect_eq "tree after restore" "$(git -C "$R" status --porcelain | wc -l)" "0"
expect_eq "state file after restore" "$([ -e "$R/.git/seed-defects-state.json" ] && echo present || echo absent)" "absent"

echo
if [ "$FAIL" -eq 0 ]; then
  echo "PASSED: every guard and scoring assertion held."
  exit 0
fi
echo "FAILED: $FAIL assertion(s)."
exit 1
