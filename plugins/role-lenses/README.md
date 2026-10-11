# role-lenses

role-lenses gives product managers, designers and developers eight reviewer roles for a second opinion from Claude. Ask one to examine an idea, a screen, a system design, a code change or a test suite, and it checks that part of your idea or change, explains the risks it finds and gives a recommendation. Each runs only when you invoke it.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install role-lenses@imisic
```

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/role-lenses](https://ivanmisic.net/toolshed/plugins/role-lenses).

Each role checks a specific part of your idea or change, explains the risks it finds and gives a recommendation. It uses checked evidence and labels assumptions, and it hands off what belongs to another role.

## The eight roles

| Command | Seat | Answers | Refuses |
|---|---|---|---|
| `/role-lenses:role-architect` | Principal architect | System shape, boundaries, build-vs-buy, what breaks at 10x, framework choice when the stack is undecided | Replacing a stack that already fits, writing code, runtime recovery |
| `/role-lenses:role-critic` | Red-team reviewer | Where a plan breaks, the load-bearing assumptions, ranked failure modes | Being contrarian for sport, patching what it finds |
| `/role-lenses:role-design` | Design director | The user's job on the screen, information hierarchy, the states everyone forgets | Hex values and CSS before the flow is right |
| `/role-lenses:role-ops` | Principal SRE | Blast radius, failure modes, observability, the recovery path | Redesigning the system, picking the implementation |
| `/role-lenses:role-pm` | Product manager | Who it's for, the smallest slice that proves the bet, what not to build | Writing the design or the implementation plan |
| `/role-lenses:role-security` | Security engineer | Trust boundaries, where authorization is enforced, secrets and data exposure | Theoretical risks with no path from attacker to impact |
| `/role-lenses:role-staff` | Staff engineer | The simplest thing that works, what to delete, the order to build it | Rubber-stamping, redesigning the whole system |
| `/role-lenses:role-testing` | Test reviewer | Whether the tests would fail if the feature broke, and the cheat that would still pass | Coverage for its own sake, invented requirements |

## How they compose

For a complex decision, you can run several roles in sequence:

`/role-lenses:role-pm` (worth doing?) → `/role-lenses:role-architect` (what shape?) → `/role-lenses:role-staff` (how to build?) → `/role-lenses:role-ops` (will it survive production?) → `/role-lenses:role-critic` (test the result)

`/role-lenses:role-security` and `/role-lenses:role-testing` sit beside ops: run them on a concrete change before it ships. `/role-lenses:role-critic` is the final review: the others form a position, and critic tests it. You rarely need all eight for a given question. Pick the role that matches the decision in front of you.

## Usage

Each role takes the thing you want examined as its argument. They run only when you invoke them, never on their own:

```
/role-lenses:role-critic we should cache the whole graph in memory to save tokens
/role-lenses:role-ops this migration drops a column on the orders table
/role-lenses:role-pm a browser extension that summarizes every page you visit
/role-lenses:role-security the new password-reset endpoint in src/auth/reset.py
```

Invoke with no argument and it works on the current conversation context.

## Privacy

The roles are instructions only: they add no scripts and no network access of their own. When a role reads code, fetches a source or runs your tests, it does so through Claude's normal tools in your session, with your usual permissions. The plugin collects and stores nothing, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.
