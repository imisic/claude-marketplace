---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# Data Fetching

Layers on the TypeScript standards. Assumes a server-state library (React Query / TanStack Query); the discipline transfers to SWR.

## One Tool for Server State
- A server-state library is the only tool for fetching, caching, and syncing server data. Don't also keep server data in a global client-state store (Redux, Zustand, Jotai). Local UI state (modals, filters, toggles) stays in `useState` or `useReducer`.

## Check Before You Use
- If your API wraps responses (`{ success, data, error }`), check `success` and throw on failure before returning `data`. The query function returns the inner payload, not the envelope.

## Query Key Factory
- Give each domain a flat query-key factory so invalidation stays consistent:

```ts
export const userKeys = {
  all: ['users'] as const,
  list: (f: UserFilters) => [...userKeys.all, 'list', f] as const,
  detail: (id: string) => [...userKeys.all, 'detail', id] as const,
};
```

## Hook Naming
- Fetch list `use<Resource>s()`, fetch one `use<Resource>(id)`, mutate `useCreate/Update/Delete<Resource>()`.

## Mutations
- On success: invalidate the queries the mutation affects, then show a success toast.
- On error: show the error toast. Never let a failed mutation fail silently.

## Auth Tokens
- Prefer an httpOnly cookie the browser sends automatically over a token in `localStorage`. A JS-readable token is an XSS payload's first prize.
- Keep a separate JS-readable, non-sensitive flag if the SPA needs to know it's logged in; the actual credential stays httpOnly.
