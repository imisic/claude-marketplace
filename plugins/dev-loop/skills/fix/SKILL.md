---
name: fix
description: Diagnose and fix a bug, or apply fixes from a review report in severity order.
disable-model-invocation: true
---

# Debug and Fix

Fix bugs and review findings while staying inside the project's own patterns. This skill has no built-in bug catalog for any specific stack; it teaches a method, not a list of known errors, because that list is different for every codebase.

## Input

$ARGUMENTS

## Mode Detection

- If arguments contain severity markers (Critical, High, Medium, Low) or a file:line table: **Batch Mode**
- Otherwise: **Single Bug Mode**

---

## Single Bug Mode

### Step 1: Triage

Understand the symptom before touching code:
- What should happen versus what actually happens?
- When and where does it occur (which input, which environment, which trigger)?
- Ask clarifying questions if the description is ambiguous. Don't guess at reproduction steps.

### Step 2: Trace the Request Through the Architecture

Every stack has some version of this chain; adapt the names to what the project actually uses:

```
Entry point (route, CLI command, event handler, queue consumer)
    |
Dispatch (router, framework middleware, controller)
    |
Business logic (service, use case, domain layer)
    |
Data access (model, repository, query layer)
    |
Presentation (view, template, serializer, response)
```

Read the relevant files along this path, starting from the entry point and following the call chain. If the project has a CLAUDE.md, a rules directory, or an architecture doc, read it first: that's where the actual layer names and boundaries are defined for this specific codebase.

### Step 3: Diagnose

Identify the root cause, not just the symptom. Check neighboring code for the same pattern; a bug caused by a missing cast, a missing null check, or a missing escape often exists in more than one place.

### Step 4: Fix

Apply the fix following the project's own conventions, not a generic default:
- Match the error-handling style already in use (exceptions, result objects, error codes) rather than introducing a new one.
- Match the existing naming, layering, and helper usage. If the project has a validation helper, a response helper, or an escaping helper, use it instead of inlining the logic again.
- If the fix touches a boundary (user input, external API response, file path from a request), re-check it against the project's security rules, not just the immediate bug.

### Step 5: Verify

Sanity-check the changed code:
- Types are correct (respect the language's type system, strict mode, or type hints if the project uses them).
- The fix follows the same pattern used elsewhere in the file/module.
- No new issue was introduced (an off-by-one in the fix, a newly-unhandled edge case, a broken caller).

### After Fixing

1. Explain the root cause in plain terms.
2. Explain what changed and why.
3. Note if the same pattern might exist elsewhere and should be checked.

---

## Batch Mode

For processing review reports, architecture analyses, or tech-debt reports.

### Step 1: Parse the Report

Extract every issue. For each, capture:
- File path and line number
- Severity (Critical / High / Medium / Low)
- Description of what's wrong
- Suggested fix, if the report provides one

### Step 2: Read Affected Files First

Read ALL affected files before changing anything. Understand context before acting; a fix applied file-by-file without seeing the whole picture tends to miss cross-file duplication of the same bug.

### Step 3: Fix in Priority Order

**Critical**: fix one at a time. Show the diff before applying. Verify after each fix.

**High**: batch similar fixes together (e.g. all missing null checks, all missing escapes).

**Medium**: fix if the change is straightforward and low-risk.

**Low**: fix only if the file is already open for a higher-priority issue in the same pass.

### Step 4: Report Results

For each issue in the report, output one line:

```
Fixed:      [file:line] - [what was done]
Skipped:    [file:line] - [why]
Need input: [file:line] - [the question]
```

### Gating Rules

- **BLOCK** on anything the report marks "requires confirmation." Show the proposed change and ask first.
- **BLOCK** on every Critical fix. Always show the diff before applying.
- **SKIP** if the fix instructions are unclear. Ask rather than guess.
- Group related fixes so the diff reads as one coherent change, not a scatter of unrelated edits.
- After a batch, run a sanity check on every changed file (the project's linter, type check or a syntax check) before reporting it fixed.
- If the review report already records the user's answer beside a finding, apply that answer. Do not ask the same question again.

---

## Fix Checklist (Both Modes)

- Root cause identified, not just the symptom patched
- The fix actually addresses that root cause
- No new security issue introduced
- Types/casts correct for the language and its strictness settings
- The project's own patterns followed (not a generic textbook pattern)
- No database or network queries added inside a loop (batch or preload instead)
- No duplicated logic; check whether the same fix already exists as a helper elsewhere

## Workflow Chain

After fixing, suggest running the project's review skill on the changed files to verify the fixes, then `/commit`.

## Closing questions

Before you present the report, turn every `Need input:` line into a short set of choices for the user: each option with what it costs, and your recommendation first. A finding with one right answer is not a question; fix it and say so in a line. If nothing is left open, say "no open items" in one line rather than staying silent.
