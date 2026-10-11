# Why the since-last-review scope exists

This note keeps the history behind the scope rule in `SKILL.md` §1, so the rule itself stays short.

Commits that land between reviews, above all the fix commit for a finding the previous run reported, used to be read by nothing. On 2026-10-11 three real bugs sat in such a follow-up fix commit in one repository, and only the built-in `/code-review` over a time range found them. The since-last-review scope closes that gap.

It has one known limit, also observed on 2026-10-11: a run against the commit the previous review had missed read only the follow-up commits, exactly as specified, and so could not see two bugs in files those commits did not touch (a timestamp compared as text, and input compared without stripping its BOM). That is why the rule sends untouched files to the dimensions and grep-able pitfalls to the project's preflight checks, rather than widening this scope.
