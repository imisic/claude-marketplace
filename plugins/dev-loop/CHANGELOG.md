# dev-loop changelog

## 1.3.1

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes. `/ship` is now described correctly: it pauses once, after the review, not before every step.

## 1.3.0

`/fix` now runs a sanity check on every file it changed in a batch before calling it fixed, applies answers the review report already recorded instead of asking again, and ends with open questions as short choices with a recommendation rather than a list you have to answer in free text.

`/ship` no longer asks its own round of questions at the end. Review and fix already asked theirs, so it carries those answers into the final report and only asks when the commit step turns up something new.

## 1.2.0

The skills in this plugin now carry an `agents/openai.yaml` sidecar, so they show up in Codex's skill picker with a proper name and one-line description instead of a raw folder name. All three are explicit-only in Codex as well, matching `disable-model-invocation` on the Claude Code side.

## 1.1.0

`fix`, `commit`, and `ship` are now yours to invoke only. Each one commits, deploys, or rewrites code, and none of that should start because a model judged the moment right. Their descriptions are one line each, written to be read off the slash-command menu rather than to trigger anything.

## Earlier

1.0.0 and before predate this file. See the git history at https://github.com/imisic/claude-marketplace.
