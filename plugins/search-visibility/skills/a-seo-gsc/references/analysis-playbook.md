# Analysis playbook

Work every dimension the data supports. Most sites show only a subset; report those, name what is missing, and never invent a finding the data does not carry. The parser (`scripts/parse_gsc.py`) computes the arithmetic for most dimensions below; you supply judgment and the ones it cannot.

Order below is roughly "most decisive first." On any given site, one or two dimensions dominate. Find the dominant one and lead with it.

---

## 0. Baseline and shape

Read the totals first (from the Dates/Chart file, which is authoritative; query/page files are a top-N sample).

- **Clicks, impressions, CTR, average position.** Position is impression-weighted, so a few high-impression page-2 queries drag it up.
- **Branded vs non-branded** (needs `--brand`). Branded clicks are people who already know the site. If branded is most of the traffic, the site is not winning new audiences. If the site cannot even rank #1 for its own brand, that is a distinct, fixable problem (entity signals, homepage authority).
- **Concentration.** What share of impressions sits on the single top page? High concentration (one page ≫ everything) means the site's search presence is one lucky page, not a system. Ask whether that page is even on-topic for the site.

Sanity flag: if impressions are large but clicks are near zero, the whole site is probably ranking on page 2, or the snippets are wrong, or the impressions are for queries the content does not actually answer.

## 1. Indexing / coverage pathology

Often the real story, and people never look. Diagnose which pattern:

- **Index-starvation:** more pages excluded than indexed, good content sitting in "Crawled - currently not indexed" or "Discovered - currently not indexed." Common causes are **authority + internal linking + crawl priority**, but rule out canonicals, rendering and server errors first; Google gives no single cause. Fixes: earn links, strengthen internal links from indexed high-authority pages, get hub/index pages indexed, request indexing for priority URLs, submit a clean sitemap. Do NOT tell a starved site to publish more; it just grows the parked pile.
- **Index-bloat:** thousands of thin/duplicate/parameter URLs indexed or clogging crawl. Fixes: canonicalize, noindex thin templates, `Disallow` parameter and faceted URLs, consolidate.
- **Canonical confusion:** large "Duplicate without user-selected canonical" or "Alternate page with proper canonical tag." Check that canonicals are self-consistent and point where you intend.

Coverage reason cheat-sheet (GSC label → what it means → move):

| Reason | Meaning | Move |
|--------|---------|------|
| Crawled - currently not indexed | Google fetched it, chose not to index | Quality/authority/linking. Improve links + request indexing. If genuinely thin, improve or noindex. |
| Discovered - currently not indexed | Known but not even crawled yet | Low priority, or Google held back to avoid overloading the host. Check server response times, then internal links + sitemap + authority. |
| Duplicate without user-selected canonical | Google picked a different canonical | Set explicit canonical; consolidate duplicates. |
| Duplicate, Google chose different canonical than user | Your canonical was overridden | Check the signals disagree (internal links, sitemap, redirects); merge or differentiate. |
| Alternate page with proper canonical tag | Correctly canonicalized dupe | Usually fine. Expected for param/AMP variants; paginated pages should normally carry their own canonical instead. |
| Page with redirect | 301/302 | Fine if intended (restructure fallout). Audit for redirect chains. |
| Not found (404) | Gone or broken | Fine if the page was removed on purpose. Otherwise fix internal links or 301 to the right page. |
| Soft 404 | Thin/empty page returning 200 | Add content or return real 404. |
| Blocked by robots.txt | Disallowed | Verify intentional; accidental blocks are common after CMS/CDN changes. |
| Blocked due to unauthorized request (401) | Auth-gated | Fine if intended. |
| Server error (5xx) | Broke during crawl | Reliability issue; investigate logs. |
| Redirect error | Loop, chain too long, empty or bad redirect URL | A failure, not a choice: run URL Inspection, then fix the redirect. |
| Blocked due to access forbidden (403), URL blocked due to other 4xx issue, Excluded by 'noindex' tag | As named | Verify each is intended. |
| Indexed, though blocked by robots.txt | Warning on indexed pages | Unblock if the page should rank properly, or noindex it (Google must be able to crawl to see noindex). |
| Page indexed without content | Google indexed the URL but could not read its content | Not a robots.txt block: likely cloaking or a format Google can't index. Run URL Inspection and look at the rendered page. |

Then **categorize the not-indexed URL list** (the parser buckets by generic path pattern: content, taxonomy-tag, taxonomy-category, product, pagination, parameter-url, feed, redirect-endpoint). Interpret per site: which buckets are junk that should never be index candidates (feeds, redirect endpoints, param/sort URLs, thin tag pages) vs which are real content being wrongly excluded. Junk → exclude from crawl. Real content excluded → the starvation fight above.

## 2. Striking distance

