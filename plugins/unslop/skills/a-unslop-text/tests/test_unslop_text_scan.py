import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "unslop_text_scan.py"
SPEC = importlib.util.spec_from_file_location("unslop_text_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class ScannerTests(unittest.TestCase):
    def scan_text(self, text):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text(text, encoding="utf-8")
            return SCANNER.scan(str(path), "low")

    def test_literal_landscape_navigation_and_ecosystem_pass(self):
        findings, _ = self.scan_text(
            "Use landscape orientation for the image. "
            "The app navigates to the next page. "
            "A pond ecosystem has insects."
        )
        self.assertEqual([], findings)

    def test_consultant_compound_is_high(self):
        findings, _ = self.scan_text("The competitive landscape keeps changing.")
        self.assertEqual(["consultant-compound"], [item["rule"] for item in findings])
        self.assertEqual("high", findings[0]["sev"])

    def test_rhetorical_unpack_fails_but_tuple_operation_passes(self):
        rhetorical, _ = self.scan_text("Let's unpack this before deciding.")
        technical, _ = self.scan_text("The function returns three values; unpack the tuple first.")
        self.assertEqual(["high-signal-vocab"], [item["rule"] for item in rhetorical])
        self.assertEqual([], technical)

    def test_house_words_need_a_cluster_and_count_same_line(self):
        one, _ = self.scan_text("The plan is robust.")
        two, _ = self.scan_text("The robust plan is comprehensive.")
        self.assertEqual([], one)
        self.assertEqual(2, len(two))
        self.assertEqual({"medium"}, {item["sev"] for item in two})

    def test_frequency_rule_requires_two_hits(self):
        one, _ = self.scan_text("This is crucial.")
        two, _ = self.scan_text("This is crucial and ultimately useful.")
        self.assertFalse(any(item["rule"] == "frequency-words" for item in one))
        self.assertEqual(2, len([item for item in two if item["rule"] == "frequency-words"]))

    def test_frontmatter_quotes_code_and_allow_comments_are_ignored(self):
        findings, words = self.scan_text(
            "---\ntitle: Delve into this\n---\n"
            "> Delve into this quoted sentence.\n"
            "`delve into this literal`\n"
            "Delve into this allowed example. <!-- unslop-ignore -->\n"
            "One visible sentence.\n"
        )
        self.assertEqual([], findings)
        self.assertEqual(3, words)

    def test_dash_house_rule_still_applies_inside_quotes(self):
        findings, _ = self.scan_text('A quoted "range — still blocked" appears here.')
        self.assertEqual(["em-dash"], [item["rule"] for item in findings])

    def test_worn_origin_template_is_flagged(self):
        findings, _ = self.scan_text("I saw a gap in the available tools, so I built this one.")
        self.assertEqual(["social-template"], [item["rule"] for item in findings])
        self.assertEqual("medium", findings[0]["sev"])

    def test_dropped_pronoun_opener_passes(self):
        findings, _ = self.scan_text(
            "Made a free guide for people setting up their first server."
        )
        self.assertEqual([], findings)

    def test_many_high_findings_return_boolean_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "many.md"
            path.write_text("—" * 300, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(1, result.returncode)


if __name__ == "__main__":
    unittest.main()
