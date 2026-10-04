---
name: sanitize-public
effort: xhigh
description: >-
  Pre-publish privacy gate. Runs before anything crosses from a private working environment to a
  public one: a plugin marketplace repo, a downloadable bundle, a public GitHub repo or gist, a
  shared skill or command. Scans the exact files that will ship for key material, credentials,
  internal hostnames, LAN IPs, personal home paths, work-email domains, secrets plumbing and
  internal or client project names with a deterministic scanner, then does a human pass for the
  contextual leaks a regex cannot see. Fires on packaging, bundling, publishing, exporting or
  "shipping" content for other people, and on "is this safe to publish", even if the word
  "private" is never said, as long as the destination is public.
---

# sanitize-public

The gate between a private working environment and anything other people can
see. Most setups carry some private infrastructure worth keeping private (a
LAN host, machine names, encrypted secrets, work that cannot be named
publicly). Most of what gets authored is clean, but the cost of one leak
crossing into a marketplace others clone onto their own machines is high and
irreversible. This skill makes the check mechanical and repeatable instead of
a thing you have to remember.

## Why this exists (the marketplace fact that raises the stakes)

When someone installs a Claude Code plugin, the plugin directory is **copied
onto their machine**, and relative-path plugins clone the whole marketplace
repo. Whatever sits in that repo ships. The same is true of a downloadable
content bundle (a tar.gz someone fetches) and any public repo. There is no
"delete it later" once it is on other people's disks and in git history. So
the scan runs on the **artifact that will actually ship**, not the source
tree it came from.

## When this fires (and when it does not)

**Fires on:**
- Building or updating a plugin marketplace repo, or adding a plugin to one
- Packaging a downloadable bundle or exporting content for publish
- Pushing a new public repo or gist, or sharing a skill/command with someone
- Explicit ask: "is this safe to publish," "scan before shipping," "make sure
  nothing private leaks," "check this bundle"

**Does not fire on:**
- Work that stays inside a private surface (private repos, local-only files,
  a private Claude config repo). Those are allowed to contain private data;
  that is the point of them.
- Routine editing that is not about to be published. Do not nag mid-draft.

If the destination is ambiguous, ask one question: "is this going somewhere
the public can reach?" If yes, gate it.

## Rebuild, do not redact (the rule that actually prevents leaks)

**Never copy a private file into a public artifact and then remove the private parts.** Redaction can only remove what you thought to look for, so it fails on the thing you did not think of, every time. The scanner is a backstop for when this rule is broken, not a substitute for it. A scanner finding means the process already failed.

The failure is mechanical rather than careless. You build a substitution map from the identifiers you can name, run it over the copied file, and every identifier outside that map survives untouched. The map covers the people and terms you remembered; the file carries the ones you did not. A bare first name, an internal acronym, a market or product codename, a former employer: all of those read as ordinary words to you and to the scanner's generic layer alike.

**Port in two phases, with a hard break between them.**

1. **Read the private artifact and write a behaviour spec.** For a test, that is the function name plus what it asserts, in words. For a script, the mechanism, keyed to function and phase names. No fixture strings, no names, no subjects, no example data. If the spec contains something you would not publish, it does not belong in the spec.
2. **Close the private source. Write the new file from the spec alone,** inventing every fixture from the destination's own roster and vocabulary.

The assertions still match, because the code under test is identical. The content is authored rather than laundered, so there is nothing private left to find and remove.

**Fixtures and test data are the high-risk surface**, not prose. Nobody reads a test fixture the way they read a paragraph, so real names survive there. Treat any ported fixture as unsanitized until proven otherwise.

**Redaction is acceptable only for a file that is already public**, where you are editing in place rather than deriving a new artifact.

**A remediation commit must not quote what it removed.** Naming the value in the commit message, the changelog or the issue writes it straight back into history, in a place the working-tree scan will never look. Describe the shape and the location ("a first name in a fixture table"), never the value. The same applies to the report you hand someone: say what class of thing was found and where, and quote the string itself only when they need it to make a decision.

