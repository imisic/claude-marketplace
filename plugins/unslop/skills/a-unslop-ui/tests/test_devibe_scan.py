"""Regression tests for devibe_scan.

Every case here is a false positive that shipped, or the true positive its fix had to
keep. A scanner that reports black drop shadows as neon glow stops being run, so each
false positive here is pinned.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "devibe_scan.py"
SPEC = importlib.util.spec_from_file_location("devibe_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class ScannerTests(unittest.TestCase):
    def scan(self, text, name="sample.css"):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            return SCANNER.scan(str(path), "low")

    def rules(self, text, name="sample.css"):
        return sorted({f["rule"] for f in self.scan(text, name)})

    # ---- neon-glow: the colour is what makes it a glow ----

    def test_black_soft_shadow_is_not_neon_glow(self):
        self.assertEqual([], self.rules(
            ".a{box-shadow: 0 0 10px rgba(0, 0, 0, .08)}\n"
            ".b{text-shadow: 0 0 50px rgba(0,0,0,.9)}\n"
            ".c{text-shadow: 0 0 20px #333}\n"
        ))

    def test_inset_fill_is_not_neon_glow(self):
        self.assertEqual([], self.rules(
            ".t{box-shadow: inset 0 0 0 9999px var(--bs-table-accent-bg)}\n"))

    def test_saturated_glow_is_still_caught(self):
        self.assertEqual(["neon-glow"], self.rules(
            ".g{box-shadow: 0 0 20px #00ffff}\n"
            ".h{text-shadow: 0 0 12px rgba(0,255,200,.8)}\n"))

    def test_tailwind_arbitrary_glow_is_still_caught(self):
        self.assertEqual(["neon-glow"], self.rules(
            '<div class="shadow-[0_0_15px_rgba(139,92,246,0.5)]">x</div>\n', "a.html"))

    # ---- ai-purple: someone else's brand is a fact, not a default ----

    def test_platform_brand_purple_is_allowed(self):
        self.assertEqual([], self.rules(
            ".brand-twitch { @apply text-violet-700; }\n"
            ".social-discord { @apply text-indigo-700; }\n"))

    def test_purple_as_site_primary_is_still_caught(self):
        self.assertEqual(["ai-purple"], self.rules(
            '<button class="bg-indigo-600">Go</button>\n', "a.html"))

    # ---- claude-default-look: amber status chrome is not a cream page ----

    def test_amber_warning_badge_is_allowed(self):
        self.assertEqual([], self.rules(
            ".status-pending { @apply bg-amber-100 text-amber-700; }\n"))

    def test_cream_page_background_alone_is_allowed(self):
        self.assertEqual([], self.rules("body{background:#faf6ef}\n"))

    def test_instrument_serif_alone_is_allowed(self):
        self.assertEqual([], self.rules("body{font-family:'Instrument Serif',serif}\n"))

    # ---- comments describe tells, they do not commit them ----

    def test_rule_written_in_a_comment_is_not_a_finding(self):
        self.assertEqual([], self.rules(
            "/*\n * No rounded-full anywhere. No bare rounded (4px).\n */\n"))

    def test_same_text_as_real_css_is_a_finding(self):
        self.assertEqual(["rounded-everything"], self.rules(".pill{border-radius:9999px}\n"))

    # ---- escape hatch ----

    def test_unslop_ignore_line_is_skipped(self):
        self.assertEqual([], self.rules("body{background:#faf6ef} /* unslop-ignore */\n"))

    # ---- scope: design comps and archives are not shipped UI ----

    def test_docs_and_archive_directories_are_skipped(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp)
            for sub in ("docs", "_archive", "mockups"):
                (root / sub).mkdir()
                (root / sub / "spec.css").write_text(".cta{background:#6366f1}", encoding="utf-8")
            (root / "app.css").write_text(".cta{background:#6366f1}", encoding="utf-8")
            findings = SCANNER.scan(str(root), "low")
        self.assertEqual(1, len(findings), "only the shipped stylesheet should be scanned")

    # ---- palette/type signals combine only within one file ----

    def test_cream_and_serif_together_are_high(self):
        findings = self.scan("body{background:#F4F1EA}\nh1{font-family:Fraunces}\n")
        self.assertEqual([("claude-default-look", "high", 1)],
                         [(f["rule"], f["sev"], f["line"]) for f in findings])

    def test_all_palette_signal_pairs_are_caught(self):
        signals = ["body{background:#faf8f5}", "h1{font-family:'Instrument Serif'}",
                   '.cta{color:#D97757}']
        for a, b in ((0, 1), (0, 2), (1, 2)):
            with self.subTest(pair=(a, b)):
                self.assertEqual(["claude-default-look"], self.rules(signals[a] + "\n" + signals[b]))

    def test_supported_accent_swatches_and_utilities(self):
        for accent in ("#D97757", "#C96442", "#CC785C", "#9caf88", "#264e36",
                       "bg-emerald-700", "text-green-900"):
            with self.subTest(accent=accent):
                self.assertEqual(["claude-default-look"], self.rules(
                    'h1{font-family:Fraunces}\n.cta{color:' + accent + '}'))
                self.assertEqual([], self.rules('.cta{color:' + accent + '}'))

    def test_green_and_clay_are_only_one_signal(self):
        self.assertEqual([], self.rules('.cta{color:#d97757}\n.other{color:#264e36}'))

    def test_status_colour_does_not_complete_cluster(self):
        self.assertEqual([], self.rules(
            "h1{font-family:Fraunces}\n.warning{background:#faf8f5}\n"))

    def test_cream_text_colour_is_not_background_signal(self):
        self.assertEqual([], self.rules("h1{font-family:Fraunces;color:#faf8f5}"))

    def test_cluster_respects_comments_and_escape(self):
        for ignored in ("/* body{background:#f4f1ea} */", "body{background:#f4f1ea} /* unslop-ignore */"):
            with self.subTest(ignored=ignored):
                self.assertEqual([], self.rules("h1{font-family:Fraunces}\n" + ignored))

    def test_signals_do_not_combine_across_files(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp)
            (root / "base.css").write_text("body{background:#f4f1ea}", encoding="utf-8")
            (root / "type.css").write_text("h1{font-family:Fraunces}", encoding="utf-8")
            self.assertEqual([], SCANNER.scan(str(root), "low"))

    # ---- repeated template chrome ----

    def test_three_direct_eyebrows_are_medium(self):
        label = '<p class="tracking-widest uppercase">Overview</p>\n<h2>Routes</h2>\n'
        findings = self.scan(label * 3, "page.html")
        self.assertEqual([("eyebrow-chrome", "medium", 1)],
                         [(f["rule"], f["sev"], f["line"]) for f in findings])

    def test_eyebrow_class_order_and_inline_letter_spacing(self):
        for style in ('uppercase tracking-wide', 'tracking-wider uppercase',
                      'uppercase" style="letter-spacing: .1em'):
            with self.subTest(style=style):
                self.assertEqual(["eyebrow-chrome"], self.rules(
                    ('<span class="' + style + '">Area</span><h3>Detail</h3>') * 3, "page.tsx"))

    def test_inline_css_eyebrows_are_caught(self):
        self.assertEqual(["eyebrow-chrome"], self.rules(
            '<small style="text-transform:uppercase;letter-spacing:.1em">Area</small><h2>Routes</h2>' * 3,
            "page.html"))
        self.assertEqual([], self.rules(
            '<small style="text-transform:lowercase;letter-spacing:.1em">Area</small><h2>Routes</h2>' * 3,
            "page.html"))

    def test_eyebrows_need_repetition_both_styles_and_adjacency(self):
        for label in ('<p class="uppercase tracking-wide">Area</p><h2>Detail</h2>\n' * 2,
                      '<p class="uppercase">Area</p><h2>Detail</h2>\n' * 3,
                      '<p class="tracking-wide">Area</p><h2>Detail</h2>\n' * 3,
                      '<p class="uppercase tracking-wide">Area</p><hr/><h2>Detail</h2>\n' * 3,
                      '<p class="not-uppercase not-tracking-wide">Area</p><h2>Detail</h2>\n' * 3,
                      '<p data-label="uppercase tracking-wide">Area</p><h2>Detail</h2>\n' * 3):
            with self.subTest(label=label):
                self.assertEqual([], self.rules(label, "page.html"))

    def test_two_middle_dot_meta_runs_are_low(self):
        findings = self.scan('<p>London · Design · 2026</p>\n' * 2, "page.html")
        self.assertEqual([("middle-dot-meta", "low")], [(f["rule"], f["sev"]) for f in findings])

    def test_two_meta_strings_in_one_text_run_do_not_meet_threshold(self):
        self.assertEqual([], self.rules(
            '<p>London · Design · 2026 / Paris · Art · 2025</p>', "page.html"))

    def test_middle_dot_needs_repetition_and_markup_text(self):
        for text in ('<p>London · Design · 2026</p>',
                     'const tags = ["London · Design · 2026", "Paris · Art · 2025"];',
                     '<p data-meta="London · Design · 2026">Event</p>\n' * 2,
                     '<p>London · Design</p>\n' * 2,
                     '<script>const a="London · Design · 2026";const b="Paris · Art · 2025";</script>'):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, "page.tsx"))

    def test_three_appended_arrows_are_low(self):
        for text in ('<a href="/routes">Routes →</a>', '<button>Open →</button>',
                     '<Link to="/routes">Routes →</Link>'):
            with self.subTest(text=text):
                findings = self.scan(text * 3, "page.tsx")
                self.assertEqual([("appended-arrow", "low")], [(f["rule"], f["sev"]) for f in findings])

    def test_arrows_need_repetition_and_action_suffix(self):
        for text in ('<a>Open →</a>' * 2, '<p>A → B</p>' * 3, '<span>Open →</span>' * 3):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, "page.html"))

    def test_three_lucide_tiles_are_medium(self):
        text = ('import { MapPin as Pin } from "lucide-react";\n' +
                '<div className="bg-primary/10 rounded-lg"><Pin /></div>\n' * 3)
        findings = self.scan(text, "page.tsx")
        self.assertEqual([("tinted-icon-tiles", "medium", 2)],
                         [(f["rule"], f["sev"], f["line"]) for f in findings])

    def test_icon_tiles_allow_reordered_classes_and_coloured_tint(self):
        self.assertEqual(["tinted-icon-tiles"], self.rules(
            'import { MapPin } from "lucide-react";\n' +
            '<span className="rounded-lg p-3 bg-blue-500/10">\n<MapPin size={20} />\n</span>\n' * 3,
            "page.tsx"))

    def test_icon_tiles_need_three_tinted_rounded_lucide_wrappers(self):
        prefix = 'import { MapPin } from "lucide-react";\n'
        tile = '<div className="bg-primary/10 rounded-lg"><MapPin /></div>\n'
        for text in (prefix + tile * 2, prefix + tile.replace(' rounded-lg', '') * 3,
                     prefix + tile.replace('bg-primary/10 ', '') * 3,
                     prefix + tile.replace('<MapPin />', 'Map') * 3,
                     prefix + tile.replace('<MapPin />', '<Weather />') * 3,
                     prefix + tile.replace('bg-primary/10', 'hover:bg-primary/10') * 3,
                     prefix + tile.replace('rounded-lg', 'hover:rounded-lg') * 3,
                     prefix + tile.replace('className=', 'data-label=') * 3, tile * 3):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, "page.tsx"))

    def test_repetition_ignores_comments_and_escaped_lines(self):
        samples = [('<p class="uppercase tracking-wide">Area</p><h2>Routes</h2>', 3),
                   ('<p>London · Design · 2026</p>', 2), ('<a>Open →</a>', 3),
                   ('<div className="bg-primary/10 rounded-lg"><MapPin /></div>', 3)]
        for sample, threshold in samples:
            for ignored in ('<!-- ' + sample + ' -->', sample + ' /* unslop-ignore */'):
                with self.subTest(sample=sample, ignored=ignored):
                    text = 'import { MapPin } from "lucide-react";\n' + (sample + '\n') * (threshold - 1) + ignored
                    self.assertEqual([], self.rules(text, "page.tsx"))

    # ---- shadcn signatures and configuration discovery ----

    def test_current_and_reordered_card_classes_are_caught(self):
        for classes in ('flex flex-col gap-6 rounded-xl border bg-card py-6 text-card-foreground shadow-sm',
                        'shadow-sm text-card-foreground p-4 border rounded-lg',
                        'bg-card border shadow-sm text-card-foreground',
                        'rounded-xl border bg-card shadow-sm'):
            with self.subTest(classes=classes):
                self.assertEqual(["shadcn-default-card"], self.rules(
                    '<div className="' + classes + '">Content</div>', "card.tsx"))

    def test_card_needs_four_distinct_exact_classes_in_one_literal(self):
        for text in ('<div className="rounded-lg border bg-card">Content</div>',
                     '<div className="rounded-lg border border border">Content</div>',
                     '<div className="rounded-lg border"/><div className="bg-card shadow-sm"/>',
                     '<div className="hover:rounded-lg border-b bg-cardinal shadow-sm">Content</div>'):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, "card.tsx"))

    def test_card_class_literal_can_span_lines(self):
        self.assertEqual(["shadcn-default-card"], self.rules(
            'const card = `rounded-xl\n border\n bg-card\n shadow-sm`;', "card.tsx"))

    def test_components_json_is_scanned_in_directories(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp)
            config = '{"tailwind":{"baseColor":"zinc","cssVariables":true}}'
            (root / "components.json").write_text(config, encoding="utf-8")
            (root / "package.json").write_text(config, encoding="utf-8")
            findings = SCANNER.scan(str(root), "low")
            self.assertEqual(["components.json"], [Path(f["file"]).name for f in findings])
            self.assertEqual(["shadcn-default-card"], [f["rule"] for f in findings])
            self.assertEqual([str(root / "components.json")], list(SCANNER.iter_files(str(root))))

    def test_default_config_colours_and_cssvars_alias(self):
        for colour in ('slate', 'zinc', 'neutral', 'gray', 'stone'):
            with self.subTest(colour=colour):
                self.assertEqual(["shadcn-default-card"], self.rules(
                    '{"baseColor":"' + colour + '","cssVars":true}', "components.json"))

    def test_custom_or_invalid_configs_are_allowed(self):
        for config in ('{"tailwind":{"baseColor":"blue","cssVariables":true}}',
                       '{"baseColor":"zinc","cssVars":false}', '{"baseColor":"zinc"}',
                       '{"tailwind":null}', '[]', '{invalid json}'):
            with self.subTest(config=config):
                self.assertEqual([], self.rules(config, "components.json"))

    def test_config_escape_suppresses_finding(self):
        self.assertEqual([], self.rules(
            '{"baseColor":"zinc","cssVars":true,"note":"unslop-ignore"}', "components.json"))

    # ---- verifier round: paired positive and negative controls ----

    def test_card_apply_and_nested_quotes_are_caught(self):
        for text, name in (
            ('.card { @apply rounded-lg border bg-card text-card-foreground shadow-sm; }', "card.css"),
            ('<div className="rounded-lg border bg-card text-card-foreground shadow-sm after:content-[\'\']"/>', "card.tsx"),
            ('<div className="rounded-lg border bg-card shadow-sm after:content-[\'/*\']"/>', "card.tsx"),
        ):
            with self.subTest(text=text):
                self.assertEqual(["shadcn-default-card"], self.rules(text, name))

    def test_card_apply_and_nested_quotes_still_need_four_groups(self):
        for text, name in (
            ('.card { @apply rounded-lg border bg-card; }', "card.css"),
            ('.a { @apply rounded-lg border; } .b { @apply bg-card shadow-sm; }', "card.css"),
            ('<div className="rounded-lg border bg-card after:content-[\'shadow-sm\']"/>', "card.tsx"),
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, name))

    def test_multiline_comments_cannot_contribute_to_any_rule(self):
        for text, name in (
            ('/* archived:\nbody {background:#f4f1ea}\nh1 {font-family:Fraunces}\n--radius:0.5rem\n*/', "page.css"),
            ('<!-- archived:\n' + '<a>Open →</a>\n' * 3 + '--radius:0.5rem\n--primary:#6366f1\n-->', "page.html"),
            ('/* archived:\n' + '<a>Open →</a>\n' * 3 + '*/', "page.tsx"),
            ('// --radius:0.5rem\n// <a>Open →</a>\n' * 3, "page.js"),
            ('<div className={ /* --radius:0.5rem */ "plain" }/>', "page.tsx"),
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, name))

    def test_comment_masking_preserves_live_code_and_line_numbers(self):
        text = '/* --radius:0.5rem\nnot live */\n/* note */ .card { @apply rounded-lg border bg-card shadow-sm; }'
        self.assertEqual([("shadcn-default-card", 3)],
                         [(f["rule"], f["line"]) for f in self.scan(text)])
        for text in ('const url = "https://example.test/*path*/";\nconst card = "rounded-lg border bg-card shadow-sm";',
                     '<p>It\'s live</p><style>/* note */ :root{--radius:0.5rem}</style>'):
            with self.subTest(text=text):
                self.assertEqual(["shadcn-default-card"], self.rules(text, "page.tsx"))

    def test_escaped_default_config_key_produces_valid_cli_json(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / "components.json"
            path.write_text(r'{"tailwind":{"base\u0043olor":"zinc","cssVariables":true}}', encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"], capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertEqual("", result.stderr)
            data = json.loads(result.stdout)
            self.assertEqual([("shadcn-default-card", 1)],
                             [(f["rule"], f["line"]) for f in data["findings"]])

    def test_escaped_custom_config_and_nonscalar_values_are_clean(self):
        for config in (r'{"tailwind":{"base\u0043olor":"blue","cssVariables":true}}',
                       r'{"tailwind":{"base\u0043olor":"zinc","cssVariables":false}}',
                       '{"baseColor":[],"cssVars":true}', '{"baseColor":{},"cssVars":true}'):
            with self.subTest(config=config):
                self.assertEqual([], self.rules(config, "components.json"))

    def test_tooltip_examples_are_not_applied_eyebrow_styles(self):
        for attrs in ('''title='Example: class="uppercase tracking-wide"' ''',
                      '''title='class="uppercase" style="letter-spacing:.1em"' ''',
                      '''data-example='className={cn("uppercase tracking-wide")}' '''):
            with self.subTest(attrs=attrs):
                self.assertEqual([], self.rules(('<p ' + attrs + '>CSS</p><h2>Classes</h2>') * 3, "page.html"))

    def test_real_eyebrow_attributes_survive_quoted_tooltips(self):
        text = '''<p title='Example: class="lowercase" >' class="uppercase tracking-wide">CSS</p><h2>Classes</h2>'''
        self.assertEqual(["eyebrow-chrome"], self.rules(text * 3, "page.html"))

    def test_static_react_letter_spacing_and_jsx_comments_are_caught(self):
        for spacing in ('".1em"', "'.1em'", "2"):
            with self.subTest(spacing=spacing):
                text = '<p className="uppercase" style={{letterSpacing:' + spacing + '}}>Area</p>{/* note\n continued */}<h2>Routes</h2>\n'
                self.assertEqual(["eyebrow-chrome"], self.rules(text * 3, "page.tsx"))

    def test_react_eyebrows_need_applied_static_spacing_and_adjacency(self):
        for text in ('<p className="uppercase" data-style={{letterSpacing:".1em"}}>Area</p><h2>Routes</h2>',
                     '<p className="uppercase" style={{letterSpacing:spacing}}>Area</p><h2>Routes</h2>',
                     '<p className="uppercase" style={{letterSpacing:".1em"}}>Area</p>{divider}<h2>Routes</h2>'):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text * 3, "page.tsx"))

    def test_static_cn_and_clsx_icon_tiles_are_caught(self):
        for expression in ('cn("bg-primary/10 rounded-lg")',
                           'clsx("rounded-lg", "bg-primary/10",)',
                           "cn('bg-blue-500/10', 'rounded-lg')"):
            with self.subTest(expression=expression):
                text = 'import { MapPin as Pin } from "lucide-react";\n' + ('<div className={' + expression + '}><Pin /></div>\n') * 3
                self.assertEqual(["tinted-icon-tiles"], self.rules(text, "page.tsx"))

    def test_cn_icon_tiles_still_need_static_applied_tint_and_lucide(self):
        for attrs, icon in (('className={cn("rounded-lg")}', 'MapPin'),
                            ('data-class={clsx("rounded-lg bg-primary/10")}', 'MapPin'),
                            ('className={cn(flag && "rounded-lg bg-primary/10")}', 'MapPin'),
                            ('className={clsx("rounded-lg bg-primary/10")}', 'Weather')):
            with self.subTest(attrs=attrs, icon=icon):
                text = 'import { MapPin } from "lucide-react";\n' + ('<div ' + attrs + '><' + icon + ' /></div>\n') * 3
                self.assertEqual([], self.rules(text, "page.tsx"))

    def test_javascript_and_jsx_escaped_markup_do_not_count_as_metadata(self):
        for text, name in (
            ('const examples = ["<p>A · B · C</p>", "<p>D · E · F</p>"];', "page.js"),
            ('const example = `<p>A · B · C</p>\n<p>D · E · F</p>`;', "page.tsx"),
            ('<pre>{"<p>A · B · C</p><p>D · E · F</p>"}</pre>', "page.tsx"),
            ('<p title="<p>A · B · C</p><p>D · E · F</p>">Example</p>', "page.html"),
            ('<script>const examples=["<p>A · B · C</p>","<p>D · E · F</p>"];</script>', "page.html"),
        ):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, name))

    def test_real_jsx_metadata_after_code_examples_is_caught(self):
        text = 'const example = "<p>A · B · C</p>";\nexport const Page = () => <><p>London · Design · 2026</p>\n<p>Paris · Art · 2025</p></>;'
        self.assertEqual([("middle-dot-meta", 2)], [(f["rule"], f["line"]) for f in self.scan(text, "page.tsx")])

    def test_calendar_archive_metadata_is_not_template_chrome(self):
        self.assertEqual([], self.rules('<li>2026 · September · Archive</li>\n<li>2026 · October · Archive</li>', "page.html"))

    def test_nonarchive_metadata_triplets_still_count(self):
        self.assertEqual(["middle-dot-meta"], self.rules('<li>2026 · London · Design</li>\n<li>2025 · Paris · Art</li>', "page.html"))

    def test_rendered_static_arrow_suffixes_are_caught(self):
        for suffix in ('&rarr;', '{"→"}', "{'→'}", '<span aria-hidden="true">→</span>',
                       '<span class="sr-only">&rarr;</span>'):
            for tag in ("a", "button", "Link"):
                with self.subTest(suffix=suffix, tag=tag):
                    text = '<' + tag + '>Open ' + suffix + '</' + tag + '>\n'
                    self.assertEqual(["appended-arrow"], self.rules(text * 3, "page.tsx"))

    def test_arrows_in_strings_prefixes_attributes_and_midtext_are_clean(self):
        for text in ('const states = ["Queued →", "Running →", "Completed →"];',
                     'const example = "<a>Open →</a>";' * 3,
                     '<a>→ Open</a>' * 3, '<button>&rarr; Open</button>' * 3,
                     '<a>Open → more</a>' * 3, '<button title="Open →">Open</button>' * 3,
                     '<a>Open →{count}</a>' * 3, '<span>Open {"→"}</span>' * 3):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text, "page.tsx"))

    def test_small_green_status_pills_cannot_complete_palette_cluster(self):
        for classes in ('bg-emerald-100 text-emerald-700', 'text-green-700 bg-green-100',
                        'rounded-full text-xs text-emerald-800', 'text-green-900 text-xs rounded-full'):
            with self.subTest(classes=classes):
                text = '<style>h1{font-family:Fraunces}</style>\n<span class="' + classes + '">Published</span>'
                self.assertNotIn("claude-default-look", self.rules(text, "page.html"))

    def test_primary_green_and_clay_accents_complete_palette_cluster(self):
        for accent in ('<button class="bg-emerald-700">Go</button>', '<a class="text-green-800">Read</a>',
                       '<h1 class="text-emerald-900">Title</h1>', '<div class="btn-primary bg-green-700">Go</div>',
                       '<div class="CTA bg-green-700">Go</div>',
                       '<style>:root{--primary:#264e36}</style>', '<style>:root{--accent:#d97757}</style>',
                       '<style>:root{--brand-color:#9caf88}</style>', '<style>.btn-primary{@apply bg-emerald-700;}</style>'):
            with self.subTest(accent=accent):
                self.assertIn("claude-default-look", self.rules('<style>h1{font-family:Fraunces}</style>\n' + accent, "page.html"))

    def test_green_in_unrelated_elements_is_not_a_brand_signal(self):
        for accent in ('<div class="text-emerald-700">Count</div>', '<span class="text-green-900">Published</span>',
                       '<p class="bg-green-700">Aside</p>', '<style>.chart{color:#264e36}</style>'):
            with self.subTest(accent=accent):
                self.assertEqual([], self.rules('<style>h1{font-family:Fraunces}</style>\n' + accent, "page.html"))

    def test_demo_fixture_and_storybook_trees_are_skipped(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp)
            for sub in ("_demo", "demo", "demos", "fixtures", "storybook-static"):
                (root / sub / "nested").mkdir(parents=True)
                (root / sub / "nested" / "theme.css").write_text(':root{--radius:0.5rem}', encoding="utf-8")
            self.assertEqual([], list(SCANNER.iter_files(str(root))))
            self.assertEqual([], SCANNER.scan(str(root), "low"))

    def test_shipped_ui_and_explicit_demo_paths_are_still_scanned(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            root = Path(tmp)
            for sub in ("src", "demo"):
                (root / sub).mkdir()
                (root / sub / "theme.css").write_text(':root{--radius:0.5rem}', encoding="utf-8")
            self.assertEqual([str(root / "src" / "theme.css")], [f["file"] for f in SCANNER.scan(str(root), "low")])
            self.assertEqual(["shadcn-default-card"], [f["rule"] for f in SCANNER.scan(str(root / "demo"), "low")])

    # ---- fixtures: explicit paths exercise directories skipped in normal scans ----

    def test_clean_fixtures_have_zero_findings(self):
        root = Path(__file__).parent / "fixtures" / "clean"
        self.assertTrue(2 <= len(list(SCANNER.iter_files(str(root)))) <= 4)
        self.assertEqual([], SCANNER.scan(str(root), "low"))

    def test_every_rule_fires_on_dirty_fixtures(self):
        root = Path(__file__).parent / "fixtures" / "dirty"
        found = {f["rule"] for f in SCANNER.scan(str(root), "low")}
        self.assertEqual({r["id"] for r in SCANNER.RULES}, found)

    def test_fixtures_stay_excluded_from_skill_scan(self):
        paths = list(SCANNER.iter_files(str(Path(__file__).parents[1])))
        self.assertFalse(any("fixtures" in Path(p).parts for p in paths))

    def test_cli_json_shape_severity_and_high_exit_count(self):
        root = Path(__file__).parent / "fixtures" / "dirty"
        for severity in ("low", "high"):
            with self.subTest(severity=severity):
                result = subprocess.run([sys.executable, str(SCRIPT), str(root), "--json",
                                         "--severity", severity, "--max", "1"],
                                        capture_output=True, text=True)
                data = json.loads(result.stdout)
                self.assertEqual({"path", "files_scanned", "counts", "vibe_score", "verdict", "findings"}, set(data))
                self.assertEqual(data["counts"]["high"], result.returncode)
                for finding in data["findings"]:
                    self.assertEqual({"rule", "label", "sev", "fix", "file", "line", "snippet"}, set(finding))
                if severity == "high":
                    self.assertEqual({"high"}, {f["sev"] for f in data["findings"]})
                else:
                    self.assertEqual({"high", "medium", "low"}, {f["sev"] for f in data["findings"]})

    def test_cli_clean_and_missing_path_exit_codes(self):
        root = Path(__file__).parent / "fixtures" / "clean"
        clean = subprocess.run([sys.executable, str(SCRIPT), str(root), "--max", "1"],
                               capture_output=True, text=True)
        self.assertEqual(0, clean.returncode)
        self.assertIn("Clean, no tells detected", clean.stdout)
        missing = subprocess.run([sys.executable, str(SCRIPT), str(root / "absent.css")],
                                 capture_output=True, text=True)
        self.assertEqual(2, missing.returncode)
        self.assertIn("path not found", missing.stderr)

    # ---- verdict: low-severity noise must not read as STRONG ----

    def test_many_low_findings_never_reach_strong(self):
        self.assertEqual("Mostly clean, minor tells",
                         SCANNER.verdict({"low": 40}, 40))

    def test_three_highs_reach_strong(self):
        self.assertEqual("STRONG AI-default look", SCANNER.verdict({"high": 3}, 9))

    def test_clean_is_clean(self):
        self.assertEqual("Clean, no tells detected", SCANNER.verdict({}, 0))


if __name__ == "__main__":
    unittest.main()
