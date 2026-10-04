# Pattern Detection Script Library

Use this during the pattern-inventory phase and when generating preflight scripts. Pick the scripts relevant to the project's stack.

All scripts are designed to be safe (|| true suffix, head limits on output) and produce file:line locations.

## Patterns That Can Be Proven To Fire

A pattern that cannot match reads as a clean result forever, and a clean result is the one nobody checks. Four checks in one project's `.claude/scripts/review-metrics.sh` were dead from the day they were written and surfaced only when someone read the source, never by running it. Before any pattern from this library goes into a script, run it against one input that MUST match and one near miss that MUST NOT. The harness for that is `a-review-optimizer/references/preflight-template.md` > Canary Self-Test.

The traps that produced those dead checks, all re-verified on Mint 22.3, 2026-08-29:

**Verify the flag means what you think.** `rg -L` is `--follow` (descend into symlinks), not invert-match. That script's `strict_types` check used it expecting "files with no match" and reported 316 files missing `declare(strict_types=1)` on a tree where the true count was 0, because it was in fact listing the files that had it. The flags you want are `-v` / `--invert-match` for non-matching lines, `--files-without-match` for non-matching files, `-l` / `--files-with-matches` for the opposite. Read `rg --help` for any single-letter flag before using it: the short forms are not grep's.

**Verify the tool's regex dialect supports your syntax.** The system `awk` on Mint is mawk 1.3.4, which has no `\s`, `\d` or `\w`. Two checks in that same script used `\s` in awk patterns and matched nothing from the day they were added.

```bash
printf 'foo bar\n' | awk '/foo\sbar/ {print "MATCHED"}'            # prints nothing under mawk
printf 'foo bar\n' | awk '/foo[[:space:]]bar/ {print "MATCHED"}'   # MATCHED
```

POSIX classes work under mawk and gawk both, so write `[[:space:]]`, `[[:digit:]]`, `[[:alnum:]_]` in every awk pattern. The dialects elsewhere in this file are not interchangeable either: `rg` is Rust regex (no backreferences, no lookaround), `grep -E` is POSIX ERE (no `\d`), Python `re` takes both. A pattern moved from one to another gets re-tested, not translated by eye.

**Verify the literal you match can occur in the target language.** A Dart project grepped `EdgeInsets\.\(` for hardcoded spacing. That matches the text `EdgeInsets.(`, which is not valid Dart and cannot appear anywhere. It reported 0 against roughly 193 real sites. Build a literal pattern by pasting a real occurrence out of the codebase and matching against that, never by writing the syntax from memory.

**Verify that two extractions off one line actually differ.** A cross-feature-import check ran two greedy `sed` calls over the same `rg` line and compared the results. Both landed on the same trailing `@/features/<name>`, so the halves always compared equal and the check emitted nothing on a tree holding five real violations. Any check that compares two derived values needs a fixture where those values are known to differ, or the comparison itself is untested.

## Universal Detection Scripts

### Credentials & Secrets
```bash
# Hardcoded secret assignments (exclude env/config accessors)
rg -n '(password|api_key|secret_key|api_secret|token|private_key)\s*=\s*["\x27][^"\x27]{4,}' \
  --type-add 'code:*.{py,php,js,ts,rb,go,java}' -t code src/ \
  | grep -v 'getenv\|os.environ\|get_setting\|\.get(' || true

# Files that shouldn't be tracked
git ls-files -- '*.env' '.env.*' '*.key' '*.pem' 2>/dev/null \
  | grep -v '.example' | grep -v '.sample' || true
```

