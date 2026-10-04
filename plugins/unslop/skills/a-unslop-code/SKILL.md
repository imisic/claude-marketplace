---
name: a-unslop-code
description: >-
  Finds what makes source code read as AI-written and points you at the parts that actually
  ship bugs. Sorts every tell into three buckets and fixes them in that order: bugs
  (swallowed errors, a made-up API, a left-in "rest of the code" stub), substance
  (tutorial-shaped boilerplate, over-engineering, code that ignores the surrounding repo),
  and cosmetic (emoji in source, a comment narrating the obvious, a generic process_data
  name, chat text pasted into a file). Ships a scanner for the surface tells and says plainly
  that the loudest ones are structural and need a compiler or a human. Use when writing,
  generating, reviewing, refactoring, or auditing code, and when the user says it "looks
  AI-written," "reads like a tutorial," "is too generic," or "de-slop this." Trigger even
  if "AI tell" is never said.
---

# a-unslop-code

Part of the unslop family (see `a-unslop-text`, `a-unslop-ui`). Same shape: an auto-trigger,
a Build mode and an Audit mode, a scanner that gates on a high-severity exit code, and an
`unslop-ignore` line escape. This one is about code.

**What it is not.** It does not write good code and it has no house style. It removes the
surface cues that read as machine-generated, and it points at the deeper tells that ship
bugs, the ones no scanner catches. Whether the code is correct and right for the problem
is still your call.

## Sort every tell before you fix it

One question sets the order of work: is the code wrong, wrong for the job, or does it just
look machine-made?

- **Bug.** A bare `except` eats the failure you needed. A made-up API will not run. A
  `// rest of your code` stub means the file is unfinished. Fix these because the code is
  broken, the same as any bug, whether or not anyone suspected AI.
- **Substance.** Not a local bug, wrong for the job: tutorial-shaped boilerplate, an
  abstraction with one caller, a 2000-line change that should have been 50 because it
  ignored the repo. A compiler passes these; a reader comparing the diff to the
  neighbouring code does not.
- **Cosmetic.** The chat voice leaking into the file: emoji, a comment that restates the
  next line, a `process_data` doing eleven things, pasted "Good catch!" text. Worth
  removing, but nothing breaks if one survives.

The ranking behind this is blunt: the structural tells (tutorial shape, made-up APIs) lead
by a wide margin, and the cosmetic ones people argue about sit far down. So the surface
scan is the cheap part, not the job. A clean scan is not clean code.

## How it fits your setup

If your project already has house rules for substance (smallest code that solves the
problem, no abstraction for single-use code, surgical changes, comment the why not the
what, no commented-out code, no v2/v3 files, remove orphaned imports), this skill does not
restate them. It is the audit layer that catches a violation of them, plus the scanner for
the cosmetic tells. If no-emoji and no-em-dash are already house rules for you, the scanner
flags emoji in source on top of that.

## Build mode

Most "looks AI-written" output is an under-specified prompt, not a style problem. The
average of public code is the tutorial. Before generating, set three things:

- **The surrounding code.** Give the model the file it will sit beside, the nearest sibling
  that does something similar, and how the repo handles errors, logging, and naming. This
  one input does more than the rest combined. The single most repeated fix in the data was
  "make it follow the existing code instead of guessing the average."
- **The real requirement.** What the code has to do, including the failure modes and the
  real integration, not the demo. A vague ask gets the sample-app shape: one page, dummy
  data, no backend.
- **Calls that exist.** Generated code invents plausible APIs. Plan to run it and check
  every import and method against real docs.

`references/fitting-the-codebase.md` is the method.

## Audit mode

Order matters, because the scanner is blind to the worst tell.

1. **Run what only code lets you run.** Code can be executed, and that is the strongest
   tool you have. Build it, type-check it, lint it, resolve every import and call against
   real docs. This is how the made-up API surfaces, and no regex sees it. Python:
   `py_compile`, `ruff` or `pyflakes`, `mypy`, plus a real import. JS/TS: `tsc --noEmit`,
   `eslint`, `node --check`. Go: `go build ./...` and `go vet`. Rust: `cargo check` and
   `cargo clippy`. If it will not build, or a call resolves to nothing, fix that first.
2. **Run the scanner** for the surface tells.

   ```bash
   python3 scripts/unslop_code_scan.py <path>                 # report + slop score
   python3 scripts/unslop_code_scan.py <path> --severity high # strongest only
   python3 scripts/unslop_code_scan.py <path> --json          # for CI
   ```

   It covers Python, JS/TS, Java, Go, Rust, Ruby, PHP, C/C++, C#, and more. Each finding
   carries a class (bug or cosmetic) and a fix. Exit code is the high count, so CI can gate
   on it. Fix every bug-class finding regardless of severity.
3. **Read the diff** for what neither step sees: tutorial shape, over-engineering, and
   whether the code matches the repo. These are the loudest tells and they need your eyes.

**Escape hatch.** A line with `unslop-ignore` is skipped, for a real decision (a broad
catch at a boundary, an emoji in a CLI banner).

## The over-correction trap

Told to "write clean code" or "make this not look AI," a model over-produces: a null check
for a case that cannot happen, a type on every local, a comment on every block, a factory
for a thing with one caller. That is performed seniority, and it reads as AI for the same
reason boilerplate does. The cure is the same anchor as the rest: match the level the
surrounding code operates at. Add nothing the neighbouring code would not have.

## Fixing well

Renaming `process_data` to `processDataFunction` is a different tell, not a fix. Name it for
what it does, the way the repo names things. Code has little aesthetic room: the question is
almost always "is it correct, and does it match this project," not "which look do I want."

## Reporting

Lead with the verdict and the single highest-impact change. Findings by priority with
file:line and the fix, bug-class first. Close with the slop score and a reminder that the
structural tells still need a compiler or a human.

## Credits

The tell catalog and its ranking come from the vibecoded-design-tells research by
JCarterJohnson (https://github.com/JCarterJohnson/vibecoded-design-tells, MIT), which mined
Reddit for what developers name as AI-code giveaways. This skill rewrites that material into
the unslop family: one skill per surface, a shared bug/substance/cosmetic split as its spine,
and a shared Build/Audit shape with the text and ui skills. `scripts/unslop_code_scan.py` is
an adapted fork of that project's scanner (MIT); the credit is in its header.
