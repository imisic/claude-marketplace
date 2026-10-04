# dev-workflow-forge changelog

## 1.6.1

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes.

## 1.6.0

`--dismissed "<reason>"` now works. `a-review-core` told review skills to capture dismissals with it, but the capture helper that shipped did not accept the flag. The helper is now the full schema-2 version: dismissals with their reason, resolution rows (`--action fixed|dismissed|covered|wont-fix`, `--resolves <finding_id>`), and a warning when a category slug is missing from the project's slug table. If a project already has `.claude/scripts/capture-finding.sh` from an earlier version, copy the new one over it and run `scripts/migrate-review-log-v2.py` on its log. `a-review-optimizer` now tells you to copy that file rather than emitting its own older copy.

`a-self-learner` counts confirmed findings only, falls back sensibly on older logs, proposes a check and a rule together when a script can catch the pattern, and treats a pattern that returns after a defense was added as that defense failing. It also tells a rule that never loaded apart from one that loaded and was ignored, since they need opposite fixes.

The preflight template no longer silences a crashing probe, reads non-UTF-8 files instead of dying on them, matches `timeout=` as an argument rather than any mention of the word, and counts an empty result as one zero instead of two.

`a-rules-optimizer` stops recommending `alwaysApply`, which Claude Code does not read, warns that removing an `@import` can silently stop a prohibition from loading, checks the rule list an `AGENTS.md` gives other agents, and stamps each audited rule file with its audit date.

`a-review-core` gives the verifier seat a smaller model, keeps each seat's configuration identical so its agents share a prompt cache, and points at the setting that keeps that cache warm across a long run.


## 1.5.0

The review skill this kit generates is now an overlay on a shared engine rather than a standalone copy of one. `a-review-core` ships alongside the generators and holds the mechanics every review has in common: scope resolution, the preflight protocol, dispatch, verify calibration, the finding contract, the report shape, reconciliation and capture. A generated skill reads it at runtime and supplies only what is true for its own project.

The reason is drift. When the engine is copied into each generated skill, a fix reaches whichever copy someone remembered to update, and the rest quietly fall behind the one they came from. Nothing tells you this has happened, because every copy still runs.

`a-review-optimizer` also gains a benchmark harness. `scripts/seed-defects.py` plants known defects on a scratch branch, runs the review over them, and scores what it caught against what it invented, so "the review got better" can be a recall and precision number instead of an impression. `--build-corpus` mines a project's own review log into a starter corpus, since the defects worth seeding are the ones that codebase actually keeps producing.

`--stack` on the benchmark harness is no longer a closed php-or-python list. `--build-corpus` invites you to name your own stack, and the harness then rejected the corpus it had just told you to build, so anything outside those two languages hit a dead end. It now validates against the corpus you hand it and names what is actually in there.

`a-self-learner` now proposes a deterministic check alongside a rule wherever a script could catch the pattern outright, on the grounds that prose asking a model to remember something is weaker than a command that fails.

## 1.4.0

The generators now include the latest review, rules, and self-learning guardrails. The glob verifier carries a pinned local dependency instead of relying on a global npm install.

## 1.3.1

The README now says which commands you get after installing.

## 1.3.0

The skills in this plugin now carry an `agents/openai.yaml` sidecar, so they show up in Codex's skill picker with a proper name and one-line description instead of a raw folder name. All three are explicit-only in Codex as well, matching `disable-model-invocation` on the Claude Code side.

## 1.2.0

All three generators are now yours to invoke only. Each one writes files you then have to live with (a review skill, a rules set, proposed rule updates), so none of them should start on a model's judgement. Their descriptions are one line each instead of the 88 to 97-word trigger paragraphs they carried, which were only ever there to make auto-invocation fire.

## Earlier

1.1.0 and before predate this file. See the git history at https://github.com/imisic/claude-marketplace.