### Error Handling
```bash
# Bare except (Python)
rg -n '^\s*except\s*:' --type py src/ || true

# catch(Exception) or catch(\Exception) (PHP)
rg -n 'catch\s*\(\s*\\?Exception' --type php src/ || true

# Generic catch(e) (JS/TS)
rg -n 'catch\s*\(\s*\w+\s*\)\s*\{' --type js --type ts src/ || true

# Silent exception handlers (Python: except block with only pass/continue)
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    lines = f.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(r'\s*except\b', line):
            # Check next non-blank lines in the except block
            body_lines = []
            base_indent = len(line) - len(line.lstrip())
            for j in range(i+1, min(i+5, len(lines))):
                stripped = lines[j].strip()
                indent = len(lines[j]) - len(lines[j].lstrip())
                if indent <= base_indent and stripped: break
                if stripped: body_lines.append(stripped)
            if body_lines and all(b in ('pass', 'continue', '...') for b in body_lines):
                print(f'{f}:{i+1}: silent except, body is only {body_lines[0]}')
" 2>/dev/null || true

# Empty catch blocks (PHP: brace-balanced scan, catches multi-line)
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.php'):
    text = f.read_text(errors='ignore')
    for m in re.finditer(r'catch\s*\([^)]*\)\s*\{', text):
        depth, pos = 1, m.end()
        while pos < len(text) and depth > 0:
            if text[pos] == '{': depth += 1
            elif text[pos] == '}': depth -= 1
            pos += 1
        body = text[m.end():pos-1].strip()
        line = text[:m.start()].count('\n') + 1
        if not body or re.fullmatch(r'(//[^\n]*|\s)*', body):
            print(f'{f}:{line}: empty catch block, error discarded')
" 2>/dev/null || true

# Empty catch blocks (JS/TS: brace-balanced scan) + log-only promise .catch
python3 -c "
import re, pathlib
for ext in ('*.js', '*.ts', '*.jsx', '*.tsx'):
    for f in pathlib.Path('src').rglob(ext):
        text = f.read_text(errors='ignore')
        for m in re.finditer(r'catch\s*(\([^)]*\))?\s*\{', text):
            depth, pos = 1, m.end()
            while pos < len(text) and depth > 0:
                if text[pos] == '{': depth += 1
                elif text[pos] == '}': depth -= 1
                pos += 1
            body = text[m.end():pos-1].strip()
            line = text[:m.start()].count('\n') + 1
            if not body or re.fullmatch(r'(//[^\n]*|\s)*', body):
                print(f'{f}:{line}: empty catch block, error discarded')
" 2>/dev/null || true
rg -n '\.catch\s*\(\s*(\(\s*\)|\(?\w*\)?)\s*=>\s*\{?\s*\}?\s*\)|\.catch\s*\(\s*console\.(log|error)\s*\)' --type js --type ts src/ || true

# Error suppression operators (PHP)
rg -n '@\s*(file_get_contents|file_put_contents|unlink|fopen|mkdir|rmdir|copy|rename|include|require|mysqli_|json_decode|simplexml_|\$)' --type php src/ || true
rg -n 'error_reporting\s*\(\s*0\s*\)' --type php src/ || true

# Fail-open except (Python): error branch returns a success-looking default with no raise/log
python3 -c "
import re, pathlib
DEFAULTS = re.compile(r'return\s+(None|True|False|\[\]|\{\}|0|[\"\x27][\"\x27])\s*(#.*)?$')
for f in pathlib.Path('src').rglob('*.py'):
    lines = f.read_text(errors='ignore').splitlines()
    for i, line in enumerate(lines):
        if not re.match(r'\s*except\b', line): continue
        base = len(line) - len(line.lstrip())
        body = []
        for j in range(i+1, min(i+8, len(lines))):
            s = lines[j].strip()
            ind = len(lines[j]) - len(lines[j].lstrip())
            if s and ind <= base: break
            if s: body.append(s)
        if not body: continue
        has_default_return = any(DEFAULTS.match(b) for b in body)
        has_signal = any(re.search(r'raise|log|warn|print', b) for b in body)
        if has_default_return and not has_signal:
            print(f'{f}:{i+1}: fail-open except, returns default without raising or logging')
" 2>/dev/null || true
```

