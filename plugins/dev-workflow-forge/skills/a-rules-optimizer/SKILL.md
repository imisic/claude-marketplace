---
name: a-rules-optimizer
description: Audit and update .claude/rules/ and CLAUDE.md to match the codebase; use --audit-only for a report without edits.
disable-model-invocation: true
---

# Rules Optimizer

Audit `.claude/rules/` and `CLAUDE.md` against the actual codebase. Creates missing rules, fixes drift, ensures coverage. Works on any project regardless of stack.

**Input:** optional flags
- `--full`: full audit and optimization (default)
- `--audit-only`: report drift without making changes
- `--sync`: just fix stale references and drift, skip coverage analysis

If no `.claude/rules/` directory exists, create it and build rules from scratch. That's the whole point of running this skill.

---

## Core Principles

**Rules are instructions, not code examples.** Each rule is a declarative statement: "do X", "never Y", "Z must always include W". No code blocks longer than a single line. If a pattern needs showing, use `Reference: path/file.py:42`.

**Rules prevent what reviews catch.** Every rule should map to something that would otherwise be flagged during code review. If a rule doesn't prevent a real mistake, it's noise.

**Path scoping saves context.** Rules scoped to `src/web/**/*.py` don't load when editing `src/core/`. Use the narrowest glob that covers the files where the rule matters. It also fires less often than it looks: `paths:` is reliable for reference material consulted during a read and unreliable for anything that must govern a write, so run the Phase 2e decision rule before adding it to any file.

**`@imports` to rule files defeat path-scoping.** If `CLAUDE.md` references a rule file with `@.claude/rules/foo.md`, that file is force-loaded at session start regardless of its `paths:` frontmatter. Always reference rule files by name only ("see `services.md`") so the path scoping the user wrote actually takes effect.

**Rules are pointers, not inventories.** Anything derivable by `ls`, `grep`, or reading one well-known file (base classes, enums, route configs) does not belong in a rule file. Lists of controllers, models, services, helpers, partials, URL routes, directory trees, base-class method signatures, design tokens, all rot the moment the code changes. Replace with one-liners: `Inventory: ls app/src/Models/`, `Methods: read app/src/Core/View.php`, `Routes: app/config/routes.php`. Keep the rule (the "must"/"never"), drop the catalog.

**Preserve the user's voice.** If rules already exist, the user wrote them from experience. Keep their wording, organization, and emphasis. Only change what has a concrete reason (drift, gap, stale reference).

---

## Phase 1: Project Profile

Discover the tech stack, architecture, and patterns. This drives everything else.

### 1a: Stack Detection

Build a project profile. Pick **one** of these two ways:

- **Option 1 (default, preferred):** Dispatch an `Explore` agent with the brief below. Useful when the project is large or you want the analysis to stay out of your own context window.
- **Option 2 (fallback):** If no agent is available, run the commands yourself and summarize the findings.

