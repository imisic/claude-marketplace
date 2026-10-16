"""Regression tests for surface findings, test-integrity diffs, and CLI compatibility."""
import importlib.util
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT = Path(__file__).parents[1] / "scripts" / "unslop_code_scan.py"
SPEC = importlib.util.spec_from_file_location("unslop_code_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)
FIXTURES = Path(__file__).parent / "fixtures"


class ScannerTests(unittest.TestCase):
    def scan(self, text, name="sample.py"):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / name
            path.parent.mkdir(parents=True, exist_ok=True)
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
        for name in ("getUserDataFromApiResponseHandler", "getActiveUserApiJsonPayload",
                     "get_active_user_api_json_payload"):
            with self.subTest(name=name):
                self.assertEqual(["verbose-naming"], self.rules(f"def {name}():\n    pass\n"))

    def test_five_segment_identifiers_are_allowed(self):
        for name in ("getUserFromApiResponse", "getUserForApiResponse", "getUserWithApiResponse",
                     "getUserAndApiResponse", "getUserApiResponseHandler", "getUserApiResponseFunction"):
            with self.subTest(name=name):
                self.assertNotIn("verbose-naming", self.rules(f"function {name}() {{}}", "a.js"))
        for name in ("getUserApiJsonPayload", "getUserFromApi", "buildItemListJsonLd",
                     "getCollectionPageJsonLd", "editItemIsComingSoon", "exchangeCodeForUserInfo",
                     "getWebSiteWithSearchJsonLd", "get_user_from_api_response"):
            with self.subTest(name=name):
                self.assertNotIn("verbose-naming", self.rules(f"public function {name}() {{}}", "a.php"))

    def test_verbose_names_only_fire_on_definitions(self):
        name = "getUserDataFromApiResponseHandler"
        for text, suffix in ((f"async def {name}():\n    pass", "py"),
                             (f"public static function {name}(): array {{}}", "php"),
                             (f"const {name} = () => {{}};", "ts"),
                             (f"    {name}() {{}}", "js"),
                             (f"public static Result {name}() {{}}", "java"),
                             (f"func (s *Service) {name}() {{}}", "go"),
                             (f"${name} = null;", "php")):
            with self.subTest(text=text):
                self.assertEqual(["verbose-naming"], self.rules(text, "a." + suffix))
        for text in (f"{name}();", f"result = {name}()", f"return {name}();",
                     f"await {name}();", f"new {name}();", f"$this->{name}();",
                     f"Service::{name}();", f'<input id="{name}">',
                     f'const id = "{name}";', f"// {name}",
                     "const ZERO_RESULT_QUERY_MAX_PER_DAY = 200;"):
            with self.subTest(text=text):
                self.assertNotIn("verbose-naming", self.rules(text, "a.php"))

    # ---- CMT: `--` opens a SQL comment, not a shell flag ----

    def test_shell_long_flags_are_not_comments(self):
        self.assertEqual([], self.rules(
            'rsync --archive --delete --comments "nightly" src/ dst/\n', "a.sh"))

    def test_real_sql_comment_still_matches(self):
        self.assertEqual(["narrating-comment"], self.rules(
            "-- Step 1: create the table\nCREATE TABLE t (id int);\n", "a.sql"))

    # ---- narrating-comment: adjacency and explicit steps ----

    def test_long_comment_carrying_a_reason_is_allowed(self):
        self.assertEqual([], self.rules(
            "# Retry once before failing the job: the upstream API drops the first request\n"
            "# after a cold start, and its own docs recommend a single retry.\n", "a.sh"))

    def test_short_restating_comment_is_still_caught(self):
        for text in ("# increment i\ni += 1\n", "// increment i\n$i++;\n",
                     "# increment the counter\ncounter += 1\n", "# decrement i\n--i;\n",
                     "// Return the result\nreturn result;\n", "// Save invoice\nsaveInvoice();\n"):
            with self.subTest(text=text):
                self.assertEqual(["narrating-comment"], self.rules(text))

    def test_explicit_step_narration_is_caught(self):
        for prefix in ("#", "//"):
            for text in ("Step 1", "Now we connect", "First, we connect", "Next, we connect",
                         "Finally, we close", "Step 2: " + "a long explanation " * 6):
                with self.subTest(prefix=prefix, text=text):
                    self.assertIn("narrating-comment", self.rules(f"{prefix} {text}\n"))

    def test_docblock_lines_are_exempt_from_narration(self):
        for suffix in ("php", "js"):
            for text in ("/**\n * Create a new note\n * Get the application secret key\n */\n",
                         " * Step 1\n * Now we connect\n * First, we connect\n",
                         "/**\n// Step 1\n# Now we connect\n*/\n",
                         "/** Step 1 */\n"):
                with self.subTest(suffix=suffix, text=text):
                    self.assertNotIn("narrating-comment", self.rules(text, "a." + suffix))
        self.assertIn("narrating-comment", self.rules("/** ignored */\n# Step 1\n"))

    def test_section_labels_and_nonadjacent_or_different_code_are_allowed(self):
        for text in ("// Initialize database connection\n$db = new PDO($dsn);\n",
                     "// Create a new note\nif ($ready) {\n    saveNote();\n}\n",
                     "# Initialize database connection\n{\nconnect()\n}\n",
                     "# First, validate input\nvalidate(request)\n",
                     "# increment i\n\ni += 1\n", "# increment i\nsave()\ni += 1\n",
                     "# increment i\nj += 1\n", "# increment i\ni += 10\n",
                     "# increment i\n# i += 1\n", "# increment i\n",
                     "const label = '// Step 1';"):
            with self.subTest(text=text):
                self.assertNotIn("narrating-comment", self.rules(text))

    # ---- the loud tells must keep firing ----

    def test_placeholder_stub_is_high_and_bug_class(self):
        findings = self.scan("def f():\n    # ... rest of your code\n    pass\n")
        self.assertEqual(["placeholder-comment"], [f["rule"] for f in findings])
        self.assertEqual("high", findings[0]["sev"])
        self.assertEqual("bug", findings[0]["class"])

    def test_chat_artifact_is_caught(self):
        self.assertIn("chat-artifact", self.rules(
            "# Here's the updated code for your handler\nx = 1\n"))

    def test_assistant_instructions_after_preambles_are_caught(self):
        for text in ("# Note: I've updated this", "# Note: you'll need to configure this",
                     "# Remember to replace the token", "# Important: make sure you run this",
                     "// Tip: you'll need to add the path", "# Keep in mind: I'll fix this now"):
            with self.subTest(text=text):
                self.assertIn("chat-artifact", self.rules(text))

    def test_invariant_preambles_are_allowed(self):
        for text in ("# Note: writes must remain atomic", "# Remember: retries are bounded",
                     "// Important: order is stable", "# Tip: cache entries expire after a minute",
                     "# Keep in mind: offsets are in bytes", "# Important: you must hold the lock",
                     "# Note: you can read committed snapshots", "# Tip: to run faster, batch writes"):
            with self.subTest(text=text):
                self.assertNotIn("chat-artifact", self.rules(text))

    def test_bare_except_is_bug_class(self):
        findings = self.scan("try:\n    f()\nexcept:\n    pass\n")
        self.assertEqual(["swallowed-errors"], [f["rule"] for f in findings])
        self.assertEqual("bug", findings[0]["class"])

    def test_empty_and_log_only_python_handlers_are_caught(self):
        for header in ("except:", "except Exception:", "except BaseException as exc:"):
            for body in ("", "    pass\n", "    ...\n", "    # failure ignored\n",
                         '    print("failed")\n', '    logger.exception("failed")\n',
                         '    logger.error(\n        "failed"\n    )\n'):
                with self.subTest(header=header, body=body):
                    self.assertIn("swallowed-errors", self.rules("try:\n    save()\n" + header + "\n" + body))

    def test_handled_python_errors_are_allowed(self):
        for header in ("except:", "except Exception:", "except BaseException as exc:"):
            for body in ('    logger.exception("failed")\n    raise\n',
                         '    print("failed")\n    return None\n',
                         '    logger.error("failed")\n    raise WriteError()\n',
                         "    recover()\n", "    if retry:\n        raise\n"):
                with self.subTest(header=header, body=body):
                    self.assertNotIn("swallowed-errors", self.rules("try:\n    save()\n" + header + "\n" + body))

    def test_python_handler_stops_at_dedent_and_supports_inline_suites(self):
        self.assertIn("swallowed-errors", self.rules("try:\n    save()\nexcept Exception:\n    pass\nraise OtherError()\n"))
        self.assertIn("swallowed-errors", self.rules("except Exception: print('failed')\n"))
        self.assertNotIn("swallowed-errors", self.rules("except Exception: print('failed'); raise\n"))
        self.assertNotIn("swallowed-errors", self.rules("except ValueError:\n    pass\n"))
        self.assertNotIn("swallowed-errors", self.rules("except Exception: return None\n"))

    def test_javascript_empty_catches_are_still_caught(self):
        for suffix in ("js", "ts"):
            with self.subTest(suffix=suffix):
                self.assertIn("swallowed-errors", self.rules("try { save(); } catch (err) {}", "a." + suffix))
                self.assertNotIn("swallowed-errors", self.rules("try { save(); } catch (err) { throw err; }", "a." + suffix))

    def test_success_logging_is_allowed_and_emoji_is_counted_once(self):
        for call in ("print", "console.log", "println", "fmt.Println", "System.out.println"):
            for message in ("Successfully saved", "Done!"):
                with self.subTest(call=call, message=message):
                    self.assertEqual([], self.rules(f'{call}("{message}")'))
            findings = self.scan(f'{call}("\U00002705 done")')
            self.assertEqual(["emoji-in-code"], [f["rule"] for f in findings])

    def test_dummy_markers_and_remaining_log_marker_still_fire(self):
        for text in ('key = "YOUR_API_KEY"', 'print("Here we go")'):
            self.assertIn("boilerplate-marker", self.rules(text))
        self.assertNotIn("boilerplate-marker", self.rules('key = read_secret()'))

    def test_example_domain_in_documentation_and_form_hints_is_allowed(self):
        for text in ('placeholder="you@example.com">',
                     'placeholder="https://example.com" value="<?= e($url) ?>">',
                     "placeholder='https://example.com'>",
                     '<p class="help">Absolute URL (https://example.com/page).</p>',
                     '<li>Absolute (<code class="url">https://example.com</code>)</li>',
                     " * in subdirectories (e.g., 'example.com/myapp/').",
                     " * sc-domain:example.com keeps a colon.",
                     "/**\nAn example.com installation.\n*/",
                     "// See https://example.com for the URL format."):
            with self.subTest(text=text):
                self.assertNotIn("boilerplate-marker", self.rules(text, "a.php"))

    def test_runtime_example_domains_and_other_placeholders_still_fire(self):
        for text in ('endpoint = "https://example.com"',
                     'const endpoint = "you@example.com";',
                     '<a href="https://example.com">Service</a>',
                     '<script>const endpoint = "https://example.com";</script>',
                     '<input placeholder="example.com"><script>const endpoint = "https://example.com";</script>',
                     '<input placeholder="YOUR_API_KEY">', '// YOUR_API_KEY',
                     '<p>lorem ipsum</p>', '<p>John Doe</p>'):
            with self.subTest(text=text):
                self.assertIn("boilerplate-marker", self.rules(text, "a.php"))

    def test_fallbacks_are_left_to_human_review(self):
        self.assertNotIn("fallback-masking", {rule["id"] for rule in SCANNER.RULES})
        for text in ("config = payload or {}", "rows = payload ?? []", "options = payload ?? {}",
                     'value = getattr(item, "name", None)', "$eng = $engagement ?? [];"):
            with self.subTest(text=text):
                self.assertEqual([], self.rules(text))

    def test_required_values_and_explicit_getattr_defaults_are_allowed(self):
        for text in ("config = payload", "rows = payload ?? loadRows()", 'value = getattr(item, "name", "anonymous")'):
            self.assertEqual([], self.rules(text))

    def test_checker_suppressions_without_reasons_are_caught(self):
        for text in ("x = f()  # type: ignore", "x = f()  # type: ignore[arg-type]",
                     "x = f()  # noqa", "x = f()  # noqa: E501, F401", "// @ts-ignore",
                     "// @ts-expect-error", "// eslint-disable", "// eslint-disable-next-line no-console",
                     "const result = value as any;", "const result = value as unknown as Result;"):
            with self.subTest(text=text):
                findings = [f for f in self.scan(text) if f["rule"] == "checker-suppression"]
                self.assertEqual(1, len(findings))
                self.assertEqual(("medium", "bug"), (findings[0]["sev"], findings[0]["class"]))

    def test_checker_suppressions_with_reasons_are_allowed(self):
        for text in ("x = f()  # type: ignore[arg-type]  upstream annotation is wrong",
                     "x = f()  # noqa: E501  reason", "// @ts-expect-error: upstream types wrong",
                     "// @ts-ignore: tracked upstream issue", "// eslint-disable no-console -- CLI output",
                     "const result = value as any; // vendor has no types",
                     "const result = value as unknown as Result; /* upstream type mismatch */"):
            with self.subTest(text=text):
                self.assertNotIn("checker-suppression", self.rules(text))

    def test_change_narration_is_caught(self):
        for text in ("# Updated to match responses", "// Changed from the previous helper",
                     "# Modified so errors propagate", "# Fixed the retry loop", "// Refactored to share setup",
                     "# Previously this was inline", "// Old: transport", "# New: transport"):
            with self.subTest(text=text):
                self.assertIn("change-narration", self.rules(text))

    def test_continuing_rationale_is_allowed(self):
        self.assertNotIn("change-narration", self.rules("# Retries stop here because the request may have committed."))
        self.assertNotIn("change-narration", self.rules('status = "Updated to current version"'))

    def test_debris_filenames_are_checked_at_any_depth(self):
        for name in ("IMPLEMENTATION_SUMMARY.md", "docs/API_SUMMARY.md", "docs/deep/COMPLETED.md",
                     "CHANGES_MADE.md", "notes/FIX_NOTES.md"):
            with self.subTest(name=name):
                findings = self.scan("", name)
                self.assertEqual(["repo-debris"], [f["rule"] for f in findings])
                self.assertEqual(("medium", "cosmetic"), (findings[0]["sev"], findings[0]["class"]))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            nested = Path(tmp) / "docs"
            nested.mkdir()
            (nested / "COMPLETED.md").write_text("# Here's the updated code", encoding="utf-8")
            (nested / "guide.md").write_text("# Here's the updated code", encoding="utf-8")
            self.assertEqual(["repo-debris"], [f["rule"] for f in SCANNER.scan(tmp, "low")])

    def test_regular_documentation_and_filename_escape_are_allowed(self):
        for name in ("docs/README.md", "notes/SUMMARY.md", "docs/COMPLETED.py"):
            self.assertNotIn("repo-debris", self.rules("", name))
        self.assertEqual([], self.rules("<!-- unslop-ignore: retained as a release record -->", "COMPLETED.md"))

    def diff(self, removed, added, name="tests/test_invoice.py"):
        old = "\n".join("-" + line for line in removed)
        new = "\n".join("+" + line for line in added)
        return (f"diff --git a/{name} b/{name}\n--- a/{name}\n+++ b/{name}\n"
                f"@@ -12,{len(removed)} +20,{len(added)} @@\n" + old + ("\n" if old else "") + new + "\n")

    def test_diff_literals_and_comments_are_data(self):
        for text in ('message = "Please use .skip() to omit optional data"',
                     'message = "assert failed for malformed input"',
                     'const text = "expect(true).toBe(true)";',
                     'text = "@pytest.mark.skipif(True)"',
                     '# assert True; test.skip("case", run)',
                     '/* t.Skipf("pending"); assert True */',
                     'message = """\nassert True\nt.SkipNow()\n"""'):
            for direction in ("+", "-"):
                with self.subTest(text=text, direction=direction):
                    diff = self.diff(text.splitlines() if direction == "-" else [],
                                     text.splitlines() if direction == "+" else [])
                    self.assertEqual([], SCANNER.scan_diff(diff, "low"))
        for text, direction, rule in (("assert result", "-", "test-assertion-removed"),
                                       ("test.skip('case', run)", "+", "test-skip-added"),
                                       ("assert True", "+", "test-tautology-added")):
            findings = SCANNER.scan_diff(self.diff([text] if direction == "-" else [],
                                                   [text] if direction == "+" else []), "low")
            self.assertEqual([rule], [f["rule"] for f in findings])

    def test_regression_module_as_added_diff_has_no_integrity_findings(self):
        lines = Path(__file__).read_text().splitlines()
        self.assertEqual([], SCANNER.scan_diff(self.diff([], lines), "low"))

    def test_diff_context_preserves_quote_and_comment_state(self):
        for opening, closing in (('message = """', '"""'), ('/*', '*/')):
            diff = ('--- a/tests/test_invoice.py\n+++ b/tests/test_invoice.py\n'
                    '@@ -10,3 +10,3 @@\n ' + opening + '\n'
                    '-assert failed for malformed input\n'
                    '+t.Skipf("pending"); assert True\n ' + closing + '\n')
            with self.subTest(opening=opening):
                self.assertEqual([], SCANNER.scan_diff(diff, "low"))
        diff = ('--- a/tests/test_invoice.py\n+++ b/tests/test_invoice.py\n'
                '@@ -10,4 +10,4 @@\n message = """\n text\n """\n'
                '-assert result\n+assert (True)\n')
        self.assertEqual(["test-assertion-removed", "test-tautology-added"],
                         [f["rule"] for f in SCANNER.scan_diff(diff, "low")])

    def test_standard_skip_variants(self):
        for text in ('@pytest.mark.skipif(True, reason="temporary")',
                     '@pytest.mark.xfail(reason="pending")', 'pytest.skip("pending")',
                     'pytest.xfail("pending")', '@unittest.skip("pending")',
                     '@unittest.skipIf(True, "pending")', '@unittest.skipUnless(False, "pending")',
                     '@skipIf(True, "pending")', '@unittest.expectedFailure',
                     'test.skip("case", run)', 'describe.skip("case", run)', 'xdescribe("case", run)',
                     'xit("case", run)', 'it . skip ("case", run)',
                     't.Skipf("pending")', 't.SkipNow()',
                     '$this->markTestSkipped("pending");', '$this->markTestIncomplete("pending");'):
            with self.subTest(text=text):
                self.assertEqual(["test-skip-added"], [f["rule"] for f in SCANNER.scan_diff(self.diff([], [text]), "low")])
        for text in ('skip_reason = "pending"', 'xfail = False', 't.Skipper()',
                     'transaction.error()', '@unittest.skipper', 'pytest.mark.skipping',
                     'marker = pytest.mark.skip', 'const key = obj.assert;', '$assert = value;'):
            with self.subTest(text=text):
                self.assertEqual([], SCANNER.scan_diff(self.diff([], [text]), "low"))

    def test_tautology_spacing_parentheses_and_continuation(self):
        for lines in (("assert (True)",), ("assert (( True ))",),
                      ("assert(True)",), ("expect ( ( true ) ).toBe ( ( true ) )",),
                      ("expect (true).toBe(true)",), ("expect((true)).toBe((true))",),
                      ("expect(true)", "    .toBe(true)")):
            with self.subTest(lines=lines):
                findings = SCANNER.scan_diff(self.diff([], lines), "low")
                self.assertEqual(["test-tautology-added"], [f["rule"] for f in findings])
                self.assertEqual(20, findings[0]["line"])
        for lines in (("assert (result)",), ("assert (True) == result",),
                      ("expect(false)", "    .toBe(true)"), ("expect(true)", "    .toBe(result)")):
            with self.subTest(lines=lines):
                self.assertEqual([], SCANNER.scan_diff(self.diff([], lines), "low"))

    def test_diff_base_and_stdin_ignore_quoted_data(self):
        diff = self.diff(['message = "assert failed for malformed input"'],
                         ['message = "Please use .skip() to omit optional data"'])
        code, report = self.cli(["--diff", "--json"], diff)
        self.assertEqual((0, []), (code, report["findings"]))
        with patch.object(SCANNER.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=diff)):
            code, report = self.cli(["--diff-base", "main", "--json"])
        self.assertEqual((0, []), (code, report["findings"]))

    def test_chat_change_reports_and_reader_instructions(self):
        for text in ("# Note: I have updated this code", "# I've added retry handling",
                     "// I changed the parser", "# As requested, here is the updated file",
                     "# Here is the updated code", "# Let me know", "# Hope this helps",
                     "# Remember: replace the token before running", "# Don't forget to add the path",
                     "# Do not forget to configure the token", "# I will fix this now"):
            with self.subTest(text=text):
                self.assertIn("chat-artifact", self.rules(text))
        for text in ("# Important: make sure you hold the lock during writes",
                     "# Note: make sure you preserve insertion order", "# Previously computed values remain valid",
                     "# Important: you'll need to hold the lock during writes",
                     "# Remember to update the index under the lock"):
            with self.subTest(text=text):
                self.assertNotIn("chat-artifact", self.rules(text))

    def test_type_suppression_requires_syntax(self):
        for text, name in (('const text = "Customers may cancel as any authorized user"', 'a.ts'),
                           ('<p>Works as any standard adapter.</p>', 'a.tsx'),
                           ('// folded the same as any other', 'a.ts'),
                           ('const text = "folded the same as any other"', 'a.ts'),
                           ('const directive = "// @ts-ignore"', 'a.ts'),
                           ('text = "# type: ignore"', 'a.py'),
                           ('/* as any */', 'a.ts')):
            with self.subTest(text=text):
                self.assertNotIn("checker-suppression", self.rules(text, name))
        for text, name in (('const value: any = source;', 'a.ts'),
                           ('const value = source as any;', 'a.ts'),
                           ('const value = identity<Result>(source) as any;', 'a.ts'),
                           ('const value = identity <string>(source) as any;', 'a.ts'),
                           ('value = read() # type: ignore [arg-type]', 'a.py'),
                           ('/* @ts-expect-error */', 'a.ts'), ('/* @ts-ignore */', 'a.ts')):
            with self.subTest(text=text):
                self.assertIn("checker-suppression", self.rules(text, name))
        for text, name in (('// @ts-expect-error: lib types wrong, see #12', 'a.ts'),
                           ('/* @ts-ignore: vendor types wrong */', 'a.ts'),
                           ('value = read() # type: ignore [arg-type] vendor types wrong', 'a.py'),
                           ('const value: any = source; // untyped library', 'a.ts')):
            with self.subTest(text=text):
                self.assertNotIn("checker-suppression", self.rules(text, name))

    def test_suppression_reason_stays_inside_its_comment(self):
        self.assertIn("checker-suppression", self.rules('/* @ts-ignore */ const value = source;', 'a.ts'))
        self.assertNotIn("checker-suppression", self.rules('/* @ts-ignore: vendor types wrong */ const value = source;', 'a.ts'))

    def test_broad_exception_variants_use_narrow_logging_receivers(self):
        for header in ('except (Exception,):', 'except builtins.Exception:',
                       'except ( builtins.BaseException, ) as exc:'):
            for call in ('logger.error', 'logging.exception', 'log.warning', 'console.log',
                         'self.logger.error', 'this.logger.error', 'error_log', 'Log.error'):
                with self.subTest(header=header, call=call):
                    self.assertIn("swallowed-errors", self.rules(f'try:\n    save()\n{header}\n    {call}("failed")\n'))
            for body in ('    transaction.error()\n', '    service.exception()\n', '    logger.error("failed")\n    raise\n'):
                with self.subTest(header=header, body=body):
                    self.assertNotIn("swallowed-errors", self.rules(f'try:\n    save()\n{header}\n' + body))
        self.assertNotIn("swallowed-errors", self.rules('except (ValueError,):\n    pass\n'))

    def test_change_history_only_in_real_comments(self):
        for text, name in (('# Updated  to use a shared parser', 'a.py'),
                           ('// Now uses a shared parser', 'a.ts'),
                           ('# Previously this was inline', 'a.py'),
                           ('# This was changed to share the parser', 'a.py'),
                           ('/* Updated to share setup */', 'a.css')):
            with self.subTest(text=text):
                self.assertIn("change-narration", self.rules(text, name))
        for text, name in (('const label = "// New: subscription";', 'a.ts'),
                           ('a { content: "// New: pending"; }', 'a.css'),
                           ('# Previously computed values must remain available for rollback.', 'a.py'),
                           ('text = """\n# Updated to share setup\n"""', 'a.py'),
                           ('// Updated values must remain available', 'a.ts')):
            with self.subTest(text=text):
                self.assertNotIn("change-narration", self.rules(text, name))

    def test_fixture_scope_documentation_matches_traversal(self):
        catalog = (SCRIPT.parents[1] / 'references' / 'tells.md').read_text()
        self.assertIn('`fixtures` directories are excluded from project traversal', catalog)
        self.assertIn('a direct path still scans them', catalog)
        self.assertNotIn('fixtures stay in normal scan scope', catalog)

    def test_removed_assertions_fire_only_in_test_paths(self):
        for name in ("test_invoice.py", "invoice_test.go", "invoice.test.ts", "invoice.spec.js",
                     "pkg/tests/invoice.py", "pkg/__tests__/invoice.js"):
            with self.subTest(name=name):
                findings = SCANNER.scan_diff(self.diff(["    assert result == 42"], [], name), "low")
                self.assertEqual(["test-assertion-removed"], [f["rule"] for f in findings])
                self.assertEqual((name, 12, "high", "bug"), (findings[0]["file"], findings[0]["line"], findings[0]["sev"], findings[0]["class"]))
        for line in ("expect(result).toBe(42)", "self.assertEqual(result, 42)"):
            self.assertEqual(1, len(SCANNER.scan_diff(self.diff([line], []), "low")))
        for name in ("src/invoice.py", "src/contest.py", "docs/testing.md"):
            self.assertEqual([], SCANNER.scan_diff(self.diff(["assert value"], [], name), "low"))

    def test_added_skip_markers_are_high_bug_findings(self):
        for text in ("@pytest.mark.skip", "@pytest.mark.xfail", "describe.skip('case', run)",
                     "it.skip('case', run)", "xit('case', run)", "@Disabled", 't.Skip("pending")'):
            with self.subTest(text=text):
                findings = SCANNER.scan_diff(self.diff([], [text]), "low")
                self.assertEqual(["test-skip-added"], [f["rule"] for f in findings])
                self.assertEqual(("high", "bug", 20), (findings[0]["sev"], findings[0]["class"], findings[0]["line"]))
                self.assertEqual([], SCANNER.scan_diff(self.diff([], [text], "src/invoice.py"), "low"))

    def test_new_tautologies_are_high_bug_findings(self):
        for text in ("assert True", "    assert True, 'always passes'", "expect(true).toBe(true);"):
            with self.subTest(text=text):
                findings = SCANNER.scan_diff(self.diff([], [text]), "low")
                self.assertEqual(["test-tautology-added"], [f["rule"] for f in findings])
                self.assertEqual(("high", "bug"), (findings[0]["sev"], findings[0]["class"]))
        for text in ("assert True == result", "assert TrueValue", "assert result", "expect(result).toBe(true)"):
            self.assertEqual([], SCANNER.scan_diff(self.diff([], [text]), "low"))

    def test_diff_direction_context_comments_and_escape(self):
        self.assertEqual([], SCANNER.scan_diff(self.diff(["@pytest.mark.skip"], ["assert value"]), "low"))
        for text in ("# assert value", "// expect(value)", "assert value # unslop-ignore"):
            self.assertEqual([], SCANNER.scan_diff(self.diff([text], []), "low"))
        for text in ("assert True # unslop-ignore", "@pytest.mark.skip # unslop-ignore"):
            self.assertEqual([], SCANNER.scan_diff(self.diff([], [text]), "low"))
        context = self.diff([], ["assert result"]) + " assert True\n"
        self.assertEqual([], SCANNER.scan_diff(context, "low"))

    def test_diff_multiple_hunks_deleted_files_and_quoted_paths(self):
        diff = ('--- "a/tests/test invoice.py"\n+++ /dev/null\n@@ -5,1 +0,0 @@\n-assert value\n'
                '\\ No newline at end of file\n'
                '--- a/invoice.test.ts\n+++ b/invoice.test.ts\n@@ -2,0 +3,1 @@\n+it.skip("case", run)\n'
                '@@ -8,0 +10,1 @@\n+expect(true).toBe(true)\n')
        findings = SCANNER.scan_diff(diff, "high")
        self.assertEqual([("tests/test invoice.py", 5), ("invoice.test.ts", 3), ("invoice.test.ts", 10)],
                         [(f["file"], f["line"]) for f in findings])

    def test_clean_fixtures_have_zero_findings(self):
        self.assertEqual(3, len(list((FIXTURES / "clean").iterdir())))
        self.assertEqual([], SCANNER.scan(str(FIXTURES / "clean"), "low"))

    def test_every_rule_fires_on_a_dirty_fixture(self):
        findings = SCANNER.scan(str(FIXTURES / "dirty"), "low")
        for path in (FIXTURES / "dirty").rglob("*.diff"):
            findings.extend(SCANNER.scan_diff(path.read_text(encoding="utf-8"), "low"))
        self.assertEqual({r["id"] for r in SCANNER.RULES}, {f["rule"] for f in findings})

    def test_project_scan_skips_fixtures_but_direct_path_scans_them(self):
        files = set(SCANNER.iter_files(str(SCRIPT.parents[1])))
        self.assertIn(str(Path(__file__)), files)
        self.assertNotIn(str(FIXTURES / "dirty" / "handler.py"), files)
        self.assertIn(str(FIXTURES / "dirty" / "handler.py"), set(SCANNER.iter_files(str(FIXTURES / "dirty"))))

    def cli(self, args, stdin=""):
        output = io.StringIO()
        with patch.object(sys, "argv", [str(SCRIPT)] + args), patch.object(sys, "stdin", io.StringIO(stdin)), contextlib.redirect_stdout(output):
            with self.assertRaises(SystemExit) as result:
                SCANNER.main()
        return result.exception.code, json.loads(output.getvalue())

    def test_diff_stdin_cli_keeps_json_shape_and_high_count_exit(self):
        diff = (FIXTURES / "dirty" / "integrity.diff").read_text(encoding="utf-8")
        code, report = self.cli(["--diff", "--json"], diff)
        self.assertEqual(3, code)
        self.assertEqual({"path", "files_scanned", "counts", "class_counts", "slop_score", "verdict", "findings"}, set(report))
        self.assertEqual(1, report["files_scanned"])
        self.assertEqual({"high": 3}, report["counts"])

    def test_diff_base_runs_git_diff_without_a_shell(self):
        diff = self.diff(["assert value"], [])
        with patch.object(SCANNER.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout=diff)) as run:
            code, report = self.cli(["--diff-base", "main", "--json"])
        self.assertEqual(1, code)
        self.assertEqual("test-assertion-removed", report["findings"][0]["rule"])
        self.assertEqual(["git", "diff", "--no-ext-diff", "--no-color", "main", "--"], run.call_args.args[0])
        self.assertTrue(run.call_args.kwargs["check"])

    def test_diff_base_also_accepts_diff_flag_and_repo_path(self):
        with patch.object(SCANNER.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, stdout="")) as run:
            code, report = self.cli([str(SCRIPT.parents[1]), "--diff", "--diff-base", "main", "--json"])
        self.assertEqual(0, code)
        self.assertEqual([], report["findings"])
        self.assertEqual(str(SCRIPT.parents[1]), run.call_args.kwargs["cwd"])

    def test_new_surface_rules_keep_the_line_escape(self):
        for text in ("const result = value as any;", "# Updated to reuse the response",
                     "function getUserDataFromApiResponseHandler() {}", "# Step 1"):
            with self.subTest(text=text):
                self.assertTrue(self.rules(text))
                self.assertEqual([], self.rules(text + " // unslop-ignore"))

    def test_failed_diff_base_exits_two(self):
        with patch.object(SCANNER.subprocess, "run", side_effect=subprocess.CalledProcessError(128, ["git", "diff"])), contextlib.redirect_stderr(io.StringIO()):
            with patch.object(sys, "argv", [str(SCRIPT), "--diff-base", "missing"]), self.assertRaises(SystemExit) as result:
                SCANNER.main()
        self.assertEqual(2, result.exception.code)

    def test_normal_cli_counts_only_high_findings(self):
        code, report = self.cli([str(FIXTURES / "dirty" / "handler.py"), "--json"])
        self.assertEqual(2, code)
        self.assertEqual(report["counts"]["high"], code)
        self.assertGreater(report["counts"]["medium"], 0)
        code, report = self.cli([str(FIXTURES / "dirty" / "surface.ts"), "--json"])
        self.assertEqual(0, code)
        self.assertTrue(report["findings"])

    def test_severity_filter_preserves_high_findings(self):
        code, report = self.cli([str(FIXTURES / "dirty" / "handler.py"), "--severity", "high", "--json"])
        self.assertEqual(2, code)
        self.assertEqual({"high"}, {f["sev"] for f in report["findings"]})

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
