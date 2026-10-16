#!/usr/bin/env python3
"""
Scan source code for surface tells and test diffs for weakened checks.

Adapted (MIT) from github.com/JCarterJohnson/vibecoded-design-tells, whose Reddit study catalogs developer complaints. Those classifications do not measure scanner precision. Severity sets review priority; class separates bug, substance, and cosmetic findings. Cosmetic findings are advisory. Only bug-class HIGHs should gate review, but the compatible CLI exit code counts all HIGH findings. Structural problems still need execution and human review; see references/tells.md.

Usage:
    python3 unslop_code_scan.py <path>
    python3 unslop_code_scan.py <path> --severity high
    python3 unslop_code_scan.py <path> --json
    python3 unslop_code_scan.py <path> --max 8
    git diff | python3 unslop_code_scan.py --diff
    python3 unslop_code_scan.py --diff-base REF

A line containing unslop-ignore is skipped. Exit code is the number of HIGH findings (0 = none); invalid input exits 2.
"""
import os, re, sys, json, argparse, ast, textwrap, subprocess

EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rs", ".rb", ".php",
        ".c", ".h", ".cpp", ".cc", ".hpp", ".cs", ".kt", ".kts", ".swift", ".scala",
        ".m", ".mm", ".sh", ".bash", ".lua", ".dart", ".vue", ".svelte", ".sql", ".r"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "vendor", "target",
             "coverage", ".venv", "venv", "__pycache__", ".idea", ".gradle", "bin", "obj",
             "fixtures"}  # test fixtures quote tells on purpose; scan one by path to include it
W = {"high": 3, "medium": 2, "low": 1}
# Comment openers across common languages. The SQL/Lua `--` must be followed by a space,
# or every shell long-flag (`--create`, `--comments`) reads as a comment about creating.
CMT = r"(?://|\#|/\*|\*|--(?=\s)|<!--)"
EMOJI = ("\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
         "\U00002B00-\U00002BFF\U0001F900-\U0001F9FF\U00002764")
DEBRIS = r"(?:IMPLEMENTATION_SUMMARY|.+_SUMMARY|COMPLETED|CHANGES_MADE|FIX_NOTES)\.md"

