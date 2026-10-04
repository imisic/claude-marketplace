#!/usr/bin/env python3
"""Migrate a project's review-issues.jsonl from schema v1 to v2.

v1 had no row type and no disposition, so three incompatible conventions grew up
in practice:

  Convention A
      a-self-learner stamped processed_by / covered_by / processed_date onto the
      ORIGINAL finding row, in place. The row is then both the evidence of a
      problem and the record of its fix, and the log cannot say which.
  Convention B
      a *-fix skill appended a NEW row whose message starts "FIXED: ", with its own
      finding_id and no link back. Pairing was (category, file) guesswork.
  everywhere else
      nothing. Six projects captured findings and never recorded an outcome.

This script converts all three into v2's explicit shape: findings carry
type/disposition, outcomes become separate type:"resolution" rows, and the link
is a real finding_id in `resolves` wherever the pairing is unambiguous.

Conservative by design. An ambiguous pairing is left unlinked rather than
guessed: an absent `resolves` means unknown, and a-self-learner's folding rule
falls back to (category_hash, file) exactly as before. Guessing here would
manufacture the certainty the migration exists to restore.

Usage:
    migrate-review-log-v2.py <path-to-jsonl> [more paths...]   # dry run, prints a plan
    migrate-review-log-v2.py --apply <path> [...]              # rewrites, keeps <path>.bak

Archives are migrated only when named explicitly. The active log is what
a-self-learner clusters, so that is what matters first.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

FIXED_PREFIXES = ("fixed:", "fix:", "resolved:")


def load(path: Path) -> tuple[list[dict], list[tuple[int, str]]]:
    """Return (rows, malformed) where malformed is [(lineno, raw)]."""
    rows, malformed = [], []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            malformed.append((i, line[:120]))
    return rows, malformed


def canonical_hash(category: str) -> str:
    """The one true category_hash: sha256 of the lowercased slug, first 16 hex chars.

    Must stay byte-identical to capture-finding.sh, which hashes the lowercased
    category with no separator and no trailing newline.
    """
    return hashlib.sha256(category.lower().encode("utf-8")).hexdigest()[:16]


def is_resolution_v1(row: dict) -> bool:
    """Did v1 mean this row as an outcome rather than a finding?

    Two independent conventions, both checked because a fleet-wide migration
    meets both: the message prefix and the skill name
    (any *-fix skill appending to the same log).
    """
    msg = (row.get("message") or "").strip().lower()
    if msg.startswith(FIXED_PREFIXES):
        return True
    skill = (row.get("skill") or "").lower()
    return skill.endswith("-fix") or skill.endswith("_fix")


def strip_fixed_prefix(message: str) -> str:
    low = message.strip().lower()
    for p in FIXED_PREFIXES:
        if low.startswith(p):
            return message.strip()[len(p):].strip() or message.strip()
    return message.strip()


def backfill_hash(row: dict, stats: Counter) -> dict:
    """Recompute category_hash from the category slug.

    Historical logs carry hashes from whatever formula that project's capture
    helper used at the time, and several used one that folded in the free-text
    message. Those rows can never cluster with anything captured now, which
    silently defeats the whole recurrence loop: the log looks fine and every
    finding is its own cluster of one. Measured 2026-08-29 on the migrated logs:
    100 percent mismatch in four repos, 5 percent in a fifth.

    Idempotent by construction, since it is a pure function of the category.
    """
    cat = row.get("category")
    if not cat:
        return row
    want = canonical_hash(cat)
    if row.get("category_hash") != want:
        row = dict(row)
        row["category_hash"] = want
        stats["hash_backfilled"] += 1
    return row


def migrate(rows: list[dict]) -> tuple[list[dict], Counter]:
    stats = Counter()

    # Index findings by (category_hash, file) so resolution rows can be linked.
    # Only rows that are themselves findings are candidates.
    findings_by_key: dict[tuple, list[dict]] = {}
    for row in rows:
        if row.get("schema") == 2 or is_resolution_v1(row):
            continue
        key = (row.get("category_hash"), row.get("file"))
        findings_by_key.setdefault(key, []).append(row)

    out = []
    for row in rows:
        if row.get("schema") == 2:
            stats["already_v2"] += 1
            out.append(backfill_hash(row, stats))
            continue

        new = dict(row)
        new["schema"] = 2

        if is_resolution_v1(row):
            new["type"] = "resolution"
            new["action"] = "fixed"
            new["message"] = strip_fixed_prefix(row.get("message", ""))
            key = (row.get("category_hash"), row.get("file"))
            candidates = findings_by_key.get(key, [])
            # Link only when exactly one finding shares the key. Two findings of
            # the same category in the same file are genuinely ambiguous: the
            # fix row records neither line nor id, so any pick is a coin flip.
            if len(candidates) == 1:
                new["resolves"] = candidates[0].get("finding_id")
                stats["resolution_linked"] += 1
            else:
                stats["resolution_unlinked"] += 1
            # These v1 keys described the finding, not the outcome, and mean
            # nothing on a resolution row.
            for k in ("disposition", "whitelisted", "processed_by", "processed_date"):
                new.pop(k, None)
            stats["resolutions"] += 1
            out.append(new)
            continue

        new["type"] = "finding"
        # whitelisted was the only v1 disposition signal, and it was set by a
        # flag almost nobody passed, so false means "unknown", not "confirmed".
        # Treating it as confirmed is right anyway: these rows were reported to
        # the user as real findings at the time.
        new["disposition"] = "dismissed" if row.get("whitelisted") is True else "confirmed"
        if new["disposition"] == "dismissed":
            stats["dismissed"] += 1

        # In-place stamps (convention A above) become a real resolution
        # row, and the stamp keys come off the finding. Same information, but
        # now the finding stays evidence and the outcome stands on its own.
        covered_by = row.get("covered_by")
        processed_by = row.get("processed_by")
        processed_date = row.get("processed_date")
        for k in ("covered_by", "processed_by", "processed_date"):
            new.pop(k, None)
        stats["findings"] += 1
        out.append(new)

        if covered_by:
            res = {
                "schema": 2,
                "type": "resolution",
                "date": processed_date or row.get("date"),
                "project": row.get("project"),
                "skill": processed_by or "a-self-learner",
                "run_id": row.get("run_id"),
                "finding_id": (row.get("finding_id") or "") + "-r",
                "dimension": row.get("dimension"),
                "severity": row.get("severity"),
                "category": row.get("category"),
                "file": row.get("file"),
                "line": row.get("line", 0),
                "message": f"covered by {covered_by}",
                "category_hash": row.get("category_hash"),
                "action": "covered",
                "resolves": row.get("finding_id"),
                "covered_by": covered_by,
                "note": "migrated from a v1 in-place covered_by stamp",
            }
            out.append(res)
            stats["stamps_converted"] += 1

    out = [backfill_hash(r, stats) for r in out]
    return out, stats


def main() -> int:
    ap = argparse.ArgumentParser(description="Migrate review-issues.jsonl v1 to v2")
    ap.add_argument("paths", nargs="+", type=Path)
    ap.add_argument("--apply", action="store_true",
                    help="rewrite the files (a .bak copy is kept); default is a dry run")
    args = ap.parse_args()

    exit_code = 0
    for path in args.paths:
        if not path.is_file():
            print(f"SKIP {path}: not a file", file=sys.stderr)
            exit_code = 1
            continue

        rows, malformed = load(path)
        out, stats = migrate(rows)

        print(f"\n{path}")
        print(f"  read {len(rows)} rows" + (f", {len(malformed)} malformed" if malformed else ""))
        for lineno, raw in malformed:
            print(f"    MALFORMED line {lineno}: {raw}")
        for k in ("already_v2", "findings", "dismissed", "resolutions",
                  "resolution_linked", "resolution_unlinked", "stamps_converted",
                  "hash_backfilled"):
            if stats[k]:
                print(f"  {k:20s} {stats[k]}")
        print(f"  writes {len(out)} rows")

        if args.apply:
            # Malformed lines are dropped by load(), so refuse rather than lose
            # them silently. The user fixes the line, then reruns.
            if malformed:
                print("  REFUSED: fix the malformed lines first, they would be dropped",
                      file=sys.stderr)
                exit_code = 1
                continue
            shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
            with path.open("w", encoding="utf-8") as f:
                for row in out:
                    f.write(json.dumps(row, separators=(",", ":")) + "\n")
            print(f"  APPLIED, backup at {path.name}.bak")
        else:
            print("  dry run, nothing written (pass --apply to rewrite)")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
