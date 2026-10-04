---
name: dev-workflow-forge
tagline: Build review skills and project rules for your codebase, then use review history to propose improvements.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install dev-workflow-forge@imisic
tags: developers, claude-code, workflow
---

Most shared review skills are written for one stack and one set of conventions, then passed around as if they generalize. They don't. A review skill tuned to a PHP MVC app has no idea what a Rust CLI's architecture looks like, and a rules file copied from another project encodes that project's directory layout, not yours.

This bundle ships the generator instead of the output. Point it at your repo and it reads the actual stack, architecture, and conventions in front of it, then writes tooling that fits.

**What you get**

- `/a-review-optimizer`: builds a project-specific review skill from scratch, or surgically improves one you already have. Parallel agents with non-overlapping scopes, a deterministic preflight script, and fix-readiness output on every finding.
- `/a-rules-optimizer`: does the same for `.claude/rules/`, cross-checked against what the review skill catches so your rules prevent what review would otherwise flag.
- `/a-self-learner`: mines accumulated review findings for recurring patterns and proposes rule or preflight updates, always behind an explicit approval gate before anything is written.
- `a-review-core`: the shared review engine the generated skill reads while it runs. You never invoke this one; it is what keeps what you generate an overlay rather than a private copy of the mechanics.

**New in 1.6.0**

Dismissed findings are now recorded with the reason they were dismissed, instead of being dropped. That reason is what a whitelist entry gets built from, and a pattern dismissed again and again is a check that needs narrowing. `a-self-learner` also reads fixes and defenses off the same log now, so when a pattern keeps turning up after a rule or check was put in place for it, it treats that as the defense failing and proposes enforcement, not another rule.

Generated preflight scripts no longer pass when a probe crashes, and an empty result counts as zero instead of breaking the comparison that follows it. `a-rules-optimizer` stops recommending `alwaysApply`, a Cursor marker Claude Code ignores, and dates each rule file it audits so a stale one is visible.

**Why the engine is shared**

The review skill this kit writes for you used to be a standalone thing: your project's context and a full copy of the review mechanics, welded together. That copy is the problem. Improve how findings get verified, or how the report is shaped, and the improvement reaches whichever generated skills someone remembered to regenerate. The rest keep running, silently a version behind, and nothing tells you which is which.

So the mechanics now live in one place, `a-review-core`, and what you generate reads it at runtime. Your project's dimensions, whitelist, preflight and thresholds stay yours. The engine underneath them stops being your copy to maintain.

`a-review-optimizer` also learned to measure itself. It can plant a set of known defects on a scratch branch, run your review over them, and score what it caught against what it invented, which turns "the review feels better" into a recall and a precision number. It builds the defect set from your own review log, because the mistakes worth testing against are the ones your codebase actually keeps making, not a textbook's.

And `a-self-learner` now proposes a check as well as a rule whenever a script could catch the pattern outright. A rule asks a model to remember something. A check fails the build. Where both are possible, the second one is what actually stops the pattern coming back.

**On a stack I have never touched.** The method is language-neutral: the dimensions are conceptual, the review engine has nothing language-specific in it, and the generators read your codebase rather than assuming a framework. The worked detection examples do lean PHP, shell and Python, because that is what they were mined from. On Go, Rust, Ruby or C# you still get a review skill fitted to your code, with a preflight that leans harder on your own linters and type checker than on borrowed grep patterns, which is the better default regardless.

How I run it: `a-review-optimizer` first on a new project, then `a-rules-optimizer`, then `a-self-learner` once review findings pile up. And it's not a one-time setup: every few weeks or monthly, depending on the project's pace, I re-run the generators, because the code evolves and the review skill and rules drift behind it. A re-run reads the codebase as it stands and pulls the tooling back in line. Everything the generators produce is yours and stays local: nothing about your stack, your conventions, or your codebase ships back anywhere.

For the day-to-day loop this tooling feeds, the `fix`, `commit`, and `ship` commands live in the companion [dev-loop](/toolshed/plugins/dev-loop) plugin.
