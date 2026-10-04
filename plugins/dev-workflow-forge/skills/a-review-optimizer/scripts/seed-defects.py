#!/usr/bin/env python3
"""Seeded-defect benchmark harness for a-review-optimizer.

Plants known defects from benchmarks/corpus.json onto a scratch branch, then scores a
review skill's findings against the manifest. Standard library only, no venv, no install.

Runbook: skills/a-review-optimizer/references/benchmark.md
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import subprocess
import sys
from pathlib import Path

SEVERITY_ORDER = ["critical", "high", "medium", "low", "info"]
SEED_GAP = 8  # blank lines between planted seeds; caps usable --tolerance at SEED_GAP // 2
def _default_corpus() -> Path:
    """Find corpus.json in either layout this script ships in.

    Standalone it sits in scripts/ beside a skills/ tree; bundled into a plugin it
    sits in the skill's own scripts/ with benchmarks/ as a sibling. Checking both
    beats hardcoding one and failing silently in the other.
    """
    here = Path(__file__).resolve().parent
    for cand in (here.parent / "benchmarks" / "corpus.json",
                 here.parent / "skills" / "a-review-optimizer" / "benchmarks" / "corpus.json"):
        if cand.is_file():
            return cand
    return here.parent / "skills" / "a-review-optimizer" / "benchmarks" / "corpus.json"


DEFAULT_CORPUS = _default_corpus()
STATE_NAME = "seed-defects-state.json"
COMMIT_PREFIX = "seed-defect:"
DEFAULT_SCRATCH_PREFIX = "benchmark/"

# A branch nobody should ever wake up to find mutated, prefix match or not.
PROTECTED_BRANCHES = {"main", "master", "develop", "trunk", "production", "release", "stable"}


class Refused(Exception):
    """A guard said no. Never caught internally; it aborts the run."""


def git(repo: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), *args],
        capture_output=True, text=True,
    )
    if check and proc.returncode != 0:
        raise Refused(f"git {' '.join(args)} failed: {proc.stderr.strip() or proc.stdout.strip()}")
    return proc.stdout.strip()


def repo_state(repo: Path) -> dict:
    if not (repo / ".git").exists() and git(repo, "rev-parse", "--is-inside-work-tree", check=False) != "true":
        raise Refused(f"{repo} is not a git working tree")
    git_dir = Path(git(repo, "rev-parse", "--absolute-git-dir"))
    common_dir = Path(git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    branch = git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    return {
        "repo": str(repo),
        "git_dir": str(git_dir),
        "branch": branch,
        "detached": branch == "HEAD",
        "linked_worktree": git_dir != common_dir,
        "dirty": bool(git(repo, "status", "--porcelain")),
        "head": git(repo, "rev-parse", "HEAD"),
    }


def guard_scratch(st: dict, prefix: str) -> None:
    """Planting into real code is the one unacceptable failure of this tool, so the
    location check runs before anything is read, let alone written."""
    if st["detached"]:
        raise Refused("REFUSED: HEAD is detached. Check out a scratch branch first.")
    if st["branch"] in PROTECTED_BRANCHES:
        raise Refused(
            f"REFUSED: branch {st['branch']!r} is protected. "
            f"Plant only on a branch named {prefix}* or inside a linked worktree."
        )
    if st["branch"].startswith(prefix):
        return
    if st["linked_worktree"]:
        return
    raise Refused(
        f"REFUSED: branch {st['branch']!r} is neither a scratch branch (prefix {prefix!r}) "
        f"nor a linked git worktree. Run: git switch -c {prefix}round-1"
    )


def guard_clean(st: dict) -> None:
    if st["dirty"]:
        raise Refused(
            "REFUSED: working tree is dirty. Commit or stash first, otherwise restore "
            "cannot tell your work from the planted defects."
        )


def state_path(st: dict) -> Path:
    # .git/ is never tracked and never shows as dirty, and a throwaway worktree takes it
    # with it when removed, so state cannot outlive the tree it describes.
    return Path(st["git_dir"]) / STATE_NAME


def load_corpus(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise Refused(f"corpus not found: {path}")


def select(corpus: dict, stack: str | None, ids: str | None) -> list[dict]:
    defects = corpus["defects"]
    if stack:
        known = sorted({d["stack"] for d in defects if d.get("stack")})
        if stack not in known:
            raise Refused(
                f"no defects for stack {stack!r}. This corpus has: "
                + (", ".join(known) if known else "none")
                + ". Build one for your own stack with --build-corpus."
            )
        defects = [d for d in defects if d["stack"] == stack]
    if ids:
        wanted = [i.strip() for i in ids.split(",") if i.strip()]
        by_id = {d["id"]: d for d in corpus["defects"]}
        missing = [i for i in wanted if i not in by_id]
        if missing:
            raise Refused(f"unknown defect ids: {', '.join(missing)}")
        defects = [by_id[i] for i in wanted]
    if not defects:
        raise Refused("no defects selected")
    return defects


def cmd_list(args) -> int:
    corpus = load_corpus(Path(args.corpus))
    defects = select(corpus, args.stack, args.ids)
    src = corpus.get("sources") or {}
    # sources carries anonymous counts only: a corpus travels, and a defect list
    # naming real files in real sites is not something to hand around.
    scanned = src.get("rows_read", 0) if isinstance(src, dict) else sum(s.get("rows", 0) for s in src)
    print(f"{scanned} source findings scanned, {len(corpus['defects'])} in corpus, {len(defects)} selected\n")
    hdr = f"{'ID':7} {'STACK':7} {'SEV':6} {'DIMENSION':13} {'EXT':5} {'RECUR':11} CATEGORY"
    print(hdr)
    print("-" * len(hdr))
    for d in defects:
        r = d["recurrence"]
        recur = f"{r['findings']}f/{r['files']}p/{r['run_dates']}d"
        print(f"{d['id']:7} {d['stack']:7} {d['severity']:6} {d['dimension']:13} {d['target_ext']:5} {recur:11} {d['category']}")
    if args.verbose:
        for d in defects:
            print(f"\n--- {d['id']} {d['category']}")
            # source is optional: a corpus that travels carries recurrence counts
            # only, with no project, path, line or date to attribute.
            src = d.get("source")
            if src:
                print(f"    from {src['project']} {src['file']}:{src['line']} ({src['date']})")
                print(f"    {src['message']}")
            for i, line in enumerate(d["seed"]["snippet"], 1):
                mark = ">>" if i == d["seed"]["defect_line"] else "  "
                print(f"    {mark} {line}")
    print("\nrecur = real findings / distinct files / distinct run dates in the source logs (whitelisted rows excluded)")
    return 0


def inside_repo(repo: Path, p: Path) -> Path:
    """Repo-relative path, or a refusal. Resolve first, because PurePath.relative_to is
    lexical: '/repo/../elsewhere/x.php'.relative_to('/repo') succeeds and hands back
    '../elsewhere/x.php', a path the tool would then happily write to."""
    real = p.resolve()
    try:
        return real.relative_to(repo.resolve())
    except ValueError:
        raise Refused(f"REFUSED: target {p} resolves to {real}, outside {repo}")


def resolve_targets(repo: Path, targets: list[str]) -> dict:
    by_ext: dict[str, list[Path]] = {}
    for t in targets:
        p = Path(t).resolve() if Path(t).is_absolute() else (repo / t).resolve()
        inside_repo(repo, p)
        if not p.is_file():
            raise Refused(f"target not found: {t}")
        by_ext.setdefault(p.suffix, []).append(p)
    return by_ext


def cmd_plant(args) -> int:
    repo = Path(args.repo).resolve()
    st = repo_state(repo)
    guard_scratch(st, args.scratch_prefix)
    guard_clean(st)

    sp = state_path(st)
    if sp.exists():
        raise Refused(f"REFUSED: {sp} already exists. Run --restore before planting again.")

    corpus = load_corpus(Path(args.corpus))
    defects = select(corpus, args.stack, args.ids)
    by_ext = resolve_targets(repo, args.target)

    base = st["head"]
    planted, skipped = [], []
    cursor = {ext: 0 for ext in by_ext}

    for d in defects:
        ext = d["target_ext"]
        if ext not in by_ext:
            skipped.append({"id": d["id"], "reason": f"no --target with extension {ext}"})
            continue
        pool = by_ext[ext]
        target = pool[cursor[ext] % len(pool)]
        cursor[ext] += 1

        # Containment is re-proved here, before the first byte is written, so a refusal
        # leaves nothing on disk to undo.
        rel = str(inside_repo(repo, target))

        text = target.read_text(encoding="utf-8")
        if text and not text.endswith("\n"):
            text += "\n"
        # SEED_GAP blank lines between seeds. The scorer clamps each seed's match
        # window to the midpoint of this gap so a finding is credited to the right
        # defect, which means the gap, not --tolerance, sets how far a window can
        # actually reach: usable tolerance is SEED_GAP // 2. At the old gap of 2 the
        # knob was inert for every interior seed.
        start = text.count("\n") + SEED_GAP + 1
        block = "\n" * SEED_GAP + "\n".join(d["seed"]["snippet"]) + "\n"
        target.write_text(text + block, encoding="utf-8")

        git(repo, "add", rel)
        git(repo, "commit", "-q", "-m", f"{COMMIT_PREFIX} {d['id']} {d['category']}")
        entry = {
            "id": d["id"], "category": d["category"], "severity": d["severity"],
            "dimension": d["dimension"], "stack": d["stack"], "file": rel,
            "start_line": start, "end_line": start + len(d["seed"]["snippet"]) - 1,
            "defect_line": start + d["seed"]["defect_line"] - 1,
            "commit": git(repo, "rev-parse", "HEAD"),
        }
        planted.append(entry)
        print(f"planted {d['id']:7} {d['category']:42} -> {rel}:{entry['defect_line']}")

    if not planted:
        raise Refused("nothing planted; every selected defect was skipped")

    sp.write_text(json.dumps({
        "schema": 1, "repo": str(repo), "branch": st["branch"], "base": base,
        "corpus": str(Path(args.corpus).resolve()), "planted": planted, "skipped": skipped,
    }, indent=2), encoding="utf-8")

    for s in skipped:
        print(f"SKIPPED {s['id']:7} {s['reason']}")
    print(f"\n{len(planted)} planted, {len(skipped)} skipped. base={base[:8]} state={sp}")
    return 0


def load_state(repo: Path) -> tuple[dict, dict, Path]:
    st = repo_state(repo)
    sp = state_path(st)
    if not sp.exists():
        raise Refused(f"no plant state at {sp}. Nothing planted in this working tree.")
    return st, json.loads(sp.read_text(encoding="utf-8")), sp


def cmd_verify(args) -> int:
    repo = Path(args.repo).resolve()
    _, state, _ = load_state(repo)
    corpus = load_corpus(Path(state["corpus"]))
    snippets = {d["id"]: d["seed"]["snippet"] for d in corpus["defects"]}

    bad = 0
    for e in state["planted"]:
        path = repo / e["file"]
        want = snippets[e["id"]]
        got = path.read_text(encoding="utf-8").split("\n")[e["start_line"] - 1:e["end_line"]] if path.is_file() else []
        ok = got == want
        bad += 0 if ok else 1
        print(f"{'PRESENT' if ok else 'MISSING'} {e['id']:7} {e['file']}:{e['start_line']}-{e['end_line']}")
    print(f"\n{len(state['planted']) - bad}/{len(state['planted'])} present")
    return 1 if bad else 0


FILE_KEYS = ("file", "path", "file_path", "filename")
LINE_KEYS = ("line", "line_number", "lineno", "start_line")
CAT_KEYS = ("category", "slug", "rule", "check", "check_id")


def read_findings(path: Path) -> list[dict]:
    # Mistyping the results path is the likeliest operator error in step 4 of the runbook,
    # so it gets the same clean refusal as every other bad input, not a traceback.
    try:
        raw = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise Refused(f"findings file not readable: {path}: {exc}")
    if not raw:
        return []
    items: list = []
    try:
        # A pretty-printed {"findings": [...]} has no object at column 0 past line 1, so a
        # line-start brace is the tell for JSONL whatever the file is named.
        if path.suffix == ".jsonl" or (not raw.startswith("[") and "\n{" in raw):
            for line in raw.split("\n"):
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        else:
            doc = json.loads(raw)
            if isinstance(doc, dict):
                for key in ("findings", "issues", "results"):
                    if isinstance(doc.get(key), list):
                        doc = doc[key]
                        break
                else:
                    raise Refused(f"{path}: object has no findings/issues/results list")
            items = doc
    except json.JSONDecodeError as exc:
        raise Refused(f"findings file is not valid JSON: {path}: {exc}")

    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        f = next((it[k] for k in FILE_KEYS if it.get(k)), None)
        line = next((it[k] for k in LINE_KEYS if it.get(k) is not None), 0)
        cat = next((it[k] for k in CAT_KEYS if it.get(k)), "")
        try:
            line = int(line)
        except (TypeError, ValueError):
            line = 0
        out.append({"file": str(f or ""), "line": line, "category": str(cat).strip().lower(),
                    "severity": str(it.get("severity", "")), "raw": it})
    return out


def same_file(finding_file: str, planted_file: str) -> bool:
    if not finding_file:
        return False
    a, b = finding_file.replace("\\", "/"), planted_file.replace("\\", "/")
    if a.startswith("./"):
        a = a[2:]
    if a == b or a.endswith("/" + b):
        return True
    # A review that reports absolute or bare filenames still has to match, but the
    # basename fallback is scoped to those two shapes: two same-named files in
    # different directories would otherwise collide into a false hit.
    if a.startswith("/") or "/" not in a:
        return Path(a).name == Path(b).name
    return False


def match_windows(planted: list[dict], tol: int) -> dict[int, tuple[int, int]]:
    """Per-entry line window, split at the midpoint of the gap between adjacent seeds in the
    same file. Without the split a raw +/-tol window reaches into the next seed's own lines and
    the greedy scorer credits its finding to the wrong defect.

    The clamp bounds the usable tolerance at SEED_GAP // 2 for interior seeds, so a --tolerance
    above that is silently capped rather than honoured. Widen SEED_GAP if a larger one is wanted."""
    win: dict[int, tuple[int, int]] = {}
    by_file: dict[str, list[int]] = {}
    for i, e in enumerate(planted):
        by_file.setdefault(e["file"], []).append(i)
    for idxs in by_file.values():
        idxs.sort(key=lambda i: planted[i]["start_line"])
        for n, i in enumerate(idxs):
            e = planted[i]
            lo, hi = e["start_line"] - tol, e["end_line"] + tol
            if n:
                prev = planted[idxs[n - 1]]
                lo = max(lo, (prev["end_line"] + e["start_line"]) // 2 + 1)
            if n + 1 < len(idxs):
                nxt = planted[idxs[n + 1]]
                hi = min(hi, (e["end_line"] + nxt["start_line"]) // 2)
            win[i] = (lo, hi)
    return win


def cmd_score(args) -> int:
    repo = Path(args.repo).resolve()
    _, state, _ = load_state(repo)
    findings = read_findings(Path(args.score))
    tol = args.tolerance
    need_cat = args.match == "file-line-category"
    windows = match_windows(state["planted"], tol)

    used: set[int] = set()
    rows = []
    for i, e in enumerate(state["planted"]):
        lo, hi = windows[i]
        hit = None
        for idx, f in enumerate(findings):
            if idx in used or not same_file(f["file"], e["file"]):
                continue
            if not (lo <= f["line"] <= hi):
                continue
            if need_cat and f["category"] != e["category"].lower():
                continue
            hit = idx
            break
        if hit is not None:
            used.add(hit)
        rows.append((e, hit))

    found = sum(1 for _, h in rows if h is not None)
    planted_n, reported_n = len(rows), len(findings)
    recall = found / planted_n if planted_n else 0.0
    precision = len(used) / reported_n if reported_n else 0.0

    print(f"repo={repo}  branch={state['branch']}  base={state['base'][:8]}")
    print(f"match: file + line within planted block +/-{tol}, split at the midpoint between adjacent seeds"
          + (" + category" if need_cat else " (category ignored)"))
    print()
    hdr = f"{'RESULT':7} {'ID':7} {'SEV':6} {'DIMENSION':13} {'CATEGORY':42} LOCATION"
    print(hdr)
    print("-" * len(hdr))
    for e, h in rows:
        loc = f"{e['file']}:{e['defect_line']}"
        note = f"   <- finding line {findings[h]['line']}" if h is not None else ""
        print(f"{'HIT' if h is not None else 'MISS':7} {e['id']:7} {e['severity']:6} {e['dimension']:13} {e['category']:42} {loc}{note}")

    def rollup(key):
        agg = {}
        for e, h in rows:
            got, tot = agg.get(e[key], (0, 0))
            agg[e[key]] = (got + (1 if h is not None else 0), tot + 1)
        return "  ".join(f"{k} {v[0]}/{v[1]}" for k, v in sorted(agg.items()))

    print()
    print(f"recall     {found}/{planted_n} = {recall:.2f}   planted defects the review found")
    print(f"precision  {len(used)}/{reported_n} = {precision:.2f}   reported findings that matched a planted defect")
    print(f"unmatched  {reported_n - len(used)} findings matched no planted defect")
    print(f"by severity   {rollup('severity')}")
    print(f"by dimension  {rollup('dimension')}")
    print()
    print("Unmatched findings are NOT automatically false positives: a scratch branch cut from")
    print("real code still carries real pre-existing defects. Treat precision as a signal only")
    print("when the review ran diff-scoped over the planted commits.")

    if args.out:
        Path(args.out).write_text(json.dumps({
            "repo": str(repo), "branch": state["branch"], "base": state["base"],
            "match": args.match, "tolerance": tol,
            "planted": planted_n, "found": found, "recall": round(recall, 4),
            "reported": reported_n, "matched": len(used), "precision": round(precision, 4),
            "results": [{"id": e["id"], "category": e["category"], "severity": e["severity"],
                         "dimension": e["dimension"], "file": e["file"],
                         "defect_line": e["defect_line"], "hit": h is not None} for e, h in rows],
        }, indent=2), encoding="utf-8")
        print(f"\nwrote {args.out}")
    return 0


def cmd_restore(args) -> int:
    repo = Path(args.repo).resolve()
    st, state, sp = load_state(repo)
    guard_clean(st)

    log = git(repo, "log", "--format=%H %s", f"{state['base']}..HEAD")
    extra = [l for l in log.split("\n") if l and not l.split(" ", 1)[1].startswith(COMMIT_PREFIX)]
    if extra:
        raise Refused(
            "REFUSED: commits that are not ours sit on top of the planted ones:\n  "
            + "\n  ".join(extra) + "\nMove them off this branch first; restore would discard them."
        )

    git(repo, "reset", "--hard", state["base"])
    sp.unlink()
    print(f"restored {repo} to {state['base'][:8]}, removed {sp}")
    return 0



def cmd_build_corpus(args) -> int:
    """Mine a repo's own review log into a starter corpus.

    The shipped corpus is deliberately small and carries no provenance, because a
    corpus travels between machines and people, and a defect list naming real
    files in real sites is not something to hand around. It is also the wrong
    corpus for anyone else: a benchmark is only meaningful when it seeds the
    defects THIS codebase actually keeps producing.

    So this reads `.claude/reviews/review-issues.jsonl`, groups confirmed findings
    by category, keeps the patterns that recurred across several files, and emits
    entries with the recurrence evidence but no project, path, line or date. The
    `seed` snippet is left blank on purpose: only a human who knows the stack can
    write a defect that looks like it belongs in this code, and an invented one
    measures nothing.
    """
    repo = Path(args.repo).resolve()
    log = repo / ".claude" / "reviews" / "review-issues.jsonl"
    if not log.is_file():
        raise Refused(f"no review log at {log}. Capture findings first; there is nothing to mine.")

    rows, malformed = [], 0
    for line in log.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            malformed += 1

    findings = [r for r in rows
                if r.get("type", "finding") == "finding"
                and r.get("disposition", "confirmed") != "dismissed"
                and r.get("category")]
    if not findings:
        raise Refused("the log has no confirmed findings to mine")

    by_cat: dict[str, list[dict]] = {}
    for r in findings:
        by_cat.setdefault(r["category"], []).append(r)

    defects, skipped = [], 0
    for cat, group in sorted(by_cat.items(), key=lambda kv: -len(kv[1])):
        files = {g.get("file") for g in group if g.get("file")}
        dates = {g.get("date") for g in group if g.get("date")}
        if len(files) < args.min_recurrence:
            skipped += 1
            continue
        worst = min(group, key=lambda g: SEVERITY_ORDER.index(g.get("severity", "low"))
                    if g.get("severity") in SEVERITY_ORDER else len(SEVERITY_ORDER))
        exts = collections.Counter(Path(g["file"]).suffix for g in group if g.get("file"))
        defects.append({
            "id": f"gen-{len(defects) + 1:02d}",
            "stack": "",                      # you name it: the harness matches --target on target_ext
            "category": cat,
            "severity": worst.get("severity", "medium"),
            "dimension": worst.get("dimension", "quality"),
            "target_ext": exts.most_common(1)[0][0] if exts else "",
            "recurrence": {"findings": len(group), "files": len(files), "run_dates": len(dates)},
            "description": "",               # one line, in your own words
            "seed": {"mode": "append", "snippet": []},
        })

    out = Path(args.out) if args.out else repo / ".claude" / "reviews" / "corpus-draft.json"
    doc = {
        "schema": 1,
        "purpose": ("Starter corpus mined from this project's own review log. Fill in `description` and "
                    "`seed.snippet` for each entry you keep, and delete the rest. An entry with an empty "
                    "snippet is skipped by --plant."),
        "sources": {"note": "Anonymous by construction: no project, path, line or date is recorded.",
                    "rows_read": len(rows), "confirmed_findings": len(findings)},
        "selection": (f"categories spanning >= {args.min_recurrence} distinct files; "
                      f"{skipped} single-file categories skipped"),
        "defects": defects,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")

    print(f"read {len(rows)} rows" + (f", {malformed} malformed" if malformed else ""))
    print(f"{len(findings)} confirmed findings in {len(by_cat)} categories")
    print(f"{len(defects)} recurring pattern(s) kept, {skipped} single-file skipped")
    print(f"\nwrote {out}")
    print("Next: for each entry you want, write a one-line description and a seed snippet")
    print("that looks like this codebase. Entries with an empty snippet are not planted.")
    return 0


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="seed-defects.py", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--list", action="store_true", help="show the corpus")
    mode.add_argument("--plant", action="store_true", help="apply defects to a scratch branch, one commit each")
    mode.add_argument("--verify", action="store_true", help="confirm every planted defect is still present")
    mode.add_argument("--score", metavar="RESULTS", help="score a review's findings (.json or .jsonl) against the manifest")
    mode.add_argument("--restore", action="store_true", help="reset the branch to the pre-plant commit")
    mode.add_argument("--build-corpus", action="store_true",
                      help="mine this repo's own review log into a starter corpus (writes --out, no provenance)")

    p.add_argument("--repo", default=".", help="working tree to act on (default: cwd)")
    p.add_argument("--corpus", default=str(DEFAULT_CORPUS), help="manifest path")
    # Deliberately not a choices= list. --build-corpus writes whatever stack the
    # user names, so hardcoding php/python here rejects the corpus this same
    # script just told them to build. Validated against the corpus instead.
    p.add_argument("--stack", help="restrict to one stack, as named in the corpus")
    p.add_argument("--ids", help="comma-separated defect ids")
    p.add_argument("--target", nargs="+", default=[], help="file(s) to plant into, matched by extension, one per file in turn")
    p.add_argument("--scratch-prefix", default=DEFAULT_SCRATCH_PREFIX, help="branch prefix the plant guard accepts")
    p.add_argument("--tolerance", type=int, default=3, help="line proximity for a match (default 3)")
    p.add_argument("--match", choices=["file-line-category", "file-line"], default="file-line-category")
    p.add_argument("--out", help="write the score as JSON, or the corpus for --build-corpus")
    p.add_argument("--min-recurrence", type=int, default=2,
                   help="--build-corpus: least distinct files a pattern must span to be worth seeding (default 2)")
    p.add_argument("-v", "--verbose", action="store_true", help="--list: also print snippets")
    args = p.parse_args(argv)

    if args.plant and not args.target:
        p.error("--plant needs at least one --target file")

    try:
        if args.list:
            return cmd_list(args)
        if args.build_corpus:
            return cmd_build_corpus(args)
        if args.plant:
            return cmd_plant(args)
        if args.verify:
            return cmd_verify(args)
        if args.score:
            return cmd_score(args)
        return cmd_restore(args)
    except Refused as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
