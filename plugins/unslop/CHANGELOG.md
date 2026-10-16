# unslop changelog

## 1.5.0

All three tools are updated against 2026 research on what people now call AI-written, AI-coded and AI-designed.

- `a-unslop-text` separates evidence-backed patterns from style preferences, so it flags fewer harmless words. It also catches newer patterns: staged reveals ("The result:"), tacked-on significance ("highlighting the importance of"), leftover citation markup from chat tools, and "not just X, it's Y" in its variants. A new `--compare ORIGINAL REWRITE` mode lists the numbers, URLs, negations and modal verbs that a rewrite dropped or added.
- `a-unslop-code` checks diffs for weakened tests (`--diff` or `--diff-base REF`): removed assertions, newly skipped tests, `assert True`. It is much quieter on hand-written code: doc comments, ordinary names and `??` defaults no longer count.
- `a-unslop-ui` knows the newer defaults: the cream, serif and terracotta look, near-black with one acid accent, and template details such as all-caps eyebrows and arrow buttons. Commented-out CSS no longer counts.
- Every scanner ships clean and dirty test fixtures. Project scans skip `fixtures` folders; pass a fixture path directly to scan it.

## 1.4.3

The skills now call their scanners through `${CLAUDE_SKILL_DIR}`, so they run from your project directory instead of depending on the current working directory. The README opens with installation and requirements, uses full command names (`/unslop:a-unslop-text`), and explains the tools in plainer words.

## 1.4.2

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes.

## 1.4.1

`a-unslop-code` and `a-unslop-ui` now ship regression tests (`tests/`, run with `python3 -m unittest`) covering the false positives that were fixed and the true positives each fix had to keep. `a-unslop-ui` documents which directories its scanner skips and how to scan one of them anyway. `a-unslop-text` says when not to load it: tiny labels, routine code comments and one-line edits.

## 1.4.0

The text scanner and its reference catalog now carry the latest rules, exceptions, and structural review guidance.

## 1.3.1

The README now says which commands you get after installing.

## 1.3.0

The skills in this plugin now carry an `agents/openai.yaml` sidecar, so they show up in Codex's skill picker with a proper name and one-line description instead of a raw folder name. All three stay implicitly invocable, so Codex reaches for them while you write, the same as Claude Code does.

## Earlier

Versions before this predate this file. See the git history at https://github.com/imisic/claude-marketplace.
