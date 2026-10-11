---
name: dev-workflow-forge
tagline: Build review skills and project rules for your codebase, then use review history to propose improvements.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install dev-workflow-forge@imisic
tags: developers, claude-code, workflow
---

Review instructions copied from another project can miss your architecture and conventions, and a rules file copied from another project describes that project's folder structure, not yours.

This bundle reads your codebase and writes code-review instructions and coding rules for it, then uses your review history to propose further improvements.

**What you get**

- `/dev-workflow-forge:a-review-optimizer`: builds a code-review skill for your project, or improves the one you already have. Several review agents each check a different area, automated checks run before the review, and each finding includes its location, reason and proposed fix.
- `/dev-workflow-forge:a-rules-optimizer`: does the same for the coding rules in `.claude/rules/` and `CLAUDE.md`, checked against what the review skill catches, so the rules prevent what the review would otherwise flag.
- `/dev-workflow-forge:a-self-learner`: looks for findings your reviews keep repeating and proposes rule or automated-check updates. Nothing is written until you approve it.
- `a-review-core`: used internally. The generated review skill stores your project's rules and exceptions. It reuses `a-review-core` for the review process, so that process can be updated in one place.

You start the generators yourself. They write files in your project: a review skill, coding-rule files, and, after your approval, the self-learner's proposed changes.

Whole-tree reviews also read everything changed since the last review, line by line. This helps them catch new bugs that the existing checklists may miss.

Dismissed findings are recorded with the reason they were dismissed. That reason becomes an exception in the review skill, and a pattern dismissed again and again points to a check that needs narrowing. When a pattern keeps returning after a rule or check was added for it, `a-self-learner` treats the existing defense as failing and proposes enforcement rather than another rule.

The automated checks fail when one of them crashes, and an empty result counts as zero. `a-rules-optimizer` never recommends `alwaysApply`, a Cursor setting Claude Code ignores, and dates each rule file it audits so an outdated one is visible.

`a-review-optimizer` can also measure itself. It can plant a set of known defects on a scratch branch, run your review over them, and score what it caught against what it invented, which turns "the review feels better" into a recall and a precision number. It builds the defect set from your own review log, because the mistakes worth testing against are the ones your codebase actually keeps making, not a textbook's.

`a-self-learner` proposes an automated check as well as a rule whenever a script could catch the pattern outright. A rule asks a model to remember something. A check fails the build. Where both are possible, the check is what stops the pattern coming back.

**On a stack I have never touched.** The method works across languages and frameworks: the review areas are general, the review engine has nothing language-specific in it, and the generators read your codebase rather than assuming a framework. The worked detection examples do lean PHP, shell and Python, because that is what they were mined from. On Go, Rust, Ruby or C# you still get a review skill fitted to your code, with automated checks that rely more on your own linters and type checker than on borrowed text patterns.

How I run it: `a-review-optimizer` first on a new project, then `a-rules-optimizer`, then `a-self-learner` once review findings pile up. And it's not a one-time setup: every few weeks or monthly, depending on the project's pace, I re-run the generators, because the code evolves and the review skill and rules drift behind it. A re-run reads the codebase as it stands and pulls the tooling back in line. Everything the generators produce is yours and stays local: nothing about your stack, your conventions, or your codebase ships back anywhere.

For the day-to-day loop this tooling feeds, the `fix`, `commit`, and `ship` commands live in the companion [dev-loop](/toolshed/plugins/dev-loop) plugin.
