# search-visibility

search-visibility helps website owners and marketers decide what to fix in Google search and get their site ready for AI assistants. `a-seo-gsc` turns your Google Search Console data into a ranked action plan: which pages lost traffic, which searches you nearly rank for, and what is blocking indexing. `a-geo-optimizer` checks whether AI assistants such as ChatGPT, Claude and Perplexity can reach, read and cite your pages, and lists the fixes. Neither can guarantee rankings or citations.

Once it is listed, you can also add it from Anthropic's plugin directory: **Customize > Plugins** in claude.ai, or `/plugin` in Claude Code.

## The two skills

| Skill | Starts from | Answers | Invoked by |
|---|---|---|---|
| `a-seo-gsc` | Your Google Search Console data, over the API or exported | What is actually costing me traffic, and in what order do I fix it | you only |
| `a-geo-optimizer` | The site or page itself | Can an AI assistant reach this, parse it, and quote it | you or Claude |

`a-seo-gsc` is a session you sit down to run once your data is in hand, so Claude will not start it for you. `a-geo-optimizer` is the opposite: it earns its keep by firing while you are building a page, before anyone thinks to ask for it.

### a-seo-gsc

Give it a property name and it produces a prioritized action plan instead of a wall of rows. It covers the diagnoses that matter and that people usually miss: pages with impressions but no clicks, striking-distance queries sitting just off page one, keyword cannibalization where your own pages compete, indexing failures (`crawled - currently not indexed`, `discovered - currently not indexed`), and index bloat.

`scripts/fetch_gsc.py` pulls the Performance data over the Search Console API, so most of the downloading is gone. It is also more than the export gives you: the UI caps its query and page tables near a thousand rows where the API returns up to 25,000 top rows per request, it fetches a matching previous window so trend analysis always runs, and it returns **page+query pairs**. Google does not guarantee every row through the API, even with pagination. No manual export contains the paired shape, which is why "which of my own pages compete for this query" has never been answerable from one. The parser now answers it, and flags the case worth fixing first, where the page Google shows most often is not the one that ranks best.

Coverage and Links still need a manual export, because neither has an API. The guide says which two reports to grab and why the URL Inspection API is not a substitute for the coverage one.

Prefer to keep downloading CSVs? That still works exactly as before. The fetcher writes Google's own export shapes, so the parser cannot tell the two apart.

It adapts to the site type, because a 300-page blog, a 50k-SKU store, a docs site, and a local business fail in different ways. `scripts/parse_gsc.py` pre-processes the data deterministically, so the numbers come from arithmetic rather than from a model's reading of a CSV.

`references/export-guide.md` covers the one-time API setup, the exact click-paths for the reports you still export by hand, and which alternative sources work (Bing Webmaster Tools, an Ahrefs or Semrush CSV).

For the same setup with an explanation of what each step does, read the [full Search Console API walkthrough](https://ivanmisic.net/blog/ai-tools/search-console-api-page-query-pairs). The installed guide remains complete and walks through the setup without depending on the article.

The bundled API fetcher needs Python 3 and `openssl` on macOS, Linux, or WSL. On native Windows, the skill offers WSL or the manual-export route before asking you to create a key.

The fetcher saves the raw exports locally and sends requests only to `oauth2.googleapis.com` and `www.googleapis.com`. The bundled parser computes the findings on your machine, then Claude reads those findings in the session under your Claude Code plan's data controls. The plugin adds no telemetry, and your service-account key never leaves your machine.

### a-geo-optimizer

Generative engine optimization, the AI-search counterpart to SEO. Being useful is not enough if the assistant cannot fetch the page, cannot tell what it says, or cannot find a quotable claim in it.

Covers crawler access, structured data, and content shaped so an answer can be lifted out of it. It recommends changes that improve the page's eligibility for citation, not a guaranteed result. Use it when building a page as well as when auditing one: the cheapest time to fix this is before publishing.

## Examples

- `/a-seo-gsc example.com: which pages lost clicks over the last three months, and what should I fix first?`
- `My Search Console exports are in ./gsc-exports. Build the prioritized action plan from them.`
- `Use a-geo-optimizer to check whether AI assistants can fetch, parse and cite example.com, and list the fixes.`

## Privacy

`a-seo-gsc` reads Search Console data for a property you own. On the API route, `fetch_gsc.py` signs a request with the service-account key file you provide and sends it only to Google (`oauth2.googleapis.com`, `www.googleapis.com`); the key is read from the path you give it and never written elsewhere. Exports are saved in your project and analysed on your machine. `a-geo-optimizer` fetches public pages of the site you ask it to check. Nothing is sent to the plugin's author or anyone else, and there is no telemetry. Your conversation with Claude is processed by Anthropic under its usual terms; that is separate from the plugin. Retention: the plugin's author never receives any of it, and the only thing kept is what the plugin writes in your own project, which you can delete at any time.

## Support

Questions, bugs or a security concern: open an issue at https://github.com/imisic/claude-marketplace/issues, or email hello@ivanmisic.net.

## Install

```
/plugin marketplace add imisic/claude-marketplace
/plugin install search-visibility@imisic
```

Then the commands are `/search-visibility:a-seo-gsc` and `/search-visibility:a-geo-optimizer`.

The longer write-up lives on the storefront: [ivanmisic.net/toolshed/plugins/search-visibility](https://ivanmisic.net/toolshed/plugins/search-visibility).

## Using them together

Run `a-seo-gsc` first when you have data, because it tells you where the loss actually is and stops you optimizing a page nobody was going to visit. Run `a-geo-optimizer` on a new site or page, where there is no data yet, and on anything you want quoted by an assistant.

`a-seo-gsc` only produces findings and a plan. `a-geo-optimizer` can also make the fixes it recommends (crawler rules, structured data, page structure) when you ask it to. Either way, you decide what lands.
