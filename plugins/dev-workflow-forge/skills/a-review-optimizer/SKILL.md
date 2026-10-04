---
name: a-review-optimizer
description: Create or improve a project-specific code review skill and its automated checks.
disable-model-invocation: true
---

# Review Skill Optimizer

Takes an existing review skill and makes it sharper by deeply analyzing the actual codebase. The approach is surgical: keep everything that works, fix what doesn't, add what's missing. The user built that skill with real experience. Don't throw it away.

**Input:** optional path to a review skill's SKILL.md (e.g., `.claude/skills/example-review/SKILL.md`)

If no path given, auto-detect: scan `.claude/skills/*/SKILL.md` for review-related skills (look for "review" in name, description, or content mentioning agents/preflight/findings). If exactly one found, use it. If multiple found, list them and ask which one. If none found, create a new review skill from scratch.

---

## Core Principle: Preserve First, Improve Surgically

The existing skill reflects real project knowledge: conventions the user discovered, false positives they already solved, agent scopes they tuned through experience. Treat it as the baseline, not a rough draft.

**Default behavior:** Keep every section of the existing skill unless the gap analysis gives a concrete reason to change it. When you do change something, the change must be traceable to a specific gap, overlap, or false positive you found.

**What gets preserved:**
- Agent names and their general scope (unless overlaps are found)
- Known-correct pattern whitelists (these are hard-won project knowledge)
- Output format structure (unless it lacks fix readiness fields)
- Existing preflight checks that still work
- Project-specific context sections and conventions documentation
- Anything the user invested effort into getting right

**What gets changed (with justification):**
- Gaps: missing checks the project needs but the skill doesn't cover
- False positives: patterns the skill flags that are actually correct in this project
- Overlaps: two agents checking the same thing (tighten scopes)
- Stale references: file:line examples pointing to code that no longer exists
- Missing preflight: deterministic checks that should exist but don't
- Missing fix readiness: findings without file:line + current code + proposed fix + why

---

## What This Skill Produces

**What you generate is an overlay, not a whole skill.** The review engine lives in the `a-review-core` skill that ships beside this one: scope resolution, the preflight protocol, dispatch, the angle sets, verify calibration, the finding contract, the report shape, reconciliation and capture. A generated skill opens by reading that skill in full, then supplies only what is true for its own project. Write nothing the core already covers: a second copy of the engine drifts from the original within a release, and the drift is silent.

**Adoption is per skill and non-breaking.** A skill that still carries its own copy of the engine keeps working. There is no flag day and no version to bump. Migrate one when you are already improving it, never as a sweep for its own sake.

By the end, you deliver back to the user an improved (or new) review skill package:

1. **Improved SKILL.md**: the existing skill with surgical changes: new checks added, false positive whitelists updated, agent scopes tightened, concrete examples refreshed from current codebase
2. **Preflight script**: new or improved deterministic checks (grep/rg + Python) tailored to patterns actually found in the project
3. **Gap report**: what you found and what you changed, so the user can verify you didn't break what was working
4. **Capture script**: `.claude/scripts/capture-finding.sh` if the skill doesn't already have one, so confirmed findings feed the self-learning loop (see `references/skill-scaffold.md` §6)

A fully-featured generated skill also carries a flag surface, a parallel-dispatch skeleton, a growing "Context Awareness (DO NOT flag)" whitelist, `--debt` scoring, `--full` architecture diagrams, self-learning capture, and rule-candidate surfacing. `references/skill-scaffold.md` documents every one of these sections. When improving, use it as a coverage checklist (missing section → `ADD`); when building from scratch, use it as the blueprint. Emit only the modes the project actually needs.

---

## Phase 1: Ingest the Existing Skill

Read the target SKILL.md completely. Extract, catalog, and **tag each section for preservation**:

- **Agents defined**: names, scopes, what each checks
- **Scope overlaps**: where two agents could flag the same thing
- **Coverage gaps**: categories of issues not assigned to any agent
- **Preflight scripts**: what exists, what checks they run, how results feed into agents
- **Output format**: what findings look like, whether they enforce fix readiness (file:line + current code + proposed fix + why)
- **Known-correct patterns**: whitelists, things agents are told to skip
- **Project-specific rules**: anything hardcoded to this project's conventions

For each section, assign a tag:

