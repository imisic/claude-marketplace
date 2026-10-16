#!/usr/bin/env node
/**
 * Verify .claude/rules/ path scoping against the real matcher.
 *
 * Claude Code bundles minimatch (confirmed in the 2.1.220 binary: the compiled
 * bundle carries minimatch's own exports.GLOBSTAR / Minimatch class). This
 * script resolves that same library so a `paths:` glob is tested with the
 * matcher that actually decides whether a rule loads, instead of a shell glob
 * that only approximates it.
 *
 * Why this exists: a scoped rule whose glob matches nothing never fires, and it
 * reads as covered in an audit. That is strictly worse than having no rule.
 *
 * How Claude Code actually parses `paths:` (verified 2026-07-28 against 2.1.220
 * with an InstructionsLoaded hook, reading the `globs` array it reports back):
 *   - One inline value holding several comma-separated globs IS split into
 *     several patterns. `a/**\/*.php, b/**\/*.php` was reported as two globs.
 *     Spaces after the comma are optional.
 *   - Braces are expanded before matching: `app/{foo,bar}/**\/*.php` came back
 *     as ["app/foo/**\/*.php", "app/bar/**\/*.php"].
 *   - A rule loads when ANY one of its patterns matches. The others may be dead
 *     without blocking the load.
 * Re-checked 2026-10-16 against 2.1.301 the same way: rule files in
 * subdirectories of .claude/rules/ load, and a YAML flow list
 * (`paths: ["a/**", "b/**"]`) loads like a block list. Both used to be missed
 * here: the directory read was flat and the flow list kept its brackets, so a
 * working rule reported NEVER LOADS.
 * An earlier version of this script pushed the whole inline value as a single
 * glob, so every multi-pattern rule file reported DEAD GLOB. That is the exact
 * false-positive this script exists to prevent, pointed the wrong way: it would
 * have condemned 9 working rule files in the first project it was run against.
 *
 * Usage, from a project root:
 *   node verify-rule-globs.js               report every rule file and its globs
 *   node verify-rule-globs.js --for <path>  which rules load when <path> is read or written
 *   add --json to either form for machine-readable output
 *   node verify-rule-globs.js --rules <dir> non-default rules directory
 *
 * Exit codes: 0 clean, 1 at least one dead glob, 2 setup problem.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

function loadMinimatch() {
    try {
        return require('minimatch');
    } catch {}
    try {
        const globalRoot = execSync('npm root -g', { encoding: 'utf8' }).trim();
        return require(path.join(globalRoot, 'minimatch'));
    } catch {}
    console.error('minimatch is not installed for this skill. Run: npm ci --prefix "' + __dirname + '"');
    process.exit(2);
}

/**
 * One frontmatter value to the pattern list Claude Code derives from it:
 * brace-expand first, then split the result on commas. Applying it in that
 * order keeps a comma inside `{a,b}` from being treated as a separator.
 */
