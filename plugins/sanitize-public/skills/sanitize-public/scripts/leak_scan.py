#!/usr/bin/env python3
"""
leak_scan.py - scan a file or directory for private data before it ships to a
public surface (a plugin marketplace repo, a toolshed bundle, a public gist or
GitHub repo). Deterministic source of truth for the leak patterns; the
human-readable view is references/patterns.md. If the two disagree, this wins.

What ships vs what stays local. The RULES below are GENERIC: key material,
credential assignments, internal-host and LAN-IP shapes, personal home paths,
secrets-management plumbing. They contain no one's private identifiers, so this
script is safe to publish (it is itself shipped inside the sanitize-public
plugin). Your OWN private identifiers (internal product names, project
codenames, a work email domain, named infra hosts) load at runtime from a local
override file that never ships:

    $LEAK_SCAN_PRIVATE            if set, else
    ~/.config/leak-scan/private-terms   if it exists

That file is one rule per line: `<severity> <regex>` (first whitespace splits
severity from the regex; blank lines and #-comments ignored). With it present
you get full coverage locally; without it you get the generic layer only. Point
the scanner at the shipping artifact and it catches your private terms via the
local file; the copy someone else installs carries only the generic rules.

A MISSING local file does not make a scan pass, it makes it narrow. This layer
carries every real name, address and internal term, so without it the generic
layer alone will happily call an artifact clean while it is full of colleagues'
names. That is an observed failure, not a hypothetical. So a run without the
local file says so, loudly, on every line of output that reports a result, and
sets "trustworthy": false in --json. It still exits 0, because a fresh install
has no local file yet and a tool that refuses on first run reads as broken. Pass
--require-private to turn that warning into exit 3, which is what you want once
you have a local file and want CI to notice if it goes missing.

What it can and cannot see. The mechanical tells live here. The high-value
leaks are CONTEXTUAL and a regex cannot see them: unreleased plans, a client's
name, infra topology described in prose, a private opinion about a named
person. Those are in references/patterns.md for a human pass. A clean scan
means the lexical layer is clean, not that the content is safe to publish.
Plain Python, standard library only.

Escape hatch. A line containing  ship-allow  is skipped, for a value that is
public on purpose (the site's own public contact address, a documented public
repo). Use it sparingly and only after you have looked at the line.

Usage:
    python3 leak_scan.py <path>                  # scan a file or dir
    python3 leak_scan.py <path> --severity high  # only the hard blocks (gate tier)
    python3 leak_scan.py <path> --json           # machine-readable (for CI / hooks)

Exit codes: 0 = clean at the requested severity floor, 1 = findings at or above
the floor, 2 = bad invocation, 3 = no local private layer (scan not trustworthy).
Wire it as a gate: default floor is 'medium'.
"""

import argparse
import json
import os
import re
import sys

SEV_RANK = {"low": 0, "medium": 1, "high": 2}

# Each rule: (id, severity, regex, human note). Severity order:
# high  = near-certain secret or credential. Never ships. Hard block.
# medium = internal infra / personal identifier shape. Almost never ships; review.
# low   = a token that is often private in this context; manual call.
# These are GENERIC by design. Private identifiers live in the local override
# file (see load_local_rules), never here, so this script can ship as-is.
RULES = [
    ("private-key-block", "high",
     r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----",
     "PEM/OpenSSH/PGP private key material"),
    ("age-secret-key", "high",
     r"AGE-SECRET-KEY-1[0-9A-Z]+",
     "age private key"),
    ("aws-access-key", "high",
     r"\bAKIA[0-9A-Z]{16}\b",
     "AWS access key id"),
    ("google-api-key", "high",
     r"\bAIza[0-9A-Za-z_\-]{35}\b",
     "Google API key"),
    ("openai-key", "high",
     r"\bsk-[A-Za-z0-9]{20,}\b",
     "OpenAI-style secret key"),
    ("github-token", "high",
     r"\bgh[pousr]_[A-Za-z0-9]{36,}\b",
     "GitHub personal access / OAuth token"),
    ("slack-token", "high",
     r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
     "Slack token"),
    ("bearer-token", "high",
     r"(?i)\b(?:authorization|bearer)\b\s*[:=]?\s*['\"]?[A-Za-z0-9._\-]{20,}",
     "Authorization / bearer token with a value"),
    # `pass` on its own is ordinary English ("- Pass: document file list", "a
    # second pass") and fired far more often on prose than on credentials. A
    # high-severity rule that cries wolf is worse than no rule, because it is the
    # tier people are told never to ship past. password/passwd only.
    ("credential-assignment", "high",
     r"(?i)\b(pass(?:word|wd)|secret|api[_-]?key|access[_-]?token|"
     r"client[_-]?secret|private[_-]?token|db[_-]?pass\w*)\b\s*[:=]\s*"
     r"['\"]?(?!(?:null|none|true|false|changeme|<|\$|\{|env|your[_-])\b)[^\s'\"]{6,}",
     "credential assigned a concrete value"),

    # The trailing (?!\.\w) keeps ordinary filenames out: `settings.local.json`,
    # `config.local.yml` and friends are a widespread convention, not hosts, and
    # a rule that cries wolf on them teaches you to skim past its real findings.
    ("lan-host", "medium",
     r"\b[a-z0-9][a-z0-9\-]*\.(?:lan|local|internal|home)\b(?!\.\w)",
     "internal-only hostname"),
    ("private-ipv4", "medium",
     r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|"
     r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",
     "RFC1918 private IP"),
    ("home-path", "medium",
     r"/home/[a-z_][a-z0-9_\-]*/|/Users/[a-z_][a-z0-9_\-]*/",
     "absolute personal home path"),

    ("sops-age-ref", "low",
     r"(?i)\b(?:sops|age|keys\.txt|known_hosts|dev-bootstrap)\b",
     "secrets-management plumbing reference"),
]


