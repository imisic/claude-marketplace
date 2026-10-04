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

Most AI crawlers (GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot) do NOT execute JavaScript. Analysis of 500M+ GPTBot fetches showed zero JS execution. Only Googlebot reliably renders JS.

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

**Priority: CRITICAL. Blocking crawlers = invisible to AI**

See `crawler-reference.md` for complete user-agent list. Here's the recommended robots.txt template:

```
# === Standard Search Crawlers ===
User-agent: Googlebot
Allow: /

User-agent: Bingbot
Allow: /

# === AI Search Crawlers (allow for search visibility) ===
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

# === AI Training Crawlers (optional, allow if you want to be in training data) ===
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: Google-Extended
Allow: /

# === Block paths that shouldn't be crawled ===
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /tmp/
Disallow: /private/

Sitemap: https://yoursite.com/sitemap.xml
```

**Important distinctions:**
- **Search crawlers** (OAI-SearchBot, Claude-SearchBot, ChatGPT-User, Claude-User, PerplexityBot): These power real-time search features. Blocking them removes you from AI search results.
- **Training crawlers** (GPTBot, ClaudeBot, Google-Extended): These collect data for model training. Blocking them doesn't affect real-time search but reduces long-term model familiarity with your content. Sites blocking GPTBot were cited 73% less often.
- ChatGPT-User and Claude-User operate on behalf of human users and may not fully respect robots.txt blocks.

**Audit check:**
```bash
# Fetch and inspect current robots.txt
curl -s https://yoursite.com/robots.txt
# Look for blanket "Disallow: /" rules or blocks on AI user-agents
```

---

## 3. Schema.org Structured Data

**Priority: HIGH. GPT-4 accuracy jumps from 16% to 54% with structured data**

All schema must be:
- In JSON-LD format (Google-recommended, easiest for AI to parse)
- Rendered server-side in the HTML `<head>` (not injected via JS)
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

**FAQPage (powerful for AI extraction):**
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
        "text": "Direct, complete answer in 40-80 words."
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

**HowTo (for tutorials/guides):**
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

**Priority: LOW-MEDIUM (uneven adoption as a retrieval source, but since 2026 Lighthouse/PageSpeed Insights validates the file, so a malformed one shows up as a red audit to anyone who tests your site)**

Place at `https://yoursite.com/llms.txt`. Markdown-formatted overview of your site for AI consumption. Takes minutes to create, costs nothing.

**Format is now machine-validated.** Lighthouse's Agentic Browsing category (see section 13) parses the file as markdown and fails it unless:
- It contains exactly the spec structure: an H1 with the site/project name (the only hard-required element), then optionally a blockquote summary, prose, and H2 sections.
- Link entries use real markdown link syntax: `- [Name](https://url): note`. Plain `Title: URL` lines do NOT count and fail the audit with "File does not appear to contain any links".
- The file is longer than ~50 characters.
- Gotcha: avoid `---` horizontal-rule lines. Markdown parsers can read the first one as a YAML front-matter delimiter and discard everything above it, including the H1, so the audit reports "missing an H1 header" even though the file visibly has one.

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

**Current status (as of 2026-07, per third-party trackers, not primary sources; verify before quoting):** Adoption is growing but uneven (roughly 10% of large domain samples). Some providers have confirmed support (Anthropic by late 2024, Perplexity by 2025), and by 2026 most major Western AI platforms offer partial support. The most concrete, verifiable adoption is in AI dev tools: Claude Code, Cursor, Windsurf, GitHub Copilot, Cline, Aider all fetch `/llms.txt` and `/llms-full.txt`, especially for documentation/reference sites. Google has said it does not use llms.txt for Search, and as of Q1 2026 no major AI provider (OpenAI, Google, Anthropic, Meta, Mistral) has publicly committed to reading it in production answer systems. What HAS changed: Google now validates the file in Lighthouse and PageSpeed Insights (Agentic Browsing category, section 13), which makes it a visible pass/fail checkbox for clients, tools, and audits. Bottom line: still don't prioritize it over robots.txt, schema, sitemap, or content structure, but if you ship one, it MUST follow the format rules above or it hurts you in audits.

---

## 6. Page Speed Optimization

**Priority: HIGH. Pages with FCP < 0.4s get 3× more AI citations**

Target metrics:
- First Contentful Paint (FCP): < 0.4 seconds
- Time to First Byte (TTFB): < 200ms
- Largest Contentful Paint (LCP): < 2.5 seconds

AI crawlers abandon slow pages more aggressively than traditional search crawlers.

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

Bing is critical because ChatGPT and Copilot both use Bing's index. 87% of ChatGPT citations match Bing's top results.

---

## 8. IndexNow Implementation

**Priority: MEDIUM-HIGH**

IndexNow instantly notifies Bing (and by extension ChatGPT/Copilot) when content is published or updated.

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

AI models process Markdown natively. This gives them a clean, uncluttered version of your content.

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

**Priority: HIGH. Pillar-cluster architecture delivers 2.7× citation multiplier**

Structure sites as topic clusters:
- **Pillar page**: Covers a whole topic end to end (2000+ words)
- **Cluster pages**: Detailed sub-topic articles linking back to pillar
- **Bidirectional links**: Pillar links to clusters, clusters link to pillar
- Use descriptive anchor text (not "click here")

82.5% of ChatGPT citations link to pages within established topic hierarchies, not isolated articles.

---

## 13. Lighthouse Agentic Browsing Audit

**Priority: MEDIUM (new in 2026, the first mainstream tool that grades agent-readiness; category is explicitly "under development and subject to change")**

Chrome Lighthouse (Chrome 150+, also surfaced on pagespeed.web.dev) added an "Agentic Browsing" category that scores how well a site works for AI agents. Unlike other categories there is no 0-100 weighted score: each audit reports pass/fail (or a pass ratio) independently.

**What it checks:**

1. **llms.txt presence and format**: see section 5 for the exact validation rules (H1 required, markdown `[text](url)` links required, minimum length, no `---` front-matter trap).
2. **WebMCP integration**: WebMCP (Web Model Context Protocol) is a W3C proposal that lets a page expose callable tools to AI agents via `navigator.modelContext` instead of the agent guessing at the UI. Announced February 2026, in Chrome origin trial (Chrome 149-156); the main consuming agent today is Gemini in Chrome. Lighthouse verifies both declarative tools (defined in HTML) and imperative tools (registered from JS). Only relevant for interactive sites (search, cart, booking, filters); content/publishing sites can safely skip it. Reference: https://developer.chrome.com/docs/ai/webmcp
3. **Agent-centric accessibility subset**: agents drive pages through the accessibility tree, so Lighthouse filters the a11y audits that matter for machine interaction: every interactive element has a programmatic name, ARIA roles are valid and on compatible elements, identical links have the same purpose, touch targets have sufficient size/spacing. Accessibility fixes now double as agent-readiness fixes; pitch them that way.
4. **Layout stability (CLS)**: agents target elements by position, so layout shift breaks them the same way it annoys humans.

**Audit check:** run the site through https://pagespeed.web.dev/ and read the Agentic Browsing section at the bottom of the report, or use Lighthouse in Chrome DevTools (Chrome 150+).

**Watch for false positives:** entrance animations that fade content in (opacity 0 to 1 on scroll-reveal) can make the contrast and visibility audits fail elements whose static styles pass. Verify the computed static colors before "fixing" contrast findings caused by animation timing.
