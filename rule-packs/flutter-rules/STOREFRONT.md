---
name: flutter-rules
tagline: Claude Code rules for Flutter and Dart, covering state and navigation with Riverpod and GoRouter examples. Use alongside the generic pack.
kind: rules
repo_url: https://github.com/imisic/claude-marketplace/tree/main/rule-packs/flutter-rules
tags: developers, claude-code, rules
---

The Flutter and Dart layer that sits on top of the generic pack. Drawn from a production Flutter app on Riverpod and GoRouter, generalized so the discipline holds even if your packages differ.

**What's inside**

- `dart-standards.md`: null-safety discipline, naming, `const`/`final` idioms, async and subscription cleanup, collection and import order, docs and lint.
- `state-management.md`: logic out of widgets, the repository pattern, reading state correctly (`read` vs `watch` vs `listen`), the data/loading/error branch, and testing via overrides. Riverpod examples, portable principles.
- `navigation.md`: route constants over hardcoded strings, push-vs-switch, sheet-vs-full-screen, redirect-based auth guards, and treating deep-link parameters as untrusted input.

**How to use**

Download and drop the `.md` files into `.claude/rules/` alongside the generic pack. They load whenever you touch a `.dart` file. If you use Bloc or a different router, keep the principles and adjust the package-specific examples.

Want these tuned to your actual codebase? Run `/a-rules-optimizer` from the dev-workflow-forge plugin.