### Code Metrics
```bash
# Files over 300 lines
find src/ app/ lib/ -name '*.py' -o -name '*.php' -o -name '*.ts' -o -name '*.js' 2>/dev/null \
  | xargs wc -l 2>/dev/null | awk '$1 > 300 && !/total$/' | sort -rn || true

# Deep nesting (5+ levels = 20+ leading spaces)
rg -n '^\s{20,}\S' --type-add 'code:*.{py,php,js,ts}' -t code src/ | head -20 || true

# Long functions (Python: def to next def at same/lower indent, >50 lines)
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    lines = f.read_text().splitlines()
    func_start = None
    func_name = ''
    func_indent = 0
    for i, line in enumerate(lines):
        m = re.match(r'^(\s*)def\s+(\w+)', line)
        if m:
            if func_start and (i - func_start) > 50:
                print(f'{f}:{func_start+1}: {func_name}() is {i - func_start} lines')
            func_start = i
            func_name = m.group(2)
            func_indent = len(m.group(1))
    if func_start and (len(lines) - func_start) > 50:
        print(f'{f}:{func_start+1}: {func_name}() is {len(lines) - func_start} lines')
" 2>/dev/null || true

# print/var_dump/console.log in production code
rg -n '\bprint\(' --type py src/ --glob '!*test*' --glob '!*__pycache__*' 2>/dev/null | head -20 || true
rg -n '\bvar_dump\(|\bdd\(' --type php src/ 2>/dev/null | head -20 || true
rg -n '\bconsole\.(log|debug)\(' --type js --type ts src/ --glob '!*test*' 2>/dev/null | head -20 || true

# Commented-out code (3+ consecutive comment lines with code patterns)
python3 -c "
import re, pathlib
code_pattern = re.compile(r'#\s*(def |class |import |return |if |for |while |print|self\.|=\s)')
for f in pathlib.Path('src').rglob('*.py'):
    lines = f.read_text().splitlines()
    streak = 0
    streak_start = 0
    for i, line in enumerate(lines):
        if code_pattern.match(line.strip()):
            if streak == 0: streak_start = i
            streak += 1
        else:
            if streak >= 3:
                print(f'{f}:{streak_start+1}: {streak} lines of commented-out code')
            streak = 0
    if streak >= 3:
        print(f'{f}:{streak_start+1}: {streak} lines of commented-out code')
" 2>/dev/null || true
```

## Shell Script Detection

Silent failure in bash is the fleet's most common script defect: the happy path works, the unhappy path exits 0. Distinguish state-changing commands (rm, mv, cp, rsync, docker, systemctl) from read-only probes; `|| true` on a probe is deliberate, on a mutation it masks real failures.

```bash
# Missing safety flags in scripts that change state (>20 lines as a proxy)
for f in $(find . -name '*.sh' -not -path '*/node_modules/*' -not -path '*/vendor/*' -not -path '*/.git/*' 2>/dev/null); do
  [ "$(wc -l < "$f")" -lt 20 ] && continue
  head -10 "$f" | grep -q 'set -e' || echo "$f:1: no set -e"
  grep -q 'pipefail' "$f" || echo "$f:1: no pipefail, failures inside pipelines are invisible"
done

# || true or || : on state-changing commands
rg -n '\b(rm|mv|cp|mkdir|rsync|scp|docker|systemctl|crontab|chown|chmod)\b[^|#]*\|\|\s*(true|:)' --glob '*.sh' . || true

# Blanket stderr suppression on state-changing commands
rg -n '\b(rm|mv|cp|rsync|scp|docker|systemctl)\b[^#]*2>\s*/dev/null' --glob '*.sh' . || true

# cd without failure guard (subsequent commands run in the wrong directory)
rg -n '^\s*cd\s+[^&|;]+$' --glob '*.sh' . || true

# mktemp without an EXIT trap in the same file
for f in $(rg -l 'mktemp' --glob '*.sh' . 2>/dev/null); do
  grep -q 'trap.*EXIT' "$f" || echo "$f: mktemp without EXIT trap cleanup"
done

# Opportunistic: real linter when installed (catches quoting, word splitting, and much more)
command -v shellcheck >/dev/null 2>&1 && shellcheck -f gcc -S warning $(find . -name '*.sh' -not -path '*/.git/*') 2>/dev/null | head -30 || true
```

