---
name: react-ts-rules
tagline: Claude Code rules for React and TypeScript, covering components, forms and data fetching. Use alongside the generic rules pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/react-ts-rules
tags: developers, claude-code, rules
---

The React and TypeScript layer that sits on top of the generic pack. Drawn from a production React 19 and Vite SPA, generalized so the rules hold whatever your folder layout is.

**What's inside**

- `ts-standards.md`: strict mode with no `any`, alias imports, naming and file conventions, named-exports-only, and the two client-side security checks (no secrets in the bundle, no unsanitized `dangerouslySetInnerHTML`).
- `react-patterns.md`: props-and-variant patterns (`as const` maps, `cn()` merging), composition over rebuild, the mandatory loading, error, and empty async states, schema-first forms, and accessibility basics.
- `data-fetching.md`: one tool for server state, check-before-use, query-key factories, hook naming, mutations that refresh affected queries and show feedback, and httpOnly-cookie auth over `localStorage` tokens.

**How to use**

Download the pack and copy its rule files (`data-fetching.md`, `react-patterns.md` and `ts-standards.md`) into `.claude/rules/` alongside the generic pack. If you copy from a clone of the GitHub repo instead, leave out `STOREFRONT.md`; it is the website description, not a rule, and the download does not include it. They load whenever you touch a `.ts` or `.tsx` file. Adjust the import-alias and folder references to your project.

Want these tuned to your actual codebase? Run `/a-rules-optimizer` from the dev-workflow-forge plugin.
