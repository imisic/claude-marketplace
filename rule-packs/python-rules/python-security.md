---
paths:
  - "**/*.py"
---

# Python Security

The Python enforcement of the generic security discipline. Weighted toward the surfaces that data pipelines and scrapers actually hit.

## Subprocess
- Never `shell=True`. Never `os.system()`. Use `subprocess.run()` with a list of arguments.
- Never interpolate a variable into a command string (no f-strings, `.format()`, or `%` in the args list).
- Always set `timeout=` on `run()`, `call()`, `wait()`, and `communicate()`.

## Unsafe Deserialization
- YAML: `yaml.safe_load()` only. Never `yaml.load()` without `Loader=SafeLoader`.
- Never `pickle.load()` or `pickle.loads()` on data that could be untrusted; pickle executes arbitrary code on load.
- No `eval`, `exec`, or `marshal.loads` on external input. For literals, `ast.literal_eval()` is safe (it doesn't execute code).

## SSRF on Outbound Requests
- Validate every URL before an HTTP request when the URL came from anywhere untrusted (scraped content, search results, sitemaps, user input): resolve the host and reject private, loopback, link-local, reserved, multicast, and unspecified addresses.
- Re-validate the final URL after following redirects. A safe first hop can redirect to an internal address.
- URLs from operator config or environment are trusted; a scraped URL becoming part of a config-derived URL is not. Keep that boundary.
- Bound request volume (crawl and page budgets), set timeouts, and back off on retry.

## Regex on Untrusted Input
- Patterns that run over crawled or user-supplied text must avoid catastrophic backtracking: no nested quantifiers (`(a+)+`, `(.*)*`) or overlapping alternation inside repetition. Prefer several small anchored patterns over one greedy alternation.

## Secrets
- API keys, tokens, and passwords come from `os.getenv()` or an encrypted config, never hardcoded. `.env.example` files hold placeholders, not real values.
- Never log a secret. Redact sensitive fields before any logging.
- Key files on disk get `0o600` permissions.

## Files and Archives
- Validate archive member names before extracting a tar: reject entries containing `../` or starting with `/`. Validate `arcname` on `tar.add()` too.
- `os.walk(followlinks=False)`; remember `Path.rglob()` follows symlinks by default.
- Temp files from `mkstemp()` or `NamedTemporaryFile(delete=False)` get cleaned up in a `finally` block.
