---
name: generic-rules
tagline: Claude Code rules for security, code quality, architecture and CSS. Use this baseline alongside a language pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/generic-rules
tags: developers, security, claude-code, standards, rules
---

The rules I want Claude to follow on every project, regardless of language. Four files that carry the discipline without any project's specifics baked in.

**What's inside**

- `security-discipline.md` (always on): input validation, injection, output escaping, least-privilege access, secrets, timing-safe comparison, time-of-check to time-of-use (TOCTOU) races. Language-neutral; the language pack names the exact calls.
- `code-quality.md` (always on): single responsibility, DRY without over-abstraction, minimum code, replacing old code instead of adding a second version beside it, complexity thresholds, measure-before-optimize.
- `architecture.md` (always on): layered separation (transport, logic, persistence), clear boundaries, fail-fast, the add-a-feature checklist.
- `css-discipline.md` (loads on `*.css`): token-first, search-before-adding, no hardcoded colors, no inline styles, focus and reduced-motion.

**How to use**

Download the pack and copy its rule files (`architecture.md`, `code-quality.md`, `css-discipline.md` and `security-discipline.md`) into your project's `.claude/rules/`. If you copy from a clone of the GitHub repo instead, leave out `STOREFRONT.md`; it is the website description, not a rule, and the download does not include it. Files with no `paths:` front matter load on every turn; `css-discipline.md` scopes itself to stylesheets. Layer a language pack (PHP, Python) on top for the stack-specific enforcement.

Want these tuned to your actual codebase instead of generic? Run `/a-rules-optimizer` from the dev-workflow-forge plugin: it reads your repo and rewrites the rules around your real conventions.
