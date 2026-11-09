# Technical Checklist for AI Search Visibility

Complete technical implementation guide. Work through sequentially for new builds, or use as an audit checklist for existing sites.

## Table of Contents

1. [Server-Side Rendering](#1-server-side-rendering)
2. [Robots.txt Configuration](#2-robotstxt-configuration)
3. [Schema.org Structured Data](#3-schemaorg-structured-data)
4. [XML Sitemap + RSS/Atom Feed](#4-xml-sitemap--rssatom-feed)
5. [llms.txt File](#5-llmstxt-file)
6. [Page Speed Optimization](#6-page-speed-optimization)
7. [Search Console Submissions](#7-search-console-submissions)
8. [IndexNow Implementation](#8-indexnow-implementation)
9. [Markdown Alternate Links](#9-markdown-alternate-links)
10. [Meta Tags for AI Extraction](#10-meta-tags-for-ai-extraction)
11. [HTTPS and Security](#11-https-and-security)
12. [Internal Linking Architecture](#12-internal-linking-architecture)
13. [Lighthouse Agentic Browsing Audit](#13-lighthouse-agentic-browsing-audit)

---

## 1. Server-Side Rendering

**Priority: CRITICAL. This is a binary gate**

The major AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot) do not execute JavaScript: Vercel and MERJ's 2024 analysis of their fetches found no JS rendering. Googlebot and Applebot render JS, and agentic browsers run full pages, but content that only exists after JS runs is invisible to the bots that feed ChatGPT, Claude and Perplexity. Server-rendered HTML remains the safe default.

**Audit check:**
```bash
# Test what a non-JS crawler sees
curl -s -A "GPTBot" https://yoursite.com/page | grep -c "your-expected-content"
# If 0 matches, your content is invisible to AI crawlers
```

**For PHP sites:** This is rarely an issue since PHP renders server-side. But check for:
- Content loaded via AJAX after page load
- React/Vue/Angular widgets embedded in PHP pages
- Lazy-loaded content that requires scroll events
- Content behind JavaScript tabs/accordions (use `<details>`/`<summary>` instead)

**For JS frameworks (React, Vue, Angular, Next.js, Nuxt):**
- Enable SSR or Static Site Generation (SSG)
- Use `getServerSideProps` (Next.js) or equivalent
- Pre-render critical pages at minimum

---

## 2. Robots.txt Configuration

**Priority: CRITICAL. Blocking a search/index bot removes the site from that assistant's answers**

Templates, the user-agent list and what each bot does are in `crawler-reference.md` sections 1 and 8. Two things to get right:
- **Named groups don't inherit `User-agent: *`** (RFC 9309). If every bot gets the same rules, use only the `*` group. If a bot gets its own group, repeat every shared Disallow line in it, or it may crawl `/admin/`, `/checkout/` and the rest.
- **Three kinds of bot.** Search/index bots (OAI-SearchBot, Claude-SearchBot, PerplexityBot, Googlebot, Bingbot) decide whether you appear in AI answers. User-triggered fetchers (ChatGPT-User, Claude-User, Perplexity-User, Google-Agent) load a page because a person asked, and most vendors say they may ignore robots.txt. Training bots and tokens (GPTBot, ClaudeBot, Google-Extended, Applebot-Extended) govern model training, and allowing them is the site owner's call, not a visibility requirement. Google-Extended also controls Gemini app grounding.

**Audit check:**
```bash
# Fetch and inspect current robots.txt
curl -s https://yoursite.com/robots.txt
# Look for blanket "Disallow: /" rules or blocks on AI user-agents
```

---

## 3. Schema.org Structured Data

**Priority: HIGH for entities (Organization, Person, Product, LocalBusiness, Article); optional elsewhere**

Google says AI Overviews and AI Mode need no special schema; structured data earns Google rich results and states entities unambiguously. No published evidence shows schema itself raising AI citations. (An often-quoted "GPT-4 accuracy 16% to 54%" comes from a knowledge-graph study on enterprise SQL databases, not website markup; don't cite it for schema.)

Schema should be:
- JSON-LD (Google's recommended format; Microdata and RDFa also work)
- In the server-rendered HTML, so non-JS AI crawlers see it; `<head>` or body both work
- Accurately matching visible page content (mismatches reduce trust)

### Schema templates by page type

**Organization (site-wide, on every page):**
```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Company Name",
  "url": "https://yoursite.com",
  "logo": "https://yoursite.com/logo.png",
  "description": "One-sentence description of what you do",
  "foundingDate": "2020",
  "address": {
    "@type": "PostalAddress",
    "streetAddress": "123 Main St",
    "addressLocality": "Zagreb",
    "addressCountry": "HR"
  },
  "contactPoint": {
    "@type": "ContactPoint",
    "email": "info@yoursite.com",
    "contactType": "customer service"
  },
  "sameAs": [
    "https://www.linkedin.com/company/yourcompany",
    "https://www.facebook.com/yourcompany",
    "https://twitter.com/yourcompany"
  ]
}
```

**Article / BlogPosting:**
```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article Title Here",
  "description": "2-sentence summary of what this article covers",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "url": "https://yoursite.com/about/author-name",
    "jobTitle": "Author's Role/Title",
    "sameAs": ["https://linkedin.com/in/author"]
  },
  "publisher": {
    "@type": "Organization",
    "name": "Your Company Name",
    "logo": { "@type": "ImageObject", "url": "https://yoursite.com/logo.png" }
  },
  "datePublished": "2026-03-01",
  "dateModified": "2026-03-20",
  "mainEntityOfPage": "https://yoursite.com/blog/article-slug",
  "image": "https://yoursite.com/images/article-hero.jpg"
}
```

**FAQPage (optional):** Google stopped showing FAQ rich results on 2026-05-07; the markup is still valid but earns nothing visible in Google. Keep a visible Q&A section when readers ask those questions; add the schema only if it's free to generate.
```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is [topic]?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "A direct, complete answer to the question."
      }
    },
    {
      "@type": "Question",
      "name": "How does [topic] compare to [alternative]?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "Specific comparison with concrete details."
      }
    }
  ]
}
```

**Product (for e-commerce/service pages):**
```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Product Name",
  "description": "Clear product description",
  "image": "https://yoursite.com/images/product.jpg",
  "brand": { "@type": "Brand", "name": "Brand Name" },
  "sku": "SKU-12345",
  "offers": {
    "@type": "Offer",
    "price": "99.00",
    "priceCurrency": "EUR",
    "availability": "https://schema.org/InStock",
    "url": "https://yoursite.com/products/product-name"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4.5",
    "reviewCount": "42"
  }
}
```

**HowTo (optional; Google dropped HowTo rich results in 2023):**
```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to [do thing]",
  "description": "Brief overview",
  "step": [
    {
      "@type": "HowToStep",
      "name": "Step 1 title",
      "text": "Step 1 instructions"
    }
  ]
}
```

**LocalBusiness (for agency/local service sites):**
```json
{
  "@context": "https://schema.org",
  "@type": "ProfessionalService",
  "name": "Agency Name",
  "description": "What you do in one sentence",
  "url": "https://yoursite.com",
  "address": { ... },
  "geo": { "@type": "GeoCoordinates", "latitude": "45.815", "longitude": "15.982" },
  "openingHours": "Mo-Fr 09:00-17:00",
  "priceRange": "$$",
  "areaServed": "Croatia"
}
```

### PHP implementation pattern

```php
// In your base template or header include
function render_schema_jsonld(array $schema_data): string {
    return '<script type="application/ld+json">' .
           json_encode($schema_data, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT) .
           '</script>';
}

// Per page template, build the schema array and render in <head>
$schema = [
    '@context' => 'https://schema.org',
    '@type' => 'Article',
    'headline' => $article->title,
    'datePublished' => $article->published_at,
    'dateModified' => $article->updated_at,
    // ... etc
];
echo render_schema_jsonld($schema);
```

---

## 4. XML Sitemap + RSS/Atom Feed

**Priority: HIGH**

**XML Sitemap requirements:**
- Include all indexable pages
- Accurate `<lastmod>` timestamps (critical for AI crawlers detecting fresh content)
- Split by content type if site is large (blog-sitemap.xml, product-sitemap.xml)
- Submit to both Google Search Console AND Bing Webmaster Tools
- Reference in robots.txt: `Sitemap: https://yoursite.com/sitemap.xml`

**RSS/Atom feed:**
- Google recommends pairing sitemaps with RSS/Atom feeds for change detection
- Microsoft's NLWeb protocol uses RSS feeds as a primary data source
- Include at minimum: title, link, description, pubDate/updated, author
- Auto-generate from your CMS or build a `/feed.xml` endpoint

```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Site Name</title>
    <link>https://yoursite.com</link>
    <description>Site description</description>
    <atom:link href="https://yoursite.com/feed.xml" rel="self" type="application/rss+xml"/>
    <item>
      <title>Article Title</title>
      <link>https://yoursite.com/blog/slug</link>
      <description>First 200 chars of article</description>
      <pubDate>Wed, 20 Mar 2026 10:00:00 +0000</pubDate>
      <guid>https://yoursite.com/blog/slug</guid>
    </item>
  </channel>
</rss>
```

---

## 5. llms.txt File

**Priority: LOW-MEDIUM (uneven adoption as a retrieval source, but since 2026 Lighthouse/PageSpeed Insights audits the file, so one that fails its checks shows up as a red audit to anyone who tests your site)**

Place at `https://yoursite.com/llms.txt`. Markdown-formatted overview of your site for AI consumption. Takes minutes to create, costs nothing.

**Format is now machine-checked.** Lighthouse's llms-txt audit (Agentic Browsing category, see section 13) runs three regular expressions over the raw file, per its source (`core/audits/agentic/llms-txt.js` in the GoogleChrome/lighthouse repo, checked 2026-10-11). It fails the file when any of these is missing:
- An H1 header anywhere in the file (`# Title`).
- At least one markdown link, `[text](url)`. Plain `Title: URL` lines do not count and fail with "File does not appear to contain any links".
- At least 50 characters.

A server error when fetching the file also fails the audit; a 404 is reported as not applicable, because the file is optional. Lighthouse checks nothing else: section order, blockquotes and H2 sections are the llmstxt.org format, worth following, but not part of the audit. `geo_probe.py` reports the three Lighthouse checks as `llms-format` and its own spec heuristic (the H1 should be the first line) separately as low-severity `llms-spec`.

```markdown
# Site Name

> One-sentence description of what this site is about.

## About
Brief 2-3 sentence description of the organization, what it does, who it serves.

## Key Pages
- [Homepage](https://yoursite.com/): Brief description
- [Services](https://yoursite.com/services/): What services are offered
- [Blog](https://yoursite.com/blog/): Topics covered

## Popular Content
- [Article Title](https://yoursite.com/blog/article): One-line summary
- [Guide Title](https://yoursite.com/guides/guide): One-line summary

## Contact
- Email: info@yoursite.com
- Location: Zagreb, Croatia
```

Optionally create `llms-full.txt`: the same overview followed by the full markdown of your key pages/articles, so a tool gets deep context in one fetch. This is cheap when the site already exposes per-page markdown (e.g. a `/article/markdown` endpoint or a content/export service): a single route can concatenate the `llms.txt` intro with each published page's markdown. Serve it `X-Robots-Tag: noindex, follow` (it duplicates page bodies, so avoid search-index duplicate content) and exclude any gated/premium content so you don't leak it. When you bound the dump (top-N, page cap), say what was dropped rather than silently truncating.

**Priority:** LOW / optional. Future-proofing, not a required output.

**Current status (checked 2026-11-08):** Google's AI optimization guide says Search does not use llms.txt. No major AI provider (OpenAI, Google, Anthropic, Meta, Mistral) has published a statement that its answer systems read customer sites' llms.txt; providers publishing their own llms.txt for their docs is not the same thing. Server-log studies (industry, e.g. Ahrefs) report that most llms.txt files get almost no requests. The real consumers are coding agents and docs tools that fetch it for documentation sites. What did change: Lighthouse and PageSpeed Insights validate the file (section 13), so a malformed one shows as a failed audit. Bottom line: don't prioritize it over robots.txt, content, sitemap or schema; if you ship one, make it pass the three Lighthouse checks. For agents, Markdown content negotiation (`crawler-reference.md` section 13) is the more direct route.

---

## 6. Page Speed Optimization

**Priority: HIGH**

Target metrics:
- Time to First Byte (TTFB): < 200ms (crawlers fetch HTML; this is what they feel)
- First Contentful Paint (FCP): < 1.8s (Google's "good"); faster is better
- Largest Contentful Paint (LCP): < 2.5 seconds

An SE Ranking industry study (2025-11) found pages with very fast FCP were cited more by ChatGPT. That is a correlation (fast sites tend to be well-built, authoritative sites), not proof that speed causes citation; don't promise a multiplier. Speed matters regardless because AI fetchers work on tight time budgets and slow or timed-out pages can't be quoted.

Quick wins for PHP sites:
- Enable OPcache
- Use a reverse proxy cache (Varnish, Nginx FastCGI cache)
- Optimize images (WebP, lazy loading for below-fold)
- Minimize CSS/JS blocking resources
- Use a CDN for static assets
- Database query optimization (avoid N+1 queries)

---

## 7. Search Console Submissions

**Priority: HIGH**

Submit your sitemap to both:
- **Google Search Console**: https://search.google.com/search-console
- **Bing Webmaster Tools**: https://www.bing.com/webmasters

Bing matters because Copilot runs on it and ChatGPT search draws partly on it (evidence and limits in `crawler-reference.md` section 6). Both consoles now report AI visibility: Google's Generative AI performance report and Bing's AI Performance report (citations and grounding queries). Turn both on; they are the only first-party AI numbers available.

In Google Search Console, also check Settings > Search generative AI. It should be on Include (the default); Exclude removes the site from AI Overviews and AI Mode.

---

## 8. IndexNow Implementation

**Priority: MEDIUM-HIGH**

IndexNow instantly notifies Bing (and so Copilot) and other participating engines when content is published or updated. Google does not use IndexNow.

```php
// After publishing or updating content
function notify_indexnow(string $url, string $api_key): void {
    $endpoint = "https://api.indexnow.org/indexnow";
    $params = http_build_query([
        'url' => $url,
        'key' => $api_key,
        'host' => parse_url($url, PHP_URL_HOST),
    ]);

    $ch = curl_init("{$endpoint}?{$params}");
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    curl_exec($ch);
    curl_close($ch);
}
```

Place your API key file at `https://yoursite.com/{api-key}.txt`.

---

## 9. Markdown Alternate Links

**Priority: LOW (experimental, but zero-cost if you have Markdown source)**

If you write content in Markdown (e.g., from Obsidian, a CMS, or a static site generator), serve the raw Markdown version alongside HTML and signal it:

```html
<link rel="alternate" type="text/markdown" href="/blog/post-slug.md" />
```

AI models process Markdown natively. This gives them a clean, uncluttered version of your content. Stronger option: answer `Accept: text/markdown` requests with the Markdown version directly (content negotiation, with `Vary: Accept`), which some agents already send; see `crawler-reference.md` section 13. Either way, the Markdown must say the same thing as the HTML.

---

## 10. Meta Tags for AI Extraction

**Priority: MEDIUM**

Ensure every important page has:
```html
<meta name="description" content="Concise, factual 150-160 char description" />
<meta name="author" content="Author Name" />
<meta property="og:title" content="Page Title" />
<meta property="og:description" content="Same as meta description" />
<meta property="og:type" content="article" />
<meta property="og:url" content="https://yoursite.com/page" />
<meta property="og:image" content="https://yoursite.com/images/og-image.jpg" />
<meta property="article:published_time" content="2026-03-01T10:00:00Z" />
<meta property="article:modified_time" content="2026-03-20T10:00:00Z" />
```

---

## 11. HTTPS and Security

**Priority: CRITICAL (baseline requirement)**

All pages must be served over HTTPS. This is a ranking factor for Google/Bing and a trust signal for AI systems. No exceptions.

---

## 12. Internal Linking Architecture

**Priority: HIGH**

Google documents "query fan-out" for AI Overviews and AI Mode: one question is split into several related searches, and the answer draws on pages for each. A site that covers a topic's subquestions on well-linked pages has more chances to be pulled in. Structure sites as topic clusters:
- **Pillar page**: Comprehensive overview of a topic (2000+ words)
- **Cluster pages**: Detailed sub-topic articles linking back to pillar
- **Bidirectional links**: Pillar links to clusters, clusters link to pillar
- Use descriptive anchor text (not "click here")

---

## 13. Lighthouse Agentic Browsing Audit

**Priority: MEDIUM (new in 2026, the first mainstream tool that grades agent-readiness; category is explicitly "under development and subject to change")**

Chrome Lighthouse (Chrome 150+, also surfaced on pagespeed.web.dev) added an "Agentic Browsing" category that scores how well a site works for AI agents. Unlike other categories there is no 0-100 weighted score: each audit reports pass/fail (or a pass ratio) independently.

**What it checks:**

1. **llms.txt presence and format**: see section 5 for the three checks (an H1, at least one markdown `[text](url)` link, at least 50 characters).
2. **WebMCP integration**: WebMCP lets a page expose callable tools to AI agents (`document.modelContext.registerTool()` in the current draft) instead of the agent guessing at the UI. It is a Web Machine Learning Community Group draft (2026-11-02), "not a W3C Standard nor … on the W3C Standards Track", and the API has changed between drafts (earlier versions used `navigator.modelContext` and a declarative HTML form that the current draft drops). Chrome runs an origin trial from Chrome 149; the Lighthouse audit only passes with the trial token. Which production agents consume it is not settled; check the spec repo's implementation-status page before promising anything. Only relevant for interactive sites (search, cart, booking, filters); content sites skip it. References: https://developer.chrome.com/docs/ai/webmcp, https://webmachinelearning.github.io/webmcp/
3. **Agent-centric accessibility subset**: agents drive pages through the accessibility tree, so Lighthouse filters the a11y audits that matter for machine interaction: every interactive element has a programmatic name, ARIA roles are valid and on compatible elements, identical links have the same purpose, touch targets have sufficient size/spacing. Accessibility fixes now double as agent-readiness fixes; pitch them that way.
4. **Layout stability (CLS)**: agents target elements by position, so layout shift breaks them the same way it annoys humans.

**Audit check:** run the site through https://pagespeed.web.dev/ and read the Agentic Browsing section at the bottom of the report, or use Lighthouse in Chrome DevTools (Chrome 150+).

**Watch for false positives:** entrance animations that fade content in (opacity 0 to 1 on scroll-reveal) can make the contrast and visibility audits fail elements whose static styles pass. Verify the computed static colors before "fixing" contrast findings caused by animation timing.
