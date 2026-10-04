#!/usr/bin/env python3
"""
parse_gsc.py: normalize Google Search Console exports into a findings report.

Deterministic pre-processor for the a-seo-gsc skill. Point it at one or more
GSC export zips (or a directory / loose CSVs) and it auto-detects each report
type, normalizes the numbers, and emits a structured set of findings: striking-
distance queries, zero-click high-impression queries, CTR outliers vs an
expected curve, parameter-duplicate cannibalization, coverage buckets, and a
categorized list of not-indexed URLs.

The model reads this output and layers strategy on top. Keeping the arithmetic
here makes the analysis fast, cheap, and repeatable across sites.

Pure standard library. No third-party deps. Cross-platform.

Usage:
    python3 parse_gsc.py <path...> [options]

    <path>              One or more GSC export .zip files, a directory
                        containing them (or extracted CSVs), or loose .csv files.

Options:
    --brand "a,b,c"     Comma-separated brand terms to split branded vs
                        non-branded queries (case-insensitive substring match).
    --min-impressions N Minimum impressions for a query to surface in findings
                        (default: 5).
    --json              Emit JSON instead of the markdown report.
    --out FILE          Write output to FILE instead of stdout.

Exit codes: 0 on success, 2 on "no recognizable GSC data found".
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import sys
import tempfile
import zipfile

# Rough organic CTR-by-position reference (desktop+mobile blended, 2023-2024
# industry averages). Used only to flag snippet underperformance, not as truth.
EXPECTED_CTR = {
    1: 0.275, 2: 0.150, 3: 0.100, 4: 0.070, 5: 0.055,
    6: 0.043, 7: 0.034, 8: 0.028, 9: 0.024, 10: 0.021,
}
PAGE2_CTR = 0.010  # positions 11-20, generic


def _num(s: str) -> float:
    """Parse a GSC numeric cell: '1.92%', '11.85', '1,234', '40%', '' -> float."""
    if s is None:
        return 0.0
    s = s.strip().replace("%", "")
    if not s:
        return 0.0
    # Thousands separators vs decimal comma: GSC uses '.' decimals, but be lenient.
    if s.count(",") == 1 and "." not in s:
        s = s.replace(",", ".")
    else:
        s = s.replace(",", "")
    try:
        return float(s)
    except ValueError:
        return 0.0


def _read_csv(text: str) -> tuple[list[str], list[list[str]]]:
    """Return (header, rows). Handles quoted multi-line cells (GSC query cells)."""
    reader = csv.reader(io.StringIO(text))
    rows = [r for r in reader if r]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def _find_col(header: list[str], *names: str) -> int:
    low = [h.strip().lower() for h in header]
    for name in names:
        n = name.lower()
        for i, h in enumerate(low):
            if h == n or h.startswith(n) or n in h:
                return i
    return -1


def _collect_csvs(paths: list[str], tmpdir: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return ({logical_name: csv_text}, {logical_name: source_export}) from zips/dirs/loose csvs.

    The second map records which export each CSV came from (the zip, or the
    directory holding it). Performance exports carry their settings in a
    sibling Filters.csv, so grouping by source is what lets us tell a Web
    export from an Image one before anything gets merged.
    """
    out: dict[str, str] = {}
    src: dict[str, str] = {}

    def add(name: str, text: str, source: str) -> None:
        base = os.path.basename(name)
        key = base
        n = 1
        while key in out:  # keep duplicates from multiple exports distinct
            n += 1
            key = f"{base}#{n}"
        out[key] = text
        src[key] = source

    def handle_file(path: str) -> None:
        if not os.path.exists(path):
            print(f"warning: path not found, skipping: {path}", file=sys.stderr)
            return
        low = path.lower()
        if low.endswith(".zip"):
            try:
                with zipfile.ZipFile(path) as z:
                    for info in z.namelist():
                        if info.lower().endswith(".csv"):
                            with z.open(info) as f:
                                add(info, f.read().decode("utf-8-sig", "replace"), path)
            except zipfile.BadZipFile:
                print(f"warning: not a valid zip, skipping: {path}", file=sys.stderr)
        elif low.endswith(".csv"):
            with open(path, encoding="utf-8-sig", errors="replace") as f:
                add(path, f.read(), os.path.dirname(os.path.abspath(path)))

    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for fn in files:
                    handle_file(os.path.join(root, fn))
        else:
            handle_file(p)
    return out, src


