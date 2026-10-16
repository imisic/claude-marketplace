---
name: unslop
tagline: Three Claude Code skills for reviewing AI-generated writing, code and website design, with scanners and manual checks.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install unslop@imisic
tags: product-managers, developers, claude-code, standards, writing
---

Use AI to draft something and it often comes out sounding like AI: the same words, the same rhythm, the same stock look everyone else gets. unslop is three tools that flag those repeated patterns, one for writing, one for code, one for web design. Each works in two ways. While you draft, it helps you set your own direction before anything is generated. When you review, a scanner checks configured patterns and a manual review covers meaning, structure and layout. Claude can start each tool during related work, or you can run it by name, and you can mark a pattern you chose on purpose with `unslop-ignore` so the scanner skips it.

The tools leave style choices to you. They flag the patterns, and you choose changes that fit your own voice, conventions and brand.

**What you get**

- [a-unslop-text](/toolshed/skills/a-unslop-text) for reader-facing prose: docs, posts, commit bodies, emails.
- [a-unslop-code](/toolshed/skills/a-unslop-code) for source that reads tutorial-shaped or machine-written.
- [a-unslop-ui](/toolshed/skills/a-unslop-ui) for web UI stuck on a stock default look.

Each linked page carries the full case for its skill: what it catches, what it deliberately refuses to do, and the trap it watches for that the obvious fix walks into.

Version 1.5.0 updates all three against 2026 research. The writing tool can compare a rewrite with the original and list any number, URL, negation or modal verb that went missing or appeared (`--compare`), the code tool flags diffs that weaken tests, and the design tool knows the newer stock looks, not just the old purple gradients.

Every scanner reports file, line, and fix, plus a severity-weighted score, and exits non-zero on high-severity findings so a CI job can stop when it fails. All three tell catalogs and scanner designs are adapted from the [vibecoded-design-tells](https://github.com/JCarterJohnson/vibecoded-design-tells) research (MIT), a large-scale study of what people actually name when they call something AI-written, AI-coded, or AI-designed.
