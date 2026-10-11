# imisic marketplace

This repository contains six Claude Code plugins and five sets of coding rules. They help with code review, bug fixes, Git commits, checks before publishing, search visibility, and reviewing AI-generated writing and design. I adapted them from tools I use in my own projects so you can use them in yours. Longer write-ups live on [the toolshed at ivanmisic.net](https://ivanmisic.net/toolshed).

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install unslop@imisic
```

Swap `unslop` for any plugin name in the table below. `/plugin marketplace update imisic` pulls newer versions.

The skills use the [Agent Skills](https://agentskills.io) format and include Codex display metadata. The installation commands above are for Claude Code. Some workflows also use Claude-specific tools and paths.

### What you install, and what you then type

A plugin is the install unit and a skill is the tool, so the two are named for different jobs. Installing `search-visibility` gives you `/search-visibility:a-seo-gsc` and `/search-visibility:a-geo-optimizer`. A name without a slash is a skill the others read, not one you run. The full `/plugin:skill` form always identifies the installed plugin. The short form (`/a-seo-gsc`) also works when no other command has the same name, and it is the form you use for standalone skills copied into a personal skills directory.

| Install | Then run | Used internally |
|---|---|---|
| `unslop` | `/unslop:a-unslop-text` `/unslop:a-unslop-code` `/unslop:a-unslop-ui` | |
| `dev-workflow-forge` | `/dev-workflow-forge:a-review-optimizer` `/dev-workflow-forge:a-rules-optimizer` `/dev-workflow-forge:a-self-learner` | `a-review-core` |
| `dev-loop` | `/dev-loop:fix` `/dev-loop:commit` `/dev-loop:ship` | |
| `sanitize-public` | `/sanitize-public:sanitize-public` | |
| `search-visibility` | `/search-visibility:a-seo-gsc` `/search-visibility:a-geo-optimizer` | |
| `role-lenses` | `/role-lenses:role-architect` `/role-lenses:role-critic` `/role-lenses:role-design` `/role-lenses:role-ops` `/role-lenses:role-pm` `/role-lenses:role-security` `/role-lenses:role-staff` `/role-lenses:role-testing` | |

## What these are for

Four problems I kept hitting. Each one has a plugin.

### Your AI output reads like AI

You draft something with a model and it comes back sounding like a model. Same words, same rhythm, same stock look everyone else gets. Readers notice, and once they notice, they stop reading.

[**unslop**](plugins/unslop) is three scanners for that: one for prose, one for source, one for web UI. Each reports file, line, and fix, and exits non-zero on high-severity findings so a CI job can stop when it fails. The tools leave style choices to you: they flag the patterns that read as machine-written, and you choose changes that fit your own voice and project.

The tell catalogs come from [vibecoded-design-tells](https://github.com/JCarterJohnson/vibecoded-design-tells), a large study of what people actually name when they call something AI-written.

### A shared review skill does not know your codebase

Review instructions copied from another project can miss your architecture and conventions. A rules file copied from another project describes that project's folder structure, not yours.

[**dev-workflow-forge**](plugins/dev-workflow-forge) reads your codebase and writes code-review instructions and coding rules for it, then uses your review history to propose further improvements. The generated review skill stores your project's rules and exceptions. It reuses `a-review-core` for the review process, so that process can be updated in one place. [**dev-loop**](plugins/dev-loop) covers everyday work: `/fix`, `/commit`, `/ship`. It works across languages and frameworks and adds your project's conventions on top of a general baseline.

### You are one command away from publishing something private

The moment before a repo goes public is the moment nothing is checking. An internal hostname in a code comment, a `/home/you/...` path in an example, a client name in a fixture. You will not catch these by reading carefully, because you wrote them and they look normal to you. <!-- ship-allow: illustrative placeholder; this sentence names the patterns the scanner hunts -->


[**sanitize-public**](plugins/sanitize-public) scans the artifact that is about to ship, not the source tree it came from. A bundle and its source are rarely the same set of files, and the scan only counts on the one that leaves. It covers secrets, internal hosts, and private paths deterministically, then walks a manual checklist for the contextual leaks a regex cannot see. You can point it at your own private-terms file, which stays on your machine and is never read into the plugin.

### Search Console shows impressions and no clicks

Thousands of rows and no priority. Clicks are down, some pages are not indexed, a query sits at position 11, and none of that tells you which one is worth a Tuesday afternoon.

[**search-visibility**](plugins/search-visibility) is two skills working from opposite ends. `a-seo-gsc` starts from your own Search Console data, fetched over the API or read from a manual export, and ranks what to fix, with a Python pre-processor doing the arithmetic so the numbers are not a model's reading of a CSV. `a-geo-optimizer` starts from the page and checks whether an assistant can fetch it, parse it, and find a usable answer, then recommends the changes worth making. The scripts save exports and compute findings on your machine; the fetcher talks only to Google, Claude reads the findings in your session, and nothing goes to the plugin's author.

## And a second opinion, on demand

[**role-lenses**](plugins/role-lenses) is eight reviewer roles you start by name: architect, critic, design, ops, pm, security, staff, testing. Each role checks a specific part of your idea or change, explains the risks it finds and gives a recommendation. It uses checked evidence and labels assumptions.

```
/role-lenses:role-critic we should cache the whole graph in memory to save tokens
/role-lenses:role-ops this migration drops a column on the orders table
```

## Reference

| Plugin | What it is | Page |
|---|---|---|
| [unslop](plugins/unslop) | Three tools that flag repeated patterns in AI-generated writing, code and design, so you can make the work your own. | [toolshed](https://ivanmisic.net/toolshed/plugins/unslop) |
| [dev-workflow-forge](plugins/dev-workflow-forge) | Two generators that read your codebase and write a review skill and a rules set fitted to it, plus a learning loop that proposes updates from your review history. | [toolshed](https://ivanmisic.net/toolshed/plugins/dev-workflow-forge) |
| [dev-loop](plugins/dev-loop) | Three everyday commands that work across languages: `/fix`, `/commit`, `/ship`. Each stops before the next step when a check fails. | [toolshed](https://ivanmisic.net/toolshed/plugins/dev-loop) |
| [sanitize-public](plugins/sanitize-public) | Checks a repository, plugin or bundle for credentials and private details before you publish it, plus a short manual checklist for what text patterns cannot catch. | [toolshed](https://ivanmisic.net/toolshed/plugins/sanitize-public) |
| [search-visibility](plugins/search-visibility) | Rank what to fix from your Search Console data, over the API or from an export, and audit whether AI assistants can fetch, parse, and cite a page. | [toolshed](https://ivanmisic.net/toolshed/plugins/search-visibility) |
| [role-lenses](plugins/role-lenses) | Eight reviewer roles, started by name, that give a reasoned second opinion on an idea or change. | [toolshed](https://ivanmisic.net/toolshed/plugins/role-lenses) |

Invocation settings differ by skill. The plugin README states which skills you must start yourself and which Claude may select during related work.

## Rule packs

Not plugins. [rule-packs/](rule-packs/) are drop-in `.claude/rules/` files for five stacks (generic, PHP, Python, React and TypeScript, Flutter). Copy the rule files into your project, but not `STOREFRONT.md`, which is the website description. See [rule-packs/README.md](rule-packs/README.md) or the [toolshed rules shelf](https://ivanmisic.net/toolshed/rules).

They are a baseline, not a fit. For rules tuned to your actual conventions, install `dev-workflow-forge` and run `/dev-workflow-forge:a-rules-optimizer` on the repo.

## License

MIT. See [LICENSE](LICENSE).
