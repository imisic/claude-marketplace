# Generated-Skill Scaffold

The parts of a mature review skill that live *outside* the agent prompts and the report format. `output-template.md` covers the report body and severity definitions; this file covers everything else a hand-tuned review skill contains: the flag surface, the parallel-dispatch skeleton, the growing false-positive whitelist, the `--debt` and `--full` modes, the self-learning capture loop, and rule-candidate surfacing.

**The mechanics live in the `a-review-core` skill, which the generated skill reads at runtime.** This file stayed as the generator's coverage checklist, so the two overlap on purpose and for different readers: the core is what the review reads while it runs, this is what you check while you build one. Where they describe the same mechanism, the core is authoritative and this file is the reminder that the project skill needs to have dealt with it.

Use it two ways:
- **Improving an existing skill (Phase 3/4):** treat the section list below as a coverage checklist. For each section, does the target skill have it? Missing ones are `ADD`; thin ones are `UPDATE`. Never rip out a section the user already tuned.
- **From scratch (Phase 4 "When No Review Skill Exists"):** this is the blueprint. Emit the sections the project actually needs (a static site skips `--debt` query scoring; a CLI tool skips web XSS whitelists), each populated with real file:line referents from Phase 2, never generic placeholders.

Everything here is stack-agnostic. The examples span PHP, Python, JS/TS, Go, and Rust on purpose; pick the idiom that matches the project you analyzed.

---

## 1. Flag surface

A mature skill exposes a small, stable set of scope/depth flags. Emit only the ones the project needs, but keep the names identical across projects so muscle memory transfers.

```markdown
## Flags

| Flag | Behavior |
|-|-|
| `--changed` | Default. Review only files changed since HEAD (`git diff --name-only HEAD`) |
| `--full` | Review the whole source tree + architecture diagrams + health score |
| `--security-only` | Run the Security agent alone |
| `--debt` | Add tech-debt scoring, stricter thresholds, and extra checks to every agent |
| `--all` | `--full` + `--debt` combined (most thorough) |

Flags combine where logical (e.g. `--security-only --debt`).
```

Guidance:
- `--changed` is always the default. State the exact git command so the skill is deterministic about scope.
- `--debt` is a *modifier*, not a separate scope: it lowers thresholds (file-length, function-length) and turns on extra checks that are too noisy for every run.
- Only ship `--full`'s diagram half if the project has a real layered architecture to draw. A 3-file script doesn't.

---

## 2. Execution / dispatch

Every mature skill runs its dimensions concurrently and hands each one only its slice of the preflight output. **Dispatch them through a mechanism that returns each agent's report, not through a batch of fire-and-forget Agent calls.** In Claude Code that mechanism is the Workflow tool, and the rest of this section is written against it. On a harness without Workflow, keep the requirement and substitute its own orchestration primitive: the non-negotiable part is that every dispatched agent's findings come back to the caller, structured, before reconciliation runs.

### Why Workflow, not a batch of Agent calls

The batch-of-Agent-calls form was the recommendation here until 2026-08-05. It fails in a way that is easy to mistake for success: the agents spawn, run to completion, and then go idle without ever returning their report. You get an `idle_notification`, no findings, and a review that looks like it ran. `run_in_background: false` does **not** reliably prevent it (the flag has been observed ignored), `TaskList` does not show the agents, and `SendMessage` nudges return another idle notification rather than the report. Observed twice on the same skill, two runs apart.

The same work expressed as a Workflow script ran 25 agents with zero errors on the run that replaced it. Workflow also buys three things the batch form cannot express: a structured return schema per agent (so findings arrive parseable instead of as prose you re-read), an adversarial verify stage, and a journal you can inspect when a result looks wrong.

Teach the generated skill this shape:

```markdown
## Execution

Dispatch via the Workflow tool. One finder per dimension, then an adversarial
verify pass on every finding the finders return.

| Agent | Owns (checks these) | Does NOT check |
|-|-|-|
| Security | injection, authn/authz, secrets, unsafe deserialization, SSRF | error-handling structure, types, dead code |
| Architecture | layering, registration/wiring, error-handling structure, resource cleanup | injection content, type modernization |
| Quality | types, dead code, duplication, complexity, modernization | anything Security or Architecture owns |

Each finder's prompt carries: the shared context file, its own brief, its slice of
the preflight output split by check-ID prefix (SEC-* → Security, ARCH-*/EXC-*/WEB-* →
Architecture, TYPE-*/QUAL-* → Quality), and the repo root.

If `--security-only` is set, run only the Security dimension.
After the workflow returns, run Post-Flight Reconciliation on the confirmed findings.
```

