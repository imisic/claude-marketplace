---
name: a-geo-optimizer
description: "Optimize websites for AI search visibility (GEO/AEO) so ChatGPT, Claude, Gemini, Perplexity and Copilot can find and cite their pages. Use for AI SEO, GEO, AEO, generative or answer engine optimization, llms.txt, schema markup for AI, robots.txt for AI bots, WebMCP, agentic browsers and structured data audits for AI visibility, \"make my site AI-friendly\", \"optimize for ChatGPT\" or \"get cited by AI\". Also use when building a new site or page, even without an explicit GEO request. Covers crawler access, content structure and AI referral monitoring, not general copy editing. For your site's Search Console traffic analysis, use a-seo-gsc."
---

# GEO Optimizer: AI Search Visibility Skill

Make any web project discoverable and citable by AI assistants (ChatGPT, Claude, Gemini, Perplexity, Copilot). This skill covers technical implementation, content structure, and ongoing monitoring.

## When to use this skill

- **New site/page creation**: Bake GEO in from the start
- **Existing site audit**: Diagnose and fix AI visibility gaps
- **Content writing/restructuring**: Format content for AI citation
- **Template development**: Build PHP/HTML templates with GEO built-in
- **robots.txt / schema / sitemap work**: Ensure AI crawler compatibility
- **Competitive analysis**: Compare AI citation performance

## How to use this skill

### Step 1: Determine the task type

Ask yourself which mode applies:

| Mode | When | What to do |
|------|------|------------|
| **Full audit** | User wants the full review | Run all checklists from `references/technical-checklist.md` |
| **New build** | Creating a site/page from scratch | Follow the build-time integration guide below |
| **Content optimization** | Writing or restructuring content | Follow `references/content-strategy.md` |
| **Quick fix** | Specific technical task (robots.txt, schema, etc.) | Jump to relevant section in `references/technical-checklist.md` |

### Step 2: For full audits, follow this sequence

