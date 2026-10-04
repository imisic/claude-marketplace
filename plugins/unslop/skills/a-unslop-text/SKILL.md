---
name: a-unslop-text
description: "Remove generic, padded or machine-written phrasing while keeping the author's voice. Use when writing, editing, reviewing or auditing substantive reader-facing prose: docs, READMEs, blog posts, emails, commit bodies and site copy. Also trigger for \"sounds like AI\", \"de-slop this\", \"make it sound like me\" or \"is this slop\". Apply during prose work even when AI is not mentioned. Includes a style scanner and a method for building a voice profile from real writing. Checks style, not authorship. Skip tiny labels, routine code comments and one-line mechanical edits."
---

# a-unslop-text

Read this first, because the common misunderstanding sinks the whole thing.

**This skill does not write well for you, and it does not impose a single house voice.** It does two narrow things. It removes the specific cues that make text read as machine-written, and where the text reads as AI because nobody chose a voice, it forces a deliberate, register-appropriate one. The argument and what you actually want to say are still yours. A guardrail is not a writer.

Most of the work is the first thing, and most of the first thing is mechanical. The em dash becomes a comma or a period. `delve into` becomes `look at`. The sycophantic opener gets cut. The `as an AI` boilerplate gets deleted. Those are not style calls; there is no voice to invent. Lead with the plain fix. Reserve the deliberate-voice work for the stylistic choices.

## How this fits alongside a house style guide

This is the depth layer, not the floor. If you already have an always-on style floor (a house style doc, a project CLAUDE.md rule: no em dash, no bookending, contractions, match length to the question), that floor still applies whether or not this skill loaded. This skill owns the full banned-vocabulary catalog and the scanner, so a single list stays canonical instead of drifting across every project that keeps its own copy.

If you also have a write-time hook that blocks the em dash on public-facing content, that hook and this skill's scanner share the same rule and neither re-derives it: the hook stops it at write time, the scanner catches it at audit time everywhere else.

Per-project overlays sit on top of this layer, not under it: a project's own terminology, provenance rules, and register choice, or a first-person brand voice a project already keeps. Those overlays describe the project; this skill describes the prose.

## The trap to avoid

The failure mode of every anti-AI-writing effort is swapping one default register for another. The smooth corporate voice (the em dash, `delve`, a bulleted list for everything, a tidy "in conclusion") was the 2024 default. The 2026 over-correction is its mirror: staccato three-word fragments, forced lowercase, a `here's the thing` cold open, a swear bolted on, fake typos to beat a detector. Readers clock the second just as fast. Treat the over-corrected register as its own tell. The fix for a dash is a comma in a sentence you would actually write, not an ellipsis and not a contortion around the gap. See `references/writing-with-intent.md`.

## Not an AI detector

Detectors return a probability and are wrong often enough to ruin a real writer's day. This skill does not guess who wrote something. It finds configured style violations and advisory patterns, removes them, and then asks for a human read on rhythm, substance, and voice. It adds a deterministic scanner you can run in CI and an explicit warning against the over-corrected register.

## Build mode

Most "sounds like AI" outcomes are a specification problem, not a wording one. An unspecified prompt gets the model's median voice. So before drafting anything for a reader, pin the register (A casual / B conversational-professional / C expository / D formal), then a speaker inside it, then state the claim in a sentence. `references/writing-with-intent.md` is the method. Then write, avoiding the tells in `references/tells.md`.

The ban list alone gets you to clean, not to you. So before drafting under a real person's byline, check whether they have a voice profile (moves extracted from their real pre-AI writing, a register dial, a language ceiling); ask if you don't know. If they do, the speaker step is already answered: load the profile and hold it. If they don't, do not silently produce generic text under their name. Offer the choice: build one now with them (about an hour following `references/voice-profile.md`, and it moves a draft further toward its author than everything else in this skill combined), or proceed and say plainly the result will read as clean, not as them. Keep any resulting profile private; the method is shareable, the output is personal data.

If you already have a default register for chat and most docs (say, terse: verdict first, short sentences, fragments for punch, no preamble), that is a chosen register, not the model's default, so hold it. Do not pad it back toward the median, and do not over-correct it into performative fragments.

## Audit mode

When reviewing or cleaning existing prose, or on "does this sound like AI / de-slop this / make it sound like me," run the scanner first, then fix in priority order.

```bash
python3 scripts/unslop_text_scan.py <path>                 # report + slop score
python3 scripts/unslop_text_scan.py <path> --severity high # only the hard bans (gated tier)
python3 scripts/unslop_text_scan.py <path> --json          # for CI
```

It scans `.md .markdown .mdx .txt .rst .html`, reports each finding with file, line, the matched text, and the fix, plus a configured-style score and a density per 1,000 authored words (quoted lines are excluded from the denominator, so a piece that is mostly quotation is not diluted). Exit code is `1` when any high-severity violation exists, `0` when none exists, and `2` for invalid input, so CI can gate on it.

Some rules are frequency-sensitive and stay silent until a word appears twice in the same file, because one register-appropriate `robust` is not a signal and four of them are. `references/tells.md` marks which rules work that way.

Be honest about what the scanner is: a lexical style filter. It catches the em dash, the high-signal diction, the antithesis cadence, the formatting tics. It cannot judge authorship, factual value, originality, uniform rhythm, or whether a paragraph earns its space. A clean scan means the configured lexical layer is clean, not that the writing reads as a person. After every scan, run the structural and concision pass in `references/tells.md`.

For the concision pass, test every paragraph and sentence: keep it only if it adds a claim, evidence, a decision, an exception, necessary context, or a reader action. Cut it when removing it changes nothing. Do not shorten away a requirement, a factual caveat, or a source.

**Escape hatch.** A line containing `unslop-ignore` or `voice-allow` is skipped, for a tell used on purpose (a verbatim citation, a section name, a deliberate register). Use it sparingly; if you reach for it more than once or twice per pass, the rule probably needs adjusting.

**Fixing well.** Do not fix `delve into` by swapping in `dive into`, which is another tell. Use the plain verb you would actually say. A fix that introduces the over-corrected register (choppy fragments, fake typos) is not a fix.

## What it does not flag

Grounded in what readers actually cite, not a keyword pass. Lone `however`, `thus`, a single register-appropriate `crucial`, a real thematic-break `---`: these are usually the writer's own prose, not a tell. The scanner leaves them alone (the DO NOT CHASE section of `references/tells.md`). Over-flagging trains people to ignore the tool, so the scanner stays narrow.

## Reporting an audit

Lead with the verdict and the single highest-impact change. Then findings by priority with file:line and the fix. Close with the configured-style score and the top three changes, reported as a style measurement and not as a claim about who wrote the text. Plain and specific. The goal is prose that reads like one person who meant it, which is the one thing the scanner cannot do for them.

## Credits

The over-correction framing, the register model, and the scanner design are adapted from the vibecoded-design-tells research by JCarterJohnson (https://github.com/JCarterJohnson/vibecoded-design-tells, MIT). The banned-vocabulary list and its tiers here are this skill's own merge of several style guides into one canonical source; the shape and the over-correction idea come from that project. `scripts/unslop_text_scan.py` is an adapted fork of its text scanner (MIT); the credit is in its header.