## Hostile Content Detection (reviewer integrity)

MANDATORY in every generated preflight, regardless of stack. These checks defend the AI reviewer itself: a prompt-injection payload in a comment can hijack the agent reading the file, so detection MUST be deterministic. A regex cannot be sweet-talked; the agent can. Never move these checks into an agent prompt.

```bash
# INJ-01: Invisible / bidirectional Unicode (Trojan Source, CVE-2021-42574)
python3 -c "
import pathlib
BAD = {0x200B, 0x200C, 0x200D, 0x200E, 0x200F, 0x2060, 0xFEFF} | set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))
EXTS = {'.py', '.php', '.js', '.ts', '.jsx', '.tsx', '.sh', '.md', '.yml', '.yaml', '.json', '.html', '.css', '.sql', '.env', '.txt'}
SKIP = {'.git', 'node_modules', 'vendor', '__pycache__', 'dist', 'build'}
for f in pathlib.Path('.').rglob('*'):
    if f.is_dir() or set(f.parts) & SKIP or f.suffix not in EXTS: continue
    try: text = f.read_text(encoding='utf-8')
    except Exception: continue
    for i, line in enumerate(text.splitlines(), 1):
        hits = sorted({hex(ord(c)) for c in line if ord(c) in BAD})
        if hits:
            print(f'{f}:{i}: invisible/bidi characters {hits}')
" 2>/dev/null || true

# INJ-02: AI-directed instruction phrases in comments/strings/docs
rg -ni 'ignore (all |any )?(previous|prior|above|earlier) (instructions|prompts|rules)|disregard (the |your )?(system|previous|above)|you are now (a|an|in)|new (system )?instructions:|do not (flag|report|mention|include) (this|the following)|(assistant|claude|copilot|gpt|reviewer)[,:]? (please )?(approve|ignore|skip|omit)' \
  --glob '!*.lock' --glob '!node_modules/**' --glob '!vendor/**' . | head -20 || true

# INJ-03: Large base64 blobs in comments (hidden payloads)
rg -n '(#|//|/\*|<!--|;)\s*[A-Za-z0-9+/]{120,}={0,2}' --glob '!*.lock' --glob '!*.min.*' --glob '!*.svg' . | head -10 || true
```

Whitelist note: security tooling, test fixtures, and this file itself legitimately contain INJ-02 phrases. Findings inside `*test*`, `*fixture*`, or the review skill's own tree get dismissed with a reason, not silently skipped.

## LLM Integration Detection (conditional)

Only include these when the gate check finds LLM usage. The greps surface candidate sites; whether the interpolated content is actually untrusted is the agent's judgment call.

```bash
# Gate: does the project call an LLM at all? (empty output = skip the LLM-* group entirely)
rg -l 'import anthropic|from anthropic|import openai|from openai|import ollama|messages\.create|chat\.completions|api\.anthropic\.com|api\.openai\.com' src/ || true

# LLM-01: Prompt-building sites with interpolation (candidate injection points)
rg -n '(prompt|messages|system_prompt|user_content|content)\s*[=:+].{0,50}(f["\x27]|\.format\(|%s|\$\{|\+\s*\w)' --type py --type js --type ts src/ | head -20 || true

# LLM-02: LLM output rendered or executed
rg -n '(response|completion|\.content|message\.content|\.text|output)\w*.{0,60}(innerHTML|dangerouslySetInnerHTML|v-html|st\.markdown|st\.html|eval\(|exec\(|subprocess|os\.system|shell)' src/ | head -20 || true

# LLM-03: API calls inside loops without an iteration bound nearby (cost/DoS)
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    lines = f.read_text(errors='ignore').splitlines()
    for i, line in enumerate(lines):
        if re.search(r'messages\.create|chat\.completions|\.generate\(', line):
            window = lines[max(0, i-15):i]
            in_loop = any(re.match(r'\s*(while|for)\b', w) for w in window)
            bounded = any(re.search(r'range\(|max_|limit|\[:\d', w) for w in window)
            if in_loop and not bounded:
                print(f'{f}:{i+1}: LLM call inside loop with no visible bound')
" 2>/dev/null || true
```

