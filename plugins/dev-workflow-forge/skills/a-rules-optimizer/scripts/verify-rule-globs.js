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
 * An earlier version of this script pushed the whole inline value as a single
 * glob, so every multi-pattern rule file reported DEAD GLOB. That is the exact
 * false-positive this script exists to prevent, pointed the wrong way: it would
 * have condemned 9 working rule files in the first project it was run against.
 *
 * Usage, from a project root:
 *   node verify-rule-globs.js               report every rule file and its globs
 *   node verify-rule-globs.js --for <path>  which rules load when editing <path>
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

/** Frontmatter paths, supporting `paths: glob` and the block-list form. */
function parseFrontmatter(text, braceExpand) {
    const m = text.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!m) return { paths: [], legacyMarker: false, hasFrontmatter: false };

    const body = m[1];
    const legacyMarker = /^alwaysApply\s*:/m.test(body);
    const paths = [];

    // Horizontal whitespace only: \s would match the newline after `paths:` and
    // swallow the first list item as if it were an inline value.
    const inline = body.match(/^paths[ \t]*:[ \t]*(\S.*)$/m);
    if (inline) {
        paths.push(...expandPatterns(inline[1].trim(), braceExpand));
    } else if (/^paths[ \t]*:[ \t]*$/m.test(body)) {
        let inBlock = false;
        for (const line of body.split(/\r?\n/)) {
            if (/^paths[ \t]*:[ \t]*$/.test(line)) { inBlock = true; continue; }
            if (!inBlock) continue;
            const item = line.match(/^\s*-\s*(.+?)\s*$/);
            if (item) paths.push(...expandPatterns(item[1], braceExpand));
            else if (line.trim() !== '') break; // next key ends the block
        }
    }
    return { paths, legacyMarker, hasFrontmatter: true };
}

/** A pattern with no glob metacharacter is a literal path, matchable on disk alone. */
function isLiteral(p) {
    return !/[*?[\]{}!+@]/.test(p);
}

/** Tracked files are the right universe: respects .gitignore, skips vendor/node_modules. */
function repoFiles() {
    try {
        return execSync('git ls-files', { encoding: 'utf8', maxBuffer: 64 * 1024 * 1024 })
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
    return fs.readdirSync(rulesDir).filter(f => f.endsWith('.md')).sort()
        .map(f => path.join(rulesDir, f));
}

function reportForFile(rules, minimatch, braceExpand, target) {
    const norm = target.replace(/^\.\//, '');
    console.log(`Rules that load when reading ${norm}:\n`);
    let any = false;
    let bytes = 0;
    for (const rf of rules) {
        const { paths, hasFrontmatter } = parseFrontmatter(fs.readFileSync(rf, 'utf8'), braceExpand);
        const name = path.basename(rf);
        const size = fs.statSync(rf).size;
        if (!hasFrontmatter || paths.length === 0) {
            console.log(`  [always]  ${name}  ${size} B`);
            any = true;
            bytes += size;
            continue;
        }
        const hit = paths.find(p => minimatch(norm, p));
        if (hit) {
            console.log(`  [scoped]  ${name}  ${size} B   via  ${hit}`);
            any = true;
            bytes += size;
        }
    }
    if (!any) console.log('  (none)');
    else console.log(`\n  Total in context for this read: ${bytes} B`);
    console.log('\nNote: a scoped rule fires on a READ of a matching file. It does not');
    console.log('fire when such a file is written without a matching read first.');
}

function reportAll(rules, minimatch, braceExpand, files) {
    let dead = 0, alwaysBytes = 0, alwaysCount = 0, scopedCount = 0, neverLoads = 0;

    for (const rf of rules) {
        const text = fs.readFileSync(rf, 'utf8');
        const { paths, legacyMarker, hasFrontmatter } = parseFrontmatter(text, braceExpand);
        const name = path.basename(rf);
        const bytes = Buffer.byteLength(text);

        if (!hasFrontmatter || paths.length === 0) {
            alwaysCount++;
            alwaysBytes += bytes;
            const note = legacyMarker
                ? '  (alwaysApply: is a Cursor convention Claude Code ignores; this file is'
                  + '\n            always-on because it has no paths:, not because of the marker)'
                : '';
            console.log(`ALWAYS  ${name}  ${bytes} B${note}`);
            continue;
        }

        scopedCount++;
        const matchedAll = new Set();
        const lines = [];
        for (const p of paths) {
            const hits = files.filter(f => minimatch(f, p));
            hits.forEach(h => matchedAll.add(h));
            // git ls-files can't see a gitignored file, but Claude Code matches
            // real reads. `.env` is the usual case: present, scoped, untracked.
            if (hits.length === 0 && isLiteral(p) && fs.existsSync(p)) {
                matchedAll.add(p);
                lines.push(`             1 file   ${p}  (untracked on disk)`);
                continue;
            }
            if (hits.length === 0) dead++;
            lines.push(`          ${hits.length === 0 ? 'DEAD GLOB ->' : String(hits.length).padStart(4) + ' files'}  ${p}`);
        }
        // A rule loads if ANY one pattern matches (verified against 2.1.220), so
        // a dead pattern beside a live one is dead weight, not a dead rule.
        const status = matchedAll.size === 0 ? '  <- NEVER LOADS' : '';
        if (matchedAll.size === 0) neverLoads++;
        console.log(`SCOPED  ${name}  ${bytes} B  ${matchedAll.size} distinct files${status}`);
        lines.forEach(l => console.log(l));
    }

    console.log(`\nAlways-on: ${alwaysBytes} B across ${alwaysCount} file(s), paid every turn.`);
    console.log(`Scoped:    ${scopedCount} file(s), paid only on a matching read.`);
    if (neverLoads > 0) {
        console.log(`\n${neverLoads} rule file(s) NEVER LOAD: every pattern is dead. Fix or remove them.`);
        if (dead > neverLoads) console.log(`${dead} dead pattern(s) in total; the rest sit beside a live pattern and are dead weight only.`);
        return 1;
    }
    if (dead > 0) {
        console.log(`\nNo unreachable rule files. ${dead} dead pattern(s) sit beside a live pattern:`);
        console.log('the rule still loads, but that pattern matches nothing. Worth pruning, not urgent.');
        return 0;
    }
    console.log('\nNo dead globs.');
    return 0;
}

function main() {
    const argv = process.argv.slice(2);
    const forIdx = argv.indexOf('--for');
    const rulesIdx = argv.indexOf('--rules');
    const rulesDir = rulesIdx !== -1 ? argv[rulesIdx + 1] : '.claude/rules';

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
        reportForFile(rules, minimatch, braceExpand, target);
        process.exit(0);
    }

    process.exit(reportAll(rules, minimatch, braceExpand, repoFiles()));
}

main();
