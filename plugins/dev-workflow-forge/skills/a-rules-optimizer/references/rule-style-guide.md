# Rule Style Guide

How to write `.claude/rules/` files that are effective, concise, and correctly scoped.

## File Structure

Every rule file starts with YAML frontmatter for scoping, then markdown content.

### Path-Scoped (most files)
```yaml
---
paths:
  - "src/**/*.py"
  - "lib/**/*.py"
---
```

### Always-Applied (rare, for project-wide architecture rules)
```yaml
---
alwaysApply: true
---
```

Use `alwaysApply` only for rules that genuinely matter regardless of which file is being edited (e.g., architecture layer rules, fundamental conventions). Default to `paths:` scoping.

That default holds for reference material only. `paths:` fires when Claude **reads** a matching file and stays silent when it **writes** one, so prohibitions, access inventories, and any rule governing a write-heavy workflow belong in `alwaysApply: true` however large they are. Shrink those rather than scoping them. Full decision rule and the measured trigger behavior: SKILL.md Phase 2e.

### Additional frontmatter notes

- **Two `paths:` forms are equally valid:** the block-list form above and an inline comma-separated form (`paths: app/**/*.php, public/index.php, composer.json`). They behave identically. Match whichever the existing rule set already uses; don't rewrite one into the other during an audit.
- **`paths:` entries can be exact files, not just globs.** A subsystem rule scopes cleanly to the handful of files that implement it: `paths: src/consolidator.py`, or `paths: app/src/Core/FeatureFlags.php, app/src/Services/OAuthService.php, .env`. The rule loads exactly when those files are edited and stays out of context otherwise.
- **`security.md` is the canonical always-on file.** Security review applies to every source file, so mark it `alwaysApply: true` or scope it to all source (`src/**/*.py`, `app/**/*.php`). Every mature rule set has exactly one always-on security file.

## Scoping Guidelines

| Pattern | When to use |
|-|-|
| `src/**/*.py` | Language-wide rules (security, error handling, quality) |
| `src/web/**/*.py` | Framework-specific rules (Streamlit, Flask, Django) |
| `src/core/**/*.py` | Domain-specific rules (backup engine, data processing) |
| `backend/**/*.php` | Platform rules in a monorepo |
| `tests/**/*.py` | Test-specific conventions |

**Too broad:** `**/*.py` loads on test files, scripts, config generators. Scope to where source code actually lives.

**Too narrow:** `src/core/backup/engine.py` only loads for one file. Broaden to `src/core/**/*.py` unless the rule truly applies to only that file.

**When single-file scope IS right:** the "unless it truly applies to only that file" case is common, since a rule governing one subsystem/module (a scraper, a consolidator, a dashboard, a feature-flag registry) should scope to the single file (or small set) that implements it. Only broaden a single-file scope when the rule is really a language-wide concern mis-filed under one file: a generic "catch specific exceptions" rule pinned to `engine.py` belongs in the language-wide error-handling file instead.

**Multi-pattern:** Use when rules apply to related but separate directories:
```yaml
paths:
  - "src/core/**/*.py"
  - "src/utils/**/*.py"
```

## Writing Rules

### Format

```markdown
## Section Heading

- Rule statement as a declarative instruction
- Another rule, direct and specific
- Rule with rationale: "Never do X because Y" (only when the reason isn't obvious)
```

### Style

**DO:**
- Write imperative statements: "Always set timeout= on subprocess calls"
- Be specific: "Use `html.escape()` before embedding in `unsafe_allow_html=True`"
- Group related rules under `##` headings
- One concern per bullet point
- Reference files when a pattern is project-specific: `Reference: src/core/config_manager.py`

