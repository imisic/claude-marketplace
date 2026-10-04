#!/usr/bin/env bash
# capture-finding.sh: append one row to .claude/reviews/review-issues.jsonl
#
# Helper for project *-review and *-fix skills. Call once per finding, and once
# per resolution. Safe to call from any skill across any project.
#
# Writes schema 2. See review-log-schema.md for the field reference. A v1 call
# (no --schema-affecting flags) still works and still produces a valid row: the
# only difference is that v2 rows carry "schema":2, "type" and "disposition".
#
# FINDING MODE (default), one confirmed or dismissed finding:
#   bash capture-finding.sh \
#       --project myapp \
#       --skill myapp-review \
#       --run-id "$RUN_ID" \
#       --dimension security \
#       --severity high \
#       --category subprocess-without-timeout \
#       --file src/core/backup_engine.py \
#       --line 142 \
#       --message "subprocess.run() without timeout=" \
#       [--fix "add timeout=30"] \
#       [--agent security] \
#       [--check-id SUB-01] \
#       [--evidence "read backup_engine.py:140-145, no timeout kwarg"] \
#       [--dismissed "framework invokes it, see context.md"] \
#       [--new-slug]   # category deliberately new, skip the vocabulary warning
#
# RESOLUTION MODE (--action), a later statement about an earlier finding:
#   bash capture-finding.sh \
#       --action fixed \
#       --resolves 9a2c4f1e8b3d7a06 \
#       --project myapp --skill myapp-fix --run-id "$RUN_ID" \
#       --dimension security --severity high \
#       --category subprocess-without-timeout \
#       --file src/core/backup_engine.py --line 142 \
#       --message "added timeout=30" \
#       [--fix-commit a1b2c3d] \
#       [--covered-by SUB-01]
#
# --resolves takes the finding_id printed by the capture that recorded the
# finding. Pass it whenever you have it: without it, a-self-learner falls back
# to pairing on (category, file), which mispairs whenever one file holds two
# findings of the same category. The helper prints the finding_id of every row
# it writes to stdout for exactly this reason.
#
# The helper creates .claude/reviews/ if missing, computes category_hash,
# assigns a finding_id, and appends one JSON line. No other side effects.

set -euo pipefail

# Defaults
PROJECT=""; SKILL=""; RUN_ID=""; DIMENSION=""; SEVERITY=""
CATEGORY=""; FILE=""; LINE="0"; MESSAGE=""
FIX=""; AGENT=""; CHECK_ID=""; WHITELISTED="false"; EVIDENCE=""
ACTION=""; RESOLVES=""; FIX_COMMIT=""; COVERED_BY=""; NOTE=""; NEW_SLUG="false"
DISPOSITION=""; DISMISS_REASON=""

while [ $# -gt 0 ]; do
    case "$1" in
        --project)     PROJECT="$2"; shift 2 ;;
        --skill)       SKILL="$2"; shift 2 ;;
        --run-id)      RUN_ID="$2"; shift 2 ;;
        --dimension)   DIMENSION="$2"; shift 2 ;;
        --severity)    SEVERITY="$2"; shift 2 ;;
        --category)    CATEGORY="$2"; shift 2 ;;
        --file)        FILE="$2"; shift 2 ;;
        --line)        LINE="$2"; shift 2 ;;
        --message)     MESSAGE="$2"; shift 2 ;;
        --fix)         FIX="$2"; shift 2 ;;
        --agent)       AGENT="$2"; shift 2 ;;
        --check-id)    CHECK_ID="$2"; shift 2 ;;
        --evidence)    EVIDENCE="$2"; shift 2 ;;
        # A dismissed finding is knowledge, so it is captured, not dropped. The
        # reason is required because "dismissed" with no reason is the state the
        # whitelisted flag was already in, and that flag taught nobody anything.
        --dismissed)   DISPOSITION="dismissed"; DISMISS_REASON="$2"; shift 2 ;;
        # Deprecated spelling of --dismissed, kept so v1 callers keep working.
        --whitelisted) WHITELISTED="true"; DISPOSITION="dismissed"; shift ;;
        --new-slug)    NEW_SLUG="true"; shift ;;
        --action)      ACTION="$2"; shift 2 ;;
        --resolves)    RESOLVES="$2"; shift 2 ;;
        --fix-commit)  FIX_COMMIT="$2"; shift 2 ;;
        --covered-by)  COVERED_BY="$2"; shift 2 ;;
        --note)        NOTE="$2"; shift 2 ;;
        *)             echo "Unknown arg: $1" >&2; exit 2 ;;
    esac
done

# Required-field check. Both row types need the same identifying fields, because
# a resolution row must carry enough of its finding's identity to pair on
# (category, file) when --resolves is absent.
for v in PROJECT SKILL RUN_ID DIMENSION SEVERITY CATEGORY FILE MESSAGE; do
    if [ -z "${!v}" ]; then
        echo "capture-finding.sh: missing required --${v,,}" >&2
        exit 2
    fi
done

if [ -n "$ACTION" ]; then
    ROW_TYPE="resolution"
    case "$ACTION" in
        fixed|dismissed|covered|wont-fix) ;;
        *) echo "capture-finding.sh: --action must be fixed|dismissed|covered|wont-fix" >&2; exit 2 ;;
    esac
    # 'covered' is the action that changes how the loop reads later findings, so
    # it has to say what covers it or it is indistinguishable from 'fixed'.
    if [ "$ACTION" = "covered" ] && [ -z "$COVERED_BY" ]; then
        echo "capture-finding.sh: --action covered requires --covered-by (check ID or rule file)" >&2
        exit 2
    fi
else
    ROW_TYPE="finding"
    [ -z "$DISPOSITION" ] && DISPOSITION="confirmed"
