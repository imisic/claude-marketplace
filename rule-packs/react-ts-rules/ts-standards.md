---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---

# TypeScript Standards

Layers on the generic code-quality and architecture rules. Written for a React SPA, but the TypeScript rules hold for any TS project.

## TypeScript
- Strict mode on. No `any`. Reach for `unknown` and narrow, or write the real type.
- Absolute imports via a path alias (for example `@/`), not long `../../../` chains.
- Domain-scoped type files (`types/user.ts`, `types/billing.ts`), not one giant `types.ts`.

## Naming
- Types and interfaces: `PascalCase` (`User`, `CreateClassInput`).
- Component props interface: `ComponentNameProps`.
- When consuming an API, match the backend's field names rather than silently renaming, so the payload and the type line up.

## File Naming
- Components `kebab-case.tsx`, pages `<name>-page.tsx`, hooks `use-<name>.ts`, types `<domain>.ts`, utils `<name>.ts`. Pick one convention and hold it.

## Import Order
1. React and external libraries
2. UI primitives
3. Custom components
4. Feature modules
5. Hooks, lib, types
6. Relative (sibling) imports

## Exports
- Named exports only. No `export default`. Default exports make renames lossy and hurt auto-import.
- One component per file for page-level components; a small helper component can share the parent file.

## Client-Side Security
- The client bundle is public. Never put an API secret, private key, or server-only token in code that ships to the browser.
- Don't set `dangerouslySetInnerHTML` from any value that isn't statically known or run through a sanitizer. It is the one place React stops escaping for you.