Use `pipeline()` so each dimension's findings start verifying as soon as that dimension finishes, rather than waiting on the slowest finder. Give every agent a `schema` so findings come back structured. Require a `failure_scenario` field: concrete inputs or state leading to a specific wrong outcome. A finding whose author cannot fill that field is the kind that wastes the reviewer's afternoon.

**The verify stage is not optional.** Prompt it to *refute*, defaulting to refuted when uncertain, and require it to trace the chain from source rather than accept the finder's reasoning. On the 2026-08-05 run this refuted 6 of 18 raw findings, including three whose stated mechanism was accurate but whose claimed consequence did not follow. That failure mode (true mechanism, wrong conclusion) is the dominant one on a mature codebase, and only an adversarial second pass catches it.

Tell the generated skill to state in its report what the verify stage refuted, not just what it confirmed. A run that reports 12 findings and silently drops 6 reads as less trustworthy than one that shows both numbers.

The **Owns / Does NOT check** two-column form is the anti-overlap device: a finding belongs to exactly one agent, and each agent is told in writing what to leave alone. This is where the Phase 3c overlap resolutions get written down. 3+ dimensions is the norm; 2 is acceptable for a small single-concern project, more than 4 usually means you fragmented a scope that should be one dimension.

Workflow requires the user to have opted into multi-agent orchestration. A user-invoked review skill whose instructions say to call Workflow satisfies that, so the generated skill should say so explicitly in its execution section.

---

## 3. Context Awareness (DO NOT flag), and how it grows

The single highest-value section in a mature skill. It records hard-won false positives so the review stops re-flagging correct project conventions. A from-scratch skill starts this section from Phase 2/3b findings; every later optimizer run **appends** to it.

```markdown
## Context Awareness (DO NOT flag)

These patterns are correct in THIS project; agents must not flag them:
- Base class handles prepared statements via inherited query methods (all Models extend it)
- `<Framework>` command functions look unused; they're invoked by the framework via decorators/registry
- `.example` / `.sample` config files are committed intentionally; real configs are gitignored
- Result-tuple return shape `(ok, msg)` is the project convention, not a smell; see src/core/engine.<ext>:45

### Added by a-review-optimizer [YYYY-MM-DD]
- <newly confirmed false positive>, with a real file:line referent and one-line reason
```

**The growth mechanism (make the optimizer do this every run):**
- When Post-Flight Reconciliation *dismisses* a preflight finding as a false positive, that dismissal is knowledge. Add it here under a dated `### Added by a-review-optimizer [DATE]` marker, with the file:line and the one-line reason it's safe.
- Never delete an existing whitelist entry unless you confirmed (via grep of current code) the referenced pattern is gone. Stale-looking entries still catch things.
- Keep the user's original wording verbatim; only append. A rephrased whitelist entry is a whitelist entry the user can no longer trust.
- Prefer a real referent (`file:line`) over prose; it lets the next run verify the entry is still live.

This section and the self-learning log (§6) are two halves of the same loop: confirmed findings feed the log; dismissed findings feed this whitelist.

---

## 4. `--debt` mode

Turns the review into a scored artifact. Only computed when `--debt` (or `--all`) is set.

```markdown
## Debt Scoring (--debt / --all only)

Assign points per confirmed finding, then sum (cap at 100, lower is better):

| Severity | Points |
|-|-|
| Critical | 8 |
| High | 4 |
| Medium | 2 |
| Low | 1 |

### Score Breakdown
| Agent | Critical | High | Medium | Low | Score |
|-|-|-|-|-|-|
| Security | X | X | X | X | X |
| Architecture | X | X | X | X | X |
| Quality | X | X | X | X | X |
| **Total** | X | X | X | X | **X/100** |

Bands: 0 pristine · 25 healthy · 50 needs attention · 75+ stop and fix.

### Auto-Fixable
**Safe (no logic change):**
- [ ] <mechanical fix, e.g. add missing strict/type declarations in N files>
- [ ] <remove unused imports in N files>
- [ ] <swap debug-print for logger in N locations>

**Needs confirmation (behavior may change):**
- [ ] <narrow a broad catch; verify intended behavior>
- [ ] <remove apparently-dead code; confirm no dynamic dispatch>
- [ ] <add null/None check after lookup; decide the miss behavior>
```

