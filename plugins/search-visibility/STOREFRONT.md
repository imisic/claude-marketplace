---
name: search-visibility
tagline: Two Claude Code skills to analyze Search Console data and audit pages for AI search visibility.
kind: plugins
repo_url: https://github.com/imisic/claude-marketplace
install_cmd: /plugin install search-visibility@imisic
tags: digital-strategy, content-creators, marketers, claude-code
---

Search Console gives you thousands of rows and no priority. You can see that clicks are down, that some pages are not indexed, that a query sits at position 11, and still have no idea which of those is worth a Tuesday afternoon.

This bundle is two skills for the two ways people find things now: a search engine, and an AI assistant answering on their behalf.

**What you get**

- `/search-visibility:a-seo-gsc`: give it your property name and get a prioritized action plan. It pulls your Search Console data over the API, then finds the pages earning impressions but no clicks, the queries sitting just off page one where a title rewrite is worth more than a new post, the places your own pages compete with each other, and the indexing failures that quietly keep content out of results. Every item is ranked by impact against effort, so the plan starts with the cheapest real win rather than the most alarming number.
- `/search-visibility:a-geo-optimizer`: the AI-search half. It checks whether assistants such as ChatGPT, Claude, Perplexity, or Gemini can fetch a page, understand it, and find a usable answer. It then recommends the crawler, structured-data, and content changes worth making. It improves eligibility for citation, but no tool can promise a citation. Use it when auditing a live site and when writing a page, as the second is much cheaper than the first.

**The numbers in your plan are computed by a script, not read off a spreadsheet by a model.** A bundled parser pre-processes everything before anything reasons about it. The methodology then adapts to what you actually run, because a 300-page blog, a large store, a docs site, and a local business fail in different ways and the generic advice fits none of them.

Fetching over the API buys more than saved clicks. Search Console's own export caps its query and page tables near a thousand rows; the API returns up to 25,000 top rows per request, fetches a matching earlier window so trend analysis always runs, and returns page and query together. That last one answers a question no export can: which of your own pages compete for the same term, and whether the one Google shows most often is the one that actually ranks best. Two reports still need downloading by hand, coverage and links, because Google publishes no API for either, and the guide says so plainly instead of letting you discover it.

Need the one-time setup? [The full Search Console API walkthrough](/blog/ai-tools/search-console-api-page-query-pairs) explains the Cloud project, service account, key placement, and page-and-query request. The installed skill still guides the setup one step at a time.

The bundled API fetcher needs Python 3 and `openssl` on macOS, Linux, or WSL. On native Windows, the skill offers WSL or the manual-export route before asking you to create a key.

If you would rather keep downloading CSVs, nothing changes. The fetcher writes Google's own export shapes, so the parser cannot tell the two apart.

The fetcher saves the raw exports locally and sends requests only to Google's OAuth and Search Console endpoints. The bundled parser computes the findings on your machine, then Claude reads those findings in the session under your Claude Code plan's data controls. The plugin adds no telemetry, and the service-account key never leaves your machine.
