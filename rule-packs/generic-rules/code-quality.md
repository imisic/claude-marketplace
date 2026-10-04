# Code Quality

Always-on baseline for keeping a codebase legible and small.

## Single Responsibility
- One function, one job. If a function needs a paragraph to explain, split it.
- Side effects at the edges, pure logic in the middle. Isolate I/O from decisions so the decisions are testable.
- Composition over inheritance.

## DRY, But Not Too Dry
- Don't repeat yourself. Two copies is fine; three means extract.
- Don't over-abstract. No flexibility or configurability nobody asked for. No abstraction for a single call site.

## Minimum Code
- Write the least code that solves the problem. No features beyond what was asked.
- No error handling for impossible states. Handle what can actually happen.
- Senior-engineer test: could 200 lines be 50? If yes, rewrite before shipping.

## Replace, Don't Append
- No `v2`, `_new`, `_final`, or `_improved` copies. Update the original and delete what you replace.
- Remove imports and variables your change orphaned. Flag pre-existing dead code; don't silently delete it.

## Complexity Signals (refactor triggers)
- Files over ~500 lines and functions over ~30 lines are review hot spots. New code in an already-large file should shrink it, not grow it.
- Nesting deeper than 4 levels, or more than 4 parameters, is a signal to extract a value object or split the function.

## Comments
- Comment the why, not the what. The code already says what it does.
- Follow the established patterns in the file you're editing. Match its style even if you'd do it differently.

## Performance (measure first)
- Profile before optimizing. Don't guess at bottlenecks.
- Watch for N+1: never issue a query inside a loop. Batch-load before the loop.
- Index the columns you filter, join, and order by.
- Cache expensive work with real invalidation. A stale cache is worse than no cache.
- Lazy-load. Don't fetch data you won't use.