# Performance-report members. Coverage and drilldown CSVs are not in here, so
# they always survive the search-type filter below.
_PERF_FILES = {
    "queries.csv", "pages.csv", "countries.csv", "devices.csv",
    "dates.csv", "chart.csv", "filters.csv", "search appearance.csv",
    "pairs.csv",
}


def _basename_of(key: str) -> str:
    return key.split("#", 1)[0].lower()


def _search_types(csvs: dict[str, str], src: dict[str, str]) -> dict[str, str]:
    """Map source export -> declared search type, read from its Filters.csv."""
    types: dict[str, str] = {}
    for key, text in csvs.items():
        if _basename_of(key) != "filters.csv":
            continue
        _header, rows = _read_csv(text)
        for row in rows:
            if len(row) >= 2 and row[0].strip().lower() == "search type":
                types[src.get(key, "")] = row[1].strip().lower()
    return types


def _split_by_search_type(
    csvs: dict[str, str], src: dict[str, str], prefer: str
) -> tuple[dict[str, str], str, dict[str, int]]:
    """Keep one search type's performance data; drop the rest.

    Web and Image exports describe the same URLs from different indexes.
    Merging them double-counts every page and surfaces the duplicates as
    parameter cannibalization, which is an artifact rather than a finding.
    """
    types = _search_types(csvs, src)
    present = {t for t in types.values() if t}
    if len(present) <= 1:
        return csvs, (next(iter(present)) if present else ""), {}

    if prefer and prefer.lower() in present:
        keep = prefer.lower()
    elif "web" in present:
        keep = "web"
    else:
        keep = sorted(present)[0]

    kept: dict[str, str] = {}
    dropped: dict[str, int] = {}
    for key, text in csvs.items():
        t = types.get(src.get(key, ""))
        if t and t != keep and _basename_of(key) in _PERF_FILES:
            dropped[t] = dropped.get(t, 0) + 1
            continue
        kept[key] = text
    return kept, keep, dropped


def _classify_url(url: str) -> str:
    """Generic path-pattern bucket for a not-indexed URL (site-agnostic)."""
    u = url.lower()
    path = u.split("://", 1)[-1]
    path = "/" + path.split("/", 1)[1] if "/" in path else "/"
    if "?" in u:
        return "parameter-url"
    if any(seg in path for seg in ("/feed", "/rss", "/atom")) or path.endswith(".xml"):
        return "feed"
    if any(seg in path for seg in ("/visit", "/go/", "/out/", "/redirect", "/goto")):
        return "redirect-endpoint"
    if "/page/" in path or "/p/" in path.rstrip("/").rsplit("/", 1)[0] + "/":
        return "pagination"
    if any(seg in path for seg in ("/tag/", "/tags/", "/label/", "/topic/", "/topics/")):
        return "taxonomy-tag"
    if any(seg in path for seg in ("/category/", "/categories/", "/cat/", "/c/")):
        return "taxonomy-category"
    if any(seg in path for seg in ("/product/", "/products/", "/shop/", "/item/")):
        return "product"
    return "content-page"


class Report:
    def __init__(self) -> None:
        self.queries: list[dict] = []
        self.pages: list[dict] = []
        self.countries: list[dict] = []
        self.devices: list[dict] = []
        self.dates: list[dict] = []          # perf time series
        self.coverage_issues: list[dict] = []
        self.coverage_series: list[dict] = []  # indexed vs not-indexed over time
        self.not_indexed: list[dict] = []     # drilldown table
        self.pairs: list[dict] = []           # page+query rows (API only)
        self.drill_issue: str = ""


