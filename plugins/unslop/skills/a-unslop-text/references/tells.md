# The prose tells: the catalog

This is the human-readable view of the vocabulary and patterns in `scripts/unslop_text_scan.py`. The documentation and the implementation must agree. Treat any mismatch as a defect; neither silently overrides the other.

It merges what used to be several separate per-project banned-word lists, already drifting apart from each other, into one canonical catalog.

Read by tier, not as a flat blocklist. HIGH is a configured violation and gates the scanner's exit code. MEDIUM is advisory and often frequency-sensitive: the scanner stays quiet on a single use and reports the cluster. LOW is weak or contextual. The structural review at the bottom covers rhythm, substance, and concision that no regex can judge, and that is usually the real giveaway.

Every configured term below is in `backticks` so this file scans clean against its own scanner.

## HIGH: gated violations

### The em dash and en dash

`—` and `–`, anywhere, including the HTML entities `&mdash;` / `&ndash;`. This is the one rule flagged even inside quotes, because the rule is simply not to ship one. The fix is a comma, a period, or parentheses, in a sentence you would actually write. Not a colon (people flag that now too) and not a sentence visibly contorted around the gap. If you also run a write-time hook that blocks the em dash on public-facing content, that hook and this scanner share the rule; neither re-derives it. <!-- voice-allow: this line defines the banned dash characters -->

### High-signal vocabulary

Distinctive enough to gate on a single use. Use the plain word or state the concrete behavior.

| Banned | Use instead |
|-|-|
| `delve`, `dive into`, `deep dive`, `let's unpack this`, `unpack the issue` | look at, examine, go through |
| `paradigm` | approach, model |
| `synergy` / `synergies` | describe the specific interaction |
| `holistic` | whole, end-to-end |
| `cutting-edge` | new, the specific capability |
| `game-changer` | what actually changes |
| `unleash` | the specific result |
| `realm`, `tapestry`, `beacon`, `testament`, `myriad`, `plethora` | the plain word; usually cut |
| `best-in-class` | what makes it good |

If one of these seems necessary, the sentence is hedging. Rewrite for the underlying thought.

### Plain-word vocabulary (advisory as a cluster)

These are ordinary formal English. One register-appropriate use is not an authorship signal, so the scanner stays silent until two or more appear in the same file. Prefer the plain word anyway.

| Word | Prefer |
|-|-|
| `leverage` (verb) | use, apply, build on |
| `utilize` / `utilise` | use |
| `robust` | reliable, handles edge cases, or describe the behaviour |
| `comprehensive` | covers the named scope |
| `seamless` | works without an extra step |
| `streamline` | cut steps, simplify |
| `foster` | build, support, grow |
| `empower` | let, give, enable |
| `unlock` | name the result |
| `elevate` | improve, raise |

If your project wants any of these gated on a single use, raise that rule's severity in the scanner rather than keeping a second list somewhere.

### Contextual consultant compounds

The compound gates; the same word used literally does not. `competitive landscape`, `regulatory landscape`, `market landscape`, `navigate the complexities`, `product ecosystem`, `partner ecosystem`, `strategic alignment`, `customer alignment`. Name the competitors, the decision, the products, or the relationship instead.

Literal uses pass and are not tells: `landscape orientation`, a browser navigating to a page, a biological ecosystem, aligning two columns.

### Stacked connective openers

`Moreover`, `Furthermore`, `Additionally`, `Consequently`, `Notably` as a sentence opener. They almost always mean "extending a thought without a new idea." Just start the sentence.

### The antithesis cadence

`it's not just X, it's Y`, `not X, but Y`, `not because X but because Y`. The negate-then-assert shape manufactures profundity for free. If Y is the point, say Y.

### The assistant voice leaking in

`as an AI language model`, a refusal (`I cannot assist`), a `knowledge cutoff` line, `I don't have personal opinions`. Delete every trace before anything ships.

### Sycophancy and the apology reflex

`Great question`, `Certainly!`, `You're absolutely right`, `I'd be happy to`, `happy to help`, `good catch`, and the apology paragraph (`I apologize for the confusion`). Open with the point. When wrong, fix it in one line, no paragraph.

### Filler and preamble patterns

`it's important to note`, `it's worth mentioning`, `in today's [anything]`, `let me break this down`, `Imagine a world where`, `Picture this`, `That said,`, `With that in mind,`, `At the end of the day,`, `needless to say`. State the thing.

### Bookending and trailing offers

`I hope this helps`, `Let me know if you need more`, `Would you like me to`, `is there anything else`, `feel free to reach out`, `hope this email finds you well`, `happy to answer` as a closer. If the answer is done, stop.

### Contextual consultant-speak compounds

The same banned words in their consultant compounds: `competitive landscape`, `regulatory landscape`, `navigate the complexities`, `product ecosystem`, `strategic alignment`, `in alignment`, `cross-product synergies`. The scanner catches the single words; watch for these compounds by eye.

## MEDIUM: use sparingly (advisory)

