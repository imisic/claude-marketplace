#!/usr/bin/env python3
"""
geo_probe.py - deterministic first phase of a GEO (AI search visibility) audit.

Fetches what the skill's technical checklist tells the model to inspect by hand on every
run: robots.txt (per AI crawler: allowed, disallowed, unmentioned; Sitemap and
Content-Signal lines), /llms.txt and /llms-full.txt (presence, size, first heading,
format), and each page's JSON-LD blocks plus the head tags AI extraction depends on.

Plain Python, standard library only. It reports evidence, never recommendations: the
model judges the candidate set in phase two and reads the pages only for what a probe
cannot see (wording, citability of the content itself).

Usage:
    python3 geo_probe.py <url-or-domain> [more page URLs...]
    python3 geo_probe.py <url> --json            # machine-readable, for phase two
    python3 geo_probe.py <url> --severity high   # report and gate on high only
    python3 geo_probe.py <url> --timeout 5       # per-request timeout in seconds

Exit code is 1 when any finding at or above --severity exists (default: low, so any
finding), 0 when the reported set is empty, 2 on bad arguments.
"""
import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser

# Source of truth for this list: references/crawler-reference.md, section 1 (quick
# reference table) and section 7 (other AI crawlers). The reference may not ship next to
# this script, so the tokens are embedded; update both together. Tier decides severity
# when a crawler is disallowed: "search" powers live answers (blocking removes the site
# from AI search), "training" only reduces long-term model familiarity, "other" is
# smaller platforms.
CRAWLERS = {
    "Googlebot": "search", "Bingbot": "search", "OAI-SearchBot": "search", "ChatGPT-User": "search",
    "Claude-SearchBot": "search", "Claude-User": "search", "PerplexityBot": "search",
    "GPTBot": "training", "ClaudeBot": "training", "Google-Extended": "training",
    "cohere-ai": "other", "Bytespider": "other", "Applebot": "other", "Applebot-Extended": "other",
    "FacebookBot": "other", "meta-externalagent": "other", "Amazonbot": "other", "Timesbot": "other",
}
TIER_SEVERITY = {"search": "high", "training": "medium", "other": "low"}

# Fields per @type, from references/technical-checklist.md section 3 templates and the
# entity checks in SKILL.md step 2. First tuple is required (missing = medium), second is
# recommended (missing = low). Aliases map subtypes onto the template they follow.
SCHEMA_FIELDS = {
    "Organization": (("name", "url"), ("logo", "sameAs", "address")),
    "WebSite": (("name", "url"), ()),
    "Article": (("headline", "author", "datePublished"), ("dateModified", "publisher")),
    "FAQPage": (("mainEntity",), ()),
    "Product": (("name", "offers"), ("description", "brand")),
    "HowTo": (("name", "step"), ()),
}
SCHEMA_ALIASES = {
    "LocalBusiness": "Organization", "ProfessionalService": "Organization", "Corporation": "Organization",
    "BlogPosting": "Article", "NewsArticle": "Article", "TechArticle": "Article",
}

SEVERITY_RANK = {"high": 0, "medium": 1, "low": 2}
# Below this many characters of visible body text, a homepage is almost certainly a JS
# shell (`<div id="root"></div>` plus a bundle). Heuristic: a legitimately terse landing
# page trips it too, which is why the finding says so in its evidence.
MIN_BODY_TEXT = 400
# shortcut: single attempt per URL, no retry or backoff. A flaky host shows up as
# `unreachable` and the model re-runs; retries would hide intermittent blocking, which is
# itself a finding for AI crawlers.
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36"
MAX_BODY_BYTES = 5 * 1024 * 1024  # shortcut: cap reads; nothing we inspect lives past 5 MB
SKIP_TEXT_TAGS = {"script", "style", "noscript", "template", "svg", "head"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source",
             "track", "wbr"}


# ---------------------------------------------------------------- fetching

