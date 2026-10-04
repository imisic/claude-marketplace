"""Regression tests for devibe_scan.

Every case here is a false positive that shipped, or the true positive its fix had to
keep. A scanner that reports black drop shadows as neon glow stops being run, so each
false positive here is pinned.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "devibe_scan.py"
SPEC = importlib.util.spec_from_file_location("devibe_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class ScannerTests(unittest.TestCase):
    def scan(self, text, name="sample.css"):
        with tempfile.TemporaryDirectory() as tmp:
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

    def test_cream_page_background_is_still_caught(self):
        self.assertEqual(["claude-default-look"], self.rules("body{background:#faf6ef}\n"))

    def test_instrument_serif_is_still_caught(self):
        self.assertEqual(["claude-default-look"], self.rules(
            "body{font-family:'Instrument Serif',serif}\n"))

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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for sub in ("docs", "_archive", "mockups"):
                (root / sub).mkdir()
                (root / sub / "spec.css").write_text("body{background:#faf6ef}", encoding="utf-8")
            (root / "app.css").write_text("body{background:#faf6ef}", encoding="utf-8")
            findings = SCANNER.scan(str(root), "low")
        self.assertEqual(1, len(findings), "only the shipped stylesheet should be scanned")

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
