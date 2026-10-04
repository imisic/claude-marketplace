# Architecture Discipline

Always-on. A pattern, not a framework. Adapt the names to your stack; keep the separation.

## Layered Separation
- Keep transport concerns, business logic, and persistence in separate layers. A request handler that also runs business rules and writes to the database is three responsibilities in one place.
- A common shape: Handler (transport) to Service (business logic) to Model or Repository (persistence). Handlers translate requests and responses; services own the rules and the mutations; models own data access.
- Mutations go through the logic layer. Reads may skip it. Don't put validation, business rules, or cache invalidation in the transport layer.

## Boundaries and Interfaces
- Each unit has one clear responsibility, a well-defined interface, and can be understood without reading its internals.
- If you can't change a unit's internals without breaking its callers, the boundary is wrong.
- Trace the data flow before writing code: know where input enters and where output goes.

## Failure Handling
- Fail explicitly with context. No silent exception swallowing.
- A catch block with no log call and no re-raise inside it is a bug, not a style choice. This is the checkable form of the rule above: if the block neither records the failure nor propagates it, the failure is gone.
- Don't raise the language's generic base exception for a domain condition. A caller cannot tell a domain failure from an unrelated runtime error, so it either catches too much or catches nothing.
- Include the inputs that caused the failure, sanitized if they may carry personal data. "Failed to parse JSON" without the path is unactionable.
- Watch for fail-open error paths: an error branch that returns a success-looking default (null, true, an empty list) turns a failure into a wrong answer that nothing reports.
- Error-suppression operators and blanket output redirection on state-changing commands hide real failures. Acceptable on a read-only probe, not on a mutation.
- Validate early, fail fast: check preconditions at the entry of a function, not deep inside it.
- The user-facing message stays friendly; the log carries the full detail. Never leak internals to the user.

## Adding a Feature (checklist shape)
- Persistence change first (a migration if the schema moves), then the model, then the service, then the handler, then the view. Wire feature flags and navigation last.
- Keep files that change together close together. Split by responsibility, not by technical layer.
