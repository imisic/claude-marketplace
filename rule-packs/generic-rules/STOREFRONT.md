---
name: generic-rules
tagline: Claude Code rules for security, code quality, architecture and CSS. Use this baseline alongside a language pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/generic-rules
tags: developers, security, claude-code, standards, rules
---

The rules I want Claude to follow on every project, regardless of language. Four files that carry the discipline without any project's specifics baked in.

**What's inside**

- `security-discipline.md` (always on): input validation, injection, output escaping, least-privilege access, secrets, timing-safe comparison, TOCTOU. Language-neutral; the language pack names the exact calls.
- `code-quality.md` (always on): single responsibility, DRY without over-abstraction, minimum code, replace-don't-append, complexity thresholds, measure-before-optimize.
- `architecture.md` (always on): layered separation (transport, logic, persistence), clear boundaries, fail-fast, the add-a-feature checklist.
- `css-discipline.md` (loads on `*.css`): token-first, search-before-adding, no hardcoded colors, no inline styles, focus and reduced-motion.

**How to use**

Download the pack and drop the `.md` files into your project's `.claude/rules/`. Files with no `paths:` front matter load on every turn; `css-discipline.md` scopes itself to stylesheets. Layer a language pack (PHP, Python) on top for the stack-specific enforcement.

Want these tuned to your actual codebase instead of generic? Run `/a-rules-optimizer` from the dev-workflow-forge plugin: it reads your repo and rewrites the rules around your real conventions.
