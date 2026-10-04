# Shared Reference Files

The following files in this directory are **duplicated** from `a-review-optimizer/references/`:

- `review-dimensions.md`: taxonomy of review categories
- `pattern-detection.md`: detection script library by language

Both `a-rules-optimizer` and `a-review-optimizer` read these. Each skill keeps its own copy so it stays self-contained and can be installed on its own.

## When editing one, update the other

If you change `review-dimensions.md` or `pattern-detection.md` here, **update the copy in `a-review-optimizer/references/` in the same commit**. The two copies must stay identical.

Quick parity check, run from this skill's directory:

```bash
diff -q references/review-dimensions.md ../a-review-optimizer/references/review-dimensions.md
diff -q references/pattern-detection.md ../a-review-optimizer/references/pattern-detection.md
```

Both should print nothing. If they diverge, pick the authoritative version and sync.

## Why not a symlink?

Symlinks silently break on some filesystems (NTFS without Developer Mode, some synced drives) and hide the dependency; an editor sees one file and doesn't realize changes propagate. Explicit duplication with this note makes the coupling visible.

