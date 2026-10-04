# role-lenses changelog

## 1.1.1

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes.

## 1.1.0

Two new lenses. `/role-security` looks for the path from untrusted input to damage: trust boundaries, where authorization is actually enforced, secrets, and data leaving the system. `/role-testing` asks whether the tests would fail if the feature broke, and which lazy implementation would still pass them.

The lenses are now skills that run only when you invoke them, so they also work in Codex and in claude.ai, where they will not apply themselves to an ordinary conversation. You still type `/role-pm` and the rest exactly as before.

Every lens now grounds its claims in what it checked, reading the code or the source before judging, and labels anything it could not verify as speculation.

## Earlier

1.0.0 shipped the six original lenses as slash commands. See the git history at https://github.com/imisic/claude-marketplace.
