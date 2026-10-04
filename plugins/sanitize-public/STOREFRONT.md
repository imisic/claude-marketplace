---
name: sanitize-public
tagline: Scan a repository or bundle for credentials and private details before publishing, then review what the scanner cannot detect.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install sanitize-public@imisic
tags: developers, security, claude-code, privacy
---

Before a skill, plugin, or bundle leaves a private working environment, this runs the check that is easy to skip under deadline pressure: does anything in what's about to ship carry a private leak.

Installing a Claude Code plugin copies the plugin directory onto the installer's machine, and relative-path plugins pull in the whole marketplace repo. A public repo, gist, or downloadable bundle works the same way. Once it's out, there's no "delete it later."

**What you get**

- `/sanitize-public`: scan a target and walk the manual-review checklist before you publish it.
- `publish_gate.sh`: one command that scans the tree you are about to push, every commit reachable from it, the email on each commit, and a second-opinion secret scan with gitleaks.

The scan reads the exact files that will ship (key material, credentials, internal hostnames, LAN IPs, personal home paths, secrets-management references) with a deterministic scanner, then walks a short manual-review checklist for the leaks a regex can't see: unreleased plans, a client named in prose, infra topology described in words, git history baked into a bundle that still has its `.git` folder.

A name deleted last month still sits in every clone if an old commit carries it. The gate scans the commit you are about to push and everything reachable from it, then refuses to pass a commit made under an email you did not mean to publish.

Private names are matched in any spelling. A project called `FooBar` in your notes turns up as `foo_bar` in a Python import or inside a class name, and the scanner splits identifiers into words before it checks them.

Out of the box it ships generic patterns only. Your own private identifiers, an internal product name, a client codename, a work email domain, a named infra host, live in a local override file on your machine and are never part of what the plugin ships to anyone who installs it.
