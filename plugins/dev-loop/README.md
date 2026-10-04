# dev-loop

dev-loop gives developers three commands for the daily loop in Claude Code. `/fix` traces a bug through your code's layers, or applies a pasted review report by severity. `/commit` checks for secrets and unwanted files, then commits your selected changes with a Conventional Commits message. `/ship` runs your project's review skill, fixes what it finds and commits, pausing after the review for your go-ahead. None of them assumes a language or framework; each layers your project's own conventions on a general method.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

## Commands

| Command | Does |
|-|-|
| `/fix` | Debug a single bug by tracing it through your architecture's layers, or batch-apply a review report by severity |
| `/commit` | Pre-flight checks, sensitive-file gate, conventional commit message, files staged individually |
| `/ship` | Chains review, fix, and commit, pausing after the review for your go-ahead |

`fix` and `commit` need no setup. `ship` calls the project's review skill, so it pairs with `a-review-optimizer` (in the dev-workflow-forge plugin), which generates one tuned to your stack.

All three commit, deploy, or rewrite code, so all three wait for you to type them. Claude never decides on its own that a change looks ready to ship.

## Examples

- `/fix the login form returns 500 when the email has a plus sign`
- `/fix` followed by a pasted review report (batch mode: it reads the severity markers and file:line table and applies Critical first)
- `/ship --no-commit` (runs your review, fixes what it finds, and stops before committing so you can look)

## Privacy

Everything runs on your machine, inside the repository you are working in. The skills read your code and git state, edit files you approve, and run your project's own checks and git commands. `/commit` pushes only when you explicitly ask it to. The plugin itself collects nothing and sends nothing anywhere, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install dev-loop@imisic
```

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/dev-loop](https://ivanmisic.net/toolshed/plugins/dev-loop).