# Each rule: id, label, severity, class, share (provenance), fix, patterns.
RULES = [
    # ---------- HIGH: paste-in artifacts and unfinished code ----------
    {"id": "chat-artifact", "label": "Leftover chat / assistant / markdown artifact in the code", "sev": "high", "class": "cosmetic",
     "share": "vibecoded-design-tells; assistant-voice matching narrowed locally",
     "fix": "Delete the assistant's voice: code fences, 'Here's the updated code', 'As an AI', 'Good catch!', or assistant instructions after 'Note:'.",
     "pats": [r"^\s*```", r"\b(?:here's|here is) the (updated|complete|full|fixed|revised|new) (code|version|implementation|file)\b",
              r"\bas an? (ai|a\.i\.) (language )?model\b", r"\bas a large language model\b",
              r"\b(good|great) catch!", r"\b(?:you['’]re|you are) absolutely right\b",
              r"\bi(?:['’]ve| have)?\s+(?:updated|added|changed|fixed|refactored|implemented)\b", r"\bas requested\b",
              r"^\s*" + CMT + r"\s*(?:note|remember|important|keep in mind|tip)\b\s*:?\s*(?:you(?:['’]ll| will) need to (?:configure this|add the path|install)\b|to replace the token\b|make sure you run this\b)",
              r"\breplace the token before running\b", r"\b(?:don['’]t|do not) forget to\b",
              r"\b(certainly|sure)! here('?s| is)\b", r"\bi(?:['’]ll| will) (add|update|fix|implement) .{0,40}\bnow\b",
              r"\b(?:i )?hope this helps\b", r"\blet me know\b"]},
    {"id": "placeholder-comment", "label": "Placeholder / ellipsis comment left in (\"// rest of your code\")", "sev": "high", "class": "bug",
     "share": "vibecoded-design-tells; unfinished-code marker",
     "fix": "Write the actual code. These '... rest of the code' stubs mean the file is unfinished, not just untidy.",
     "pats": [r"" + CMT + r"\s*\.{2,}\s*(rest|the rest|your|remaining|existing|previous|other)\b",
              r"" + CMT + r"\s*(rest|remainder) of (your |the |my )?(code|implementation|logic|function|file|owl)\b",
              r"" + CMT + r"\s*(your|the) (code|logic|implementation|stuff) (goes )?here\b",
              r"" + CMT + r"\s*(add|insert|implement|put) (your )?(code|logic|implementation) here\b",
              r"" + CMT + r"\s*(implementation|code|logic) (goes |go )?here\b",
              r"" + CMT + r"\s*existing code (here|unchanged|stays|remains)\b",
              r"" + CMT + r"\s*\.\.\. ?\((?:rest|your|the|existing)[^)]*\)",
              r"" + CMT + r"\s*TODO:?\s*(implement|add|fill in|finish)\b"]},

    # ---------- MEDIUM: the surface tells ----------
    {"id": "emoji-in-code", "label": "Emoji in code, comments, strings, logs, or commit text", "sev": "medium", "class": "cosmetic",
     "share": "house preference; also cataloged by vibecoded-design-tells",
     "fix": "Remove emoji from source. They survive from the model's chat output and read as vibe-coded.",
     "pats": [r"[" + EMOJI + r"]"]},
    {"id": "swallowed-errors", "label": "Catch-all / swallowed errors (bare except, empty catch, empty Go err block)", "sev": "medium", "class": "bug",
     "share": "vibecoded-design-tells; Python handler-body check",
     "fix": "Catch specific exceptions and handle them. Empty or log-only handlers hide failures; propagate or handle the error.",
     "pats": [r"^\s*except(?:\s+(?:(?:builtins\.)?(?:Exception|BaseException)|\(\s*(?:builtins\.)?(?:Exception|BaseException)\s*,?\s*\))(?:\s+as\s+\w+)?)?\s*:",
              r"\bcatch\s*\([^)]*\)\s*\{\s*\}", r"\bcatch\s*\{\s*\}",
              r"\brescue\s*=>\s*\w+\s*$", r"\bcatch\s*\([^)]*\)\s*\{\s*//",
              r"\bif\s+err\s*!=\s*nil\s*\{\s*\}", r"\bif\s+err\s*!=\s*nil\s*\{\s*//"]},
    {"id": "narrating-comment", "label": "Narrating comment that restates the obvious / step-by-step '# Step 1'", "sev": "medium", "class": "cosmetic",
     "share": "vibecoded-design-tells; adjacent-line restatement or explicit steps",
     "fix": "Cut comments that say what the next line plainly does. Comment why, not what.",
     "pats": [r"^\s*(?://|\#|--(?=\s))\s*(?P<comment>\S.*?)\s*$"]},
    {"id": "generic-naming", "label": "Generic placeholder function name (process_data, handleData, doStuff)", "sev": "medium", "class": "cosmetic",
     "share": "vibecoded-design-tells; placeholder-name subset",
     "fix": "Name it for what it actually does in this domain. process_data() that does 11 things is the AI tell.",
     "pats": [r"\b(def|function|func|fn|fun|sub)\s+(process_?[Dd]ata|handle_?[Dd]ata|do_?[Ss]tuff|do_?[Ss]omething|my_?[Ff]unction|process_?[Ii]tem|process_?[Ii]nput|main_?[Ff]unction)\b",
              r"\b(process_?[Dd]ata|handle_?[Dd]ata|do_?[Ss]tuff|do_?[Ss]omething)\s*\("]},

    # ---------- LOW: weak / inflated signals ----------
    {"id": "verbose-naming", "label": "Over-verbose, robotically self-documenting identifier", "sev": "low", "class": "cosmetic",
     "share": "vibecoded-design-tells; weak, contextual signal", "cs": True,
     "fix": "A name that is a whole sentence (getUserDataFromApiResponseHandler) reads as machine-generated. Trim it.",
     "pats": [r"^\s*(?:(?:public|protected|private|static|abstract|final|export|default|async|override|open|suspend)\s+)*(?:def|function|func|fn|fun|sub|class)\s+&?(?P<name>[A-Za-z_]\w*)\b",
              r"^\s*func\s+\([^)]*\)\s+(?P<name>[A-Za-z_]\w*)\b",
              r"^\s*(?:(?:export|public|protected|private|static|readonly)\s+)*(?:(?:const|let|var)\s+)?(?P<name>\$?[A-Za-z_]\w*)\s*(?::[^=;]+)?=(?!=|>)",
              r"^\s*(?:(?:public|protected|private|static|async)\s+)*(?P<name>[A-Za-z_]\w*)\s*\([^;{}]*\)\s*(?::[\w<>\[\]|? ]+)?\s*\{",
              r"^\s*(?:(?:public|protected|private|static|final|readonly)\s+)*(?!(?:return|throw|new|yield|await|raise)\b)[A-Za-z_]\w*(?:<[^>]+>|\[\]|\?)?\s+(?P<name>\$?[A-Za-z_]\w*)\s*(?:\(|=|;)"],
     # A test name is a sentence on purpose: test_returns_none_on_malformed_yaml is the
     # convention, not a tell. Left unsuppressed this rule was 30 of 37 findings on a
     # clean repo, and its own share note already calls the signal inflated.
     "suppress": r"\bdef\s+test|\btest_|\b(it|describe|context|specify)\s*\(|\bfunc\s+Test|@Test\b"},
    {"id": "boilerplate-marker", "label": "Boilerplate / dummy-data marker (placeholder keys, sample data)", "sev": "low", "class": "cosmetic",
     "share": "vibecoded-design-tells; weak proxy for tutorial-shaped code",
     "fix": "Replace generated dummy data and placeholders with the real thing. Tutorial-shaped sample data is the loudest tell, but only a human can judge the shape.",
     "pats": [r"\blorem ipsum\b", r"\b(your|my)[-_]?api[-_]?key\b", r"\bYOUR_API_KEY\b", r"\bexample\.com\b",
              r"\b(John|Jane) (Doe|Smith)\b", r"['\"]sk-(xxx|your|placeholder|123)",
              r"(console\.log|print|println|fmt\.Print\w*|System\.out\.print\w*)\s*\(\s*['\"]Here we go"]},
    {"id": "checker-suppression", "label": "Checker suppression without a reason", "sev": "medium", "class": "bug",
     "share": "cursor deslop; advisory bypass check",
     "fix": "fix the underlying error or add a reason",
     "pats": [r"#\s*type:\s*ignore\b(?:\s*\[[^\]]*\])?", r"#\s*noqa\b(?::\s*[A-Z]\d+(?:\s*,\s*[A-Z]\d+)*)?",
              r"@ts-(?:ignore|expect-error)\b", r"eslint-disable(?:-next-line|-line)?\b(?:\s+[\w@/.-]+(?:\s*,\s*[\w@/.-]+)*)?",
              r"\bas\s+unknown\s+as\b", r"\bas\s+any\b", r":\s*any\b"]},
    {"id": "change-narration", "label": "Comment narrates an edit instead of explaining the code", "sev": "medium", "class": "cosmetic",
     "share": "code-humanizer; change-narration comments",
     "fix": "Remove the edit history or explain the continuing reason for the code.",
     "pats": [r"(?:#|//|/\*|\*)\s*(?:(?:Updated|Changed|Modified|Fixed|Refactored)\s+(?:to|from|so|the)\b|Now\s+uses\b|Previously\s+(?:this|was)\b|(?:This\s+)?was\s+changed\s+to\b|Old:|New:)"]},
    {"id": "repo-debris", "label": "Possible leftover implementation summary", "sev": "medium", "class": "cosmetic",
     "share": "house preference; review whether the file has a continuing purpose",
     "fix": "Remove transient implementation notes or keep them only for a continuing documentation purpose.",
     "filename": True, "pats": [r"^" + DEBRIS + r"$"]},
    {"id": "test-assertion-removed", "label": "Assertion removed from a test", "sev": "high", "class": "bug",
     "share": "EvilGenie arXiv:2511.21654; METR reward hacking (2025)",
     "fix": "Restore the check or verify that a changed requirement justifies its removal.",
     "diff": "-", "pats": [r"(?<![\w.$])assert(?=\s|\()|\b(?:\w+\.)?assert\w*\s*\(|\bexpect\s*\("]},
    {"id": "test-skip-added", "label": "Skip or expected-failure marker added to a test", "sev": "high", "class": "bug",
     "share": "EvilGenie arXiv:2511.21654; METR reward hacking (2025)",
     "fix": "Run the test and fix the failure, or document why the requirement permits skipping it.",
     "diff": "+", "pats": [r"@pytest\s*\.\s*mark\s*\.\s*(?:skip|skipif|xfail)\b|\bpytest\s*\.\s*mark\s*\.\s*(?:skip|skipif|xfail)\s*\(|\bpytest\s*\.\s*(?:skip|xfail)\s*\(|@(?:unittest\s*\.\s*)?(?:skip|skipIf|skipUnless|expectedFailure)\b|\.\s*skip\s*\(|\b(?:it|test|describe)\s*\.\s*skip\b|\b(?:xit|xdescribe)\s*\(|@Disabled\b|\bt\s*\.\s*Skip(?:f|Now)?\s*\(|(?:->|::)\s*markTest(?:Skipped|Incomplete)\s*\("]},
    {"id": "test-tautology-added", "label": "Always-true assertion added to a test", "sev": "high", "class": "bug",
     "share": "EvilGenie arXiv:2511.21654; METR reward hacking (2025)", "cs": True,
     "fix": "Assert an observable result from the implementation instead of a constant truth.",
     "diff": "+", "pats": [r"\bassert\s*(?:\(\s*)*True(?:\s*\))*\s*(?:$|[,;])", r"\bexpect\s*\(\s*(?:\(\s*)*true(?:\s*\))*\s*\)\s*\.\s*toBe\s*\(\s*(?:\(\s*)*true(?:\s*\))*\s*\)"]},
]