| Tag | Meaning | Action |
|-|-|-|
| **KEEP** | Works well, no issues found | Preserve verbatim |
| **UPDATE** | Needs extension (append checks) or correction (stale ref, scope overlap, false positive) | Targeted edit, preserve surrounding context |
| **ADD** | Needed but doesn't exist yet | Add a new section |
| **REMOVE** | Covers a pattern the project no longer uses (rare, prefer UPDATE for most cleanup) | Delete the section |
| **MOVE** | Correct content, wrong agent or scope | Relocate to the right place |
| **CORE** | Restates mechanics `a-review-core` already owns | Delete from the project skill, which now reads the core instead. Only when the project text adds nothing beyond it |

`CORE` is the one tag that needs care, because it deletes text. Read what you are removing rather than matching on headings: a section that looks generic often carries one project-specific caveat somebody learned the hard way, and losing that caveat to a tidy-up is the only real failure mode of this migration. Keep the caveat, drop the surrounding mechanics, and note the split in the diff summary.

The tag vocabulary is shared with `a-rules-optimizer` so both skills' diff summaries read the same way.

Default tag is **KEEP**. Only change what you have evidence to change.

If no existing review skill was found, skip this phase and proceed to Phase 2 to build one from scratch.

---

## Phase 2: Deep Project Analysis

This is the core of the optimizer. You need to understand the project as well as a senior engineer who's worked on it for 6 months. Don't skim: actually read the code.

### Step 1: Project Profile

The manifest checks below cover Python, JavaScript/TypeScript, PHP, Ruby, Go, Rust, and .NET. For Java add `pom.xml` / `build.gradle`, for Elixir `mix.exs`, for Swift `Package.swift`. **Adapt the stack-specific commands below to whatever language you detect**: the shape is the same (list the manifest, grep dependencies), only the filenames change.

```bash
# Language & framework detection
ls composer.json package.json requirements.txt Pipfile pyproject.toml go.mod Cargo.toml Gemfile *.sln pom.xml build.gradle mix.exs Package.swift 2>/dev/null
cat composer.json 2>/dev/null | grep -A5 '"require"' | head -20
cat package.json 2>/dev/null | grep -A10 '"dependencies"' | head -20
cat requirements.txt pyproject.toml 2>/dev/null | head -30

# Project structure
find . -maxdepth 3 -type d -not -path '*/\.*' -not -path '*/node_modules/*' -not -path '*/vendor/*' -not -path '*/__pycache__/*' -not -path '*/.git/*' | sort

# Entry points & architecture indicators
ls index.php main.py app.py manage.py server.* cmd/ src/ lib/ app/ 2>/dev/null
ls Dockerfile docker-compose.yml Makefile .github/workflows/ 2>/dev/null

# Config patterns
ls .env .env.example config/ *.yaml *.yml 2>/dev/null

# Test structure
find . -path '*/test*' -name '*.py' -o -path '*/test*' -name '*.php' -o -path '*/test*' -name '*.ts' -o -path '*/__tests__/*' -name '*.js' 2>/dev/null | head -20

# Size & complexity overview
find src/ app/ lib/ -name '*.py' -o -name '*.php' -o -name '*.ts' -o -name '*.js' 2>/dev/null | xargs wc -l 2>/dev/null | sort -rn | head -20
```

### Step 2: Convention Discovery

Read the 5-10 largest/most important files and document the conventions the project actually uses. You're looking for:

**Architecture patterns:**
- How is code organized? (MVC, service-repository, layered, modular, flat)
- How do modules communicate? (direct imports, events, message passing, DI container)
- Where does business logic live? (services, models, controllers, standalone functions)

**Error handling patterns:**
- How does the project handle failures? (exceptions, result tuples, error codes, Either types)
- Are there project-specific error classes?
- What's the logging strategy? (logger, print, console, Rich)

**State management:**
- Web: session, state store, context, global
- CLI: config objects, env vars, argument parsing
- Framework-specific: st.session_state (Streamlit), request context (Flask), etc.

**Config access:**
- How are settings loaded? (env, YAML, JSON, PHP config, .ini)
- Is there a centralized config manager or is it scattered?
- How are secrets handled?

**Data access patterns:**
- ORM or raw queries?
- Repository pattern or inline queries?
- How are connections managed?

