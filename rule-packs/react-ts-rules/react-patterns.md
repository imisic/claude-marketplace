---
paths:
  - "**/*.tsx"
---

# React Component Patterns

Layers on the TypeScript standards.

## Props and Variants
- Define a `ComponentNameProps` interface. Destructure known props and accept an optional `className` for overrides.
- Type variants against a `const` object: `const variants = { success: '...', danger: '...' } as const`, then `variant: keyof typeof variants`. One source of truth for the allowed values.
- Merge class names with a helper, not string concatenation. In Tailwind projects the standard is `clsx` plus `tailwind-merge`, exposed as `cn()`; on other setups use whatever class-merge helper your styling approach provides.

## Composition
- Use your primitive or UI library for form controls, dialogs, sheets, and dropdowns. Don't rebuild a select from scratch.
- Extract a shared component once a pattern repeats three times, not before.

## The Three Async States (mandatory)
Never render a data view without handling all three states. A blank screen while loading is a bug.

```tsx
if (isLoading) return <LoadingState />;
if (error) return <ErrorState message="Failed to load" onRetry={refetch} />;
if (!data.length) return <EmptyState />;
return <DataDisplay data={data} />;
```

## Forms
- Schema-first validation (Zod or equivalent) bridged to the form library (React Hook Form via `zodResolver`).
- Always show inline field-level errors, not just a top-level "something went wrong".

## Accessibility
- Every icon-only button needs an `aria-label`.
- Every modal traps focus (most primitive libraries handle this; verify it).
- Interactive elements get a visible focus state and press feedback.