# Populated by load_local_rules() so the report can state which layers actually
# ran. A scan that cannot name its layers is a scan you cannot act on.
LOCAL_LAYER = {"path": None, "rules": 0}

# What the scan actually looked at. A skipped file must be visible in the report:
# silent skips are how a gate reports "clean" on content it never opened.
SCAN_STATS = {"scanned": 0, "binary": 0, "unreadable": 0,
              "skipped_ext": 0, "skipped_names": []}


def load_local_rules():
    """Load private, machine-local rules that must never ship inside this
    script. Path: $LEAK_SCAN_PRIVATE, else ~/.config/leak-scan/private-terms.
    Format: one rule per line, `<severity> <regex>` (first whitespace splits).
    Missing file is normal (the shipped default) and yields no extra rules."""
    path = os.environ.get("LEAK_SCAN_PRIVATE") or os.path.expanduser(
        "~/.config/leak-scan/private-terms")
    # Recorded before the existence check: the "no private layer" warning has to
    # name the path it looked for, which is exactly the case where it is absent.
    LOCAL_LAYER["path"] = path
    if not path or not os.path.isfile(path):
        return []
    extra = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for lineno, raw in enumerate(fh, 1):
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) != 2 or parts[0] not in SEV_RANK:
                    sys.stderr.write(
                        f"leak-scan: {path}:{lineno} skipped (want "
                        f"'<low|medium|high> <regex>')\n")
                    continue
                sev, rx = parts
                try:
                    extra.append(("private-local", sev, re.compile(rx),
                                  "private identifier (local rule)"))
                except re.error as exc:
                    sys.stderr.write(
                        f"leak-scan: {path}:{lineno} bad regex: {exc}\n")
    except OSError as exc:
        sys.stderr.write(f"leak-scan: cannot read {path}: {exc}\n")
    return extra


COMPILED = [(rid, sev, re.compile(rx), note) for rid, sev, rx, note in RULES]
_LOCAL = load_local_rules()
LOCAL_LAYER["rules"] = len(_LOCAL)
COMPILED.extend(_LOCAL)

# Never descend into these; they are not the shipped artifact.
SKIP_DIRS = {".git", "node_modules", "vendor", ".claude", "storage",
             "__pycache__", ".idea", ".vscode"}
# Binary / non-text extensions we do not read.
SKIP_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
            ".gz", ".tar", ".tgz", ".woff", ".woff2", ".ttf", ".mp4", ".mp3",
            ".wav", ".phar", ".lock"}


def iter_files(path):
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if os.path.splitext(name)[1].lower() in SKIP_EXT:
                # Counted, not silent: these are exactly the files that need a
                # human to open them (a screenshot with a real terminal in frame
                # leaks more than any string, and no regex will ever see it).
                SCAN_STATS["skipped_ext"] += 1
                SCAN_STATS["skipped_names"].append(os.path.join(root, name))
                continue
            yield os.path.join(root, name)


def split_identifiers(line):
    """The line with identifiers broken into words: `BenchFooPanel` becomes
    `Bench Foo Panel`, `foo_bar` becomes `foo bar`.

    Private rules are usually word-bounded, and `\\b` sees no edge inside
    camelCase or on either side of `_`, so a private project name inside a
    function or module name scans clean. Code is exactly where such names hide.
    Only private rules get this second look: the generic ones are shaped for
    raw text.
    """
    line = re.sub(r"(?<=[a-z0-9])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])", " ", line)
    return line.replace("_", " ")


