#!/usr/bin/env python3
"""Pull Search Console Performance data straight from the API, as CSVs.

Replaces the click-through-and-download-three-zips intake for the Performance
half of a-seo-gsc. Writes the same CSV shapes Google's own export produces, so
parse_gsc.py reads a fetched directory and a hand-exported zip identically and
the manual route stays a working fallback.

What this CANNOT fetch, because no API serves it:
  - the Index Coverage report (indexed vs not, reason breakdown, the
    "Crawled - currently not indexed" URL table). The URL Inspection API only
    answers for URLs you already hand it, so it can confirm a sitemap but never
    reveal bloat from URLs Google holds that you never submitted. Still a
    manual export.
  - the Links report. No API at all.

What it fetches that no export can give you:
  - page+query PAIRS, which is the only way to prove true cannibalization.
    Google's UI export lists queries and pages in separate tables, so the
    question "which of my pages compete for this query" has never been
    answerable from an export.
  - a second, immediately preceding window of equal length, so decay analysis
    works without anyone remembering to tick Compare in the UI.

Usage:
    python3 fetch_gsc.py --property sc-domain:example.com
    python3 fetch_gsc.py --property https://example.com/ --days 180 --out ./gsc
    python3 fetch_gsc.py --property sc-domain:example.com --no-compare

Auth is a Google service account with the Search Console API enabled, added as
a user on the property. Key file resolution, in order: --key, then
$GSC_SERVICE_ACCOUNT_JSON, then ~/.config/gsc/<property-slug>.json.

Standard library only, like parse_gsc.py. On Unix-like systems, RS256 is signed
by shelling out to openssl rather than pulling in google-auth or cryptography.
The private key is passed to openssl through a pipe file descriptor and never
written to disk.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import io
import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

API_BASE = "https://www.googleapis.com/webmasters/v3/sites/"
TOKEN_URI = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"

# Google's per-request cap. Paginated past with startRow.
ROW_LIMIT = 25000
# Runaway guard, not a real limit: 40 pages is a million rows.
MAX_PAGES = 40

# Search Console finishes processing a day about two days late, and a range
# ending today reads as a slump that is really just missing data.
LAG_DAYS = 3

# Each output CSV, as (filename, dimensions, first column header).
#
# Everything except dates.csv is aggregated over the whole range, one row per
# dimension value, because that is the shape Google's export has and the shape
# parse_gsc.py analyses. Asking for ['date', 'query'] instead would return one
# row per query PER DAY, and every query would then appear ninety times in the
# striking-distance table.
DATASETS = [
    ("dates.csv", ["date"], "Date"),
    ("queries.csv", ["query"], "Query"),
    ("pages.csv", ["page"], "Page"),
    ("countries.csv", ["country"], "Country"),
    ("devices.csv", ["device"], "Device"),
    ("pairs.csv", ["page", "query"], "Page"),
]


def eprint(*a: object) -> None:
    print(*a, file=sys.stderr)


# ---------------------------------------------------------------- auth


def load_key(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        key = json.load(f)
    for field in ("client_email", "private_key"):
        if not key.get(field):
            raise SystemExit(
                f"{path} has no {field}. Point --key at the JSON Google issued, unedited."
            )
    return key


def b64url(raw: bytes) -> bytes:
    import base64

    return base64.urlsafe_b64encode(raw).rstrip(b"=")


def require_supported_environment() -> None:
    if os.name == "nt":
        raise SystemExit(
            "The bundled API fetcher needs a Unix-like environment for secure "
            "key handoff. Use it in WSL, or use the manual Search Console export route."
        )


def sign_rs256(payload: bytes, private_key_pem: str) -> bytes:
    """Sign with openssl, handing it the key on a pipe rather than a temp file.

    A service-account private key written to /tmp, even at mode 600, outlives
    the process if anything crashes between write and unlink. The pipe dies
    with the process. 64KB is the default pipe buffer and a PEM is under 2KB,
    so writing the whole key before the child reads cannot deadlock.
    """
    require_supported_environment()
    read_fd, write_fd = os.pipe()
    try:
        os.write(write_fd, private_key_pem.encode())
    finally:
        os.close(write_fd)
    try:
        proc = subprocess.run(
            ["openssl", "dgst", "-sha256", "-sign", f"/dev/fd/{read_fd}"],
            input=payload,
            capture_output=True,
            pass_fds=(read_fd,),
        )
    except FileNotFoundError:
        raise SystemExit("openssl is not on PATH; it is needed to sign the assertion.")
    finally:
        os.close(read_fd)
    if proc.returncode != 0:
        raise SystemExit(
            "openssl rejected the private key while signing: "
            + proc.stderr.decode("utf-8", "replace")[:300]
        )
    return proc.stdout


def access_token(key: dict, scope: str = SCOPE) -> str:
    """Mint a bearer token. `scope` is a parameter so sibling fetchers
    (fetch_ga4.py) reuse this signing path instead of copying key handling."""
    now = int(dt.datetime.now(dt.timezone.utc).timestamp())
    header = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = b64url(
        json.dumps(
            {
                "iss": key["client_email"],
                "scope": scope,
                "aud": key.get("token_uri", TOKEN_URI),
                "iat": now,
                "exp": now + 3600,
            }
        ).encode()
    )
    signing_input = header + b"." + claims
    assertion = signing_input + b"." + b64url(sign_rs256(signing_input, key["private_key"]))

    body = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion.decode(),
        }
    ).encode()
    req = urllib.request.Request(
        key.get("token_uri", TOKEN_URI),
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            token = json.load(resp).get("access_token")
    except urllib.error.HTTPError as e:
        # The failure body can echo part of the assertion back, so truncate it.
        raise SystemExit(
            f"Token exchange failed (HTTP {e.code}): "
            + e.read().decode("utf-8", "replace")[:500]
        )
    if not token:
        raise SystemExit("Google returned no access_token for the service account assertion.")
    return token


# ---------------------------------------------------------------- fetch


def query_api(prop: str, token: str, dimensions: list[str], start: str, end: str,
              search_type: str) -> list[dict]:
    """One dataset, paginated to exhaustion."""
    url = API_BASE + urllib.parse.quote(prop, safe="") + "/searchAnalytics/query"
    rows: list[dict] = []
    for page in range(MAX_PAGES):
        payload = {
            "startDate": start,
            "endDate": end,
            "dimensions": dimensions,
            "rowLimit": ROW_LIMIT,
            "startRow": page * ROW_LIMIT,
            "type": search_type,
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode(),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                batch = json.load(resp).get("rows", [])
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "replace")[:600]
            raise SystemExit(
                f"Search Console returned HTTP {e.code} for {'+'.join(dimensions)} "
                f"{start}..{end}:\n{detail}"
            )
        rows.extend(batch)
        if len(batch) < ROW_LIMIT:
            break
    return rows


def write_csv(path: str, dimensions: list[str], first_header: str, rows: list[dict]) -> int:
    """Write one dataset in Google's own export shape.

    CTR is written as a PERCENTAGE NUMBER, not the 0-1 fraction the API
    returns, because a real export writes '1.92%' and parse_gsc.py divides the
    CTR column by 100. Getting this wrong understates every CTR by 100x and the
    CTR-underperformer analysis then flags the entire site.
    """
    headers = [first_header]
    if len(dimensions) > 1:
        headers.append("Query" if dimensions[1] == "query" else dimensions[1].title())
    headers += ["Clicks", "Impressions", "CTR", "Position"]

    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(headers)
        for r in rows:
            keys = r.get("keys", [])
            w.writerow(
                keys
                + [
                    int(r.get("clicks", 0)),
                    int(r.get("impressions", 0)),
                    f"{r.get('ctr', 0.0) * 100:.2f}%",
                    f"{r.get('position', 0.0):.2f}",
                ]
            )
    return len(rows)


def write_filters(path: str, search_type: str, start: str, end: str) -> None:
    """The sibling Filters.csv a real export carries.

    parse_gsc.py reads it to tell a Web export from an Image one before merging
    anything. Without it a fetched directory behaves differently from an
    exported one the moment the two are analysed together.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Filter", "Value"])
        w.writerow(["Search type", search_type.title()])
        w.writerow(["Date range", f"{start} to {end}"])


