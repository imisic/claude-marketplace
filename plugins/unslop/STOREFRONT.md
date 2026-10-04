---
name: unslop
tagline: Three Claude Code skills for reviewing AI-generated writing, code and website design, with scanners and manual checks.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install unslop@imisic
tags: product-managers, developers, claude-code, standards, writing
---

Use AI to draft something and it comes out sounding like AI: the same words, the same rhythm, the same stock look everyone else gets. That default is the problem. unslop is three tools that catch it, one for writing, one for code, one for UI. Each ships the same shape: an auto-trigger, a Build mode that specifies your way out of the median before you generate anything, an Audit mode with a deterministic scanner plus a human pass for what a regex can't see, and an `unslop-ignore` escape hatch for a tell you chose on purpose.

None of the three hands you a house style. They remove the cues that make something read machine-written, and where that default exists only because nobody chose otherwise, they force a real decision instead. The choice itself, your voice, your conventions, your brand, stays yours.

**What you get**

- [a-unslop-text](/toolshed/skills/a-unslop-text) for reader-facing prose: docs, posts, commit bodies, emails.
- [a-unslop-code](/toolshed/skills/a-unslop-code) for source that reads tutorial-shaped or machine-written.
- [a-unslop-ui](/toolshed/skills/a-unslop-ui) for web UI stuck on a stock default look.

Each linked page carries the full case for its skill: what it catches, what it deliberately refuses to do, and the trap it watches for that the obvious fix walks into.

Every scanner reports file, line, and fix, plus a severity-weighted score, and exits non-zero on high-severity findings so it can gate a CI job. All three tell catalogs and scanner designs are adapted from the [vibecoded-design-tells](https://github.com/JCarterJohnson/vibecoded-design-tells) research (MIT), a large-scale study of what people actually name when they call something AI-written, AI-coded, or AI-designed.