def fetch(url, timeout):
    """One GET. Returns a dict with http_status, text, content_type, final_url, error.
    Network and HTTP errors land in the dict rather than raising, so every URL yields
    a finding instead of a crash."""
    out = {"url": url, "http_status": None, "text": "", "content_type": "", "final_url": url, "error": None}
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(MAX_BODY_BYTES)
            out["http_status"] = resp.status
            out["final_url"] = resp.geturl()
            out["content_type"] = resp.headers.get_content_type()
            charset = resp.headers.get_content_charset() or "utf-8"
    except urllib.error.HTTPError as e:
        # A 404 is an answer, not a failure: robots.txt or llms.txt may simply not exist.
        out["http_status"] = e.code
        try:
            raw = e.read(MAX_BODY_BYTES)
        except Exception:  # noqa: BLE001 - the status is what matters here
            raw = b""
        out["content_type"] = e.headers.get_content_type() if e.headers else ""
        charset = (e.headers.get_content_charset() if e.headers else None) or "utf-8"
    except Exception as e:  # noqa: BLE001 - URLError, socket.timeout, ssl errors, bad host
        out["error"] = f"{type(e).__name__}: {e}"
        return out
    try:
        out["text"] = raw.decode(charset, errors="replace")
    except LookupError:  # unknown charset label in the header
        out["text"] = raw.decode("utf-8", errors="replace")
    return out


def normalize_target(arg):
    """Accept `example.com`, `example.com/path` or a full URL. Returns (origin, page_url)."""
    if not re.match(r"^[a-z][a-z0-9+.-]*://", arg, re.I):
        arg = "https://" + arg
    parts = urllib.parse.urlsplit(arg)
    if not parts.netloc:
        raise ValueError(f"not a URL or domain: {arg}")
    origin = f"{parts.scheme}://{parts.netloc}"
    page = urllib.parse.urlunsplit((parts.scheme, parts.netloc, parts.path or "/", parts.query, ""))
    return origin, page


# ---------------------------------------------------------------- robots.txt

def parse_robots(text):
    """Groups of (agent tokens, rules) plus Sitemap and Content-Signal lines. Follows the
    REP grouping: consecutive User-agent lines share one rule block; a rule line closes
    the agent list. Comments and blank lines are ignored."""
    groups, sitemaps, signals = [], [], []
    agents, rules, collecting = [], [], False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key, val = key.strip().lower(), val.strip()
        if key == "user-agent":
            if not collecting:
                if agents:
                    groups.append((agents, rules))
                agents, rules = [], []
                collecting = True
            agents.append(val.lower())
            continue
        collecting = False
        if key in ("allow", "disallow") and agents:
            rules.append((key, val))
        elif key == "sitemap":
            sitemaps.append(val)
        elif key == "content-signal":
            signals.append({"agents": list(agents), "value": val, "line": line})
    if agents:
        groups.append((agents, rules))
    return groups, sitemaps, signals


def _rule_matches_root(path):
    # Empty Disallow means "nothing disallowed"; `*` and `$` are the only wildcards.
    if not path:
        return False
    pattern = "^" + re.escape(path).replace(r"\*", ".*")
    if pattern.endswith(r"\$"):
        pattern = pattern[:-2] + "$"
    return re.match(pattern, "/") is not None


def root_access(rules):
    """Longest-match evaluation of `/`; Allow wins ties, as Google and Bing do it."""
    best = None
    for kind, path in rules:
        if not _rule_matches_root(path):
            continue
        key = (len(path), kind == "allow")
        if best is None or key > best[0]:
            best = (key, kind, path)
    if best is None:
        return "allowed", None
    return ("allowed" if best[1] == "allow" else "disallowed"), f"{best[1].capitalize()}: {best[2]}"