## Python-Specific Detection

### Security
```bash
# shell=True
rg -n 'shell\s*=\s*True' --type py src/ || true

# os.system()
rg -n 'os\.system\(' --type py src/ || true

# Unsafe deserialization
rg -n 'pickle\.loads?\(' --type py src/ || true
rg -n 'yaml\.load\(' --type py src/ | grep -v SafeLoader || true
rg -n '\beval\s*\(' --type py src/ | grep -v 'ast.literal_eval' || true
```

### Subprocess (multi-line aware)
```bash
# subprocess without timeout: MUST use Python for multi-line detection
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    text = f.read_text()
    for m in re.finditer(r'subprocess\.(run|call|check_output|check_call|Popen)\s*\(', text):
        start = m.start()
        depth, pos = 1, m.end()
        while pos < len(text) and depth > 0:
            if text[pos] == '(': depth += 1
            elif text[pos] == ')': depth -= 1
            pos += 1
        call_text = text[m.start():pos]
        if 'timeout' not in call_text:
            line_num = text[:start].count('\n') + 1
            print(f'{f}:{line_num}: subprocess.{m.group(1)}() without timeout=')
" 2>/dev/null || true

# String interpolation in subprocess args
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    text = f.read_text()
    for m in re.finditer(r'subprocess\.\w+\s*\(', text):
        start = m.start()
        depth, pos = 1, m.end()
        while pos < len(text) and depth > 0:
            if text[pos] == '(': depth += 1
            elif text[pos] == ')': depth -= 1
            pos += 1
        call_text = text[m.start():pos]
        if re.search(r'f[\"\\x27]|\.format\(|%\s', call_text) and 'shell' not in call_text:
            line_num = text[:start].count('\n') + 1
            print(f'{f}:{line_num}: f-string/format in subprocess args')
" 2>/dev/null || true
```

### Type Modernization (Python 3.10+)
```bash
# Old typing imports
rg -n 'from typing import.*(Optional|List|Dict|Tuple|Set|Union)' --type py src/ || true

# Public functions without return type
python3 -c "
import re, pathlib
for f in pathlib.Path('src').rglob('*.py'):
    for i, line in enumerate(f.read_text().splitlines(), 1):
        if re.match(r'^(\s{0,8})def\s+(?!_|test_)\w+\(.*\)\s*:', line) and '->' not in line:
            print(f'{f}:{i}: {line.strip()[:80]}')
" 2>/dev/null | head -30 || true

# Unsafe nested dict access on external data
rg -n '\[.+\]\[.+\]' --type py src/ | grep -v 'test' | head -20 || true
```

### Streamlit-Specific
```bash
# st.rerun() without invalidate() in preceding N lines
python3 -c "
import pathlib
for f in pathlib.Path('src/web').rglob('*.py') if pathlib.Path('src/web').exists() else []:
    lines = f.read_text().splitlines()
    for i, line in enumerate(lines):
        if 'st.rerun()' in line:
            window = lines[max(0,i-10):i]
            if not any('invalidate' in w for w in window):
                print(f'{f}:{i+1}: st.rerun() without invalidate() in preceding 10 lines')
" 2>/dev/null || true

# @st.cache_data without TTL
rg -n '@st\.cache_data' --type py src/ | grep -v 'ttl' || true

# print() in web layer
rg -n '\bprint\(' --type py src/web/ 2>/dev/null | grep -v 'console' || true
```

## PHP-Specific Detection

