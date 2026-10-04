# Making code fit the repo

Code reads as AI because the model reaches for the most common pattern in its training set instead of the one your project uses. Any fixed style applied by default is just a different average. So this is how to make code fit the project, which is the property that stops it reading as machine-made.

Code has little aesthetic room. The question is almost never which look you want; it is whether the code is correct and matches what the project already does. Fit is the standard, not taste.

## Feed it the repo

The input that does the most work is the repo itself. Before generating, give the model the file it will sit beside, the nearest sibling that already does something similar, and the conventions (how errors are handled, how things log, how modules are structured, the naming). A change that follows the patterns is small and invisible. One that ignores them is the 2000-line change that should have been 50.

On a brand-new project with no precedent, make one deliberate decision and write it down (a short conventions note the model can read), rather than letting each file invent its own. The tell is not any one pattern; it is the absence of a chosen one.

## State the requirement, not the demo

Name the real inputs, the real failure modes, the real integration before generating. Tutorial-shaped code is the loudest tell because the model falls back to the sample-app shape when the ask is vague. If you cannot state the requirement, you will get the demo.

## Run what only code lets you run

The tells that bite are the ones no scanner sees, and code has one advantage prose and design do not: you can execute it. Two checks catch most:
- Does it call anything that does not exist? Build it, type-check it, resolve every import and method against real docs, not the model's confidence. `tsc --noEmit` and `eslint`, `mypy` and a real import, `go build ./...` and `go vet`, `cargo check` and `cargo clippy`.
- Does it match how this repo does things? Read the diff against the neighbouring code. A new logging style or a new structure mid-file is the mismatch tell.

If you cannot explain a line the model wrote, do not ship it.

## Do not over-correct

"Write clean code" or "do not look AI" backfires into over-production: checks for cases that cannot happen, a type on every local, a comment on every block, a layer for one caller. That is performed seniority, and it reads as AI for the same reason boilerplate does. Match the level the surrounding code operates at. Add nothing the neighbouring code would not have.

## Escape hatch

A pattern chosen on purpose is not a tell. A project may want a broad catch at a boundary, an emoji in a CLI banner, a `process_data` step in a throwaway script. The skill flags unchosen defaults, not banned constructs. Mark a real decision `unslop-ignore`.

## One line

Feed the model the surrounding code and tell it to match it, then run the result and check every call is real. The scanner removes the surface tells; this removes the ones that ship bugs.
