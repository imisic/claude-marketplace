# Seeded-Defect Benchmark

Read this after any improve or from-scratch pass, before claiming the skill got better. Until a round has run, "the review skill now catches more" is an opinion.

The problem it solves: this skill rewrites another skill and then hands it back with no measurement. Plant defects the fleet has actually shipped, run the review, count how many it found. That turns "did the optimizer help" into two numbers you can put side by side.

## Parts

| Path | What it is |
|-|-|
| `benchmarks/corpus.json` | 22 defects, 11 PHP and 11 Python, each one a real past finding mined from the fleet review logs |
| `scripts/seed-defects.py` | The harness: list, plant, verify, score, restore. Standard library only, no venv |
| `benchmarks/test-guards.sh` | Regression test for the harness: asserts every guard refuses, exits 1 if one stops refusing |

The corpus was built by scanning 2014 rows across six `review-issues*.jsonl` files from four projects, two PHP and two Python. Selection favoured categories that recurred across several files and several run dates, because a category that fired once is a one-off and a category that fired on eight dates is what the fleet keeps getting wrong. Each entry carries its `recurrence` counts so you can re-derive the ranking. No project name, file path, line or date is recorded: the corpus travels, and a defect list naming real files in real sites is not something to hand around.

Whitelisted rows and preflight false positives are excluded from those counts, and a category whose every logged instance was a false positive was dropped outright. `gather-without-watchdog` was in an early draft and came out again: all ten of its logged rows are whitelisted, so seeding it would train the reviewer to flag exactly what the project already ruled acceptable. `recurrence.whitelisted_in_log` keeps that check visible per entry.

Category slugs are the real ones from the capture schema, so a benchmark result ties back to the same `category` field `a-self-learner` groups on.

## Design decisions worth knowing before you use it

**JSON, not YAML, for the manifest.** The harness is standard library only, and stdlib has no YAML parser. The multi-line code snippets live as line arrays (`"snippet": ["line", "line"]`), which reads fine in a diff and needs no dependency.

**Seeds are appended, never patched in place.** Every seed is a self-contained top-level function or class appended to a target file. An anchored find-and-replace mutation would need an anchor that exists in the target repo, and no anchor is portable across repos, so the manifest could not carry one. The tradeoff: appended code is new code, so a diff-scoped review sees it as added. That matches how most of these defects entered the real repos in the first place.

**The snippets carry no seed markers.** No `// benchmark seed php-04` comment, no distinctive names beyond a `bench` prefix that reads as ordinary code. A marker would make the benchmark trivially winnable and the number meaningless.

**One commit per defect.** `git log --oneline` then shows exactly what is planted, `git bisect` can isolate which seed a reviewer reacted to, and `--restore` has a recorded base to reset to. They stack, so HEAD carries all of them for a single review run.

**State lives in `.git/seed-defects-state.json`.** Never tracked, never shows as dirty, and a throwaway worktree takes it with it when removed, so the state cannot outlive the tree it describes.

## The guards

Planting defects into real code is the one unacceptable failure of this tool, so the location check runs before anything is written.

| Guard | Refuses when |
|-|-|
| Protected branch | branch is `main`, `master`, `develop`, `trunk`, `production`, `release`, `stable`, prefix match or not |
| Not a scratch location | branch does not start with `--scratch-prefix` (default `benchmark/`) AND the tree is not a linked git worktree |
| Detached HEAD | `HEAD` is detached, so there is no branch to reset |
| Dirty tree | `git status --porcelain` is non-empty, because restore could not then tell your work from the planted defects |
| Already planted | a state file exists; run `--restore` first |
| Target outside the repo | the real path of a `--target`, after `..` and symlinks are resolved, is not under the repo. Containment is proved twice, once at argument parsing and again immediately before the write |
| Foreign commits (restore only) | a commit without the `seed-defect:` prefix sits on top of the planted ones; restore would discard it |

