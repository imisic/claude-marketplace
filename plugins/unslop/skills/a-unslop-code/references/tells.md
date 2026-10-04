# AI-code tells: the catalog

The human-readable view. The scanner (`scripts/unslop_code_scan.py`) is the enforced layer for the surface tells; this file explains them and lists the ones a regex cannot see. The ranking and the shares come from the research credited in `SKILL.md`; the structure and prose here are this skill's.

Sort by class first, not by whether a regex can see it. A bug means the code is wrong. A substance problem means it is wrong for the job. A cosmetic just looks machine-made. Fix bugs and substance because the code is broken or wrong-for-the-job. Strip cosmetics because they read as AI. A clean cosmetic pass is not a substitute for the other two.

## The loud ones (no regex sees these)

The research is blunt: the tells people name most are about shape, and a scanner is blind to all of them. These need a compiler or your eyes.

- **Tutorial-shaped boilerplate** (the top tell, ~19% verified). Substance. The model emits the average of public code: the sample app, dummy data, no real backend. Fix: build the real thing against the real requirement. The scanner's dummy-data markers (`lorem ipsum`, `YOUR_API_KEY`, `John Doe`) are a weak proxy only.
- **Made-up APIs and libraries** (~11%). Bug, the one that bites in production. A plausible call to something that does not exist, or logic that reads right and runs wrong. Only building, type-checking, running, or resolving the import catches it. Run it.
- **Over-engineering** (~8%). Substance. Layers and abstractions for a simple task. Every extra layer is more surface for a bug. Ask whether an `if`/`else` would do; delete the abstraction with one caller.
- **Ignoring the surrounding repo** (~4%). Substance, and the spine of the fix. Code that works in isolation and invents a new logging style, a new error pattern, a new structure mid-file. The 2000-line change that should have been 50. Fix: feed the model the existing code and match it.
- **Mixed skill level** (~2%). Substance. Advanced patterns next to beginner mistakes, and no one can explain it because no single person wrote it. If you cannot explain a line, do not ship it.
- **Too clean, no human mess** (weak, contested). A meta-signal: passes the linter, no quirks, logic still wrong. For the reviewer only: a clean surface does not end the review.

## The surface ones (the scanner catches these)

Each tagged bug or cosmetic.

- **Swallowed errors** (bug). A bare `except:`, `except Exception: pass`, an empty `catch {}`, an empty Go `if err != nil {}`. Eats the failure you needed. Fix: catch the specific case, handle it, let the unexpected surface. Rust `.unwrap()`/`let _ =` and Go's multi-line empty block are a human pass (too overloaded to regex without noise).
- **Placeholder stubs** (bug). `// rest of your code`, `# your logic here`, `// implementation goes here`, `# TODO: implement`. The file is unfinished. Fix: write the real code.
- **Emoji in source** (cosmetic, the highest-precision cosmetic tell). Any emoji in a comment, string, or log. Fix: remove it. A real CLI checkmark chosen on purpose gets `unslop-ignore`.
- **Narrating comments** (cosmetic). A comment that restates the next line (`# increment i`) or steps through (`# Step 1`, `# Now we...`). Fix: comment why, not what.
- **Generic placeholder names** (cosmetic, often hiding a substance problem). `process_data`, `handle_data`, `do_stuff`, `do_something`. A `process_data` that does eleven things is the canonical case. Fix: name it for its job; if you cannot, it does too much.
- **Pasted chat artifacts** (cosmetic). A code fence inside a source file, `Here's the updated code`, `As an AI`, `Good catch!`, a trailing `Note:`/`Remember:` preamble. Fix: delete the assistant's voice.
- **Whole-sentence identifiers** (cosmetic, weak). `getUserDataFromApiResponseHandler`. The model pads names to self-document. Fix: trim to the precise noun or verb. Descriptive is good; a paragraph is not.

## Language coverage

A tell in a comment or string looks the same in every language, so emoji, stubs, narrating comments, and chat artifacts are caught anywhere. Syntax-keyed tells are uneven by design, because forcing a regex past what it does reliably costs precision:
- Swallowed errors: matched for Python, JS/TS, Java, C#, Ruby try/catch and Go's single-line empty error block. Rust `.unwrap()`/`let _ =` and Go's `_`-discard are a hand read.
- Generic names: keyed on `def`/`function`/`func`/`fn`/`fun`/`sub`.
- An over-broad-but-handled `catch (Exception)` that logs and moves on is not flagged; it can be a real boundary.

If your language is outside that set, read for swallowed errors and generic names by hand.

## Do not chase (cleared by the research)

Three popular complaints did not survive verification. The scanner leaves them alone:
- Left-in debug logging (`print`/`console.log`, chatty `Successfully...` lines): the tagged cases were workflow opinions, not code. Bare logging is not flagged.
- Reinventing the wheel: mostly misread as duplication or made-up libraries.
- Over-defensive validation: half the complaints were the opposite (no validation at all). Do not flag it in review. Do still avoid producing it (see the over-correction trap in `SKILL.md`).

Flag what the research supports, at the weight it supports. Over-flagging trains people to ignore the tool.
