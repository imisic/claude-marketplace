---
name: dev-loop
tagline: Fix bugs, review changes and prepare commits with Claude Code commands that use your project conventions.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install dev-loop@imisic
tags: developers, claude-code, workflow
---

Three commands for work every project does regularly: fix a bug, commit the change, ship the batch. They work across languages and frameworks, so they behave the same on a Rust CLI as on a PHP app, and they add your project's own sensitive paths and conventions on top of a general baseline.

**What you get**

- `/dev-loop:fix`: debug one bug by tracing it through your architecture's layers, or point it at a review report and it applies the findings in severity order.
- `/dev-loop:commit`: checks before committing, a sensitive-file check that stops secrets before they are staged, a conventional-commit message drafted from the actual diff, and files staged individually so nothing rides along by accident.
- `/dev-loop:ship`: runs review, then fix, then commit in one flow, pausing after the review so nothing is fixed or committed until you have seen what was found.

`fix` and `commit` stand on their own: install this plugin and they work as-is. `ship` needs a review skill in your project to call. You get one by running [`a-review-optimizer`](/toolshed/plugins/dev-workflow-forge) from the companion dev-workflow-forge plugin. So the order is: install both, run `a-review-optimizer` once against your repo, and the full review, fix, commit pipeline is live.