def _ingest(csvs: dict[str, str]) -> Report:
    r = Report()
    for name, text in csvs.items():
        header, rows = _read_csv(text)
        if not header:
            continue
        h = [c.strip().lower() for c in header]

        # --- Coverage drilldown table: URL,Last crawled ---
        if "url" in h and any("crawl" in c for c in h):
            ci = _find_col(header, "url")
            cc = _find_col(header, "last crawled", "crawled")
            for row in rows:
                if len(row) > ci and row[ci].strip():
                    r.not_indexed.append({
                        "url": row[ci].strip(),
                        "last_crawled": row[cc].strip() if cc >= 0 and len(row) > cc else "",
                    })
            continue

        # --- Coverage issue tables: Reason,Source,Validation,Pages ---
        if "reason" in h and "pages" in h:
            cr = _find_col(header, "reason")
            cp = _find_col(header, "pages")
            for row in rows:
                if len(row) > cr and row[cr].strip():
                    r.coverage_issues.append({
                        "reason": row[cr].strip(),
                        "pages": int(_num(row[cp])) if cp >= 0 and len(row) > cp else 0,
                    })
            continue

        # --- Coverage chart: Date,Not indexed,Indexed,Impressions ---
        if "date" in h and any("not indexed" in c for c in h) and any(c == "indexed" or c.endswith("indexed") for c in h):
            cn = _find_col(header, "not indexed")
            cidx = -1
            for i, c in enumerate(h):
                if c == "indexed" or (c.endswith("indexed") and "not" not in c):
                    cidx = i
                    break
            for row in rows:
                if len(row) <= cn or row[cn].strip() == "":
                    continue
                r.coverage_series.append({
                    "date": row[0].strip(),
                    "not_indexed": int(_num(row[cn])),
                    "indexed": int(_num(row[cidx])) if cidx >= 0 and len(row) > cidx else 0,
                })
            continue

        # --- Page+query pairs (API only; no GSC export has this shape) ---
        #
        # Checked BEFORE the generic performance branch on purpose. That branch
        # buckets on column 0, and a pairs file leads with Page, so it would be
        # merged into r.pages and double every page's clicks and impressions.
        if ("clicks" in h and "impressions" in h
                and any("quer" in c for c in h)
                and any(c.startswith("page") or c.startswith("url") for c in h)):
            cq = _find_col(header, "query")
            cu = _find_col(header, "page", "url")
            cc = _find_col(header, "clicks")
            cimp = _find_col(header, "impressions")
            cpos = _find_col(header, "position")
            for row in rows:
                if len(row) <= max(cq, cu) or not row[cq].strip() or not row[cu].strip():
                    continue
                r.pairs.append({
                    "query": row[cq].strip(),
                    "url": row[cu].strip(),
                    "clicks": int(_num(row[cc])) if len(row) > cc else 0,
                    "impressions": int(_num(row[cimp])) if len(row) > cimp else 0,
                    "position": _num(row[cpos]) if cpos >= 0 and len(row) > cpos else 0.0,
                })
            continue

        # --- Performance breakdowns: have Clicks + Impressions + Position ---
        if "clicks" in h and "impressions" in h and "position" in h:
            cc = _find_col(header, "clicks")
            cimp = _find_col(header, "impressions")
            cctr = _find_col(header, "ctr")
            cpos = _find_col(header, "position")
            dim = header[0].strip().lower()
            bucket = None
            label = "name"
            if "quer" in dim:
                bucket, label = r.queries, "query"
            elif "page" in dim or "url" in dim:
                bucket, label = r.pages, "url"
            elif "countr" in dim:
                bucket, label = r.countries, "country"
            elif "device" in dim:
                bucket, label = r.devices, "device"
            elif "date" in dim:
                bucket, label = r.dates, "date"
            else:
                continue
            for row in rows:
                if not row or not row[0].strip():
                    continue
                rec = {
                    label: row[0].strip(),
                    "clicks": int(_num(row[cc])) if len(row) > cc else 0,
                    "impressions": int(_num(row[cimp])) if len(row) > cimp else 0,
                    "ctr": _num(row[cctr]) / 100.0 if cctr >= 0 and len(row) > cctr else 0.0,
                    "position": _num(row[cpos]) if cpos >= 0 and len(row) > cpos else 0.0,
                }
                bucket.append(rec)
            continue
    return r


def _clean_url(url: str) -> str:
    return url.split("?", 1)[0].split("#", 1)[0]


