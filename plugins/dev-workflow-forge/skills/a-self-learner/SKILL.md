---
name: a-self-learner
description: Turn recurring review findings into proposed rule and skill updates.
disable-model-invocation: true
---

# Self-Learner: Review → Rule/Skill Feedback Loop

Closes the loop between review skills and rule/skill files. When a project review catches the same class of issue repeatedly, this skill proposes a preventive update (a new rule, a new preflight check, or a whitelist entry) and hands it off to `a-rules-optimizer` or `a-review-optimizer` for application.

**Input:** optional flags
- `--dry-run` (default): analyze and propose, never write
- `--apply`: after each proposal, ask user, apply on approval
- `--since YYYY-MM-DD`: only consider findings from this date forward
- `--threshold N`: override recurrence threshold (default 3 for recurring, 5 for chronic)

If the project has no `.claude/reviews/` directory yet, the skill reports "no history to learn from" and offers to scaffold the convention (see `references/review-log-schema.md`).

---

## Core Principles

**Propose, never silently write.** Every rule/skill change must be shown to the user as a diff with rationale, then applied only after explicit approval. Propose only; never auto-apply and never auto-commit. A proposal workflow is not commit authorization, whatever your project or global commit rules say.

**Delegate writes to the other optimizers.** This skill never edits rule files or review SKILL.md directly. It generates a structured proposal and invokes `a-rules-optimizer` (for rule writes) or `a-review-optimizer` (for preflight/agent writes). Keeps each skill's scope tight.

**Evidence > opinion.** A recurrence claim needs ≥ N findings of the same category across distinct dates. "Feels recurring" is not good enough; the cluster must survive the grouping algorithm in `references/recurrence-detection.md`.

**Record rejections.** Proposals the user declines get logged to `rejected-proposals.md` with the reason. Next run shouldn't re-raise the same rejection: only surface if new evidence appears (e.g., the issue recurred another 5 times since rejection).

