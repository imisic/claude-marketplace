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

1. **Technical foundation**: Start with `python3 "${CLAUDE_SKILL_DIR}/scripts/geo_probe.py" <url> [more page URLs] --json`. It fetches robots.txt (per-crawler allow/disallow/unmentioned, Sitemap and Content-Signal lines), `/llms.txt` and `/llms-full.txt` (presence, size, first heading, format), and every page's JSON-LD blocks (`@type` values, parse errors, missing template fields) plus `<title>`, meta description, canonical, `<html lang>` and a no-JS body-text heuristic. Its findings are evidence with a severity, never recommendations: judge that candidate set, then read `references/technical-checklist.md` and the pages themselves only for what the probe cannot see (wording quality, whether the content is worth citing, CDN-level bot blocking via `curl -A "GPTBot"`, page speed, Lighthouse). Verify:
   - robots.txt allows the AI search/index bots (exact user-agents in `references/crawler-reference.md`), and named groups repeat the `*` group's Disallow lines (named groups don't inherit them; probe check `robots-named-group-skips-wildcard`). Allowing training bots is the owner's decision; ask
   - Google Search Console > Settings > Search generative AI is on Include (Exclude drops the site from AI Overviews and AI Mode)
   - Server-side rendering (critical: the OpenAI, Anthropic and Perplexity crawlers don't execute JS)
   - Schema.org JSON-LD for entities on key pages (Organization, Person, Product, LocalBusiness, Article); FAQ/HowTo markup optional
   - Page speed (TTFB < 200ms, LCP < 2.5s)
   - XML sitemap + RSS/Atom feed
   - HTTPS, mobile-friendly
   - llms.txt file: if present, it should pass Lighthouse's llms-txt audit, which checks three things: an H1 header, at least one markdown `[text](url)` link, and at least 50 characters (checklist section 5)
   - Agentic Browsing readiness (checklist section 13): run PageSpeed Insights and read the Agentic Browsing category; agent-critical a11y (programmatic names, valid ARIA, touch targets) and CLS now double as agent-readiness signals. WebMCP only matters for interactive sites (search, cart, booking)
   - If behind Cloudflare: fetch the LIVE robots.txt and check for injected Content-Signal directives (`ai-train=no` is the managed default; `ai-input=no` would hurt AI citation, see crawler-reference section 12)

2. **Content structure**: Read `references/content-strategy.md` and evaluate:
   - Short direct answer opening each section (a habit, not a word-count rule; Google says AI features need no special chunking)
   - Coverage of the topic's real subquestions (query fan-out)
   - Front-loaded key content (the answer near the top, not after the background)
   - Sections sized to the question each one answers
   - Evidence where it helps the reader, with sources for any statistic
   - Question-style headings matching conversational queries
   - FAQ sections with real user questions
   - Author bios with credentials

3. **Entity and authority signals**: Check:
   - Organization schema with consistent NAP (Name, Address, Phone)
   - Author schema with credentials and external profile links
   - Third-party presence (review sites, directories, Reddit, YouTube)
   - Internal linking structure (pillar-cluster architecture)

4. **Monitoring setup**: Recommend:
   - Google Search Console Generative AI performance report and Bing Webmaster Tools AI Performance (the only first-party AI visibility and citation numbers)
   - GA4 AI Assistant channel (built in since 2026-05), plus the source regex for gaps (crawler-reference section 10)
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
- Fast TTFB (< 200ms) and LCP (< 2.5s)

### Step 4: Output deliverables

Depending on the task, produce one or more of:

- **robots.txt**: ready to deploy, from a template in `references/crawler-reference.md` section 8 chosen with the owner (training allowed or not); AI search/index bots always allowed
- **llms.txt / llms-full.txt** (optional, low priority): Markdown site overview, plus an optional full-content companion. Google Search doesn't use it, no major AI provider has said its answer systems read customer sites' files, and log studies show few requests; coding agents and docs tools are the real readers. Lighthouse/PageSpeed Insights audits the file for an H1, at least one markdown link and at least 50 characters, so if one exists it should pass; write links as `- [name](url): note` bullets, never plain `Title: URL` lines. Generate it when trivial, notably when the site already exposes per-page markdown. Don't prioritize it over robots.txt, content, sitemap or schema.
- **Markdown for agents** (optional, docs/content sites): answer `Accept: text/markdown` with the same content as Markdown (crawler-reference section 13)
- **Schema JSON-LD blocks**: per page type (Article, Product, FAQPage, Organization, etc.)
- **Content restructured**: in answer-capsule format with front-loaded answers
- **Audit report**: findings and priority-ordered recommendations
- **PHP template code**: with GEO elements built into the template layer
- **Sitemap + RSS/Atom feed**: if missing or incomplete
- **Measurement setup**: Search Console Generative AI report, Bing AI Performance, GA4 AI Assistant channel
- **Product feeds** (shops only): Merchant Center and AI shopping feeds (crawler-reference section 9)

## Key principles to always follow

1. **GEO is mostly SEO**: Google says AI Overviews and AI Mode need nothing beyond normal Search eligibility. Fix crawlability, indexing and content quality before anything AI-specific, and never promise a citation multiplier: the commonly quoted figures are unsourced or correlations (sourcing rules in `references/content-strategy.md`).

2. **SSR is non-negotiable**: If content requires JavaScript to render, the crawlers behind ChatGPT, Claude and Perplexity cannot see it (Googlebot and Applebot render JS). Always flag this.

3. **Front-load answers**: The most important content goes near the top of the page. AI systems tend to extract from the top.

4. **Be specific, not promotional**: Factual language with specific numbers, dates and names is easier to quote than sales copy. Keep true caveats; specific is not overconfident.

5. **Earned media > owned content**: Assistants lean on third-party mentions, not just what a site says about itself. Recommend off-site authority building where the business can earn it.

6. **Freshness matters**: Recently updated pages are favoured, so recommend a refresh cycle for pages whose facts change, with real updates rather than date bumps.

7. **Cross-platform optimization**: Different assistants cite different sources. Optimize for all major AI systems, not just one.

8. **Don't block crawlers by accident**: Always check the LIVE robots.txt for inherited CMS/CDN blocks on AI user-agents, named groups that drop the `*` rules, injected Content-Signal directives (Cloudflare's managed robots.txt adds `ai-train=no`; more than 3.8M domains used it at its 2025 launch), CDN-level bot blocking that fires before robots.txt is read (test with `curl -A "GPTBot"`, confirm in logs), and the Search Console generative AI setting.