The brief (paste into the agent's prompt, or walk through it yourself):

```
Analyze the project at [CWD]. Report back concisely:

1. STACK: Language(s), framework(s), runtime version requirements
   - Check: package.json, composer.json, requirements.txt, pyproject.toml, go.mod, Cargo.toml, Gemfile, *.sln
   - Check: Dockerfile, docker-compose.yml if present

2. STRUCTURE: Top-level directory layout. Which directories contain source code vs config vs tests vs assets?
   - Run: find . -maxdepth 3 -type d (excluding .git, node_modules, vendor, __pycache__, venv)

3. ARCHITECTURE PATTERN: How is the code organized?
   - MVC, service-repository, layered, modular, flat, monorepo?
   - Where does business logic live?
   - How do modules communicate?

4. KEY PATTERNS (read the 5 largest source files to discover):
   - Error handling: exceptions, result tuples, error codes?
   - Config access: env vars, YAML, JSON, centralized manager?
   - Data access: ORM, raw queries, repository pattern?
   - State management: framework-specific patterns?
   - Registration: how are routes/views/commands/components wired?
   - Logging: which logger, what patterns?

5. BOUNDARIES: Where does external input enter the system?
   - CLI args, HTTP requests, file uploads, API responses, user config?

6. FILE METRICS:
   - Total source files and lines (by language)
   - Largest files (top 10)
   - Test presence and structure

7. DOMAIN VOCABULARY (drives project-specific rules a generic taxonomy can't):
   - Enums / status fields and the meaning of their values (which value gates a downstream action?)
   - Status machines / lifecycle transitions (draft→published, pending→approved)
   - Distinct subsystems with their own conventions (scraper, consolidator, scorer, feature-flag registry, importer)
   - Cross-entity invariants ("excluded rows never get positive flags", "counts never overwritten on sync")
   - Content-integrity constraints (fields that must not be edited via raw SQL, unique keys, derivation provenance)

Report in structured sections, not prose. Keep under 3000 chars.
```

### 1b: Existing Rules Inventory

If `.claude/rules/` exists, read every rule file. For each one, extract:
- File name and load class (frontmatter `paths:` present = scoped, absent = unconditional)
- Section headings (these are the rule categories)
- Individual rules (bullet points under each heading)
- Any file:line references (these need freshness checks)

Build a flat list: `[rule_file, category, rule_text, referenced_paths[]]`

Also read `CLAUDE.md` and extract:
- Sections that describe architecture, patterns, or conventions
- Any references to `.claude/rules/`
- File paths or line numbers mentioned anywhere

### 1c: Review Skill Cross-Reference

If a review skill exists (check `.claude/skills/*/SKILL.md` for review-related skills), read it and extract:
- What checks each agent performs
- What preflight scripts exist and what they scan for
- Known-correct pattern whitelists

This tells you what the review process catches, so rules can prevent those same issues upstream.

If preflight scripts exist (`.claude/scripts/preflight-*.sh`), read them and extract check IDs and what they detect.

---

## Phase 2: Coverage Analysis

Cross-reference what rules exist against what the project needs.

### 2a: Dimension Mapping

Read `references/review-dimensions.md` for the full taxonomy. For each dimension, ask two questions:

1. **Is this dimension relevant to this project?** A CLI tool doesn't need WebSocket rules. A static site doesn't need N+1 query rules. Skip irrelevant dimensions.

2. **Is this dimension covered by existing rules?** Map each relevant dimension to the rule file and bullet point that covers it. Mark uncovered dimensions.

**What "covered" means.** A dimension is covered only when a rule **explicitly forbids or prescribes** the pattern, with a concrete signal (file path, function name, framework primitive), not just a passing mention. "Validate input" alone is not coverage for SQL injection; "All SQL goes through `$pdo->prepare()`; never concatenate `$_POST` into a query string" is. If a rule only names the topic, mark it PARTIAL.

**Derive domain dimensions (do not stop at the fixed taxonomy).** `review-dimensions.md` covers generic engineering concerns (security/architecture/quality/performance). It cannot list the rules that only this codebase needs; those come from the DOMAIN VOCABULARY in the Phase 1 profile. For each item there, add a project-specific dimension row to the matrix and check coverage:

- **Enum/status semantics** → is there a rule stating what each value permits or forbids (which value gates outreach/publishing/deletion), and the `NONE`-vs-`NULL` style distinctions?
- **Status-machine transitions** → is the legal lifecycle written down, and are illegal transitions forbidden?
- **Subsystem invariants** → does each distinct subsystem (scraper, consolidator, importer, feature-flag registry) have a rule file or section capturing its non-obvious contract (SSRF/redirect model, dedup key, sync-safety)?
- **Cross-entity invariants** → is the integrity rule that must hold across tables/modules stated ("excluded rows never get positive flags", "analytics counts never overwritten on import")?
- **Content-integrity constraints** → are the "never edit this field via raw SQL", unique-key, and provenance rules present?

A rule set that covers every generic dimension but none of the domain dimensions is under-covering. These project-specific rules are usually the highest-value ones; they encode knowledge no linter or generic reviewer has. Mark each derived domain dimension Covered / Partial / Gap just like the taxonomy rows.

Output a coverage matrix:

```
COVERAGE MATRIX
===============
Dimension                    | Relevant? | Covered by           | Gap?
SQL injection                | YES       | security.md:Input    | NO
Command injection            | YES       | security.md:Subproc  | NO
Path traversal               | YES       | security.md:File     | NO
XSS                          | YES       | security.md:XSS      | NO
SSRF                         | YES       | security.md:Network  | NO
Cache invalidation           | YES       | web-layer.md:Cache   | NO
N+1 queries                  | NO (no ORM)| -                   | -
Registration/wiring          | YES       | web-layer.md:Reg     | NO
Type safety                  | YES       | code-quality.md:Type | NO
Dead code                    | YES       | code-quality.md:Dead | PARTIAL (no unused import rule)
Atomic file writes           | YES       | (none)               | YES: need file-operations.md
...
```

### 2b: Pattern Scan

Use detection scripts from `references/pattern-detection.md` (pick ones matching the project's stack) to find what actually exists in the codebase. This grounds the analysis in reality rather than theory.

For each pattern found, check: "Is there a rule that would have prevented/guided this?"

### 2c: Drift Detection

**First, check CLAUDE.md for `@imports` that defeat path-scoping.** Run:

```bash
rg -n '^[^`]*@\.claude/rules/' CLAUDE.md 2>/dev/null
```

Any match is a bug: the imported rule file is force-loaded every turn, ignoring its `paths:` frontmatter. Flag each one for removal in Phase 3 (replace the `@path/file.md` reference with a plain `file.md` mention so the path-scoping kicks in).

**Then check inventory bloat.** For each rule file, scan for content that's derivable from the codebase rather than rule content:

- ASCII directory trees (covered by `ls -F`)
- Tables of controllers / models / services / partials / routes (covered by `ls` of the relevant dir)
- Base-class method dumps (covered by reading the base class file)
- Helper function lists (covered by reading `helpers.php` or equivalent)
- URL route enumerations (covered by reading `routes.php` or equivalent)
- Token/color/spacing references (covered by reading the tokens file)

Mark every such block for replacement with a one-line pointer in Phase 3.

**Then existing reference checks.** For every file:line reference in existing rules:
- Does the file still exist?
- Does the referenced line still contain what the rule describes?
- Has the file been moved or renamed?

**Detect probable renames** (file gone but a sibling with a close name exists):

```bash
# For each missing file path referenced by a rule, look for a similar name
# in the same directory. Adjust the basename match to your tolerance.
for ref in $(rg -oN 'Reference:\s*`?([^`\s]+\.(py|php|ts|tsx|js|go|rb|java))' \
                 -r '$1' .claude/rules/ 2>/dev/null | sort -u); do
    if [ ! -f "$ref" ]; then
        dir=$(dirname "$ref")
        base=$(basename "$ref" | sed 's/\.[^.]*$//')
        # Candidates in the same directory whose name shares a token with the old name
        candidates=$(find "$dir" -maxdepth 1 -type f 2>/dev/null \
                     | grep -iE "$(echo "$base" | tr '_-' '|')" || true)
        echo "DRIFT: $ref missing; candidates: ${candidates:-none}"
    fi
done
```

For every pattern described in rules:
- Does the codebase still use this pattern?
- Has the convention changed since the rule was written?

For every path scope in rule frontmatter:
- Do files matching this glob still exist?
- Are there new directories that should be included?

**Then check any rule list kept for another agent.** A repo shared with Codex or another agent often carries an `AGENTS.md` that names the rule files that agent must always read. That list hardcodes file names, so it goes stale the moment a pass rescopes, renames, splits or adds a rule. Compare the files it names against the files that are actually unconditional:

```bash
if [ -f AGENTS.md ] && rg -q '\.claude/rules/' AGENTS.md; then
  named=$(rg -o '\.claude/rules/[A-Za-z0-9_-]+\.md' AGENTS.md | sed 's|\.claude/rules/||' | sort -u)
  actual=$(for f in .claude/rules/*.md; do head -n 15 "$f" | rg -q '^paths:' || basename "$f"; done | sort -u)
  comm -23 <(echo "$named") <(echo "$actual") | sed 's/^/NAMED BUT NOT UNCONDITIONAL: /'
  comm -13 <(echo "$named") <(echo "$actual") | sed 's/^/UNCONDITIONAL BUT NOT NAMED: /'
fi
```

An `AGENTS.md` that mentions a rule file in passing rather than as an always-read list will show noise here, so read the hits before reporting them. Do not fall back to `CLAUDE.md` `@imports` when there is no `AGENTS.md`: that list is the force-load trap from the first check in this phase, not a second agent's list, and comparing it would relabel a finding you already have. Do not edit `AGENTS.md` yourself; report the drift and propose the correction in Phase 5.

### 2d: Redundancy Check

- Are any rules duplicated across files?
- Do any rules contradict each other?
- Are there rules that duplicate what's already in `CLAUDE.md`?
- Are there rules that duplicate what's in the user's global `~/.claude/CLAUDE.md`?

---

### 2e: Context Budget

An unconditional rule file is paid for on every turn of every session; a path-scoped one is paid for only when it fires. This phase measures the bill per file, then decides file by file whether the lever is scoping or compression. The two are not interchangeable. Scope covers both `.claude/rules/` and every `CLAUDE.md` that loads for the project; running this skill in any project should optimize both in one pass.

**Measure the rule files first.** Size and frontmatter class, largest first:

```bash
for f in .claude/rules/*.md; do
    [ -f "$f" ] || continue
    if head -n 15 "$f" | rg -q '^paths:'; then cls=scoped
    elif head -n 15 "$f" | rg -q '^alwaysApply:'; then cls=cursor-legacy
    else cls=unscoped; fi
    printf '%7d  %-8s  %s\n' "$(wc -c < "$f")" "$cls" "$f"
done | sort -rn
```

`unscoped` means the file carries no `paths:` and therefore loads every session: "Rules without a `paths` field are loaded unconditionally", per the Claude Code memory docs, and directly observable in any session whose system prompt inlines its frontmatter-less rule files verbatim. `cursor-legacy` flags an `alwaysApply:` key, a Cursor rules convention that Claude Code neither documents nor honors (zero mentions across the memory and settings docs; the installed 2.1.220 binary contains the literal `alwaysApply: false` exactly once, a template artifact). Such a file is unconditional because it lacks `paths:`, not because of the marker. Report the marker as legacy noise, and never add one to mark a file unconditional. Flag every file over ~2KB that is not `scoped`. A flag is a question to answer with the decision rule below, not a verdict.

**Then verify the globs actually resolve.** Size and class are only half the picture: a scoped rule whose glob matches nothing never loads, and in an audit it reads as covered, which is strictly worse than having no rule. Run `scripts/verify-rule-globs.js`, giving the script its path inside this skill directory while keeping the **project root** as the working directory, since it reads `.claude/rules/` and shells out to `git ls-files` relative to wherever it is invoked:

```bash
cd /path/to/project && node /path/to/this/skill/scripts/verify-rule-globs.js
```

It resolves the same minimatch Claude Code bundles (the 2.1.220 binary carries minimatch's own `exports.GLOBSTAR` and `Minimatch` class), tests every `paths:` entry against `git ls-files` (falling back to an on-disk check for a literal path, so a gitignored-but-real target like `.env` isn't called dead), prints a match count per pattern, and exits 1 when a rule file has no live pattern at all. `--for <path>` answers the reverse question: which rules load when a given file is read. After installing or updating this plugin, run `npm ci --prefix /path/to/this/skill/scripts` once. The pinned dependency stays beside the skill, not in your global npm installation. Never substitute a shell glob for this check. `**` semantics differ between shells and minimatch, so a pattern you rewrote to make the shell happy proves nothing about the real matcher.

**Then measure what ONE read actually costs, and optimize that number rather than per-file size.** Per-file bytes are a proxy. The bill actually paid is the sum of every rule that loads together for one file, and rules that individually look reasonable stack into something that isn't. Take a baseline before changing anything, on five or six files chosen to span the tree (one per subsystem, plus one in the purest layer the architecture has):

```bash
for p in <representative files>; do
    printf '%9s  %s\n' \
      "$(node /path/to/this/skill/scripts/verify-rule-globs.js --for "$p" | rg -o 'read: [0-9]+' | rg -o '[0-9]+')" "$p"
done
```

Then read the baseline for two things:

- **The floor**: what EVERY file pays. A rule scoped to `src/**/*.py` is effectively unconditional for that language, so it belongs in the floor even though the measurement calls it `scoped`. Sum the floor and ask, rule by rule, whether a file in the project's purest layer can actually violate it. On one hex-architecture project the answer was no for a 16KB build rule that loaded on a `core/` file forbidden from doing I/O at all.
- **The stack**: which files pay several large rules at once. Those are where a split pays, and they are usually leaf adapters, which is also where most edits land.

Re-run the identical command after the changes and report before/after per file. A total-bytes figure across the directory is the wrong headline: a good pass often moves total bytes barely at all, because nothing was deleted, it just stopped loading where it does not apply.

**What `paths:` actually does** (verified 2026-07-27, three controlled runs with an `InstructionsLoaded` hook). These were measured, not assumed. Don't re-derive them:

- A path-scoped rule loads when Claude **reads** a file matching the glob. The hook logs `load_reason: path_glob_match` with a `trigger_file_path`.
- It does **not** load when Claude **writes** a matching file without having read one first. No warning, no log line, no rule.
- When the read is delegated to the `Explore` subagent, the rule loads into **that subagent**, not the main thread. The main thread then writes the file without it. Claude auto-delegates reads to `Explore` routinely, so this is the common case, not a corner case.

Three more, measured the same way on 2026-07-28 against 2.1.220 by reading back the `globs` array the hook reports:

- **One inline `paths:` value may hold several comma-separated globs, and Claude Code splits them itself.** `paths: a/**/*.php, b/**/*.php` was reported back as two patterns; the space after the comma is optional. This is a normal authoring form. Never rewrite it into a YAML block list, and never report it as a dead glob.
- **Braces are expanded before matching.** `app/{foo,bar}/**/*.php` came back already expanded to two patterns, so a comma inside braces is not a separator. Expand braces first, then split on commas, which is the order `verify-rule-globs.js` uses.
- **A rule loads when ANY one of its patterns matches.** A dead pattern beside a live one is dead weight worth pruning, not an unreachable rule. Only a file whose patterns ALL match nothing truly never loads; that is the case the report must escalate.

An earlier `verify-rule-globs.js` pushed the whole inline value as one glob and so reported every multi-pattern rule file as dead. On the first project it ran against that was 9 of 16 files, all of them working. If this check ever reports a wall of dead globs, suspect the parser before the rules.

**Decision rule.** For each flagged file, pick a column. Don't blanket-recommend `paths:`.

| Scope it with `paths:` when | Keep it unconditional when |
|-|-|
| It is reference material: an API shape, a schema, a convention catalog, a pattern index | It is a prohibition ("never `flush ruleset`", "never force-push to a shared branch") |
| Its absence degrades an answer rather than causing an incident | It is an access inventory or credential map, where absence produces a wrong conclusion ("I have no access to that host") |
| Claude reliably reads a matching file before acting | Its absence causes an incident rather than a worse answer |
| The governed workflow is read-then-edit | The governed workflow mostly **writes** files: new configs, generated scripts, scaffolded modules |

For a file that stays unconditional, the lever is compression, not scoping. Shrink it against the never-strip list below and leave the frontmatter alone. A 6KB prohibition file compressed to 3KB is a real win; the same file scoped with `paths:` is a silent regression.

**There is a third lever, and it beats both when the file covers more than one subsystem: split it.** A file that is already scoped and still large is usually not badly written, it is carrying several disjoint rule sets behind one union of paths, so every file in the union pays for all of them. The tell is a `paths:` list long enough that no single file matches most of it. A measured case: one 62KB rule file carried 28 paths spanning four subsystems, so editing a single adapter in one of them loaded all four. Split into four siblings with disjoint paths, that adapter's total dropped 43%.

Test for it: **would a competent reviewer of file X need section S?** Group sections by the answer, and each group with a distinct answer is a file. Splitting when the answer is the same for everything just creates two files that always load together, which is strictly worse than one.

Five rules for doing it without regressing:

- **Never copy the parent's `paths:` onto each child.** Four 15KB files each carrying the parent's 28-path list is a net loss and the single easiest way to make this pass worthless. Each child gets only the files its own rules govern.
- **Keep the original filename for the largest or most-referenced piece, and split the others out as siblings.** Renaming is what breaks things: check inbound references first with `rg -l '<name>\.md'` across the repo. One file had roughly 14 references including a comment in a source file, a CHANGELOG entry and three decision records, so it kept its name and the bulk moved to `<name>-<topic>.md` beside it.
- **Prefer flat prefixed names over subdirectories.** The docs say `.claude/rules/` is discovered recursively, so `rules/<subsystem>/input.md` works. But other tooling may not walk it: check for a flat `rules/*.md` glob in `AGENTS.md`, preflight scripts and CI before nesting. `<subsystem>-input.md` sorts identically and nothing has to be taught about it.
- **A prohibition does not split by path even when its subject does.** Split off the reference half and leave the rule half broad. A subprocess rule set divides cleanly into "never `shell=True`, always bound the wait" (governs the call site that does not exist yet, so it stays repo-wide) and "here are the 17 existing call sites and why each is safe" (reference material, read before touching one, so it scopes to those 17 files).
- **Say in `CLAUDE.md` that the globs are now narrow.** Narrower scoping has a real maintenance cost: a new file in a subsystem gets no rule until it is added to the matching `paths:`. That trade is worth making and worth writing down, next to the `--for` command that checks it.

**`CLAUDE.md` is unconditional by construction.** It can't be path-scoped, so compression is its only lever. Discover and measure every one that loads for this project, in lines, which is the unit the official guidance uses:

```bash
d=$(pwd)
{ while :; do
    for f in "$d/CLAUDE.md" "$d/CLAUDE.local.md" "$d/.claude/CLAUDE.md"; do
      [ -f "$f" ] && printf '%5d  %s\n' "$(wc -l < "$f")" "$f"
    done
    [ "$d" = "/" ] && break
    d=$(dirname "$d")
  done
  [ -f "$HOME/.claude/CLAUDE.md" ] && printf '%5d  %s\n' "$(wc -l < "$HOME/.claude/CLAUDE.md")" "$HOME/.claude/CLAUDE.md"
} | awk '!seen[$2]++'
```

Ancestor directories count. A `CLAUDE.md` three levels up loads for this project too and is the one people forget. Flag every file over 200 lines, per the target in the Claude Code memory docs (`docs.claude.com/en/docs/claude-code/memory`): "target under 200 lines per CLAUDE.md file. Longer files consume more context and reduce adherence." **Adherence is the point.** An oversized `CLAUDE.md` doesn't just cost tokens, it dilutes every instruction inside it, so the trim is a correctness fix worth proposing even when context is plentiful. The user's global `~/.claude/CLAUDE.md` belongs in the measurement because it loads, but it isn't this project's file: report it and get an explicit go before editing it.

**What to cut, what to keep in `CLAUDE.md`.** The same criteria `/doctor` applies:

| Cut it: Claude can derive it | Keep it: Claude cannot derive it |
|-|-|
| Directory layouts, file inventories | Pitfalls and gotchas, especially ones that already bit |
| Dependency lists | The rationale behind a convention |
| Generic architecture overviews | Conventions that differ from the tool's default |
| Restated framework defaults and language idioms | Exact commands, with their flags |
| Anything one `ls`, one manifest read, or one `rg` answers | Access pointers: hosts, tokens, where a credential lives |
| | Hard prohibitions ("never X") |

A cut block isn't always a deletion. If it is a real constraint that only applies to part of the tree, move it into a scoped rule file instead of dropping it; that is the trim and the rules analysis paying for each other.

**Check derivability, don't assume it.** Before cutting any block, prove the codebase actually says the same thing:

- Documented directory layout: run `ls` on that directory and compare it to the text.
- Dependency list: read `package.json` / `composer.json` / `pyproject.toml` / `go.mod` and compare.
- "This project uses pattern X": `rg` for it and confirm it's the dominant pattern rather than an aspiration.

A block that reproduces reality is a safe cut. A block that turns out **stale or wrong** is not: that's a separate finding. Report it as drift (Phase 2c) with the correct value, then either fix it in place or cut it with the correction recorded. Never silently delete something because it disagreed with the codebase. The disagreement is usually the most interesting thing the audit found.

**Complement `/doctor`, don't duplicate it.** Claude Code 2.1.206+ already proposes `CLAUDE.md` trims in `/doctor`. This skill's value is doing the trim in the same pass as the rules analysis, so a cut block can land in a scoped rule file instead of being lost, and doing it under the never-strip list and verify step below, which `/doctor` doesn't enforce. If `/doctor` has already trimmed the file, measure and move on rather than re-cutting.

**Rules that duplicate a skill: excise the section, keep the file.** Phase 2d already checks duplication against sibling rule files, `CLAUDE.md`, and the global `~/.claude/CLAUDE.md`. Extend the same check to installed skills (`.claude/skills/*/SKILL.md` and `~/.claude/skills/*/SKILL.md`), because a rule file often carries a catalog a skill has since absorbed. The typical shape: a project's `voice.md` holds a banned-vocabulary list that a writing skill already owns, while the rest of that file is a legitimate per-project overlay that has to stay. The output is an excision plus a one-line pointer ("banned vocabulary: `<skill-name>`"), not a deleted file. Delete the whole file only when every section of it is duplicated.

**Multi-step procedures are skill-migration candidates, with one caveat.** A rule file that has grown a numbered runbook (deploy sequence, release checklist, migration steps) is carrying procedure in a slot meant for constraints, and procedure belongs in a skill: loaded on demand, priced only when invoked. The caveat decides it: a skill fires on its `description`, and a vague `description` silently never fires. A rule that costs 3KB every turn but always applies beats a skill that costs nothing and never loads. Propose the migration only when you can write a `description` naming the concrete triggers (the tool, the command, the phrasing the user actually types), and have the rule file keep a one-line pointer to the skill.

**Never-strip list.** Any compression proposed anywhere in this skill, in rule files and in `CLAUDE.md` alike, must preserve, verbatim:

- Incident dates and version numbers
- Hostnames and full IP addresses. Never abbreviate `198.51.100.40` to `.40`
- Exact commands, including their flags
- File paths and config keys
- The sentence explaining why the rule exists

**Verify every compression.** Snapshot before editing, then confirm each identifier survived. Same procedure for a rule file and for `CLAUDE.md`, only `T` changes:

Match identifier **shapes**, never backtick pairs. A ``​`...`​`` pattern looks like the obvious way to catch commands and paths, and it silently breaks: any literal backtick inside a code span (a shell regex such as ``^[a-zA-Z0-9 !#$%&'*+-.^_`|~=/]*$`` contains one) throws off the pairing for the rest of the line, so tokens after it are never extracted and the check reports losses that did not happen. Unwrapping prose makes this worse, because one paragraph is now one long line and the mis-pairing cascades across all of it. This produced a full page of false LOST lines on a real run.

```bash
T=.claude/rules/foo.md                     # or CLAUDE.md
S=/tmp/trim-$(basename "$T")               # per-file name; distinct per file in a batch
git show "HEAD:$T" > "$S.pre"              # or cp "$T" "$S.pre" if not committed
# after editing, extract shapes from the pre-image and substring-check each one:
rg -oN -e '[0-9]{1,3}(\.[0-9]{1,3}){3}(:[0-9]+)?' \
       -e '[0-9]{4}-[0-9]{2}-[0-9]{2}' \
       -e '[A-Za-z0-9_*.-]+\.(lan|net|com|local|io|dev)\b' \
       -e '(/[A-Za-z0-9._-]+){2,}' \
       -e '[A-Za-z0-9_-]+\.(yml|yaml|json|conf|sh|py|md|service|sock)\b' \
       -e '\b[A-Z][A-Z0-9]{2,}(_[A-Z0-9]+)+\b' \
       -e '\b[a-z]+([A-Z][a-z0-9]+)+\b' \
       "$S.pre" | sort -u > "$S.ids"
while IFS= read -r id; do rg -qNF -- "$id" "$T" || echo "LOST: $id"; done < "$S.ids"
```

Any `LOST:` line is a regression: restore the identifier or abandon that edit. Two refinements learned from running this for real. First, on a `CLAUDE.md` trim a missing identifier does not always mean data loss: if the block was de-duplicated into a file the session still loads (a rule file, or the doc that CLAUDE.md names as source of truth), the identifier moved rather than died. So re-check each hit against the whole repo, `rg -F -- "$id" .claude/rules/ docs/`, and only treat it as a loss when it survives nowhere the session will read. Second, an identifier that genuinely vanished usually means a block you classified as derivable was carrying an access pointer or an exact command in passing, which is precisely what the never-strip list protects.

The pattern cannot check the last item on that list, so read the diff yourself as a separate pass and confirm the "why this exists" sentence is still there. A compressed rule that no longer says which incident produced it reads as unmotivated and gets deleted by the next audit.

When several files were produced from one pre-image, check each identifier against the **whole set** at once (`rg -qNF -- "$id" newA.md newB.md newC.md`), not against one file, or every relocated line reports as lost.

**After a split, run a second, different check: per-path fit.** The identifier sweep proves each identifier survives somewhere in the union of the new files. It does NOT prove a rule still loads for the file it governs, and those are separable: a rule can pass the grep and stop firing. Text that moved into a sibling whose `paths:` does not include the governed file is invisible exactly where it was needed. The union stays intact, so nothing looks wrong.

For every path in the ORIGINAL file's `paths:`, confirm the split still reaches it:

```bash
git show HEAD:.claude/rules/<original>.md | sed -n '/^paths:/,/^---$/p' \
  | rg -o '"[^"]+"' | tr -d '"' | while read -r p; do
    [ -e "$p" ] || { printf '%-55s MISSING FILE\n' "$p"; continue; }
    loaded=$(node /path/to/this/skill/scripts/verify-rule-globs.js --for "$p" | rg -o '<prefix>[a-z-]*\.md' | sort -u | tr '\n' ' ')
    printf '%-58s %s\n' "$p" "${loaded:-NONE}"
  done
```

`NONE` is a hard failure. But a single-entry row needs judgement too, and that is where the real miss hides: read what the file actually declares and ask whether the sibling it landed in covers it. On one split, a port file declaring eight interfaces matched only the first child, while the rules describing four of those interfaces had moved to the second; the fix is one path entry, and nothing else in the audit would have surfaced it.

Two more things this pass should report rather than hide:

- **Read the glob output unfiltered at least once.** `verify-rule-globs.js` exits non-zero only when a file has NO live pattern, so a file can carry several dead patterns beside one live one and still pass. After authoring dozens of new path entries, grep the full output for `0 files` instead of trusting the exit code.
- **A per-file cost that goes UP is not automatically a regression.** When a narrower glob newly includes a file that the old union missed, that file starts paying a rule that genuinely governs it, which is a coverage fix. Report it as one, with the reason, rather than quietly reverting to keep the numbers clean.

---

## Phase 3: Generate Changes

Based on the coverage analysis, determine what needs to change. Follow these priorities:

### Priority 1: Fix Drift (accuracy)
- Update stale file:line references
- Remove rules for patterns the project no longer uses
- Update path scopes to match current directory structure

### Priority 2: Restore Path-Scoping (efficiency)
- Replace any `@.claude/rules/foo.md` reference in `CLAUDE.md` with a plain mention (`see services.md`). The `@` prefix forces the file into context every turn and defeats the `paths:` frontmatter the user wrote.
- Removing an `@import` is only half the fix. It drops the file back to whatever its own frontmatter says, so a prohibition that had been reaching context through the `@import` silently stops firing on writes. Classify the file with the Phase 2e decision rule first. If it should be unconditional, the fix is simply to leave it without `paths:`, which is what makes a rule load every session. Do not add a marker field for it.
- Verify each rule file's load class is deliberate rather than accidental: `paths:` present means scoped, absent means it loads every session. Where the choice looks unconsidered, pick it with the Phase 2e decision rule rather than defaulting to `paths:`.

### Priority 2b: Split Multi-Subsystem Files (efficiency)
- Any scoped file that is still large after the scoping pass, and whose `paths:` list no single file matches most of, is a split candidate. Apply the "would a reviewer of file X need section S?" test and the five rules above.
- This is usually the biggest single win available, and it is invisible to a size-only audit: the files look fine individually, and only the per-read baseline shows them stacking.
- The split is not a rewrite. Move sections whole, preserve wording, and let each child keep the author's voice. Compression, if any, is a separate decision per section.
- Update `CLAUDE.md`'s rules table in the same pass. A split makes that table wrong immediately, and the table is how the next reader (and the review skill) maps scope to file.

### Priority 3: Strip Inventory Bloat (efficiency)
- Replace directory trees with `Layout: ls dir/`.
- Replace controller/model/service/partial/route inventories with `Inventory: ls path/`.
- Replace base-class method dumps with `Read app/path/Base.php for the API`.
- Replace helper/token/route enumerations with a one-line pointer to the source-of-truth file.
- Keep the rule (the "must"/"never"); drop the catalog. Inventories rot the moment files are added or renamed; pointers don't.

### Priority 4: Fill Gaps (completeness)
- Add missing rules for relevant uncovered dimensions
- Prefer adding to existing rule files over creating new ones
- New rules must be written as instructions, not code examples

### Priority 5: Reduce Redundancy (clarity)
- Remove duplicates (keep in the most specific file)
- Collapse near-identical rules into one clear statement
- Remove rules that restate what the framework already enforces
- **Exception: path-visibility duplication is intentional.** Before deleting a "duplicate," check the two files' `paths:` scopes. If the source-of-truth file is scoped to a directory that never loads when editing the file type where the rule is actually violated, the restatement is load-bearing, not noise. (Real case: a "no inline event handlers" rule in `js-standards.md` scoped `public/js/**` never loaded while editing PHP views, where every regression happened; the rule had to be restated in the views-scoped file with a cross-reference.) Keep both; ensure the restatement carries a one-line "source of truth: X" pointer.

### What NOT to Change
- The user's organizational structure (number of files, file names, section headings)
- Working rules that are correctly scoped and accurate
- Project-specific conventions the user documented from experience
- The level of detail the user chose (some projects have dense rules, some have sparse ones)

---

## Phase 4: Apply

### 4a: Run-Stamp Convention

Every rule file this skill audits gets a one-line HTML comment footer recording the audit date:

```html
<!-- rules-optimizer: audited YYYY-MM-DD -->
```

Place it at the end of the file, after all rule content, and replace an existing stamp in place rather than adding a second one. Without it, a file audited last week and a file nobody has checked in two years look identical, and the stale one is exactly what this skill hunts. The stamp records the audit date, not authorship, never renders in Markdown and never reads as a rule. A stamp older than the last significant change to the code its rules govern is a signal to re-audit. `CLAUDE.md` does not get one; report its line count instead.

### 4b: For Existing Rules (`--full` or `--sync`)

Edit rule files using preservation tags:

| Tag | Meaning | Action |
|-|-|-|
| **KEEP** | Accurate, well-scoped, no issues | Don't touch |
| **UPDATE** | Stale reference or path | Minimal targeted edit |
| **ADD** | Missing rule for a real gap | Append to relevant section |
| **REMOVE** | Covers a pattern that no longer exists | Delete the rule |
| **MOVE** | Rule in wrong file or wrong scope | Move to correct file |

For CLAUDE.md:
- Update the rules reference table if rule files were added/removed
- Fix any stale file paths or line numbers
- Apply the Phase 2e trim to every `CLAUDE.md` that loads for the project, then re-measure the line counts

### 4c: For New Rules (no existing `.claude/rules/`)

**First: pick the organization pattern.** Three patterns exist. Default to the first unless you have a specific reason:

| Pattern | When to use | Example files |
|-|-|-|
| **By Domain** (default) | Most projects. Rules grouped around the concern they protect. | `security.md`, `database.md`, `code-quality.md`, `web-layer.md` |
| **By Layer** | Architecture is strictly layered (controllers → services → repositories) and layer-specific rules actually differ. Don't use if "layer" is notional. | `controllers.md`, `services.md`, `repositories.md` |
| **By Platform** | Monorepo with distinct stacks that share a repo (e.g. backend PHP + mobile Dart + web TS). Each stack has its own conventions. | `be-security.md`, `mo-components.md`, `we-architecture.md` + one shared `code-quality.md` |

Pick one and stick to it: don't mix (`security.md` + `controllers.md` + `be-api.md` is noise).

Then determine rule files based on what the project actually needs. Common patterns across stacks:

**Python projects:**
- `security.md`: scoped to `src/**/*.py`
- `error-handling.md`: scoped to `src/**/*.py`
- `code-quality.md`: scoped to `src/**/*.py`
- Framework-specific (e.g., `web-layer.md` for Streamlit/Flask/Django): scoped to web directories
- Domain-specific if the project has distinct subsystems (e.g., `backup-engine.md`, `api.md`)

**PHP projects:**
- `security.md`: scoped to source directories
- `architecture.md`: typically unconditional (no `paths:`) for service-layer/MVC rules
- `database.md`: scoped to repository/model files
- `php-standards.md`: scoped to all PHP source
- Layer-specific files for each architectural layer (controllers, processors/services, repositories)
- `frontend.md`: scoped to view/template/JS/CSS files

**JavaScript/TypeScript projects:**
- `security.md`: scoped to `src/**/*.{ts,tsx}`
- `architecture.md`: scoped to source directories
- `api-integration.md`: scoped to API/service files
- `components.md`: scoped to component directories
- `state-management.md`: scoped to state/store files

**Multi-platform projects:**
- Prefix with platform: `be-security.md`, `mo-components.md`, `we-architecture.md`
- One cross-platform file for shared rules: `code-quality.md`

Whatever the stack, two things hold for a freshly generated set:

- **Exactly one always-on `security.md`:** leave it without `paths:` so it loads every session. Security review applies to every file; it's the one dimension that shouldn't wait for a path match.
- **Domain rule files derived from the Phase 1 DOMAIN VOCABULARY**, not just the generic stack list above. If the profile surfaced distinct subsystems (scraper, consolidator, scorer, feature-flag registry) or a rich enum/status vocabulary, generate a file (or a dedicated section) per subsystem, scoped to the files that implement it. These are usually the highest-value rules; don't ship a set that's all generic and zero domain.

Write rules as declarative instructions. Each rule is one bullet point. Group related rules under `##` headings. No code blocks longer than a one-liner. Use `Reference: path/file` when showing a pattern would be clearer than describing it. Where a recurring create-flow exists (adding a model/content-type/migration/endpoint), close the relevant file with a numbered "Adding a new X" checklist whose steps point to the sibling rule files; see `references/rule-style-guide.md` "Rule Shapes."

### 4d: Review generated rules against anti-patterns

Before declaring Phase 4 done, scan every file you created or touched against the anti-patterns in `references/rule-style-guide.md` (the "Anti-patterns" section near the bottom). Flag and fix any of these:

- **Tutorial file**: prose explaining *what* the framework does instead of *what this project does with it*.
- **Kitchen sink**: one file covers unrelated concerns (security + style + performance mixed together).
- **Aspirational rules**: rules that describe ideal behavior the codebase doesn't actually follow. Either remove or fix the code first.
- **Duplicates**: same rule appears in two files (or restates something already in `CLAUDE.md` or the global `~/.claude/CLAUDE.md`).
- **Stale references**: file paths or line numbers that no longer match the code (drift).
- **Unscoped when it should be scoped**: a `paths:`-less rule file that only applies to one part of the tree *and* is reference material (Phase 2e). A prohibition scoped to one part of the tree stays unconditional; compress it instead.
- **Inventory dump**: directory trees, lists of controllers/models/services/partials/routes, base-class method signatures, helper indexes, design-token catalogs. Replace with one-line pointers (`Inventory: ls path/`, `Methods: read path/Base.php`).
- **`@import` trap**: `CLAUDE.md` references a rule file with `@.claude/rules/foo.md`. That force-loads it every turn and breaks `paths:` scoping. Replace with a plain mention (`see foo.md`).
- **All-generic, zero-domain.** The set covers security/quality/architecture but encodes none of the project's own enum semantics, status machines, subsystem contracts, or cross-entity invariants (Phase 2a domain dimensions). A rule set a reviewer could have written without reading this codebase is under-covering it.
- **Missing always-on security.** No `security.md`, or it's path-scoped so narrowly it doesn't load on most edits. Security should be the one always-on file.

If you fix any, note them in the Phase 5 report so the user can see why.

After creating rules, add a reference section to CLAUDE.md:

```markdown
## Coding Rules (`.claude/rules/`)

Path-scoped rules auto-loaded when editing matching files.

| Rule file | Scope | Covers |
|-|-|-|
| `security.md` | `src/**/*.py` | Subprocess safety, input validation, secrets, XSS |
| ... | ... | ... |
```

---

## Phase 5: Report

Present the results:

### For `--audit-only`

```
## Rules Audit Report

### Coverage: X/Y relevant dimensions covered (Z%)

### Drift Found
| File | Rule | Issue |
|-|-|-|
| security.md | "ConfigManager handles YAML" | ConfigManager renamed to SettingsManager |
| web-layer.md | path scope `src/web/**` | New directory src/dashboard/ not covered |

### Gaps Found
| Dimension | Severity | Suggested Rule |
|-|-|-|
| Atomic file writes | HIGH | "Critical files must be written atomically via temp + rename" |
| Missing timeouts | MEDIUM | "All subprocess calls must include timeout=" |

### Redundancies
| Rule | Appears in | Keep in |
|-|-|-|
| "Use parameterized queries" | security.md, database.md | database.md |

### Context Budget
| File | Size | Class | Verdict |
|-|-|-|-|
| CLAUDE.md | 412 lines | always | TRIM to <200: §Layout + §Dependencies derivable (checked via `ls` and `package.json`), §Deploy steps move to `deploy.md` |
| ../CLAUDE.md (ancestor) | 240 lines | always | TRIM: loads for this project, user unaware |
| access-inventory.md | 5158 B | unscoped | KEEP unconditional (prohibition + credential map), compress to ~3k |
| api-shapes.md | 6120 B | unscoped | SCOPE to `src/api/**` (reference material, always read before edit) |
| voice.md | 3277 B | unscoped | EXCISE §3 (duplicates an installed writing skill), keep the rest |

Loaded every turn: N bytes across M files.

Looked derivable but wasn't (reported as drift, not cut):
- CLAUDE.md §Layout claimed `src/api/v1/`, actual is `src/api/` since the v2 merge

### AGENTS.md Rule-List Drift (only if AGENTS.md names rule files)
| Named in AGENTS.md | Actual load class | Status |
|-|-|-|
| security.md | unconditional | OK |
| api.md | scoped: `src/api/**` | AGENTS.md still tells the other agent to always read it |

### Run Stamps
| File | Last stamp | Status |
|-|-|-|
| security.md | 2026-03-02 | Current (governed code unchanged since) |
| api.md | 2025-11-20 | Stale: the code it governs changed after the audit |
| legacy.md | none | Never audited by this skill |

### Recommendations
- Add file-operations.md with 3 rules for atomic writes, TOCTOU, locking
- Update path scope in web-layer.md to include src/dashboard/
- Remove duplicate SQL injection rule from security.md (covered in database.md)
```

### For `--full` or `--sync` (including new rule creation)

```
## Rules Optimization Report

### Changes Applied

#### Updated Files
| File | Change | Reason |
|-|-|-|
| security.md | Updated 1 stale reference | ConfigManager → SettingsManager at line 15 |
| web-layer.md | Expanded path scope | Added src/dashboard/** to cover new directory |

#### New Files
| File | Scope | Rules added | Covers |
|-|-|-|
| file-operations.md | src/core/**/*.py | 3 rules | Atomic writes, TOCTOU, locking |

#### Removed
| File | Rule | Reason |
|-|-|-|
| security.md | "Use parameterized queries" | Duplicate of database.md rule |

#### Run Stamps Added/Updated
- security.md (added)
- api.md (updated 2025-11-20 -> 2026-03-02)

### Coverage After: X/Y relevant dimensions (Z%)

### Context Budget After: N bytes loaded every turn across M unconditional files (was P bytes / Q files). CLAUDE.md X lines (was Y, target <200)

### Review Skill Alignment
- Rules now cover N of M checks from the review skill
- Remaining uncovered checks are runtime-only (can't be prevented by rules)
```

---

## Reference Files

Read as needed during analysis:

| File | When to Read | Contains |
|-|-|-|
| `references/review-dimensions.md` | Phase 2a: dimension mapping | Full taxonomy of review categories |
| `references/pattern-detection.md` | Phase 2b: pattern scanning | Detection scripts per language/stack |
| `references/rule-style-guide.md` | Phase 4: writing new rules | Format, scoping, and style conventions |
| `scripts/verify-rule-globs.js` | Phase 2e: scoping check, and after writing any new `paths:` | Runnable. Invoke by its path in this skill directory with the project root as the working directory. Tests every glob with the minimatch Claude Code bundles; exits 1 on a dead glob. `--for <path>` lists which rules load for one file. After install or update, run `npm ci --prefix /path/to/this/skill/scripts` once. |