def analyze(r: Report, brand: list[str], min_imp: int) -> dict:
    f: dict = {}

    # Baseline totals: prefer the date series (authoritative), else devices.
    if r.dates:
        tot_clicks = sum(d["clicks"] for d in r.dates)
        tot_imp = sum(d["impressions"] for d in r.dates)
    elif r.devices:
        tot_clicks = sum(d["clicks"] for d in r.devices)
        tot_imp = sum(d["impressions"] for d in r.devices)
    else:
        tot_clicks = sum(q["clicks"] for q in r.queries)
        tot_imp = sum(q["impressions"] for q in r.queries)
    wpos = (sum(q["position"] * q["impressions"] for q in r.queries) /
            sum(q["impressions"] for q in r.queries)) if r.queries else 0.0
    f["baseline"] = {
        "clicks": tot_clicks,
        "impressions": tot_imp,
        "ctr": (tot_clicks / tot_imp) if tot_imp else 0.0,
        "impression_weighted_position": round(wpos, 2),
        "queries_tracked": len(r.queries),
        "pages_tracked": len(r.pages),
    }

    # Branded vs non-branded
    if brand:
        bl = [b.lower() for b in brand if b.strip()]
        def is_brand(q: str) -> bool:
            ql = q.lower()
            return any(b in ql for b in bl)
        bq = [q for q in r.queries if is_brand(q["query"])]
        nbq = [q for q in r.queries if not is_brand(q["query"])]
        f["branded_split"] = {
            "branded": {"clicks": sum(q["clicks"] for q in bq), "impressions": sum(q["impressions"] for q in bq)},
            "non_branded": {"clicks": sum(q["clicks"] for q in nbq), "impressions": sum(q["impressions"] for q in nbq)},
        }

    # Striking distance: page-2 queries (pos 11-20) with real impressions.
    striking = sorted(
        [q for q in r.queries if 10.5 < q["position"] <= 20.5 and q["impressions"] >= min_imp],
        key=lambda q: -q["impressions"],
    )
    f["striking_distance"] = striking[:30]

    # Page-1 low CTR: pos <=10, impressions >= min, actual CTR far below expected.
    ctr_outliers = []
    for q in r.queries:
        if q["position"] <= 10.5 and q["impressions"] >= min_imp:
            exp = EXPECTED_CTR.get(round(q["position"]), PAGE2_CTR)
            if q["ctr"] < exp * 0.4:  # under 40% of expected = snippet/intent problem
                ctr_outliers.append({**q, "expected_ctr": round(exp, 3)})
    f["ctr_underperformers"] = sorted(ctr_outliers, key=lambda q: -q["impressions"])[:30]

    # Zero-click high-impression
    f["zero_click"] = sorted(
        [q for q in r.queries if q["clicks"] == 0 and q["impressions"] >= max(min_imp, 10)],
        key=lambda q: -q["impressions"],
    )[:30]

    # Parameter-duplicate cannibalization (same clean URL indexed under variants)
    groups: dict[str, list[dict]] = {}
    for p in r.pages:
        groups.setdefault(_clean_url(p["url"]), []).append(p)
    dup = []
    for clean, variants in groups.items():
        if len(variants) > 1:
            dup.append({
                "clean_url": clean,
                "variants": sorted(variants, key=lambda p: -p["impressions"]),
                "total_impressions": sum(v["impressions"] for v in variants),
            })
    f["param_cannibalization"] = sorted(dup, key=lambda d: -d["total_impressions"])

    # True query cannibalization: one query, several of your pages competing.
    #
    # Only possible from page+query pairs, which no GSC export contains. The
    # UI's own export lists queries and pages in separate tables, so this
    # question was unanswerable until the API path existed. Absent pairs, the
    # key is left out entirely rather than reported as "none found", because
    # nothing was looked at and saying otherwise would read as a clean bill.
    if r.pairs:
        by_query: dict[str, list[dict]] = {}
        for row in r.pairs:
            by_query.setdefault(row["query"], []).append(row)
        cannibal = []
        for query, hits in by_query.items():
            total = sum(x["impressions"] for x in hits)
            # Rank by impressions, but report position too: the actionable
            # signal is a mismatch, where the page Google shows most often is
            # not the page that ranks best for the query.
            ranked = sorted(hits, key=lambda x: -x["impressions"])
            rivals = [x for x in ranked if x["impressions"] >= min_imp]
            if len(rivals) < 2 or total <= 0:
                continue
            # A runner-up holding a token share is noise, not competition.
            if rivals[1]["impressions"] / total < 0.20:
                continue
            # Over rivals, NOT over hits. Picking the best position from every
            # page for the query lets a page below the impression floor win,
            # and the report then names a URL that does not appear in its own
            # evidence list while the listed numbers contradict the claim.
            best = min(rivals, key=lambda x: x["position"] if x["position"] else 999)
            cannibal.append({
                "query": query,
                "total_impressions": total,
                "rival_impressions": sum(x["impressions"] for x in rivals),
                "pages_seen": len(hits),
                "total_clicks": sum(x["clicks"] for x in hits),
                "pages": rivals,
                "most_shown": ranked[0]["url"],
                "best_ranked": best["url"],
                "split_mismatch": best["url"] != ranked[0]["url"],
            })
        f["query_cannibalization"] = sorted(
            cannibal, key=lambda d: -d["total_impressions"]
        )[:30]
        f["pairs_seen"] = len(r.pairs)

    # Concentration: what share of impressions does the top page hold?
    if r.pages:
        top = max(r.pages, key=lambda p: p["impressions"])
        f["concentration"] = {
            "top_page": top["url"],
            "top_page_impressions": top["impressions"],
            "share_of_total": round(top["impressions"] / tot_imp, 3) if tot_imp else 0.0,
        }

    # Coverage
    if r.coverage_issues:
        buckets = {}
        for c in r.coverage_issues:
            buckets[c["reason"]] = buckets.get(c["reason"], 0) + c["pages"]
        f["coverage_issues"] = buckets
    if r.coverage_series:
        first = r.coverage_series[0]
        last = r.coverage_series[-1]
        f["coverage_trend"] = {
            "first": first, "last": last,
            "indexed_delta": last["indexed"] - first["indexed"],
            "not_indexed_delta": last["not_indexed"] - first["not_indexed"],
            "diagnosis": (
                "index-starvation (more pages excluded than indexed)"
                if last["not_indexed"] > last["indexed"]
                else "index-bloat risk" if last["not_indexed"] > last["indexed"] * 0.5
                else "healthy"
            ),
        }

    # Not-indexed URL categorization
    if r.not_indexed:
        cats: dict[str, list[str]] = {}
        for u in r.not_indexed:
            cats.setdefault(_classify_url(u["url"]), []).append(u["url"])
        f["not_indexed"] = {
            "issue": r.drill_issue or "not indexed",
            "total": len(r.not_indexed),
            "by_category": {k: {"count": len(v), "sample": v[:12]} for k, v in
                            sorted(cats.items(), key=lambda kv: -len(kv[1]))},
        }
    return f