def crawler_status(groups, token):
    own = [r for agents, rules in groups if token.lower() in agents for r in rules]
    if any(token.lower() in agents for agents, _ in groups):
        status, rule = root_access(own)
        return {"status": status, "via": token, "rule": rule}
    wildcard = [r for agents, rules in groups if "*" in agents for r in rules]
    if any("*" in agents for agents, _ in groups):
        status, rule = root_access(wildcard)
        return {"status": status, "via": "*", "rule": rule}
    return {"status": "unmentioned", "via": None, "rule": None}


def check_robots(origin, timeout, findings):
    url = origin + "/robots.txt"
    got = fetch(url, timeout)
    data = {"url": url, "http_status": got["http_status"], "status": "present", "sitemaps": [],
            "content_signals": [], "crawlers": {}}
    if got["error"]:
        data["status"] = "unreachable"
        findings.append(finding("robots-unreachable", "medium", url, got["error"]))
        return data
    if got["http_status"] == 404:
        data["status"] = "missing"
        findings.append(finding("robots-missing", "low", url, "HTTP 404: no robots.txt, every crawler is allowed by default"))
        return data
    if not 200 <= got["http_status"] < 300:
        data["status"] = "unreachable"
        findings.append(finding("robots-unreachable", "medium", url, f"HTTP {got['http_status']}"))
        return data
    if got["text"].lstrip()[:1] == "<":
        # Soft 404: a server that answers unknown paths with the homepage.
        data["status"] = "missing"
        findings.append(finding("robots-missing", "low", url, f"HTTP {got['http_status']} but the body is HTML, not a robots.txt"))
        return data

    groups, sitemaps, signals = parse_robots(got["text"])
    data["sitemaps"] = sitemaps
    data["content_signals"] = signals
    if not sitemaps:
        findings.append(finding("robots-no-sitemap", "medium", url, "no Sitemap: line"))
    for sig in signals:
        for part in re.split(r"[,\s]+", sig["value"]):
            name, _, val = part.partition("=")
            if val.lower() != "no":
                continue
            sev = "high" if name in ("ai-input", "search") else "low"
            findings.append(finding("robots-content-signal", sev, url,
                                    f"{sig['line']} (User-agent: {', '.join(sig['agents']) or '?'})"))
    for token, tier in CRAWLERS.items():
        st = crawler_status(groups, token)
        st["tier"] = tier
        data["crawlers"][token] = st
        if st["status"] == "disallowed":
            findings.append(finding("robots-disallow", TIER_SEVERITY[tier], url,
                                    f"{token} ({tier}) blocked by `{st['rule']}` under User-agent: {st['via']}"))
    return data


# ---------------------------------------------------------------- llms.txt

LINK_RE = re.compile(r"\[[^\]]+\]\(https?://[^)\s]+\)")


def llms_format_problems(text):
    """Split llms.txt problems into what Lighthouse fails and what is only this plugin's reading of the spec.

    The first list mirrors Lighthouse's llms-txt audit (core/audits/agentic/llms-txt.js): three regexes over
    the raw text, an H1 anywhere, at least one [text](url) link, at least 50 characters. Nothing else fails
    that audit. The second list is a heuristic from the llmstxt.org format, which puts the H1 first; Lighthouse
    does not check it, so it reports at low severity and never as a Lighthouse failure.
    """
    lighthouse = []
    if not re.search(r"^\s*#\s+.+", text, re.M):
        lighthouse.append("no H1 header (Lighthouse check)")
    if not re.search(r"\[.+\]\(.+\)", text):
        lighthouse.append("no markdown [text](url) links (Lighthouse check)")
    if len(text) < 50:
        lighthouse.append(f"only {len(text)} characters, under Lighthouse's 50 (Lighthouse check)")
    lines = [ln for ln in text.splitlines() if ln.strip()]
    spec = []
    if lines and not lines[0].lstrip().startswith("# "):
        spec.append("first non-blank line is not the H1 the llmstxt.org format puts first (plugin heuristic)")
    return lighthouse, spec