All refusals exit 2 and write nothing. `benchmarks/test-guards.sh` is the regression test: it builds a throwaway repo under `mktemp -d`, asserts each plant guard exits 2, says `REFUSED` and adds no commit, asserts the file outside the repo is byte-identical after the traversal case, then runs a full plant, verify, score and restore cycle. It prints `FAILED` and exits 1 on any broken assertion, so a guard that stops refusing breaks the script instead of reading as a pass. Run it after editing the harness.

## A round

Five steps. Steps 3 and 4 are the only ones that need judgement.

**1. Cut the scratch branch.**

```bash
cd /path/to/your/project
git switch -c benchmark/round-1
```

A linked worktree works too and keeps your main checkout usable while the review runs:

```bash
git worktree add -b benchmark/round-1 /tmp/bench-round-1
```

**2. Plant.** Pick targets that are plain code files, not templates: a PHP class or helper file, a Python module. Never an HTML-bearing view, because an appended top-level function lands in the rendered output. Give one target per extension the corpus needs; `php-07` is a `.js` seed and is skipped with a named reason if you give no `.js` target.

```bash
python3 scripts/seed-defects.py --plant \
  --repo . --stack php \
  --target app/Helpers/InvoiceFormatter.php app/Repositories/UserRepository.php public/js/admin/calendar.js
```

Several targets spread the seeds one per file in turn, which is closer to a real diff than dropping all eleven into one file.

**3. Run the project's own review skill** over the planted commits, diff-scoped against the base. Capture its findings to a file. Any shape works as long as each finding carries a file, a line and a category: `.jsonl` one object per line, or `.json` holding a list or an object with a `findings`, `issues` or `results` key. The field names `file` / `path` / `file_path` / `filename`, `line` / `line_number` / `lineno` / `start_line`, and `category` / `slug` / `rule` / `check` / `check_id` are all read. A skill that already emits `capture-finding.sh` rows can hand over its `review-issues.jsonl` directly. Paths are compared repo-relative; an absolute path or a bare filename falls back to a basename match, so a review that reports `/abs/path/to/repo/app/Helpers.php` still scores.

**4. Score.**

```bash
python3 scripts/seed-defects.py --score /tmp/findings.jsonl --repo . --out /tmp/round-1.json
```

Optionally `--verify` first, which confirms every seed is still byte-identical in the tree. Worth doing when a review run was long, or when anything might have touched the branch.

**5. Restore.**

```bash
python3 scripts/seed-defects.py --restore --repo .
git switch -   # then delete the branch, or remove the worktree
```

## Reading the numbers

```
recall     9/22 = 0.41   planted defects the review found
precision  9/13 = 0.69   reported findings that matched a planted defect
unmatched  4 findings matched no planted defect
by severity   high 3/5  info 0/1  low 3/6  medium 3/10
by dimension  architecture 1/6  performance 0/1  quality 4/7  security 4/8
```

## Build your own corpus

The shipped corpus is small and carries no provenance on purpose: a corpus travels between machines and people, and a list naming real defects in real files is not something to hand around. It is also the wrong corpus for anyone else. A benchmark only means something when it seeds the defects THIS codebase keeps producing, which is exactly what its own review log already records.

```bash
python3 scripts/seed-defects.py --repo . --build-corpus
```

That reads `.claude/reviews/review-issues.jsonl`, groups confirmed findings by category, keeps the patterns that recurred across two or more distinct files (raise the bar with `--min-recurrence`), and writes a draft carrying the recurrence counts and nothing else: no project, no path, no line, no date.

It deliberately leaves `description` and `seed.snippet` empty, and `--plant` skips any entry whose snippet is empty. Only someone who knows the stack can write a defect that looks like it belongs in this code, and an invented one measures nothing. Filling in ten of them is an hour of work that pays for itself the first time you need to know whether a change to the review skill actually helped.

