---
name: a-seo-gsc
description: Turn Search Console data, fetched over the API or exported by hand, into a ranked, evidence-backed action plan.
disable-model-invocation: true
---

# a-seo-gsc: Search Console → action plan

Google Search Console already knows what is wrong with a site's search performance. This skill fetches its Performance data over the API or ingests manual exports, runs a deterministic parser, applies a full analysis playbook (adapting to the site type), and writes a prioritized action plan you can actually execute. It works on any website, not one specific project.

The output is a doc: `docs/seo/YYYY-MM-DD-action-plan.md` in the target project (or wherever the user keeps analyses), plus a spoken summary of the headline finding and the top moves.

## First run: what to give me, and where to get it

**Open by asking which route they are on**, because both are fully supported and the answer changes only the first step:

> Do you have the Search Console API set up for this property, or would you rather download the reports by hand? Both work. The API saves clicking and returns one extra thing the download cannot, but hand-exported CSVs are a first-class input here, not a fallback.

### Route A: they have the API, or want it

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/a-seo-gsc/scripts/fetch_gsc.py" \
    --property sc-domain:example.com --days 90
```

That writes `current/` and `previous/` directories of CSVs in Google's own export shape. If the property has no service-account key yet, do not hand them a link. Run Setup mode below.

Then ask for the two reports no API serves:

> Two exports I cannot fetch, both from **Indexing → Pages**:
> 1. Click **Export** on the summary. That gives the indexed vs not-indexed counts and the reason breakdown.
> 2. Click the biggest "not indexed" reason (usually "Crawled - currently not indexed"), then **Export** the URL table. Repeat for any other large reason. This is the one people skip and the most useful file in the set.
> Drop the zips in a folder next to the fetched data. Optional extras: the **Links** report (top linking sites, also no API), **Sitemaps**, and **Core Web Vitals**.

### Route B: no API, or they would rather click

Give them this in full. Do not redirect them to a reference file.

> Go to Google Search Console (search.google.com/search-console), pick the property, and export three things. Each "Export" button gives a zip of CSVs.
> 1. **Performance → Search results**, set the date range (**Last 3 months** at minimum; if you can, also use the **Compare** tab against the previous period so I can see trends). Click **Export**.
> 2. **Indexing → Pages**, click **Export** on the summary (the indexed vs not-indexed counts and the reason breakdown).
> 3. **Indexing → Pages → click the biggest "not indexed" reason** (usually "Crawled - currently not indexed") **→ Export** the URL table. Repeat for any other large reason. This is the one people skip, and it is the most useful file.
> Drop all the zips in a folder and point me at it. Optional extras: the **Links** report, **Sitemaps**, and **Core Web Vitals**.

Everything downstream is identical. The parser cannot tell a fetched directory from an exported zip, and every analysis runs the same way on either.

**Say plainly what route B costs**, once, without labouring it: page+query pairs. No Search Console export has ever contained that shape, so the true query-cannibalization section is omitted rather than reported as clean. Every other dimension is unaffected. That is the whole difference, and for a small site it is often not worth setting up an API to get.

Then ask for the site's **brand terms** (name, domain, product names) so branded vs non-branded traffic can be split, and what the site is **for** (blog, ecommerce, SaaS, docs, local business) so the playbook adapts.

## Modes

| Mode | Trigger | What happens |
|------|---------|--------------|
| **Setup** | Route A, no key yet | Walk them through the API setup one step at a time, then verify |
| **Fetch** | Route A, key present | Run `fetch_gsc.py`, then ask only for the two coverage exports |
| **Intake** | Route B, or no data yet | Give the full three-export list inline, collect brand terms + site type |
| **Analyze** | Exports in hand | Run the parser, then work the playbook, report findings |
| **Plan** | After analyze | Write the tiered action-plan doc to `docs/seo/` |
| **Competitors** | On request, or when content gaps dominate | Dependency-free competitor lens (see below) |

Analyze and Plan usually run together. Do not skip Plan: the written, prioritized doc is the deliverable.

## Setup mode

Ask for the property exactly as Search Console names it, then resolve the key the same way `fetch_gsc.py` does: an explicit `--key` path, `GSC_SERVICE_ACCOUNT_JSON`, or `~/.config/gsc/<property-slug>.json`. Only skip setup when one of those resolves for the requested property. Do not skip because another JSON file happens to exist in `~/.config/gsc/`.

Before creating a key, identify the environment and check for Python 3 and `openssl`. The bundled API fetcher needs a Unix-like environment because its secure key handoff uses `/dev/fd`. On native Windows, offer WSL or Route B before walking through setup. If they are setting up the API for their own Windows-capable script, continue and let that script define its credential location.

One service-account key can be reused for several properties, but its account must be added to each property. When reusing one key, pass its path with `--key` or set `GSC_SERVICE_ACCOUNT_JSON`; the property-derived default filename is for zero-argument lookup, not a second key requirement.

Read `references/export-guide.md` and walk them through its setup section **one step at a time, waiting after each**. Do not paste seven steps at once. This is a browser flow across two Google products and people get stuck at a single step, usually the one they think is a formality.

The procedure stays in the reference rather than here on purpose. It runs once per property and this file loads on every invocation.

Finish by verifying, which is the part a written guide cannot do:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/a-seo-gsc/scripts/fetch_gsc.py" \
    --property <theirs> --days 7 --no-compare
```