**Registration patterns:**
- How are routes/views/commands registered?
- Are there maps, decorators, or auto-discovery?
- What needs to be exported/registered when adding new code?

**Return value conventions:**
- Do functions return specific shapes? (e.g., `(bool, str)` tuples, Result objects, response dicts)
- Are there project-specific conventions for success/failure?

### Step 3: Pattern Inventory

Programmatically scan for the patterns that a review skill should know about. Read `references/pattern-detection.md` for the full detection script library. Pick the scans relevant to this project's stack.

The goal: build a concrete list of "things that exist in this codebase" so the improved skill can reference real file:line examples.

```bash
# Example: find all exception handling patterns used in the project
rg -n 'except\s+\w+' --type py src/ | awk -F: '{print $3}' | sort | uniq -c | sort -rn

# Example: find all subprocess usage patterns
rg -n 'subprocess\.' --type py src/

# Example: find all route/view registrations
rg -n 'PAGE_MAP|url_patterns|@app.route|router\.' src/

# Example: find all cache patterns
rg -n 'cache|@st.cache|@lru_cache|Redis' src/
```

Adapt these scans to whatever stack you detected. The output feeds into Phase 3.

### Step 4: Find Real Issues (Sampling)

Actually review 3-5 files from the project yourself, applying the existing skill's checklist. Note:
- Issues the existing skill WOULD catch (working correctly)
- Issues the existing skill WOULD MISS (gaps)
- Things the existing skill WOULD falsely flag (false positives due to project conventions)

This sampling gives you concrete evidence for Phase 3.

---

## Phase 3: Gap Analysis

Compare what the existing skill checks against what the project actually needs. Produce a structured gap report.

> **Output framing.** The reports in 3a-3d are **internal**: Phase 3 is your planning artifact. Do not show these raw blocks to the user. The user-facing deliverable is the Phase 5 **Diff Summary**, which traces each change back to one of these Phase 3 findings.

### 3a: Missing Checks

For each issue category, ask: "Does the existing skill cover this for this specific project?"

Read `references/review-dimensions.md` for the full taxonomy of review dimensions. Cross-reference each dimension against the existing skill's agent prompts.

Output:
```
MISSING CHECKS
==============
[SECURITY] No check for pickle.load(): project uses pickle in src/cache/serializer.py
[ARCHITECTURE] No check for view registration: project uses PAGE_MAP in src/web/views/__init__.py
[QUALITY] No check for Python 3.10+ type modernization: project uses Optional[] in 14 files
[PERFORMANCE] No check for N+1: project uses SQLAlchemy with lazy loading
```

### 3b: False Positive Sources

Identify patterns the existing skill flags (or would flag) that are actually correct in this project.

Output:
```
FALSE POSITIVES TO WHITELIST
============================
[ARCHITECTURE] BackupEngine returns (bool, str) tuples: this is the project convention, not a code smell
[QUALITY] Click command functions appear unused: they're invoked by the Click framework via decorators
[QUALITY] Streamlit render functions appear uncalled: they're dispatched via PAGE_MAP string lookup
[SECURITY] .example config files are committed: this is intentional, real configs are gitignored
```

### 3c: Scope Overlaps

Check every pair of agents for items that both could flag. **Then check the review skill against its sibling skills in the same project**, not just its own agents. A project with a `*-perf`, `*-seo` or `*-docs` skill has a second tool claiming some of the same ground, usually with its own preflight and its own noise profile, and neither skill says who wins. The recurring pair is review-Quality against perf on N+1 and dead CSS.

Resolve by consequence, not by topic: the review skill keeps the findings with a correctness consequence (a cron read that OOMs the worker, a cache with no invalidation serving stale data) and the perf skill keeps "this could be faster". Write the boundary into the review skill's scope table, and do **not** edit the sibling skill: the same `*-perf` skill may exist in other projects where it is the only owner, so a one-sided note in the skill you were asked to improve is the safe form.

Output:
```
SCOPE OVERLAPS
==============
[Security × Architecture] Both check exception handling: Security checks "secrets in error messages", Architecture checks "bare except". These OVERLAP on: except blocks that log sensitive data. Fix: Security owns "what's in the error message", Architecture owns "how the exception is structured"
[Architecture × Quality] Both could flag "missing registration": Architecture checks view registration, Quality checks dead code. Fix: Architecture owns registration, Quality skips functions that appear in PAGE_MAP/route decorators
```

