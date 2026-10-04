---
paths:
  - "**/*.py"
---

# Python Standards

Layers on the generic code-quality and architecture rules.

## Type Hints
- Annotate every public function's parameters and return type.
- Use `X | None` (3.10+), not `Optional[X]`. Use lowercase generics (`list[str]`, `dict[str, int]`), not `List` or `Dict`.
- Dataclasses for structured data, not ad-hoc dicts passed between functions.

## Naming
- `snake_case` for functions and variables, `UPPER_SNAKE_CASE` for module-level constants, `_prefix` for private or internal, `PascalCase` for classes and dataclasses.

## Logging
- `logger = logging.getLogger(__name__)` at module level. Never `print()` for anything that isn't a CLI's own stdout contract.
- Levels: DEBUG for detail, INFO for progress, WARNING for recoverable issues, ERROR for failures. Use `logger.exception()` to capture the traceback.

## Error Handling
- Catch specific exception types, never bare `except:`.
- Log and continue where a single item can fail without sinking the batch; let truly unexpected errors propagate to a top-level handler.

## Imports
- Import specific names; no `from x import *`.
- No circular imports. Keep config and constants in a leaf module that imports nothing local.

## Anti-Patterns
- No mutable default arguments (`def f(x=[])`).
- No hardcoded config. Values come from environment or a config module, not literals scattered through the code.
- No `print()` debugging left in committed code. Use the logger.
- Lint before committing (`ruff check` or your linter of choice).
