# Build a voice profile from your own writing

**This is a method, not a template.** You do not fill this file in. Following the steps below produces a *separate* file, your voice profile, which you keep in your own private config and point the skill at. This method file is generic and shareable; the profile it produces is personal data, so keep it private and never ship it in a public bundle.

The ban catalog has a ceiling. Remove every tell from a draft and you get text that is clean, correct, and still nobody's: the model's median with the fingerprints wiped. What makes text read as a specific person was never the absence of `delve`; it is a set of habits the author does not know they have. This file is the method for extracting those habits from your real writing and turning them into a profile the Build mode can load. An hour with your own sent emails buys more authenticity than any banned-word list.

## Step 1: gather real samples

Collect 10 to 15 pieces you actually wrote, before AI assistants were involved, across more than one register: work emails you sent, feedback you gave on someone's work, a doc or spec you wrote alone, chat messages, a post if you have one. Unedited and unpolished beats curated. The typos stay in for now; they carry information for step 6.

Two things matter about the sample set. It must be yours alone (in shared documents, other contributors' sections sneak in; drop anything you did not write yourself). And it should span situations, because the interesting part is what changes between them and what does not.

## Step 2: extract moves, not phrases

A move is a repeatable decision about how you handle a situation in prose. Phrases are what the move leaves behind. Profile the moves; list the phrases only as evidence.

Questions that surface moves, with the kind of answer you are looking for:

- **How do you open?** Position first ("Agree, with one change...") or context first ("Some background before I answer...")? Whichever it is, it is probably consistent, and it is probably the strongest single marker you have.
- **How do you disagree?** Flat contradiction, a softened "not sure this holds because...", a question that carries the objection ("would this survive two concurrent users?")?
- **Do your suggestions travel with their reasons?** Some writers attach a "because" to every proposal; others state the proposal bare and defend it only if challenged.
- **Where does your opinion live?** In the main clause, in a parenthetical aside, in a dry closing fragment?
- **How do you handle uncertainty?** Hedge words, explicit confidence levels, silence until sure?
- **What do you do with numbers?** Some writers reach for a figure wherever one exists; others reach for an adjective.
- **How do you close?** A named owner and a next step, a one-word sign-off, nothing at all?

Write each move as one line with one or two short real examples from your samples. Eight to twelve moves is a full fingerprint; more than that and you are cataloging noise.

## Step 3: map your registers

You are not one voice; you are one identity at different intensities. Map your real destinations (email, chat, docs, posts, specs) onto the A/B/C/D register model in `writing-with-intent.md`, and note what changes between them: where the softeners drop away, where fragments appear, where the wit is allowed out. The profile should say which moves are always on and which belong to one register only.

## Step 4: set a language ceiling

This is the step most people skip and the one that catches the most ghostwriting. The model's natural register is polished, native, faintly literary English. If that is not how you write, every draft published under your name is dressed in someone else's vocabulary, and readers who know you notice even when they cannot say what is off.

State the ceiling explicitly. For a non-native author the effective instruction is: **write in clean C1 English**. Grammar and spelling always correct, but everyday professional vocabulary, main clause first, at most one subordinate clause, no rare idioms a language learner would not use, plain intensity words. Correct is not the same as fancy. For a native author with a plain register, the same idea applies with a different label: cap the vocabulary at how you talk in a meeting, not how you would write an essay.

The scanner's `c2-flourish` rule backs this ceiling from the ban side, but the ceiling belongs in the profile because it is a positive instruction, not a list of exceptions.

## Step 5: signature phrases, capped

List the phrases that recur in your samples. Then cap them: at most one or two per generated piece, and only where they would fall naturally. This anti-parroting rule is load-bearing. A draft that hits four of your signature phrases is an impression of you, which reads worse than a plain draft; the moves carry the voice, the phrases are incidental. (Same logic as the over-correction trap in `tells.md`: an overdone costume is its own tell.)

## Step 6: list what not to copy

Now use the typos. Recurring misspellings, dropped articles, run-on chains, inconsistent capitalization: these are typing artifacts and second-language slips, not voice. The profile should name them explicitly as things never to reproduce, because a model shown your raw samples will otherwise imitate them, and deliberate fake errors are a known over-correction tell. The recognizable signal survives cleanup; the slips do not need to.

## Step 7: set precedence

One line at the end of the profile: the ban catalog (`tells.md` and the scanner) always wins. The profile chooses among what the bans allow; it never licenses a banned form. If one of your real habits collides with a hard ban (plenty of real people close emails with a phrase that is now an assistant tell), the ban wins for generated text, because the reader cannot tell your habit from the machine's.

## The template

```markdown
# <name>'s voice profile

Private. Derived <date> from <n> samples (<kinds>). Never ships in a public bundle.

## Who is speaking
<two or three sentences: role, stance, what they connect when they argue>

## The moves
<8-12 one-liners, each with a short example>

## Register dial
<destination -> register letter + which moves intensify or drop>

## Language ceiling
<e.g. "Write in clean C1 English: ..." with the concrete rules>

## Signature phrases (evidence, not injection)
<the list, then: max 1-2 per piece, never mechanically placed>

## What not to copy
<typing artifacts, normalized away>

## Precedence
tells.md and the scanner always win.
```

## Using it

Wire the profile into the Build mode flow: pin the register per piece as usual, and when the byline is the profile's owner, the speaker step is already answered. Load the profile and hold it. Then audit as always; the scanner catches the bans, and your own read catches whether the person on the page is you.
