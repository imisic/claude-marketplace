# GSC export guide

Exact steps to pull the data this skill needs. Google Search Console UI wording drifts; match on intent if a label moved.

For the same setup with an explanation of what each step does, read the [full Search Console API walkthrough](https://ivanmisic.net/blog/ai-tools/search-console-api-page-query-pairs). This guide remains complete, so the skill never depends on the article being available.

## Prefer the API for Performance

`scripts/fetch_gsc.py` pulls the whole Performance half over the API, so export 1 below is only needed when the API is not set up for a property. The API also adds data: the UI export caps its query and page tables near 1000 rows while the API returns up to 25,000 top rows per request, it writes a matching previous window so trend analysis always runs, and it returns **page+query pairs**, a shape no export has ever contained and the only way to prove true cannibalization. Google does not guarantee every row through the API, even with pagination, so treat it as a larger and more useful sample rather than a complete copy of every search.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/a-seo-gsc/scripts/fetch_gsc.py" \
    --property sc-domain:example.com --days 90
```

Output is a directory of CSVs in Google's own export shape, so `parse_gsc.py` reads it exactly like a hand-exported zip and everything below stays a working fallback.

The bundled fetcher requires Python 3 and `openssl` on macOS, Linux, or WSL. On native Windows, use WSL for the API route or take the manual-export route below. The Google API itself is not limited to those systems; this is a constraint of the bundled dependency-free fetcher.

**One-time setup per Google account:**
1. `console.cloud.google.com` → pick or create a project.
2. APIs & Services → Library → **Google Search Console API** → Enable. Skipping this returns a 403 from the query endpoint whose wording sounds like a permissions problem rather than a disabled API.
3. APIs & Services → Credentials → Create credentials → **Service account**. No project IAM roles are needed; property access is granted in Search Console, not in IAM.
4. Open it → **Keys** → Add key → Create new key → **JSON**. Save it outside any webroot at `~/.config/gsc/<property-slug>.json`, mode 600. The slug is the property with `:`, `/` and `.` turned into `-`, so `sc-domain:example.com` becomes `example-com`.

**Per property:** Search Console → Settings → Users and permissions → Add user → the service account's `...iam.gserviceaccount.com` address → **Restricted**. The query endpoint needs read permission, so Full is unnecessary. One service account can be granted access to several properties; pass the same key with `--key` or `GSC_SERVICE_ACCOUNT_JSON` when its default filename belongs to another property.

**What the API cannot give you, ever:** the Index Coverage report (exports 2 and 3 below) and the Links report. There is no endpoint for either. The URL Inspection API is not a substitute for coverage: it only answers for URLs you hand it, so it can confirm a sitemap but can never reveal index bloat from URLs Google holds that you never submitted, which is half of what that report is for.

## The three core exports

Open [search.google.com/search-console](https://search.google.com/search-console) and select the property. With the API set up, only 2 and 3 still need doing by hand.

### 1. Performance (Search results)
1. Left nav → **Performance** → **Search results**.
2. Top of page: click the **Date** filter. Choose **Last 3 months** (or longer; 12 months is better if the site is older). To get trend data in one shot, use the **Compare** tab → "Compare last 3 months to previous period".
3. Make sure the four metric toggles are all on: **Total clicks, Total impressions, Average CTR, Average position**.
4. Click **Export** (top right) → **Download CSV** (a zip).

This zip contains: `Queries.csv`, `Pages.csv`, `Countries.csv`, `Devices.csv`, `Dates.csv` (or `Chart.csv`), `Filters.csv`, `Search appearance.csv`. Note: the Queries and Pages files are a top-N sample (~1000 rows), not every query, so query-level totals are a sample, not the site total. The Dates/Chart file carries the true totals.

### 2. Indexing summary (Pages)
1. Left nav → **Indexing** → **Pages**.
2. Click **Export** on the summary view.

Gives the indexed vs not-indexed counts over time (`Chart.csv`) and the reason breakdown (`Critical issues.csv` / `Non-critical issues.csv`, columns `Reason,Source,Validation,Pages`).

### 3. Indexing drilldown (the one people skip)
1. Still in **Indexing → Pages**, scroll to "Why pages aren't indexed".
2. Click the largest reason (usually **Crawled - currently not indexed**, or **Discovered - currently not indexed**, or **Duplicate without user-selected canonical**).
3. On the detail page, click **Export**. This gives `Table.csv` (`URL,Last crawled`), the actual list of affected URLs.
4. Repeat for any other reason with a meaningful count.

The drilldown is what turns "44 pages aren't indexed" into "these specific 44 URLs, and here's the pattern." Without it the analysis is guesswork.

## Getting trend data (two date ranges)

With `fetch_gsc.py` this is automatic: it writes `current/` and `previous/` windows of equal length unless you pass `--no-compare`. The rest of this section is the manual route.

A single export is a snapshot: it cannot show "position improved but CTR dropped" or "this query is decaying." To diff:
- **Easiest:** in Performance, use the **Compare** tab (previous period or year-over-year), then Export. The CSVs then carry both periods.
- **Manual:** export "Last 3 months" today, and separately export the prior 3 months (custom range). Hand both to the skill; it will diff them.

## Optional exports that sharpen the analysis

| Report | Where | Adds |
|--------|-------|------|
| **Links** | Left nav → Links → Export | Top linking sites, top linked pages, internal links. Reveals authority and orphan pages. |
| **Sitemaps** | Indexing → Sitemaps | Submitted vs discovered counts; sitemap errors. |
| **Core Web Vitals** | Experience → Core Web Vitals | Slow-URL groups (LCP/CLS/INP). CWV code fixes belong to a performance or technical-SEO skill, not here. |
| **Enhancements / Structured data** | Experience/Enhancements | Which rich-result types are eligible and erroring. |
| **Manual actions / Security** | Security & Manual Actions | Penalties or hacks. Always check; a manual action explains everything at once. |

## Alternative and supplementary data sources

- **Bing Webmaster Tools** exports in a similar shape; the parser reads generic Clicks/Impressions/CTR/Position CSVs, so Bing "Search Performance" exports work too.
- **Ahrefs / Semrush / Moz** CSV exports (keyword volume, difficulty, backlinks) are not GSC but plug into the competitor lens as extra inputs for real search-volume and referring-domain numbers. GSC has no volume or difficulty data, so if the user has these, ask for them.
- **GA4** organic-landing-page export pairs conversions with the GSC clicks, answering "traffic but no conversions." GSC alone cannot see conversions.

## What GSC data cannot tell you (state these up front)

- **Search volume or keyword difficulty**, GSC shows your impressions, not total market demand. Use a keyword tool for that.
- **Why visitors don't convert**, clicks in, but not what happened after. Needs analytics.
- **Query × page pairing at scale**, the standard export gives queries and pages separately, not which query drove which page (unless you export a page-filtered Performance view). True one-query-many-pages cannibalization needs that filtered export or the API.
- **Causation**, correlation only. A change and a metric move in the same week is a hypothesis, not proof.
