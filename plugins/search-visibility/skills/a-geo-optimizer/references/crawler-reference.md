# AI Crawler Reference

Complete reference of AI crawler user-agents, which platforms they serve, and how to configure access.

## Table of Contents

1. [Crawler Quick Reference Table](#1-crawler-quick-reference-table)
2. [OpenAI Crawlers](#2-openai-crawlers)
3. [Anthropic (Claude) Crawlers](#3-anthropic-claude-crawlers)
4. [Google AI Crawlers](#4-google-ai-crawlers)
5. [Perplexity Crawlers](#5-perplexity-crawlers)
6. [Microsoft/Bing Crawlers](#6-microsoftbing-crawlers)
7. [Other AI Crawlers](#7-other-ai-crawlers)
8. [Complete robots.txt Template](#8-complete-robotstxt-template)
9. [Platform Submission Guide](#9-platform-submission-guide)
10. [GA4 AI Traffic Tracking](#10-ga4-ai-traffic-tracking)
11. [Agentic Browsers](#11-agentic-browsers)
12. [Content Signals in robots.txt](#12-content-signals-in-robotstxt)

---

## 1. Crawler Quick Reference Table

| User-Agent | Company | Purpose | Block = |
|-----------|---------|---------|---------|
| `GPTBot` | OpenAI | Training data collection | Less model familiarity |
| `OAI-SearchBot` | OpenAI | Search index for ChatGPT Search | Invisible in ChatGPT search |
| `ChatGPT-User` | OpenAI | Real-time user-triggered fetch | May not respect robots.txt |
| `ClaudeBot` | Anthropic | Training data collection | Less model familiarity |
| `Claude-SearchBot` | Anthropic | Search index for Claude web search | Invisible in Claude search |
| `Claude-User` | Anthropic | Real-time user-triggered fetch | May not respect robots.txt |
| `Googlebot` | Google | Search index (also feeds AI Overviews) | No Google visibility at all |
| `Google-Extended` | Google | Gemini training data only | No Gemini training (AI Overviews unaffected) |
| `PerplexityBot` | Perplexity | Search index + real-time crawl | Invisible in Perplexity |
| `Bingbot` | Microsoft | Bing index (feeds ChatGPT + Copilot) | No Bing/ChatGPT/Copilot visibility |

**Key insight:** For maximum AI search visibility, you must allow at minimum: OAI-SearchBot, ChatGPT-User, Claude-SearchBot, Claude-User, PerplexityBot, Googlebot, and Bingbot. The training crawlers (GPTBot, ClaudeBot, Google-Extended) are optional but recommended.

---

## 2. OpenAI Crawlers

**GPTBot**
- Purpose: Collects web content for training OpenAI models
- User-agent string: `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; GPTBot/1.0; +https://openai.com/gptbot)`
- Respects: robots.txt
- Impact of blocking: 73% fewer ChatGPT citations (correlation, not direct causation)

**OAI-SearchBot**
- Purpose: Indexes content for ChatGPT's web search feature
- User-agent string: `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; OAI-SearchBot/1.0; +https://openai.com/searchbot)`
- Respects: robots.txt
- Impact of blocking: Removed from ChatGPT search results

**ChatGPT-User**
- Purpose: Real-time page fetching when a user's conversation triggers web lookup
- User-agent string: `Mozilla/5.0 AppleWebKit/537.36 (KHTML, like Gecko; compatible; ChatGPT-User/1.0; +https://openai.com/bot)`
- Respects: robots.txt partially (operates on behalf of human user)
- Impact of blocking: Reduced but not eliminated ChatGPT access

---

## 3. Anthropic (Claude) Crawlers

**ClaudeBot**
- Purpose: Collects web content for training Claude models
- User-agent string: `claudebot` (case variations exist)
- Respects: robots.txt (including non-standard Crawl-delay directive)
- Impact of blocking: Less model familiarity with your content

**Claude-SearchBot**
- Purpose: Indexes content for Claude's web search (via Brave Search supplementation)
- User-agent string: `Claude-SearchBot`
- Respects: robots.txt
- Impact of blocking: Reduced visibility in Claude web search

**Claude-User**
- Purpose: Real-time fetching during user conversations with web search enabled
- User-agent string: `Claude-User`
- Respects: robots.txt partially (operates on behalf of human user)
- Impact of blocking: Reduced but not eliminated Claude access

**Note:** Claude's search primarily uses Brave Search's independent index. Ensure your site is visible in Brave Search for maximum Claude visibility.

---

## 4. Google AI Crawlers

**Googlebot**
- Purpose: Google's main search crawler. Feeds both traditional search AND AI Overviews.
- User-agent string: Various (Googlebot, Googlebot-Mobile, etc.)
- Respects: robots.txt
- Impact of blocking: Complete loss of Google search AND AI Overview visibility
- **Critical:** You CANNOT block AI Overviews without losing all Google search visibility. There is no separate AI Overview crawler.

**Google-Extended**
- Purpose: Controls training data for Gemini and Vertex AI products
- User-agent string: `Google-Extended`
- Respects: robots.txt
- Impact of blocking: Blocks Gemini training. Does NOT affect AI Overviews or Google Search.
- **Note:** Blocking Google-Extended is a viable choice if you want search visibility but don't want to contribute to Gemini training.

---

## 5. Perplexity Crawlers

**PerplexityBot**
- Purpose: Indexes content for Perplexity's AI search engine
- User-agent string: `PerplexityBot`
- Respects: robots.txt
- Impact of blocking: Invisible in Perplexity search results

Perplexity maintains its own independent index. It's the most citation-transparent platform (numbered inline citations in every response). Reddit content dominates at 46.5% of Perplexity citations.

**Perplexity Publishers' Program:** Partnership program with revenue sharing (80/20 split favoring publishers). Currently 30+ partners including TIME, Fortune, Der Spiegel.

---

## 6. Microsoft/Bing Crawlers

**Bingbot**
- Purpose: Bing's main search crawler. Feeds Bing Search, ChatGPT (via Bing), and Microsoft Copilot.
- User-agent string: `Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)`
- Respects: robots.txt
- Impact of blocking: Complete loss of Bing, ChatGPT (Bing-backed), and Copilot visibility

**Critical:** Bingbot is the single most impactful crawler for ChatGPT visibility. Industry analyses have reported ~87% overlap between ChatGPT citations and Bing's top results (figure undated, verify against a current source before quoting). If you do nothing else, make sure Bingbot can access your site and you've submitted to Bing Webmaster Tools.

**Bing Content Submission API:** Enables pushing structured facts directly for Copilot sidebar answers.

---

## 7. Other AI Crawlers

| User-Agent | Company | Purpose |
|-----------|---------|---------|
| `cohere-ai` | Cohere | Training/search |
| `Bytespider` | ByteDance | Training for AI products |
| `Applebot` | Apple | Apple Intelligence/Siri |
| `Applebot-Extended` | Apple | Apple Intelligence training |
| `FacebookBot` | Meta | Meta AI features |
| `meta-externalagent` | Meta | Meta AI training |
| `Amazonbot` | Amazon | Alexa/AI features |
| `Timesbot` | Perplexity (for publisher partners) | Premium content |

---

## 8. Complete robots.txt Template

### Maximum AI Visibility (recommended)

```
# Standard search
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# AI Search (required for AI search visibility)
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

# AI Training (recommended for maximum citation likelihood)
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /
Crawl-delay: 10

User-agent: Google-Extended
Allow: /

# Apple Intelligence
User-agent: Applebot
Allow: /

User-agent: Applebot-Extended
Allow: /

# Blocked paths (customize per site)
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /tmp/
Disallow: /private/
Disallow: /wp-admin/
Disallow: /cart/
Disallow: /checkout/
Disallow: /my-account/

Sitemap: https://yoursite.com/sitemap.xml
```

### Selective (search only, no training)

```
# Standard search
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# AI Search only
User-agent: OAI-SearchBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Claude-SearchBot
Allow: /

User-agent: Claude-User
Allow: /

User-agent: PerplexityBot
Allow: /

# Block AI training
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: Google-Extended
Disallow: /

Sitemap: https://yoursite.com/sitemap.xml
```

---

## 9. Platform Submission Guide

### Google Search Console
- URL: https://search.google.com/search-console
- Submit: XML sitemap
- Feeds: Google Search + AI Overviews + Gemini
- Monitor: Performance report (AI Overview data merged under "Web" search type)

### Bing Webmaster Tools
- URL: https://www.bing.com/webmasters
- Submit: XML sitemap + implement IndexNow
- Feeds: Bing + ChatGPT + Microsoft Copilot
- **This is the #1 priority submission for ChatGPT visibility**

### Brave Search
- Brave uses its own independent index (Web Discovery Project)
- No manual submission process
- Focus on standard SEO + allowing Brave's crawler
- Claude's search draws from Brave's index

### Perplexity
- No manual submission
- Allow PerplexityBot in robots.txt
- Perplexity's own index discovers content independently
- Publishers' Program for partnership: https://www.perplexity.ai/hub/partnerships

### Google Business Profile
- URL: https://business.google.com
- Critical for local/service businesses
- Primary data source for AI local recommendations
- Complete all fields: services, hours, photos, Q&A, posts

---

## 10. GA4 AI Traffic Tracking

### Create an AI referral traffic segment

In GA4, go to Explore > create a custom segment with traffic source filter:

**Regex for AI referral sources:**
```
perplexity\.ai|chatgpt\.com|chat\.openai\.com|claude\.ai|gemini\.google\.com|copilot\.microsoft\.com|you\.com|phind\.com
```

Apply this to:
- Session source/medium (for full session data)
- Landing page (to see which pages AI tools are sending traffic to)

### Track AI-influenced conversions

Add "How did you find us?" to lead forms with options:
- ChatGPT
- Claude
- Perplexity
- Google AI Overview
- Other AI tool

This captures dark AI traffic (users who get a recommendation from AI but then go straight to your site).

### Isolate likely AI Overview impressions in Google Search Console

No direct filter exists. Workarounds:
- Filter by query length (10+ words)
- Filter by conversational keywords: "compare", "top", "best", "vs", "how to", "what is"
- These queries are more likely to trigger AI Overviews

---

## 11. Agentic Browsers

A category that matters since late 2025: full browsers where an AI agent drives real user sessions. These are NOT crawlers and mostly cannot be managed via robots.txt.

| Product | Company | Notes |
|-|-|-|
| Atlas | OpenAI | Launched October 2025. Agent Mode executes multi-step tasks autonomously |
| Comet | Perplexity | Chromium-based; traffic looks like a normal Chrome session |
| Gemini in Chrome | Google | The main consumer of WebMCP tools during the origin trial |

**Implications for GEO:**
- Their traffic is largely indistinguishable from human sessions in analytics; you cannot segment it with a user-agent regex.
- They interact with your site through the rendered page and the accessibility tree, which is why Lighthouse's Agentic Browsing category audits a11y and CLS (see technical-checklist section 13).
- Sites that work well for keyboard/screen-reader users work well for agentic browsers. Broken forms, unlabeled buttons, and layout shift break agent task completion (and the sale that came with it).

---

## 12. Content Signals in robots.txt

Cloudflare's Content Signals Policy (September 2025) extends robots.txt with usage-category signals, expressed per user-agent group:

```
User-agent: *
Content-Signal: search=yes, ai-input=yes, ai-train=no
Allow: /
```

The three signals: `search` (build a search index), `ai-input` (feed content into AI answers at query time, i.e. RAG/grounding), `ai-train` (training or fine-tuning). The policy text frames restrictions as an express reservation of rights under EU DSM Directive 2019/790 Article 4.

**Why a GEO skill cares:**
- **Cloudflare's managed robots.txt injects `search=yes, ai-train=no` for 3.8M+ domains.** If the site sits behind Cloudflare, fetch the LIVE robots.txt and check whether a managed policy has been layered on top of (or replaces) the site's own file. A client maximizing AI visibility may be sending "don't train on me" without knowing it.
- For maximum AI visibility, either omit content signals entirely or set them permissively. `ai-input=no` works against citation in AI answers.
- Same audit lesson as user-agents: the robots.txt you deploy is not always the robots.txt the world sees. CDN-level bot management (Cloudflare Bot Fight Mode, WAF rules, security plugins) can also block AI crawlers before robots.txt is ever read; test with `curl -A "GPTBot" https://site.com/` and check for 403s.
