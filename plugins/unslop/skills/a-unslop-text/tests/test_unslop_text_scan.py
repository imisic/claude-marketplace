import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).parents[1] / "scripts" / "unslop_text_scan.py"
SPEC = importlib.util.spec_from_file_location("unslop_text_scan", SCRIPT)
SCANNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCANNER)
FIXTURES = Path(__file__).parent / "fixtures"


class ScannerTests(unittest.TestCase):
    def scan_text(self, text):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
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
        findings, _ = self.scan_text('A quoted "range \u2014 still blocked" appears here.')
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
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / "many.md"
            path.write_text("\u2014" * 300, encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), str(path), "--json"],
                capture_output=True,
                text=True,
                check=False,
            )
        self.assertEqual(1, result.returncode)


    def rule_hits(self, text, rule, severity="low"):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text(text, encoding="utf-8")
            findings, _ = SCANNER.scan(str(path), severity)
        return [item for item in findings if item["rule"] == rule]

    def test_literal_earlier_vocabulary_passes(self):
        examples = (
            "A woven tapestry from Iran covers the wall.",
            "A hand-woven tapestry is on display.",
            "A silk tapestry is in the case.",
            "A medieval tapestry hangs in the hall.",
            "The tapestry hangs on the wall.",
            "They restored a tapestry yesterday.",
            "The programming paradigm uses functions.",
            "This scientific paradigm explains the observation.",
            "The radio beacon transmits at noon.",
            "A beacon flashes beside the harbour.",
            "The Kerberos realm is EXAMPLE.ORG.",
            "The New Testament is in the case.",
        )
        for text in examples:
            with self.subTest(text=text):
                self.assertEqual([], self.rule_hits(text, "era-vocab"))

    def test_figurative_earlier_vocabulary_is_advisory(self):
        for word in ("delve", "tapestry", "realm", "beacon", "testament", "myriad", "plethora", "paradigm"):
            with self.subTest(word=word):
                hits = self.rule_hits("We describe a " + word + " of ideas.", "era-vocab")
                self.assertEqual(1, len(hits))
                self.assertEqual("medium", hits[0]["sev"])
        self.assertTrue(self.rule_hits("A rich tapestry of ideas.", "era-vocab"))
        self.assertTrue(self.rule_hits("A woven tapestry of ideas.", "era-vocab"))
        self.assertTrue(self.rule_hits("A paradigm shift is coming.", "era-vocab"))
        self.assertEqual([], self.rule_hits("A rich tapestry of ideas.", "era-vocab", severity="high"))

    def test_real_cause_corrections_pass_and_promotional_antithesis_fires(self):
        correction = "The job failed not because the file is missing but because access was denied."
        self.assertEqual([], self.scan_text(correction)[0])
        self.assertEqual([], self.rule_hits("It is not red, but blue.", "antithesis"))
        for text in ("It's not just a tool, it's a movement.", "This is not merely a tool, but a movement."):
            with self.subTest(text=text):
                self.assertTrue(self.rule_hits(text, "antithesis"))

    def test_bolded_bullet_labels_need_three_consecutive_items(self):
        for marker in ("-", "*", "+", "1."):
            for label in ("**Owner:** Casey", "**Owner**: Casey"):
                with self.subTest(marker=marker, label=label):
                    bullet = marker + " " + label + "\n"
                    self.assertEqual([], self.rule_hits(bullet, "bolded-label-list"))
                    self.assertEqual([], self.rule_hits(bullet * 2, "bolded-label-list"))
                    hits = self.rule_hits(bullet * 3, "bolded-label-list")
                    self.assertEqual([1, 2, 3], [f["line"] for f in hits])
                    self.assertEqual({"low"}, {f["sev"] for f in hits})
                    self.assertEqual(3, len(self.rule_hits(bullet * 2 + "\n" + bullet, "bolded-label-list")))
                    self.assertEqual([], self.rule_hits(bullet * 2 + "Plain text.\n" + bullet, "bolded-label-list"))
        self.assertTrue(self.rule_hits("**Owner:** Casey", "bolded-lead-in"))
        self.assertEqual([], self.rule_hits("- **Owner:** Casey", "bolded-lead-in"))

    def test_current_vocabulary_needs_three_distinct_local_words(self):
        hits = self.rule_hits("A dependable and practical plan stays steady.", "current-era-cluster")
        self.assertEqual(3, len(hits))
        self.assertEqual({"medium"}, {f["sev"] for f in hits})
        self.assertEqual([], self.rule_hits("Practical practical practical.", "current-era-cluster"))
        self.assertEqual([], self.rule_hits("A dependable practical plan.", "current-era-cluster"))
        self.assertEqual([], self.rule_hits("Practical steady " + "word " * 300 + "dependable", "current-era-cluster"))
        self.assertEqual([], self.scan_text("The problem is multifaceted.")[0])
        words = "challenge clearer dependable echoed foster leverage matters multifaceted practical prioritize quietly steady universally"
        hits = self.rule_hits(words, "current-era-cluster")
        self.assertEqual(13, len(hits))

    def test_current_vocabulary_does_not_combine_separate_windows(self):
        text = "practical " + "word " * 200 + "steady " + "word " * 200 + "dependable"
        self.assertEqual([], self.rule_hits(text, "current-era-cluster"))
        hits = self.rule_hits("practical steady dependable " + "word " * 300 + "clearer", "current-era-cluster")
        self.assertEqual({"practical", "steady", "dependable"}, {f["match"] for f in hits})

    def test_frequency_and_house_clusters_are_local_across_lines(self):
        for rule, first, second in (("frequency-words", "crucial", "vital"), ("house-vocab", "robust", "comprehensive")):
            with self.subTest(rule=rule):
                self.assertEqual(2, len(self.rule_hits(first + "\n" + "word " * 298 + second, rule)))
                self.assertEqual([], self.rule_hits(first + "\n" + "word " * 299 + second, rule))
                hits = self.rule_hits(first + " " + first + " " + "word " * 300 + second, rule)
                self.assertEqual([first, first], [f["match"] for f in hits])

    def test_local_clusters_do_not_cross_files(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            Path(tmp, "a.md").write_text("crucial robust practical steady", encoding="utf-8")
            Path(tmp, "b.md").write_text("vital comprehensive dependable", encoding="utf-8")
            findings, _ = SCANNER.scan(tmp, "low")
        self.assertEqual([], findings)

    def test_staged_reveals_are_sentence_initial(self):
        for word in ("result", "catch", "kicker", "payoff", "twist", "answer", "truth"):
            for punctuation in (":", "?"):
                with self.subTest(word=word, punctuation=punctuation):
                    self.assertTrue(self.rule_hits("The " + word + punctuation + " It works.", "staged-reveal"))
                    self.assertTrue(self.rule_hits("We checked. The " + word + punctuation + " It works.", "staged-reveal"))
                    self.assertEqual([], self.rule_hits("We recorded the " + word + punctuation + " it works.", "staged-reveal"))
        self.assertEqual([], self.scan_text("The port: 8080. The result was accepted.")[0])

    def test_significance_tails_need_comma_participle_and_determiner(self):
        for verb in ("highlighting", "underscoring", "reflecting", "symbolizing", "showcasing", "emphasizing"):
            for determiner in ("the", "its", "their", "a"):
                with self.subTest(verb=verb, determiner=determiner):
                    self.assertTrue(self.rule_hits("It changed, " + verb + " " + determiner + " role.", "significance-tail"))
                    self.assertEqual([], self.rule_hits("We are " + verb + " " + determiner + " role.", "significance-tail"))
            self.assertEqual([], self.rule_hits("It changed, " + verb + " evidence.", "significance-tail"))

    def test_copula_avoidance_is_low_and_needs_an_article(self):
        for verb in ("serves", "stands"):
            for article in ("a", "an", "the"):
                with self.subTest(verb=verb, article=article):
                    hits = self.rule_hits("It " + verb + " as " + article + " example.", "copula-avoidance")
                    self.assertEqual(1, len(hits))
                    self.assertEqual("low", hits[0]["sev"])
            self.assertEqual([], self.rule_hits("It " + verb + " as evidence.", "copula-avoidance"))
        self.assertEqual([], self.rule_hits("It stands beside the gate.", "copula-avoidance"))

    def test_renderer_citation_residue_is_high(self):
        tokens = ("contentReference", "oaicite", "oai_citation", "turn0search12", "attributableIndex", "grok_card", "grok_render_citation_card_json", "[cite: 7]", "[span_12](start_span)", "ppl-ai-file-upload")
        for token in tokens:
            with self.subTest(token=token):
                hits = self.rule_hits("The source is " + token + ".", "citation-markup")
                self.assertEqual(1, len(hits))
                self.assertEqual("high", hits[0]["sev"])
                self.assertEqual([], self.rule_hits("`" + token + "` is a literal example.", "citation-markup"))
        for text in ("The source is [7](https://example.org/paper).", "The content reference is in the note.", "turn0search has no numeric suffix.", "The citation is [cite: author]."):
            with self.subTest(text=text):
                self.assertEqual([], self.rule_hits(text, "citation-markup"))

    def test_new_rules_keep_noise_and_escape_handling(self):
        text = "The result: practical steady dependable, highlighting the source contentReference."
        for wrapped in ("> " + text, '`' + text + '`', '"' + text + '"', "```\n" + text + "\n```", text + " <!-- unslop-ignore -->", text + " <!-- voice-allow: quoted example -->"):
            with self.subTest(wrapped=wrapped):
                self.assertEqual([], self.scan_text(wrapped)[0])
        bullet = "- **Owner:** Casey\n"
        self.assertEqual([], self.rule_hits(bullet + bullet.rstrip() + " <!-- unslop-ignore -->\n" + bullet, "bolded-label-list"))

    def test_clean_fixtures_have_zero_findings(self):
        files = list((FIXTURES / "clean").iterdir())
        self.assertGreaterEqual(len(files), 2)
        self.assertLessEqual(len(files), 4)
        for path in files:
            with self.subTest(path=path.name):
                findings, _ = SCANNER.scan(str(path), "low")
                self.assertEqual([], findings)

    def test_every_rule_fires_on_a_dirty_fixture(self):
        seen = set()
        for path in (FIXTURES / "dirty").iterdir():
            findings, _ = SCANNER.scan(str(path), "low")
            seen.update(f["rule"] for f in findings)
        self.assertEqual({r["id"] for r in SCANNER.RULES}, seen)

    def test_fixture_traversal_excludes_test_fixtures(self):
        files = set(SCANNER.iter_files(str(SCRIPT.parents[1])))
        self.assertNotIn(str(FIXTURES / "dirty" / "catalog.md"), files)

    def test_scan_cli_keeps_json_shape_severity_and_exit_codes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            path = Path(tmp) / "sample.md"
            path.write_text("Delve into this.", encoding="utf-8")
            for text, code in (("Delve into this.", 0), ("This holistic approach brings synergy.", 1)):
                path.write_text(text, encoding="utf-8")
                result = subprocess.run([sys.executable, str(SCRIPT), str(path), "--json"], capture_output=True, text=True)
                self.assertEqual(code, result.returncode)
                data = json.loads(result.stdout)
                self.assertEqual({"path", "files_scanned", "words", "counts", "configured_style_score", "density_per_1k_words", "verdict", "findings"}, set(data))
                self.assertEqual({"rule", "label", "sev", "note", "fix", "file", "line", "match", "snippet"}, set(data["findings"][0]))
            high_only = subprocess.run([sys.executable, str(SCRIPT), str(path), "--severity", "high", "--json"], capture_output=True, text=True)
            self.assertEqual(1, high_only.returncode)
            self.assertTrue(all(f["sev"] == "high" for f in json.loads(high_only.stdout)["findings"]))
            missing = subprocess.run([sys.executable, str(SCRIPT), str(path) + ".missing"], capture_output=True, text=True)
            self.assertEqual(2, missing.returncode)
            missing_path = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
            self.assertEqual(2, missing_path.returncode)

    def test_structured_citations_survive_json_quotes_but_examples_pass(self):
        residues = ('({"attribution":{"attributableIndex":"1009-1"}})', '<grok-card data-id="e8ff4f">', '[cite: 19, 20, 21]', '{"type":"grok_card","citation_id":"abc"}')
        for text in residues:
            with self.subTest(text=text):
                hits = self.rule_hits(text, "citation-markup")
                self.assertEqual(1, len(hits))
                self.assertEqual("high", hits[0]["sev"])
                for example in ('`' + text + '`', '> ' + text, text + ' <!-- unslop-ignore -->'):
                    self.assertEqual([], self.rule_hits(example, "citation-markup"))
        for text in ('"attributableIndex" is a quoted field name.', '"The field is attributableIndex."', '[cite: Alice, Bob]', '<p title="attributableIndex">Source</p>'):
            self.assertEqual([], self.rule_hits(text, "citation-markup"))

    def test_project_traversal_prunes_nested_fixtures_but_scans_direct_files(self):
        with tempfile.TemporaryDirectory(dir=SCRIPT.parent.parent) as tmp:
            root = Path(tmp)
            readme = root / "README.md"
            readme.write_text("A plain guide.", encoding="utf-8")
            dirty = []
            for parent in ("tests", "test"):
                for middle in ("", "unit/helpers"):
                    path = root / parent / middle / "fixtures" / "dirty.md"
                    path.parent.mkdir(parents=True)
                    path.write_text("Delve into this.", encoding="utf-8")
                    dirty.append(path)
            ordinary = root / "fixtures" / "guide.md"
            ordinary.parent.mkdir()
            ordinary.write_text("A plain guide.", encoding="utf-8")
            live = root / "test" / "notes.md"
            live.write_text("Delve into this.", encoding="utf-8")
            self.assertEqual({str(readme), str(ordinary), str(live)}, set(SCANNER.iter_files(tmp)))
            self.assertEqual(1, len(SCANNER.scan(tmp, "low")[0]))
            for path in dirty:
                self.assertEqual(1, len(SCANNER.scan(str(path), "low")[0]))
                self.assertEqual([], list(SCANNER.iter_files(str(path.parent))))
            live.unlink()
            self.assertEqual([], SCANNER.scan(tmp, "low")[0])

    def test_literal_textiles_and_dataflow_pass_but_figurative_weaving_fires(self):
        for text in ("A woven tapestry of Saint George covers the wall.", "A rich collector owns a silk tapestry.", "Together, we restored a silk tapestry.", "The museum displays a woven\ntapestry from France.", "Python supports the object oriented paradigm.", "The dataflow paradigm represents computation as a directed graph."):
            self.assertEqual([], self.rule_hits(text, "era-vocab"))
        for text in ("Together, we have woven a rich tapestry celebrating our community.", "We have woven a tapestry celebrating our community.", "A woven tapestry of ideas.", "A paradigm of excellence."):
            hits = self.rule_hits(text, "era-vocab")
            self.assertEqual(1, len(hits))
            self.assertEqual("medium", hits[0]["sev"])

    def test_promotional_antithesis_variants_gate_and_cause_corrections_pass(self):
        for subject, repeat in (("It's", "it's"), ("It’s", "it’s"), ("It is", "it is")):
            for noun in ("a tool", "another software tool", "a server deployment tool"):
                for ending in (repeat + " a movement", "but a movement"):
                    text = subject + " not just " + noun + ", " + ending + "."
                    hits = self.rule_hits(text, "antithesis")
                    self.assertEqual(1, len(hits), text)
                    self.assertEqual("high", hits[0]["sev"])
        self.assertTrue(self.rule_hits("Not just another software tool, but a movement.", "antithesis"))
        for text in ("The job failed not because the file is missing but because access was denied.", "It is not red, but blue.", "It is not just another tool.", "It is just a tool, but a useful one."):
            self.assertEqual([], self.rule_hits(text, "antithesis"))

    def test_markup_and_soft_wraps_keep_phrase_matching_and_source_lines(self):
        cases = (("\n<p>The result: You move faster.</p>", "staged-reveal", 2),
                 ("The team grew,\nhighlighting the power of collaboration.", "significance-tail", 1),
                 ("Our product serves  as a guide to excellence.", "copula-avoidance", 1),
                 ("<p>The team grew,\nhighlighting the power of collaboration.</p>", "significance-tail", 1),
                 ("<p>The <em>result:</em> You move faster.</p>", "staged-reveal", 1),
                 ("**The result:** You move faster.", "staged-reveal", 1),
                 ("- The catch? There is none.", "staged-reveal", 1),
                 ("The team grew, highlighting **the** power of collaboration.", "significance-tail", 1),
                 ("The team grew, _highlighting_ the power of collaboration.", "significance-tail", 1),
                 ("Plain text.\nThe result: You move faster.", "staged-reveal", 2))
        for text, rule, line in cases:
            hits = self.rule_hits(text, rule)
            self.assertEqual([line], [f["line"] for f in hits], text)
        for text, rule in (("<p>We recorded the result: accepted.</p>", "staged-reveal"),
                           ("The team grew,\n\nhighlighting the power of collaboration.", "significance-tail"),
                           ("Our product serves  as evidence.", "copula-avoidance"),
                           ('<p title="The result:">A plain paragraph.</p>', "staged-reveal")):
            self.assertEqual([], self.rule_hits(text, rule))

    def test_bolded_label_items_allow_blank_lines_and_wrapped_continuations(self):
        item = "- **Owner:** Casey\n  manages the queue.\n\n"
        hits = self.rule_hits(item * 3, "bolded-label-list")
        self.assertEqual([1, 4, 7], [f["line"] for f in hits])
        for separator in ("A new paragraph.\n", "- An unlabelled item.\n", "## A new section\n"):
            self.assertEqual([], self.rule_hits(item * 2 + separator + item, "bolded-label-list"))
        self.assertEqual([], self.rule_hits(item * 2, "bolded-label-list"))

    def test_compare_preserves_signed_numbers_exponents_negation_and_url_suffixes(self):
        pairs = (("The balance is -5.", "The balance is 5.", "numbers only in original: -5"),
                 ("The value is 1e3.", "The value is 1e4.", "numbers only in original: 1e3"),
                 ("You cannot proceed.", "You can proceed.", "negations only in original: cannot"),
                 ("You can't proceed.", "You can proceed.", "negations only in original: can't"),
                 ("https://example.org/Function_(mathematics)", "https://example.org/Function_(physics)", "URLs only in original: https://example.org/Function_(mathematics)"))
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            original, rewrite = Path(tmp) / "a.md", Path(tmp) / "b.md"
            for before, after, expected in pairs:
                original.write_text(before, encoding="utf-8")
                rewrite.write_text(after, encoding="utf-8")
                differences = SCANNER.compare_text(str(original), str(rewrite))
                self.assertTrue(any(expected in d for d in differences), differences)
                self.assertEqual([], SCANNER.compare_text(str(original), str(original)))
            for before, after in (("You can’t proceed.", "You can't proceed."),
                                  ("https://example.org/Function_(mathematics)", "[source](https://example.org/Function_(mathematics))."),
                                  ("https://example.org/Function_(mathematics)", "(https://example.org/Function_(mathematics)).")):
                original.write_text(before, encoding="utf-8")
                rewrite.write_text(after, encoding="utf-8")
                self.assertEqual([], SCANNER.compare_text(str(original), str(rewrite)))

    def test_html_script_style_bodies_are_not_prose_but_visible_text_is(self):
        for hidden in ('<script>const challenge = 1; const steady = 2; const practical = 3;</script>',
                       '<style>.challenge { --steady: practical; }</style>',
                       '<SCRIPT type="text/javascript">\nconst challenge = "steady practical";\n</SCRIPT>',
                       '<script>const residue = "<grok-card>";</script>'):
            self.assertEqual([], self.scan_text(hidden + '<p>A plain guide.</p>')[0])
            findings, words = self.scan_text(hidden + '<p>challenge steady practical</p>')
            self.assertEqual(3, len([f for f in findings if f["rule"] == "current-era-cluster"]))
            self.assertEqual(3, words)

    def test_compare_lists_lost_and_added_tokens_but_exits_zero(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            original = Path(tmp) / "original.md"
            rewrite = Path(tmp) / "rewrite.md"
            original.write_text("It must not cost 12.5 at https://example.org/a", encoding="utf-8")
            rewrite.write_text("It may cost 20 at https://example.org/b", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "--compare", str(original), str(rewrite)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode)
            for difference in ("numbers only in original: 12.5", "numbers only in rewrite: 20", "URLs only in original: https://example.org/a", "URLs only in rewrite: https://example.org/b", "negations only in original: not", "modals only in original: must", "modals only in rewrite: may"):
                self.assertIn(difference, result.stdout)

    def test_compare_unchanged_inventories_do_not_report_differences(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as tmp:
            original = Path(tmp) / "original.md"
            rewrite = Path(tmp) / "rewrite.md"
            original.write_text("No user should pay 12 at https://example.org/a", encoding="utf-8")
            rewrite.write_text("At [the source](https://example.org/a), no user should pay 12", encoding="utf-8")
            # Capitalization of sentence-initial negations must not create a difference.
            self.assertEqual([], SCANNER.compare_text(str(original), str(rewrite)))
            result = subprocess.run([sys.executable, str(SCRIPT), "--compare", str(original), str(original)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode)
            self.assertIn("No token inventory differences found.", result.stdout)
            missing = subprocess.run([sys.executable, str(SCRIPT), "--compare", str(original), str(rewrite) + ".missing"], capture_output=True, text=True)
            self.assertEqual(2, missing.returncode)


if __name__ == "__main__":
    unittest.main()
