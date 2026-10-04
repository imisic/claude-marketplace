# sanitize-public

sanitize-public helps anyone publishing a plugin, repository or download check it for credentials and private details before it goes public. It scans the files and their full Git history for keys, passwords, internal hostnames, private IP addresses and home-folder paths, matches your own private names (employer, clients, internal projects) from a local list you keep, and walks a short checklist for the leaks a scanner can't see. Out of the box it knows only the generic patterns; add your own private terms to make it catch what matters to you.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

Installing a Claude Code plugin **copies the plugin directory onto the
installer's machine**, and relative-path plugins pull in the whole
marketplace repo. There is no "delete it later" once something ships. This
skill turns the pre-publish check into a deterministic scan plus a short
manual-review checklist, instead of something you have to remember to do by
hand every time.

## Quickstart

```bash
python3 skills/sanitize-public/scripts/leak_scan.py <artifact> --severity medium
```

Point it at the artifact that will actually ship (a plugin directory, a
bundle folder, a repo root), not the wider tree you authored it in. Exit code
0 means clean at that floor; exit code 1 means findings to review. `high`
findings should never ship; `medium` findings almost never should.

```bash
python3 skills/sanitize-public/scripts/leak_scan.py <artifact> --severity high  # hard blocks only
python3 skills/sanitize-public/scripts/leak_scan.py <artifact> --json           # for a hook or CI
```

A clean scan means the lexical layer is clean. It is not the same as "safe to
publish": run the manual-review section in
`skills/sanitize-public/references/patterns.md` for the contextual leaks a
regex cannot see (unreleased plans, a client named in prose, infra topology
described in words).

## The full gate

```bash
skills/sanitize-public/scripts/publish_gate.sh --repo . --ref <what-you-will-push> --identity <public-email>
```

The scanner alone reads files. The gate also scans every commit reachable from the ref you are about to push, including old blobs and commit messages, checks that every commit carries the email you mean to publish under, runs gitleaks as a second opinion on secrets, and lists binaries for you to open. Add `--also <dir>` for anything else that ships, such as an unzipped download bundle. Any finding exits 1.

## What it runs

Everything happens on your machine. `leak_scan.py` is standard-library Python that reads the files you point it at and prints findings; it opens no network connection. `publish_gate.sh` runs `git` against your local repository and `python3`. If gitleaks is installed it runs that, otherwise it uses the `ghcr.io/gitleaks/gitleaks` Docker image with networking disabled, provided you have pulled it. Nothing is uploaded and no telemetry is sent.

## Local override (your own private identifiers)

Out of the box the scanner only knows generic shapes. Your own private
identifiers, an internal product name, a client codename, a work email
domain, a named infra host, never belong in a script that ships. Add them to
a local file instead:

- `$LEAK_SCAN_PRIVATE` if set, else `~/.config/leak-scan/private-terms` if it
  exists.
- One rule per line: `<low|medium|high> <regex>` (first whitespace splits
  severity from the regex). `#`-comments and blank lines are ignored.

That file lives only on your machine. The scanner reads it to do the matching; it is never copied into anything the plugin ships or publishes.

Write each term so it matches every spelling, because code spells a project name however its language prefers: `medium (?i)\bfoo[\s_\-.]*bar\b` catches `FooBar`, `foo_bar`, `foo-bar` and `Foo Bar`. The scanner also splits identifiers into words before applying your rules, so the same term inside `BenchFooBarPanel` is caught.

## Examples

- `/sanitize-public plugins/my-plugin before I push it to a public repo.`
- `Run publish_gate.sh on the release branch I'm about to push, with my public email as the identity.`
- `Scan the unzipped download bundle in dist/bundle for credentials, internal hostnames and home paths.`

## Privacy

Everything runs on your machine. The scanner reads the files you point it at and prints findings; it opens no network connection. Your private terms stay in a local file the plugin never copies. The plugin itself collects nothing and sends nothing anywhere, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install sanitize-public@imisic
```

Then the command is `/sanitize-public`.

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/sanitize-public](https://ivanmisic.net/toolshed/plugins/sanitize-public).
