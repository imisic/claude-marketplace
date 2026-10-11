# dev-workflow-forge

dev-workflow-forge helps developers set up code review and coding rules for their own repository in Claude Code. `a-review-optimizer` reads your codebase and writes, or improves, a review skill fitted to it; `a-rules-optimizer` does the same for your `.claude/rules/` files and `CLAUDE.md`; and `a-self-learner` reads what your reviews keep finding and proposes rule and check updates for your approval. All three sit on one shared review engine, `a-review-core`.

Review instructions copied from another project can miss your architecture and conventions. The generators in this bundle read your codebase and produce a review skill, coding rules, and a learning step that fit it.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install dev-workflow-forge@imisic
```

Then the commands are `/dev-workflow-forge:a-review-optimizer`, `/dev-workflow-forge:a-rules-optimizer` and `/dev-workflow-forge:a-self-learner`.

Needs Python 3 and bash for the bundled scripts, and Node with npm only for the optional rule-glob verifier. Output is files in your project: a review skill, `.claude/rules/` files, or proposed changes for your approval.

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/dev-workflow-forge](https://ivanmisic.net/toolshed/plugins/dev-workflow-forge).

## What's in it

| Skill | Produces |
|-|-|
| `a-review-optimizer` | A project-specific `*-review` skill: several review agents that each check a different area, automated checks run before the review, findings that include location, reason and proposed fix, and `--debt`/`--full` modes where useful |
| `a-rules-optimizer` | `.claude/rules/*.md` and a `CLAUDE.md` reference table, scoped to your directory layout and cross-checked against the review skill's checks |
| `a-self-learner` | Mines `.claude/reviews/review-issues.jsonl` for recurring findings and proposes rule or automated-check updates; nothing is written until you approve it |
| `a-review-core` | Used internally. The generated review skill stores your project's rules and exceptions and reuses `a-review-core` for the review process, so that process can be updated in one place |

Each one is surgical: it preserves what already works in an existing skill or rule file and only changes what a concrete gap, false positive, or drift justifies. Run `a-review-optimizer` first on a new project; `a-rules-optimizer` and `a-self-learner` are more useful once a review skill exists to cross-reference.

## Use

```
/dev-workflow-forge:a-review-optimizer     # build or improve this project's review skill
/dev-workflow-forge:a-rules-optimizer      # audit or create .claude/rules/
/dev-workflow-forge:a-self-learner         # propose updates from accumulated review history
#  a-review-core is the shared engine, read by the skills you generate, not run on its own
```

All three rewrite files you have to live with afterwards, so all three are yours to start. Claude will not reach for them on its own.

`a-rules-optimizer` includes a glob verifier that uses a pinned local `minimatch` dependency. After installing or updating this plugin, run `npm ci --prefix <plugin folder>/skills/a-rules-optimizer/scripts` once before using the verifier. The plugin folder is `~/.claude/plugins/cache/imisic/dev-workflow-forge/<version>` for a Claude Code install, or `plugins/dev-workflow-forge` in a clone of this repo. It installs beside the skill, not globally.

## What this assumes about your stack

The method works across languages and frameworks. The review areas the generators work from are general (injection, authorization, resource cleanup, error handling), the review engine in `a-review-core` has nothing language-specific in it, and the generators read the codebase actually in front of them rather than pattern-matching a framework they already know.

What is not evenly spread is the **example** library. `references/pattern-detection.md` is a set of worked detection scripts, and its examples lean PHP, shell and Python because that is what they were mined from. On a Go, Rust, Ruby, C# or Kotlin project you still get a review skill fitted to your code; you get fewer ready-made detectors to start from, so the automated checks the generator writes rely more on your own linters and type checker and less on borrowed text patterns. That is the right default anyway: a real linter beats an approximated regex.

The benchmark harness is the one place this bites. It ships a corpus of PHP and Python defects, so `--stack go` has nothing to plant until you build your own with `scripts/seed-defects.py --build-corpus`, which mines your project's own review log. That needs review history to exist first, so on a new project the benchmark is something you grow into rather than run on day one.

## The day-to-day loop

The generators produce the tooling; the everyday `fix`, `commit`, and `ship` commands that run on top of it live in the companion **dev-loop** plugin. Install both if you want the full pipeline.

## Examples

- `/dev-workflow-forge:a-review-optimizer build a review skill for this repository.`
- `/dev-workflow-forge:a-rules-optimizer audit .claude/rules and CLAUDE.md against what the code actually does.`
- `/dev-workflow-forge:a-self-learner look at our review history and propose rule or check updates for what keeps recurring.`

## Privacy

Everything runs on your machine, inside the repository you point it at. The generators read your code and write skills and rule files into your project; the review loop appends findings to `.claude/reviews/` in that same repository. The plugin itself collects nothing and sends nothing anywhere, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.
