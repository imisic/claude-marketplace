# AI Crawler Reference

AI crawler user-agents, what each one feeds, how it treats robots.txt, and how to configure access. Vendor facts checked against each vendor's own crawler page on 2026-11-08 unless marked otherwise; recheck before quoting, these pages change often.

## Table of Contents

1. [Crawler Quick Reference Table](#1-crawler-quick-reference-table)
2. [OpenAI Crawlers](#2-openai-crawlers)
3. [Anthropic (Claude) Crawlers](#3-anthropic-claude-crawlers)
4. [Google Crawlers and Controls](#4-google-crawlers-and-controls)
5. [Perplexity Crawlers](#5-perplexity-crawlers)
6. [Microsoft/Bing Crawlers](#6-microsoftbing-crawlers)
7. [Other AI Crawlers](#7-other-ai-crawlers)
8. [robots.txt Templates](#8-robotstxt-templates)
9. [Platform Submission Guide](#9-platform-submission-guide)
10. [AI Traffic and Citation Measurement](#10-ai-traffic-and-citation-measurement)
11. [Agentic Browsers](#11-agentic-browsers)
12. [Content Signals and Training Preferences](#12-content-signals-and-training-preferences)
13. [Agent Identity and Markdown Delivery](#13-agent-identity-and-markdown-delivery)

---

## 1. Crawler Quick Reference Table

Three kinds of bot, and robots.txt means something different for each:
- **Search/index bots** build the index that AI answers cite. Blocking one removes or reduces the site in that assistant's answers (vendors word it differently: OpenAI "will not be shown", Anthropic "may reduce").
- **User-triggered fetchers** load a page because a person asked. OpenAI, Google, Perplexity, Meta and Amazon all say these may ignore robots.txt. Blocking them is partial at best.
- **Training bots or tokens** govern whether content trains future models. Blocking one does not remove the site from live answers (Google-Extended is the exception, see section 4).

| User-Agent | Company | Kind | Blocking it means |
|-|-|-|-|
| `OAI-SearchBot` | OpenAI | Search | Not shown in ChatGPT search answers; can still appear as a navigational link |
| `ChatGPT-User` | OpenAI | User-triggered | Partial; "robots.txt rules may not apply"; not used for search eligibility |
| `GPTBot` | OpenAI | Training | Content not used for training; no documented effect on ChatGPT search |
| `Claude-SearchBot` | Anthropic | Search | Reduced visibility in Claude web search |
| `Claude-User` | Anthropic | User-triggered | Claude can't fetch the page when a user asks; Anthropic says its bots honour robots.txt |
| `ClaudeBot` | Anthropic | Training | Content excluded from training |
| `Googlebot` | Google | Search | Pages can't be crawled, so their content drops out of Search and AI features (a blocked URL can still be listed without content; use noindex to deindex) |
| `Google-Extended` | Google | Token (no own crawler) | No Gemini training **and** no grounding in Gemini Apps / Vertex AI; Search and AI Overviews unaffected |
| `Google-Agent` | Google | User-triggered agent | Partial; Google's user-triggered fetchers "generally ignore robots.txt" |
| `PerplexityBot` | Perplexity | Search | Invisible in Perplexity answers |
| `Perplexity-User` | Perplexity | User-triggered | Partial; "generally ignores robots.txt" |
| `Bingbot` | Microsoft | Search | Out of Bing and Copilot; ChatGPT search draws partly on Bing (section 6) |

**Minimum for AI search visibility:** don't block Googlebot, Bingbot, OAI-SearchBot, Claude-SearchBot or PerplexityBot. Whether to allow training bots is the site owner's decision, not a visibility requirement; no vendor documents a citation effect from it.

---

## 2. OpenAI Crawlers

Source: https://developers.openai.com/api/docs/bots. Each setting is independent; if both OAI-SearchBot and GPTBot are allowed, OpenAI may use one crawl for both. robots.txt changes take about 24 hours to apply to search.

- **OAI-SearchBot** (`...compatible; OAI-SearchBot/1.4; +https://openai.com/searchbot`): surfaces sites in ChatGPT search. Opted-out sites "will not be shown in ChatGPT search answers, though can still appear as navigational links". OpenAI recommends allowing it.
- **ChatGPT-User** (`...compatible; ChatGPT-User/1.0; +https://openai.com/bot`): user actions in ChatGPT, Custom GPTs and GPT Actions. "Because these actions are initiated by a user, robots.txt rules may not apply." Use OAI-SearchBot, not this, to manage search opt-outs.
- **GPTBot** (`...compatible; GPTBot/1.x; +https://openai.com/gptbot`): content that may be used for training. Disallowing it signals the content should not be used for training.
- **OAI-AdsBot** (`OAI-AdsBot/1.0`): checks landing pages submitted as ChatGPT ads. Not used for training. Irrelevant to GEO unless the client advertises in ChatGPT; don't block it if they do.

---

## 3. Anthropic (Claude) Crawlers

Source: https://support.claude.com/en/articles/8896518 ("Does Anthropic crawl data from the web…").

- **ClaudeBot**: training data. Honours robots.txt, including the non-standard `Crawl-delay`.
- **Claude-SearchBot**: improves Claude's search results. Blocking may reduce visibility in Claude search.
- **Claude-User**: fetches pages when a Claude user asks. "Disabling `Claude-User` on your site prevents our system from retrieving your content in response to a user query." The page says Anthropic's bots honour robots.txt and does not carve out Claude-User.
- **Claude-Agent**: browsers Anthropic hosts (for example in Claude Duet) identify as `Claude-Agent`; details are in a separate support article (18234133), not verified here.
- **Training preference signal**: since 2026-10-30 Anthropic recognises the IETF aipref-based "no AI training" signal (section 12). A robots.txt rule naming ClaudeBot overrides it.

Which web index Claude search uses is not documented by Anthropic. Reports since 2025 list Brave Search as a subprocessor; treat "Claude uses Brave" as plausible but unverified, and don't build a strategy on it.

---

## 4. Google Crawlers and Controls

Sources: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers, .../google-user-triggered-fetchers, https://support.google.com/webmasters/answer/16908024.

- **Googlebot** (smartphone and desktop): Google Search, which also feeds AI Overviews and AI Mode. Google states there are no extra technical requirements or special optimisations for AI features beyond normal Search eligibility.
- **Google-Extended**: a robots.txt product token, not a separate crawler. Controls whether content Google crawls is used to train Gemini models **and** for grounding in Gemini Apps and Grounding with Google Search on Vertex AI. "Google-Extended does not impact a site's inclusion in Google Search nor is it used as a ranking signal." Blocking it is a valid choice for search-but-no-training, but note it also removes the site from Gemini app grounding.
- **Google-Agent**: agents hosted on Google infrastructure that "navigate the web and perform actions upon user request". UA contains `compatible; Google-Agent`; IPs in `user-triggered-agents.json`. As a user-triggered fetcher it "generally ignores robots.txt". Google is testing Web Bot Auth for it under the identity `https://agent.bot.goog` (section 13).
- **Search generative AI control** (Search Console > Settings > Search generative AI; rolled out worldwide 2026-08-31): Include / Exclude / Inherit. **Exclude** removes the site from AI Overviews, AI Mode and Discover's generative AI features while keeping it in Search: "this control isn't used as a ranking or inclusion signal affecting other parts of Search." Takes 1-2 days. It does not affect training (use Google-Extended). For GEO the default (Include) is what you want; check it hasn't been switched to Exclude when a client's AI Overview impressions vanish.
- **Shared training signal**: Google says it intends to support the AIPREF training preference (`user-agent: __usage_ai-training`) in early 2027 (section 12).

---

## 5. Perplexity Crawlers

Source: https://docs.perplexity.ai/guides/bots.

- **PerplexityBot**: indexes for Perplexity search. Honours robots.txt. Perplexity says it is not used to train foundation models.
- **Perplexity-User**: fetches pages for user questions; "generally ignores robots.txt". IP ranges published as JSON.

Perplexity shows numbered inline citations, which makes it the easiest assistant to test by hand. Citation mix (industry study, Profound, data Aug 2024 to Jun 2025, updated Aug 2025): Reddit was 6.6% of all Perplexity citations, and 46.7% of citations within Perplexity's top 10 sources. Quote the two numbers with their denominators; they are often confused.

Publisher revenue: the 2024 Publishers' Program shared ad revenue with partners; the 80% revenue share announced in August 2025 applies to Comet Plus subscription revenue. Current partner count not verified.

---

## 6. Microsoft/Bing Crawlers

- **Bingbot** (`Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)`): Bing Search and Microsoft Copilot. Honours robots.txt.

**Bing and ChatGPT:** OpenAI's ChatGPT search draws partly on Bing. The only measurement found is Seer Interactive's industry study (2025-02-06, 500+ citations for about 100 questions): 87% of SearchGPT citations matched Bing's top 20 results versus 56% for Google; Seer calls the sample limited and the result "directional". Ahrefs (https://ahrefs.com/blog/ai-search-overlap/) measured much lower overlap between AI-cited URLs and either engine's top 10. So: get indexed in Bing (cheap, and Copilot depends on it) and use its AI Performance report, but don't call Bing "the #1 lever for ChatGPT".

**Bing Webmaster Tools AI Performance** (public preview 2026-02-10, extended June and October 2026): citations of your pages in Copilot, Bing AI summaries and partner experiences, the grounding queries behind them, citation share against competitors and topic groupings. The only first-party citation report any AI platform offers; set it up for every client.

---

## 7. Other AI Crawlers

| User-Agent | Company | Purpose | robots.txt |
|-|-|-|-|
| `Applebot` | Apple | Siri, Spotlight, Safari suggestions; renders JS | Honours; with no Applebot group it follows Googlebot's rules |
| `Applebot-Extended` | Apple | Token only, no crawling: controls training use of Applebot data | Honours |
| `Meta-WebIndexer` | Meta | Meta AI search; "Allowing Meta-WebIndexer… helps us cite and link to your content" | Honours |
| `meta-externalagent` | Meta | Training foundation models or indexing | Honours |
| `Meta-ExternalFetcher` | Meta | User-requested fetches, agentic features | "may bypass robots.txt" |
| `FacebookExternalHit` | Meta | Link previews when shared | May bypass for integrity checks |
| `Amazonbot` | Amazon | Products and services; may train Amazon AI models | Honours; no crawl-delay |
| `Amzn-SearchBot` | Amazon | Search experiences such as Alexa; not training | Honours; if unnamed, follows rules given to other search bots |
| `Amzn-User` | Amazon | Live user actions (Alexa queries) | "may not follow all robots.txt directives" |
| `MistralAI-Index` | Mistral | Indexing for Mistral search (Le Chat/Vibe); not training | Honours |
| `MistralAI-User` | Mistral | User-requested fetches with source links | Governs which sites user requests can reach |
| `MistralAI-Training` | Mistral | Training datasets | Honours |
| `DuckAssistBot` | DuckDuckGo | Real-time fetch for cited AI answers; not training | Honours; 72 h to apply; no effect on organic rankings |
| `Bytespider` | ByteDance | Reported as AI training | Not documented by vendor; widely reported to ignore robots.txt |
| `cohere-ai` | Cohere | Historical token | Cohere's current crawler page lists no active crawler |

Sources: support.apple.com/119829, developers.facebook.com/docs/sharing/webmasters/web-crawlers, developer.amazon.com/docs/amazonbot/amazonbot.html, docs.mistral.ai/robots, duckduckgo.com/duckduckgo-help-pages/results/duckassistbot. `FacebookBot` and `Timesbot` appeared in earlier versions of this file; neither is on its vendor's current crawler documentation, so they were dropped.

---

## 8. robots.txt Templates

**The rule that breaks most templates (RFC 9309 section 2.2.1):** a crawler obeys only the group that names it most specifically, and ignores `User-agent: *` entirely once it has its own group. Rules do not inherit. A template that gives `GPTBot` an `Allow: /` group and lists `/admin/` only under `*` lets GPTBot crawl `/admin/`. So:
- If every bot gets the same rules, name none of them. The `*` group alone covers everyone, including bots launched next month.
- Name a bot only to treat it differently, and then repeat every shared `Disallow` line in its group. Several `User-agent` lines can share one group.
- `geo_probe.py` flags named groups that skip the `*` group's Disallow lines (`robots-named-group-skips-wildcard`).

Allowing training bots is a decision for the site owner (content licensing, competitive concerns), not a GEO default. Ask, then pick a template.

### Maximum visibility, training allowed

```
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /cart/
Disallow: /checkout/
Disallow: /my-account/

Sitemap: https://yoursite.com/sitemap.xml
```

### Search and answers yes, training no

```
# Training bots and tokens: blocked everywhere
User-agent: GPTBot
User-agent: ClaudeBot
User-agent: Google-Extended
User-agent: Applebot-Extended
User-agent: meta-externalagent
User-agent: MistralAI-Training
User-agent: Amazonbot
User-agent: Bytespider
Disallow: /

# Everyone else, including Googlebot, Bingbot and the AI search bots
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /cart/
Disallow: /checkout/
Disallow: /my-account/

Sitemap: https://yoursite.com/sitemap.xml
```

Google-Extended also controls Gemini app grounding (section 4), so blocking it costs some Gemini visibility; tell the client. If ClaudeBot needs a crawl delay, give it its own group with `Crawl-delay: 10` plus every shared Disallow line.

---

## 9. Platform Submission Guide

### Google Search Console
- URL: https://search.google.com/search-console
- Submit: XML sitemap
- Feeds: Google Search, AI Overviews, AI Mode, Gemini grounding
- Monitor: Generative AI performance report (section 10). Check Settings > Search generative AI is not on Exclude.

### Bing Webmaster Tools
- URL: https://www.bing.com/webmasters
- Submit: XML sitemap; implement IndexNow
- Feeds: Bing, Copilot, partners (ChatGPT search draws partly on Bing)
- Monitor: AI Performance report (section 6)

### Perplexity, Claude, Mistral, DuckDuckGo
- No manual submission. Allow their search/index bots and keep the site in Google and Bing; assistants without their own complete index fall back on search APIs.

### Google Business Profile
- URL: https://business.google.com
- Critical for local/service businesses: local AI answers draw on it. Complete services, hours, photos and posts.

### Merchant feeds (online shops only)
- Google Merchant Center product feeds feed Shopping and agentic checkout in AI Mode/Gemini (select merchants, US/CA/AU at time of writing).
- OpenAI accepts product feeds and Agentic Commerce Protocol onboarding from approved partners (https://developers.openai.com/commerce/guides/get-started); Instant Checkout was scaled back in 2026.
- Perplexity Instant Buy (US-focused).
- For a shop client, a clean, complete product feed is worth more than any on-page GEO tweak. Brochure sites skip this.

---

## 10. AI Traffic and Citation Measurement

Use the first-party reports first; regexes and prompt tests fill gaps.

### Google Search Console: Generative AI performance report
Announced 2026-06-03 (https://developers.google.com/search/blog/2026/06/gen-ai-performance-reports): impressions (no clicks) for AI Overviews and AI Mode, rolled out worldwide 2026-08-31; Discover's AI features have a separate report (https://support.google.com/webmasters/answer/16984139). This replaces the old workaround of filtering long, conversational queries in the Web report.

### Bing Webmaster Tools: AI Performance
See section 6. The only first-party citation counts available.

### GA4: AI Assistant channel
Since 2026-05-13 GA4's Default Channel Group has an **AI Assistant** channel (medium `ai-assistant`) for referrals from recognised assistants "like ChatGPT, Gemini, and Claude"; a June 2026 Source Group adds groupings for ChatGPT and Perplexity. AI Overviews and AI Mode clicks still land in Organic Search. Google doesn't publish the recognised source list, so for older properties, custom channel groups or a cross-check, keep a source regex:

```
chatgpt\.com|chat\.openai\.com|perplexity\.ai|claude\.ai|gemini\.google\.com|copilot\.microsoft\.com|grok\.com|chat\.deepseek\.com|chat\.mistral\.ai|meta\.ai|poe\.com|duck\.ai|notebooklm\.google\.com|you\.com|phind\.com
```

Apply it to session source, not landing page.

### Dark AI traffic
Agentic browsers and copied links arrive as direct traffic. Add "How did you find us?" to lead forms (ChatGPT, Claude, Perplexity, Google AI answer, Other AI tool).

---

## 11. Agentic Browsers

Full browsers where an AI agent drives a real session. They are not crawlers and mostly can't be managed with robots.txt.

| Product | Company | Notes |
|-|-|-|
| Atlas | OpenAI | Launched October 2025; agent mode runs multi-step tasks |
| Comet | Perplexity | Chromium-based; traffic looks like normal Chrome |
| Gemini in Chrome | Google | Agentic features in Chrome; Google-hosted agents identify as Google-Agent |
| Claude in Chrome / Claude Duet | Anthropic | Hosted browsers identify as `Claude-Agent` |

**Implications:**
- Locally run agentic browsers look like human sessions; hosted agents increasingly identify themselves (Google-Agent, Claude-Agent, Web Bot Auth signatures, section 13).
- They work through the rendered page and the accessibility tree, which is why Lighthouse's Agentic Browsing category audits a11y and CLS (technical-checklist section 13).
- A site that works for keyboard and screen-reader users works for agents. Unlabelled buttons, broken forms and layout shift break agent tasks, and the sale with them.

---

## 12. Content Signals and Training Preferences

### Cloudflare Content Signals (September 2025)

```
User-agent: *
Content-Signal: search=yes, ai-input=yes, ai-train=no
Allow: /
```

Signals: `search` (build a search index), `ai-input` (use in AI answers at query time), `ai-train` (training). Cloudflare's managed robots.txt, used by more than 3.8 million domains at launch (Cloudflare, 2025-09-24), adds `search=yes, ai-train=no`. Google Search Console may flag the line as "Syntax not understood"; that's cosmetic.

**Audit points:**
- Behind Cloudflare, fetch the LIVE robots.txt; a managed policy may be layered over the site's own file. A client chasing AI visibility may be sending "don't train" without knowing it.
- `ai-input=no` works directly against AI citation. `ai-train=no` does not affect answers.
- CDN bot management (Bot Fight Mode, WAF rules, security plugins) can block AI crawlers before robots.txt is read. Test with `curl -A "GPTBot" https://site.com/` and look for 403s or challenges; a spoofed UA can't prove what the real bot from its real IPs gets, so confirm in server logs when it matters.

### IETF AI Preferences (aipref)

A vendor-neutral way to say "no AI training", still an IETF draft (vocabulary draft-ietf-aipref-vocab, September 2026).
- Anthropic honours a training preference signal based on the draft since 2026-10-30, rolling out across its services; a robots.txt rule naming ClaudeBot overrides it.
- Google's crawler page says it intends to support `user-agent: __usage_ai-training` in early 2027; Google-Extended stays (blog, 2026-10-30: https://developers.google.com/search/blog/2026/10/ai-training-control).
- It expresses a training preference and doesn't affect Search or AI Overviews. **Exception:** Google plans to treat the shared opt-out as a Google-Extended disallow when Google-Extended isn't named, and only sites that allow Google-Extended are eligible for Gemini app grounding. A client who opts out of training but wants Gemini citations needs an explicit `User-agent: Google-Extended` group allowing it (with the shared Disallow lines). Don't deploy it for a client who wants maximum visibility, and don't copy Cloudflare's Content-Signal syntax for it: they are different mechanisms. Recheck syntax and adopters before using it; the draft is moving.

---

## 13. Agent Identity and Markdown Delivery

### Web Bot Auth (signed agents)
An IETF draft where bots sign requests with HTTP Message Signatures (RFC 9421) so a site or CDN can verify who is calling, instead of trusting the User-Agent header. Cloudflare verifies signed bots (https://developers.cloudflare.com/bots/reference/bot-verification/web-bot-auth/) and Google is testing it for Google-Agent. For GEO: when a WAF blocks "bots", allow verified AI search bots and signed agents rather than whitelisting UA strings that anyone can spoof.

### Markdown for Agents (content negotiation)
Cloudflare (beta, paid plans, announced 2026-02-12) converts HTML to Markdown when a request sends `Accept: text/markdown`; some coding agents (Claude Code, OpenCode) send that header. A site can do the same itself: return Markdown for `Accept: text/markdown`, HTML otherwise, with `Vary: Accept`. Keep the Markdown identical in substance to the HTML: serving agents different claims than humans is cloaking. This is stronger than `<link rel="alternate" type="text/markdown">` (technical-checklist section 9), which an agent has to notice and follow. Low priority for brochure sites; worthwhile for documentation and content-heavy sites.