def check_llms(origin, name, timeout, findings):
    url = f"{origin}/{name}"
    got = fetch(url, timeout)
    data = {"url": url, "http_status": got["http_status"], "status": "absent", "size": 0,
            "first_heading": None, "h1_first": False, "link_count": 0}
    if got["error"]:
        data["status"] = "unreachable"
        findings.append(finding("llms-unreachable", "low", url, got["error"]))
        return data
    text = got["text"]
    ok = got["http_status"] and 200 <= got["http_status"] < 300
    is_html = text.lstrip()[:1] == "<" or "html" in got["content_type"]
    if not ok or is_html:
        # A 2xx with an HTML body is a server answering unknown paths with the homepage.
        why = f"HTTP {got['http_status']}" + (" but the body is HTML (soft 404)" if ok and is_html else "")
        findings.append(finding("llms-absent", "low", url, why))
        return data

    data["status"] = "present"
    data["size"] = len(text.encode("utf-8"))
    lines = [ln for ln in text.splitlines() if ln.strip()]
    heading = next((ln.strip() for ln in lines if ln.lstrip().startswith("#")), None)
    data["first_heading"] = heading
    data["h1_first"] = bool(lines) and lines[0].lstrip().startswith("# ")
    data["link_count"] = len(LINK_RE.findall(text))
    lighthouse, spec = llms_format_problems(text)
    if lighthouse:
        findings.append(finding("llms-format", "medium", url, "; ".join(lighthouse)))
    if spec:
        findings.append(finding("llms-spec", "low", url, "; ".join(spec)))
    return data


# ---------------------------------------------------------------- pages