Queries at **positions 11-20** with real impressions are the highest-ROI lever on most sites: they already rank, just below the fold of page 1. Small on-page improvements (title/meta relevance, adding the exact sub-topic, one internal link, a bit more depth) can push them onto page 1 where clicks live. Sort by impressions; the top of that list is the week's to-do. Positions 5-10 with low CTR belong to dimension 3, not here.

## 3. CTR vs position

For queries in the top 10, compare actual CTR to the expected-for-position curve (parser flags actual below 40% of expected). Under-performers are a **snippet or intent problem**, not a ranking problem:
- Title/meta does not match the query intent (page ranks for "X system requirements" but the title says "X overview").
- A SERP feature (AI Overview, featured snippet owned by someone else, People-Also-Ask, a pack, an ad block) is eating the clicks. Check the Search generative AI report for the page and look at the live results page before rewriting anything.
- Low volume: a handful of impressions cannot carry a CTR verdict. Segment by device and country before concluding.
- The URL/brand looks untrustworthy in the SERP.

Fixes: rewrite the title to lead with the searcher's outcome and include the query's head term; tighten the meta description; add the structured data that could win the feature (defer schema specifics to `a-geo-optimizer`, or to your project's code-level SEO skill). Zero-click at a strong position is the loudest, cheapest win on the board.

## 3b. How much of the traffic do query rows actually cover?

Before trusting anything computed from query rows, total them and compare against the property totals in `dates.csv` (the query table is aggregated by property, the page table by page, so page totals are the wrong yardstick). Google withholds queries too few people ran, so the query table is a sample, and on a low-volume site it is a small one. Measured on one low-traffic blog over 28 days: the property carried about 11,700 impressions, query rows carried 4 clicks and about 1,900 impressions. Query rows saw about 16% of impressions and under a tenth of clicks.

That does not invalidate striking-distance or CTR work, but it changes what those findings are: statements about the disclosed minority, not about the site. State the coverage ratio in the report. Never present a query-row total as the site's traffic, and never subtract query clicks from page clicks and call the remainder anything.

Related, and worth not chasing: `dates.csv` and `pages.csv` disagree slightly (about 1% apart on the window above). Google aggregates by property for the chart and by page for the page table, so the numbers legitimately differ. Use `dates.csv` for site totals and for the query-coverage ratio, with the same filters on both.

## 4. Cannibalization and duplicate URLs (partial)

- **Parameter/duplicate URLs** (parser detects): the same clean URL indexed under `?ref=`, `?sort=`, `?utm=`, session IDs, tracking tags, pagination. Splits signals and wastes crawl. First check the parameter doesn't select different content (PHP sites often serve real pages from `?id=`). For tracking and sort variants: a canonical to the clean URL, or 301. Don't `Disallow` them while the canonical still needs to be seen. Paginated pages keep their own URLs and canonicals.
- **Shared-query candidates** (several of your pages appearing for one query): the parser flags these whenever a `pairs.csv` is present, which `fetch_gsc.py` writes across the whole property. Google's standard export lists queries and pages in separate tables, and a page-filtered export covers one page at a time, so without pairs the section is omitted rather than reported as clean. A flagged query has two or more of your pages each holding at least the impression floor, with the runner-up on 20% or more of the query's impressions. Read the **position/impression mismatch** flag first: Google shows one page most often while a different one ranks better. A flag is a candidate, not a diagnosis: pages can share a query and serve different intents, and both may deserve to rank. Before merging, check that the pages answer the same intent for the same reader. Only then pick one canonical page, merge the others into it and 301 them. (Typical symptom when it is real: several near-identical titles, none ranking well, positions bouncing.)
- **Over-splitting a topic:** a cluster of thin posts on near-identical sub-topics that would rank better as one strong page. Consolidation beats proliferation on low-authority sites.

## 5. Content gaps (partial)

Queries the site gets impressions for but has no dedicated page answering. Signals: a broad page ranking at position 9-15 for many specific long-tail variants it does not directly address (e.g., one overview post catching dozens of "X requirements / X pricing / X vs Y" queries). Two responses:
1. If on-topic and worth it: build the dedicated page (or a strong section) that directly answers the cluster.
2. If off-topic for the site's purpose: ignore it. Chasing off-audience queries grows vanity impressions. Judge against who the site is for.

GSC only shows queries you already appear for. For demand you are missing entirely, you need a keyword tool or the competitor lens.

## 6. Decay and trend (needs two date ranges)

`fetch_gsc.py` writes `current/` and `previous/` windows of equal length by default, so this dimension runs without anyone having remembered to tick Compare in the UI. Parse each directory and diff. With hand exports it still depends on the Compare box, and if only one range is present, say the dimension was skipped rather than implying stability.

With a comparison export, diff period-over-period:
- **Declining queries/pages:** falling clicks or impressions, or rising position number. Often a competitor overtook, content went stale, or a redesign/restructure lost signals. Freshness updates and re-earning links help.
- **Position improved but CTR dropped:** you moved up but the SERP got more competitive (features, ads) or the snippet stopped matching. Snippet work.
- **Seasonality:** distinguish a real drop from an annual dip. Year-over-year comparison separates them.
- **Restructure fallout:** a category/URL migration typically shows a wave of new redirects, duplicate-canonical entries, and a not-indexed bump as Google re-evaluates. Time findings against known deploy dates before blaming quality.

Without two ranges, say so and recommend pulling the comparison export next time.

## 7. Device and geo

- **Device CTR gap:** if mobile CTR ≪ desktop at the same position (or vice versa), the mobile SERP layout or the page's mobile snippet/experience is the issue.
- **Geo/language mismatch:** impressions concentrated in countries the site does not serve or in a language it does not publish (common: a homelab/tech post pulling global traffic a personal/consulting site cannot use). Or the reverse: target market underrepresented, implying weak local relevance or hreflang gaps. Match the geo distribution against the site's actual market.

## 8. Rich results / search appearance

The Search-appearance breakdown (and Enhancements report) shows which rich-result types the site is eligible for and which are erroring. Missing eligibility for types Google still shows (Article, Product, Breadcrumb, Review snippet, LocalBusiness, Discussion forum) is a structured-data opportunity. FAQ rich results ended 2026-05-07 and HowTo in 2023; don't recommend either.

## 8b. AI features (Search generative AI report)

Since 2026-08-31 the Search generative AI performance report is available worldwide, though a site with too few impressions may not see it. It shows impressions only (no clicks or position), by page, country, device and date, for AI Overviews and AI Mode combined, with Discover's AI features reported separately. No API exposes it, so read it from the UI or a screenshot. Use it as context: whether a page's links appear in Google's AI features at all, and whether that changed alongside a CTR drop at a stable position. It can't say which feature or query, and it only measures your own links, so a causal claim ("AI Overviews took these clicks") needs separate evidence. Hand the specifics to `a-geo-optimizer` or to whatever skill owns code changes in the project; this skill just flags the gap from the data.

## 9. Authority and internal linking (needs Links export)

- **Referring domains:** few linking sites suggests low authority, a likely index-starvation gate. The clearest tell: only backlinked pages are indexed and ranking.
- **Internal-link distribution:** pages with zero internal links are orphans Google deprioritizes. The Links report is a sample, so a page missing from it is not proof it is an orphan; confirm from the site's own link graph. Ensure every important page is linked from indexed, higher-authority pages (home, hubs, related content), not just from each other.
- **Anchor concentration:** if all internal anchors are generic ("read more"), you are wasting relevance signals.

---

## Site-type adaptations

The dominant failure mode shifts with what the site is.

- **Blog / content site:** cannibalization from overlapping posts, thin-tag index bloat, striking-distance long-tail, freshness decay. Growth = consolidate + strengthen the best, not endless new posts (on low authority).
- **Ecommerce:** faceted-navigation parameter explosion (the #1 cause of index bloat), thin product pages, category-vs-product cannibalization, out-of-stock/discontinued 404s, seasonality. Canonicals and parameter handling dominate.
- **SaaS / marketing site:** small page count, so every page matters; branded vs non-branded split is diagnostic; feature/comparison/alternative pages are the striking-distance goldmine; docs subdomain interplay.
- **Docs / knowledge base:** huge page count, internal-search-style queries, version duplication (v1/v2 pages competing), "answer" intent where featured snippets matter most.
- **Local business:** geo distribution is everything; Maps/local-pack impressions; branded + "near me" queries; NAP consistency and local schema.
- **Directory / aggregator / marketplace:** thin auto-generated pages Google routinely refuses to index (expect large "crawled not indexed"); the fight is proving unique value per page or accepting partial indexing and concentrating authority on the pages that matter.

## Thresholds used by the parser (tune per site)

- Striking distance: position 11-20, impressions ≥ `--min-impressions` (default 5).
- CTR underperformer: position ≤ 10 and actual CTR < 40% of the expected-for-position value.
- Zero-click: clicks == 0 and impressions ≥ max(min-impressions, 10).
- Expected CTR curve is a rough reference with no single named source (pos 1 ≈ 27%, pos 10 ≈ 2%, page 2 ≈ 1%), set before AI Overviews were common. It is for spotting outliers, not ground truth; real CTR varies wildly by query type and results-page layout.
- Striking distance uses average position, which blends days and devices; check the date or device split before calling a query page-2.
- The API returns at most about 50,000 rows per day per search type, top rows by clicks. On large sites the long tail (where striking distance and shared queries live) is missing; `fetch_gsc.py` warns when a dataset reaches that cap. BigQuery bulk export avoids the cap for long-term clients (no backfill, needs billing).
