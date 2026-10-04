---
paths:
  - "**/*.php"
---

# PHP Standards

Layers on the generic code-quality and architecture rules; this file is the PHP-specific enforcement.

## PHP 8.2+
- `declare(strict_types=1);` at the top of every file.
- Type declarations on every function: parameters and return types.
- Enums for fixed sets of constants, not loose string literals.
- When a domain enum exists, compare against the enum case (or its `->value`), not a raw string literal. A raw `=== 'archived'` in a file whose siblings use the enum is the tell.
- `match` over `switch` for value mapping.
- Constructor property promotion.

## Naming
- Classes `PascalCase`, methods and variables `camelCase`, constants `UPPER_SNAKE_CASE`, DB columns `snake_case`.

## Error Suppression
The `@` operator is allowed only with explicit intent, shown one of these ways:
- A sibling `// reason: ...` comment explaining why the failure is safe to swallow.
- A check that distinguishes success from failure: `if (!@unlink($f) && file_exists($f)) { /* handle */ }`.
- An idempotent mkdir with a recheck: `@mkdir($d, 0700, true); if (!is_dir($d)) { throw ...; }`.

A bare `@`-suppressed call with none of the above is rejected in review.

## Efficiency
- Batch-load before a loop; never query inside a loop (N+1).
- Operate directly and handle the error instead of check-then-act (TOCTOU).
- Guard updates in loops with change detection; avoid unconditional writes.
- Read only the columns and rows you need.

## Complexity
- Files over ~500 lines and methods over ~30 lines are hot spots. Shrink, don't grow, an already-large file.
- Strip unused `use` imports as you edit. If a class is referenced only in a docblock, use a fully-qualified name there and drop the `use`.

## Debug Output
- No `var_dump()`, `print_r()`, or `dd()` in committed code. Use logging. Keep throwaway experiments out of the committed tree.
