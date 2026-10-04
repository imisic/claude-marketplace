# Review Dimensions Taxonomy

Use this during the gap-analysis phase to identify what the existing skill or rule set is missing. For each dimension, check whether it is already covered AND whether the project actually needs it.

Not every project needs every dimension. A CLI tool doesn't need "WebSocket security." A static site doesn't need "N+1 query detection." Skip what's irrelevant, flag what's missing and needed.

## Security Dimensions

### Input Handling
- SQL injection (parameterized queries, ORM safety)
- Command injection (subprocess, exec, system calls)
- Path traversal (filesystem operations with user input)
- XSS (output encoding, template escaping)
- SSRF (URL construction from user input)
- Deserialization (pickle, unserialize, YAML load, eval)
- ReDoS (catastrophic regex backtracking on user input)
- Header injection (CRLF in user-controlled headers)
- Template injection (SSTI in Jinja2, Twig, EJS)

### Credentials & Secrets
- Hardcoded passwords, API keys, tokens in source
- Secrets in logs, error messages, or stack traces
- Secrets committed to git (even in history)
- Encryption keys with wrong file permissions
- Default/weak passwords in config examples
- Credentials in URLs (basic auth in connection strings)

### Authentication & Authorization
- Missing auth checks on endpoints/routes
- Auth without authz (logged in but not permitted)
- Session fixation (no regeneration after login)
- CSRF protection on state-changing requests
- JWT: hardcoded secret, missing expiry, alg:none
- Cookie flags: httpOnly, secure, sameSite
- Timing attacks on password/token comparison
- Password hashing: bcrypt/argon2 vs MD5/SHA1

### Data Protection
- Sensitive data in localStorage/sessionStorage
- PII in logs or analytics
- Missing encryption at rest for sensitive data
- Broad CORS configuration with credentials
- Missing rate limiting on auth endpoints

### Hostile Content (reviewer integrity)
These run as deterministic preflight checks ONLY, never as agent-prompt checks: the AI reviewer is the attack target here, and a hijacked reviewer cannot be trusted to flag its own hijack.
- Invisible or bidirectional Unicode in source (Trojan Source: U+202A-202E, U+2066-2069, zero-width U+200B-200D, U+FEFF)
- Instruction-like phrases aimed at AI tools in comments/strings/docs ("ignore previous instructions", "you are now", "do not flag this")
- Large encoded blobs (base64) in comments with no stated purpose

## LLM Integration Dimensions (conditional)

Only when the project calls an LLM API (imports anthropic/openai/ollama, or hits an LLM HTTP endpoint). Skip entirely otherwise.

### Prompt Injection
- Untrusted content (user input, scraped pages, file contents, third-party API responses) concatenated into prompts without delimiting or marking
- System instructions and untrusted content mixed into the same message role
- LLM output fed into subsequent prompts unsanitized (injection laundering across calls)

### Output Handling
- LLM output rendered as HTML/markdown without escaping
- LLM output parsed as code, SQL, or shell, or passed to eval/exec
- LLM output driving decisions (scores, filters, routing) without schema or bounds validation
- Unbounded loops calling the API (no max iterations, no cost guard)

### Tool Use & Data Exposure
- Tools/functions exposed to the model broader than the task needs
- Secrets or PII included in prompt context
- Model-controlled parameters reaching filesystem, network, or DB operations without validation

## Architecture Dimensions

### Configuration Management
- Hardcoded values that should be configurable
- Config access scattered vs centralized
- Missing defaults for optional config
- Environment-specific logic in business code
- Secrets mixed with non-secret config

### Error Handling Strategy
- Generic catch-all exceptions
- Swallowed exceptions (catch + pass/ignore)
- Empty or log-only catch blocks (catch that discards the error and continues)
- Error suppression operators (@ in PHP, error_reporting(0), blanket 2>/dev/null in shell)
- Fail-open error paths (error branch returns a success-looking default: None, true, empty list)
- Missing cleanup on failure (partial state)
- Missing timeouts on external calls
- Error messages that don't help diagnose
- Inconsistent error return shapes
- Missing retry logic with backoff where needed

### Shell Scripts
- Missing set -euo pipefail (or targeted equivalents) in scripts that change state
- || true or 2>/dev/null on state-changing commands (masks real failures; fine on read-only probes)
- cd without failure guard (subsequent commands run in the wrong directory)
- mktemp or sensitive output files without an EXIT trap cleanup
- Unquoted variable expansions in paths (word splitting on spaces)