def compile_rules(min_sev):
    order = ["high", "medium", "low"]
    floor = order.index(min_sev) if min_sev else len(order) - 1
    out = []
    for r in RULES:
        if order.index(r["sev"]) > floor:
            continue
        r = dict(r)
        flags = 0 if r.get("cs") else re.IGNORECASE
        r["rx"] = [re.compile(p, flags) for p in r["pats"]]
        # Per-rule opt-out, same mechanism the ui scanner uses.
        r["suppress_rx"] = re.compile(r["suppress"], re.IGNORECASE) if r.get("suppress") else None
        out.append(r)
    return out

def iter_files(path):
    if os.path.isfile(path):
        yield path; return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".min.js") or f.endswith(".min.css") or f.endswith(".map"):
                continue
            if os.path.splitext(f)[1].lower() in EXTS or re.fullmatch(DEBRIS, f, re.IGNORECASE):
                yield os.path.join(root, f)

def finding(rule, fp, number, line, match):
    return {"rule": rule["id"], "label": rule["label"], "sev": rule["sev"],
            "class": rule["class"], "share": rule["share"], "fix": rule["fix"],
            "file": fp, "line": number, "match": match.strip()[:50], "snippet": line.strip()[:160]}

def python_swallow(lines, index):
    header = re.match(r"^([ \t]*)except[^:]*:(.*)", lines[index])
    body = [header[2].lstrip() + "\n"]
    if not header[2].split("#", 1)[0].strip():
        indent = len(header[1].expandtabs())
        body = []
        for line in lines[index + 1:]:
            if line.strip() and not line.lstrip().startswith("#"):
                if len(line.expandtabs()) - len(line.expandtabs().lstrip()) <= indent:
                    break
            body.append(line)
    try:
        statements = ast.parse(textwrap.dedent("".join(body))).body
    except SyntaxError:
        return False
    for node in statements:
        if isinstance(node, ast.Pass):
            continue
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant) and node.value.value is Ellipsis:
                continue
            if isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Name) and func.id == "print":
                    continue
                if isinstance(func, ast.Name) and func.id == "error_log":
                    continue
                if isinstance(func, ast.Attribute) and func.attr in {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}:
                    if ast.unparse(func.value) in {"logger", "logging", "log", "console", "self.logger", "this.logger", "Log"}:
                        continue
        return False
    return True

