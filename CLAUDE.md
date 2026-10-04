# CLAUDE.md

Maintenance contract for this repo. It is not the publishing pipeline (that lives outside this repo); it is the set of invariants that must hold inside it, and the checks that catch a break.

## Layout

```
.claude-plugin/marketplace.json   the marketplace manifest, lists every plugin
plugins/<name>/                   one installable plugin
  .claude-plugin/plugin.json      the plugin manifest
  README.md                       repo-facing docs for the plugin
  STOREFRONT.md                   site copy for the ivanmisic.net toolshed page
  skills/<skill>/SKILL.md         model- or user-invoked skills
  commands/<name>.md              slash commands
rule-packs/<name>/                drop-in .claude/rules/ files, not plugins
  STOREFRONT.md                   site copy, same role as above
```

`STOREFRONT.md` is site copy, not plugin content. The toolshed importer reads it for the page and excludes it from the downloadable bundle. Everything else in a plugin directory ships to whoever installs it, so write it for a stranger.

## What must move together

Adding, removing, or renaming a plugin touches four places. Miss one and the break is silent.

1. `plugins/<name>/.claude-plugin/plugin.json`, the plugin's own manifest.
2. `.claude-plugin/marketplace.json`, the entry in the `plugins` array. A plugin with a valid `plugin.json` but no marketplace entry is invisible; nothing warns you.
3. `README.md`, a row in the Plugins table, with its storefront link.
4. `plugins/<name>/STOREFRONT.md`, the page copy, and a matching toolshed row on the site.

Both manifests carry `author`, `homepage`, `license`, and `keywords`. Keywords are what plugin directories index on, so a new plugin without them is unlisted everywhere but here.

`homepage` is the plugin's toolshed detail page, and that URL contains the toolshed row's *kind*. Change a row's kind on the site and two manifests, a README row, and the plugin's own README link all go stale, with nothing to catch it: `claude plugin validate` checks the schema, never that the URL resolves. The kind also lives in `STOREFRONT.md`'s front matter, so that is a fifth place. `sanitize-public` moved from `skills` to `plugins` this way, following the same move `role-lenses` made earlier; both left a redirect behind for the old URL.

## Plugin names are immutable

The `name` field is the slug users install under. Renaming it breaks every existing install with `plugin-not-found`. To change how a plugin is labelled, set `displayName`. If a rename is genuinely unavoidable, add a `renames` map to `marketplace.json` so existing installs migrate on the next sync.

Skill names inside a plugin are a separate namespace and can change freely, but a rename means updating every prose cross-reference in the other skills that invoke it.

## Versions

`version` in `plugin.json` is what Claude Code compares to decide whether an installed user sees an update. A behaviour change that ships without a bump reaches nobody.

- Feature or new behaviour: minor.
- Wording, docs, a fixed typo in a prompt: patch.
- Every bump gets an entry in the plugin's `CHANGELOG.md`, newest first.

A version bump usually makes `STOREFRONT.md` stale, and nothing checks that. If the change was worth a version, it is worth a line on the page.

## Invocation mode

Every skill is one of two things, and the frontmatter has to say which.

- **User-invoked**: reachable only when a human types it. Set `disable-model-invocation: true`. The `description` is human-facing: one line, read off a slash-command menu. No trigger list.
- **Model-invoked**: reachable by the model or the user. Omit the flag and keep rich trigger phrasing ("Use when the user wants X, mentions Y, asks for Z") so auto-invocation actually fires.

The test is whether the model could usefully reach for it on its own. A skill that only makes sense when deliberately invoked but carries a trigger paragraph pays that paragraph's context cost in every session, and fires when nobody asked.

Every skill also carries an `agents/openai.yaml` beside its `SKILL.md`, holding Codex picker metadata (`interface.display_name`, `interface.short_description`). `policy.allow_implicit_invocation` defaults to true, so only a user-invoked skill sets it, to `false`. **The two harnesses must agree**: a skill is user-invoked in both or neither. Nothing enforces that, so when you change one, change the other in the same edit.

Commands under `commands/` are typed by definition and have neither setting. Converting one to a skill would make it reachable from Codex too, which is the reason to do it if the question ever comes up.

## Unpromoted work

Work that is not ready to install goes in `in-progress/` at the repo root, with a README saying so, and gets no entry in `marketplace.json` or the top-level README table. It ships in the repo anyway: half-finished is fine to read, not fine to install. The directory is created when there is something to put in it, not before.

## Before pushing anywhere public

- `claude plugin validate . --strict` from the repo root, and once per plugin directory. All must pass.
- Run the leak scanner over the tree. Nothing here is private, and that is a property to verify rather than assume.
- Sweep for em dashes and en dashes across everything touched, including imported reference files, which carry them in bulk.
- Run the prose scanner over new README and `STOREFRONT.md` copy.

## Public copies are hand-written

The skills here are genericized rewrites of private originals, not a fork that drifted. Never copy a private skill in wholesale: it re-imports project names, personal paths, and local hostnames that were deliberately stripped. Port the changed hunk into the public copy's register instead.