### Security
```bash
# SQL with string interpolation
rg -n '(query|execute|prepare)\s*\(.*[\$"]' --type php src/ \
  | grep -v 'prepare.*?\?' | grep -v bindParam || true

# Shell execution functions
rg -n '\b(exec|system|shell_exec|passthru|proc_open|popen)\s*\(' --type php src/ || true

# File operations with variables (path traversal risk)
rg -n '(include|require|file_get_contents|fopen|unlink|rmdir)\s*\(\s*\$' --type php src/ || true

# echo/print without escaping
rg -n '(echo|print)\s+\$' --type php src/ | grep -v 'htmlspecialchars\|htmlentities' | head -20 || true

# unserialize on potentially untrusted data
rg -n 'unserialize\s*\(' --type php src/ || true
```

### Architecture
```bash
# env() outside config files (Laravel: returns null when cached)
rg -n '\benv\(' --type php src/ --glob '!config/*' 2>/dev/null | head -20 || true

# Missing $fillable/$guarded on Eloquent models
for f in $(find src/ app/ -name '*.php' 2>/dev/null | xargs grep -l 'extends Model' 2>/dev/null); do
  grep -L 'fillable\|guarded' "$f" && echo "$f: missing \$fillable/\$guarded"
done 2>/dev/null || true
```

### Modernization
```bash
# Legacy array() syntax
rg -n '\barray\s*\(' --type php src/ | head -20 || true

# strpos instead of str_contains (PHP 8.0+)
rg -n 'strpos\s*\(' --type php src/ | head -20 || true
```

## JavaScript/TypeScript-Specific Detection

### Security
```bash
# XSS vectors
rg -n 'innerHTML|outerHTML|document\.write|dangerouslySetInnerHTML|v-html' --type js --type ts src/ || true

# eval / Function constructor
rg -n '\beval\s*\(|new\s+Function\s*\(' --type js --type ts src/ || true

# Hardcoded JWT secrets
rg -n 'jwt\.(sign|verify)\s*\(' --type js --type ts src/ | head -10 || true
```

### TypeScript Quality
```bash
# any type usage
rg -n ':\s*any\b' --type ts src/ | head -20 || true

# Type assertions (hiding real errors)
rg -n '\bas\s+\w' --type ts src/ | head -20 || true

# @ts-ignore without explanation
rg -n '@ts-ignore|@ts-expect-error' --type ts src/ || true

# Non-null assertions
rg -n '\w+!' --type ts src/ | grep -v '!=\|!=' | head -20 || true
```

### React Patterns
```bash
# useEffect without cleanup (missing return in useEffect callback)
# Approximate: agents should verify
rg -n 'useEffect\(' --type ts --type js src/ | head -20 || true

# Missing key prop indicator (map without key)
rg -n '\.map\(' --type ts --type js src/ | head -20 || true

# Large components (>200 lines)
find src/ -name '*.tsx' -o -name '*.jsx' 2>/dev/null | xargs wc -l 2>/dev/null \
  | awk '$1 > 200 && !/total$/' | sort -rn || true
```

### Node.js
```bash
# Sync file operations in non-config code
rg -n 'readFileSync|writeFileSync|existsSync' --type js --type ts src/ \
  | grep -v 'config\|setup\|init' | head -20 || true

# Missing error handling middleware (Express)
rg -n 'app\.(get|post|put|delete|patch)\(' --type js --type ts src/ | head -10 || true
rg -n 'err,\s*req,\s*res,\s*next' --type js --type ts src/ || true
```

## Cross-Reference Detection

These checks compare two sources of truth. They're project-specific by nature; the optimizer should generate them based on what registration patterns the project uses.

### Registration Completeness Template
```bash
# Template: check that all X are registered in Y
# Adapt the patterns to the project's registration mechanism

# Example: Python views registered in PAGE_MAP
python3 -c "
import pathlib, re
view_dir = pathlib.Path('src/web/views')
init_file = view_dir / '__init__.py'
if not init_file.exists(): exit()
init_text = init_file.read_text()
for f in view_dir.glob('*.py'):
    if f.name.startswith('_'): continue
    for m in re.finditer(r'def (render_\w+)', f.read_text()):
        if m.group(1) not in init_text:
            print(f'{f}:{0}: {m.group(1)} not registered in PAGE_MAP')
" 2>/dev/null || true

# Example: PHP routes vs controllers
# Example: React pages vs router config
# Example: CLI commands vs command group registration
```