def suppression_reason(comments, match):
    tail = comments[match.end():].split("*/", 1)[0]
    return bool(re.search(r"[a-zA-Z]", tail))


def source_views(lines, fp):
    """Keep offsets while separating code, comments, and quoted data."""
    quote = block = ""
    hash_comment = os.path.splitext(fp)[1].lower() not in {".js", ".jsx", ".ts", ".tsx", ".css", ".java", ".go", ".c", ".cpp", ".cs"}
    for line in lines:
        code, comments = list(line), [" "] * len(line)
        i = 0
        while i < len(line):
            start = i
            if block:
                end = line.find(block, i)
                i = len(line) if end < 0 else end + len(block)
                if end >= 0:
                    block = ""
                comments[start:i] = line[start:i]
                code[start:i] = " " * (i - start)
            elif quote:
                if line.startswith(quote, i):
                    i += len(quote)
                    quote = ""
                elif line[i] == "\\":
                    i = min(i + 2, len(line))
                else:
                    i += 1
                code[start:i] = "~" * (i - start)
            elif line.startswith(("//", "-- "), i) or (hash_comment and line[i] == "#"):
                comments[i:] = line[i:]
                code[i:] = " " * (len(line) - i)
                break
            elif line.startswith(("/*", "<!--"), i):
                block = "*/" if line.startswith("/*", i) else "-->"
            elif line[i] in "\"'`":
                quote = line[i] * (3 if line.startswith(line[i] * 3, i) else 1)
                i += len(quote)
                code[start:i] = "~" * (i - start)
            else:
                i += 1
        # Visible markup text is data too, including prose in PHP templates and JSX.
        for text in re.finditer(r"<(?!/?(?:script|style)\b)/?[a-z][^>]*>([^<]*)", line, re.IGNORECASE):
            before = line[:text.start()].rstrip()
            if re.search(r"[\w)\]]$", before) and not re.search(r"\breturn$", before):
                continue  # a generic argument list, not an opening markup tag
            code[text.start(1):text.end(1)] = "~" * len(text[1])
        yield "".join(code), "".join(comments)

