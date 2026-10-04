---
name: a-unslop-ui
description: "Remove stock AI-generated design patterns without imposing a look. Use when building, styling, reviewing, refactoring or auditing websites, landing pages, web app UIs, dashboards or web components; for \"looks AI-generated\", \"de-slop this\", \"make it look custom\", slop or vibe-coded UI; and for Tailwind or shadcn appearance work. Apply during web UI work even when AI is not mentioned. Checks stock themes, AI-purple, gradient hero/body text, unprompted neon glow, emoji icons, hero-plus-three-cards layouts and cream/serif/green defaults. Includes a scanner plus visual checks for layout, spacing and overflow. Preserve deliberate brand choices."
---

# a-unslop-ui

Part of the unslop family (see `a-unslop-text`, `a-unslop-code`). Same shape: an auto-trigger,
Build and Audit modes, a scanner that gates on a high-severity exit code, an `unslop-ignore`
escape. This one is about web UI. It works on any web codebase, whatever sites or apps you
run it against, and the method and scanner do not assume a particular stack.

**What it is not.** It does not give you a good design and it has no preferred look. It removes
the cues that read as AI-made, and where the model would reach for a default it forces a choice
the project actually made. Taste, brand, and layout judgment stay yours.

## The trap: do not swap one default for another

Every anti-slop effort fails the same way, by replacing one default look with another. The 2024
default was the purple-to-blue gradient on a dark hero. The 2026 default is a warm cream
background, a serif display face (Instrument Serif, Fraunces), and a sage or forest-green
accent, which is the current Claude/Anthropic house look. Swapping the first for the second is
not unslopping. People clock it just as fast, and it reads as AI for the same reason: nobody
chose it, the model did.

So this skill prescribes no palette, no font, no layout. It detects the defaults, old and new,
and asks that any replacement be a choice the project made on purpose. The one rule is "make a
deliberate choice and be able to say why," which is the one thing a default never is. If the
brand really is purple, neon, or a cream serif look, that is not slop; mark it
`unslop-ignore` and move on. A tell is an unspecified default, not a banned colour.

## How it differs from the built-in frontend-design skill

Claude ships a frontend-design skill, and it is good, but it produces the cream-plus-serif-plus-
green look this one now flags. They work together: let the design skill build, let this one keep
it honest. What this adds: a deterministic scanner that gates a build, a ranking so effort goes
where the real complaints are, and an explicit check on the new "tasteful default" so you do not
launder slop into nicer slop.

## Build mode

Most "looks AI" output is an under-specified prompt. An unspecified prompt gets the median of
the training data, and everyone's median is the same. Before generating, set four things:

- **A reference.** One real site, brand, or screenshot whose design language to follow. This one
  input does more than the rest combined. If there is none, pick a named direction (editorial,
  brutalist, dense-utilitarian, warm-consumer, technical-mono), not "modern and clean," which
  means nothing.
- **A colour.** A real brand colour or a chosen one, stated. Not the framework default, not the
  cream/sage default.
- **A typeface.** A specific face or pairing chosen for this project, with a reason. The
  autopilot picks are Inter and Geist on the sans side, Instrument Serif, Fraunces, Playfair on
  the "tasteful" side; both are defaults, so reach for them only as a real choice.
- **A layout intent.** What the page is for and what the reader should do first. Structure
  follows the goal, which is how you avoid the hero-plus-three-cards skeleton.

With no brief, do not produce one median result. Produce a deliberate one and say what you chose,
or offer two or three distinct directions. The value is breaking the monoculture.
`references/choosing-a-look.md` is the method; the tells to avoid are in `references/tells.md`.

## Audit mode

On "does this look AI" or "de-slop this," run the scanner, then fix in priority order.

```bash
python3 scripts/devibe_scan.py <path>                 # report + vibe score
python3 scripts/devibe_scan.py <path> --severity high # strongest only
python3 scripts/devibe_scan.py <path> --json          # for CI
```

It scans `.html .css .scss .js .jsx .ts .tsx .vue .svelte .astro`, reports each finding with
file, line, and fix, and gives a vibe score. Exit code is the high count, so CI can gate on it.
It catches the mechanical tells: colours, fonts, gradients, the cream-plus-serif combo. It cannot
see layout coherence, spacing, or text overflowing its container, and those are also why a page
reads as AI, so after the scan check them by eye against the catalog.

**Shipped UI only.** The scanner skips `docs/`, `_archive/`, `archive/`, `mockups/` and `examples/` as well as the usual `node_modules`, `dist` and `vendor`. A design comp or a palette swatch page quotes a tell rather than committing one, and scanning those buries the real findings. If a site really serves its UI from one of those directories, point the scanner at that path directly.

**Escape hatch.** A line with `unslop-ignore` is skipped, for a real brand decision.

**Fixing well.** Do not fix `bg-purple-600` by swapping in `bg-emerald-700`, which is a different
default. Apply the project's real colour, or ask what it should be. A fix that introduces a new
unspecified default is not a fix.

## What it does not flag

Grounded in the ranking, not vibes. Mesh, aurora, and blob backgrounds barely register (mostly a
keyword artifact). Bento grids and glassmorphism are low and contested, so they are allowed. Dark
mode itself is fine; only the unprompted glow is a tell. shadcn and Tailwind are fine; their
untouched defaults are the tell. Over-flagging trains people to ignore the tool, so the scanner
stays narrow.

## Reporting

Lead with the verdict and the single highest-impact change. Findings by priority with file:line
and the fix. Close with the vibe score and the top three changes. The goal is a site that looks
like a person made a decision, the one thing the scanner cannot do for you.

## Credits

The tell catalog and its ranking come from the vibecoded-design-tells research by JCarterJohnson
(https://github.com/JCarterJohnson/vibecoded-design-tells, MIT), a Reddit study of what people
flag as AI-built websites. This skill rewrites that material into the unslop family and a shared
Build/Audit shape with the text and code skills. `scripts/devibe_scan.py` is an adapted fork of
that project's scanner (MIT); the credit is in its header.
