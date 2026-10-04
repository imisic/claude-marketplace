# Recurrence Detection Algorithm

How `a-self-learner` Phase 2 turns a pile of findings into clustered patterns ready for Phase 3 proposals.

## Inputs

- `review-issues.jsonl` (current window)
- `review-issues-archive.jsonl` (optional, only read if `--deep` flag set or if window is very small)
- `feedback_fp_*.md` files from project memory: for marking clusters as False Positive

## Step 1: Parse and filter

```python
import json
from pathlib import Path
from datetime import datetime

findings = []
for line in Path(".claude/reviews/review-issues.jsonl").read_text().splitlines():
    line = line.strip()
    if not line:
        continue
    try:
        f = json.loads(line)
    except json.JSONDecodeError as e:
        print(f"MALFORMED: {line[:80]}... ({e})")
        continue
    findings.append(f)
```

Drop findings where:
- `type = "resolution"` (an outcome, not an occurrence)
- `disposition = "dismissed"` (keep the dismissal data for FP analysis, but don't cluster into recurring)
- `severity = info` (not actionable by itself)
- `dimension = other` and no explicit category

**On a v1 row (no `schema` key) those two fields do not exist, so fall back to the old heuristics:** treat `whitelisted = true` as dismissed, and treat a `FIXED:`-prefixed `message` or a `skill` ending in `-fix` as a resolution. Both heuristics are wrong somewhere, which is why v2 replaced them, so migrate the log rather than living on them: `scripts/migrate-review-log-v2.py` (dry run by default).

Excluding resolutions is not cosmetic. Fix skills log a row carrying the **same** `category` as the finding they closed, so counting both doubles every cluster and a well-fixed pattern accumulates evidence that it is chronic. Resolutions can easily be a third of a log, and a category with 11 findings and 11 fixes then reads as 22 occurrences. Since these counts are what escalate a prose rule into a fail-gating preflight check, the inflation buys checks nobody needed.

Keep the resolution rows in the log. They are what lets you spot a category that keeps coming back after being fixed, which is a different and more interesting signal than raw recurrence. Read them deliberately in Step 4; don't let them into the Step 2 counts.

## Step 2: Group by `category_hash`

```python
from collections import defaultdict

clusters = defaultdict(list)
for f in findings:
    clusters[f["category_hash"]].append(f)
```

`category_hash` is `sha256(category)[:16]` (see `review-log-schema.md`), so this is identical to grouping by `category`: one cluster per pattern class. Two different categories sharing a hash would be a sha256 collision (effectively impossible). If you ever see one category split across multiple hashes, the log predates a hash-definition change and needs a backfill: don't treat the fragments as distinct patterns.

## Step 2b: Surface near-duplicate slug families (human merge gate)

Because `category_hash` is the slug, clustering is only as good as slug hygiene, and review skills drift: the same pattern arrives as `inline-event-handler`, `inline-event-handler-in-view`, `inline-event-handler-js`. Each becomes its own cluster, and the split can push a genuinely-recurring pattern below the Step 3 thresholds (one Chronic cluster of 7 becomes one Recurring of 3 plus three ignored One-offs).

Before classifying, detect candidate merge-families and **ask the human**: never auto-merge (some near-twins are intentionally distinct, e.g. `method-over-30-lines` vs `method-over-50-lines`).

```python
import difflib
from itertools import combinations

def _toks(slug): return set(slug.split("-"))

def near_dup(a, b):
    ta, tb = _toks(a), _toks(b)
    jaccard = len(ta & tb) / len(ta | tb)
    ratio = difflib.SequenceMatcher(None, a, b).ratio()
    return (a in b or b in a) or jaccard >= 0.5 or ratio >= 0.72

# union-find over near-dup edges → connected components of slugs
slugs = sorted(clusters)                       # one slug per category_hash
parent = {s: s for s in slugs}
def find(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]; x = parent[x]
    return x
for a, b in combinations(slugs, 2):
    if near_dup(a, b):
        parent[find(a)] = find(b)

families = {}
for s in slugs:
    families.setdefault(find(s), []).append(s)
families = {root: m for root, m in families.items() if len(m) > 1}
```

For each family with >1 member, present it sorted by finding count and ask:

```
Possible slug drift: one pattern under several slugs?
  inline-event-handler-in-view   (11 findings, 2 dates)
  inline-event-handler           (5,  1 date)
  inline-event-handler-js        (1)
  inline-event-handlers          (1)
  inline-event-handlers-admin    (1)
Merge for this run? [canonical slug / n = keep separate]
```

On confirm, treat the family as **one cluster for this run's Step 3** (merge in-memory under the chosen canonical slug; sum the counts/dates/files). Don't rewrite `category` on historical findings unless you deliberately want to normalize the log: that mutates the authoritative clustering key. To make a merge *durable*, do one of: record the canonical mapping in a `slug-aliases.md` note read at the top of Step 2b, or fix the slug at source so the review skill emits the canonical form going forward. Record confirmed keep-separate decisions too, so the gate stops re-asking about intentional twins.

Thresholds (Jaccard ≥ 0.5, ratio ≥ 0.72, or substring) are tuned to catch real families without flooding: loosen to surface more, tighten if it over-suggests. Union-find chains transitively (A~B~C even when A and C aren't alike), so a family may contain a stray: in practice the gate groups `method-over-30-lines` + `method-over-50-lines` correctly but also drags in `file-over-500-lines` via the shared `over…lines` tokens. Split strays when confirming. This is a suggestion engine, not an authority: the human decides every merge.

## Merged
- `inline-event-handler-in-view` <- `inline-event-handler`, `inline-event-handler-js`, `inline-event-handlers`  (YYYY-MM-DD, confirmed by <reviewer>)

## Keep separate
- `method-over-30-lines` vs `method-over-50-lines`  (different thresholds, deliberate)
```

Thresholds (Jaccard ≥ 0.5, ratio ≥ 0.72, or substring) are tuned to catch real families without flooding; loosen to surface more, tighten if it over-suggests. Union-find chains transitively (A~B~C even when A and C aren't alike), so a family may contain a stray: in practice the gate groups `method-over-30-lines` + `method-over-50-lines` correctly but also drags in `file-over-500-lines` via the shared `over…lines` tokens. Split strays when confirming. This is a suggestion engine, not an authority: the human decides every merge.

## Step 3: Classify each cluster

For each cluster, compute:

- `count` = number of findings in the cluster
- `distinct_dates` = number of distinct `date` values
- `distinct_files` = number of distinct `file` values
- `first_seen`, `last_seen` = min / max of `date`
- `span_days` = (last_seen - first_seen).days
- `severity_mix` = count by severity
- `is_fp_feedback_present` = True if any `feedback_fp_*.md` file mentions this `category`

Classification:

```
if is_fp_feedback_present:
    cls = "False Positive"
elif count >= 5 or span_days > 30 or distinct_files >= 3:
    cls = "Chronic"
elif count >= 3 and distinct_dates >= 2:
    cls = "Recurring"
else:
    cls = "One-off"
```

Thresholds are adjustable via the skill's `--threshold N` flag (overrides the `3` for Recurring; `Chronic` uses `threshold + 2`).

## Step 4: Skip clusters already resolved

Two signals mark the same class and a cluster only has to trip one, so a miss on the first is not an answer. **On a v1 log only the `applied-learnings.md` check further down fires**, because v1 rows carry no `action` field; migrate the log with `scripts/migrate-review-log-v2.py` to get the resolution-row path below.

On a v2 log, read the cluster's own resolution rows first, since they carry the signal that used to live only in `applied-learnings.md`. A resolution with `action: "covered"` names the check or rule that was supposed to end the pattern, in `covered_by`. **Any finding in that cluster dated after a `covered` resolution is a re-emergence**, and re-emergence after a defense exists is the strongest evidence the log produces: it says the defense does not work, not that the pattern is popular. The typical case is a prose rule with no mechanical check behind it, broadened or added, followed by more findings of the same slug within days. Flag these RE-EMERGENT here and let Phase 3 escalate them to a deterministic check.

Then check `applied-learnings.md` and `rejected-proposals.md`:

- If cluster_id already in `applied-learnings.md` AND no new findings since the applied date → skip (already addressed, and hasn't re-emerged).
- If cluster_id already in `applied-learnings.md` AND new findings since → **re-surface with a "RE-EMERGENT" flag**. The prior fix didn't hold. Investigate.
- If cluster_id in `rejected-proposals.md` AND current count ≤ re-proposal threshold stored there → skip.
- If cluster_id in `rejected-proposals.md` AND current count exceeds the threshold → resurface for a new decision.

## Step 5: Rank for presentation

Order clusters for Phase 3 presentation:

1. **RE-EMERGENT** clusters first: a prior fix failed; this is highest value to investigate.
2. **Chronic** clusters (broad, long-standing patterns).
3. **Recurring** clusters (narrower, newer).
4. **False Positive** clusters: whitelist proposals.

Tier sets presentation order only. It does not pick the target: that is Phase 3a's checkability test in `SKILL.md`, which proposes a check plus rule pair for anything mechanically checkable whatever its tier, and a rule alone only for judgement patterns.

Within each tier, sort by `count` descending. Present top-N per tier (default N = 5; user can override).

## Step 6: Emit `recurring-patterns.md`

See `review-log-schema.md` for the output format. Include in each section:

- cluster_id, pattern name, dimension
- classification and counts
- first/last seen dates
- distinct files affected
- representative findings (3-5 example lines with file:line and severity)
- recommended action (preflight vs rule vs whitelist)
- target skill (`a-review-optimizer` vs `a-rules-optimizer`)

## Edge cases

- **Cluster with one dominant file.** If 10 findings are all in `src/legacy/*.py`, the fix might be "deprecate that module" rather than "add a rule." Flag these as `LOCALIZED`: they may deserve a different proposal (code fix vs rule) or a path-scoped rule.
- **Cluster that spans multiple skills.** If `skill` varies within a cluster (e.g. both `example-review` and an older `example-review-legacy` captured it), note it: the fix might need to apply to both review skills.
- **Runaway cluster from a single bad run.** If all findings share the same `run_id` and the cluster has no findings from other runs, treat as One-off regardless of count. A single bad PR scan that flagged 30 things isn't a recurring pattern.
- **Empty project history.** Zero findings → skill reports "no history, cannot learn" and exits cleanly. Not an error.

## Calibration

These thresholds (3 for Recurring, 5 for Chronic, 30 days for span, 3 files) are defaults. For a new capture convention, findings accumulate slowly: thresholds may need lowering in the first few months. Users can pass `--threshold 2` to see near-patterns early.

Thresholds should NOT be tuned per-project in the skill itself. Pass them as arguments. Keeps behavior predictable.
