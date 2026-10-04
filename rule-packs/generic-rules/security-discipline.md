# Security Discipline

Always-on baseline, language-neutral. The stack-specific enforcement (which escape helper, which hashing call) lives in the language pack that layers on top. This file is the discipline every project owes regardless of stack.

## Input Validation
- Validate and sanitize all input at system boundaries: request handlers, API endpoints, CLI args, queue consumers, webhook receivers.
- Whitelist, don't blacklist. Reject unknown values rather than trying to strip bad ones.
- Enforce length limits, type checks, and range bounds on every field.
- Only allow `http://` and `https://` for user-supplied URLs. Reject other schemes (`javascript:`, `file:`, `data:`).
- Cap array and batch sizes on ingest endpoints (for example, max 200 items) so one request can't exhaust memory.
- Bound date and time inputs to a sane range instead of trusting the parser.

## Injection
- Parameterized queries only. Never concatenate user input into SQL, shell commands, or any interpreter string.
- Context-appropriate escaping on output: HTML, SQL, shell, JSON, and URL each need their own escaping, applied at the boundary where the value leaves your control.

## Output Escaping (XSS)
- Escape every dynamic value before it lands in HTML. Treat all external data (DB rows, API responses, feed titles) as untrusted.
- Validate a URL's scheme before emitting it in an `href` or `src` attribute.
- When building HTML from data that arrived over the wire, prefer text nodes and safe builders over raw string interpolation.

## Access Control
- Least privilege by default: file permissions, DB users, API scopes, tokens.
- Return 404, not 403, for a resource a user isn't allowed to see. Don't confirm its existence.
- Enforce authorization on the server for every state-changing request. Never rely on a hidden UI control as the gate.
- CSRF protection on all state-changing requests.
- **Never emit a per-session CSRF token on a route a page cache can store.** A reverse proxy or edge cache saves the rendered HTML with one visitor's token baked in and serves it to everyone: the token leaks across visitors, and every other visitor's submit fails. The trap is a shared partial or layout, where a form lands on a page nobody remembers is cacheable. A form carrying a session token belongs on an explicitly no-cache route. Where one genuinely must live on a cached page (an anonymous signup, say), drop the session token and defend with other controls (double opt-in, honeypot, per-IP rate limit), then write down why the exception exists so a later audit doesn't "fix" it back.

## Secrets
- No secrets in source. Use environment variables or config files outside the web root.
- Never log secrets, tokens, passwords, or full external responses. Truncate and redact before logging.

## Credentials and Comparison
- Store passwords only as a slow salted hash (bcrypt, argon2, scrypt). Never md5, sha1, or plaintext.
- Compare secrets, tokens, signatures, and CSRF or OAuth values in constant time. A plain `==` on a secret is a timing oracle.

## Time-of-Check to Time-of-Use
- Don't check-then-act on shared state ("file exists? then open"). Operate directly and handle the error; the gap between check and act is a race.
- Writes to shared files or state need a lock or an atomic operation. A partial write under concurrency is a corruption bug.

## Dangerous Constructs
- Avoid dynamic code execution and unsafe deserialization on any value that could be attacker-influenced. Eval, template-from-input, and object deserializers are remote-code-execution surfaces.

## Outbound HTTP
- Verify TLS on outbound calls. Don't disable certificate checks to make something work.
- Set a timeout on every external call. A hung dependency shouldn't hang your process.
- Validate the destination of any request whose URL came from user input: allowlist schemes and hosts. `python-rules/python-security.md` has a worked SSRF section if you run that pack.
