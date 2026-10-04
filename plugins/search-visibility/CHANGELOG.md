# search-visibility changelog

## 1.3.2

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes.

## 1.3.1

Fixes that landed after 1.3.0 was first published went out under the same version number, so an install from that first day never received them: the guided API setup, the native Windows check, and calling the bundled scripts through `${CLAUDE_PLUGIN_ROOT}` so they work from your own project directory. This release carries no new behaviour; the new number is what makes those installs update.

## 1.3.0

`a-seo-gsc` can now pull Search Console data itself instead of asking you to download three zips. `scripts/fetch_gsc.py` authenticates with a Google service account and writes the same CSV shapes the manual export produces, so the parser reads either one and the export route still works unchanged. Setup is in `references/export-guide.md`.

The API is not just less clicking. The UI export caps its query and page tables near a thousand rows where the API returns up to 25,000 top rows per request, it writes a matching previous window so trend analysis runs without you remembering to tick Compare, and it returns page+query pairs. Google still does not guarantee every row through the API.

That last one adds an analysis the skill could not do before. No manual export tells you which of your pages a given query hit, so "which of my own pages compete for this term" was unanswerable. The parser now detects it, and flags the case worth acting on first: where the page Google shows most often is not the one that ranks best.

Coverage and Links still need a manual export. Neither has an API, and the guide now says so rather than leaving you to find out. The URL Inspection API is not a substitute for the coverage report, because it only answers for URLs you hand it and so can never surface index bloat from URLs you never submitted.

The script is standard library only and signs its request with openssl, so there is nothing to pip install. Your key is read from a path you choose and is never written to disk or sent anywhere but Google. Raw exports and arithmetic stay local; Claude receives the parser's findings in the session, and the plugin adds no telemetry.

If you want the API but have not set it up, the skill now walks you through it one step at a time and verifies at the end, rather than handing you a link. It also recognises the two 403s that point somewhere other than where they read: the one that means the API is switched off, and the one that means the service account is not on the property yet.

Installed copies now invoke the bundled fetcher and parser through `${CLAUDE_PLUGIN_ROOT}`, so they work from the customer's project directory instead of depending on the current working directory.

Setup now checks the environment before key creation. The bundled API fetcher needs Python 3 and `openssl` on macOS, Linux, or WSL; native Windows users get the WSL or manual-export choice before setup starts.

Downloading the reports by hand stays a first-class route, not a fallback. The skill opens by asking which one you are on and gives the full export list inline either way. The only thing the download route gives up is the page and query pairing, so that one analysis is skipped rather than reported as clean, and for a small site the API is often not worth setting up to get it.

## 1.2.2

The marketplace and storefront copy now describe AI-search work as an eligibility audit and fix plan, not a promise of citations.

## 1.2.1

The README now says which commands you get after installing, and the GEO acronym is spelled out where it first appears. Four hard-banned words swapped for plain ones in `a-geo-optimizer`'s reference docs.

## 1.2.0

The skills in this plugin now carry an `agents/openai.yaml` sidecar, so they show up in Codex's skill picker with a proper name and one-line description instead of a raw folder name. `a-seo-gsc` is explicit-only in Codex, `a-geo-optimizer` is not, matching how each behaves in Claude Code.

## 1.1.0

The two skills now differ in who can start them, because they are used at opposite moments.

`a-seo-gsc` is yours to invoke only. It is a session you sit down to run once a Search Console export is in hand, and nothing about a conversation tells Claude that has happened.

`a-geo-optimizer` still fires on its own. Its whole value is arriving while a page is being built, before anyone thinks to ask whether an assistant will be able to quote it.

The README table now names the mode per skill.

## Earlier

1.0.0 predates this file. See the git history at https://github.com/imisic/claude-marketplace.
