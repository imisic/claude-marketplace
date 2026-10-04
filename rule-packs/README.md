# rule-packs

Public, generalized versions of the `.claude/rules/` I use across my own projects. Unlike the plugins in this marketplace, these are **not** installable with `/plugin install`: a Claude Code plugin can't write files into your project. Rules are copy-in.

## Use

Pick a pack, copy its `.md` files into your project's `.claude/rules/`. Start with `generic-rules` (stack-agnostic) and layer a language pack on top:

| Pack | Layer | Loads |
|-|-|-|
| `generic-rules` | any stack | security, code-quality, architecture always on; CSS on `*.css`/`*.scss` |
| `php-rules` | PHP 8.2+ | on `*.php` and `*.sql` |
| `python-rules` | Python 3.10+ | on `*.py` |
| `react-ts-rules` | React + TypeScript | on `*.ts` and `*.tsx` |
| `flutter-rules` | Flutter / Dart | on `*.dart` |

A rule file with no `paths:` front matter loads every turn; one with `paths:` globs loads only when you touch a matching file. Adjust the globs to your layout if needed.

## These are a starting point

They carry the discipline, not any one project's specifics: no real table names, tokens, or paths. To get rules tuned to your actual codebase, install the `dev-workflow-forge` plugin and run `/a-rules-optimizer`. It reads your repo and rewrites the rules around your real conventions. These packs are what a good generic baseline looks like; the optimizer makes it yours.

Also on the storefront: [ivanmisic.net/toolshed](https://ivanmisic.net/toolshed).