`--debt` also *tightens thresholds*: e.g. file-length flag drops from >500 to >300 lines, function-length from >50 to >30, and checks that are `info` on a normal run escalate to `warn`. Wire those threshold shifts into the agent prompts (a small "`--debt` / `--all` only" subsection under the relevant checks), not just the score.

The safe-vs-needs-confirmation split is load-bearing: it's what lets a downstream `fix` skill batch-apply the safe half without a human in the loop.

---

## 5. `--full` mode: architecture diagrams + health score

Only when `--full` (or `--all`) is set. Skip entirely for projects without a real layered structure.

**Dependency diagram**: scan the import mechanism for the stack (`use` in PHP, `import`/`from` in Python, `import`/`require` in JS/TS, `import` in Go, `use` in Rust) and draw cross-layer edges only (drop same-layer noise):

```markdown
### Component Dependencies
​```mermaid
graph LR
  subgraph Controllers
    BlogController
  end
  subgraph Services
    BlogService
  end
  subgraph Models
    BlogPost
  end
  BlogController --> BlogService
  BlogService --> BlogPost
​```
```

**Layer diagram**: the *allowed* dependency direction. Flag arrows going the wrong way (a violation) with red styling:

```markdown
### Layer Dependencies
​```mermaid
graph TD
  Views --> Controllers
  Controllers --> Services
  Controllers --> Models
  Services --> Models
  Models --> Core
​```
```

The layer names come from Phase 2 (MVC → Views/Controllers/Services/Models; clean/hexagonal → presentation/domain/data; pick what the project actually uses).

**Architecture Health Score**: weighted, project-specific. Weights should sum to 100 and reflect what matters for *this* architecture:

```markdown
### Architecture Health Score: X/100
| Check | Weight | Scoring |
|-|-|-|
| Layer compliance | 30 | -5 per violation |
| Base-class / interface compliance | 20 | -5 per non-compliant unit |
| Boundary pattern (mutations through services/repos) | 20 | -5 per bypass |
| Registration / wiring completeness | 15 | -3 per missing registration |
| File organization / naming | 15 | -3 per misplaced file |
```

---

## 6. Self-learning capture loop (MANDATORY in the generated skill)

A mature review skill doesn't just report; it **records** every confirmed finding to a per-project log so recurring issues can later harden rules and preflight (via `a-self-learner`). Scaffold all three pieces so a from-scratch skill wires the loop, not just the review:

### 6a. Emit the capture script

Copy `../a-self-learner/references/capture-finding.sh` (it ships in this plugin, beside this skill) into the project at `.claude/scripts/capture-finding.sh` and `chmod +x` it. **Copy it, never retype it.** That file is the canonical implementation and it is versioned: it writes schema 2, records dismissals with their reason, validates `--action`, and prints the `finding_id` it wrote so a fix skill can pass it back as `--resolves`. An embedded duplicate of it used to live here and drifted out of parity with the original within one release, which is exactly the failure this instruction replaces.

The script is stack-agnostic (it only appends JSON), creates `.claude/reviews/` on first call, and computes `category_hash` from the category slug alone. Read `../a-self-learner/references/review-log-schema.md` for the field reference before wiring capture calls.

If the project already carries an older copy, replace it and run `python3 ../a-self-learner/scripts/migrate-review-log-v2.py .claude/reviews/review-issues.jsonl` (dry run first) so the existing log matches what the new helper writes.

### 6b. Emit the capture section in the generated SKILL.md

```markdown
## Capture Findings for Self-Learning (MANDATORY)

After reconciliation, append every CONFIRMED finding (all severities, including INFO)
to `.claude/reviews/review-issues.jsonl` via `.claude/scripts/capture-finding.sh`.
This feeds `/a-self-learner` so recurring issues harden rules/preflight over time.

Generate one `RUN_ID` per review (e.g. `r-YYYYMMDD-HHMM`); reuse it for every finding
in the run. Call once per finding:

​```bash
bash .claude/scripts/capture-finding.sh \
  --project <project> --skill <this-skill> --run-id "$RUN_ID" \
  --dimension <security|architecture|quality|performance> \
  --severity <critical|high|medium|low|info> \
  --category <stable-slug> \
  --file <repo-relative-path> --line <n> \
  --message "<one-line description>" \
  [--fix "<proposed fix>"] [--agent <agent>] [--check-id <preflight id>]
