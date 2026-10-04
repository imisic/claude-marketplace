# Action-plan template

The deliverable. Write it to `docs/seo/YYYY-MM-DD-action-plan.md` in the target project. Evidence first, then ranked actions, then a tracking table so the next run can measure what worked.

Keep it honest: every claim ties to a number from the export, every hypothesis is labeled as one, and anything the data cannot show is stated plainly.

## Structure

```markdown
# SEO action plan, <site>, <YYYY-MM-DD>

Source: GSC export, <date range>. Brand terms: <...>. Site type: <...>.

## Snapshot
- Clicks / impressions / CTR / avg position (with the one-line "so what").
- Branded vs non-branded.
- Concentration (top page's share of impressions).

## Headline finding
The single most important thing, stated in one paragraph, with the numbers that prove it and the one hypothesis (labeled) for the cause. This is what the whole plan hinges on.

## Findings by dimension
For each dimension the data supports (indexing, striking distance, CTR, cannibalization, content gaps, decay, device/geo, authority):
- **Observation:** what the numbers say (cite them).
- **Hypothesis:** the likely cause, labeled as a hypothesis.
- **Check:** what would confirm it (so it does not stay a guess).

## Action list (ranked)
Tiered by impact-over-effort. Each action: what, why (which finding it addresses), effort (S/M/L), expected effect, and who does it (code change vs GSC click vs content edit vs outreach).

### Tier 1. Highest impact
### Tier 2. Quick wins / hygiene
### Tier 3. Worth doing, secondary

## What this export cannot tell us
Explicit limits: no volume/difficulty data, no conversion data, causation unproven, query×page pairing unavailable, single snapshot (no trend), etc. Plus what to export next time to close the gap.

## Tracking table
| # | Action | Target (page/query) | Baseline (date) | Changed on | Expected effect | 28-day result |
|---|--------|--------------------|-----------------|-----------|-----------------|---------------|
Leave "Changed on" and "28-day result" blank; they get filled as work ships and at the next run.
```

## Prioritization

Rank by **impact ÷ effort**, not by dimension order. A rough ICE (Impact, Confidence, Ease) or a 2×2 (impact vs effort) is enough; do not over-formalize. Bias toward:

1. **Actions that unblock everything else.** On a starved site, getting content indexed (authority + linking) gates every other win, so it is Tier 1 even though it is slow. On a bloated site, the parameter/canonical cleanup is the unblock.
2. **Zero-click strong positions.** Rewriting a title for a page already at position 5-10 with near-zero CTR is the cheapest click recovery on the board.
3. **Striking distance.** Small pushes on page-2 queries that already have impressions.
4. **Hygiene that stops the bleed.** 404 fixes, param exclusions, junk-URL noindex. Low effort, prevents further dilution.

De-prioritize: chasing off-audience query clusters (vanity impressions), building new content on a site that cannot get its existing content indexed, and anything whose expected effect you cannot articulate.

## Who executes what (label every action)

- **Code change**, needs a dev edit (canonical logic, robots rules, schema, redirects). If the project has a technical-SEO or codebase-audit skill, point there.
- **GSC action**, manual Search Console step (Request Indexing, submit sitemap, validate fix). Give the exact click-path and the prioritized URL list to paste.
- **Content edit**, rewrite title/meta, add a section, consolidate posts, refresh. Route through the project's content workflow (never raw DB edits on content fields).
- **Off-site**, earn a link, get a mention, cross-post. Usually the real lever for authority-gated sites; connect to whatever promotion workflow exists.

## Tone

Write like a senior analyst briefing the owner, not a report generator. Lead with the decision, support with the number, name the uncertainty. No filler, no "it is worth noting," no em dashes. If the honest read is "your content is fine, the problem is nobody links to you," say exactly that.
