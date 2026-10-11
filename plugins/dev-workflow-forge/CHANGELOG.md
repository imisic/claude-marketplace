# dev-workflow-forge changelog

## 1.7.0

Whole-tree reviews now also read everything changed since the last review, line by line. Checklists only find patterns that have already shipped, so new bug shapes in recent changes were slipping through.

Three cleanup angles join the review (Reuse, Simplification, and Altitude, which asks whether a change fixes the root cause or patches a symptom), so findings whose cost is maintenance rather than a bug have a finder.

Cross-file checks now compare each function's thrown exceptions with every caller's error handling, and check that sibling handlers treat the same failure the same way. The line scan carries a language-neutral pitfall list, including timestamps compared as text and input compared without normalising BOM or whitespace.

Finders pass every candidate with a concrete failure scenario to verification instead of quietly dropping the ones they half believe; the full finding format applies only to what survives verification. Reports gain a Coverage line (files and bytes of diff read versus total), so an empty result over a large range cannot read as a clean one.

Default scope when the tree is clean is now everything since the last review, derived from the newest date in `.claude/reviews/review-issues.jsonl`; with no log, the last 24 hours. Commits that land between reviews, including the fix for a reported finding, are no longer invisible.

Each review agent now has a fixed reasoning effort as well as a model: finders run at `high`, verifiers at `medium`, so a review thinks as hard on a quiet afternoon as on a busy one. Verification is batched by file (about five candidates per verifier) with an explicit instruction to judge each candidate on its own evidence, which cuts the verify stage several times over on agents and time.

`a-review-core` gains `scripts/review-scope.sh`, which resolves the review scope (explicit base, working tree, since the last review, or the last 24 hours) and the totals for the Coverage line. Every generated review skill calls it instead of carrying its own shell arithmetic, so two projects never disagree about what "since the last review" means.

`review_loop_health.py --repo <name> --clusters --json` prints the qualifying clusters it counted, and `a-self-learner` now starts every run from the health verdict and that cluster list instead of re-grouping the log by hand. Its proposal template adds a third route: findings whose fix is code work rather than a rule or a check go to the project's task tracker, and the ledger records which task.

`a-review-optimizer` generates `--full` flags that keep the diff angles, and points its verify prompt at the core's two depth-matched prompts. `a-rules-optimizer` states its Claude Code version measurements as floors rather than pins.

`a-rules-optimizer`'s rule style guide no longer recommends `alwaysApply: true`. The always-on form is a rule with no `paths:` field; the key it used to prescribe is read only by the Cursor importer and contradicted the skill's own instructions.

Generated review skills now locate `a-review-core` themselves (newest installed plugin first, then a standalone copy) and pass that directory to every core command, because the core is read as a file and skill path substitution does not apply to it. Skills that run their own scripts call them through `${CLAUDE_SKILL_DIR}`, quoted, so they work from your project directory. The scope rule in `a-review-core` keeps its incident history in `references/scope-history.md`.

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
