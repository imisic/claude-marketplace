# AI-website tells: the catalog

The scanner (`scripts/devibe_scan.py`) enforces mechanical signatures; human review decides whether they fit the brief. A tell is a reason to inspect a choice, not proof of AI authorship. Severity reflects judged risk and pattern precision, not complaint frequency. HIGH findings gate CI; MEDIUM and LOW are advisory. Sources below were checked or carried forward in 2026-10, not necessarily published then.

Source names: [Reddit study](https://github.com/JCarterJohnson/vibecoded-design-tells), [Anthropic frontend-design](https://raw.githubusercontent.com/anthropics/skills/main/skills/frontend-design/SKILL.md), [shadcn Card](https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/ui/card.tsx), [Impeccable](https://impeccable.style/slop/), [signs-of-ai-design](https://github.com/febbhav/signs-of-ai-design), [stop-design-slop](https://github.com/Juuzoe/stop-design-slop), and [NN/g sparkles](https://www.nngroup.com/articles/ai-sparkles-icon-problem/). Source guidance supports review candidates; the scanner thresholds are house choices, not validated authorship tests.

## High

### The tasteful default (`claude-default-look`)

Warm cream, a serif display face, and a sage/forest or terracotta/clay accent can become another interchangeable default. Anthropic now warns against the cream/serif/clay cluster itself. (source: Anthropic frontend-design, 2026-10)

- Scanner: any two of three signal groups in one file produce one HIGH finding. A single group produces no finding. Cream backgrounds include `#faf8f5`, `#f5f1e8`, `#f4f1ea` and related listed swatches in the scanner, or `bg-stone-50/100`, `bg-amber-50/100`, `bg-orange-50/100`. Hex cream counts on `background`, `background-color`, or `--background` declarations. Serif names are Instrument Serif, Fraunces, Playfair Display, Cormorant, Spectral, and DM Serif. The accent group includes green/emerald 700-900 colour utilities, sage/forest swatches `#9caf88`, `#87a878`, `#2d4a3e`, `#264e36`, and clay swatches `#d97757`, `#c96442`, `#cc785c`. Green and clay together still count as one group; hex matching uses listed swatches, not a continuous colour range.
- The accent must appear on a button, link or heading, a class/selector naming primary, accent, brand, CTA, button, link or heading roles, or a `--primary`, `--accent` or `--brand` theme variable (including suffixed names). Green pills combining `bg-green-100` with `text-green-700` (or emerald equivalents), and `span` elements with `rounded-full text-xs`, do not supply an accent signal. Status and warning lines do not contribute. Block, HTML and code line comments are masked across lines without treating quoted comment delimiters as comments; `unslop-ignore` lines do not contribute to any rule. Signals never combine across files. These are source co-occurrences, not computed styles or proof that a serif is used for display.
- Fix: anchor the choices to a real brand or reference. Keep a deliberate warm-editorial identity and mark its source lines `unslop-ignore`.

### Untouched shadcn / Tailwind (`shadcn-default-card`)

Shipping the stock Card and theme makes unrelated products resemble the same starter. The tools themselves are fine. (source: Reddit study, 2026-10)

- Card signature: at least four of five class groups in one quoted string or CSS `@apply` directive, in any order: `rounded-lg` or `rounded-xl`, `border`, `bg-card`, `text-card-foreground`, `shadow-sm`. Extra layout classes and nested quote characters in arbitrary utilities are allowed. The current registry uses `rounded-xl`. (source: shadcn Card, 2026-10)
- Theme signatures: `--radius: 0.5rem`, or a file literally named `components.json` with `baseColor` set to slate, zinc, neutral, gray, or stone and `cssVariables: true` (also accepts `cssVars: true`). Configuration fields can be under `tailwind` or at the root. Other JSON files are not included in directory scans.
- Fix: choose primary, radius, neutrals, and spacing for the project. The signature is a review gate, not proof that tokens are unthemed.

### AI purple (`ai-purple`)

Indigo/violet/purple used as the fallback primary is a recurring complaint. (source: Reddit study, 2026-10)

- Scanner: Tailwind indigo/violet/purple/fuchsia colour utilities at 400-800 and the listed common hex values. It cannot determine the actual primary role; platform/brand/social swatch lines are suppressed.
- Fix: use the real brand colour. A deliberate purple identity gets `unslop-ignore`, not a replacement default.

### Gradient text and purple-blue gradients (`gradient-text`, `purple-blue-gradient`)

Gradient headings and purple-to-blue/pink hero fills recur across generated landing pages. (source: Reddit study, 2026-10)

- Scanner: `bg-clip-text` with `text-transparent`, CSS text background clipping, purple-family `from-*` stops followed by blue/indigo/pink/cyan/sky `to-*`, or a linear gradient containing one of the listed purple hexes. It does not detect every gradient.
- Fix: use solid text and fills unless the brief gives the gradient a role.

## Medium

- **Repeated eyebrow chrome (`eyebrow-chrome`).** Three or more labels in one file, each with `uppercase` (a class or inline `text-transform`) and `tracking-wide`, `tracking-wider`, `tracking-widest`, or `letter-spacing`, directly preceding an `h1`-`h6`. The scanner recognizes `p`, `span`, `div`, or `small` labels containing plain text; attributes can span lines. Static React `style={{letterSpacing:".1em"}}` and `textTransform:"uppercase"` are supported, as are inline JSX comments between label and heading. Dynamic style values, spread attributes, computed properties and intervening components are not resolved. Keep an eyebrow only when it adds information. (source: Anthropic frontend-design, 2026-10)
- **Tinted icon tiles (`tinted-icon-tiles`).** Three or more rounded `div`/`span` wrappers with `bg-primary/10` or `bg-*-500/10`, directly containing an icon component imported by name from a Lucide package. Repeating the tile can substitute decoration for product-specific imagery. Static class strings and `className={cn("...", "...")}` or `clsx` calls with only string literal arguments are supported. Conditional arguments, objects, variables, spreads, interpolated templates, nested icon wrappers and default/deep imports are not resolved. The scanner recognizes direct, self-closing icon components, including named import aliases, not arbitrary component trees. (source: stop-design-slop/references/imagery-icons.md, 2026-10)
- **Too many animations (`fade-in-animations`).** Fade-in on every section and scale-up on every card can compete with the task. The scanner flags `initial={{ opacity: 0 }}`, `whileInView`, `whileHover={{ scale }}`, `data-aos`, and `hover:scale-1xx` individually; it does not measure motion density. Keep motion that explains a change and honour `prefers-reduced-motion`. (source: Reddit study, 2026-10)
- **Rounded everything (`rounded-everything`).** The scanner flags `rounded-2xl`, `rounded-3xl`, `rounded-full`, and huge pill radii. Small `h-`/`w-` boxes are suppressed so dots and avatars pass. Choose a radius scale by role. (source: Reddit study, 2026-10)
- **Unprompted neon glow (`neon-glow`).** Zero-offset saturated shadows are candidates; achromatic and inset shadows are suppressed. Dark mode itself is fine. Remove glow without a purpose. (source: Reddit study, 2026-10)
- **Emoji icons (`emoji-as-icons`).** Rocket, sparkle, lightning, lock and related emoji used as feature icons can read as placeholders. The scanner flags its listed characters anywhere in source, so review body-copy uses before changing them. Use a meaningful SVG icon or none. (source: Reddit study, 2026-10)
- **Default fonts (`generic-font`).** The scanner catches Inter, Geist, and Roboto declarations or font-loader calls, not whether the choice was deliberate. Choose one family or two for a reason; if two, make them distinct. A chosen font gets `unslop-ignore`. (source: Reddit study, 2026-10)
- **Hero and three-card skeleton (`hero-three-cards`).** The scanner catches `grid-cols-1` followed by optional `sm:grid-cols-2` and `md:grid-cols-3`; it cannot establish the hero structure. Review whether content actually benefits from three equal cards. Structure the page around its task. (source: Reddit study, 2026-10)

## Low

- **Middle-dot metadata (`middle-dot-meta`).** Two or more distinct markup text runs containing `word · word · word` in one file produce one LOW finding. Multiple triplets within one run count once. JavaScript strings, JSX escaped examples, attributes, and script/style bodies do not count. Archive rows shaped like `2026 · October · Archive` are excluded. The rule matches literal middle dots, not `&middot;`, and does not evaluate dynamic expressions. Keep separators when they help read real metadata. (source: Anthropic frontend-design, 2026-10)
- **Appended arrows (`appended-arrow`).** Three or more link/button labels ending in `→` produce one LOW finding per file. The scanner recognizes `a`, `button` and `Link`, decodes `&rarr;` and numeric entities, accepts static JSX `{"→"}` or `{'→'}`, and flattens child markup such as accessibility spans. Prefix arrows, arrows in the middle of labels, attributes and arbitrary source strings do not count. Dynamic text expressions, custom action components, CSS pseudo-elements, icon components and runtime translations are not resolved. CSS visibility and accessibility naming can change which source text readers encounter. Keep arrows that clarify navigation. (source: Anthropic frontend-design, 2026-10)
- **Hype copy (`hype-copy`).** `Transform your`, `Supercharge`, `Unleash`, `Effortlessly`, `reimagined`, and similar canned claims. Say what the product does. (source: Reddit study, 2026-10)
- **Stock illustrations (`stock-illustration`).** The scanner catches undraw, storyset, and drawkit source names. Check whether the image explains this product; prefer real screenshots where useful. (source: Reddit study, 2026-10)

Repetition rules produce one finding per file at the first occurrence. Their source patterns do not establish rendered DOM relationships. Keep intentional choices with `unslop-ignore` on the contributing lines.

## Human audit checks

- **Decorative numbering.** `01 / 02 / 03` section labels belong on real sequences, such as steps or timelines. Remove numbers from unrelated sections. (source: Anthropic frontend-design, 2026-10)
- **Dark acid-accent default.** Near-black `#0B0B0B`, `#111`, or `#111111` with one acid-green or vermilion accent can become another fallback. Check the brief and the whole palette; no scanner rule. (source: Anthropic frontend-design, 2026-10)
- **Hairline broadsheet.** Dense newspaper columns, hairline rules, and zero radius need a content reason. Do not substitute this look for every rounded-card design; no scanner rule. (source: Anthropic frontend-design, 2026-10)
- **Fabricated trust.** Verify logo clouds, testimonials, ratings, compliance badges, and rows claiming `10x`, `99.9%`, or `10,000+ users` against supplied sources, quote originals, relationships, and metric definitions. If unsupported, remove them or ask for evidence. Missing provenance is a verification gap, not proof of fabrication. No stat-row regex. (source: stop-design-slop, 2026-10)
- **Sparkles / Wand2 on non-AI actions.** Check whether the icon explains the action. NN/g discusses ambiguous sparkles as an AI signifier, not an AI-authorship detector. No scanner rule for action meaning. (source: NN/g sparkles, 2026-10)
- **Overflow and clipping.** Test headings and labels with real strings at narrow widths. Give text room and let it wrap. (house preference)
- **Spacing, alignment, hierarchy.** Use a consistent spacing scale and gutters; make the primary task visually clear. A clean scan cannot establish layout coherence. (house preference)
- **Centred everything and endless whitespace.** Review density and alignment against the content rather than applying either everywhere. (source: Reddit study, 2026-10)

## Do not chase without context

- **Mesh/blob/aurora backgrounds.** Advisory when repeated reflexively or unrelated to content. The original Reddit keyword analysis rejected an artifact involving `/blob/` URLs; it cannot prove absence as a tell. Current catalogs list these backgrounds. No scanner rule. (source: signs-of-ai-design, 2026-10)
- **Bento grids.** Advisory when every section becomes a bento regardless of its content. The original Reddit study cannot prove absence as a tell; current catalogs list the pattern. No scanner rule. (source: signs-of-ai-design, 2026-10)
- **Glassmorphism.** Advisory when glass panels recur without a layering need. Review purpose and readability; no scanner rule. (source: Impeccable, 2026-10)
- **Dark mode and shadcn/Tailwind.** Tools and modes do not establish authorship. Review defaults and fit to the brief. (house preference)
