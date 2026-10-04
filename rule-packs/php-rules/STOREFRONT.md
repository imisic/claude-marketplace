---
name: php-rules
tagline: Claude Code rules for PHP 8.2+, covering types, database access and security. Use alongside the generic rules pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/php-rules
tags: developers, security, claude-code, rules
---

The PHP layer that sits on top of the generic pack. Broad `paths:` globs (`**/*.php`), so it works whatever your directory layout is.

**What's inside**

- `php-standards.md`: `declare(strict_types)`, typed signatures, enums over string literals, `match` over `switch`, the disciplined `@`-suppression patterns, N+1 and TOCTOU, no `var_dump` in commits.
- `database.md`: migrations with UP and DOWN, model or repository access only, prepared statements, the LIMIT and OFFSET cast, column allow-lists, indexing.
- `php-security.md`: `filter_var`, `htmlspecialchars`, `password_verify` and `password_hash`, `hash_equals`, JSON hex flags, `realpath` path containment, CRLF-safe headers, the SVG-upload ban, the dangerous-function list.

**How to use**

Download and drop the `.md` files into `.claude/rules/` alongside the generic pack. They load whenever you touch a `.php` file; `database.md` also loads on `.sql`. The generic `security-discipline` file states the principle; `php-security.md` names the call that satisfies it.

Want these tuned to your actual codebase? Run `/a-rules-optimizer` from the dev-workflow-forge plugin.