9. **Agent-readiness is the new layer**: Lighthouse's Agentic Browsing category (experimental, Chrome 150+) checks llms.txt format, WebMCP tools, agent-critical accessibility and CLS. Agentic browsers (OpenAI Atlas, Perplexity Comet, Gemini in Chrome, Claude in Chrome) drive real sessions through the rendered page and a11y tree, so accessibility fixes double as agent task-completion fixes. Hosted agents now identify themselves (Google-Agent, Claude-Agent, Web Bot Auth); WAF rules should let verified ones through.

10. **Training is a separate decision from visibility**: Blocking GPTBot, ClaudeBot or Applebot-Extended doesn't remove a site from AI answers; blocking OAI-SearchBot, Claude-SearchBot, PerplexityBot or Bingbot removes or reduces it there. Amazonbot may also train Amazon models (Amzn-SearchBot doesn't). Google-Extended sits in between (training plus Gemini grounding). Ask the owner, then use the matching template. The IETF aipref training signal (Anthropic since 2026-10-30, Google from early 2027) is a draft to watch, not a default.

## Reference files

- `scripts/geo_probe.py`: deterministic first phase (robots.txt, llms.txt, JSON-LD, head tags), stdlib only; `--json` for phase two, exit 1 when any finding at or above `--severity` exists. The embedded crawler list mirrors `references/crawler-reference.md` sections 1 and 7, so update both together.
- `references/technical-checklist.md`: complete technical implementation checklist (robots.txt, schema, sitemap, llms.txt, page speed, rendering)
- `references/content-strategy.md`: content formatting, answer-capsule structure, citation optimization, topic clustering
- `references/crawler-reference.md`: AI crawler user-agents with robots.txt behaviour (vendor pages checked 2026-11-08), Google's AI controls, robots.txt templates, submission and measurement, content signals and aipref, Web Bot Auth and Markdown negotiation
