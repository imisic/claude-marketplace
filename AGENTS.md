<!-- CLAUDE-CODEX-BRIDGE START -->
## Codex Bridge to Claude Project Guidance

This repository keeps detailed project guidance in `CLAUDE.md` and
`.claude/`. Do not duplicate those files into a separate Codex tree;
treat them as the source of truth unless the user explicitly asks for a
conversion.

For every non-trivial coding, review, deploy, content, database, SEO, or
docs task:

1. Read `CLAUDE.md` before planning or editing.
2. Read any always-on rule files under `.claude/rules/` before code changes.
3. If this repo later adds `.claude/rules/`, read matching rules before editing.
4. Before flagging a documented exception, check project and skill references.
5. Use project preflight scripts when present and relevant.

Codex repo skills live under `.agents/skills`. They may be symlinks to
the matching `.claude/skills/*` directories so Claude and Codex share one
workflow definition.
<!-- CLAUDE-CODEX-BRIDGE END -->