### 3d: Preflight Gaps

What deterministic checks should exist but don't? Compare the project's patterns against `references/pattern-detection.md`:

Output:
```
MISSING PREFLIGHT CHECKS
=========================
[NEED] subprocess calls without timeout: project has 8 subprocess calls, none checked by preflight
[NEED] st.rerun() without preceding invalidate(): project pattern requires cache invalidation before rerun
[NEED] View files not registered in PAGE_MAP: project uses explicit registration
[HAVE] Bare except check: already covered, working
[SKIP] innerHTML check: no HTML rendering in this project
```

---

## Phase 4: Generate Improved Skill

Apply targeted improvements based on the gap analysis. Follow the preservation tags from Phase 1. Default is KEEP: only touch what has a concrete reason to change.

### 4a: Enhance Agent Prompts

For each agent, check its preservation tag. If it's KEEP, don't touch it. If UPDATE, apply these additions/edits while keeping the existing prompt structure intact:

**Add if missing: YOUR SCOPE**: explicit, non-overlapping list. Use the overlap resolution from Phase 3c.

**KNOWN CORRECT PATTERNS (DO NOT FLAG)**: from Phase 3b. Include actual file:line references:
```
These patterns are correct in this project. Do not flag them:
- BackupEngine methods return (bool, str) tuples: see src/core/backup_engine.py:45
- @st.cache_resource used for heavy component init: see src/web/state.py:12
- Storage paths dict uses keys 'local' and 'sync': see src/core/config_manager.py:88
```

**CONCRETE EXAMPLES TO FIND**: from Phase 2 Step 4. Show agents what real issues look like in THIS codebase:
```
Look for patterns like these (found during analysis):
- src/cli.py:622: subprocess.run() without timeout (similar calls may exist elsewhere)
- src/web/views/text_sanitizer.py:45: st.rerun() without invalidate() in preceding lines
```

**PREFLIGHT KNOWN ISSUES**: placeholder for runtime injection from the preflight script:
```
The preflight scan found these issues in your scope. Verify each one:
${PREFLIGHT_SECURITY_FINDINGS}
For each: confirm it's real, add context about why it matters here, and look for similar patterns nearby.
```

**OUTPUT CONSTRAINT**: every finding must include all 5 fields:
```
Every finding MUST include:
1. File:Line: exact location
2. Current code: the line(s) as they exist
3. Proposed fix: what it should look like
4. Why: one sentence, specific to this project (not generic)
5. Intent ruled out: what you checked to confirm this is not deliberate. A comment on
   the thing itself, a sibling doing the same, a rule or allowlist naming it. If the
   current behaviour has a plausible reason to exist, state it and why it still fails.
   If you cannot find the reason, mark the finding intent-unverified rather than
   asserting a defect.
Findings missing any field are incomplete. Do not include them.
```

Field 5 is the one that stops inverted fixes: a correct claim about how something works does not establish that it is wrong. Ask what would break if the fix landed and the behaviour turned out to be intentional. The whitelists this skill maintains are the reactive half of the same problem, paid one false positive at a time; field 5 is the preventive half.

### 4b: Generate Preflight Script

Based on the preflight gaps from Phase 3d, write a bash script (with embedded Python for multi-line detection) that:

1. Runs checks specific to this project's stack and patterns
2. Outputs structured JSON with check IDs, status, file:line locations, and messages
3. Routes results to the correct agent by check ID prefix

Follow the pattern in `references/preflight-template.md` for the script structure.

