# role-lenses

role-lenses gives product managers, designers and developers eight reviewer roles for a second opinion from Claude. Ask one to examine an idea, a screen, a system design, a code change or a test suite, and it checks that one thing hard, says what it will not do, and ends with a clear call. Each runs only when you invoke it.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

Default assistant behavior drifts toward agreement. These lenses redirect that: each persona is defined by what it pushes on and what it hands off to another lens, so the output stays pointed.

## The eight lenses

| Command | Seat | Answers | Refuses |
|---|---|---|---|
| `/role-architect` | Principal architect | System shape, boundaries, build-vs-buy, what breaks at 10x | Picking frameworks, writing code, runtime recovery |
| `/role-critic` | Red-team reviewer | Where a plan breaks, the load-bearing assumptions, ranked failure modes | Being contrarian for sport, patching what it finds |
| `/role-design` | Design director | The user's job on the screen, information hierarchy, the states everyone forgets | Hex values and CSS before the flow is right |
| `/role-ops` | Principal SRE | Blast radius, failure modes, observability, the recovery path | Redesigning the system, picking the implementation |
| `/role-pm` | Product manager | Who it's for, the smallest slice that proves the bet, what not to build | Writing the design or the eng plan |
| `/role-security` | Security engineer | Trust boundaries, where authorization is enforced, secrets and data exposure | Theoretical risks with no path from attacker to impact |
| `/role-staff` | Staff engineer | The simplest thing that works, what to delete, the order to build it | Rubber-stamping, redesigning the whole system |
| `/role-testing` | Test reviewer | Whether the tests would fail if the feature broke, and the cheat that would still pass | Coverage for its own sake, invented requirements |

## How they compose

For a real decision they run as a pipeline, not in isolation:

`/role-pm` (worth doing?) → `/role-architect` (what shape?) → `/role-staff` (how to build?) → `/role-ops` (will it survive production?) → `/role-critic` (break whatever came out)

`/role-security` and `/role-testing` sit beside ops: run them on a concrete change before it ships. `/role-critic` is the terminal gate. The others generate a position; critic is the only one whose job is to attack one. You rarely need all eight for a given question. Reach for the one whose refusals match the decision in front of you.

## Usage

Each lens takes the thing you want examined as its argument. They run only when you invoke them, never on their own:

```
/role-critic we should cache the whole graph in memory to save tokens
/role-ops this migration drops a column on the orders table
/role-pm a browser extension that summarizes every page you visit
/role-security the new password-reset endpoint in src/auth/reset.py
```

Invoke with no argument and it works on the current conversation context.

## Privacy

The lenses are instructions only: they add no scripts and no network access of their own. When a lens reads code, fetches a source or runs your tests, it does so through Claude's normal tools in your session, with your usual permissions. The plugin collects and stores nothing, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install role-lenses@imisic
```

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/role-lenses](https://ivanmisic.net/toolshed/plugins/role-lenses).
