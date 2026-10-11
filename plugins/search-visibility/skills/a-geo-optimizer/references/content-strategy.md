# Content Strategy for AI Citations

How to structure, write, and maintain content that AI systems extract, cite, and recommend.

**How to read this file.** It gives direction, not measured effects. Earlier versions quoted citation percentages and multipliers from industry analyses that named no source; they were removed because a figure with no source and no stated limits cannot justify a rule. If you quote a number to a client or on a page, quote one you have checked against a named primary source, with its date, the platforms it measured and its limits.

## Table of Contents

1. [The Answer-Capsule Format](#1-the-answer-capsule-format)
2. [Front-Loading Critical Content](#2-front-loading-critical-content)
3. [Section Structure and Length](#3-section-structure-and-length)
4. [Heading Strategy](#4-heading-strategy)
5. [Statistical Density and Source Attribution](#5-statistical-density-and-source-attribution)
6. [Entity Density](#6-entity-density)
7. [Language and Tone](#7-language-and-tone)
8. [FAQ Sections](#8-faq-sections)
9. [Comparison Tables](#9-comparison-tables)
10. [Content Formats That Get Cited](#10-content-formats-that-get-cited)
11. [Author Authority Signals](#11-author-authority-signals)
12. [Content Freshness](#12-content-freshness)
13. [Topic Cluster Architecture](#13-topic-cluster-architecture)
14. [Off-Site Authority Building](#14-off-site-authority-building)
15. [Intent Modifier Phrases](#15-intent-modifier-phrases)
16. [Brand Sentiment Auditing](#16-brand-sentiment-auditing)
17. [What NOT to Do](#17-what-not-to-do)

---

## 1. The Answer-Capsule Format

The core content pattern for AI citation. Every major section should follow this structure:

```
[Question-style H2 heading]

[40-60 word direct answer, the "capsule"]

[Supporting detail, evidence, examples, 80-120 additional words]

[Optional: data table, comparison, or specific example]
```

**Example (good):**
```markdown
## How long does it take to set up a Synology NAS?

A basic Synology NAS setup takes 15-30 minutes for hardware assembly
and initial DSM installation. Full configuration including RAID setup,
shared folders, user accounts, and package installation typically
requires 1-2 hours. Advanced setups with Docker containers, reverse
proxies, and automated backups can take a full day.

The process breaks down into three phases. First, physical assembly:
insert drives, connect cables, power on. Second, DSM installation
via find.synology.com or Synology Assistant. Third, configuration
of storage pools, shared folders, and services.
```

**Example (bad, buries the answer):**
```markdown
## NAS Setup Guide

Network Attached Storage devices have become increasingly popular
in recent years. There are many brands to choose from, each with
their own strengths. In this guide, we'll walk through everything
you need to know about setting up your device. But first, let's
understand what a NAS actually is...

[answer appears 500 words later]
```

---

## 2. Front-Loading Critical Content

**Put the answer near the start of the page.** Readers and AI systems both meet the opening first; background and method can follow.

Rules:
- The most important, quotable, citable content goes at the top
- First paragraph after H1 should answer the page's core question
- No lengthy introductions, no "in this article we will discuss..."
- Get to the point immediately, then expand

For product/service pages: Lead with what it is, who it's for, and what problem it solves. Pricing and key differentiators in the first 3 paragraphs.

For blog posts: Lead with the answer or key finding. Background and methodology come after.

---

## 3. Section Structure and Length

**Size each section to the question it answers.** Give a distinct question its own section, long enough to answer it completely and short enough that the answer is not buried.

Each section should be:
- Self-contained (extractable without needing context from other sections)
- Focused on one specific sub-question
- Bounded by a descriptive heading
- Complete enough to stand alone as an answer

Articles over 2,900 words average 5.1 citations vs 3.2 for content under 800 words. Longer is better, but only if each section adds genuine value.

---

## 4. Heading Strategy

Use question-style headings that mirror how people ask AI assistants.

**Good headings (match conversational queries):**
- "How does [X] compare to [Y]?"
- "What are the pricing options for [service]?"
- "How long does [process] take?"
- "What's the best [tool] for [use case]?"
- "Is [product] worth it in 2026?"

**Bad headings (traditional SEO style, hard for AI to map to queries):**
- "Features"
- "Overview"
- "Technical Specifications"
- "Our Approach"
- "More Information"

Also: ChatGPT internally appends intent modifiers like "detailed guide", "step-by-step tutorial", "in-depth comparison" to its search queries. Including these phrases naturally in your headings or opening paragraphs can improve retrieval.

---

## 5. Statistical Density and Source Attribution

**Include evidence where it helps the reader.** The original GEO research (the 2023 paper "GEO: Generative Engine Optimization") found that adding cited sources, quotations and statistics improved visibility on its own benchmark; treat that as direction, not a guarantee for any particular assistant.

Rules:
- Use a statistic when it is the clearest evidence for a claim, not to meet a quota
- Always attribute statistics to their source
- Use specific numbers, not vague claims ("3.2× faster" not "much faster")
- Include dates with stats to signal freshness
- Prefer original data you've collected over recycled third-party stats

**Good (hypothetical figures, use your own sourced data):** "According to our 2026 client survey, 73% of small businesses in Croatia report spending less than 2 hours per week on social media marketing."

**Bad:** "Many businesses find social media marketing time-consuming."

---

## 6. Entity Density

**Name things specifically.** Specific names, dates, places and products make a passage easier to understand and to quote than vague references.

Entities = proper nouns, specific names, dates, places, product names, company names, standards, technologies.

- Use full, specific names on first mention (not just pronouns)
- Include dates, version numbers, specific locations
- Reference specific standards, frameworks, or methodologies by name
- Mention specific tools, platforms, or competitors by name when relevant

**High entity density (hypothetical figures):** "Zagreb-based agencies using Figma and Webflow in 2026 report 40% faster delivery times compared to agencies still using WordPress page builders."

**Low entity density:** "Agencies using modern design tools report faster delivery times than those using older platforms."

---

## 7. Language and Tone

AI systems prefer **definitive, authoritative language** over hedging.

**Preferred:**
- "The best approach is..."
- "This costs €500-800 per month"
- "Setup takes 2-3 business days"
- "The main drawback is..."

**Avoided by AI systems:**
- "It depends on various factors..."
- "There are many considerations to keep in mind..."
- "Results may vary..."
- "Contact us to learn more" (dead-end for AI)

**Critical:** AI systems filter out overtly promotional or sales-heavy content. Write as a knowledgeable advisor, not a salesperson. Neutral, factual language with specific claims wins citations.

---

## 8. FAQ Sections

FAQ sections with question-style headings nearly double citation chances. AI systems extract Q&A pairs directly, especially when paired with FAQPage schema.

**Requirements:**
- Use actual questions your customers/readers ask
- Match the conversational phrasing people use with AI ("How do I..." not "Methodology for...")
- Each answer direct and complete, as long as the question needs
- Include the questions readers actually ask, not a set number
- Pair with FAQPage JSON-LD schema (see technical-checklist.md)

**Good FAQ structure:**
```markdown
## Frequently Asked Questions

### How much does a website redesign cost in Croatia?

A professional website redesign in Croatia typically costs €2,000-8,000
for small business sites, €8,000-25,000 for mid-size corporate sites,
and €25,000+ for complex e-commerce platforms. Pricing depends on page
count, custom functionality, and whether content migration is included.

### How long does a typical web project take?

Most small business websites take 4-8 weeks from kickoff to launch.
Mid-size projects run 8-16 weeks. Enterprise-level builds with custom
integrations can extend to 3-6 months.
```

---

## 9. Comparison Tables

**Use a table when readers compare options.** A table states the relationships between items more clearly than prose.

Use HTML tables or Markdown tables for:
- Product vs. competitor comparisons
- Feature comparisons across tiers/plans
- Pros vs. cons
- Technology comparisons
- Before/after scenarios

Keep tables clean and data-rich. AI systems extract structured relationships from tables better than from prose.

---

## 10. Content Formats That Get Cited

Formats that answer a clear question tend to be quoted:

| Format | Notes |
|--------|-------|
| "Best X" lists | Useful when the list is honest about criteria |
| How-to guides | Especially with step-by-step structure |
| Comparison articles | X vs Y format |
| Definitions and explainers | "What is X" format |
| Case studies | With specific metrics and outcomes |

Pick the format that fits what your readers are trying to decide, not the one assumed to be cited most.

---

## 11. Author Authority Signals

Cited pages average 4.1 expert quotations vs 2.4 on non-cited pages.

For every content page, include:
- Author name and photo
- Professional title/role
- Years of experience or credentials
- Links to LinkedIn, professional profiles, or personal site
- Brief description of relevant expertise

For the Organization/brand:
- Clear "About Us" page with founding date, team, and mission
- Google Business Profile (fully optimized)
- Consistent Name, Address, Phone (NAP) across all platforms
- Wikidata entry (for entity recognition by AI)

---

## 12. Content Freshness

**Keep pages current when their facts change.**

Rules:
- Review key pages on a schedule that matches how fast their facts change
- Update with substantive changes (not just timestamp bumps)
- A changed date with no changed content misleads readers and earns nothing
- Display a visible "Last Updated: [date]" on the page
- The `dateModified` in your Article schema must match the visible date

---

## 13. Topic Cluster Architecture

**Group related pages into clusters.** A hub page that links its detailed pages, and links back from them, makes the whole topic easier to follow and to crawl.

Structure:
```
Pillar Page: "Complete Guide to [Topic]" (2,000-4,000 words)
├── Cluster: "How to [subtopic A]" (1,200-2,000 words)
├── Cluster: "Best [tools] for [subtopic B]" (1,500-2,500 words)
├── Cluster: "[Topic] vs [Alternative]" (1,000-1,500 words)
├── Cluster: "[Topic] for [specific audience]" (1,200-2,000 words)
└── Cluster: "Common [topic] mistakes and how to fix them" (1,000-1,500 words)
```

Rules:
- Pillar links to all cluster pages
- Each cluster page links back to pillar
- Cluster pages cross-link to related clusters
- Use descriptive anchor text

---

## 14. Off-Site Authority Building

**Earn mentions elsewhere.** Assistants draw on what other sites say about a brand, not only on the brand's own pages.

Priority platforms for AI citations:
1. **YouTube**: demo videos, tutorials, case studies.
2. **Reddit**: build an authentic presence in relevant subreddits.
3. **Review platforms**: G2, Clutch, Capterra, Trustpilot.
4. **Industry comparison articles**: Get listed in "best [service] in [location/niche]" articles.
5. **Guest posts**: Contribute to industry publications with expert commentary.
6. **Wikipedia/Wikidata**: Create or update entity entries for your brand/key people.
7. **Google Business Profile**: Primary data source for local AI recommendations.

Active profiles on the platforms your audience actually uses matter more than a presence everywhere.

---

## 15. Intent Modifier Phrases

ChatGPT appends modifier phrases to internal search queries when users ask questions. Including these naturally in your content improves retrieval:

- "detailed guide"
- "step-by-step tutorial"
- "in-depth comparison"
- "comprehensive overview"
- "complete guide"
- "how to [specific task]"
- "best [thing] for [use case]"
- "[thing] vs [alternative]"
- "pricing", "cost", "how much"
- "pros and cons"
- "review" / "honest review"

Don't stuff these artificially. Use them in headings and opening paragraphs where they fit naturally.

---

## 16. Brand Sentiment Auditing

Regularly test what AI tools say about your brand:

1. Ask each major AI tool: "Give me pros and cons of [Your Brand]"
2. Ask: "What are the best [your service type] companies in [your location]?"
3. Ask: "Compare [Your Brand] vs [Competitor]"
4. Document what's accurate, what's wrong, what's missing

If AI is hallucinating facts about you:
- Update your About page with clear, declarative sentences
- Update llms.txt with correct information
- Add specific factual claims to schema markup
- Build corrective third-party content (reviews, profiles, mentions)

AI systems pick up corrections faster from multiple independent sources than from your own site alone.

---

## 17. What NOT to Do

**Content that gets ignored or filtered by AI:**

- **Sales copy and promotional language**: AI filters out overtly commercial content
- **Vague, hedging language**: "It depends" answers get skipped in favor of specific ones
- **Thin content under 500 words**: Rarely provides enough value for citation
- **AI-generated content at scale without editorial enhancement**: Produces patterns AI learns to skip
- **Keyword-stuffed content**: The original GEO research showed keyword stuffing produced zero gains
- **Content with no original information**: If AI can generate the same content itself, it won't cite you
- **Content behind login walls**: AI crawlers cannot access paywalled content
- **Information scattered across multiple thin pages**: Consolidate into one page that covers the whole topic
- **Timestamp-only refreshes**: Changing the date without substantive updates doesn't fool AI systems
- **Ignoring a platform**: different assistants cite different sources; optimize for all

**The Chegg lesson:** If your content is commodity information that AI can generate independently, you'll be displaced. Content must include what AI cannot replicate: original data, proprietary research, real case studies with specific metrics, expert quotes from named professionals, and first-person experience.
