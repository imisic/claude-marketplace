# imisic marketplace

Six Claude Code plugins and five rule packs. I built all of them for my own work, then genericized them so they carry the discipline without carrying my project's directory layout. Longer write-ups live on [the toolshed at ivanmisic.net](https://ivanmisic.net/toolshed).

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install unslop@imisic
```

Swap `unslop` for any plugin name in the table below. `/plugin marketplace update imisic` pulls newer versions.

The skills follow the [Agent Skills](https://agentskills.io) open format and carry Codex picker metadata, so they work in Codex and the other agents that read the standard, not only in Claude Code.

### What you install, and what you then type

A plugin is the install unit and a skill is the tool, so the two are named for different jobs. Installing `search-visibility` gives you `/search-visibility:a-seo-gsc` and `/search-visibility:a-geo-optimizer`. A name without a slash is a skill the others read, not one you run.

| Install | Then run |
|---|---|
| `unslop` | `/a-unslop-text` `/a-unslop-code` `/a-unslop-ui` |
| `dev-workflow-forge` | `/a-review-optimizer` `/a-rules-optimizer` `/a-self-learner` `a-review-core` |
| `dev-loop` | `/fix` `/commit` `/ship` |
| `sanitize-public` | `/sanitize-public` |
| `search-visibility` | `/search-visibility:a-seo-gsc` `/search-visibility:a-geo-optimizer` |
| `role-lenses` | `/role-architect` `/role-critic` `/role-design` `/role-ops` `/role-pm` `/role-security` `/role-staff` `/role-testing` |

## What these are for

Four problems I kept hitting. Each one has a plugin.

### Your AI output reads like AI

You draft something with a model and it comes back sounding like a model. Same words, same rhythm, same stock look everyone else gets. Readers notice, and once they notice, they stop reading.

[**unslop**](plugins/unslop) is three scanners for that: one for prose, one for source, one for web UI. Each reports file, line, and fix, and exits non-zero on high-severity findings so it can gate a CI job. None of them hands you a house style. They strip the cues that read as machine-written and then ask you to make an actual choice, because a default is the one thing you can never give a reason for.

The tell catalogs come from [vibecoded-design-tells](https://github.com/JCarterJohnson/vibecoded-design-tells), a large study of what people actually name when they call something AI-written.

### A shared review skill does not know your codebase

Most review tooling gets passed around as if it generalizes. It does not. A review skill tuned to a PHP MVC app has nothing useful to say about a Rust CLI, and a rules file copied from another project encodes that project's folder structure, not yours.

[**dev-workflow-forge**](plugins/dev-workflow-forge) shares the generator instead of the output. Three skills read the codebase actually in front of them and write a review skill, a rules set, and a learning loop fitted to it, on top of `a-review-core`, one shared review engine. [**dev-loop**](plugins/dev-loop) is the everyday half: `/fix`, `/commit`, `/ship`, stack-neutral, layering your project's conventions over a generic baseline.

### You are one command away from publishing something private

The moment before a repo goes public is the moment nothing is checking. An internal hostname in a code comment, a `/home/you/...` path in an example, a client name in a fixture. You will not catch these by reading carefully, because you wrote them and they look normal to you. <!-- ship-allow: illustrative placeholder; this sentence names the patterns the scanner hunts -->


[**sanitize-public**](plugins/sanitize-public) scans the artifact that is about to ship, not the source tree it came from. A bundle and its source are rarely the same set of files, and the scan only counts on the one that leaves. It covers secrets, internal hosts, and private paths deterministically, then walks a manual checklist for the contextual leaks a regex cannot see. You can point it at your own private-terms file, which stays on your machine and is never read into the plugin.

### Search Console shows impressions and no clicks

Thousands of rows and no priority. Clicks are down, some pages are not indexed, a query sits at position 11, and none of that tells you which one is worth a Tuesday afternoon.

[**search-visibility**](plugins/search-visibility) is two skills working from opposite ends. `a-seo-gsc` starts from your own Search Console data, fetched over the API or read from a manual export, and ranks what to fix, with a Python pre-processor doing the arithmetic so the numbers are not a model's reading of a CSV. `a-geo-optimizer` starts from the page and checks whether an assistant can fetch it, parse it, and find a usable answer, then recommends the changes worth making. Your data never leaves your machine.

## And a second opinion, on demand

[**role-lenses**](plugins/role-lenses) is eight lenses you invoke by name that put Claude in a specific senior seat: architect, critic, design, ops, pm, security, staff, testing. Each has a point of view and a list of things it refuses to do, so you get an argument rather than agreement.

```
/role-critic we should cache the whole graph in memory to save tokens
/role-ops this migration drops a column on the orders table
```

## Reference

| Plugin | What it is | Page |
|---|---|---|
| [unslop](plugins/unslop) | Three scanners that catch the AI tells in prose, code, and UI, so the work reads like you. | [toolshed](https://ivanmisic.net/toolshed/plugins/unslop) |
| [dev-workflow-forge](plugins/dev-workflow-forge) | Two generators that read your codebase and write a review skill and a rules set fitted to it, plus a learning loop that proposes updates from your review history. | [toolshed](https://ivanmisic.net/toolshed/plugins/dev-workflow-forge) |
| [dev-loop](plugins/dev-loop) | The everyday loop as three stack-neutral commands: `/fix`, `/commit`, `/ship`, each gated. | [toolshed](https://ivanmisic.net/toolshed/plugins/dev-loop) |
| [sanitize-public](plugins/sanitize-public) | Pre-publish leak scanner for secrets, internal hosts, and private paths, plus a manual pass for what a regex misses. | [toolshed](https://ivanmisic.net/toolshed/plugins/sanitize-public) |
| [search-visibility](plugins/search-visibility) | Rank what to fix from your Search Console data, over the API or from an export, and audit whether AI assistants can fetch, parse, and cite a page. | [toolshed](https://ivanmisic.net/toolshed/plugins/search-visibility) |
| [role-lenses](plugins/role-lenses) | Eight senior-review lenses, invoked by name, that argue back instead of agreeing. | [toolshed](https://ivanmisic.net/toolshed/plugins/role-lenses) |

Skills that write files you have to live with wait for you to type them. Skills that only report can fire on their own. Each plugin's README says which is which.

## Rule packs

Not plugins. [rule-packs/](rule-packs/) are drop-in `.claude/rules/` files for five stacks (generic, PHP, Python, React and TypeScript, Flutter). Copy the `.md` files into your project. See [rule-packs/README.md](rule-packs/README.md) or the [toolshed rules shelf](https://ivanmisic.net/toolshed/rules).

They are a baseline, not a fit. For rules tuned to your actual conventions, install `dev-workflow-forge` and run `/a-rules-optimizer` on the repo.

## License

MIT. See [LICENSE](LICENSE).