fi

DATE=$(date -u +%Y-%m-%d)
REVIEWS_DIR=".claude/reviews"
LOG="$REVIEWS_DIR/review-issues.jsonl"
mkdir -p "$REVIEWS_DIR"

# Slug vocabulary check.
#
# Clustering is by slug alone, so a-self-learner only ever sees a pattern recur if
# the next run reaches for the SAME string. That makes the vocabulary file
# load-bearing, and it drifts silently: a review run that coins new slugs and never
# writes them back means each of those patterns gets re-coined differently next
# time and counted as new forever.
#
# This never blocks. A genuinely new pattern needs a new slug, and refusing it
# mid-review would cost the finding. It warns, suggests near-matches (drift is what
# this is really for: 'cross-feature-imports' vs 'cross-feature-import'), and records
# the slug so it cannot be lost. Pass --new-slug when the new slug is deliberate.
#
# No vocabulary file means no check, so a project without one is unaffected.
VOCAB=".claude/skills/${SKILL}/references/capture-slugs.md"
if [ -f "$VOCAB" ] && [ "$NEW_SLUG" = "false" ]; then
    python3 - "$VOCAB" "$CATEGORY" "$REVIEWS_DIR/unknown-slugs.txt" "$SKILL" <<'PY' || true
import difflib, re, sys, pathlib
vocab, category, sidecar, skill = sys.argv[1:]
# Read the slug from ANY column of a table row, not just the first. Vocabulary
# tables come in both column orders (| Slug | Pattern | and | Pattern | Slug |),
# and a first-column-only regex silently returns zero slugs on the second, which
# makes the vocabulary file read as present while checking nothing.
known = [s for line in pathlib.Path(vocab).read_text().splitlines() if line.lstrip().startswith('|')
         for s in re.findall(r'`([a-z0-9][a-z0-9-]{2,})`', line)]
if known and category not in known:
    near = difflib.get_close_matches(category, known, n=3, cutoff=0.6)
    print(f"capture-finding.sh: '{category}' is not in {vocab}", file=sys.stderr)
    if near:
        print(f"  did you mean: {', '.join(near)}", file=sys.stderr)
        print("  a near-miss is slug drift, and it splits one pattern into two clusters.", file=sys.stderr)
    print(f"  if it is genuinely new, add a row to {vocab} and re-run with --new-slug.", file=sys.stderr)
    with open(sidecar, "a") as fh:
        fh.write(f"{category}\t{skill}\n")
PY
fi

# category_hash groups findings into pattern classes for a-self-learner.
# The clustering key is the CATEGORY slug alone (lowercased), NOT the free-text
# message (which carries method names / paths / identifiers that fragment one
# pattern into dozens of hashes), and NOT the dimension (the same pattern is
# tagged 'architecture' by one agent and 'quality' by another, which would
# re-split it). Slug hygiene is load-bearing: keep slugs specific enough that one
# slug == one pattern, and consistent enough that one pattern == one slug (no
# 'inline-event-handler' vs 'inline-event-handler-in-view' drift).
# See review-log-schema.md "category_hash computation".
HASH=$(printf '%s' "$CATEGORY" | tr '[:upper:]' '[:lower:]' | sha256sum | cut -c1-16)

# Simple UUID-ish id, 16 hex chars from urandom
FINDING_ID=$(head -c 8 /dev/urandom | od -An -tx1 | tr -d ' \n')

# Build JSON object. python3 handles escaping cleanly.
python3 - "$DATE" "$PROJECT" "$SKILL" "$RUN_ID" "$FINDING_ID" "$DIMENSION" \
               "$SEVERITY" "$CATEGORY" "$FILE" "$LINE" "$MESSAGE" \
               "$FIX" "$AGENT" "$CHECK_ID" "$HASH" "$WHITELISTED" "$EVIDENCE" \
               "$ROW_TYPE" "$DISPOSITION" "$DISMISS_REASON" "$ACTION" "$RESOLVES" \
               "$FIX_COMMIT" "$COVERED_BY" "$NOTE" "$LOG" <<'PY'
import json, sys
(date, project, skill, run_id, finding_id, dimension, severity, category,
 file_, line, message, fix, agent, check_id, category_hash, whitelisted, evidence,
 row_type, disposition, dismiss_reason, action, resolves,
 fix_commit, covered_by, note, log) = sys.argv[1:]

rec = {
    "schema": 2, "type": row_type,
    "date": date, "project": project, "skill": skill, "run_id": run_id,
    "finding_id": finding_id, "dimension": dimension, "severity": severity,
    "category": category, "file": file_, "line": int(line or 0),
    "message": message, "category_hash": category_hash,
}

if row_type == "finding":
    rec["disposition"] = disposition
    # whitelisted is retained only so v1 readers keep parsing; disposition is
    # the field to read. See review-log-schema.md "Schema versions".
    rec["whitelisted"] = whitelisted == "true" or disposition == "dismissed"
    if dismiss_reason:
        rec["dismiss_reason"] = dismiss_reason
else:
    rec["action"] = action
    if resolves:    rec["resolves"] = resolves
    if fix_commit:  rec["fix_commit"] = fix_commit
    if covered_by:  rec["covered_by"] = covered_by
    if note:        rec["note"] = note

if fix:      rec["fix_proposed"] = fix
if agent:    rec["agent"] = agent
if check_id: rec["check_id"] = check_id
if evidence: rec["evidence"] = evidence

with open(log, "a") as f:
    f.write(json.dumps(rec, separators=(",", ":")) + "\n")
PY

# Printed so a fix skill can pass it back as --resolves later. Callers that do
# not need it can ignore stdout.
echo "$FINDING_ID"
