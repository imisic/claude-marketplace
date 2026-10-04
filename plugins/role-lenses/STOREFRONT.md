---
name: role lenses
tagline: Eight Claude Code lenses for reviewing architecture, product decisions, design, operations, security, tests and implementation.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install role-lenses@imisic
tags: developers, prompting, ai-assistants, claude-code
---

Eight lenses that put Claude Code in a specific senior seat. Each runs only when you invoke it. Each one is a lens with a point of view and a set of things it refuses to do, so you get a real second opinion instead of a model that agrees with whatever you just said.

Default assistant behavior drifts toward agreement. That is the problem these solve. Each persona is defined by what it pushes on and what it hands off to another lens, so the output stays pointed rather than polite.

## The eight lenses

| Command | Reach for it when | Won't do |
|---|---|---|
| `/role-architect` | you're deciding how to structure something and a wrong call is expensive to undo | pick your framework or write the code |
| `/role-critic` | you have a plan or a claim and want it attacked before you commit to it | nitpick, or fix what it breaks |
| `/role-design` | a screen or flow feels off and you're not sure what the user is actually there to do | argue about colors before the flow works |
| `/role-ops` | you're about to ship something risky and want to know what breaks at 3am | redesign the system or pick the code |
| `/role-pm` | you're unsure something is worth building, or the scope keeps creeping | write the design or the eng plan |
| `/role-security` | a change touches input, logins, permissions or secrets and you want the attacker's view before it ships | list theoretical risks with no path to real damage |
| `/role-staff` | you know roughly what to build and want the simplest sane way to do it | rubber-stamp, or redesign everything |
| `/role-testing` | the tests pass and you want to know whether they would still pass if the feature were broken | demand coverage for its own sake |

Full disclosure: `/role-ops` is the one I haven't reached for yet. My own ship pipeline runs the pre-release checks, so the seat hasn't come up. It's in the set because the seat matters, not because I owe it a habit.

## How they compose

Run them in sequence for a real decision: pm (worth doing?), architect (what shape?), staff (how to build?), ops (will it survive production?), then critic to attack whatever came out. You won't need the full sequence often, and that's fine. The habit worth building is smaller: whenever something complex lands, the kind of call you'd normally want a senior colleague to sanity-check, run the one lens that matches it and let it argue with you. Critic stays the final gate for the times you want a finished position attacked before you commit.

## Install

Add the marketplace once, then install the plugin:

```
/plugin marketplace add imisic/claude-marketplace
/plugin install role-lenses@imisic
```

Prefer to grab the raw files instead? Download the bundle and copy the `role-*` folders from `skills/` into `~/.claude/skills/`.