def identifier_words(name):
    name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", name)
    return re.findall(r"[a-z]+|\d+", name.lower())

def sentence_identifier(name):
    if name.lstrip("$").isupper():
        return False
    # These conventional compounds each name one concept despite internal capitals.
    name = name.replace("WebSite", "Website").replace("JsonLd", "Jsonld")
    words = [word for word in identifier_words(name) if word.isalpha()]
    return len(words) >= 6

def narrates_next_line(comment, lines, index):
    if re.match(r"(?:step\s*\d+\b|now we\b|(?:first|next|finally),?\s+we\b)", comment, re.IGNORECASE):
        return True
    if index + 1 >= len(lines):
        return False
    code = lines[index + 1].strip()
    if not code or code.startswith(("#", "//", "/*", "*")) or re.match(r"--\s", code):
        return False
    words = [word for word in identifier_words(comment) if word not in {"a", "an", "the"}]
    # Operators have no word tokens, so match increment/decrement explicitly.
    for verb, operator in (("increment", "+"), ("decrement", "-")):
        op = re.escape(operator)
        update = re.fullmatch(rf"(?:(\$?[A-Za-z_]\w*)\s*(?:{op}{op}|{op}=\s*1)|{op}{op}\s*(\$?[A-Za-z_]\w*))\s*;?", code)
        if update and words == [verb] + identifier_words(update[1] or update[2]):
            return True
    return len(words) >= 2 and words == identifier_words(code)

