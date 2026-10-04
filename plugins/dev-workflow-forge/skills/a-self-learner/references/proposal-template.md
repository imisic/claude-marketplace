# Proposal Template

The shape of the proposal that `a-self-learner` Phase 3 generates and Phase 4 presents. Every proposal must be complete: missing fields mean the proposal isn't ready to show the user.

## Required fields

```yaml
cluster_id:        <hash prefix, e.g. "a3f1c2b4">
pattern:           <one-line human description>
dimension:         <security | architecture | quality | performance>
classification:    <Recurring | Chronic | RE-EMERGENT | False Positive>

evidence:
  count:           <integer>
  span_days:       <integer>
  distinct_files:  <integer>
  first_seen:      <YYYY-MM-DD>
  last_seen:       <YYYY-MM-DD>
  examples:        <list of 3-5 findings: file:line, severity, date>

rationale:         <why this warrants a preventive change, 1-3 sentences tied to the evidence>

target_skill:      <a-rules-optimizer | a-review-optimizer>
target_file:       <specific file the target skill should modify>
proposed_change:   <concrete diff or rule text, NOT a description>

expected_effect:   <what should differ about future reviews after this lands>

re_propose_if:     <condition that would justify re-raising if rejected>
```

## Routing: which skill writes what

| Target file | Target skill | Use when |
|-|-|-|
| `.claude/rules/<file>.md` (new or existing) | `a-rules-optimizer` | Pattern-level issue that a rule could prevent upstream (e.g. "all SQL uses prepared statements"). Preferred when the pattern represents a project convention. |
| `.claude/rules/<in-scope file>.md` (restate existing rule) | `a-rules-optimizer` | The governing rule already exists but its `paths:` scope never loads on the file type where violations occur. Propose restating it in a file scoped to those files, with a cross-reference to the source of truth, not a brand-new rule. |
| `.claude/scripts/preflight*.sh` | `a-review-optimizer` | Issue is best caught by a deterministic grep/python check. Preferred when the pattern has a mechanical signature. |
| Review skill's capture calls | `a-review-optimizer` | Scaffolding a project's capture mechanism: the review SKILL.md must call `capture-finding.sh` per confirmed finding. `a-self-learner` drops the helper script, but wiring calls into the review skill is `a-review-optimizer`'s edit. |
| Review skill's `KNOWN CORRECT PATTERNS` section | `a-review-optimizer` | False-positive whitelist additions. |
| Review skill's agent prompt | `a-review-optimizer` | New checks that require LLM judgment (not mechanical). |

**When ambiguous, prefer `a-rules-optimizer` over `a-review-optimizer`.** Rules prevent at write-time; preflight catches at review-time. Prevention is cheaper.

## Writing `proposed_change`

The proposal must be **executable** by the target skill, not descriptive. Two examples:

### Good: rule file proposal (target: `a-rules-optimizer`)

```markdown
target_file: .claude/rules/security.md

proposed_change: |
  Append to `security.md` under a new section `## Subprocess Safety`:

    - Every `subprocess.*` call must include `timeout=`: no exceptions for "quick" commands.
    - `shell=True` is forbidden outside `scripts/`: argv form only.
    - Reference: src/core/backup_engine.py:142 for the canonical pattern.
```

### Bad: too vague to act on

```markdown
target_file: .claude/rules/security.md

proposed_change: "Add a rule about subprocess safety."
```

The second form forces the target skill to reinvent the proposal. Don't do that.

### Good: preflight check proposal (target: `a-review-optimizer`)

```markdown
target_file: .claude/scripts/preflight.sh

proposed_change: |
  Replace the current SUB-01 Python block with:

    ```python
    import re, pathlib
    for f in pathlib.Path('src').rglob('*.py'):
        text = f.read_text()
        for m in re.finditer(r'subprocess\.(run|call|check_output|check_call|Popen)\s*\(', text):
            ...  # balanced-paren scan checking 'timeout' not in call_text
    ```

  Reason: current regex misses `.check_output` and `.Popen` forms: evidence at src/cli.py:622, scripts/ingest.py:394.
```

## Presentation to the user

When Phase 4 shows a proposal, display it as:

```
────────────────────────────────────────────────
Proposal a3f1c2b4: subprocess-without-timeout
Classification: Chronic (10 findings, 2026-01-15 → 2026-04-19, 4 files)

Rationale:
  Current preflight catches .run() but misses .check_output() and .Popen().
  Pattern has recurred for 3 months across 4 files.

Target: a-review-optimizer → .claude/scripts/preflight.sh
Change: update SUB-01 regex to cover all subprocess variants (see diff above)

Expected effect:
  Next review should catch subprocess timeout issues in cli.py:622 and
  scripts/ingest.py:394 (both currently missed).

Apply this? [y/n/skip/details]
────────────────────────────────────────────────
```

Keep the prompt terse. The user reads the rationale, looks at the diff, decides. Don't pad with hedging or alternatives: the skill already picked one option; the user either agrees or doesn't.

## After approval

Invoke the target skill with the proposal as structured input. Example (illustrative, actual invocation shape depends on how the skill wrapper is called):

```
Delegate to a-review-optimizer with:
  action: update-preflight-check
  check_id: SUB-01
  file: .claude/scripts/preflight.sh
  proposed_change: <the diff text from the proposal>
  source_cluster: a3f1c2b4
```

The target skill applies the change and reports back with the modified file paths. `a-self-learner` then appends to `applied-learnings.md` with the cluster_id, target, and files modified.

## After rejection

Append to `rejected-proposals.md`:

- Cluster ID, pattern, date of rejection
- Evidence count at rejection time
- Reason (quote the user's reply or note "no reason given")
- Re-proposal threshold (typically: count must exceed rejected_count × 2 or a new distinct file must appear)

Re-proposal thresholds prevent the skill from pestering the user about rejected ideas.