class PageParser(HTMLParser):
    """Collects the head tags the checklist names, the JSON-LD blocks, and the visible
    body text length. Tolerant of unclosed tags the way browsers are."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = None
        self.meta_description = None
        self.canonical = None
        self.lang = None
        self.jsonld = []
        self.text_chars = 0
        self._stack = []
        self._title = None
        self._jsonld = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        a = {k.lower(): (v or "") for k, v in attrs}
        if tag == "html" and self.lang is None:
            self.lang = a.get("lang") or ""
        elif tag == "meta" and (a.get("name") or "").lower() == "description":
            self.meta_description = a.get("content", "")
        elif tag == "link" and "canonical" in (a.get("rel") or "").lower().split():
            self.canonical = a.get("href", "")
        if tag in VOID_TAGS:
            return
        self._stack.append(tag)
        if tag == "script" and "ld+json" in a.get("type", "").lower():
            self._jsonld = []
        elif tag == "title" and self.title is None:
            self._title = []

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in VOID_TAGS or tag not in self._stack:
            return
        if tag == "script" and self._jsonld is not None:
            self.jsonld.append("".join(self._jsonld))
            self._jsonld = None
        if tag == "title" and self._title is not None:
            self.title = re.sub(r"\s+", " ", "".join(self._title)).strip()
            self._title = None
        idx = len(self._stack) - 1 - self._stack[::-1].index(tag)
        del self._stack[idx:]

    def handle_data(self, data):
        if self._jsonld is not None:
            self._jsonld.append(data)
        elif self._title is not None:
            self._title.append(data)
        elif not (set(self._stack) & SKIP_TEXT_TAGS):
            self.text_chars += len(re.sub(r"\s+", " ", data).strip())


def flatten_jsonld(node):
    """Yield the page's own entities: top-level arrays and @graph members. Nested
    author/publisher/offers objects are references and stay out, otherwise an Article's
    publisher would be judged against the site-wide Organization template."""
    if isinstance(node, list):
        for item in node:
            yield from flatten_jsonld(item)
    elif isinstance(node, dict):
        if "@type" in node:
            yield node
        if "@graph" in node:
            yield from flatten_jsonld(node["@graph"])


def types_of(node):
    t = node.get("@type")
    return [t] if isinstance(t, str) else [x for x in (t or []) if isinstance(x, str)]


def check_schema_fields(node, url, findings):
    for t in types_of(node):
        canon = SCHEMA_ALIASES.get(t, t)
        if canon not in SCHEMA_FIELDS:
            continue
        required, recommended = SCHEMA_FIELDS[canon]
        for field in required:
            if not node.get(field):
                findings.append(finding("schema-field-missing", "medium", url, f"{t} without `{field}`"))
        for field in recommended:
            if not node.get(field):
                findings.append(finding("schema-field-missing", "low", url, f"{t} without `{field}`"))
        if canon == "FAQPage":
            items = node.get("mainEntity") or []
            items = items if isinstance(items, list) else [items]
            for i, q in enumerate(items):
                answer = q.get("acceptedAnswer") if isinstance(q, dict) else None
                if not isinstance(q, dict) or not q.get("name") or not (isinstance(answer, dict) and answer.get("text")):
                    findings.append(finding("schema-faq-item-incomplete", "medium", url,
                                            f"mainEntity[{i}] lacks name or acceptedAnswer.text"))


def check_page(url, timeout, findings):
    got = fetch(url, timeout)
    data = {"url": url, "final_url": got["final_url"], "http_status": got["http_status"], "title": None,
            "meta_description": None, "canonical": None, "lang": None, "text_chars": 0, "jsonld": []}
    if got["error"]:
        findings.append(finding("unreachable", "high", url, got["error"]))
        return data
    if not 200 <= got["http_status"] < 300:
        findings.append(finding("unreachable", "high", url, f"HTTP {got['http_status']}"))
        return data
    if not got["final_url"].startswith("https://"):
        findings.append(finding("not-https", "high", url, f"served at {got['final_url']}"))

    p = PageParser()
    p.feed(got["text"])
    p.close()
    data.update(title=p.title, meta_description=p.meta_description, canonical=p.canonical, lang=p.lang,
                text_chars=p.text_chars)

    if not p.title:
        findings.append(finding("title-missing", "medium", url, "no <title> text"))
    if not p.meta_description:
        findings.append(finding("meta-description-missing", "medium", url, "no <meta name=description>"))
    if not p.canonical:
        findings.append(finding("canonical-missing", "low", url, "no <link rel=canonical>"))
    if not p.lang:
        findings.append(finding("html-lang-missing", "low", url, "<html> has no lang attribute"))
    if p.text_chars < MIN_BODY_TEXT:
        findings.append(finding("thin-body-without-js", "high", url,
                                f"{p.text_chars} visible body chars without JS execution (heuristic, threshold {MIN_BODY_TEXT})"))

    types_seen = []
    for i, block in enumerate(p.jsonld):
        entry = {"index": i, "ok": False, "types": [], "error": None}
        try:
            parsed = json.loads(block)
        except json.JSONDecodeError as e:
            entry["error"] = str(e)
            snippet = re.sub(r"\s+", " ", block.strip())[:120] or "(empty block)"
            findings.append(finding("schema-parse-error", "high", url, f"block {i}: {e}; starts `{snippet}`"))
            data["jsonld"].append(entry)
            continue
        entry["ok"] = True
        for node in flatten_jsonld(parsed):
            entry["types"].extend(types_of(node))
            check_schema_fields(node, url, findings)
        types_seen.extend(entry["types"])
        data["jsonld"].append(entry)
    if not p.jsonld:
        findings.append(finding("schema-missing", "high", url, "no <script type=application/ld+json> blocks"))
    elif not any(SCHEMA_ALIASES.get(t, t) == "Organization" for t in types_seen):
        findings.append(finding("schema-no-organization", "low", url,
                                f"JSON-LD types present: {', '.join(sorted(set(types_seen))) or 'none'}"))
    return data


# ---------------------------------------------------------------- orchestration

def finding(check, severity, url, evidence):
    return {"check": check, "severity": severity, "url": url, "evidence": evidence}


def probe(target, extra_urls=(), timeout=10):
    origin, first_page = normalize_target(target)
    findings = []
    pages = [first_page] + [normalize_target(u)[1] for u in extra_urls]
    result = {
        "target": origin,
        "timeout": timeout,
        "robots": check_robots(origin, timeout, findings),
        "llms": {name: check_llms(origin, name, timeout, findings) for name in ("llms.txt", "llms-full.txt")},
        "pages": [check_page(u, timeout, findings) for u in pages],
    }
    findings.sort(key=lambda f: (SEVERITY_RANK[f["severity"]], f["url"], f["check"]))
    result["findings"] = findings
    result["counts"] = {s: sum(1 for f in findings if f["severity"] == s) for s in SEVERITY_RANK}
    return result


def filter_findings(findings, min_severity):
    floor = SEVERITY_RANK[min_severity]
    return [f for f in findings if SEVERITY_RANK[f["severity"]] <= floor]


def render_text(result, findings):
    out = [f"\n  geo probe: {result['target']}"]
    r = result["robots"]
    out.append(f"  robots.txt: {r['status']} (HTTP {r['http_status']})   sitemaps: {len(r['sitemaps'])}"
               f"   content-signals: {len(r['content_signals'])}")
    if r["crawlers"]:
        for token, st in r["crawlers"].items():
            via = "not mentioned" if st["status"] == "unmentioned" else f"via {st['via']}"
            rule = f"  {st['rule']}" if st["rule"] else ""
            out.append(f"    {token:<20} {st['status']:<12} {via}{rule}")
    for name, d in result["llms"].items():
        extra = f", {d['size']} B, heading: {d['first_heading'] or 'none'}, links: {d['link_count']}" if d["status"] == "present" else ""
        out.append(f"  /{name}: {d['status']} (HTTP {d['http_status']}){extra}")
    for pg in result["pages"]:
        types = sorted({t for b in pg["jsonld"] for t in b["types"]})
        bad = sum(1 for b in pg["jsonld"] if not b["ok"])
        out.append(f"  page {pg['url']} (HTTP {pg['http_status']})")
        out.append(f"    title: {pg['title']!r}   lang: {pg['lang']!r}   canonical: {pg['canonical']!r}")
        out.append(f"    meta description: {pg['meta_description']!r}")
        out.append(f"    body text: {pg['text_chars']} chars   JSON-LD blocks: {len(pg['jsonld'])}"
                   f" ({bad} unparseable)   types: {', '.join(types) or 'none'}")
    c = result["counts"]
    out.append(f"\n  findings: {len(findings)} reported   high: {c['high']}   medium: {c['medium']}   low: {c['low']}\n")
    for f in findings:
        out.append(f"  [{f['severity'].upper():<6}] {f['check']:<26} {f['url']}")
        out.append(f"           {f['evidence']}")
    if findings:
        out.append("")
    return "\n".join(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Deterministic GEO probe: robots.txt, llms.txt, JSON-LD and head tags.")
    ap.add_argument("target", help="domain or URL; its origin is used for robots.txt and llms.txt")
    ap.add_argument("urls", nargs="*", help="additional page URLs to probe")
    ap.add_argument("--json", action="store_true", help="machine-readable output for phase two")
    ap.add_argument("--timeout", type=int, default=10, help="per-request timeout in seconds (default 10)")
    ap.add_argument("--severity", choices=["high", "medium", "low"], default="low",
                    help="minimum severity to report and gate on (default: low = everything)")
    args = ap.parse_args(argv)

    try:
        result = probe(args.target, args.urls, args.timeout)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    reported = filter_findings(result["findings"], args.severity)
    result["findings"] = reported
    result["counts"] = {s: sum(1 for f in reported if f["severity"] == s) for s in SEVERITY_RANK}
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(render_text(result, reported))
    return 1 if reported else 0


if __name__ == "__main__":
    sys.exit(main())