## Method

1. **Identify the shipping artifact.** Not the repo you author in, the thing
   that leaves. For a marketplace, that is the plugin directory (and the repo
   root if plugins use relative paths). For a content bundle, the folder that
   gets packaged. Point the scanner at that.
2. **Seed your own private terms first (once per machine).** The scanner
   ships knowing only generic shapes (key material, LAN IPs, home paths);
   it cannot know your employer domain, your client codenames, or your
   internal product names, and a scan blind to those returns a false
   "clean" that is worse than no scan. Check for the override file
   (`$LEAK_SCAN_PRIVATE`, else `~/.config/leak-scan/private-terms`); if it
   is absent, offer to create it now, seeded with the private identifiers
   already visible in this session or environment, before running the
   scanner. If you proceed without one, say plainly the run only catches
   generic patterns. Format is under "Running the scanner" below.
3. **Run the scanner at the gate floor.** `python3 scripts/leak_scan.py
   <artifact> --severity medium`. Exit code 1 means stop and review. `high`
   findings never ship. `medium` (internal host, LAN IP, home path, a private
   email domain) almost never ship; each needs a reason. Re-run until clean.
4. **Do the human pass.** The scanner is blind to contextual leaks. Walk
   `references/patterns.md` "manual review" section against the content:
   unreleased plans, a client or vertical named in prose, infra topology
   described in words, a private opinion about a named person, a screenshot
   or attachment with private data, git history baked into a bundle.
5. **Report, do not silently pass.** State what shipped clean, what was
   flagged, and what was allow-listed and why. A clean scan is "the lexical
   layer is clean," not "safe to publish." Say that distinction out loud.
6. **Sweep git history when the history itself will ship.** The scanner above only reads the working tree. If the shipping artifact is a git repo whose history goes public too (a marketplace repo pushed as-is, a tarball that still has `.git` inside), a term can be clean in the current tree and still sit in an old commit. Do not loop `git log -S` once per rule: with a generated private layer there are thousands of terms and the loop never finishes. Extract every text blob reachable from what you will push, plus commit messages and authors, into one file and scan that once. `scripts/publish_gate.sh` does exactly this. Then run `git log -S"<term>"` only for the few terms that hit, to find the commit. Note that `-S` also lists the commit that *removed* a term, so read the message before concluding it is still there. A real hit means a history rewrite (`git filter-repo` or equivalent) or, usually cheaper, a fresh-history branch with one clean commit. **Check whether the commit is already on a public remote before promising to remove it.** If it has been pushed, it may already be cloned, forked or cached; a rewrite narrows the exposure, it does not undo it. Say so plainly.
7. **Check the author identity on every commit you will publish.** A fresh clone silently inherits the machine's global git email, which is often a work address. `git log <ref> --format="%ae %ce" | sort -u` should return only the identity you mean to publish under. Fix it with a repo-local `git config user.email` and a rewrite of the affected commits before they are pushed.
8. **Open every binary that ships.** Images, PDFs and archives are skipped by the scanner on purpose and counted in its output. A screenshot with a real terminal, tab, path or calendar in frame leaks more than any string, and no regex will ever see it.

**One command for the mechanical layers.** `scripts/publish_gate.sh --repo <repo> --ref <what-you-will-push> --identity <public-email> [--also <unzipped-bundle>]...` runs the tree scan, the history extract, the identity check, gitleaks (via a local binary or a network-less Docker container, with the reviewed allowlist in `references/gitleaks.toml`) and the binary listing, and exits 1 on any finding. It refuses to run without a private layer unless you pass `--no-private`, because without your own terms the scan passes everything that matters. Point `--ref` at what will be pushed rather than your working branch, and pass anything else that ships (a downloadable bundle, exported page copy) through `--also`: the same leak can sit in the repo, its history and a download built from an older tree at once. The contextual pass in step 4 is still yours.

## Running the scanner

