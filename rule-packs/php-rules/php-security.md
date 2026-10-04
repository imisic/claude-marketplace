---
paths:
  - "**/*.php"
---

# PHP Security

The PHP enforcement of the generic security discipline. Read the generic `security-discipline` rules first; this file names the PHP calls that satisfy them.

## Input Validation
- Use `filter_var()` for email and URL validation.
- Only allow `http://` and `https://` URL schemes; reject the rest.
- Path containment: any filesystem path built from a request or DB value must resolve with `realpath()` and be rejected (404) unless the result is prefixed by the realpath'd base directory plus a separator, checked before you open the file.

## Output Escaping
- Escape every dynamic value in a view with `htmlspecialchars($v, ENT_QUOTES, 'UTF-8')` or your framework's escape helper. Never echo raw input.
- For JSON responses, use `JSON_HEX_TAG | JSON_HEX_APOS | JSON_HEX_QUOT | JSON_HEX_AMP | JSON_UNESCAPED_SLASHES` so a value can't break out of an inline `<script>`.
- When interpolating a DB-sourced filename or slug into an HTTP header (`Content-Disposition`), strip CR and LF and escape quotes.

## Credentials and Comparison
- Verify passwords with `password_verify()` against a `password_hash()` bcrypt or argon2 digest. Never md5, sha1, or plaintext.
- Compare API keys, tokens, signatures, CSRF validators, and OAuth `state` with `hash_equals()` (trusted value first, non-empty guarded), never `==` or `===`.

## CSRF and Sessions
- CSRF token on every state-changing form and on JSON or AJAX POSTs; validate before acting on the body.
- Session cookies: httponly, secure, SameSite=Lax; regenerate the session id on login; set a timeout.

## File Uploads
- Validate MIME, size, and extension; sanitize the filename; store under a generated unique name.
- Do not accept SVG uploads. A MIME and extension check does not stop a weaponized SVG (`<script>`, `on*=`, `javascript:` hrefs).

## Concurrency
- `file_put_contents()` to shared state must pass `LOCK_EX`. Operate directly and handle the error rather than check-then-act.

## Dangerous Functions
- Avoid `extract`, `unserialize`, `eval`, `shell_exec`, `system`, `exec`, `passthru`, `proc_open`. If one is genuinely required, whitelist the binary with an absolute path, pass arguments through `escapeshellarg()`, and document why.
