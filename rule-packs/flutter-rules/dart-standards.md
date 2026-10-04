---
paths:
  - "**/*.dart"
---

# Dart Standards

Layers on the generic code-quality and architecture rules.

## Null Safety
- Non-nullable by default. Add `?` only where null is a real state for the value.
- Use `!` only when you can prove the value is non-null; prefer `??` and `?.`.
- Use `late` sparingly, only for a value guaranteed to be set before its first read.

## Naming
- Classes `PascalCase`, files `snake_case.dart`, variables and functions `camelCase`, private members `_leadingUnderscore`, global constants `SCREAMING_SNAKE_CASE`.

## Idioms
- `const` constructors wherever possible; `final` over `var`.
- Named parameters for anything with more than one or two arguments.
- Keep widgets small and focused. Extract a method rather than nesting deeply.
- Extension methods for utilities rather than free-floating helpers.

## Async
- `async`/`await` over raw `Future` chains. Wrap awaited calls in try-catch.
- `Future.wait` for genuinely parallel work.
- Cancel stream subscriptions in `dispose()`. A live subscription after dispose is a leak and a crash.

## Collections and Imports
- Collection literals (`[]`, `{}`), the spread operator, and `for`/`if` inside collection literals.
- Import order: `dart:`, `package:`, then relative. Use `show`/`hide` to keep imports narrow.

## Docs and Lint
- `///` doc comments on public APIs.
- Follow `flutter_lints` (or your `analysis_options.yaml`). Fix analyzer warnings; don't suppress them without a reason.
