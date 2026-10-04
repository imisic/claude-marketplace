#!/usr/bin/env python3
"""Fleet roll-up of review-capture health: who is capturing findings, and who never turns them into rules.

The gap this exists to surface, as it shows up in practice: most repos that capture findings into .claude/reviews/review-issues.jsonl have never written an applied-learnings entry. Some sit on dozens of unprocessed findings with qualifying clusters, and nothing anywhere says so. Capture without a periodic learn pass is just a growing log file.

Stdlib only and read-only on purpose: it has to run on any machine in the fleet, including one where the repo's own tooling is not installed, and it is meant to be safe to call from a nudge or a cron line.

Schema handling mirrors scripts/migrate-review-log-v2.py deliberately. If the two disagree about what counts as a resolution row, the health report contradicts the migration that produced the rows, so the v1 fallbacks here are copied from that script rather than re-derived.

Usage:
    review_loop_health.py                  # table, worst first
    review_loop_health.py --json           # machine output
    review_loop_health.py --repo myproject # one repo in detail
    review_loop_health.py --root ~/work    # scan somewhere else
"""

from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

# Copied from migrate-review-log-v2.py. Two independent v1 conventions grew up in the wild: one project's fix skill prefixes the message, and any *-fix skill appending to the same log marks itself by name.
FIXED_PREFIXES = ("fixed:", "fix:", "resolved:")

# A cluster a-self-learner would act on: enough repeats, and spread over more than one review day so a single noisy run cannot manufacture one.
CLUSTER_MIN_FINDINGS = 3
CLUSTER_MIN_DATES = 2

STAMP = "rules-optimizer: audited"
INJ_CHECK = re.compile(r"INJ-\d")
# applied-learnings.md has two shapes in the wild: dated headings and a markdown table. Counting only headings reports a table-shaped file's entries as 0.
LEARN_HEADING = re.compile(r"^#{2,6}\s+(\d{4}-\d{2}-\d{2})")
LEARN_TABLE_ROW = re.compile(r"^\|\s*(\d{4}-\d{2}-\d{2})\s*\|")


def is_resolution_v1(row: dict) -> bool:
    msg = str(row.get("message") or "").strip().lower()
    if msg.startswith(FIXED_PREFIXES):
        return True
    skill = str(row.get("skill") or "").lower()
    return skill.endswith("-fix") or skill.endswith("_fix")


def is_resolution(row: dict) -> bool:
    """v2 says so explicitly; v1 has to be inferred."""
    if row.get("schema") == 2:
        return str(row.get("type") or "").lower() == "resolution"
    return is_resolution_v1(row)


def read_jsonl(path: Path) -> tuple[list[dict], list[int], str | None]:
    """Return (rows, malformed_line_numbers, read_error). A bad line is skipped and counted, never fatal."""
    rows: list[dict] = []
    malformed: list[int] = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return rows, malformed, f"unreadable: {exc.strerror or exc}"
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            malformed.append(lineno)
            continue
        # A bare list or string is syntactically valid JSON but not a finding row.
        if isinstance(obj, dict):
            rows.append(obj)
        else:
            malformed.append(lineno)
    return rows, malformed, None


def read_text_or_note(path: Path, notes: list[str]) -> str:
    """Content scans must never abort the fleet run for the other repos. A root:root file left behind by a sudo-cp is a recurring trap here, so an unreadable file is reported and skipped."""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        notes.append(f"unreadable, skipped: {path} ({exc.strerror or exc})")
        return ""


