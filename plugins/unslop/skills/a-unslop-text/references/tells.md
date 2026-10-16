# The prose tells: the catalog

This is the human-readable view of the vocabulary and patterns in `scripts/unslop_text_scan.py`. The documentation and the implementation must agree. Treat any mismatch as a defect; neither silently overrides the other.

The catalog combines style preferences and sourced review cues. HIGH gates the exit code. MEDIUM and LOW are advisories. These are configured style rules and review prompts, not an authorship test. Thresholds are heuristics, not measured detection accuracy.

Provenance tags distinguish observational sources from owner preferences. [Wikipedia:Signs of AI writing](https://en.wikipedia.org/w/index.php?oldid=1380310647&title=Wikipedia:Signs_of_AI_writing) is the dated reference for Wikipedia tags below. The vocabulary changes over time; [Human-LLM Coevolution: Evidence from Academic Writing](https://aclanthology.org/2025.findings-acl.657/) documents that drift in academic writing. Neither validates this scanner across genres.

## HIGH: gated violations

### The em dash and en dash (house preference)

Unicode `U+2014` and `U+2013`, including the HTML entities `&mdash;` / `&ndash;`, are banned even inside quotes. The fix is a comma, a period, parentheses, or a colon when it fits the sentence. Avoid contortions around the gap. If a project also uses a write-time dash hook, the scanner catches the same rule at audit time. This is a house preference, not a detection signal.

### High-signal vocabulary (house preference)

These configured phrases gate on a single use. The earlier-era words are separated below because their generic severity changed.

| Configured word or phrase | Prefer |
|-|-|
| `dive into`, `let's dive`, `dive deeper`, `let's unpack this`, `unpack the issue` | look at, examine, go through |
| `synergy` / `synergies` | describe the specific interaction |
| `holistic` | whole, end-to-end |
| `cutting-edge` | new, the specific capability |
| `game-changer` | what actually changes |
| `unleash` | the specific result |
| `best-in-class` | what makes it good |

### Earlier-era vocabulary: contextual advisory (source: Wikipedia:Signs of AI writing, 2026-10)

The `era-vocab` rule reports figurative `delve`, `paradigm`, `realm`, `tapestry`, `beacon`, `testament`, `myriad`, and `plethora` as MEDIUM advisories. Wikipedia supplies the era context; this retained list and its severity are owner policy, not a claim that every term belongs to one measured cohort. (house preference)

Recognized literal and technical contexts pass. Textile cues immediately before `tapestry`, such as `woven`, `handwoven`, `silk`, `wool`, and `medieval`, or a tapestry hanging on or covering a wall, support a literal reading. `A woven tapestry of Saint George covers the wall` passes. Figurative `rich tapestry`, `tapestry of ideas`, and `we have woven a tapestry celebrating our community` still fire. Named programming, computing, software, scientific, functional, object-oriented, dataflow, logic, imperative, and declarative paradigms pass, as do recognized physical radio/navigation beacons, Kerberos/DNS/authentication realms, and the Old or New Testament. Bare `paradigm shift` remains advisory; a named technical paradigm passes. These narrow context checks can miss unfamiliar literal uses; review those and use the escape hatch when justified. (house preference)

### Vocabulary by era (source: Wikipedia:Signs of AI writing, 2026-10)

These are reading cues, not additional single-word scanner bans. Context and the destination matter more than the date label.

| Era described by Wikipedia | Examples |
|-|-|
| 2023 to mid-2024 | `delve`, `tapestry`, `testament`, `intricate`, `pivotal`, `underscore`, `vibrant`, `meticulous` |
| Mid-2024 to mid-2025 | `align with`, `enhance`, `fostering`, `highlighting`, `showcasing`, `underscore` |
| Mid-2025 to mid-2026 | `emphasizing`, `enhance`, `highlighting`, `showcasing` |
| Mid-2026 onward | `challenge`, `clearer`, `dependable`, `echoed`, `foster`, `leverage`, `matters`, `multifaceted`, `practical`, `prioritize`, `quietly`, `steady`, `universally` |

The last row comes from a review blog cited by Wikipedia, so treat it as moderate evidence. `current-era-cluster` reports MEDIUM only when at least three distinct listed words occur within 300 authored words. Repeating one term does not qualify. This rule matches the listed forms, not every inflection. The plain-word vocabulary rule can also flag local clusters containing `foster` or `leverage`; `multifaceted` alone no longer gets a LOW finding. (source: Wikipedia:Signs of AI writing, 2026-10)

### Plain-word vocabulary clusters (house preference)

One use passes and two or more within 300 authored words are MEDIUM. Distant uses do not form a cluster.

| Word | Prefer |
|-|-|
| `leverage` | use, apply, build on |
| `utilize` / `utilise` | use |
| `robust` | reliable, handles edge cases, or describe the behaviour |
| `comprehensive` | covers the named scope |
| `seamless` | works without an extra step |
| `streamline` | cut steps, simplify |
| `foster` | build, support, grow |
| `empower` | let, give, enable |
| `unlock` | name the result |
| `elevate` | improve, raise |

### Contextual consultant compounds (house preference)

Gate phrases such as `competitive landscape`, `regulatory landscape`, `market landscape`, `navigate the complexities`, `product ecosystem`, `partner ecosystem`, `strategic alignment`, and `customer alignment`. Literal landscape orientation, browser navigation, and biological ecosystems pass. `cross-product synergies` is caught by the vocabulary rule.

### Stacked connective openers (house preference)

`Moreover`, `Furthermore`, `Additionally`, `Consequently`, `Notably` at a line start or after a period. Start with the new point. The scanner flags a single configured opener; it does not require several.

### The antithesis cadence (source: Wikipedia:Signs of AI writing, 2026-10)

The scanner gates promotional `it's not just X, it's Y`, `not just X, but Y`, and related `only`/`merely` forms. `It's not just a tool, it's a movement` still fires, including curly apostrophes, expanded `it is`, multiword noun phrases, and `but a movement` endings. Plain `not X, but Y` is a human review cue, not a general regex ban.

A factual correction of cause should pass: `failed not because the file is missing but because access was denied`. The scanner leaves `not because X but because Y` alone, rather than guessing whether the causes are factual. This heuristic can miss a rhetorical causal contrast; judge that in the human pass. Do not delete a real correction to satisfy cadence advice. (house preference)

### The assistant voice leaking in (house preference)

`as an AI language model`, a refusal (`I cannot assist`), a `knowledge cutoff` line, `I don't have personal opinions`. Remove assistant boilerplate from reader-facing copy. Quoted discussion and examples are skipped.

### Sycophancy and the apology reflex (house preference)

`Great question`, `Certainly!`, `You're absolutely right`, `I'd be happy to`, `happy to help`, `good catch`, `I apologize for the confusion`. Open with the point. When wrong, acknowledge it briefly and fix it.

### Filler and preamble patterns (house preference)

`it's important to note`, `it's worth mentioning`, `in today's [anything]`, `let me break this down`, `Imagine a world where`, `Picture this`, `that being said`, `With that in mind`, `At the end of the day`, `needless to say`. State the thing.

### Bookending and trailing offers (house preference)

`I hope this helps`, `Let me know if you need more`, `Would you like me to`, `is there anything else`, `feel free to reach out`, `hope this email finds you well`, `happy to answer`. In chat replies and docs, cut empty assistant bookends and stop at the last useful point. In an actual email to a colleague, a real invitation such as `Let me know if you need more` or a polite closer is fine. Judge whether it invites a useful reply in that relationship. The scanner still flags these phrases; retain a justified email use with `voice-allow` or `unslop-ignore` and a reason.

### Leaked citation or renderer markup (source: Wikipedia:Signs of AI writing, 2026-10)

`contentReference`, `oaicite`, `oai_citation`, `turn0search` followed by digits, `attributableIndex`, `grok_card`, `<grok-card>`, `grok_render_citation_card_json`, `[cite: N]` with one or more comma-separated numeric values, `[span_N](start_span)` with a numeric N, and `ppl-ai-file-upload` are HIGH. Delete the markup and restore the real citation. Never invent a source. Structured JSON citation keys are checked before prose quote stripping, so `({"attribution":{"attributableIndex":"1009-1"}})` is caught. Code, blockquote, and ignore escapes still apply; ordinary quoted prose examples pass.

## MEDIUM: use sparingly (advisory)

- **Worn social-post templates**: `the guide I wish existed`, `I kept seeing X, so I built Y`, `I saw a gap, so I made this`. MEDIUM advisory; review especially closely in short outreach copy. Lead with what the thing is. A dropped-pronoun opener (`Made a free guide for...`) passes. (house preference)
- **Cross-sentence antithesis**: `The value was not typing speed. It was the forcing function.` / `The speed was not the interesting part. The interesting part was...`. The scanner catches the split cadence; preserve an informative correction on human review. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Frequency-sensitive words**: `crucial`, `vital`, `essential`, `essentially`, `fundamentally`, `various`, `versatile`, `significant`, `genuinely`, `nuance`, `meticulous`, `showcase`, `straightforward`, `precisely`, `dramatically`, `incredibly`, `particularly`, `ultimately`. Two or more within 300 authored words are advisory; one or distant uses pass. (house preference)
- **Softeners**: `simply run X`, `just click Y`. Drop a word that implies the instruction is trivial. (house preference)
- **Bolded lead-in labels**: `**Word:**` before prose is advisory. A list gets the separate `bolded-label-list` advisory only for three or more consecutive Markdown list items with bolded labels, including `- **Owner:** text` and `- **Owner**: text`. One or two pass. Blank lines and indented wrapped continuations preserve the run; an unlabelled item, heading, or paragraph outside the list breaks it. Useful definition lists and work-email labels can stay on review. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Staged reveals**: sentence-initial `The result:`, `The catch?`, `The kicker:`, `The payoff:`, `The twist:`, `The answer:`, `The truth?`. The tell is manufactured revelation, not the colon or question mark itself. (source: workbravely.substack.com/p/sentences-that-sound-like-other-sentences, 2026-07)
- **Significance tails**: `, highlighting the`, `, underscoring its`, `, reflecting their`, `, symbolizing a`, `, showcasing the`, `, emphasizing the`. The scanner accepts any listed participle followed by `the`, `its`, `their`, or `a`. Check that the tail adds a supported inference rather than borrowed importance. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Listicle scaffolding**: `5 ways to`, `7 signs`, `3 reasons`. Ambiguous `things`, `steps`, and `rules` need a heading or listicle continuation such as `to`, `for`, or `you`; plain counts pass. (house preference)
- **Decorative emoji** as a bullet, icon, or heading. Banned unless the user used emoji first in the conversation. Inline conversational emoji can stay. (house preference)
- **Signposted closers**: `In conclusion`, `In summary`, `to summarize`. End on a useful point. (house preference)
- **Hedging when you have a view**: `you might want to consider`, `it may be worth`, `perhaps you`, `on one hand ... on the other`, `it depends`. Keep real uncertainty and trade-offs; state your recommendation. (house preference)
- **Marketing hype**: `revolutionary`, `transformative`, `supercharge`, `to the next level`, `say goodbye to`, `look no further`. Say what the thing does. (house preference)
- **Literary/native flourish (check against the byline)**: `whilst`, `amongst`, `endeavour`, `ascertain`, `elucidate`, `quintessential`, `notwithstanding`, `henceforth`, `hitherto`, `whereby`, `thereby`, `wherein`, `albeit`, `one might`. These are byline choices, not generic AI tells. The scanner raises a MEDIUM advisory; keep vocabulary that fits the author. Build a private voice profile using `references/voice-profile.md`. (house preference)

## LOW: weak or contextual (advisory)

- **Inflated generic diction**: `facilitate`, `paramount`, `pivotal`, `intricacies`. Prefer the plain word. (house preference)
- **Work-announcement preambles**: `Let me take a look`, `I'll start by`, `Here's a breakdown of`. The reader needs the result. (house preference)
- **Fake-relatability openers**: `Honestly,`, `Look, I get it`, `Let's be real`. (house preference)
- **Copula avoidance**: `serves as a`, `stands as an`, `serves as the`. Use `is` or `are` when the phrase only renames the subject. A real function or role can justify it; this is a weak advisory. (source: Wikipedia:Signs of AI writing, 2026-10)

## DO NOT CHASE (deliberately not flagged)

- Ordinary `however`, `thus`, and `hence` connectives. (house preference)
- `when it comes to`, a single `crucial`, or a single `comprehensive` in generic prose. (house preference)
- Technical `unpack a tuple` and the literal vocabulary exceptions described above. (house preference)
- A horizontal rule (`---`) as a real thematic break. (house preference)

## STRUCTURAL (human pass)

- **Uniform rhythm and punctuation impoverishment.** Similar sentence lengths and shapes can sound mechanical, including uniform short sentences. Wikipedia now dates dash overuse to 2022 through September 2026 and describes newer models avoiding dashes while leaning on plain words and 8-20 word sentences. Dash-free plain prose is no evidence of a human. Read for rhythm that fits the argument; the dash ban remains a configured house preference. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Rhythmic triads.** Three items or matching sentences just to tie up a paragraph. A natural list of three is fine. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Sycophancy as tone.** Reflexive agreement without a position. Disagree when you disagree. (house preference)
- **Saying nothing at length.** Fluent prose with no claim. Cut a paragraph if nothing is lost. (house preference)
- **Low substance per word.** Keep claims, evidence, decisions, exceptions, necessary context, requirements, source caveats, and reader actions. Cut repetition and process narration. (house preference)
- **Same paragraph openings.** Repeated openings such as `This` can expose a template. (house preference)
- **The `. That's [adjective].` tic.** Repeated evaluations after facts add little. Let the fact speak or explain its consequence. (house preference)
- **`Think of it as / like` as an analogy launcher.** Make a useful analogy directly. (house preference)
- **Setup before the point.** Lead with the strongest claim when the reader needs it first. (house preference)
- **False ranges.** `from X to Y` implies breadth without endpoints on a coherent scale or whole, such as `from teenagers to managing directors`. Genuine geographical, chronological, and organizational ranges pass. Human-only: no regex. (source: workbravely.substack.com/p/sentences-that-sound-like-other-sentences, 2026-07)
- **Mini-report scaffolding in short pieces.** A short answer split into title-case headings, tiny sections, and unnecessary tables can add ceremony without value. Keep structure that helps this destination and reader. Human-only: no regex. (source: Wikipedia:Signs of AI writing, 2026-10)
- **Overdone voice mimicry.** Repeating the author's signature phrases in every paragraph is an impression. Hold the phrasing habits and register in their private voice profile; `references/voice-profile.md` explains how to build one. (house preference)

### A chosen terse register

Short sentences, earned fragments, and blunt verdicts are a chosen register, not a detection signal. Do not pad them to force variation. Over-correction is prose straining to look human: fragments on every beat, forced lowercase, a swear bolted on, conspicuous punctuation avoidance. Hold a real voice and give thoughts enough connective tissue for the destination.

## Post-rewrite meaning check (house preference)

Compare original and rewrite before delivery. Verify that numbers, names, dates, URLs, citations, negations (`not`, `never`, `no`), and modals (`must`, `should`, `may`) survived unchanged. Check that their relationships and scope still mean the same thing and nothing was invented. Restore lost facts or qualifications, then rescan for style and structure.

`python3 "${CLAUDE_SKILL_DIR}/scripts/unslop_text_scan.py" --compare ORIGINAL REWRITE` lists differing token counts for signed numbers (including exponents), full URLs with balanced parentheses, negations (including `cannot` and `can't`), and modals (including `can`). Curly and ASCII apostrophes compare equally. Surrounding Markdown link punctuation is excluded from URL tokens. It is advisory and exits 0 for a valid comparison, even when differences exist; unreadable files are invalid input and exit 2. It uses full file text and does not apply scan escapes. Its inventories cannot detect moved negations, swapped subjects, invented claims using the same tokens, or changed names and citations. Human comparison is required; identical inventories do not prove meaning survived. Comparison is text-only; the existing scan JSON schema is unchanged.
