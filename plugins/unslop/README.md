# unslop

unslop helps writers, developers and web designers revise output that reads as generic AI work. It checks prose, source code and web design for the specific patterns that make something look machine-made, then guides changes that fit your voice, your project's conventions or your brand. Each of the three skills has a scanner you can run, which prints the file, line and a suggested fix for every match, and a review pass for what a scanner can't see, such as rhythm and layout. Mark a deliberate choice with `unslop-ignore` and the scanner leaves it alone.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install unslop@imisic
```

Then the commands are `/unslop:a-unslop-text`, `/unslop:a-unslop-code` and `/unslop:a-unslop-ui`. You install the plugin, you run the skills.

Needs Python 3 for the scanners. Output is findings in the terminal (file, line, fix), or JSON with `--json`.

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/unslop](https://ivanmisic.net/toolshed/plugins/unslop).

The tools flag repeated patterns in AI-generated writing, code and design. You choose changes that fit your own voice and project. The scanners check configured patterns; a manual review covers meaning, structure and layout.

## The three skills

| Skill | Surface | Scanner |
|---|---|---|
| `a-unslop-text` | Prose: docs, READMEs, posts, commit bodies, emails | `unslop_text_scan.py` |
| `a-unslop-code` | Source code, any language | `unslop_code_scan.py` |
| `a-unslop-ui` | Web UI: HTML/CSS/JS/JSX/Vue/Svelte/Astro | `devibe_scan.py` |

Each scanner reports findings with file, line, and fix, plus a severity-weighted score, and exits non-zero on high-severity findings so a CI job can stop when it fails.

## a-unslop-text

Catches the em dash, banned corporate/AI diction (`delve`, `leverage`, `utilize`, `robust`, `paradigm`...), the "it's not just X, it's Y" cadence, sycophantic openers, bookending, and leftover assistant boilerplate. Flags the over-corrected 2026 register too (forced staccato fragments, fake typos) so you don't trade one tell for another.

Also ships `references/voice-profile.md`: a method for building a voice profile from your own writing from before you used AI: the phrasing habits you repeat, the tone you use for each destination, and the vocabulary level you actually write at. A draft with every pattern removed is clean, but it still needs to sound like you. Build mode loads the profile when the byline is yours. A matching scanner rule flags literary vocabulary (`whilst`, `endeavour`, `notwithstanding`) that reads as out of place when the author's real register is plainer, which is common for non-native writers.

Inside Claude Code the skill runs its scanner for you. To run one by hand from a clone of this repo, start in `plugins/unslop/`:

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

Claude can start each skill during related work (writing prose, generating or reviewing code, building or styling UI), or you can run it by name. Run the matching scanner as a final check; read the linked `references/tells.md` (and `references/choosing-a-look.md` / `references/writing-with-intent.md` / `references/voice-profile.md` / `references/fitting-the-codebase.md`) for the tells a scanner cannot see.

## Examples

- `Review docs/launch-post.md with a-unslop-text and rewrite anything that reads machine-written.`
- `Run a-unslop-code over src/ and fix the bug-class findings before anything cosmetic.`
- `Check templates/landing.html with a-unslop-ui for stock AI-default design and propose a deliberate alternative.`

## Privacy

Everything runs on your machine. The skills read the files you point them at, the scanners are standard-library Python that print findings to your terminal, and the plugin itself collects nothing, stores nothing outside your project and sends nothing anywhere. There is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Credits

All three tell catalogs and scanner designs are adapted (MIT) from the vibecoded-design-tells research by JCarterJohnson (https://github.com/JCarterJohnson/vibecoded-design-tells), a large-scale analysis of what people actually name as AI-writing, AI-code, and AI-website giveaways. Each `SKILL.md` and scanner header credits it directly.
