# Shared Reference Files

The following files in this directory are **duplicated** into `a-rules-optimizer/references/`:

- `review-dimensions.md`: taxonomy of review categories
- `pattern-detection.md`: detection script library by language

Both `a-review-optimizer` and `a-rules-optimizer` read these. Each skill keeps its own copy so it stays self-contained and can be installed on its own.

## When editing one, update the other

If you change `review-dimensions.md` or `pattern-detection.md` here, **update the copy in `a-rules-optimizer/references/` in the same commit**. The two copies must stay identical.

Quick parity check, run from this skill's directory:

```bash
diff -q references/review-dimensions.md ../a-rules-optimizer/references/review-dimensions.md
diff -q references/pattern-detection.md ../a-rules-optimizer/references/pattern-detection.md
```

Both should print nothing. If they diverge, pick the authoritative version and sync.

## Deliberately not shared: the project-profiling step

The project-profiling step is duplicated on purpose (`a-review-optimizer/SKILL.md` Phase 2, inline bash; `a-rules-optimizer/SKILL.md` Phase 1, an Explore brief). The two execution paths differ, and a shared file would have to ship into both skills anyway, so each keeps its own. Audited 2026-10-11 (decision D2); do not re-raise.