**DON'T:**
- Write code blocks longer than one line (this is a rule file, not a tutorial)
- Explain how the language works ("In Python, exceptions are...")
- Include examples of correct code (describe the rule, don't demonstrate it)
- Duplicate rules across files (put each rule in the most specific file)
- Restate what the language/framework already enforces
- Use passive voice ("Exceptions should be caught" → "Catch specific exception types")

### Granularity

A good rule is:
- Actionable in the moment of writing code
- Specific enough that you can tell if code violates it
- General enough to apply to more than one line of code

**Too vague:** "Write secure code"
**Too specific:** "Line 42 of engine.py must use parameterized queries"
**Right level:** "All YAML operations go through ConfigManager, never raw yaml.load()"

### When to Include Rationale

Most rules don't need a "because" clause. Include one only when:
- The rule is counterintuitive ("Allow direct Repository access from Controllers for reads, because Processor overhead isn't justified for simple GETs")
- The rule has project-specific history ("Never use offset-based pagination in the validator, because validated rows drop out of the result set")
- Violating the rule causes a non-obvious failure ("Write metadata JSON atomically via temp+rename, because a crash mid-write corrupts the file")

## Rule Shapes Beyond the One-Line "Do X / Never Y"

Most rules are single declarative bullets. Mature rule sets also use two other shapes; recognize and preserve them:

### Procedural create-flow checklist

A numbered "Adding a new X" list that enumerates the must-not-skip steps for a recurring create-flow (a new model, content type, migration, feature, endpoint). This IS a rule (it prevents the "forgot step 4" class of mistake), and it belongs at the bottom of the relevant rule file. Each step points to the sibling rule/file that governs it. Keep the steps; don't inline the details of each (those live in the sibling file).

Example shape (not literal content): `Adding a new content type: 1) add route + feature flag, 2) create model (see models.md), 3) create category table, 4) add pivot table, 5) add Tag methods, 6) update this doc.` Derive the actual steps from how the codebase's existing entities were wired.

### Domain / business-invariant rule

Rules that encode facts a generic engineering taxonomy can't know: which enum value blocks a downstream action, what a status transition means, the integrity constraint that must hold across entities ("excluded records never receive positive flags"), the recommended count bound ("3-7 tags per item"), the SSRF/redirect model a fetcher must follow. These come from the project's enums, status machines, subsystem boundaries, and cross-entity invariants, not from the review-dimensions taxonomy. Every mature project has a handful of these; a rule set without any is almost certainly under-covering the domain. See SKILL.md Phase 2a "Derive domain dimensions."

## Organization Patterns

### By Domain (recommended for most projects)
```
rules/
├── security.md          # Input validation, secrets, injection prevention
├── error-handling.md    # Exception patterns, logging, failure modes
├── code-quality.md      # Size limits, types, dead code, performance
├── database.md          # Query safety, access patterns, schema conventions
├── web-layer.md         # Framework-specific UI patterns
└── architecture.md      # Layer rules, module boundaries, conventions
```

### By Architectural Layer (for strict layered architectures)
```
rules/
├── controllers.md       # HTTP layer rules
├── processors.md        # Business logic layer rules
├── repositories.md      # Data access layer rules
├── security.md          # Cross-cutting security rules
└── php-standards.md     # Language conventions
```

### By Platform (for monorepos)
```
rules/
├── be-security.md       # Backend security
├── be-database.md       # Backend data access
├── mo-components.md     # Mobile component rules
├── mo-state.md          # Mobile state management
├── we-architecture.md   # Web frontend architecture
└── code-quality.md      # Cross-platform quality rules
```

## CLAUDE.md Integration

When rules exist, CLAUDE.md should reference them with a summary table:

```markdown
## Coding Rules (`.claude/rules/`)

Path-scoped rules auto-loaded when editing matching files.

| Rule file | Scope | Covers |
|-|-|-|
| `security.md` | `src/**/*.py` | Subprocess safety, input validation, secrets |
| `web-layer.md` | `src/web/**/*.py` | Cache invalidation, rerun discipline |
```

Keep it to a one-line description per file. The rules themselves have the detail.

**Critical: never use `@` import syntax for rule files in CLAUDE.md.** Writing `@.claude/rules/security.md` force-loads that file at session start, every turn, regardless of its `paths:` frontmatter. The whole point of `paths:` scoping is on-demand loading; `@imports` defeat it. Reference rule files by name only (`see security.md`, or in a table as above).

## Anti-Patterns

**The tutorial file:** A rule file that explains how to use the framework, with code examples and documentation. Rules files are instructions, not onboarding docs.

**The kitchen sink:** One file with 100+ rules covering everything. Split by domain and scope properly.

**The aspirational rule:** Rules for patterns the project doesn't use yet. Only write rules for things that exist or are about to be built.

**The duplicate rule:** Same rule in security.md and database.md. Keep each rule in exactly one file. *One deliberate exception:* when a rule's source-of-truth file is path-scoped to a directory the rule *also* needs to govern from a different file type, the scoping hides it. Real case: a "no inline event handlers" rule lived in `js-standards.md` (scoped `public/js/**`), but the regressions all happened in PHP view files, where that file never loads. The fix is to *restate* the rule in the in-scope file (`views.md`, scoped to the views dir) with a one-line cross-reference to the source of truth: deliberate duplication for path-visibility. Only do this when path-scoping genuinely hides the rule from where violations occur; don't use it as license to copy rules around freely.

**The stale reference:** `Reference: src/old_module.py:42` pointing to a file that was renamed 3 months ago. References need freshness checks.

**The inventory dump:** A rule file padded with content that's derivable from the codebase: directory trees, lists of controllers/models/services/partials, URL route enumerations, base-class method signatures, helper function indexes, design-token catalogs. These rot the moment a file is added or renamed and contribute zero rule signal. Replace with one-line pointers: `Inventory: ls app/src/Models/`, `Methods: read app/src/Core/View.php`, `Routes: app/config/routes.php`, `Tokens: public/css/tokens.css`. Keep the rule (the "must"/"never"); drop the catalog.

*Carve-out: enum/status semantics are not inventory.* The *list* of enum values is derivable (`SHOW COLUMNS`, read the enum class, use a pointer). The *meaning attached to each value* is not: "which `email_tier` values are outreach-eligible," "`NONE` means checked-and-empty vs `NULL` means not-yet-evaluated," "archived tools stay publicly linkable but drafts don't." That semantic layer is load-bearing domain knowledge no schema query returns; keep it. Drop only the mechanically-derivable column list; preserve the invariants and eligibility rules bolted to the values.

**The `@import` trap:** Referencing a rule file from `CLAUDE.md` with `@.claude/rules/foo.md` force-loads it every turn and overrides whatever `paths:` scoping the file declared. Always reference rule files by name only.
