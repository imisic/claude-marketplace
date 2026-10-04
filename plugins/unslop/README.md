# unslop

unslop helps writers, developers and web designers revise output that reads as generic AI work. It checks prose, source code and web design for the specific patterns that make something look machine-made, then guides changes that fit your voice, your project's conventions or your brand. Each of the three skills has a scanner you can run, which prints the file, line and a suggested fix for every match, and a review pass for what a scanner can't see, such as rhythm and layout. Mark a deliberate choice with `unslop-ignore` and the scanner leaves it alone.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

None of the three hand you a house style. They remove the cues that make something read as the model's median output and, where that median exists because nobody chose otherwise, they force a deliberate choice instead. The choice itself (your voice, your code conventions, your brand) stays yours.

## The three skills

| Skill | Surface | Scanner |
|---|---|---|
| `a-unslop-text` | Prose: docs, READMEs, posts, commit bodies, emails | `unslop_text_scan.py` |
| `a-unslop-code` | Source code, any language | `unslop_code_scan.py` |
| `a-unslop-ui` | Web UI: HTML/CSS/JS/JSX/Vue/Svelte/Astro | `devibe_scan.py` |

Each scanner reports findings with file, line, and fix, plus a severity-weighted score, and exits non-zero on high-severity findings so it can gate a CI job.

## a-unslop-text

Catches the em dash, banned corporate/AI diction (`delve`, `leverage`, `utilize`, `robust`, `paradigm`...), the "it's not just X, it's Y" cadence, sycophantic openers, bookending, and leftover assistant boilerplate. Flags the over-corrected 2026 register too (forced staccato fragments, fake typos) so you don't trade one tell for another.

Also ships `references/voice-profile.md`: a method for building a voice profile from your own pre-AI writing (the moves you repeat, a register dial, a language ceiling), because a draft with every tell removed is clean but still nobody's. Build mode loads the profile when the byline is yours. A matching scanner rule flags literary vocabulary (`whilst`, `endeavour`, `notwithstanding`) that reads as out of place when the author's real register is plainer, which is common for non-native writers.

```bash
python3 skills/a-unslop-text/scripts/unslop_text_scan.py <path>
python3 skills/a-unslop-text/scripts/unslop_text_scan.py <path> --severity high
```

## a-unslop-code

Sorts every tell into bugs (swallowed errors, a made-up API, a left-in stub), substance (tutorial-shaped boilerplate, over-engineering, code that ignores the repo), and cosmetic (emoji in source, narrating comments, generic `process_data` names, pasted chat text). Says plainly that the loudest tells are structural and need a compiler or a human, not a regex.

```bash
python3 skills/a-unslop-code/scripts/unslop_code_scan.py <path>
python3 skills/a-unslop-code/scripts/unslop_code_scan.py <path> --severity high
```

## a-unslop-ui

Flags both the 2024 default (shadcn/Tailwind stock theme, AI-purple, gradient text, unprompted neon glow, emoji-as-icons, the centered-hero-plus-three-cards skeleton) and the 2026 "tasteful default" (cream background, serif display face, sage-green accent) that anti-slop advice itself created. Prescribes no palette or font; asks that whatever you use be a choice you can justify.

```bash
python3 skills/a-unslop-ui/scripts/devibe_scan.py <path>
python3 skills/a-unslop-ui/scripts/devibe_scan.py <path> --severity high
```

## Use

Each skill auto-triggers on its own cues (writing prose, generating or reviewing code, building or styling UI), or invoke it directly by name. Run the matching scanner as an audit gate; read the linked `references/tells.md` (and `references/choosing-a-look.md` / `references/writing-with-intent.md` / `references/voice-profile.md` / `references/fitting-the-codebase.md`) for the tells a scanner cannot see.

## Examples

- `Review docs/launch-post.md with a-unslop-text and rewrite anything that reads machine-written.`
- `Run a-unslop-code over src/ and fix the bug-class findings before anything cosmetic.`
- `Check templates/landing.html with a-unslop-ui for stock AI-default design and propose a deliberate alternative.`

## Privacy

Everything runs on your machine. The skills read the files you point them at, the scanners are standard-library Python that print findings to your terminal, and the plugin itself collects nothing, stores nothing outside your project and sends nothing anywhere. There is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install unslop@imisic
```

Then the commands are `/a-unslop-text`, `/a-unslop-code` and `/a-unslop-ui`. You install the plugin, you run the skills.

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/unslop](https://ivanmisic.net/toolshed/plugins/unslop).

## Credits

All three tell catalogs and scanner designs are adapted (MIT) from the vibecoded-design-tells research by JCarterJohnson (https://github.com/JCarterJohnson/vibecoded-design-tells), a large-scale analysis of what people actually name as AI-writing, AI-code, and AI-website giveaways. Each `SKILL.md` and scanner header credits it directly.
