# sanitize-public changelog

## 1.2.1

Clearer name, description and keywords for the plugin directory. The README now opens by saying plainly what the plugin does and for whom, and its privacy section separates what the plugin does from how Claude itself handles your conversation. Skill descriptions reworded for accuracy; no behaviour changes.

## 1.2.0

A new `publish_gate.sh` runs every mechanical check in one command: the tree you are about to push, every blob and commit message reachable from it, the author email on each commit, gitleaks as a second opinion, and a list of binaries to open by hand. Use `--also` for anything else that ships, such as an unzipped download bundle.

Private terms now match inside code. The scanner splits `BenchFooPanel` and `foo_bar` into words before applying your private rules, and the docs show how to write a rule that matches every spelling of a name.

The history sweep extracts every blob once instead of running `git log -S` per term, which never finished against a large private layer. The method also gained the author-identity check and the binary review.

## 1.1.2

The public guidance now makes the artifact-first gate and the history sweep clearer.

## 1.1.1

The README now says which command you get after installing.

## 1.1.0

The skills in this plugin now carry an `agents/openai.yaml` sidecar, so they show up in Codex's skill picker with a proper name and one-line description instead of a raw folder name. It stays implicitly invocable, so Codex can reach for it when a publish is near.

## Earlier

Versions before this predate this file. See the git history at https://github.com/imisic/claude-marketplace.