​```

Capture dismissals too, with `--dismissed "<reason>"`. They are not noise: a
dismissed finding is the evidence behind a whitelist entry, and a pattern
dismissed repeatedly is a check that needs narrowing. They carry
`disposition: "dismissed"` and are excluded from recurrence counts, so capturing
them cannot inflate a cluster. The Context Awareness whitelist still gets the
prose entry; this is the machine-readable half of the same decision.

If the project has a `*-fix` skill, it records the outcome on the same log:

​```bash
bash .claude/scripts/capture-finding.sh \
  --action fixed --resolves <finding_id> \
  --project <project> --skill <fix-skill> --run-id "$RUN_ID" \
  --dimension <d> --severity <s> --category <same-slug-as-the-finding> \
  --file <path> --line <n> --message "<what changed>" \
  [--fix-commit <sha>]
​```

Use `--action covered --covered-by <check-id-or-rule-file>` when the fix is a new
defense rather than a one-site change. That is what lets the self-learner tell a
pattern that keeps recurring from one that recurred *after* a defense was put in
place, and the second is far more urgent than the first.
```

### 6c. Seed the stable category-slug table

**Emit it as `references/capture-slugs.md`, a markdown table with each slug in backticks.** The capture helper reads every backticked slug-shaped token from any column of a table row, so `| Slug | Pattern |` and `| Pattern | Slug |` both work; it warns on a `--category` missing from the table and suggests near-matches. A first-column-only parse would read a `| Pattern | Slug |` file as present while checking nothing, so the review would coin fresh slugs against a vocabulary it never consulted.

The `--category` slug is the clustering key: the **same class of issue must get the same slug every run**, or `a-self-learner` can't see the recurrence. Seed a generic table and let the skill coin project-specific slugs (lowercase kebab-case noun phrases) as new patterns appear:

| Pattern | Slug |
|-|-|
| SQL built by string concatenation/interpolation | `sql-injection-string-concat` |
| Output rendered without escaping (XSS) | `xss-unescaped-output` |
| State-changing endpoint without CSRF check | `missing-csrf-validation` |
| Secret/API key hardcoded in source | `hardcoded-secret` |
| Token/hash compared with `==` not constant-time | `non-constant-time-compare` |
| URL field used without protocol allowlist | `missing-url-protocol-validation` |
| Unsafe deserialization (pickle/unserialize/yaml.load) | `unsafe-deserialization` |
| Subprocess/exec without timeout | `subprocess-without-timeout` |
| Command built with string interpolation | `command-injection-interpolation` |
| Path from input used without containment check | `path-traversal-unchecked` |
| Bare/silent catch that swallows the error | `swallowed-exception` |
| Broad catch with no logging | `broad-catch-no-log` |
| DB/data access outside the data layer | `data-access-outside-layer` |
| Mutation bypassing the service/repository layer | `mutation-bypasses-service` |
| Component/route/view not registered where required | `missing-registration` |
| Check-then-act on the filesystem (TOCTOU) | `toctou-filesystem` |
| Missing null/None check after a lookup | `missing-null-check` |
| Unused import/use statement | `unused-import` |
| Dead private method / unreachable code | `dead-code` |
| Function longer than the project limit | `function-too-long` |
| File longer than the project limit | `file-too-long` |
| Duplicated logic that should be shared | `duplicate-logic` |
| Stringly-typed value where an enum/const exists | `stringly-typed-value` |
| Unbounded query / missing LIMIT | `unbounded-query-no-limit` |
| Query inside a loop (N+1) | `n-plus-one-query` |
| Debug print/log left in source | `debug-statement-left-in` |

---

## 7. Rule-candidate surfacing

When a review keeps finding the same class of issue, the fix is a *rule*, not another finding. Teach the generated skill to surface candidates at the end of every run:

```markdown
## Rule Candidates

A finding is a rule candidate when: the same issue appears in 3+ locations, OR it
reflects an undocumented project convention, OR the fix needs knowledge not obvious
from the code. For each candidate, check `.claude/rules/` (or CLAUDE.md); if it's
not already covered, propose adding it to the right file. Rules are one actionable
statement, no code blocks (use `Reference: path/file.ext` instead).

| Pattern | Occurrences | Proposed Rule | Target File |
|-|-|-|-|
| <recurring pattern> | N | <one-line actionable rule> | <rules file> |

Ask before adding; never write a rule silently.
```

This is the manual, in-the-moment counterpart to `a-self-learner` (which mines the accumulated `review-issues.jsonl` later). Both routes end at `a-rules-optimizer`, which owns the actual rule edit.