def documented_example(line, match):
    if re.match(r"\s*(?://|#|/\*|\*|--\s|<!--)", line):
        return True
    for attr in re.finditer(r"(?<![\w:-])placeholder\s*=\s*(['\"])(.*?)\1", line, re.IGNORECASE):
        if attr.start(2) <= match.start() and match.end() <= attr.end(2):
            return True
    for text in re.finditer(r"<(?!/?(?:script|style)\b)/?[a-z][^>]*>([^<]*)", line, re.IGNORECASE):
        if text.start(1) <= match.start() and match.end() <= text.end(1):
            return True
    return False

def scan(path, min_sev):
    rules = compile_rules(min_sev)
    findings = []
    for fp in iter_files(path):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue  # unreadable file: skip, not fatal
        for r in rules:
            if r.get("filename") and r["rx"][0].fullmatch(os.path.basename(fp)):
                if not lines or "unslop-ignore" not in lines[0].lower():
                    findings.append(finding(r, fp, 1, os.path.basename(fp), os.path.basename(fp)))
        if fp.lower().endswith(".md"):
            continue  # debris check is filename-only
        if len(lines) == 1 and len(lines[0]) > 5000:   # likely minified
            continue
        in_docblock = False
        views = list(source_views(lines, fp))
        for i, line in enumerate(lines, 1):
            code, comments = views[i - 1]
            docblock_line = in_docblock or bool(re.match(r"\s*/\*\*", line))
            if docblock_line:
                in_docblock = "*/" not in line
            if "unslop-ignore" in line.lower():
                continue
            for r in rules:
                if r.get("diff") or r.get("filename"):
                    continue
                if r["suppress_rx"] and r["suppress_rx"].search(line):
                    continue
                for rx in r["rx"]:
                    target = line
                    if r["id"] == "verbose-naming":
                        target = code
                    elif r["id"] == "change-narration":
                        target = comments
                    elif r["id"] == "checker-suppression":
                        target = code if rx.pattern.startswith((r"\bas", r":\s*any")) else comments
                    m = rx.search(target)
                    if m:
                        if r["id"] == "verbose-naming" and (docblock_line or not sentence_identifier(m["name"])):
                            continue
                        if r["id"] == "narrating-comment" and (docblock_line or not narrates_next_line(m["comment"], lines, i - 1)):
                            break
                        if r["id"] == "boilerplate-marker" and m.group(0).lower() == "example.com":
                            m = next((example for example in rx.finditer(line)
                                      if not (docblock_line or documented_example(line, example))), None)
                            if m is None:
                                continue
                        if r["id"] == "swallowed-errors" and line.lstrip().startswith("except"):
                            if not fp.lower().endswith(".py") or not python_swallow(lines, i - 1):
                                break
                        if r["id"] == "checker-suppression" and suppression_reason(comments, m):
                            continue
                        match = m["name"] if r["id"] == "verbose-naming" else m.group(0)
                        findings.append(finding(r, fp, i, line, match))
                        break
    return findings

def is_test_file(path):
    return bool(re.search(r"(?:^|/)(?:tests|__tests__)/|(?:^|/)test_[^/]+$|(?:^|/)[^/]*_test\.[^/]+$|\.(?:test|spec)\.[^/]+$", path))