### Export Completeness Template
```bash
# Template: check that modules export what they define
# Example: Python __init__.py exports
python3 -c "
import pathlib, re
pkg = pathlib.Path('src/web/components')
init = pkg / '__init__.py'
if not init.exists(): exit()
init_text = init.read_text()
for f in pkg.glob('*.py'):
    if f.name.startswith('_'): continue
    for m in re.finditer(r'^def (\w+)|^class (\w+)', f.read_text(), re.MULTILINE):
        name = m.group(1) or m.group(2)
        if name and not name.startswith('_') and name not in init_text:
            print(f'{f}: {name} not exported in __init__.py')
" 2>/dev/null || true
```

## Tool-Backed Detection (when CLIs are installed)

These checks require external tools. Availability-gate each on the binary's presence; emit info status if missing, never fail the script.

### Secret Detection with gitleaks

Gitleaks detects hardcoded secrets and API keys. Output format is file:line, and exit code 1 if secrets found, 0 if clean.

Caveat: projects that deliberately commit .env files (private, single-user repos, for instance) need an allowlist to suppress false positives. Record the allowlist in a comment so maintainers understand the exception.

```bash
# Baseline check without allowlist
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . -r 2>/dev/null | grep -E '^[^:]+:[0-9]+:' | head -30 || true
else
    echo "gitleaks not installed, skipped" >&2
fi

# With allowlist (for projects that deliberately track .env)
if command -v gitleaks >/dev/null 2>&1; then
    gitleaks detect --source . -r --exit-code 0 2>/dev/null | while read line; do
        # Suppress findings that are in the allowlist (e.g., intentional .env commits)
        echo "$line" | grep -v '.env:' || true
    done | head -30
else
    echo "gitleaks not installed, skipped" >&2
fi
```

### Dependency Vulnerability Scanning with osv-scanner

osv-scanner queries the OSV (Open Source Vulnerabilities) database against manifest files. It outputs JSON with advisory IDs, package names, and severity ratings. Findings are NOT file:line (there is no line in a manifest that fixes a dependency); report the advisory ID and severity instead.

Supports: package-lock.json (npm), composer.lock (PHP), requirements.txt / pyproject.toml (Python), go.mod (Go), Gemfile.lock (Ruby), and others.

```bash
# Baseline check
if command -v osv-scanner >/dev/null 2>&1; then
    osv-scanner --lockfile=. --json 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if 'results' not in data: sys.exit(0)
    for result in data['results']:
        pkg_name = result.get('package', {}).get('name', 'unknown')
        for vuln in result.get('vulnerabilities', []):
            severity = vuln.get('severity', 'UNKNOWN')
            advisory = vuln.get('id', 'unknown')
            print(f'{pkg_name}: {advisory} [severity: {severity}]')
except:
    sys.exit(0)
" | head -30
else
    echo "osv-scanner not installed, skipped" >&2
fi
```

### Structural Code Patterns with ast-grep

ast-grep matches abstract syntax trees, catching patterns that regex cannot (nested function calls, balanced delimiters, syntactic position constraints). Use YAML rule files or inline patterns.
**Gate on the `ast-grep` binary name, never on the `sg` alias its docs mention.** On Linux `/usr/bin/sg` is shadow-utils' set-group command (from the `login` package), so `command -v sg` succeeds on a machine that has no ast-grep at all and the check silently runs the wrong program. Verified on Mint 22.3, 2026-08-29, where ast-grep is also absent from apt: install it with `npm i -g @ast-grep/cli`, `cargo install ast-grep`, or a release binary.

