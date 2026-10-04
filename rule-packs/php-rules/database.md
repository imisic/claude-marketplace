---
paths:
  - "**/*.php"
  - "**/*.sql"
---

# Database Standards

## Migrations (mandatory)
- Every schema change gets a migration file: creating tables, adding or removing columns, changing types, adding or removing indexes or constraints.
- Number migrations in sequence and include both an UP and a DOWN section so rollback is possible.
- Use `IF EXISTS` and `IF NOT EXISTS` so a migration is idempotent.
- Test the DOWN section locally before deploying. A migration you can't roll back is a one-way door.

## Access Pattern
- All database access goes through a model or repository layer. No raw SQL in controllers or views.
- If your project has tooling that diffs content edits and invalidates cache, route large TEXT and content-field edits through it instead of ad-hoc UPDATE statements; if it doesn't, still avoid blind bulk updates to those fields (preview the change and invalidate any cache by hand).

## Query Safety
- Prepared statements for every query that touches a variable: `$stmt->execute(['id' => $id])`.
- LIMIT and OFFSET can't be bound as parameters in PDO. Cast to int and validate the range, then concatenate. Never interpolate a raw request value.
- Define an allow-list of columns a query may filter or order by, and reject anything outside it. Never build a WHERE or ORDER BY clause from an unvalidated field name.

## Conventions
- Tables plural, `snake_case`. Primary key `id`. Foreign keys `{table}_id`. Timestamps `created_at` and `updated_at`. Soft delete `deleted_at` (nullable).

## Indexing
- Index the columns you look up, filter, join, and order by: foreign keys, slugs, status, and any dated sort column. Add composite indexes for the multi-column filters you actually run.