def parse_applied_learnings(path: Path) -> tuple[list[str], str | None]:
    """Return (entry dates, note). A file with a header and no entries is a stub, which is not a run."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return [], f"applied-learnings unreadable: {exc.strerror or exc}"
    dates = []
    for line in text.splitlines():
        match = LEARN_HEADING.match(line.strip()) or LEARN_TABLE_ROW.match(line.strip())
        if match:
            dates.append(match.group(1))
    if not dates:
        return [], "applied-learnings.md present but holds no dated entries (stub)"
    return sorted(dates), None


def valid_date(value: str) -> bool:
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def days_since(day: str | None, today: date) -> int | None:
    if not day or not valid_date(day):
        return None
    return (today - datetime.strptime(day, "%Y-%m-%d").date()).days


def glob_files(root: Path, patterns: tuple[str, ...]) -> list[Path]:
    found: list[Path] = []
    for pattern in patterns:
        try:
            found.extend(p for p in root.glob(pattern) if p.is_file())
        except OSError:
            continue
    # `**/*.sh` also matches the directory's own files, so the two patterns overlap. The callers set-dedupe by name, but an unreadable file would otherwise be reported once per pattern.
    return sorted(set(found))


def scan_repo(repo: Path, today: date) -> dict:
    claude = repo / ".claude"
    log = claude / "reviews" / "review-issues.jsonl"
    learnings = claude / "reviews" / "applied-learnings.md"
    notes: list[str] = []

    review_skills = sorted(
        p.name for p in (claude / "skills").glob("*") if p.is_dir() and "review" in p.name.lower()
    ) if (claude / "skills").is_dir() else []

    # Some projects call the check script review-metrics.sh, so match on content and never on filename.
    inj_files = [p.name for p in glob_files(claude / "scripts", ("*.sh", "**/*.sh"))
                 if INJ_CHECK.search(read_text_or_note(p, notes))]
    stamp_files = [p.name for p in glob_files(claude / "rules", ("*.md", "**/*.md"))
                   if STAMP in read_text_or_note(p, notes)]

    learn_dates, learn_note = parse_applied_learnings(learnings) if learnings.is_file() else ([], None)
    if learn_note:
        notes.append(learn_note)

    info = {
        "repo": repo.name,
        "path": str(repo),
        "group": repo.parent.name,
        "has_log": log.is_file(),
        "schema": "-",
        "findings": 0,
        "resolutions": 0,
        "unprocessed": 0,
        "malformed": 0,
        "runs": 0,
        "last_review": None,
        "last_learn": learn_dates[-1] if learn_dates else None,
        "first_learn": learn_dates[0] if learn_dates else None,
        "learn_entries": len(learn_dates),
        "days_since_review": None,
        "days_since_learn": days_since(learn_dates[-1] if learn_dates else None, today),
        "review_skills": review_skills,
        "inj_files": sorted(set(inj_files)),
        "optimizer_stamp_files": sorted(set(stamp_files)),
        "clusters": [],
        "verdict": "NO-CAPTURE",
        "reason": "",
        "notes": notes,
    }

    if not log.is_file():
        info["reason"] = "no .claude/reviews/review-issues.jsonl"
        return info

    rows, malformed, read_error = read_jsonl(log)
    info["malformed"] = len(malformed)
    if read_error:
        notes.append(read_error)
        info["reason"] = read_error
        return info
    if malformed:
        notes.append(f"{len(malformed)} malformed line(s) skipped at {malformed[:5]}")
    if not rows:
        info["reason"] = "review log present but empty"
        notes.append("review log present but holds no rows")
        return info

    seen_schemas = {2 if row.get("schema") == 2 else 1 for row in rows}
    info["schema"] = {frozenset({1}): "v1", frozenset({2}): "v2"}.get(frozenset(seen_schemas), "MIXED")

    findings = [r for r in rows if not is_resolution(r)]
    resolutions = [r for r in rows if is_resolution(r)]
    info["findings"] = len(findings)
    info["resolutions"] = len(resolutions)
    info["runs"] = len({str(r.get("run_id")) for r in rows if r.get("run_id")})

    review_dates = sorted(d for d in (str(r.get("date") or "") for r in findings) if valid_date(d))
    info["last_review"] = review_dates[-1] if review_dates else None
    info["days_since_review"] = days_since(info["last_review"], today)
    if len(review_dates) < len(findings):
        notes.append(f"{len(findings) - len(review_dates)} finding row(s) carry no usable date")

    # Three ways a finding is already accounted for, in descending confidence: an explicit v2 back-link, the v1 in-place stamp a-self-learner wrote (548 such rows in one project's archive), and last the (category_hash, file) fold that a-self-learner falls back to when the link is absent. The fold carries the date condition a-self-learner/SKILL.md states, that the newest resolution sharing the pair is dated at or after the finding. Drop it and a finding logged after its own fix reads as processed, which silently erases re-emergence, the signal recurrence-detection.md calls the strongest evidence the log produces. The fold still over-counts where a row carries no usable date, so an unprocessed number is a floor, not an exact figure.
    resolved_ids = {str(r.get("resolves")) for r in resolutions if r.get("resolves")}
    newest_resolution: dict[tuple[str, str], str] = {}
    for row in resolutions:
        pair = (str(row.get("category_hash")), str(row.get("file")))
        day = str(row.get("date") or "")
        newest_resolution[pair] = max(newest_resolution.get(pair, ""), day if valid_date(day) else "")

    def processed(row: dict) -> bool:
        if str(row.get("finding_id")) in resolved_ids:
            return True
        if row.get("processed_by") or row.get("processed_date") or row.get("covered_by"):
            return True
        pair = (str(row.get("category_hash")), str(row.get("file")))
        if pair not in newest_resolution:
            return False
        found_on = str(row.get("date") or "")
        # An undated row on either side leaves the date condition untestable, so fall back to the bare pair match rather than inventing an order.
        if not newest_resolution[pair] or not valid_date(found_on):
            return True
        return found_on <= newest_resolution[pair]

    open_findings = [r for r in findings if not processed(r)]
    info["unprocessed"] = len(open_findings)

    by_category: dict[str, list[dict]] = defaultdict(list)
    for row in open_findings:
        by_category[str(row.get("category") or "(uncategorized)")].append(row)
    for category, group in by_category.items():
        group_dates = sorted({str(r.get("date")) for r in group if valid_date(str(r.get("date") or ""))})
        if len(group) >= CLUSTER_MIN_FINDINGS and len(group_dates) >= CLUSTER_MIN_DATES:
            info["clusters"].append({
                "category": category,
                "count": len(group),
                "dates": len(group_dates),
                "first": group_dates[0],
                "last": group_dates[-1],
            })
    info["clusters"].sort(key=lambda c: (-c["count"], c["category"]))

    if not info["clusters"]:
        info["verdict"] = "OK"
        info["reason"] = "no unprocessed cluster meets the 3-findings-over-2-dates bar"
    elif not learn_dates:
        info["verdict"] = "OVERDUE"
        info["reason"] = f"{len(info['clusters'])} qualifying cluster(s), never ran a-self-learner"
    elif info["last_review"] and info["last_learn"] < info["last_review"]:
        info["verdict"] = "OVERDUE"
        info["reason"] = (f"{len(info['clusters'])} qualifying cluster(s), findings through "
                          f"{info['last_review']} postdate the last learning on {info['last_learn']}")
    else:
        info["verdict"] = "OK"
        info["reason"] = f"last learning on {info['last_learn']} covers findings through {info['last_review']}"
    return info


def find_repos(root: Path) -> list[Path]:
    # A projects root often nests one level of grouping folders, but --root pointed straight at one group should still work rather than silently reporting nothing.
    seen: dict[Path, None] = {}
    for pattern in ("*", "*/*"):
        try:
            candidates = sorted(root.glob(pattern))
        except OSError:
            continue
        for path in candidates:
            if path.is_dir() and (path / ".claude").is_dir():
                seen.setdefault(path.resolve(), None)
    return list(seen)


def sort_key(info: dict) -> tuple:
    # Worst first. A repo that reviews but never learns outranks one that never captured; a repo with no log but a review skill installed is a live gap, while one with neither is simply not in the loop yet.
    if info["verdict"] == "OVERDUE":
        rank = 0
    elif info["verdict"] == "NO-CAPTURE":
        rank = 1 if info["review_skills"] else 3
    else:
        rank = 2
    return (rank, -info["unprocessed"], -(info["days_since_learn"] or 0), info["repo"].lower())


def flag(value) -> str:
    return "yes" if value else "no"


def print_table(reports: list[dict]) -> None:
    header = ("REPO", "VERDICT", "SCHEMA", "FIND", "RES", "UNPROC", "CLUST",
              "LAST-REVIEW", "LAST-LEARN", "AGE", "SKILL", "INJ", "STAMP")
    rows = [header]
    for r in reports:
        age = r["days_since_learn"]
        rows.append((
            r["repo"], r["verdict"], r["schema"], str(r["findings"]), str(r["resolutions"]),
            str(r["unprocessed"]), str(len(r["clusters"])),
            r["last_review"] or "-", r["last_learn"] or "never",
            f"{age}d" if age is not None else "-",
            flag(r["review_skills"]), flag(r["inj_files"]), flag(r["optimizer_stamp_files"]),
        ))
    widths = [max(len(row[i]) for row in rows) for i in range(len(header))]
    for index, row in enumerate(rows):
        print("  ".join(cell.ljust(widths[i]) for i, cell in enumerate(row)).rstrip())
        if index == 0:
            print("  ".join("-" * w for w in widths))
    print()
    print(f"{len(reports)} repo(s) with .claude/. UNPROC counts findings with no recorded resolution; CLUST counts "
          f"unprocessed categories with >={CLUSTER_MIN_FINDINGS} findings across >={CLUSTER_MIN_DATES} dates. "
          "AGE is days since the last applied learning.")
    overdue = [r for r in reports if r["verdict"] == "OVERDUE"]
    if overdue:
        print()
        print("OVERDUE:")
        for r in overdue:
            print(f"  {r['repo']}: {r['reason']}")
            for cluster in r["clusters"][:3]:
                print(f"      {cluster['count']:>4} x {cluster['category']} "
                      f"({cluster['dates']} dates, {cluster['first']} to {cluster['last']})")
    notes = [(r["repo"], n) for r in reports for n in r["notes"]]
    if notes:
        print()
        print("Notes:")
        for repo, note in notes:
            print(f"  {repo}: {note}")


def print_detail(r: dict) -> None:
    print(f"{r['repo']}  ({r['path']})")
    print(f"  verdict          {r['verdict']}  {r['reason']}")
    print(f"  capture schema   {r['schema']}")
    print(f"  findings         {r['findings']}  (resolution rows {r['resolutions']}, unprocessed {r['unprocessed']})")
    print(f"  runs             {r['runs']}")
    print(f"  malformed lines  {r['malformed']}")
    print(f"  last review      {r['last_review'] or '-'}"
          + (f"  ({r['days_since_review']}d ago)" if r["days_since_review"] is not None else ""))
    print(f"  last learning    {r['last_learn'] or 'never'}"
          + (f"  ({r['days_since_learn']}d ago)" if r["days_since_learn"] is not None else ""))
    print(f"  learn entries    {r['learn_entries']}"
          + (f"  ({r['first_learn']} to {r['last_learn']})" if r["learn_entries"] else ""))
    print(f"  review skills    {', '.join(r['review_skills']) or '(none)'}")
    print(f"  INJ checks in    {', '.join(r['inj_files']) or '(none found)'}")
    print(f"  optimizer stamp  {', '.join(r['optimizer_stamp_files']) or '(none found)'}")
    if r["clusters"]:
        print("  unprocessed clusters:")
        for cluster in r["clusters"]:
            print(f"      {cluster['count']:>4} x {cluster['category']} "
                  f"({cluster['dates']} dates, {cluster['first']} to {cluster['last']})")
    else:
        print("  unprocessed clusters: (none qualifying)")
    for note in r["notes"]:
        print(f"  note: {note}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Report which repos capture review findings and which never turn them into rules.")
    parser.add_argument("--root", default="~/Projects", help="directory to scan (default: ~/Projects)")
    parser.add_argument("--repo", help="inspect one repo by directory name")
    parser.add_argument("--json", action="store_true", dest="as_json", help="machine-readable output")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    today = date.today()
    if not root.is_dir():
        message = f"root not found: {root}"
        print(json.dumps({"error": message, "repos": []}, indent=2) if args.as_json else message)
        return 0

    repos = find_repos(root)
    if args.repo:
        wanted = args.repo.lower()
        repos = [p for p in repos if p.name.lower() == wanted]
        if not repos:
            message = f"no repo named {args.repo!r} with a .claude/ directory under {root}"
            print(json.dumps({"error": message, "repos": []}, indent=2) if args.as_json else message)
            return 0

    reports = sorted((scan_repo(repo, today) for repo in repos), key=sort_key)

    if args.as_json:
        print(json.dumps({"generated": today.isoformat(), "root": str(root), "repos": reports}, indent=2))
    elif args.repo:
        # --json already emits every match, so detail mode has to as well or two groups holding the same directory name make the two output modes disagree.
        for index, report in enumerate(reports):
            if index:
                print()
            print_detail(report)
    elif not reports:
        print(f"no repo with a .claude/ directory under {root}")
    else:
        print_table(reports)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