```bash
python3 scripts/leak_scan.py <path>                       # scan, medium floor (the gate)
python3 scripts/leak_scan.py <path> --severity high       # hard blocks only
python3 scripts/leak_scan.py <path> --json                # for a hook or CI
python3 scripts/leak_scan.py <path> --require-private     # fail if there is no private layer
```

Exit codes: `0` clean, `1` findings at or above the floor, `2` bad invocation, `3` no private layer under `--require-private`.

Every run reports which layers it used, how many files it read, and which it skipped as binary. **A run with no private layer says so on its own output and sets `"trustworthy": false` in `--json`.** It still exits 0, because a fresh install has no private layer yet. Once you have one, add `--require-private` in CI so a layer that goes missing fails the build instead of quietly narrowing the scan.

The pattern set in `scripts/leak_scan.py` is the source of truth;
`references/patterns.md` mirrors it in prose and carries the manual-review
layer. Out of the box the scanner only knows generic shapes (key material,
credential assignments, internal-host and LAN-IP patterns, home paths,
secrets-plumbing references). Your own private identifiers, an internal
product name, a client codename, a work email domain, a named infra host,
never belong in the shipped script. Add them instead to a local override file
that stays on your machine and is never part of what ships:

- `$LEAK_SCAN_PRIVATE` if set, else `~/.config/leak-scan/private-terms` if it
  exists.
- One rule per line: `<low|medium|high> <regex>` (the first whitespace
  splits severity from the regex). `#`-comments and blank lines are ignored.
- Present -> the scanner catches your private terms too. Absent -> generic
  layer only (this is what installing this skill gives you by default).

## The private layer is generated, not hand-written

The section above says the file exists. This says how to keep it honest. A hand-written `private-terms` holds the two dozen terms you thought of on the day you wrote it. Whatever system already holds your identities (a contact directory, an org chart, a CRM export, a notes vault) holds every name that actually exists. The gap between those two counts is where a leak lives, and it widens every time the real system grows and the hand list does not.

So generate the file rather than typing it. A small script that reads your source of truth, batches the names into a few compiled alternations and emits the `<severity> <regex>` format above is enough. Run it before a publish gate, and make it idempotent so regenerating is never a decision.

Two inputs stay manual, and they are the only two you edit by hand:

- **A vocabulary file** for internal terms no directory holds: employers, org units, internal product and project names, market names, infra hostnames. Add a term the first time you catch yourself typing it into public content.
- **An allow file** for names that must never be flagged: your own public identity, and the fictional roster of each public destination. Every line here is a deliberate blind spot, so keep it short and know why each one is there.

**Write vocabulary rules to match every spelling.** Code names a project however its language prefers, so a rule for `FooBar` alone misses `foo_bar`, `foo-bar` and `Foo Bar`. Split the term into its words and allow any separator run between them: `medium (?i)\bfoo[\s_\-.]*bar\b`. The scanner also re-reads every line with identifiers split into words (`BenchFooPanel` becomes `Bench Foo Panel`) before applying your private rules, so a name inside a class or module name is caught too. Add the names of your private repositories to the vocabulary as well: no directory lists side projects, and a project that exists on your disk is a name that can leak.

Keep those two wherever your config syncs between machines. Do **not** track the generated output: it expands to every real name you know, and it is one regenerate away on any machine.

**A scan is only as good as the machine's private layer.** The generated file does not travel with the repo, so a fresh machine scans with the generic rules alone and will happily call an artifact clean while it is full of colleagues' names. Regenerate there before trusting a clean result.

## Escape hatch

A line containing `ship-allow` is skipped, for a value that is public on
purpose (a published contact address, a documented public repo URL). Use it
only after looking at the line. An unexamined allow-list defeats the gate.

## Not a secret scanner for code security

This is about **publication**, not vulnerability. It does not audit for
injection, weak crypto, or exposed endpoints in running code. It answers one
question: is there anything in this artifact that should not leave your
private environment.
