# Competitor analysis (dependency-free)

GSC shows what a site ranks for. It cannot show who is beating it, or what demand it is missing entirely. This lens fills that gap using only `WebSearch` and `WebFetch` (no paid API, no new dependency). If the user has an Ahrefs/Semrush/Moz export, fold it in for real volume and backlink numbers, but the lens works without one.

Run it when: content gaps or striking-distance dominate the findings, the user asks about competitors, or a target query cluster is worth a serious push.

## Method

### 1. Pick the battleground queries
From the analysis, take the striking-distance and target-content-gap queries that actually matter for the site's audience (not the vanity clusters). Cap it: 5-15 queries is enough to see the pattern.

### 2. See who ranks
For each query, `WebSearch` it and record the top 5-10 organic results (skip ads and the site's own pages). Tally domains across queries. The domains that recur are the real competitors for this space, which is more accurate than whoever the user assumes.

Note SERP features too: who owns the featured snippet, what People-Also-Ask questions appear (these are content-gap gold), whether a pack/carousel/forum result (Reddit, Stack Overflow) dominates. If forums own the SERP, the winning move may be a genuinely better resource or participating there, not another blog post.

### 3. Read the winners
For the top 2-4 competitor pages per key query, `WebFetch` the page and compare against the site's competing (or missing) page on:
- **Depth and coverage**, sub-topics they answer that the site does not.
- **Structure**, headings, tables, direct answers up top, scannability.
- **Freshness**, visible last-updated date; stale winners are beatable.
- **Format match**, does the query want a listicle, a how-to, a definition, a comparison, a tool? Ranking pages reveal the intent.
- **Schema / rich results**, what they render in the SERP (rating stars, FAQ, breadcrumbs).
- **Authority proxy**, domain seniority, how referenced they are. Without a backlink tool this is a judgment call; say so.

### 4. Build the gap matrix
A simple table: rows = sub-topics/angles, columns = the site + top competitors, cells = covered / thin / missing. The site's "missing" rows that competitors all cover are the content plan. The rows everyone is thin on are the differentiation opportunity.

### 5. Output competitive moves
Fold into the action plan as its own tier:
- **Beat on depth:** specific sub-topics to add to an existing striking-distance page to overtake a shallow winner.
- **Beat on freshness:** pages where the winner is stale and a refresh + re-earn-links wins.
- **Beat on format:** where the site's format mismatches intent (a prose post where the SERP wants a comparison table or tool).
- **New pages:** only for gaps that are on-audience and winnable given the site's authority. Do not recommend targeting a query cluster owned by DR-90 sites on a new site; name that wall when it exists.

## Honest limits

- `WebSearch` results are personalized/regional and a moment in time, not a ranking tool's aggregate. Treat them as a strong sample, not a rank tracker.
- No backlink or traffic numbers without a paid export. State authority comparisons as estimates.
- "Winnable" depends on the site's own authority (from the Links export and the indexing diagnosis). A gap you cannot rank for yet is not an opportunity, it is a someday. Sequence competitive content behind the authority work if the site is index-starved.

## Optional: paid-tool CSV inputs

If the user provides them, these upgrade the lens from qualitative to quantitative:
- **Keyword export** (volume, difficulty) → prioritize gaps by real demand, not just GSC impressions.
- **Backlink export** (referring domains, competitor link profiles) → quantify the authority gap and surface link targets (who links to competitors but not the site).
- **Site audit export** → competitor technical posture.

Read them as extra CSVs alongside the GSC findings; the volume/difficulty columns slot straight into prioritization.