def scan_file(fpath, floor):
    """Scan one file. Decodes leniently on purpose.

    This used to open with errors="strict" and swallow UnicodeDecodeError, so a
    single stray byte anywhere in a file made the WHOLE file scan as clean with
    no message. That is the worst possible failure for a gate, and it was
    observed: a 4MB git-history extract containing two embedded PNG blobs
    reported zero findings while holding a real name in its text. Binary is now
    decided by a NUL byte in the first block (the standard heuristic), counted,
    and reported; everything else is decoded with errors="replace" and scanned.
    """
    findings = []
    try:
        with open(fpath, "rb") as fh:
            raw = fh.read()
    except OSError:
        SCAN_STATS["unreadable"] += 1
        return findings
    if b"\x00" in raw[:8192]:
        SCAN_STATS["binary"] += 1
        return findings
    SCAN_STATS["scanned"] += 1
    lines = raw.decode("utf-8", errors="replace").splitlines()
    for lineno, line in enumerate(lines, 1):
        if "ship-allow" in line:
            continue
        split = split_identifiers(line)
        for rid, sev, rx, note in COMPILED:
            if SEV_RANK[sev] < SEV_RANK[floor]:
                continue
            m = rx.search(line)
            if not m and rid == "private-local" and split != line:
                m = rx.search(split)
            if m:
                findings.append({
                    "file": fpath, "line": lineno, "rule": rid,
                    "severity": sev, "note": note,
                    "match": m.group(0)[:80],
                })
    return findings


def main():
    ap = argparse.ArgumentParser(description="Pre-publish leak scan.")
    ap.add_argument("path")
    ap.add_argument("--severity", choices=("low", "medium", "high"),
                    default="medium", help="minimum severity to report (gate floor)")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--require-private", action="store_true",
                    help="exit 3 when there is no local private layer (for CI)")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        sys.stderr.write(f"path not found: {args.path}\n")
        sys.exit(2)

    # The local layer carries every real name, address and internal term. Without
    # it a "clean" result only means no key material and no LAN hostnames, which
    # is not what anyone reads it as. Say so up front rather than mislead.
    blind = LOCAL_LAYER["rules"] == 0
    if blind and not args.json:
        sys.stderr.write(
            "leak-scan: NO LOCAL PRIVATE LAYER. Generic rules only, so this scan\n"
            "cannot see names, employers, internal products or work addresses.\n"
            "  add one: " + LOCAL_LAYER["path"] + "\n"
            "  format:  one rule per line, `<low|medium|high> <regex>`\n"
            "  in CI:   --require-private to make this an error instead\n")

    all_findings = []
    for f in iter_files(args.path):
        all_findings.extend(scan_file(f, args.severity))

    all_findings.sort(key=lambda x: (-SEV_RANK[x["severity"]], x["file"], x["line"]))

    # Always state the layers. "Clean" is only meaningful next to what was checked.
    layers = (f"generic({len(COMPILED) - LOCAL_LAYER['rules']})"
              f" + private({LOCAL_LAYER['rules']} from {LOCAL_LAYER['path']})"
              if LOCAL_LAYER["rules"] else
              f"generic({len(COMPILED)}) ONLY - no private layer")

    if args.json:
        print(json.dumps({"findings": all_findings, "count": len(all_findings),
                          "layers": {"generic": len(COMPILED) - LOCAL_LAYER["rules"],
                                     "private": LOCAL_LAYER["rules"],
                                     "private_source": LOCAL_LAYER["path"]},
                          "read": dict(SCAN_STATS),
                          "trustworthy": not blind}, indent=2))
    else:
        print(f"leak-scan: layers = {layers}")
        skipped = SCAN_STATS["binary"] + SCAN_STATS["skipped_ext"]
        print(f"leak-scan: read {SCAN_STATS['scanned']} text file(s); "
              f"skipped {skipped} binary/media, "
              f"{SCAN_STATS['unreadable']} unreadable.")
        if skipped:
            print("leak-scan: OPEN THESE YOURSELF, a regex cannot read a "
                  "screenshot:")
            for name in SCAN_STATS["skipped_names"][:20]:
                print(f"           {name}")
            if len(SCAN_STATS["skipped_names"]) > 20:
                print(f"           ... and {len(SCAN_STATS['skipped_names']) - 20} more")
        if blind:
            print("leak-scan: WARNING, generic layer only. This scan cannot see "
                  "names, employers, internal products or work addresses.")
        if not all_findings:
            print(f"leak-scan: no findings at severity>={args.severity} ({args.path})")
            print("leak-scan: this is the LEXICAL layer only. Contextual leaks "
                  "(unreleased plans, a named client, infra described in prose) "
                  "still need the human pass in references/patterns.md.")
        else:
            for f in all_findings:
                print(f"[{f['severity']:>6}] {f['file']}:{f['line']} "
                      f"{f['rule']} -- {f['note']}\n         {f['match']!r}")
            print(f"\nleak-scan: {len(all_findings)} finding(s) "
                  f"at severity>={args.severity}. Review before shipping.")

    if all_findings:
        sys.exit(1)
    # Only the caller who asked for strictness gets it. Everyone else gets a
    # clean exit with the narrowness stated in the output and in `trustworthy`.
    if blind and args.require_private:
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