- **Frequency-sensitive words**, fine once and advisory in a cluster: `crucial`, `vital`, `essential`, `essentially`, `fundamentally`, `various`, `versatile`, `significant`, `genuinely`, `nuance`, `meticulous`, `showcase`, `straightforward`, `precisely`, `dramatically`, `incredibly`, `particularly`, `ultimately`. The scanner reports them only when two or more appear in one file. Keep at most one per piece.
- **Softeners** that undercut an instruction: `simply run X`, `just click Y`. "Run X" is stronger and does not imply it is trivial.
- **Bolded lead-in labels**: `**Word:**` then a sentence. Chat formatting, not prose. Reserve bold for real terms of art or warnings.
- **Listicle scaffolding**: `5 ways to`, `7 signs`, `3 reasons`. Write prose; reserve bullets for list-like content.
- **Decorative emoji** as a bullet, an icon, or in a heading. Banned unless the user used emoji first in the same conversation. An emoji inside a sentence where a person would use one is fine.
- **The `In conclusion` / `In summary` closer**. End on a real last point.
- **Hedging when you have a view**: `you might want to consider`, `it may be worth`, `perhaps`, `on one hand ... on the other`, `it depends`. Take a position.
- **Marketing hype**: `revolutionary`, `transformative`, `supercharge`, `to the next level`, `say goodbye to`, `look no further`.
- **Literary/native flourish (byline mismatch)**: `whilst`, `amongst`, `endeavour`, `ascertain`, `elucidate`, `quintessential`, `notwithstanding`, `henceforth`, `hitherto`, `whereby`, `thereby`, `wherein`, `albeit`, `one might`. Not slop in general English. But when the named author's real register is plainer (a non-native writer, a terse operator), grammatically perfect literary vocabulary outs the text as ghostwritten. Set a language ceiling in your own voice profile (build it via `references/voice-profile.md`) and use the everyday word.

## LOW: weak or contextual (advisory)

- **Inflated generic diction**: `facilitate`, `paramount`, `pivotal`, `multifaceted`, `intricacies`. Prefer the plain word.
- **Work-announcement preambles**: `Let me take a look`, `I'll start by`, `Here's a breakdown of`. Do the thing; the reader sees the result.
- **Fake-relatability openers**: `Honestly,`, `Look, I get it`, `Let's be real`.

## DO NOT CHASE (deliberately not flagged)

These match a keyword pass but are almost always the writer's own ordinary prose, not a tell. The scanner does not flag them, and you should not either:

- `however`, `thus`, `hence` as normal connectives. A lone one is just a connective.
- `when it comes to`, a single `crucial`, or a single `comprehensive` in a long piece where it fits the register.
- Technical uses such as `unpack a tuple`, `navigate to the next page`, `landscape orientation`. The scanner gates the rhetorical use, not the literal operation.
- A horizontal rule (`---`) used as a real thematic break.

Flagging these trains people to ignore the tool. The DO-NOT-CHASE line is as load-bearing as the bans.

## STRUCTURAL (human pass: the scanner is blind here)

These are named as often as the mechanical tells and no regex catches them. Read the draft and check by ear.

- **Uniform rhythm.** Sentences of similar length and shape, evenly paced. The evenness is the tell. Vary length on purpose; let one run long and the next stop short.
- **Rhythmic triads.** Three items, or three same-structure sentences in a row, just to wrap a paragraph with a bow. A natural list of three is fine; a rhetorical one is not. Vary the count.
- **Sycophancy as tone.** Reflexive agreement, no position. Disagree when you disagree.
- **Saying nothing at length.** Fluent, grammatical, no claim. If a paragraph could be cut with nothing lost, cut it.
- **Low substance per word.** Each paragraph should add a claim, evidence, a decision, an exception, necessary context, or a reader action. Cut setup, repeated conclusions, process narration, and examples that do not change the point. Keep requirements and source caveats even when they run long.
- **Same paragraph openings.** Don't start every paragraph the same way. Starting three or more with `This` is the common version.
- **The ". That's [adjective]." tic.** "Resolution times dropped 82%. That's impressive." Fine once; at three it is a pattern. Fold into the previous sentence or let the number speak.
- **"Think of it as / like" as an analogy launcher.** Make the analogy directly: "DNS is your network's phone book," not "Think of DNS like a phone book."
- **Setup paragraph before the punch.** If the strongest line is buried after scene-setting, lead with it.
- **Overdone voice mimicry.** A draft that strings the author's signature phrases into every paragraph is an impression, not a voice. Cap borrowed phrases at one or two per piece; moves carry a voice, phrases are incidental. See `references/voice-profile.md`.

### One exemption, important

A writer may default to terse prose: short sentences, fragments for emphasis, blunt verdicts, no warm-up. That is a chosen register (see `writing-with-intent.md`), not the model's default, so it is **not** a tell and the "vary your rhythm" note does not apply to it. The over-correction trap is the opposite failure: prose straining to look un-AI (staccato three-word fragments on every beat, forced lowercase, a `Honestly` cold open, a swear bolted on, conspicuous dash-avoidance). That strain is its own tell. The fix is a real voice held consistently, not a costume of "not-AI."

A concrete over-correction case, from de-slopping a launch post for a forum audience. The rewrite stripped every sentence to a subject-less fragment: `For people who've never opened a terminal. Goes from installing to a website online. Covers X, Y, Z.` That reads exactly as fake as the slop it replaced. Reader-facing copy needs normal connective tissue, the way a person actually types: `It's aimed at people who don't code. Takes you from installing the tool all the way to putting a real website online.` Fragments belong in a terse chat or working-doc register, not in social copy meant to pass as a person posting. Register decides, and the register for a public post is not the register for your own notes.