---

## 8. Stack detection and per-stack references

A review skill that applies one lens to every file reviews the minority stacks badly. Most projects are not monolingual: a PHP app also ships browser JS, SQL migrations and CLI tooling, and a checklist written for the dominant language says nothing useful about the others.

Split the generated skill three ways:

- `SKILL.md` carries the trigger, the shared spine and the dispatch. Nothing stack-specific.
- `references/agent-*.md` carry the per-dimension scope, as today.
- `references/stack-*.md` carry stack specifics and load **only when the diff touches that stack**.

### Detect from real signals, matched against the diff

Match changed paths, not repo contents. A PHP-only change must not pay for the SQL reference. Derive the signal list from what Phase 2 actually found; do not paste a menu of every ecosystem.

```markdown
| Changed paths match | Add to prompt | Goes to |
|-|-|-|
| `**/*.php`                   | `references/stack-php.md`            | all |
| `public/assets/js/**`        | `references/stack-browser-js.md`     | Quality + Security |
| `tests/*.mjs`                | `references/stack-node-tests.md`     | Quality |
| `database/migrations/*.sql`  | `references/stack-sql-migrations.md` | Architecture |
```

Anchor detection on manifests and markers that exist (`composer.json` with a `require.php` floor, a `package.json` and its absence, `tsconfig.json`, `go.mod`, a migrations directory plus a ledger table), not on file extensions alone. The absence of a manifest is itself a signal: browser JS with no `package.json` and no bundler is a different review problem from a bundled React app, and the checks barely overlap.

### The token argument

`SKILL.md` loads in full on every run. Stack knowledge welded into an agent brief is paid for by every review of every file type, and it grows without bound as stacks are added. Behind detection, a typical single-stack diff loads the spine plus one reference, and adding a fifth stack costs one new file rather than another 40 lines that every future run carries.

### What a stack reference contains

Concrete checks with a verification command, not topic headings. "Check for N+1 queries" is worthless; a command whose output is unambiguous, plus what a hit means, is a check:

```markdown
## A new script must be registered in build.php
There is no discovery. A view can load a file the build never minifies.
Verify: `php build.php check; echo "exit=$?"`   Non-zero means unregistered.
```

If a check cannot be verified by running something or by reading one named file, it belongs in an agent brief as judgement, not in a stack reference as a check.

### Per-project, not user-level

Stack references live in the project's own skill. Every good check needs a real referent and a command that only means something in that repo (`php build.php check`, `bin/migrate.php status`, that project's PHPStan level). A shared user-level `stack-php.md` has to be true for every PHP project, which sands it down to the generic advice this whole skill exists to avoid. The cost is real: two PHP projects re-derive overlapping files and drift apart. Take it. One file that is true for neither is worse than two that are each true for one.

The **spine** is the opposite case and stays here, in `review-dimensions.md`: boundary and input handling, authorization on every path touching data, error paths and dependency-down behaviour, secrets and config leakage, unbounded queries and N+1, data migration safety, dead code and near-duplicate logic, and whether tests cover the paths that changed. Those are true everywhere. Justify each against something Phase 2 actually found in the project and drop the ones you cannot; a checklist item nobody can fail is noise.

## 9. Rules as review input

Every generated skill treats `.claude/rules/` as a destination: recurring findings become rule candidates (§7). Almost none treat it as a source. That is half a loop, and the core closes it: it resolves which rule files govern the changed paths, hands them to the owning dimension, and carries the calibration for what counts as a violation.

What the generator checks here is narrower:

- **The project has a rule-routing table** when its rules are subsystem-shaped, mapping changed paths to a rule file and to the dimensions that receive it. At least one fleet review skill is the reference implementation, carrying one since 2026-08-23.
- **The table hands over the rule FILE, never a restatement of it.** A second copy is one edit from disagreeing with the first.
- **A project with no `.claude/rules/`** gets no rules dimension, and the absence is surfaced as a gap for `a-rules-optimizer` rather than filled with invented rules.

---

## 10. Finder memory

The core injects the project's own captured findings for the files in scope, capped and marked as prior observation rather than verdict, and names git history as the fallback when the log is thin. The generator's job is to confirm the plumbing exists: the project captures to `.claude/reviews/review-issues.jsonl` at all (see §6), and its slug table is stable enough that a recurring pattern reaches the finder as one pattern rather than five near-duplicates.

