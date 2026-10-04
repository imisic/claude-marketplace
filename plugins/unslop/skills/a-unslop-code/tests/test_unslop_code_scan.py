"""Regression tests for unslop_code_scan.

Every case here is a false positive that shipped, or the true positive its fix had to
keep. Descriptive test names once made up most of the findings on a clean repo, which is
how a scanner gets ignored.
"""
import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "unslop_code_scan.py"
SPEC = importlib.util.spec_from_file_location("unslop_code_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)


class ScannerTests(unittest.TestCase):
    def scan(self, text, name="sample.py"):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_text(text, encoding="utf-8")
            return SCANNER.scan(str(path), "low")

    def rules(self, text, name="sample.py"):
        return sorted({f["rule"] for f in self.scan(text, name)})

    # ---- verbose-naming: a test name is a sentence on purpose ----

    def test_descriptive_pytest_names_are_allowed(self):
        self.assertEqual([], self.rules(
            "def test_returns_none_on_malformed_yaml(tmp_path):\n    pass\n"
            "def test_one_file_is_one_task_regardless_of_body_checkboxes(tmp_path):\n    pass\n"))

    def test_go_and_jest_test_names_are_allowed(self):
        self.assertEqual([], self.rules(
            "func TestReturnsNoneOnMalformedYamlInput(t *testing.T) {}\n", "a.go"))
        self.assertEqual([], self.rules(
            "it('renders the user profile card when data has loaded', () => {})\n", "a.js"))

    def test_genuinely_sentence_shaped_identifier_is_still_caught(self):
        self.assertEqual(["verbose-naming"], self.rules(
            "x = getUserDataFromApiResponseHandlerFactory()\n"))

    # ---- CMT: `--` opens a SQL comment, not a shell flag ----

    def test_shell_long_flags_are_not_comments(self):
        self.assertEqual([], self.rules(
            'rsync --archive --delete --comments "nightly" src/ dst/\n', "a.sh"))

    def test_real_sql_comment_still_matches(self):
        self.assertEqual(["narrating-comment"], self.rules(
            "-- create the table\nCREATE TABLE t (id int);\n", "a.sql"))

    # ---- narrating-comment: length separates restating from explaining ----

    def test_long_comment_carrying_a_reason_is_allowed(self):
        self.assertEqual([], self.rules(
            "# Retry once before failing the job: the upstream API drops the first request\n"
            "# after a cold start, and its own docs recommend a single retry.\n", "a.sh"))

    def test_short_restating_comment_is_still_caught(self):
        self.assertEqual(["narrating-comment"], self.rules(
            "# increment the counter\ncount += 1\n"))

    # ---- the loud tells must keep firing ----

    def test_placeholder_stub_is_high_and_bug_class(self):
        findings = self.scan("def f():\n    # ... rest of your code\n    pass\n")
        self.assertEqual(["placeholder-comment"], [f["rule"] for f in findings])
        self.assertEqual("high", findings[0]["sev"])
        self.assertEqual("bug", findings[0]["class"])

    def test_chat_artifact_is_caught(self):
        self.assertIn("chat-artifact", self.rules(
            "# Here's the updated code for your handler\nx = 1\n"))

    def test_bare_except_is_bug_class(self):
        findings = self.scan("try:\n    f()\nexcept:\n    pass\n")
        self.assertEqual(["swallowed-errors"], [f["rule"] for f in findings])
        self.assertEqual("bug", findings[0]["class"])

    def test_generic_naming_is_caught(self):
        self.assertEqual(["generic-naming"], self.rules("def process_data(x):\n    return x\n"))

    def test_emoji_in_source_is_caught(self):
        self.assertEqual(["emoji-in-code"], self.rules('print("done ✅")\n'))

    # ---- escape hatch ----

    def test_unslop_ignore_line_is_skipped(self):
        self.assertEqual([], self.rules("def process_data(x):  # unslop-ignore\n    return x\n"))

    # ---- verdict: low-severity noise must not read as STRONG ----

    def test_many_low_findings_never_reach_strong(self):
        self.assertEqual("Mostly clean, minor tells", SCANNER.verdict({"low": 40}, 40))

    def test_three_highs_reach_strong(self):
        self.assertEqual("STRONG AI-written-code tells", SCANNER.verdict({"high": 3}, 9))

    def test_clean_is_clean(self):
        self.assertEqual("Clean, no surface tells detected", SCANNER.verdict({}, 0))


if __name__ == "__main__":
    unittest.main()