def _pct(x: float) -> str:
    return f"{x * 100:.2f}%"


def to_markdown(f: dict) -> str:
    o: list[str] = ["# GSC parsed findings", ""]
    b = f["baseline"]
    o += [
        "## Baseline",
        f"- Clicks: **{b['clicks']}**  |  Impressions: **{b['impressions']}**  |  CTR: **{_pct(b['ctr'])}**",
        f"- Impression-weighted avg position: **{b['impression_weighted_position']}**",
        f"- Queries tracked: {b['queries_tracked']}  |  Pages tracked: {b['pages_tracked']}",
        "",
    ]
    if "branded_split" in f:
        bs = f["branded_split"]
        o += [
            "## Branded vs non-branded",
            f"- Branded: {bs['branded']['clicks']} clicks / {bs['branded']['impressions']} impr",
            f"- Non-branded: {bs['non_branded']['clicks']} clicks / {bs['non_branded']['impressions']} impr",
            "",
        ]
    if f.get("concentration"):
        c = f["concentration"]
        o += ["## Concentration",
              f"- Top page holds **{_pct(c['share_of_total'])}** of all impressions: `{c['top_page']}` ({c['top_page_impressions']} impr)",
              ""]

    def qtable(title: str, rows: list[dict], extra: str = "") -> None:
        nonlocal o
        o.append(f"## {title}")
        if not rows:
            o.extend(["_none_", ""])
            return
        o.append(f"| query | clicks | impr | CTR | pos |{' expected CTR |' if extra=='exp' else ''}")
        o.append(f"|---|--:|--:|--:|--:|{'--:|' if extra=='exp' else ''}")
        for q in rows:
            line = f"| {q['query']} | {q['clicks']} | {q['impressions']} | {_pct(q['ctr'])} | {q['position']:.1f} |"
            if extra == "exp":
                line += f" {_pct(q.get('expected_ctr', 0))} |"
            o.append(line)
        o.append("")

    qtable("Striking distance (pos 11-20, quick wins)", f.get("striking_distance", []))
    qtable("Page-1 CTR underperformers (snippet/intent problem)", f.get("ctr_underperformers", []), "exp")
    qtable("Zero-click high-impression queries", f.get("zero_click", []))

    o.append("## Parameter-duplicate cannibalization")
    if f.get("param_cannibalization"):
        for d in f["param_cannibalization"]:
            o.append(f"- `{d['clean_url']}`: {len(d['variants'])} indexed variants, {d['total_impressions']} impr total")
            for v in d["variants"]:
                o.append(f"    - {v['impressions']} impr, pos {v['position']:.1f}: `{v['url']}`")
    else:
        o.append("_none detected_")
    o.append("")

    if "query_cannibalization" in f:
        o.append("## Query cannibalization (from page+query pairs)")
        o.append(f"_{f.get('pairs_seen', 0)} page+query rows analysed._")
        if f["query_cannibalization"]:
            for d in f["query_cannibalization"]:
                flag = "  **position/impression mismatch**" if d["split_mismatch"] else ""
                tail = ""
                if d.get("pages_seen", 0) > len(d["pages"]):
                    tail = (f", {d['pages_seen'] - len(d['pages'])} more below the "
                            f"impression floor")
                o.append(
                    f"- `{d['query']}`: {len(d['pages'])} pages competing on "
                    f"{d.get('rival_impressions', d['total_impressions'])} of "
                    f"{d['total_impressions']} impr, {d['total_clicks']} clicks{tail}{flag}"
                )
                for pg in d["pages"]:
                    o.append(
                        f"    - {pg['impressions']} impr, {pg['clicks']} clicks, "
                        f"pos {pg['position']:.1f}: `{pg['url']}`"
                    )
                if d["split_mismatch"]:
                    o.append(
                        f"    - Google shows `{d['most_shown']}` most, but "
                        f"`{d['best_ranked']}` ranks better."
                    )
        else:
            o.append("_none detected_")
        o.append("")

    if "coverage_issues" in f:
        o.append("## Coverage issues")
        for reason, n in sorted(f["coverage_issues"].items(), key=lambda kv: -kv[1]):
            o.append(f"- **{n}**: {reason}")
        o.append("")
    if "coverage_trend" in f:
        t = f["coverage_trend"]
        o += ["## Coverage trend",
              f"- {t['first']['date']}: {t['first']['indexed']} indexed / {t['first']['not_indexed']} not indexed",
              f"- {t['last']['date']}: {t['last']['indexed']} indexed / {t['last']['not_indexed']} not indexed",
              f"- Diagnosis: **{t['diagnosis']}**", ""]
    if "not_indexed" in f:
        ni = f["not_indexed"]
        o.append(f"## Not-indexed URLs ({ni['total']} total)")
        for cat, d in ni["by_category"].items():
            o.append(f"### {cat} ({d['count']})")
            for u in d["sample"]:
                o.append(f"- {u}")
            if d["count"] > len(d["sample"]):
                o.append(f"- … +{d['count'] - len(d['sample'])} more")
            o.append("")
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description="Normalize GSC exports into findings.")
    ap.add_argument("paths", nargs="+")
    ap.add_argument("--brand", default="")
    ap.add_argument("--min-impressions", type=int, default=5)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--out", default="")
    ap.add_argument(
        "--search-type",
        default="web",
        help="which search type to parse when the paths hold more than one "
             "(web, image, video, news). Default web.",
    )
    args = ap.parse_args()

    with tempfile.TemporaryDirectory() as tmp:
        csvs, sources = _collect_csvs(args.paths, tmp)
    if not csvs:
        print("No CSV files found in the given paths.", file=sys.stderr)
        return 2

    csvs, kept_type, dropped = _split_by_search_type(csvs, sources, args.search_type)
    if dropped:
        others = ", ".join(f"{t} ({n} files)" for t, n in sorted(dropped.items()))
        print(
            f"note: the given paths hold more than one search type. Parsed '{kept_type}' "
            f"and ignored {others}. Merging them would double-count every page. "
            f"Re-run with --search-type to read another one.",
            file=sys.stderr,
        )
    elif kept_type:
        print(f"note: search type '{kept_type}'.", file=sys.stderr)

    report = _ingest(csvs)
    if not (report.queries or report.pages or report.coverage_issues or report.not_indexed):
        print("No recognizable GSC performance or coverage data found.", file=sys.stderr)
        return 2

    brand = [b for b in args.brand.split(",") if b.strip()]
    findings = analyze(report, brand, args.min_impressions)
    out = json.dumps(findings, indent=2, ensure_ascii=False) if args.json else to_markdown(findings)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(out + "\n")
        print(f"Wrote {args.out}")
    else:
        print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
