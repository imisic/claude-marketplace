# unslop changelog

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