**Recall is the number that matters.** It is the share of planted defects the review found. A match needs the same file, a line inside the planted block widened by `--tolerance` (default 3), and the same category slug. Adjacent seeds split the gap between them so a finding is credited to the right defect, which caps the reachable widening at half the blank-line gap the planter leaves (`SEED_GAP // 2`, currently 4). A `--tolerance` above that is silently capped, so raise `SEED_GAP` rather than the flag if you need a wider window. `--match file-line` drops the category requirement, which is useful once: if recall jumps when you relax it, the skill is seeing the defects but filing them under the wrong slug, and the fix is the slug table, not the agent prompts.

Seeds sit two blank lines apart, so a raw `+/-3` window would reach into the neighbouring seed. Windows are therefore split at the midpoint of the gap between adjacent seeds in the same file, and no line belongs to two of them. Without that, a finding on one seed's own line scored as a hit for the seed above it, recall rose for the wrong reason, and the `--match file-line` diagnostic above stopped meaning anything.

**Precision is weaker evidence, and the tool says so.** Unmatched findings are not automatically false positives. A scratch branch cut from real code still carries real pre-existing defects, and a reviewer flagging one of those is right. Precision only means something when the review ran diff-scoped over the planted commits, and even then treat a low number as a prompt to read the four unmatched findings rather than as a score.

**Per-dimension recall is where the actionable signal is.** A skill at 0.41 overall but 0/6 on architecture has an agent scope gap, not a general weakness. That maps straight onto a Phase 3a `MISSING CHECK`.

**What a good score looks like.** There is no absolute bar, because the corpus is not calibrated against anything. The only number worth acting on is the delta between two rounds on the same corpus, same targets, same review flags. Below about 0.5 on a corpus drawn from this fleet's own recurring findings, the skill is missing categories it has already been told about, which is the strongest possible evidence of a gap. Above that, compare against the previous round and ignore the absolute value.

## What it does not prove

Say this out loud in any report that quotes a benchmark number, because the number invites more confidence than it earns.

- **It measures recall on known defect classes only.** Twenty-two categories, all of them things the fleet already caught at least once. A review skill that scores 1.00 has proven it catches defects that were already in the logs. It has proven nothing about the next novel bug, and novel bugs are most of what a review is for.
- **The seeds are synthetic instances of real categories, not the real code.** A real `wrong-array-key-silent-fallback` finding usually needs the reviewer to know which columns a repository method selects, in a file far from where the key is read. The seed hands it a self-contained function where the mismatch is visible in six lines. Recall on the seed overstates recall on the real thing.
- **Optimizing a review skill to score well on a fixed corpus is overfitting, and it will happen if you let it.** Adding a grep for `benchNotificationLanguage`, or a check tuned to the exact shape of a seed, raises the score and improves nothing. The corpus is a smoke test, not a target. If a round shows a miss, fix the underlying dimension so the skill would also catch the original finding the seed came from, then re-run.
- **Appended code is easier than embedded code.** The seed sits at the end of a file with no surrounding context to distract the reviewer. Real defects hide in the middle of a 400-line class.
- **A miss can be a scope decision, not a gap.** A CLI-only Python tool has no reason to carry an `innerhtml-external-data` check. Read the misses before treating them as failures.

## When to re-run

**After an a-review-optimizer pass, as before-and-after.** Run a round against the current skill, keep the `--out` JSON, apply the optimizer's changes, restore, plant again with the same `--stack`, `--ids` and `--target`, run again. The two `recall` numbers are the delta the pass bought. Anything else, including the improve report's own diff summary, is a claim about the skill rather than a measurement of it.

**After a self-learning cycle**, when `a-self-learner` has fed new rules or checks back in and you want to know whether the loop closed on anything.

**When adding a stack.** The corpus is PHP and Python. Adding a third stack means mining that stack's own review log the same way, preferring categories that recurred across files and dates, and appending entries with the same shape. The harness reads `stack` and `target_ext` and needs no change.

## Deferred

**No baseline has been recorded yet.** Acceptance criterion #4 on the tracking task ("baseline run recorded against two project review skills") is not met by the corpus, the harness or this runbook. A baseline needs a full multi-agent review run per project, which is a long job and belongs to whoever is running the optimizer, not to the session that built the measurement. The five steps above are what that run is.
