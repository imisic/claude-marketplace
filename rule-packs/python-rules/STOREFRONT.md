---
name: python-rules
tagline: Claude Code rules for Python 3.10+, covering types, logging, subprocesses and security. Use alongside the generic rules pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/python-rules
tags: developers, security, claude-code, rules
---

The Python layer that sits on top of the generic pack. Broad `paths:` globs (`**/*.py`), so it works whatever your layout is.

**What's inside**

- `python-standards.md`: modern type hints (`X | None`, lowercase generics), naming, module-level logging with no `print()`, specific-exception handling, no mutable defaults, no `import *`, linting.
- `python-security.md`: subprocess safety (no `shell=True`, list args, `timeout=`), `yaml.safe_load` and the no-`pickle`/no-`eval` deserialization rules, SSRF validation on outbound requests with a post-redirect re-check, ReDoS-safe regex on untrusted input, secrets via `os.getenv`, tar-extraction and temp-file safety.

**How to use**

Download and drop the `.md` files into `.claude/rules/` alongside the generic pack. They load whenever you touch a `.py` file. The security file is drawn from scraper and data-pipeline projects, so it leans on the network and deserialization surfaces those hit hardest.

Want these tuned to your actual codebase? Run `/a-rules-optimizer` from the dev-workflow-forge plugin.
