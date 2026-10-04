# Leak patterns and the manual-review layer

Two halves. The **scanned patterns** are what `scripts/leak_scan.py` catches
deterministically; this section mirrors the script in prose so a human can
read the intent. The **manual review** is what a regex is blind to and a
person has to look for. A clean scan covers only the first half.

## Scanned patterns (the script is the source of truth)

The shipped `RULES` are **generic**: they contain no one's private
identifiers, so the script is safe to publish (it ships inside this plugin).
Your own private identifiers load at runtime from a local override file that
never ships (see "Local override" below).

### high (never ships, hard block)
- **Key material**: PEM / OpenSSH / PGP private key blocks, age secret keys.
- **Provider keys**: AWS access key ids, Google API keys, OpenAI-style `sk-`
  keys, GitHub `ghp_`/`gho_` tokens, Slack `xox*` tokens.
- **Bearer / Authorization** headers carrying a real token value.
- **Credential assignments**: `password=`, `secret=`, `api_key=`,
  `access_token=`, `client_secret=` with a concrete value (placeholders like
  `changeme`, `<...>`, `$VAR`, `env`, `your-...` are ignored).

### medium (almost never ships, needs a reason each time)
- **Internal hosts**: any hostname ending in `.lan`, `.local`, `.internal`,
  or `.home` (one generic rule covers every internal host on your network;
  no per-host pattern needed).
- **RFC1918 private IPs**: `10.x`, `192.168.x`, `172.16-31.x`.
- **Personal home paths**: `/home/<user>/`, `/Users/<user>/`.

### low (context-dependent, manual call)
- **Secrets plumbing**: mentions of a secrets manager, key file, or
  bootstrap script name. Fine in a private runbook, a leak in a public
  README.

## Local override (your private identifiers, never shipped)

Internal product names, project codenames, a work email domain, named infra
hosts: these are private to you and must not be baked into a script that
ships. They load from a local file instead:

- `$LEAK_SCAN_PRIVATE` if set, else `~/.config/leak-scan/private-terms` if it
  exists.
- One rule per line: `<low|medium|high> <regex>` (the first whitespace
  splits severity from the regex). `#`-comments and blank lines are ignored.
- Present -> full coverage locally. Absent (the shipped default) -> generic
  layer only.

When a new identifier enters your private set (a new machine name, a new
client, a new internal host), add it to the **local override file**, not to
`RULES` in the shipped script. The prose here follows the script's generic
layer, never leads it.

## Git history (when the artifact's `.git` ships too)

The scanner only reads the current working tree. If the shipping artifact
still has its `.git` directory (a repo pushed as-is, a tarball that forgot to
strip it), a term can be gone from the tree today and still sit in an old
commit or diff. For every medium-or-higher rule above, run `git log --all
-S"<term>" --oneline | head -5` from the repo root. Any hit means the term is
reachable by anyone who clones the repo, even if `HEAD` is clean. The fix is
a history rewrite or, usually cheaper, a fresh-history repo: new `git init`,
one clean commit, the old repo stays private.

## Manual review (the scanner cannot see these)

Run these by eye against the shipping artifact. Every one has leaked from
someone at some point with zero keyword a regex could catch.

- **Unreleased or internal plans.** Roadmap detail, an unshipped feature, a
  dated internal decision. Public copy is work-focused and does not preview
  private plans.
- **Named people or clients.** A colleague, a client, a vertical named in
  prose. If you have a standing rule about which of your own details never
  appear in public copy, this is where it applies. No opinion about a named
  individual.
- **Infra topology in words.** Describing which machine talks to which over
  the LAN leaks the same map as a hostname would, with no string to match.
- **Absolute paths and usernames in examples.** Command examples that
  hardcode a real home path or machine instead of `~` or a placeholder.
- **Attachments and media.** A screenshot with a private tab, terminal, or
  path visible. A PDF/image the scanner skipped by extension.
- **Git history baked into a bundle.** A tar of a folder that still contains
  a `.git` with private commit messages or author emails. Ship the files,
  not the history.
- **Commented-out real values.** A disabled credential line the credential
  rule might miss if malformed, or a "TODO: remove before publish" that never
  got removed.
- **The over-share in a docstring or comment.** A comment that explains
  *why* using a private incident, a client's constraint, or an internal name.

## Reporting shape

After the gate, say plainly:
- what was scanned (the artifact, not the source tree),
- scan result at the `medium` floor,
- anything allow-listed and the reason,
- the manual-review outcome,
- and the honest caveat: clean scan = lexical layer clean, not "safe to
  publish." The human pass is what makes it safe.