def iter_diff_lines(diff, context_sides=False):
    old_path = new_path = ""
    old_line = new_line = old_left = new_left = 0
    for raw in diff.splitlines():
        if raw.startswith("diff --git "):
            old_path = new_path = ""
            old_left = new_left = 0
        elif not (old_left or new_left) and raw.startswith(("--- ", "+++ ")):
            path = raw[4:].split("\t", 1)[0]
            if path.startswith('"'):
                path = ast.literal_eval(path)
            path = re.sub(r"^[ab]/", "", path)
            if raw.startswith("--- "):
                old_path = path
            else:
                new_path = path
        elif raw.startswith("@@ "):
            hunk = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", raw)
            if hunk:
                old_line, new_line = int(hunk[1]), int(hunk[3])
                old_left, new_left = int(hunk[2] or 1), int(hunk[4] or 1)
        elif (old_left or new_left) and raw[:1] in {"-", "+", " "}:
            kind = raw[0]
            path, number = (old_path, old_line) if kind == "-" else (new_path, new_line)
            if kind == " " and context_sides:
                yield old_path, old_line, "old-context", raw[1:]
                yield new_path, new_line, "new-context", raw[1:]
            else:
                yield path, number, kind, raw[1:]
            if kind != "+":
                old_line += 1; old_left -= 1
            if kind != "-":
                new_line += 1; new_left -= 1

def scan_diff(diff, min_sev):
    rules = [r for r in compile_rules(min_sev) if r.get("diff")]
    findings = []
    # Reconstruct each hunk side so strings and block comments retain lexical state.
    groups, latest = [], {}
    for fp, number, kind, line in iter_diff_lines(diff, context_sides=True):
        side = "-" if kind in {"-", "old-context"} else "+"
        key = fp, side
        rows = latest.get(key)
        if rows is None or rows[-1][0] + 1 != number:
            rows = []
            latest[key] = rows
            groups.append((fp, side, rows))
        rows.append((number, kind, line))
    for fp, side, rows in groups:
        if not is_test_file(fp):
            continue
        views = list(source_views([line for _, _, line in rows], fp))
        for index, (number, kind, line) in enumerate(rows):
            if kind != side or "unslop-ignore" in line.lower():
                continue
            code = views[index][0].strip()
            if not code:
                continue
            for r in rules:
                if r["diff"] != kind:
                    continue
                candidate = code
                if r["id"] == "test-tautology-added" and index + 1 < len(rows) and "unslop-ignore" not in rows[index + 1][2].lower():
                    following = views[index + 1][0].strip()
                    if rows[index + 1][1] == "+" and following.startswith("."):
                        candidate += " " + following
                for rx in r["rx"]:
                    m = rx.search(candidate)
                    if m:
                        findings.append(finding(r, fp, number, line, m.group(0)))
                        break
    return findings

def verdict(by_sev, weighted):
    # Severity mix decides, not the weighted total. The total let a pile of low findings
    # read as STRONG with zero high ones, which is how the scanner lost its credibility.
    high, med = by_sev.get("high", 0), by_sev.get("medium", 0)
    if high >= 3 or (high >= 1 and med >= 5):
        return "STRONG AI-written-code tells"
    if high >= 1 or med >= 3:
        return "Some AI tells present"
    if weighted > 0:
        return "Mostly clean, minor tells"
    return "Clean, no surface tells detected"