### State Management
- Framework-appropriate state patterns (session_state, context, store)
- Mutable shared state without synchronization
- State scattered across globals
- Cache invalidation after mutations
- Stale state after redirects/reruns

### Dependency & Coupling
- Circular imports/dependencies
- Layer violations (presentation ↔ data)
- God objects everything depends on
- Components reaching into other components' internals
- Business logic in infrastructure code

### Registration & Wiring
- Routes/views/commands registered correctly
- Middleware/interceptors applied where needed
- Event listeners registered for dispatched events
- Components exported from package indexes
- DI container bindings for all interfaces

### API Design
- Consistent response shapes
- Input validation at boundaries
- Versioning strategy for external APIs
- Batch operations where N individual calls exist
- Pagination on list endpoints

### Consistency
- Same pattern used differently across files
- Naming conventions followed/violated
- Import ordering convention
- File/directory organization convention

## Quality Dimensions

### Type Safety
- Missing type annotations on public interfaces
- Nullable access without null check
- Generic "any"/"mixed" where specific types work
- Type assertions hiding real type errors
- Dict/array access on external data without .get()
- Inconsistent use of type aliases

### Dead Code
- Functions never called from any module
- Unused imports
- Commented-out code blocks (>3 lines)
- Unreachable code after return/throw
- Feature flags always true/false
- Config keys defined but never accessed
- Event handlers never triggered
- Store actions never dispatched

### Complexity
- Files over 300 lines
- Functions over 50 lines
- Nesting over 4 levels
- Cyclomatic complexity over 10
- Parameter count over 5
- Boolean parameters (should be named/enum)

### Duplication
- Same logic in 2+ places
- Similar error handling repeated
- Similar validation in multiple endpoints
- Copy-pasted data transformations
- Similar test setup across test files

### Modernization
- Outdated syntax for the language version
- Old library APIs when newer alternatives exist
- Manual implementations of things the stdlib handles
- Deprecated function/method usage

### Naming
- Misleading names (function does more than name suggests)
- Boolean variables not starting with is/has/can/should
- Unclear abbreviations
- Inconsistent naming convention within a module

### Test Coverage
- Public methods with complex logic but no tests
- Edge cases not covered (empty input, null, overflow)
- Error paths not tested
- Integration points not tested
- Tests that only test the happy path

## Performance Dimensions

### Query Efficiency
- N+1 queries (loop + query pattern)
- SELECT * when specific columns suffice
- Missing LIMIT on unbounded queries
- Filtering/sorting in app instead of DB
- Missing indexes on filtered/joined columns
- Missing connection pooling
- Repeated identical queries per request

### I/O Efficiency
- File/HTTP reads inside loops
- Synchronous I/O in async context
- Loading full files when streaming works
- Not closing handles/connections (resource leaks)
- Missing batching on external API calls

### Caching
- Same expensive computation repeated per request
- Rarely-changing data fetched every time
- Missing cache invalidation after writes
- Cache keys not accounting for all parameters

### Memory
- Full dataset loaded when pagination/chunking works
- String concatenation in loops (vs join/builder)
- Large objects retained when no longer needed
- Missing generators/iterators for large sequences

### Algorithmic
- O(n²) when O(n) or O(n log n) is possible
- Linear search where hash/set lookup works
- Repeated sorts on same data
- Unnecessary serialization/deserialization cycles

### Response/Payload
- API returning more data than consumer needs
- Missing compression on large responses
- Missing pagination
- Full page re-render when partial update suffices

## AI Slop Dimensions (optional, for --slop equivalent)

### Over-Abstraction
- Interface with exactly one implementation
- Factory for something instantiated once
- Strategy with one strategy
- Wrapper that adds no behavior

### Premature Generalization
- Config options no code path exercises
- Parameters always called with same value
- Plugin systems with zero plugins

### Confident-But-Wrong
- Error handling that doesn't actually handle anything
- Retry without idempotency consideration
- Pagination that breaks on last page
- Auth checking login but not permissions

### Copy-Paste Artifacts
- Variable names from a different context
- Comments describing what code used to do
- Imports for unused libraries
- Exception types from wrong framework