Regex fails at: function calls nested inside other calls (ast-grep match ID 0 catches only the innermost paren), checking a function call only in specific contexts (e.g., not inside a conditional), or matching balanced structures across multiple lines.

```bash
# Example 1: Python subprocess without timeout (ast-grep version)
# Why regex fails: subprocess calls span multiple lines with nested parens;
# depth tracking in regex is fragile. ast-grep's pattern syntax handles it reliably.
if command -v ast-grep >/dev/null 2>&1; then
    ast-grep --pattern 'subprocess.$_($_)' --lang py src/ 2>/dev/null | grep -E '^[^:]+:[0-9]+:' || true
else
    echo "ast-grep not installed, skipped" >&2
fi

# Example 2: PHP ORM queries without parameter binding
# Why regex fails: prepared statements span lines; the query string,
# bind() calls, and execute() calls are on separate lines.
# YAML rule approach (save as rules.yaml and use --rule rules.yaml):
# ```yaml
# rule:
#   pattern: $db->query($query)
#   where:
#     $query: str
#   message: Direct query without prepared statement
# ```

# Example 3: JavaScript React useEffect without cleanup
# Why regex fails: useEffect bodies are multi-line and may have nested conditionals,
# so detecting "missing return" requires understanding the scope structure.
if command -v ast-grep >/dev/null 2>&1; then
    ast-grep --pattern 'useEffect(() => { $$_ })' --lang ts src/ 2>/dev/null | grep -E '^[^:]+:[0-9]+:' | head -20 || true
else
    echo "ast-grep not installed, skipped" >&2
fi
```

### Test Coverage Gaps with diff-cover or git-based fallback

Detects changed lines with no test coverage. Two strategies: use diff-cover if coverage data exists, or fall back to a git-based check for test file parallels (checking if source file changes have corresponding test changes).

The git fallback assumes a naming convention (test_* prefix or *_test suffix) and is a rough heuristic, not a source of truth. It catches the case where a dev adds a feature but forgets to add tests. It does not verify that the tests actually exercise the new code.

```bash
# Strategy 1: diff-cover (requires .coverage or htmlcov/)
if command -v diff-cover >/dev/null 2>&1 && { [ -f ".coverage" ] || [ -d "htmlcov" ]; }; then
    diff-cover --fail-under=0 --compare-branch=main .coverage 2>/dev/null | grep -E 'Missing lines:|Partial' | head -20 || true
else
    echo "diff-cover not installed or no coverage data" >&2
fi

# Strategy 2: git-based fallback (no coverage data needed)
if [ -d ".git" ]; then
    CHANGED_SRC=$(git diff HEAD --name-only --diff-filter=ACM 2>/dev/null | grep -E '\.(py|php|js|ts|go)$' | grep -v test | grep -v spec | head -20)
    for src in $CHANGED_SRC; do
        # Check if a corresponding test file changed
        test_name=$(echo "$src" | sed "s|^|test_|; s|/|/test_|; s|\.py|_test.py|; s|\.js|.test.js|; s|\.ts|.test.ts|")
        if git diff HEAD --name-only 2>/dev/null | grep -q "$test_name"; then
            continue  # Test file exists
        fi
        echo "$src: no corresponding test file in this diff"
    done | head -20
else
    echo "git not available, skipped" >&2
fi
```

### When to include each tool group

- GL-* (gitleaks): Always include for projects that commit to a non-public remote, and mandatory for public repos (GitHub, GitLab.com). Skip for internal-only code on unreliable systems.
- DEP-* (osv-scanner): Include when the project has manifest files (package.json, requirements.txt, composer.lock, etc.). Skip for vendored dependencies or projects without package management.
- AST-* (ast-grep): Include when regex patterns prove insufficient. Regex-only projects have clean preflight output; projects with complex patterns (nested calls, syntactic position constraints) benefit from ast-grep. Optional but recommended for mature projects.
- TESTGAP-* (diff-cover or git): Include for projects with continuous integration or test gating. Skip for research/prototype code where test coverage is advisory, not required.

