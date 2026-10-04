---
name: dev-loop
tagline: Fix bugs, review changes and prepare commits with Claude Code commands that use your project conventions.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install dev-loop@imisic
tags: developers, claude-code, workflow
---

Three commands for the loop every project runs a hundred times a week: find the bug, commit the change, ship the batch. They carry no stack-specific knowledge, so they behave the same on a Rust CLI as on a PHP app, and they layer your project's own sensitive paths and conventions on top of a generic baseline.

**What you get**

- `/fix`: debug one bug by tracing it through your architecture's layers, or point it at a review report and it applies the findings in severity order.
- `/commit`: pre-flight checks, a sensitive-file gate that stops secrets before they stage, a conventional-commit message drafted from the actual diff, and files staged individually so nothing rides along by accident.
- `/ship`: runs review, then fix, then commit in one flow, pausing after the review so nothing is fixed or committed until you have seen what was found.

`fix` and `commit` stand on their own: install this plugin and they work as-is. `ship` earns its keep once your project has a review skill for it to call, and you get one by running [`a-review-optimizer`](/toolshed/plugins/dev-workflow-forge) from the companion dev-workflow-forge plugin. So the order is: install both, run `a-review-optimizer` once against your repo, and the full review, fix, commit pipeline is live.