def main():
    ap = argparse.ArgumentParser(description="Scan source code for AI-written-code tells.")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--diff", action="store_true", help="check test integrity in a git diff read from stdin")
    ap.add_argument("--diff-base", metavar="REF", help="check test integrity in git diff REF (path selects the repo)")
    ap.add_argument("--severity", choices=["high", "medium", "low"], default="low",
                    help="minimum severity to report (default: low = everything)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max", type=int, default=10, help="max examples shown per rule (text mode)")
    args = ap.parse_args()

    if not args.path and not (args.diff or args.diff_base):
        ap.error("path is required unless --diff or --diff-base is used")
    if args.path and not os.path.exists(args.path):
        print(f"path not found: {args.path}", file=sys.stderr); sys.exit(2)

    if args.diff or args.diff_base:
        if args.diff_base:
            cwd = args.path or "."
            if os.path.isfile(cwd):
                cwd = os.path.dirname(os.path.abspath(cwd))
            try:
                diff = subprocess.run(["git", "diff", "--no-ext-diff", "--no-color", args.diff_base, "--"], cwd=cwd,
                                      check=True, capture_output=True, text=True).stdout
            except (OSError, subprocess.CalledProcessError) as exc:
                print(f"git diff failed: {exc}", file=sys.stderr); sys.exit(2)
        else:
            diff = sys.stdin.read()
        findings = scan_diff(diff, args.severity)
        files_scanned = len({fp for fp, _, _, _ in iter_diff_lines(diff) if is_test_file(fp)})
        args.path = args.path or "."
    else:
        findings = scan(args.path, args.severity)
        files_scanned = sum(1 for _ in iter_files(args.path))
    by_sev, by_class, by_rule = {}, {}, {}
    for f in findings:
        by_sev[f["sev"]] = by_sev.get(f["sev"], 0) + 1
        by_class[f["class"]] = by_class.get(f["class"], 0) + 1
        by_rule.setdefault(f["rule"], []).append(f)
    weighted = sum(W[s] * n for s, n in by_sev.items())

    if args.json:
        print(json.dumps({"path": args.path, "files_scanned": files_scanned, "counts": by_sev,
                          "class_counts": by_class, "slop_score": weighted,
                          "verdict": verdict(by_sev, weighted), "findings": findings}, indent=2))
        sys.exit(by_sev.get("high", 0))

    sev_order = {"high": 0, "medium": 1, "low": 2}
    rule_ids = sorted(by_rule, key=lambda rid: (sev_order[by_rule[rid][0]["sev"]], -len(by_rule[rid])))
    print(f"\n  unslop-code scan: {args.path}")
    print(f"  files scanned: {files_scanned}   findings: {len(findings)}   slop score: {weighted}")
    print(f"  verdict: {verdict(by_sev, weighted)}")
    print(f"  high: {by_sev.get('high',0)}   medium: {by_sev.get('medium',0)}   low: {by_sev.get('low',0)}")
    print(f"  bug-class: {by_class.get('bug',0)} (review behavior)   "
          f"substance: {by_class.get('substance',0)} (review contract)   "
          f"cosmetic: {by_class.get('cosmetic',0)} (advisory)\n")
    if not findings:
        print("  No surface tells flagged. The loudest tells are structural and a regex cannot see\n"
              "  them: boilerplate / tutorial-shaped code, hallucinated APIs, over-engineering, and\n"
              "  code that ignores the surrounding repo. Hallucinated APIs are a bug, not a style\n"
              "  issue: build it, type-check it, run it, resolve every import. Then read the diff for\n"
              "  the rest by hand against references/tells.md.\n")
        return
    for rid in rule_ids:
        items = by_rule[rid]
        f0 = items[0]
        print(f"  [{f0['sev'].upper()} · {f0['class']}] {f0['label']}  ({len(items)} hit{'s' if len(items)!=1 else ''})  [{f0['share']}]")
        print(f"        fix: {f0['fix']}")
        for it in items[:args.max]:
            print(f"        {it['file']}:{it['line']}  ({it['match']})  {it['snippet']}")
        if len(items) > args.max:
            print(f"        ... +{len(items) - args.max} more")
        print()
    top = [by_rule[rid][0]['label'] for rid in rule_ids[:3]]
    print("  Top things to change: " + "; ".join(top))
    print("  Review bug-class findings first; verify the behavior before changing it.")
    print("  The big tells (boilerplate, hallucinated APIs, over-engineering) the regex cannot see:")
    print("  build / type-check / run for the hallucinated calls, read the diff for the rest. See references/tells.md.\n")
    sys.exit(by_sev.get("high", 0))

if __name__ == "__main__":
    main()