Two failures are worth recognising on sight, because both point somewhere other than where they read:

- **`403 ... has not been used in project ... or it is disabled`.** The API is off. That is the Enable step, not a permissions problem, and the wording sends people back to Search Console to re-check the user they just added. Send them to the Cloud console instead and wait a minute for it to propagate.
- **`403` mentioning permission or the property.** The service account is not a user on the property yet, or the property string does not match. Check it is entered exactly as Search Console names it, including the `sc-domain:` prefix.

## The method

### 1. Parse (deterministic, cheap)
Run the parser over whatever the user gave you. It auto-detects Performance / Coverage / Drilldown files, normalizes the numbers, and prints findings.

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/a-seo-gsc/scripts/parse_gsc.py" \
    <zip-or-dir-or-csv> [more...] \
    --brand "brand one,brandtwo,domain.com" --min-impressions 5
```
Add `--json` to get machine output, `--out FILE` to save. Read the printed report before reasoning further; it already computes baseline, concentration, striking-distance, CTR underperformers, zero-click queries, parameter-duplicate cannibalization, coverage buckets, the index-starvation-vs-bloat diagnosis, and a categorized not-indexed list.

**Page+query pairs.** A fetched directory carries `pairs.csv`, which no manual export has. It identifies true query cannibalization: which of your own pages compete for one query, and whether the page Google shows most often is the one that ranks best. Absent that file the section is omitted rather than reported as clean, because nothing was examined. Parse `current/` and `previous/` separately and diff them for the decay dimension.

**Search types.** A downloads folder often holds Performance exports for more than one search type (Web, Image, Video, News). They describe the same URLs from different indexes, so merging them double-counts every page and the duplicates surface as parameter cannibalization that is not real. The parser reads each export's `Filters.csv`, parses one search type, and prints on stderr what it ignored. It defaults to Web; pass `--search-type image` for another. Coverage and drilldown CSVs are never filtered, so they always come through. Read the stderr note: it tells you which dataset the numbers below it describe.

**Read the index before the data.** If the project keeps a `docs/seo/README.md` or equivalent, read it first. It should say which analysis is current, what each past one settled, and what checks are outstanding. Reconstructing that by opening six dated files is the expensive way to start a run.

### 2. Analyze (judgment on top of the numbers)
Open `references/analysis-playbook.md` and walk every dimension that the data supports. The playbook covers far more than any one site will show: striking distance, CTR-vs-position, cannibalization, content gaps, indexing pathologies, decay (needs two date ranges), device/geo mismatch, rich-result opportunities, authority/linking signals, and site-type-specific failure modes (blog vs ecommerce vs SaaS vs docs vs local vs directory). Only report what the data actually supports, and say what it cannot show.

The non-negotiable discipline (from hard-won review experience): **separate observation from hypothesis from action.** "Impressions dropped" is an observation. "Googlebot got empty HTML" is a hypothesis until verified. Do not let a plausible story become a confident diagnosis. When you cannot prove causation (and a single export almost never can), say so and propose the check that would confirm it.

### 3. Plan (the deliverable)
Use `references/action-plan.md` as the template. Write findings evidence-first, then a tiered action list ranked by impact-over-effort, then a tracking table (one row per action: page/query, baseline, change date, expected effect, 28-day result) so next month's run can tell whether anything worked. Save to `docs/seo/YYYY-MM-DD-action-plan.md`. Create `docs/seo/` if absent. If the project has no `docs/`, ask where to save or offer the repo root.

### 4. Competitors (optional, dependency-free)
See `references/competitor-analysis.md`. Identify who ranks for the site's striking-distance and target queries (via `WebSearch`), fetch their ranking pages (`WebFetch`), and compare depth, structure, schema, freshness, and angle coverage. Produces a content-gap matrix and prioritized competitive moves. No paid API required; if the user has an Ahrefs/Semrush export, it plugs in as an extra CSV for real volume and backlink numbers.

## Principles

1. **Impressions are not the same as the right audience.** A page can soak up impressions from a query cluster that has nothing to do with the site's purpose. Growing that is vanity. Always sanity-check whether the winning queries match who the site is for.
2. **Index-starvation vs index-bloat are opposite problems with opposite fixes.** Starvation (good pages not indexed): fix authority, internal linking, and request indexing; do NOT publish more. Bloat (thin/duplicate pages diluting crawl): consolidate, noindex, canonicalize. The parser flags which one the data shows. Never prescribe "write more content" for a starved site.
3. **Authority is usually the real gate on a small site.** If only backlinked pages get indexed and rank while internally-linked-only pages sit in "crawled, currently not indexed," the bottleneck is authority and link architecture, not content volume. One earned link often does more than ten new posts.
4. **CTR far below the position curve = a snippet or intent problem, not a ranking problem.** A page at position 9 with 0% CTR usually means the title/meta does not match the query intent, or a SERP feature is eating the click. Fix the snippet, not the ranking.
5. **No controls means self-attributed wins.** Without an untouched comparison set and a dated change log, you cannot prove a fix caused a change. Build the tracking table so the next run can.
6. **Adapt to the site type.** The failure modes of a 300-page blog, a 50k-SKU store, a docs site, and a local business are different. Read the site-type section of the playbook.

## Cross-skill boundaries

- **a-geo-optimizer**, AI-search / GEO visibility (ChatGPT, Perplexity, Gemini citations, llms.txt, answer-capsule content). Use it for the AI-discoverability angle; this skill does not duplicate it.
- **A project-specific technical-SEO skill**, where you have one, audits the *codebase* (meta tags, canonicals, structured data, CWV). This skill diagnoses from *data* and tells that one what to go fix. Run this to find the problem, the code-level skill to fix it.

`fetch_gsc.py` saves raw exports locally and sends requests only to `oauth2.googleapis.com` and `www.googleapis.com`. The bundled parser computes the findings on the user's machine, then Claude reads those findings in the session under the user's Claude Code plan data controls. The plugin adds no telemetry, and the service-account key never leaves the machine or touches disk beyond the file the user points it at.

## Reference files

- `references/export-guide.md`, exact GSC export click-paths for every report, how to get two date ranges for trend diffing, and alternative sources (Bing Webmaster Tools, Ahrefs/Semrush CSV).
- `references/analysis-playbook.md`, the full dimension-by-dimension methodology with thresholds, formulas, and per-site-type adaptations.
- `references/action-plan.md`, output doc template and the impact/effort prioritization framework.
- `references/competitor-analysis.md`, the dependency-free competitor lens.
- `scripts/fetch_gsc.py`, the Search Console API fetcher. Standard library only, signs RS256 via openssl.
- `scripts/parse_gsc.py`, the deterministic export parser. Reads fetched and hand-exported data identically.