Every check must:
- Have a unique ID (e.g., SEC-01, SUB-01, WEB-01)
- Map to exactly one agent
- Output file:line locations (not just counts)
- Handle the "not found" case gracefully (don't error on clean code)

For multi-line pattern detection (the #1 source of false negatives in grep-based scripts), use inline Python:
- Read full expressions from `(` to matching `)`
- Scan backward/forward N lines for required companion patterns
- Parse indent-based blocks for Python

### 4c: Add Reconciliation Rules

Add a post-review section that ensures nothing falls through cracks:

```
## Post-Flight Reconciliation

After all agents return:

1. DEDUP: Same file:line from multiple agents → keep the one from the owning agent
2. PREFLIGHT CHECK: Every preflight finding must appear in an agent report as either:
   - Confirmed (with expanded context and fix)
   - Dismissed (with specific reason why it's a false positive)
   If a preflight finding is missing from all reports, it was dropped. Flag it.
3. COMPLETENESS: Reject findings missing file:line, current code, proposed fix, or why.
4. SEVERITY GATE: Apply severity levels based on project-specific impact, not generic rules.
```

### 4d: Apply Changes Using Preservation Tags

Go through the existing skill section by section, applying the tags from Phase 1:

**KEEP sections:** Copy verbatim. Don't rephrase, don't "improve" wording, don't reorganize. If it works, leave it alone. The user will notice if their carefully worded whitelist entry got rephrased into something subtly different.

**UPDATE sections, append mode:** Keep the existing content as-is, then append new items below a clear marker:
```markdown
## Security Agent
[... existing checks preserved exactly ...]

### Added by a-review-optimizer [DATE]
- [NEW] Check for pickle.load(): found in src/cache/serializer.py:22
- [NEW] Check for yaml.load without SafeLoader: found in src/config/loader.py:8
```

**UPDATE sections, correction mode:** Make the minimal targeted edit. Show a before/after in the diff summary so the user can verify:
```
[UPDATE] Security agent scope: removed "exception handling" (was overlapping with Architecture)
  Before: "Check for injection, path traversal, credentials, exception handling"
  After:  "Check for injection, path traversal, credentials"
```

**ADD sections:** Add as new sections at the end of the relevant part of the skill, clearly marked:
```markdown
### [NEW] Preflight Automated Scan
Added by a-review-optimizer: this section did not exist in the original skill.
[... new content ...]
```

**REMOVE / MOVE sections:** Rare for review skills. Only remove content when a whole check targets a pattern the project provably no longer uses (confirmed via grep of current code). Only move when content is correct but clearly belongs under a different agent or phase. In both cases, note the rationale in the Phase 5 diff summary so the user can verify.

**What you must NEVER do:**
- Rewrite agent prompts from scratch when they just need a few additions
- Remove whitelist entries without confirming they're stale (check if the referenced file/pattern still exists)
- Change agent names or restructure the skill's overall flow
- Replace working preflight scripts with new ones (add checks to existing, or create a new script alongside)
- Remove existing check items just because they're not in your gap analysis (they might catch things you haven't seen yet)
- Rephrase project-specific conventions documentation (the user wrote it in their own words for a reason)

### 4e: Wire Modes, Self-Learning, and Rule Candidates

Beyond the agent prompts and preflight, a mature skill carries a set of structural sections that make it as capable as a hand-tuned one. Read `references/skill-scaffold.md` and, for each section, check whether the target skill has it. Missing sections are `ADD`; thin ones are `UPDATE`. Preserve any the user already tuned. This step only ever adds.

- **Flag surface** (§1): `--changed` default, plus `--full` / `--security-only` / `--debt` / `--all` where the project warrants them.
- **Execution / dispatch** (§2): dimensions dispatched through a mechanism that actually returns each agent's report (in Claude Code that is the Workflow tool; a bare batch of background Agent calls is the superseded form, because those agents go idle without delivering anything back and the review silently reports nothing), an Owns / Does-NOT-check scope table (this is where Phase 3c overlap resolutions get written down), preflight findings split by check-ID prefix into each agent's `PREFLIGHT KNOWN ISSUES` block, and an adversarial verify stage on every finding.
- **Context Awareness (DO NOT flag)** (§3): a centralized whitelist that GROWS: every preflight finding the review *dismisses* as a false positive gets appended here under a dated `### Added by a-review-optimizer [DATE]` marker with a real file:line referent. This is the same append discipline as 4d; do it for the whitelist, not just the agent prompts.
- **`--debt` mode** (§4): points-per-severity scoring (Critical 8 / High 4 / Medium 2 / Low 1, cap 100), a per-agent breakdown table, tightened thresholds, and an Auto-Fixable safe-vs-needs-confirmation split.
- **`--full` mode** (§5): component + layer Mermaid diagrams (scan the stack's import mechanism, cross-layer edges only) and a weighted Architecture Health Score. Skip for projects with no real layered structure.
- **Self-learning capture loop** (§6): emit `.claude/scripts/capture-finding.sh`, a `Capture Findings for Self-Learning (MANDATORY)` section (one RUN_ID per run, one call per confirmed finding), and a seeded stable category-slug table. This wires the skill into `a-self-learner`.
- **Rule candidates** (§7): surface any pattern hit in 3+ locations as a proposed rule for `.claude/rules/`, asking before adding.
- **Stack detection** (§8): if the project ships more than one stack (and most do: a server language plus browser JS plus SQL migrations plus CLI tooling), move stack specifics into `references/stack-*.md` gated on the changed paths. Check whether the target skill's briefs assume one language; if they do, the minority stacks are being reviewed with the wrong checklist, and that is a real gap rather than a tidiness issue.

Only emit modes the project needs: don't bolt `--debt` query scoring onto a static site or draw architecture diagrams for a 3-file script. But if the target skill is missing the self-learning loop, the whitelist-growth discipline, or the flag surface, those are real capability gaps: add them.

---

## Phase 5: Deliver

Present to the user:

1. **Gap Report**: summarize what you found (missing checks, false positives, overlaps, preflight gaps). Keep it concise: this is context, not the deliverable.

2. **Improved SKILL.md**: the existing skill with targeted changes applied, ready to drop in. The user should be able to diff this against the original and see exactly what changed. Say where it goes: a review skill activates as `/<name>` only when its `SKILL.md` sits at `.claude/skills/<name>/SKILL.md` (and its preflight script at `.claude/scripts/`), so name that write target explicitly instead of handing the user a file with no destination.

3. **Preflight Script**: if the project needs one (most do), the generated script.

4. **Diff Summary**: this is the external deliverable (contrast with the internal Phase 3 gap report). What changed, what stayed, and why. Every change must be traceable to a Phase 3 finding:
   ```
   CHANGES FROM ORIGINAL
   =====================
   [KEEP] Severity gating: no issues found, preserved as-is
   [KEEP] Known-correct patterns: all references still valid
   [KEEP] Output format structure: already had fix readiness columns
   [UPDATE] Security agent prompt: appended 2 checks (pickle.load, yaml.load) found in codebase
   [UPDATE] Preflight script: appended 4 new checks (SUB-01, WEB-01, TYPE-01, TYPE-02)
   [UPDATE] Agent scope overlap: Security no longer checks exception handling (Architecture owns it)
   [UPDATE] Stale reference: updated src/web/views/old_view.py:33 → src/web/views/dashboard.py:45
   [ADD] Fix Readiness Requirement: findings now require 5 fields
   [ADD] Post-flight reconciliation: preflight findings verified against agent output
   ```

5. **Verification checklist**: specific things the user should test to confirm the improved skill works:
   ```
   RUN THESE TO VERIFY
   ====================
   1. bash .claude/scripts/preflight-comprehensive.sh | python3 -m json.tool  (valid JSON?)
   2. /example-review --full  (catches known issues X, Y, Z from our analysis?)
   3. Check: zero duplicate findings across agents
   4. Check: every finding has file:line + current code + fix + why + intent ruled out
   ```

---

## When No Review Skill Exists

Building from scratch is fundamentally different from improving an existing skill: plan on **2-3× the time** and expect fewer project-specific insights unless Phase 2 is done deeply. Don't rush Phase 2.

The from-scratch workflow:

1. **Phase 1: SKIP**: nothing to ingest, no preservation tags to apply.
2. **Phase 2: FULL**: this is now your primary input. Read the code carefully; conventions you miss here become gaps you won't catch.
3. **Phase 3: SKIP gap-against-existing**: there's no baseline. Instead, treat `references/review-dimensions.md` as the complete checklist and decide which dimensions this project actually needs (a CLI-only Python tool doesn't need a "Web Patterns" agent; a static site doesn't need SSRF checks).
4. **Phase 4: Build an overlay, not a whole skill, and not from a generic template.**
   - Open the generated skill by reading the `a-review-core` skill in full. Everything below that line is this project's overlay.
   - Write nothing the core already covers. If you find yourself explaining dispatch, verify verdicts, the finding contract or the report skeleton, stop: that is the engine.
   - Decide how many agents make sense (2-4, based on project complexity, don't over-fragment).
   - Assign scopes based on Phase 2 findings + the dimensions you kept from Phase 3. Scopes must be non-overlapping.
   - Generate agent prompts with **concrete file:line examples from the codebase you actually read**: no generic "look for bare except" lines. Every check needs a real referent.
   - Generate a preflight script using only the checks that detect patterns the project actually uses.
   - Use the output format template from `references/output-template.md`.
   - Build out the structural sections from `references/skill-scaffold.md`: the flag surface, the dispatch mechanism and its scope table, a starter Context Awareness whitelist (from your Phase 2/3b false positives), the `--debt` / `--full` modes the project warrants, the self-learning capture loop (emit `capture-finding.sh` + the seeded slug table), and rule-candidate surfacing. A skill missing these reads generic. A mature one has all of them.
5. **Phase 5:** deliver as usual; the Diff Summary just reads "built from scratch, no prior version."

The result should be what an experienced engineer would write after working on the project for months, not a generic checklist with the project name swapped in. If the output reads generic, go back to Phase 2.

---

## Capability Checklist

Before delivering (improve or from-scratch), confirm the skill can produce each of these. A gap here is a `MISSING CHECK` for Phase 3; close it (stack-appropriately) unless the project genuinely doesn't need it. Don't remove a capability the user already has.

**An item the core supplies is satisfied by the core.** A skill that reads `a-review-core` inherits dispatch, verify calibration, the depth ladder, the mechanism angles, the FP taxonomy, the finding contract, the report shape, reconciliation and the capture protocol. Do not re-check those against the project skill's own text, and do not "fix" their absence by copying them back in. What remains genuinely the project's, and what this checklist is really for, is the list at the end of the core: flags and their recorded omissions, the preflight script and its check-ID table, dimensions and the Owns / Does NOT check table, the whitelist and its dated growth markers, stack references, rule routing, thresholds and the slug table.

**An item absent by a decision the skill records is compliant, not a gap.** Read before you flag: a skill that says why it omits something has answered this checklist already, and re-adding the item overrides a judgement made with more context than a checklist has. Typical recorded omissions are a skill that deliberately runs one stack lens and says when that was last re-checked, or one that drops `--full` and `--debt` because every run on a small codebase is already a full run. What is NOT compliant is silence: an item missing with no recorded reason is a gap, and the fix is either the capability or the sentence explaining its absence.

- [ ] **3+ non-overlapping dimensions, dispatched so the reports come back**: each with an explicit YOUR SCOPE / Owns list and a Does-NOT-check column; overlaps resolved (Phase 3c, `skill-scaffold.md` §2). A skill that fires a batch of background agents and never collects them is a `MISSING CHECK`, not a style preference: that form silently returns nothing.
- [ ] **Adversarial verify stage with three-state verdicts**: CONFIRMED / PLAUSIBLE / REFUTED from a second agent that traces the chain from source, with the strict prompt on precision runs and the recall-biased one on deep runs; the report states what was refuted alongside what was confirmed (`a-review-core`). A single refute-by-default prompt used at every depth is a `MISSING CHECK`: on a deep run it deletes the findings the run exists to produce.
- [ ] **Mechanism angles on the changed-scope run**: line scan including the enclosing function, removed-behavior audit, cross-file caller and callee trace, language pitfalls, wrapper correctness (`a-review-core`). Topic dimensions alone leave every diff-relative defect unowned, and the removed-behavior angle has no substitute anywhere else in the review.
- [ ] **Generic false-positive taxonomy in every agent brief**: pre-existing lines outside the change, linter territory, deliberate behavior changes, explicitly silenced rules (`a-review-core`). The project whitelist in §3 is the learned half; this is the half that is true before the project has learned anything.
- [ ] **Effort ladder**: angle count, per-angle candidate cap, verify strictness and the sweep pass all scale together, wired to the flag surface (`a-review-core`).
- [ ] **Deterministic preflight**: unique check IDs each mapped to one agent, JSON with file:line (not just counts), graceful clean handling, inline-Python for multi-line patterns (`preflight-template.md`).
- [ ] **Hostile-content preflight (INJ-*)**: invisible/bidi Unicode and AI-directed instruction phrases scanned deterministically in every generated preflight, whatever the stack. This is reviewer self-defense: the payload's target is the agent reading the file, so the check can never live in an agent prompt (`pattern-detection.md` > Hostile Content Detection).
- [ ] **Silent-failure coverage per stack**: empty or log-only catch detection for every language the project ships (not just the majority one), suppression-operator scans, fail-open return-default detection, and the shell-script checks (SH-*) when the project carries `.sh` files (`pattern-detection.md` > Error Handling, Shell Script Detection).
- [ ] **LLM dimension when applicable**: if the project calls an LLM API, the skill has a prompt-injection / output-handling agent scope and LLM-* preflight checks; if not, it has none (`review-dimensions.md` > LLM Integration Dimensions).
- [ ] **Fix readiness**: every finding carries file:line + current code + proposed fix + why + intent-ruled-out + an impact field; incomplete findings rejected (`output-template.md`).
- [ ] **Impact field split by kind**: `failure_scenario` for correctness, counted `cost` for maintainability. A skill requiring `failure_scenario` on *every* finding is a `MISSING CHECK`, not a style preference: duplication and dead-code findings cannot produce one, so they get invented or dropped at the gate (`output-template.md` > Fix Readiness Rules).
- [ ] **Skipped table**: a confirmed finding deliberately not acted on is reported with a reason and a revisit-when, so a skip is distinguishable from an oversight (`output-template.md`).
- [ ] **Stack detection**: stack specifics live in `references/stack-*.md` and load only when the diff touches that stack; `SKILL.md` stays stack-neutral (`skill-scaffold.md` §8). A skill applying one language's lens to every file is a `MISSING CHECK` for every other stack it ships.
- [ ] **Severity gating**: BLOCK/WARN/INFO tied to project-specific impact (`output-template.md`).
- [ ] **`--debt` mode**: points-per-severity score, per-agent breakdown table, Auto-Fixable safe-vs-needs-confirmation split (`skill-scaffold.md` §4).
- [ ] **`--full` mode**: component + layer Mermaid diagrams and an Architecture Health Score (`skill-scaffold.md` §5).
- [ ] **Flag surface**: `--changed` (default), `--full`, `--security-only`, `--debt`, `--all` (`skill-scaffold.md` §1).
- [ ] **Post-flight reconciliation**: dedup by owning agent, every preflight finding accounted (confirmed/dismissed), completeness reject, severity gate (Phase 4c).
- [ ] **Self-learning loop**: emits `capture-finding.sh`, a mandatory capture section with one RUN_ID per run, and a stable kebab-case slug table feeding `a-self-learner` (`skill-scaffold.md` §6).
- [ ] **Rule candidates**: recurring pattern (3+ locations) → propose a rule for `.claude/rules/`, ask before adding (`skill-scaffold.md` §7).
- [ ] **Context Awareness whitelist that grows**: a centralized DO-NOT-flag section; dismissed false positives appended each run under a dated marker (`skill-scaffold.md` §3).

---

## Reference Files

Read these as needed during analysis:

| File | When to Read | Contains |
|-|-|-|
| `references/review-dimensions.md` | Phase 3a (finding missing checks) | Complete taxonomy of review categories across all stacks |
| `references/pattern-detection.md` | Phase 2 Step 3 and Phase 4b | Library of grep/rg/Python detection scripts per language |
| `references/preflight-template.md` | Phase 4b (generating preflight script) | Bash+Python script template with JSON output |
| `references/output-template.md` | Phase 4 (when building from scratch) | Standard output format with fix readiness columns |
| the `a-review-core` skill | Before Phase 1, every run | The review engine a generated skill reads at runtime. Anything it covers is not the project skill's job. Read it so you can tell a project delta from a restatement of the engine |
| `references/benchmark.md` | After any improve or from-scratch pass, before claiming the skill got better | Plant known defects on a scratch branch, run the review, score recall and precision. `scripts/seed-defects.py` is the harness |
| `references/skill-scaffold.md` | Phase 4d and from-scratch build | Structural sections outside the agents: flags, dispatch + adversarial verify, growing whitelist, `--debt`/`--full` modes, self-learning capture loop, rule candidates, stack detection + per-stack references (§8) |
| `references/_shared.md` | Before editing `review-dimensions.md` or `pattern-detection.md` | Those two files are deliberately duplicated into `a-rules-optimizer/references/` so each skill stays self-contained. Any edit to either must update both copies in the same commit; `_shared.md` carries the parity check |
