# Review Output Format Template

Use this when building a new review skill from scratch (Phase 4, no existing skill). The format enforces fix readiness on every finding.

## Report Template

```markdown
# Code Review Report
**Project:** [project name]
**Stack:** [languages + frameworks]
**Target:** [X files: scope description]
**Date:** [timestamp]
**Preflight:** [X checks run, Y findings fed to agents]

## Summary
| Severity | Count |
|-|-|
| Critical | X |
| High | X |
| Medium | X |
| Low | X |

## Critical Issues (Fix Before Merge)
| # | Agent | File:Line | Current Code | Proposed Fix | Why | Intent Ruled Out |
|-|-|-|-|-|-|-|
| 1 | Security | src/auth.py:44 | admin credential hardcoded as a string literal | value read from an environment variable instead | Hardcoded credential accessible to anyone with repo access | No test-fixture marker, no allowlist entry, and the two sibling auth paths both read from env |

## High Priority
| # | Agent | File:Line | Current Code | Proposed Fix | Why | Intent Ruled Out |
|-|-|-|-|-|-|-|

## Medium Priority
| # | Agent | File:Line | Current Code | Proposed Fix | Why | Intent Ruled Out |
|-|-|-|-|-|-|-|

## Low Priority
[Summary count by category: individual items not listed]
- Type modernization: X items
- Naming: X items
- Style: X items

## Skipped (real, not acted on)
| Finding | Why skipped | Revisit when |
|-|-|-|
| 6-view page shell duplicated | Fix reaches 3 files outside the diff | Next time one of those views changes |

*A confirmed finding deliberately not fixed goes here, not into silence. Legitimate reasons: the fix changes intended behaviour, it needs a decision that is the user's, or it reaches well outside the reviewed scope. Without this table a deliberate skip and an oversight look identical, and the next run rediscovers it cold.*

## Preflight Reconciliation
| Check ID | Status | Agent | Verdict |
|-|-|-|-|
| SEC-01 | fail | Security | Confirmed: see finding #1 |
| SUB-01 | warn | Architecture | Dismissed: timeout not needed (local-only script) |
| WEB-01 | warn | Architecture | Confirmed: see finding #4 |

## Auto-Fixable Issues
**Safe (no logic changes):**
- src/utils.py:1-3: remove unused imports (os, sys, re)
- src/models.py:22: `Optional[str]` → `str | None`
- src/views.py:8: `List[dict]` → `list[dict]`

**Needs confirmation:**
- src/backup.py:140-180: duplicate sync block, extract to helper? (logic might differ subtly)

## Recommended Fix Order
1. [Critical #1] Fix hardcoded credential: security exposure
2. [High #3] Add timeout to subprocess.run: blocks indefinitely on large DBs
3. [Auto-fix batch] Run safe auto-fixes (imports, types)
4. [Medium items] Address in next sprint

## Tech Debt Score (if requested)
**Score: X/100**
| Category | Points |
|-|-|
| Security | X |
| Architecture | X |
| Quality | X |
| Performance | X |

Breakdown: 0 = pristine, 25 = healthy, 50 = needs attention, 75+ = stop and fix
```

## Fix Readiness Rules

Every finding at Critical, High, or Medium severity MUST include all 6 columns:

| Column | Required | What it contains |
|-|-|-|
| File:Line | Always | Exact location, e.g., `src/backup.py:88` |
| Current Code | Always | The actual code as it exists (verbatim, can be truncated with `...`) |
| Proposed Fix | Always | What the code should look like after fixing |
| Why | Always | One sentence, specific to this project, explaining impact |
| Intent Ruled Out | Always | What was checked to confirm the behaviour is not deliberate, or `intent-unverified` |
| Impact | Always | `failure_scenario` if the finding is correctness, `cost` if it is maintainability. See below |

**Pick the impact field by kind, and never force the wrong one.**

- **correctness** → `failure_scenario`: concrete inputs or state producing a specific wrong outcome.
- **maintainability** (duplication, dead code, reuse, altitude) → `cost`: something counted. Copies removed, queries or bytes saved per request, files that must now change together. "Harder to maintain" is not a cost; "the same narrowing is written 11 times and 3 already disagree" is.

Requiring a `failure_scenario` on every finding is the trap this replaces. Nothing goes wrong when a helper exists 11 times, so a single mandatory failure field makes real cleanup findings unfileable: the agent either invents a scenario or drops the finding at the completeness gate. In practice a review skill carrying a 12-bullet reuse checklist still reported none of an 11-copy drift, a 3x duplicated SELECT list, or a 6-view duplicated page shell, because none of them could produce a failure scenario to pass the gate.

**Incomplete findings are rejected.** If an agent can't fill the fields, it either needs to investigate more or the finding isn't actionable. Reject on the wrong impact field and you delete the cleanup half of the review.

Low-priority findings are summarized by category (no individual table entries) to keep the report scannable.

## Severity Definitions

| Level | Label | Criteria | Action |
|-|-|-|-|
| BLOCK | Critical | Exploitable security vuln, data loss risk, broken core functionality | Fix before merge |
| WARN | High | Missing error handling on critical path, N+1 on hot path, broken contract, auth gap | Fix this sprint |
| WARN | Medium | Dead code, missing types on public API, duplication, modernization with clear benefit | Fix when touching file |
| INFO | Low | Style, naming, minor modernization | Optional cleanup |

## Agent Output Constraint

Include this in every agent prompt to enforce the format:

```
OUTPUT RULES:
- Final response under 3000 characters
- List findings, not your reasoning process
- Every finding: File:Line | Current Code | Proposed Fix | Why | Intent Ruled Out | Impact
- Impact is failure_scenario (correctness) or cost (maintainability), never both, never neither.
  Do NOT invent a failure_scenario for a duplication finding so it passes the gate; count the cost
- If you can't fill the fields, investigate more or drop the finding
- Intent Ruled Out: name the evidence that this is not deliberate (an adjacent comment, a
  sibling doing the same, a rule or allowlist). If you cannot find it, say intent-unverified
  instead of asserting a defect
- Group by severity: Critical first, then High, Medium
- Do not list Low-severity items individually: summarize count by category
- End with: "FINDINGS: X critical, X high, X medium, X low"
```

## Verifier Output Constraint

The verify stage returns a verdict per candidate, not a rewritten finding. Include this in the verifier prompt, and pick the closing line to match the run's effort level (see `skill-scaffold.md` "Verify calibration"):

```
For the candidate below, return exactly one verdict:
- CONFIRMED: name the inputs or state that trigger it and the wrong output or
  crash. Quote the line.
- PLAUSIBLE: the mechanism is real, the trigger is uncertain. State what would
  confirm it.
- REFUTED: factually wrong or guarded elsewhere. Quote the line that proves it.

Trace the chain from the source yourself. Do not accept the finder's reasoning
as evidence for its own finding.

[strict runs]  When you cannot construct the failure, return REFUTED.
[recall runs]  When you cannot construct the failure but the mechanism is real
               and the state is realistic, return PLAUSIBLE. Reserve REFUTED
               for what you can disprove from the code.
```

A verifier that returns prose instead of a verdict has not verified anything, and a report that lists only what survived hides how much was thrown away. Carry the refuted count into the report header.