**Per-project scope.** Each project owns its own `.claude/reviews/` directory. The skill does not cross-pollinate learnings between projects (that's a future extension; for now, deliberate isolation keeps project conventions separate).

---

## Phase 1: Ingest

Read the signals. The skill needs data before it can cluster anything.

### 1a: Review log

```bash
test -f .claude/reviews/review-issues.jsonl && wc -l .claude/reviews/review-issues.jsonl
test -f .claude/reviews/review-issues-archive.jsonl && wc -l .claude/reviews/review-issues-archive.jsonl
```

If neither exists, this project hasn't been capturing findings yet. Stop here and report:

> No review history found at `.claude/reviews/review-issues.jsonl`. To enable self-learning, add capture calls to this project's `*-review` skill (see `references/review-log-schema.md` for the format and `references/capture-finding.sh` for the helper). Until then, there's nothing for this skill to learn from.

**Optionally, offer to scaffold the convention** so the user doesn't have to wire it by hand. If they accept, this is the one thing `a-self-learner` writes directly (inert plumbing, not a rule/skill change; still show what lands and get an explicit yes first):

1. **Drop the helper.** Copy `references/capture-finding.sh` to `.claude/scripts/capture-finding.sh` and `chmod +x` it. It creates `.claude/reviews/` on first call, computes `category_hash`, and appends one JSON line per finding.
2. **Seed the ledgers.** Create `.claude/reviews/` with empty `applied-learnings.md` and `rejected-proposals.md` (just their `#` header lines from `references/review-log-schema.md`). The `review-issues.jsonl` and `review-issues-archive.jsonl` files appear on the first capture and first archive respectively; don't pre-create them.
3. **Git posture.** These files are meant to be tracked per-project (they document how defenses evolved). Do NOT gitignore them.
4. **Wire the capture calls (delegate, don't hand-edit).** The review skill's SKILL.md must call `capture-finding.sh` once per confirmed finding. Editing that review skill is `a-review-optimizer`'s job, not this skill's. Emit a proposal for `a-review-optimizer`: "add a capture-finding.sh call per confirmed finding, passing `--project/--skill/--run-id/--dimension/--severity/--category/--file/--line/--message`; slug the `--category` as one-pattern-one-slug (see `references/review-log-schema.md` slug hygiene)." Route it through the normal Phase 4 approval gate. If no `*-review` skill exists yet, tell the user to create one (via `a-review-optimizer`) first, since capture has nothing to hook into otherwise.

Either way, stop for this run: even scaffolded, the log is empty until the next review populates it. Re-run after findings accumulate.

If the file exists, read every line as JSON. Drop malformed lines with a warning (don't silently discard, print them so the user can fix the capture).

**A line count is not a finding count.** Check `schema` on the first row and read accordingly:

- **Schema 2 (current).** Count rows where `type` is `finding` and `disposition` is `confirmed`. Resolutions and dismissals are separate rows and must not inflate the count. This is the whole reason v2 exists.
- **Schema 1 (no `schema` key).** The two fields you would reach for both mislead. Resolution rows share the file, because a `*-fix` skill appends `FIXED:` rows to the same JSONL, so a log can be half resolutions. And `whitelisted` is false almost everywhere, since it is set only when a caller passed `--whitelisted`, so a dismissed finding looks exactly like a confirmed one. **Migrate rather than working around it:** `python3 scripts/migrate-review-log-v2.py <log>` prints a plan, `--apply` rewrites and keeps a `.bak`. Offer this whenever you meet a v1 log; it is inert plumbing, the same class as scaffolding the capture helper above.
- Either way, check whether a category's per-run count is **falling** before proposing anything. A category that went 16, 16, 1, 1, 1 across runs is already fixed at source, and its historical rows are backlog rather than evidence.

### 1b: Project memory (optional convention)

These sources exist only if the project keeps an agent-memory convention; many don't. Treat every one as optional: if a path is absent, skip it silently and lean on the review log and `rejected-proposals.md`. Do not stall waiting for files a fresh project never had.

Also ingest:

- Project `MEMORY.md` "Review History" section, if present (existing convention in some projects, surface debt scores and round summaries).
- `.claude/projects/<project-id>/memory/feedback_fp_*.md`: documented false positives. These become the KEEP-THIS-WHITELISTED signal for Phase 3.
- `.claude/projects/<project-id>/memory/feedback_review_*.md`: severity / priority feedback (e.g. "deprioritize X for this threat model").

### 1c: Existing review & rules context

- Read the project's `*-review` SKILL.md (whichever skill writes to the log). Extract: agent names, current check IDs, known-correct pattern whitelists.
- Read `.claude/scripts/preflight*.sh` if present. Extract check IDs.
- Read `.claude/rules/` index.

Knowing what's already checked prevents proposing duplicates.

### 1d: Previously processed

Read `.claude/reviews/applied-learnings.md` and `rejected-proposals.md` if present. Cluster IDs already applied or rejected don't need re-proposing unless new evidence arrived.

---

## Phase 2: Cluster

Group findings into patterns. See `references/recurrence-detection.md` for the full algorithm. Summary:

1. **Group** by `category_hash`: precomputed by the capture helper as `sha256(category)[:16]`, a pure function of the stable `category` slug. One cluster per category.
2. The hash deliberately excludes the free-text `message` (method names / paths vary per finding) and the `dimension` (the same pattern gets tagged differently by different agents): including either one fragmented a single pattern into many hashes. See `references/review-log-schema.md`.
3. **Count** occurrences per hash across all ingested findings.
4. **Classify**:
   - `Recurring`: ≥ 3 occurrences across ≥ 2 distinct dates
   - `Chronic`: ≥ 5 occurrences OR spans > 30 days OR in ≥ 3 distinct files
   - `False Positive`: user dismissed ≥ 2 times (from feedback_fp_* or explicit rejection)
   - `One-off`: everything else; ignore
5. **Attribute** each cluster to a review dimension (security / architecture / quality / performance). For a cluster whose findings carry more than one dimension (~4% of categories drift this way), pick the dominant one (most frequent, ties broken by highest severity). Determines which optimizer gets the proposal.

Between grouping (2) and counting (3), run the **near-duplicate slug gate** (`recurrence-detection.md` Step 2b): the hash is the slug, so slug drift (`inline-event-handler` vs `inline-event-handler-in-view`) splits one pattern into several sub-threshold clusters. Surface candidate merge-families for human confirmation before classifying: don't auto-merge.

Emit `recurring-patterns.md` as the Phase 2 artifact: one section per cluster with the data from `references/recurrence-detection.md` output format.

---

## Phase 3: Propose

For each cluster, decide the target and draft a proposal. See `references/proposal-template.md` for the exact format.

### 3a: Recurring / Chronic → preventive action

Pick one of these target actions based on the cluster's dimension and what's already in place:

| Cluster dimension | Mechanically checkable, nothing enforces it | Check exists but misses | Judgement pattern, no check is possible |
|-|-|-|-|
| Security | Propose the PAIR: preflight check via `a-review-optimizer` + rule via `a-rules-optimizer` | Fix the check pattern via `a-review-optimizer`, naming the findings it missed | Propose rule file via `a-rules-optimizer` |
| Architecture | Propose the PAIR | Fix the check pattern | Propose rule file |
| Quality | Propose the PAIR | Fix the check pattern | Propose rule, possibly scoped narrowly |
| Performance | Propose the PAIR | Fix the check pattern | Propose rule file |

**Which column you are in is decided by mechanical checkability, not by doubt.** A pattern is mechanically checkable when a grep, an AST or static-analysis query, a linter rule or a one-file script can decide it on THIS codebase at a false-positive rate the project will tolerate. Settle that by running the candidate check over the current tree before proposing it: if it fires on known-good code more often than on the cluster's own findings, it is not checkable here yet, whatever it looks like in the abstract. Checkable means the PAIR is the default: a preflight check (the enforcement) plus a rule (why it matters and what to write instead). Judgement patterns are naming, altitude, architectural taste, anything needing intent, and there a rule alone is correct, because a check could only manufacture false positives.

A pair is two proposals carrying the same bare `cluster_id`, since `target_skill` in `references/proposal-template.md` is single-valued. Label the halves `-check` and `-rule` in the heading you present them under, never inside `cluster_id`: Phase 5 records that id in `applied-learnings.md` and the next run matches it there to decide skip versus RE-EMERGENT, so a suffixed id would hide an applied pair. Present and approve them together; half a pair applied is one of the two failure modes below.

**Why the pair and not either half.** A check with no rule fails the run without saying what to write instead, so the author works around the check. A rule with no check is an intention stated to a reader who may never load the file. In practice the rule-only half is the one that fails: a rule broadened to cover a pattern keeps collecting findings that each get fixed by hand, because nothing ever fails a run, while a pattern backed by a deterministic check drops to one or none per run.

**A RE-EMERGENT cluster means the defense that exists does not work, so the proposal is not another rule.** `references/recurrence-detection.md` Step 4 assigns the class from two signals:

- **Any log: the applied-learnings signal.** The cluster_id is already in `.claude/reviews/applied-learnings.md` and the cluster has findings dated after that entry. Read the defense's identity off the applied-learnings row (its target and the files it modified). This is the only signal a v1 log can give, since v1 rows carry no `action` field.
- **v2 log: the resolution signal.** A resolution row carrying `action: "covered"`, with findings in the cluster dated after it; its `covered_by` names the defense directly. A project part-way through migration can show either signal, so a miss on one is not an answer.

Do not read `covered_by` off a v1 finding row. Where v1 stamped it there, it records a defense someone claimed, not a resolution.

Whichever signal fired, the defense it names picks the route:

1. **The defense is a rule and no check exists: propose the check.** The rule was right and nothing enforced it. Pair it with a one-line amendment to the existing rule pointing at the new check ID; do not restate the rule.
2. **The defense is a check: the check has a gap, so propose a pattern fix.** Name the specific findings the current pattern misses, `file:line` each, and say why each one slips through (a wrong glob, an anchored regex, a call shape the pattern never modelled). "Tighten the check" is not something `a-review-optimizer` can act on.
3. **A check exists and does match the findings: the failure is upstream of review.** The check is not wired into the gate, is not run before commit, or its output is being read and ignored. Escalate to the user as a process question. Do not file a third proposal against a defense that already fires correctly.

**Re-emergent clusters go first**, ahead of Chronic, in the Phase 4 batching. It is the only evidence class that says a defense was tried and did not hold; every other class only says a pattern is popular.

**Before proposing a NEW rule, check whether the rule already exists but isn't loading.** A cluster can keep recurring while the governing rule already exists, because it lives in a file whose `paths:` scope never matches the file type where violations happen (e.g. a JS rule scoped `public/js/**` that never loads while editing PHP views, where every regression sits). Signal: the cluster's `file` values cluster in one file type, and grep finds the rule already stated in a differently-scoped rule file. When you see this, the proposal is not "add a rule"; it's "restate the existing rule in a file scoped to where the violations occur, with a one-line cross-reference to the source of truth," routed to `a-rules-optimizer`. This path-visibility fix is cheaper and truer than inventing a duplicate rule. Name the root cause explicitly in the proposal's `rationale`.

**Path visibility and re-emergence look identical from the count and need opposite fixes, so decide which one you have before drafting.** Path visibility means the rule never loaded where the violations sit, so nobody read it: the fix is scope. Re-emergence means the rule did load, was read, and the pattern continued anyway: the fix is enforcement. The tell is whether the rule file's `paths:` glob matches the cluster's `file` values. If it matches, reading was never the problem and you are in the escalation ladder above.

### 3b: False Positive clusters → whitelist action

Target: the review skill's "KNOWN CORRECT PATTERNS (DO NOT FLAG)" section (see `a-review-optimizer`'s Phase 4a output). Propose adding:

```
- <normalized pattern>: <project-specific reason>, see <file:line of representative occurrence>
```

Use the existing `feedback_fp_*.md` text verbatim where possible: the user wrote it in their own words for a reason.

### 3c: Proposal structure

Every proposal must include (see `references/proposal-template.md`):

- `cluster_id`: stable identifier (hash prefix)
- `pattern`: one-line human description
- `evidence`: list of findings supporting the cluster (file:line + date + severity)
- `rationale`: why a preventive change is warranted (count, span, severity distribution)
- `target_skill`: `a-rules-optimizer` or `a-review-optimizer`
- `target_file`: which file the other skill should modify
- `proposed_diff`: concrete change, not a description of one
- `expected_effect`: what future reviews should differ about after this lands

Missing fields → proposal is incomplete, don't show it to the user.

---

## Phase 4: User approval gate (hard stop)

**This phase must pause for user input.** Present proposals one at a time, batched by priority (RE-EMERGENT first, then Chronic, then Recurring, then False Positive whitelists). For each:

1. Show the proposal in human-readable form (pattern, evidence count, rationale, the diff).
2. Ask: "Apply this? [y/n/skip/details]"
3. On `y` → delegate to the target skill with the proposal as input. That skill writes the file. Do not write anything directly from `a-self-learner`.
4. On `n` → append to `rejected-proposals.md` with reason (ask the user for the reason if `n` alone; "no reason given" is acceptable).
5. On `skip` → leave for next run, neither apply nor reject.
6. On `details` → show evidence in full (all finding lines, not just count), then re-prompt.

**Commit policy.** Even after approval, this skill does not commit. The target skill writes the file; the user decides when to stage and commit per the global per-commit-ask rule. Do not invoke `git commit` from this workflow.

---

## Phase 5: Record

After the approval loop finishes:

1. **`applied-learnings.md`**: append one entry per applied proposal: date, cluster_id, target, summary, file(s) modified. This becomes the project's "how our defenses hardened" changelog.
2. **`rejected-proposals.md`**: already appended to in Phase 4 for each rejection. Also record the evidence count at rejection time so re-proposal threshold can be computed ("this was rejected when count was 4; only re-raise when count exceeds 8").
3. **Archive processed AND resolved findings**: move them from `review-issues.jsonl` to `review-issues-archive.jsonl`, stamped with a processed-date, so the next run starts from a smaller log and doesn't re-cluster old data. Archive a finding when ANY of these holds:
   - it participated in an applied or rejected cluster this run;
   - a resolution row pairs with it on `(category, file)`, such as a `FIXED:` row written by the project's `*-fix` skill;
   - it carries a `covered_by` stamp naming the check or rule that now owns it.

   On a v2 log the first two cases are one query, not a convention hunt: a finding is resolved when a `type: "resolution"` row names it in `resolves`, or failing that, when the newest resolution sharing `(category_hash, file)` is dated at or after it. Archive the finding and its resolution rows together so the pair stays readable.

   **Archiving is not deletion, and it does not require re-verifying the fix.** The archive file is kept, and if the issue is still present the next review re-captures it. Being conservative here is exactly what breaks the loop: a resolved finding left in the active window re-clusters on every future run and buries the live signal under it.

   Archiving only the first case is the common mistake. It is how two projects reached 491 and 140 active rows that were roughly 85% resolved pairs, and on one of them a single commit fixed four findings *in the same commit that appended them to the log*, leaving all four reading as open weeks later.
4. **Report summary**: count of proposals applied / rejected / skipped, list of files modified, suggestion for when to re-run (typically: "after the next 5 reviews, or in ~4 weeks").

---

## What this skill does NOT do

- **Does not write rule files or review SKILLs directly.** Always delegates.
- **Does not auto-commit.** User owns commits per CLAUDE.md.
- **Does not cross-pollinate between projects.** Each project's feedback loop is isolated.
- **Does not re-review the codebase.** It only operates on the review log and feedback memory. If the log is empty, the skill has nothing to do.
- **Does not replace `a-rules-optimizer` or `a-review-optimizer`.** Those remain the authoritative ways to audit against the codebase. This skill adds a *historical-evidence* input that those skills can consume.

---

## Reference files

| File | When to read | Contains |
|-|-|-|
| `references/review-log-schema.md` | Phase 1a (understanding the log format) and any capture-side integration | JSONL schema, field definitions, `.claude/reviews/` directory convention |
| `references/recurrence-detection.md` | Phase 2 (clustering) | Grouping, hashing, thresholds, cluster classification |
| `references/proposal-template.md` | Phase 3 (drafting proposals) | Required fields, format, target-skill routing rules |
| `references/capture-finding.sh` | Setup: helper that existing review skills call to append findings and resolutions | Bash helper, schema 2, prints the `finding_id` it wrote so a fix skill can pass it back as `--resolves` |
| `scripts/migrate-review-log-v2.py` | Phase 1a, whenever a log has no `schema` key | Converts the three v1 conventions to v2. Dry run by default, `--apply` keeps a `.bak`, refuses to run over malformed lines |