function expandPatterns(raw, braceExpand) {
    const out = [];
    let expanded;
    try {
        expanded = braceExpand(raw);
    } catch {
        expanded = [raw];
    }
    for (const chunk of expanded) {
        for (const piece of chunk.split(',')) {
            const p = piece.trim().replace(/^["']|["']$/g, '');
            if (p) out.push(p);
        }
    }
    return [...new Set(out)];
}

/** Drop a YAML comment: ` #` outside quotes starts one. */
function stripComment(v) {
    let q = null;
    for (let i = 0; i < v.length; i++) {
        const c = v[i];
        if (q) { if (c === q) q = null; continue; }
        if (c === '"' || c === "'") q = c;
        else if (c === '#' && (i === 0 || /\s/.test(v[i - 1]))) return v.slice(0, i).trimEnd();
    }
    return v;
}

/** Inline value to the strings it holds: a YAML flow list loses its brackets. */
function inlineValues(v) {
    v = stripComment(v).trim();
    if (v.startsWith('[') && v.endsWith(']')) return [v.slice(1, -1)];
    return [v];
}

/** Frontmatter paths: inline scalar, comma string, flow list, or block list. */
function parseFrontmatter(text, braceExpand) {
    const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    // An opening fence with no closing one is reported, not silently read as an
    // always-on file: how the host treats it is unmeasured.
    if (!m) return { paths: [], legacyMarker: false, hasFrontmatter: false, malformed: /^---\r?\n/.test(text) };

    const body = m[1];
    const legacyMarker = /^alwaysApply\s*:/m.test(body);
    const paths = [];

    // Horizontal whitespace only: \s would match the newline after `paths:` and
    // swallow the first list item as if it were an inline value.
    const inline = body.match(/^paths[ \t]*:[ \t]*(\S.*)$/m);
    if (inline) {
        for (const v of inlineValues(inline[1])) paths.push(...expandPatterns(v, braceExpand));
    } else if (/^paths[ \t]*:[ \t]*$/m.test(body)) {
        let inBlock = false;
        for (const line of body.split(/\r?\n/)) {
            if (/^paths[ \t]*:[ \t]*$/.test(line)) { inBlock = true; continue; }
            if (!inBlock) continue;
            const item = line.match(/^\s*-\s*(.+?)\s*$/);
            if (item) paths.push(...expandPatterns(stripComment(item[1]), braceExpand));
            else if (line.trim() !== '' && !/^\s*#/.test(line)) break; // next key ends the block
        }
    }
    return { paths, legacyMarker, hasFrontmatter: true, malformed: false };
}

/** A pattern with no glob metacharacter is a literal path, matchable on disk alone. */
function isLiteral(p) {
    return !/[*?[\]{}!+@]/.test(p);
}

/**
 * Tracked plus untracked-but-not-ignored files: respects .gitignore, skips
 * vendor/node_modules, and still sees a new file nobody has staged yet.
 */
function repoFiles() {
    try {
        return execSync('git ls-files --cached --others --exclude-standard', { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
            .split('\n').filter(Boolean);
    } catch {
        console.error('Not a git repository. Run this from a project root.');
        process.exit(2);
    }
}

function ruleFiles(rulesDir) {
    if (!fs.existsSync(rulesDir)) {
        console.error(`No rules directory at ${rulesDir}`);
        process.exit(2);
    }
    // Recursive, as Claude Code discovers them. Symlinks are followed; the
    // realpath set stops a link cycle. See isExternal() for links that leave
    // the project.
    const out = [];
    const seen = new Set();
    (function walk(dir) {
        let real;
        try { real = fs.realpathSync(dir); } catch { return; }
        if (seen.has(real)) return;
        seen.add(real);
        for (const name of fs.readdirSync(dir).sort()) {
            const full = path.join(dir, name);
            let st;
            try { st = fs.statSync(full); } catch { continue; }
            if (st.isDirectory()) walk(full);
            else if (st.isFile() && name.endsWith('.md')) out.push(full);
        }
    })(rulesDir);
    return out;
}

/**
 * A rule file whose real path is outside the project. Claude Code treats it as
 * an external import (memory docs): nothing loads until external imports are
 * approved, and after that only rules WITHOUT `paths:` do. So an external
 * scoped rule never loads, however live its globs look.
 */
function isExternal(rf) {
    const root = fs.realpathSync(process.cwd());
    const real = fs.realpathSync(rf);
    return real !== root && !real.startsWith(root + path.sep);
}

/** Rule name relative to the rules dir, so nested/a.md and a.md stay distinct. */
const ruleName = (rulesDir, rf) => path.relative(rulesDir, rf);

function reportForFile(rules, rulesDir, minimatch, braceExpand, target, asJson) {
    // Patterns are project-relative, so an absolute or ./ target is made relative
    // to the project root (the cwd) before matching.
    const norm = path.relative(process.cwd(), path.resolve(target)).split(path.sep).join('/');
    const loaded = [];
    for (const rf of rules) {
        const { paths, hasFrontmatter, malformed } = parseFrontmatter(fs.readFileSync(rf, 'utf8'), braceExpand);
        const name = ruleName(rulesDir, rf);
        const size = fs.statSync(rf).size;
        const external = isExternal(rf);
        if (!hasFrontmatter || paths.length === 0) {
            loaded.push({ rule: name, class: 'always', bytes: size, via: null, malformed, external });
            continue;
        }
        if (external) continue;
        const hit = paths.find(p => minimatch(norm, p));
        if (hit) loaded.push({ rule: name, class: 'scoped', bytes: size, via: hit, malformed });
    }
    const total = loaded.reduce((n, r) => n + r.bytes, 0);
    if (asJson) {
        console.log(JSON.stringify({ target: norm, rules: loaded, total_bytes: total }, null, 2));
        return;
    }
    console.log(`Rules that load for ${norm}:\n`);
    if (loaded.length === 0) console.log('  (none)');
    for (const r of loaded) {
        console.log(`  [${r.class}]  ${r.rule}  ${r.bytes} B${r.via ? '   via  ' + r.via : ''}${r.malformed ? '  (unclosed frontmatter)' : ''}${r.external ? '  (external link: only after import approval)' : ''}`);
    }
    if (loaded.length) console.log(`\n  Total in context for this read: ${total} B`);
    console.log('\nNote: this is the cost for this one file, not what a session has accumulated.');
    console.log('A scoped rule loads AFTER the Read or Write that touches a matching file');
    console.log('(2.1.301), so it cannot shape the first write of a new file.');
}

function reportAll(rules, rulesDir, minimatch, braceExpand, files, asJson) {
    const log = asJson ? () => {} : (...a) => console.log(...a);
    const summary = [];
    let dead = 0, alwaysBytes = 0, alwaysCount = 0, scopedCount = 0, neverLoads = 0;

    for (const rf of rules) {
        const text = fs.readFileSync(rf, 'utf8');
        const { paths, legacyMarker, hasFrontmatter, malformed } = parseFrontmatter(text, braceExpand);
        const name = ruleName(rulesDir, rf);
        const bytes = Buffer.byteLength(text);
        const external = isExternal(rf);

        if (!hasFrontmatter || paths.length === 0) {
            alwaysCount++;
            alwaysBytes += bytes;
            const note = legacyMarker
                ? '  (alwaysApply: is a Cursor convention Claude Code ignores; this file is'
                  + '\n            always-on because it has no paths:, not because of the marker)'
                : '';
            log(`ALWAYS  ${name}  ${bytes} B${note}${malformed ? '  (unclosed frontmatter: host behaviour unmeasured)' : ''}`);
            summary.push({ rule: name, class: 'always', bytes, malformed, legacy_marker: legacyMarker });
            continue;
        }

        scopedCount++;
        const matchedAll = new Set();
        const lines = [];
        const patterns = [];
        for (const p of paths) {
            const hits = files.filter(f => minimatch(f, p));
            hits.forEach(h => matchedAll.add(h));
            // git ls-files can't see a gitignored file, but Claude Code matches
            // real reads. `.env` is the usual case: present, scoped, untracked.
            if (hits.length === 0 && isLiteral(p) && fs.existsSync(p)) {
                matchedAll.add(p);
                lines.push(`             1 file   ${p}  (ignored, present on disk)`);
                patterns.push({ pattern: p, matches: 1, ignored_on_disk: true });
                continue;
            }
            if (hits.length === 0) dead++;
            patterns.push({ pattern: p, matches: hits.length });
            lines.push(`          ${hits.length === 0 ? 'DEAD GLOB ->' : String(hits.length).padStart(4) + ' files'}  ${p}`);
        }
        // A rule loads if ANY one pattern matches (verified against 2.1.220), so
        // a dead pattern beside a live one is dead weight, not a dead rule.
        const never = matchedAll.size === 0 || external;
        const status = external ? '  <- NEVER LOADS (external symlink: scoped external rules do not load)'
            : never ? '  <- NEVER LOADS' : '';
        if (never) neverLoads++;
        log(`SCOPED  ${name}  ${bytes} B  ${matchedAll.size} distinct files${status}`);
        lines.forEach(l => log(l));
        summary.push({ rule: name, class: 'scoped', bytes, distinct_files: matchedAll.size, never_loads: never, external, patterns });
    }

    const code = neverLoads > 0 ? 1 : 0;
    if (asJson) {
        console.log(JSON.stringify({ rules: summary, always_bytes: alwaysBytes, dead_patterns: dead, never_loads: neverLoads }, null, 2));
        return code;
    }
    console.log(`\nAlways-on: ${alwaysBytes} B across ${alwaysCount} file(s), paid every turn.`);
    console.log(`Scoped:    ${scopedCount} file(s), paid only when a matching file is read or written.`);
    if (neverLoads > 0) {
        console.log(`\n${neverLoads} rule file(s) NEVER LOAD: every pattern is dead, or the file is an external scoped link. Fix or remove them.`);
        if (dead > neverLoads) console.log(`${dead} dead pattern(s) in total; the rest sit beside a live pattern and are dead weight only.`);
        return code;
    }
    if (dead > 0) {
        console.log(`\nNo unreachable rule files. ${dead} dead pattern(s) sit beside a live pattern:`);
        console.log('the rule still loads, but that pattern matches nothing. Worth pruning, not urgent.');
        return code;
    }
    console.log('\nNo dead globs.');
    return code;
}

function main() {
    const argv = process.argv.slice(2);
    const forIdx = argv.indexOf('--for');
    const rulesIdx = argv.indexOf('--rules');
    const rulesDir = rulesIdx !== -1 ? argv[rulesIdx + 1] : '.claude/rules';
    const asJson = argv.includes('--json');

    const mm = loadMinimatch();
    const minimatch = mm.minimatch;
    const braceExpand = mm.braceExpand;
    const rules = ruleFiles(rulesDir);

    if (forIdx !== -1) {
        const target = argv[forIdx + 1];
        if (!target) {
            console.error('--for needs a file path');
            process.exit(2);
        }
        reportForFile(rules, rulesDir, minimatch, braceExpand, target, asJson);
        process.exit(0);
    }

    process.exit(reportAll(rules, rulesDir, minimatch, braceExpand, repoFiles(), asJson));
}

main();