def fetch_window(prop: str, token: str, start: str, end: str, outdir: str,
                 search_type: str) -> dict[str, int]:
    os.makedirs(outdir, exist_ok=True)
    counts: dict[str, int] = {}
    for filename, dimensions, first_header in DATASETS:
        rows = query_api(prop, token, dimensions, start, end, search_type)
        counts[filename] = write_csv(
            os.path.join(outdir, filename), dimensions, first_header, rows
        )
    write_filters(os.path.join(outdir, "Filters.csv"), search_type, start, end)
    return counts


# ---------------------------------------------------------------- cli


def property_slug(prop: str) -> str:
    return (
        prop.replace("sc-domain:", "")
        .replace("https://", "")
        .replace("http://", "")
        .strip("/")
        .replace("/", "-")
        .replace(":", "-")
        .replace(".", "-")
    )


def resolve_key_path(explicit: str | None, prop: str) -> str:
    for candidate in (
        explicit,
        os.environ.get("GSC_SERVICE_ACCOUNT_JSON"),
        os.path.expanduser(f"~/.config/gsc/{property_slug(prop)}.json"),
    ):
        if candidate and os.path.isfile(candidate):
            return candidate
    raise SystemExit(
        "No service-account key found. Pass --key PATH, set "
        "GSC_SERVICE_ACCOUNT_JSON, or put the JSON at "
        f"~/.config/gsc/{property_slug(prop)}.json"
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Fetch Search Console Performance data as CSVs.")
    ap.add_argument("--property", required=True,
                    help="Property exactly as Search Console names it, e.g. sc-domain:example.com")
    ap.add_argument("--days", type=int, default=90, help="Window length in days (default 90)")
    ap.add_argument("--end", default="",
                    help=f"Last day, YYYY-MM-DD (default: today minus {LAG_DAYS} days)")
    ap.add_argument("--key", default=None, help="Service-account JSON path")
    ap.add_argument("--out", default="", help="Output directory (default: ./gsc-<slug>-<end>)")
    ap.add_argument("--search-type", default="web",
                    choices=["web", "image", "video", "news", "discover", "googleNews"])
    ap.add_argument("--no-compare", action="store_true",
                    help="Skip the preceding window; decay analysis then cannot run")
    args = ap.parse_args()
    require_supported_environment()

    if args.days < 1:
        raise SystemExit("--days must be at least 1")

    end = (
        dt.date.fromisoformat(args.end)
        if args.end
        else dt.date.today() - dt.timedelta(days=LAG_DAYS)
    )
    start = end - dt.timedelta(days=args.days - 1)
    prev_end = start - dt.timedelta(days=1)
    prev_start = prev_end - dt.timedelta(days=args.days - 1)

    outroot = args.out or f"./gsc-{property_slug(args.property)}-{end.isoformat()}"
    key = load_key(resolve_key_path(args.key, args.property))
    token = access_token(key)

    eprint(f"Property: {args.property}  ({key['client_email']})")

    windows = [("current", start, end)]
    if not args.no_compare:
        windows.append(("previous", prev_start, prev_end))

    for label, w_start, w_end in windows:
        outdir = os.path.join(outroot, label)
        counts = fetch_window(
            args.property, token, w_start.isoformat(), w_end.isoformat(),
            outdir, args.search_type,
        )
        summary = ", ".join(f"{n} {f.replace('.csv', '')}" for f, n in counts.items() if n)
        eprint(f"{label:8} {w_start} .. {w_end}  ->  {outdir}")
        eprint(f"         {summary or 'no rows returned'}")

    if all(
        os.path.getsize(os.path.join(outroot, w[0], "dates.csv")) < 40 for w in windows
    ):
        eprint("\nEvery dataset came back empty. Check the property name and that the "
               "service account is a user on it.")
        return 1

    print(outroot)
    eprint(f"\nNext: python3 parse_gsc.py {outroot}/current --brand \"...\"")
    if not args.no_compare:
        eprint(f"      and {outroot}/previous for the decay diff.")
    eprint("Coverage is not in here. Export Indexing -> Pages by hand; no API serves it.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
