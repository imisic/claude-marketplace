---
name: commit
description: Check for secrets and unwanted files, then commit the selected changes with a Conventional Commits message.
disable-model-invocation: true
---

# Git Commit

Create a clean, well-structured commit. Generic across stacks; add your own project-specific sensitive paths and commit conventions on top of the checks below.

## Phase 1: Pre-flight Checks

Run these in parallel to assess the working tree:

```bash
git status
git diff --stat
git log --oneline -5
```

Never use `git status -uall` on a large repo. It can exhaust memory scanning untracked files.

### Sensitive File Scan

Scan the diff and untracked files for:

- `.env` files, `*.pem`, `*.key`, credential files, private keys, API secrets
- Hardcoded secrets or tokens in the diff itself (`key = "..."`, `password = "..."`, connection strings with embedded credentials)
- Scratch/experiment directories that shouldn't ship (`_debug/`, `_test/`, or whatever your project uses for throwaway work)

Tell the user to extend this list with their own project's sensitive paths (a secrets directory, a local config file, a vendor-specific credentials format). The checks above are a floor, not a ceiling.

### Gating Rules

**BLOCK (stop immediately, show what was found):**
- `.env` files or equivalent in the diff
- `*.pem`, `*.key`, or other credential files
- A literal secret, API key, or private key hardcoded in a tracked file
- Files inside a scratch/experiment directory

**WARN (show the warning, ask to confirm before proceeding):**
- Large, unrelated changes spanning many files (suggest splitting into multiple commits)
- A generated or build artifact changed without its source changing (stale build, or someone hand-edited output)
- Leftover debug logging outside scratch dirs (`console.log`, `print`, `var_dump`, `dd`, or your language's equivalent)

If blocked, explain what was found and stop. Do not stage or commit.

## Phase 2: Analyze Changes

Determine commit type from the diff:

| Type | When |
|-|-|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring, no behavior change |
| `style` | Formatting, whitespace, no logic change |
| `docs` | Documentation only |
| `chore` | Build, config, dependency, maintenance |
| `perf` | Performance improvement, no behavior change |
| `test` | Test-only changes |

Determine scope from which area of the codebase changed (a directory, module, or feature name that makes the subject line legible at a glance).

## Phase 3: Draft Commit Message

Format: `type(scope): subject`

- Subject: imperative mood, 50 characters or less ("add" not "added")
- Body (optional, after a blank line): explains **why**, not what the diff already shows
- Body wraps at a reasonable width, HEREDOC preserves it exactly
- If the user supplied a message, use it but conform it to this format

Good: `fix(auth): reject expired tokens before session lookup`
Bad: `fix: fixed the auth bug that was happening`

## Phase 4: Stage Files

**Never `git add .` or `git add -A`.** Stage files individually by name.

For each candidate file, decide:
- Stage it if it's part of this commit's actual purpose
- Skip unrelated changes (suggest a separate commit)
- Skip generated/build artifacts that should be produced by the build step, not hand-committed
- Skip anything the sensitive-file scan flagged

## Phase 5: Create Commit

Use a HEREDOC so formatting survives shell quoting:

```bash
git commit -m "$(cat <<'EOF'
type(scope): subject line here

Optional body explaining why this change was made.

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

Only add the `Co-Authored-By:` trailer if your workflow wants one, and keep it generic. Do not hardcode a specific session, model version, or author identity into a shipped skill.

## Phase 6: Verify

Run `git status` after the commit to confirm a clean tree or show what's left uncommitted.

## Rules

- Never commit code you know is broken. If unsure, ask.
- Never use `--force` or `--no-verify`.
- Never amend an existing commit unless explicitly asked.
- If a pre-commit hook fails: the commit did not happen, so fix the issue, re-stage, and create a NEW commit. Do not amend (there is nothing to amend yet).
- Never push unless explicitly asked.

## Workflow Chain

After a clean commit, suggest running your project's deploy step if the change looks feature-complete or is a ready bug fix.