1. **Technical foundation**: Read `references/technical-checklist.md` and verify:
   - robots.txt allows AI crawlers (exact user-agents in `references/crawler-reference.md`)
   - Server-side rendering (critical: most AI crawlers don't execute JS)
   - Schema.org JSON-LD markup on key pages
   - Page speed (FCP < 0.4s target)
   - XML sitemap + RSS/Atom feed
   - HTTPS, mobile-friendly
   - llms.txt file: if present it MUST pass Lighthouse validation (H1 + markdown `[text](url)` links, see checklist section 5); a malformed one is worse than none because it fails a visible audit
   - Agentic Browsing readiness (checklist section 13): run PageSpeed Insights and read the Agentic Browsing category; agent-critical a11y (programmatic names, valid ARIA, touch targets) and CLS now double as agent-readiness signals. WebMCP only matters for interactive sites (search, cart, booking)
   - If behind Cloudflare: fetch the LIVE robots.txt and check for injected Content-Signal directives (`ai-train=no` is the managed default; `ai-input=no` would hurt AI citation, see crawler-reference section 12)

2. **Content structure**: Read `references/content-strategy.md` and evaluate:
   - Answer-capsule format (40-60 word direct answer after each heading)
   - Front-loaded key content (44% of AI citations come from first 30% of page)
   - Section length (120-180 words per self-contained section)
   - Statistical density (one verifiable stat per 150-200 words)
   - Question-style headings matching conversational queries
   - FAQ sections with real user questions
   - Author bios with credentials

3. **Entity and authority signals**: Check:
   - Organization schema with consistent NAP (Name, Address, Phone)
   - Author schema with credentials and external profile links
   - Third-party presence (review sites, directories, Reddit, YouTube)
   - Internal linking structure (pillar-cluster architecture)

4. **Monitoring setup**: Recommend:
   - GA4 AI traffic segment (regex for AI referral sources)
   - Monthly prompt testing across AI platforms
   - GEO monitoring tool appropriate to budget

### Step 3: For new builds, integrate GEO at template level

When building PHP/HTML templates, include these by default:

**In the `<head>` of every page:**
```html
<!-- JSON-LD schema block (populated per page type) -->
<script type="application/ld+json" id="schema-jsonld">
<!-- Populated server-side per template -->
</script>

<!-- Markdown alternate for long-form content (optional) -->
<link rel="alternate" type="text/markdown" href="<?= $markdown_url ?>" />

<!-- Standard meta for AI extraction -->
<meta name="description" content="<?= htmlspecialchars($meta_description) ?>" />
<meta name="author" content="<?= htmlspecialchars($author_name) ?>" />
<meta property="article:published_time" content="<?= $published_date ?>" />
<meta property="article:modified_time" content="<?= $modified_date ?>" />
```

**Content templates should enforce:**
- Single H1 per page
- Logical H2/H3 hierarchy
- First paragraph = direct answer to the page's core question
- Visible "Last Updated" date reflecting genuine content changes
- Author bio block with photo, credentials, external links

**Server-side requirements:**
- All content rendered server-side (SSR), not client-side JS
- JSON-LD generated server-side per page template
- Clean semantic HTML (proper heading hierarchy, lists, tables)
- Fast TTFB and FCP (< 0.4s target)

### Step 4: Output deliverables

Depending on the task, produce one or more of:

- **robots.txt**: Ready to deploy, with all AI crawlers allowed (see `references/crawler-reference.md` for exact user-agents)
- **llms.txt / llms-full.txt** (optional, low-medium priority): Markdown site overview, plus an optional full-content companion. As of 2026-07 adoption as a retrieval source is still uneven: AI dev tools (Claude Code, Cursor, Copilot, Windsurf, Cline, Aider) fetch both and some providers (Anthropic, Perplexity) confirm support, but Google doesn't use it for Search and no major provider has committed to it in production answer systems. What changed in 2026: Lighthouse/PageSpeed Insights now validates the file (Agentic Browsing category), so if one exists it MUST follow the spec format (H1 required; links as markdown `- [name](url): note` bullets, never plain `Title: URL` lines; no `---` rules that get parsed as front-matter). Generate it when trivial alongside other work, notably when the site already exposes per-page markdown, since a route can then concatenate it cheaply. Don't prioritize it over robots.txt, schema, sitemap, or content.
- **Schema JSON-LD blocks**: Per page type (Article, Product, FAQPage, Organization, etc.)
- **Content restructured**: In answer-capsule format with front-loaded answers
- **Audit report**: Findings and priority-ordered recommendations
- **PHP template code**: With GEO elements built into the template layer
- **Sitemap + RSS/Atom feed**: If missing or incomplete
- **GA4 configuration**: AI referral traffic tracking setup

## Key principles to always follow

1. **SSR is non-negotiable**: If content requires JavaScript to render, AI crawlers (except Googlebot) cannot see it. Always flag this.

2. **Front-load answers**: The most important content goes in the first 30% of the page. AI systems extract from the top.

3. **Be specific, not promotional**: AI systems filter out sales copy. Use definitive, factual language with specific numbers, dates, and names. Entity density matters.

4. **Earned media > owned content**: Third-party mentions are 6.5× more likely to generate AI citations than self-published content. Always recommend off-site authority building.

5. **Freshness is a hard requirement**: Content updated within 30 days accounts for 76% of AI citations. Recommend refresh cycles.

6. **Cross-platform optimization**: Only 11-14% of citations overlap between platforms. Optimize for all major AI systems, not just one.

7. **Don't block crawlers by accident**: Always check the LIVE robots.txt for inherited CMS/CDN blocks on AI user-agents, injected Content-Signal directives (Cloudflare's managed robots.txt defaults to `ai-train=no` on 3.8M+ domains), and CDN-level bot blocking that fires before robots.txt is read (test with `curl -A "GPTBot"`).

8. **Agent-readiness is the new layer**: Lighthouse's Agentic Browsing category (2026) grades llms.txt format, WebMCP tools, agent-critical accessibility, and CLS. Agentic browsers (OpenAI Atlas, Perplexity Comet, Gemini in Chrome) drive real sessions through the rendered page and a11y tree, so accessibility fixes now double as agent task-completion fixes.

## Reference files

- `references/technical-checklist.md`: Complete technical implementation checklist (robots.txt, schema, sitemap, llms.txt, page speed, rendering)
- `references/content-strategy.md`: Content formatting, answer-capsule structure, citation optimization, topic clustering
- `references/crawler-reference.md`: All AI crawler user-agents, which platforms they serve, robots.txt templates, and platform-specific submission guides
