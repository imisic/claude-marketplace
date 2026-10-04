# Writing in a chosen voice

This file does not hand you a voice to copy. Any fixed style, repeated, becomes the next default and the next tell. The smooth corporate voice was the 2024 default; the clipped, lowercase, swear-to-seem-real voice is the 2026 over-correction, and it reads as a machine trying not to look like a machine just as fast. So this is a way to decide what the writing is, not a thing to imitate.

The goal is one outcome: prose where every choice has a reason specific to this piece. That is the one property a default can never have.

## Pin a register, then a speaker

A register sets what "plain" means and what counts as a tell. Decide which one the piece is in before anything else:

- **A, casual.** Texts, DMs, personal posts. Contractions, fragments, slang, dropped subjects.
- **B, conversational-professional** (work email, Slack, updates, changelogs, most chat replies): plain, direct, contractions, light warmth, no throat-clearing.
- **C, expository** (essays, READMEs, blog posts, deep-dive docs): a clear argument, varied rhythm, a point of view, paragraphs over bullets. Where most unslopping happens.
- **D, formal** (specs, briefs, ADRs, research docs): structured, sourced, impersonal. Formality here is correct, not a tell.

The register is the guard against over-correcting. A fragment is native in A and a tell in D. A contraction is right in A through C and wrong in D. A `lol` is voice in A and costume in C. A research doc or ADR is mostly C and D; a first-person blog is mostly C with a named speaker; chat replies are B. Same banned list, different register on top.

Then a speaker inside the register. For a project that already has a voice, anchor to it. If you must choose, pick a named direction (plain-technical, blunt operator, dry and concrete) over "professional and engaging," which means nothing.

## The claim

Before the body, state the one thing the piece asserts, in a sentence. AI prose reads as empty because it is fluent with nothing to say. If you cannot write the claim, there is nothing to write yet. Every paragraph earns its place against that claim; if one could be cut with nothing lost, cut it. Say it with less: cut the paragraph that restates the claim instead of extending it.

## Structure follows the argument

The order is set by what the reader needs first, not a template. That is how you avoid the intro / three-even-body-paragraphs / "in conclusion" skeleton: the shape appears when structure is chosen by default. Most pieces do not need a summary at the end. Reserve bullets for list-like content; argument lives in paragraphs.

## Rhythm and diction

Vary sentence length on purpose. Use the plain word: `use` not `utilize`, `look at` not `delve into`. Cut the antithesis cadence and the throat-clearing opener. The point goes in the first sentence, not after a warm-up.

## The over-correction trap (the thing to actually watch)

Told to "sound less like AI," a model swings the other way: staccato three-word fragments on every beat, forced lowercase, a `here's the thing` cold open, a swear dropped in to seem casual, every natural dash replaced by an ellipsis or a contorted sentence. People clock that just as fast. Evenness is the tell whichever length it lands on; all-short is as mechanical as all-medium. The fix is a real register held consistently, not the absence of voice dressed up as casual.

## A terse register is a choice, not a tell

If your default for chat and most docs is terse (short sentences, fragments for punch, the verdict first, no preamble), that can be a deliberate register, so the rhythm-variation note does not have to flag it. Do not "fix" a chosen terse register by padding it back toward the median, and do not over-correct it into performative fragments either. Hold the register; vary length within it when a thought needs room.

## The escape hatch

A register or word chosen on purpose is not a tell. A formal ADR is formal. A verbatim citation reproduces external wording. A section name has to match a source. When a flagged form is a real decision, keep it and mark the line `unslop-ignore` (or `voice-allow`, a variant some docs already use), so the audit stays honest.

## Clarity wins

If a rule here produces a sentence that reads worse than the alternative, the rule loses. Rewrite the sentence and, if the rule keeps fighting clarity, change the rule (`tells.md` plus the scanner). The rules exist to make writing better, not to constrain it when they fight clarity.

## The one-line version

Pin the register, state the claim in a sentence, then write the way that speaker talks and read it back. The skill removes the tells; this is how you replace them with something chosen.
