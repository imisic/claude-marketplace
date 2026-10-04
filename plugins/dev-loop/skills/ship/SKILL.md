---
name: ship
description: Review changed files with your project's review skill, fix findings, and commit; deploy with --deploy.
disable-model-invocation: true
---

# Ship Pipeline

Review, fix, and commit in one flow, pausing after the review so nothing gets fixed or committed until you have seen what was found.

This skill assumes the project already has a review skill (the kind `a-review-optimizer`, in the dev-workflow-forge plugin, generates: a project-tuned `*-review` skill in `.claude/skills/`). If none exists, say so and suggest running `a-review-optimizer` first.

## Flags

| Flag | Effect |
|-|-|
| `--no-fix` | Skip the fix phase, go review -> commit |
| `--no-commit` | Stop after the fix phase |
| `--deploy` | Run the project's deploy step after commit, if one exists |
| Other flags | Pass through to the project's review skill (e.g. `--full`, `--debt`, `--security-only`) |

Default review scope is changed files only.

## Phase 1: Review

Invoke the project's review skill with all pass-through flags (default: changed files only).

Wait for it to finish. Capture the full report.

## Gate 1: Review Results

Show a compact summary of findings by severity (Critical/High/Medium/Low counts).

- **Zero findings:** print "Clean review. Skipping fix phase." and jump to Phase 3.
- **Findings exist:** ask the user: "Fix these? (yes / skip to commit / abort)"
  - **yes** -> Phase 2
  - **skip to commit** -> Phase 3
  - **abort** -> stop, print "Aborted."

If `--no-fix` was passed, skip this gate and go straight to Phase 3.

## Phase 2: Fix

Feed the full review report to `/fix` (batch mode; it parses the severity markers and file:line table on its own).

Wait for fixes to complete before moving on.

## Phase 3: Commit

Skip if `--no-commit` was passed. Print "Stopped after fix phase." and end.

Otherwise invoke `/commit`.

## Phase 4: Suggest Deploy

After a successful commit:

- If `--deploy` was passed and the project has a deploy step (a build script, a deploy command, a CI trigger): run it.
- If `--deploy` was passed and no deploy step exists: say so plainly; don't invent one.
- Otherwise: print a reminder that the project's own deploy step (if any) is the next manual action.

## Questions along the way

Do not run a round of questions of your own at the end. The review and fix stages each asked theirs, and asking again makes the user answer twice. Ask only when the commit step itself surfaces something neither earlier stage could have seen, and ask before committing, not after. Otherwise carry the earlier stages' answers into the final report, with one line each on what review and fix settled, so the chain's report still records the decisions.

Deploy mechanics are project-specific (a build script, cPanel upload, a container push, a CI pipeline) and out of scope for this skill; it only triggers whatever the project already defines.
