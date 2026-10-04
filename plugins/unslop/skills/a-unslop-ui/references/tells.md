# AI-website tells: the catalog

The human-readable view. The scanner (`scripts/devibe_scan.py`) is the enforced layer for the mechanical tells; this file explains them, gives the code signatures, and lists the ones only your eyes catch. The ranking comes from the research credited in `SKILL.md`; the structure and prose here are this skill's.

The loudest complaint in the data is not any single feature. It is that the sites are recognizable on sight, "they all look the same." Among specific features, ordered by how often people name them:

## Co-top priority

### The "tasteful default" (cream + serif + green), the 2026 tell

The look the previous wave of anti-slop advice (including Claude's frontend-design skill) converged on, so it is now the clearest "AI tried to be tasteful" signal. A warm cream or beige page, a serif display face (Instrument Serif, Fraunces, Playfair), a sage or forest-green accent, often a generated product-screenshot card on the right. It reads as AI for the same reason the purple gradient did: nobody chose it. It lands harder than the gradient because it looks like taste.
- Signatures: cream page background (`#faf8f5`, `#f5f1e8`, `bg-stone-50`, `bg-amber-50`); serif display (`Instrument Serif`, `Fraunces`, `Playfair Display`, `Cormorant`, `DM Serif`); sage/forest primary (emerald or green 700-900). Any two of the three together is the strong signal.
- Fix: not a different nice palette. Anchor to the real brand or a reference; with none, pick a direction that is specific and uncommon. A genuine warm-editorial brand marks it `unslop-ignore`.

### Default shadcn / Tailwind look

The single most-named concrete cause of "they all look the same." The stock slate/zinc/gray cards, the default ring and border, the uniform `p-6` rhythm, the stock `rounded-lg`. shadcn is not the problem; shipping it untouched is.
- Signatures: heavy repeated `bg-slate-*`/`bg-zinc-*`/`bg-gray-*` cards with `border rounded-lg shadow-sm`; `components.json` with `baseColor: "slate"`/`"zinc"` and untouched `cssVars`; `--radius: 0.5rem` left at default; the stock `rounded-lg border bg-card text-card-foreground shadow-sm` Card repeated with no theming.
- Fix: theme the tokens before building. A real `--primary`, a chosen `--radius`, your own neutral ramp and spacing. Test: could someone tell your Card from the shadcn docs Card in a screenshot?

## High

### AI purple (violet / indigo primary)

The top colour tell, and it co-occurs with gradients more than any other pair. Models reach for Tailwind's indigo/violet when no brand colour is given, so purple-as-primary reads as "nobody chose this."
- Signatures: `indigo-*`/`violet-*`/`purple-*`/`fuchsia-*` as the primary, CTA, or link (not an accent dot); primaries like `#6366f1`, `#7c3aed`, `#8b5cf6`, `#a855f7`; `--primary`/`--brand` at hue around 255 to 280.
- Fix: a brand colour outside that band. If purple is the real brand, pick a specific off-default purple and pair it with a non-default neutral.

### Gradients, gradient text

The purple-to-blue (or purple-to-pink) hero gradient, gradient-filled headings, gradient buttons. Gradient body text especially reads as generated, since almost no real brand does it on running copy.
- Signatures: `bg-clip-text text-transparent` (or CSS `-webkit-background-clip: text`); `from-purple-* to-blue-*`, `from-violet-* to-indigo-*`; `bg-gradient-to-*` repeated across hero, buttons, cards.
- Fix: solid fills by default. At most one restrained accent gradient, analogous and low-contrast. Never on running headings or paragraphs.

## Medium

- **Too many animations.** Fade-in on every section, scale-up on every card hover, scrolljacking. A minor and noisier signal (the keyword catches tool mentions and praise too). Signatures: repeated `initial={{ opacity: 0 }}`/`whileInView`/`whileHover={{ scale }}`, `data-aos="fade-up"` everywhere, `hover:scale-1xx` on every card. Fix: motion only when it communicates state; honour `prefers-reduced-motion`; if every section animates the same way, cut it.
- **Rounded corners and pill buttons on everything.** One large radius on cards, inputs, buttons, images, plus fully-pill buttons. Signatures: broad `rounded-2xl`/`rounded-3xl`/`rounded-full`, `border-radius: 9999px` on every button. Fix: a small radius scale applied by role. (The scanner skips `rounded-full` on small `h-`/`w-` boxes, since those are dots and avatars.)
- **Dark mode with unprompted neon glow.** Dark mode is fine; the glow added when nobody asked is the tell. Signatures: `shadow-[0_0_*]`, `drop-shadow-[0_0_*]`, a saturated low-blur `box-shadow`/`text-shadow`, neon `text-cyan-400`/`text-green-400` on `bg-black`. Fix: remove glow you did not design. Dark mode should rely on contrast and spacing.
- **Emoji as icons or bullets.** Rocket, sparkle, lightning, lock characters used as feature-card icons or section bullets. It needs no asset pipeline, so the model reaches for it. Signatures: emoji in `<h1>`/`<h2>`/`<h3>`, in feature titles, or as list markers. Fix: a real SVG icon set (Lucide, Phosphor, Heroicons) or none. Emoji in genuine body copy is fine.
- **Generic default fonts.** Inter, Geist, Roboto, or `system-ui` as the only face is "nobody chose the type." There are two defaults now: Inter/Geist (the "no choice" default) and Instrument Serif/Fraunces (the "tasteful choice" default, see the 2026 tell). Both are autopilot. Signatures: `font-family: Inter`/`Geist`/`Roboto`; `next/font/google` importing one with no real second face; `font-sans` left at default. Fix: a face with character, chosen for a reason, paired display over body.
- **The centered hero + three feature cards + CTA skeleton.** The most common generated landing page. The structure is the tell, before any colour. Signature: a `text-center` hero with a big headline and two buttons, then `grid grid-cols-1 md:grid-cols-3` of icon-title-blurb cards. Fix: break the grid. Asymmetric hero, a real product screenshot, varied sections.

## Layout-quality tells (no scanner sees these)

Not colour or font, but a large part of why a page reads as AI. Check by eye on every build.
- Text overflow and clipping: a heading or label running past or behind its container, a fixed-width card that does not handle long content. Give text room, let it wrap, test with real strings.
- Inconsistent spacing: a page mixing `p-3` here, `p-7` there, an arbitrary `mt-[37px]`, with no spacing scale. The eye reads that as machine-made.
- Misalignment: edges that almost line up, inconsistent gutters. Align to a grid.
- No hierarchy: every section the same weight. Decide what the reader sees first and make the layout say so.

Fixing colour and font on an incoherent layout still leaves a site that reads as AI. The scanner gives a clean surface; these give a coherent structure.

## Lower-signal and copy tells

Real but minor; fix if cheap.
- Centred everything and endless whitespace; stock undraw-style illustrations (use real screenshots).
- Hero-copy cliches: `Transform your X`, `Supercharge`, `Unleash`, `Effortlessly`, `Your X, reimagined`. Write specific copy about what the thing does. (The text skill flags these too.)

## Do not chase (cleared by the research)

- Mesh/blob/aurora backgrounds: rejected as a keyword artifact (most matches were github `/blob/` URLs). Not a real complaint.
- Bento grids: dead last, and people defend them. Not a tell.
- Dark mode itself: only the unprompted glow is flagged.
- shadcn/Tailwind themselves: the defaults are the tell, not the tools. A themed shadcn site is invisible to this complaint.

Flag what the ranking supports, at the weight it supports.
