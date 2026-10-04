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

- **Index-starvation:** more pages excluded than indexed, good content sitting in "Crawled - currently not indexed" or "Discovered - currently not indexed." Cause is almost always **authority + internal linking + crawl priority**, not content quality. Fixes: earn links, strengthen internal links from indexed high-authority pages, get hub/index pages indexed, request indexing for priority URLs, submit a clean sitemap. Do NOT tell a starved site to publish more; it just grows the parked pile.
- **Index-bloat:** thousands of thin/duplicate/parameter URLs indexed or clogging crawl. Fixes: canonicalize, noindex thin templates, `Disallow` parameter and faceted URLs, consolidate.
- **Canonical confusion:** large "Duplicate without user-selected canonical" or "Alternate page with proper canonical tag." Check that canonicals are self-consistent and point where you intend.

Coverage reason cheat-sheet (GSC label → what it means → move):

| Reason | Meaning | Move |
|--------|---------|------|
| Crawled - currently not indexed | Google fetched it, chose not to index | Quality/authority/linking. Improve links + request indexing. If genuinely thin, improve or noindex. |
| Discovered - currently not indexed | Known but not even crawled yet | Crawl budget / low priority. Internal links + sitemap + authority. |
| Duplicate without user-selected canonical | Google picked a different canonical | Set explicit canonical; consolidate duplicates. |
| Duplicate, Google chose different canonical than user | Your canonical was overridden | The "duplicate" is stronger; merge or differentiate. |
| Alternate page with proper canonical tag | Correctly canonicalized dupe | Usually fine. Expected for paginated/param/AMP. |
| Page with redirect | 301/302 | Fine if intended (restructure fallout). Audit for redirect chains. |
| Not found (404) | Broken | Fix internal links or 301 to the right page. |
| Soft 404 | Thin/empty page returning 200 | Add content or return real 404. |
| Blocked by robots.txt | Disallowed | Verify intentional; accidental blocks are common after CMS/CDN changes. |
| Blocked due to unauthorized request (401) | Auth-gated | Fine if intended. |
| Server error (5xx) | Broke during crawl | Reliability issue; investigate logs. |

Then **categorize the not-indexed URL list** (the parser buckets by generic path pattern: content, taxonomy-tag, taxonomy-category, product, pagination, parameter-url, feed, redirect-endpoint). Interpret per site: which buckets are junk that should never be index candidates (feeds, redirect endpoints, param/sort URLs, thin tag pages) vs which are real content being wrongly excluded. Junk → exclude from crawl. Real content excluded → the starvation fight above.

## 2. Striking distance

Queries at **positions 11-20** with real impressions are the highest-ROI lever on most sites: they already rank, just below the fold of page 1. Small on-page improvements (title/meta relevance, adding the exact sub-topic, one internal link, a bit more depth) can push them onto page 1 where clicks live. Sort by impressions; the top of that list is the week's to-do. Positions 5-10 with low CTR belong to dimension 3, not here.

## 3. CTR vs position

For queries in the top 10, compare actual CTR to the expected-for-position curve (parser flags actual below 40% of expected). Under-performers are a **snippet or intent problem**, not a ranking problem:
- Title/meta does not match the query intent (page ranks for "X system requirements" but the title says "X overview").
- A SERP feature (featured snippet owned by someone else, People-Also-Ask, a pack, an ad block) is eating the clicks.
- The URL/brand looks untrustworthy in the SERP.

Fixes: rewrite the title to lead with the searcher's outcome and include the query's head term; tighten the meta description; add the structured data that could win the feature (defer schema specifics to `a-geo-optimizer`, or to your project's code-level SEO skill). Zero-click at a strong position is the loudest, cheapest win on the board.

## 3b. How much of the traffic do query rows actually cover?

Before trusting anything computed from query rows, total them and compare against the page rows. Google withholds queries too few people ran, so the query table is a sample, and on a low-volume site it is a small one. Measured on one low-traffic blog over 28 days: page rows carried roughly 50 clicks and 12,000 impressions while query rows carried 4 and 1,900. Query rows saw 16% of impressions and 8% of clicks. Expect the gap to shrink as a site gets busier, and check it rather than assuming.

That does not invalidate striking-distance or CTR work, but it changes what those findings are: statements about the disclosed minority, not about the site. State the coverage ratio in the report. Never present a query-row total as the site's traffic, and never subtract query clicks from page clicks and call the remainder anything.

Related, and worth not chasing: `dates.csv` and `pages.csv` disagree slightly, around 1% on the window above. Both are Google's own aggregates over the same data. Use page rows for totals.

## 4. Cannibalization and duplicate URLs (partial)

- **Parameter/duplicate URLs** (parser detects): the same clean URL indexed under `?ref=`, `?sort=`, `?utm=`, session IDs, tracking tags, pagination. Splits signals and wastes crawl. Fix: self-referential-clean canonical, `Disallow` the params, or 301 the tracked variants.
- **True query cannibalization** (multiple distinct pages competing for one query): the parser detects this whenever a `pairs.csv` is present, which `fetch_gsc.py` writes and no manual export contains. Google's UI export lists queries and pages in separate tables, so from exports alone this stays unprovable and the section is omitted rather than reported as clean. A flagged query has two or more of your pages each holding at least the impression floor, with the runner-up on 20% or more of the query's impressions. Read the **position/impression mismatch** flag first: it means Google shows one page most often while a different one ranks better, which is the clearest case for consolidating. Fix: pick one canonical page, merge the others into it, 301 the losers. (Classic symptom: several near-identical titles, none ranking well, positions bouncing.)
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

The Search-appearance breakdown (and Enhancements report) shows which rich-result types the site is eligible for and which are erroring. Missing eligibility for obvious types (Article, FAQ, Product, Breadcrumb, HowTo) is a structured-data opportunity. Hand the specifics to `a-geo-optimizer` (AI-citation schema) or to whatever skill owns code changes in the project; this skill just flags the gap from the data.

## 9. Authority and internal linking (needs Links export)

- **Referring domains:** few linking sites = low authority = the index-starvation gate. The clearest tell: only backlinked pages are indexed and ranking. One earned link often pulls in a whole cluster.
- **Internal-link distribution:** pages with zero internal links are orphans Google deprioritizes. Ensure every important page is linked from indexed, higher-authority pages (home, hubs, related content), not just from each other.
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
- Expected CTR curve is a blended industry average (pos 1 ≈ 27%, pos 10 ≈ 2%, page 2 ≈ 1%). It is a reference for spotting outliers, not ground truth; real CTR varies wildly by query type and SERP layout.
