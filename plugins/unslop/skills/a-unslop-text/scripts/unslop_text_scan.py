#!/usr/bin/env python3
"""
unslop_text_scan.py - scan prose for configured style violations and advisory patterns.

This implementation and references/tells.md are two views of the same policy. A mismatch
is a defect, not a reason for one to silently override the other. Plain Python, standard
library only.

Forked (MIT) from github.com/JCarterJohnson/vibecoded-design-tells (unslop-text). The
scanning machinery (quote/code-span skipping, density weighting, severity floor, JSON
mode, exit-code gating) is upstream's; the RULES are this skill's own merge.

What it can and cannot see. Mechanical style rules live here: the dash rule, high-signal
phrases, plain-word vocabulary, and formatting tics. A regex cannot judge authorship,
originality, factual value, rhythm, or whether a paragraph earns its space. Those need
the structural pass in references/tells.md.

How it reads a file. It lints YOUR running prose. A quoted line (starts with > or sits
inside "double quotes") and a literal example (inside `backticks` or a fenced block) is
skipped, because flagging a cliche you are quoting in order to discuss it would be wrong.
The one exception is the em dash, flagged everywhere, because the rule is simply not to
ship one.

Escape hatch. A line containing  unslop-ignore  OR  voice-allow  is skipped, for a tell
used on purpose (a verbatim citation, a section name, a deliberate register). The
voice-allow token matches the  <!-- voice-allow: reason -->  comment style some docs
already use, so those need no rewrite.

Usage:
    python3 unslop_text_scan.py <path>                 # scan a file or dir
    python3 unslop_text_scan.py <path> --severity high # only the hard bans (gated tier)
    python3 unslop_text_scan.py <path> --json          # machine-readable (for CI)
    python3 unslop_text_scan.py <path> --max 8         # cap examples shown per rule
    python3 unslop_text_scan.py --compare ORIGINAL REWRITE # advisory meaning check

Exit code is 1 when any HIGH-severity finding exists, 0 when none exists, and 2 for invalid
input. A boolean failure avoids shell exit-code wraparound on files with many findings.
"""
import os, re, sys, json, argparse
from bisect import bisect_right
from html.parser import HTMLParser

EXTS = {".md", ".markdown", ".mdx", ".txt", ".text", ".rst", ".html", ".htm"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "vendor",
             "coverage", "__pycache__", ".venv", "venv"}
W = {"high": 3, "medium": 2, "low": 1}

EMOJI = ("\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF"
         "\U00002190-\U000021FF\U00002B00-\U00002BFF\U0000FE00-\U0000FE0F\U00002764")

# Each rule has an id, label, default severity, note, fix, and patterns. Optional
# min_hits, window_words, distinct, and consecutive fields adjust local grouping
# without copying patterns. HIGH gates the exit code. MEDIUM and LOW are advisory.
# The dash rule is raw=True because it also covers quoted text.
RULES = [
    # ---------- HIGH: gated violations ----------
    {"id": "em-dash", "label": "Em dash or en dash (hard ban, anywhere)", "sev": "high",
     "note": "configured house preference", "raw": True,
     "fix": "Cut it. Use a comma, a period, or parentheses. Use a colon when the sentence calls for one.",
     "pats": [r"\u2014", r"\u2013", r"&mdash;", r"&ndash;"]},
    {"id": "high-signal-vocab", "label": "High-signal generic or consultant diction", "sev": "high",
     "note": "configured high-signal pattern",
     "fix": "Use the plain word or state the concrete behavior. See the high-signal table in tells.md.",
     "pats": [r"\b(dives? in(to)?|let'?s dive|diving in|dive deep(er)?( into)?)\b",
              r"\bsynerg(y|ies|istic)\b",
              r"\bholistic(ally)?\b", r"\bcutting[- ]?edge\b", r"\bgame[- ]?chang(er|ers|ing)\b",
              r"\bunleash(es|ing|ed)?\b", r"\bbest[- ]?in[- ]?class\b",
              r"\b(?:let'?s\s+unpack(?:\s+(?:this|that|the (?:topic|issue|idea|question|concept|complexity|details?)))?|unpack\s+(?:this|that|the (?:topic|issue|idea|question|concept|complexity|details?)))\b"]},
    {"id": "era-vocab", "label": "Earlier-era vocabulary (contextual advisory)", "sev": "medium",
     "note": "earlier-era advisory; literal senses pass",
     "fix": "Use the plain word for figurative filler. Keep a literal or technical term when it names the thing.",
     "pats": [r"\bdelv(e|es|ing|ed)\b", r"\bparadigm(s|atic)?\b", r"\brealm\b",
              r"\btapestr(y|ies)\b", r"\bbeacon\b", r"\btestament\b", r"\bmyriad\b", r"\bplethora\b"]},
    {"id": "house-vocab", "label": "Plain-word house vocabulary", "sev": "medium",
     "min_hits": 2, "window_words": 300,
     "note": "one use passes; two or more within 300 words are advisory",
     "fix": "Prefer the plain word or describe the behavior. One register-appropriate use is not an authorship signal.",
     "pats": [r"\bleverag(e|es|ing|ed)\b", r"\butili[sz](e|es|ing|ed|ation|ate)\b",
              r"\brobust\b", r"\bcomprehensive\b", r"\bseamless(ly)?\b",
              r"\bstreamlin(e|es|ing|ed)\b", r"\bfoster(s|ing|ed)?\b",
              r"\bempower(s|ing|ed|ment)?\b", r"\bunlock(?:s|ed|ing)?\s+(?:(?:your|our|their|the|its|new|full|true|hidden|untapped)\s+){0,3}(?:potential|possibilit(?:y|ies)|opportunit(?:y|ies)|growth|success|creativity|productivity|value)\b",
              r"\belevat(e|es|ing|ed)\b"]},
    {"id": "consultant-compound", "label": "Contextual consultant-speak compound", "sev": "high",
     "note": "phrase-level rule; the same words used literally pass",
     "fix": "Name the competitors, the decision, the products, or the relationship instead of the consultant phrase. 'the competitive landscape' is 'who we compete with'.",
     "pats": [r"\b(competitive|regulatory|market|vendor|technology|business) landscape\b",
              r"\bnavigate the (complexity|complexities|landscape)\b",
              r"\b(product|partner|partnership|technology|developer) ecosystem\b",
              r"\b(strategic|customer|organi[sz]ational) alignment\b"]},
    {"id": "transition-openers", "label": "Stacked connective as a sentence opener (Moreover, Furthermore, Additionally, Consequently, Notably)", "sev": "high",
     "note": "hard ban",
     "fix": "Just start the new sentence. These mean 'extending a thought without a new idea'.",
     "pats": [r"(^|\.\s+|\n)\s*(moreover|furthermore|additionally|consequently|notably)\b"]},
    {"id": "antithesis", "label": "\"not just X, it's Y\" / \"not just X, but Y\" antithesis cadence", "sev": "high",
     "note": "manufactured-profundity cadence",
     "fix": "State the point plainly. If Y is the point, say Y; drop the negation in front.",
     "pats": [r"\b(?:(?:it'?s|it is|that'?s|that is|this is|they'?re|they are)\s+not|isn'?t|not)\s+(?:just|only|merely|simply)\s+[^.?!,;]{1,100},?\s+(?:but\b|(?:it'?s|it is|they'?re|they are)\b)"]},
    {"id": "assistant-boilerplate", "label": "Leftover assistant boilerplate", "sev": "high",
     "note": "the assistant talking; delete",
     "fix": "Delete assistant disclaimers, refusals, and knowledge-cutoff lines.",
     "pats": [r"\bas an?\s+(ai|a\.i\.)\s+(language\s+)?model\b", r"\bas a large language model\b",
              r"\bi (cannot|can'?t|am unable to)\s+(assist|help|fulfil|fulfill|comply|provide)\b",
              r"\bknowledge cut[- ]?off\b", r"\bas of my last (knowledge )?(update|training)\b",
              r"\bi (do not|don'?t) have (personal|the ability|access|feelings|opinions)\b"]},
    {"id": "sycophancy-apology", "label": "Sycophantic opener / apology reflex (\"Great question!\", \"You're absolutely right\", \"I apologize for the confusion\")", "sev": "high",
     "note": "flattery / apology paragraph",
     "fix": "Drop it; open with the point. When wrong, acknowledge in one line and fix. No apology paragraph.",
     "pats": [r"\b(great|good|excellent|that'?s a (great|good))\s+question\b",
              r"(^|[\"'`(]\s*)(certainly|absolutely|sure thing|of course)\s*[!,]",
              r"\bi'?d be (happy|glad|delighted) to\b", r"\bhappy to help\b",
              r"\byou'?re absolutely right\b", r"\bwhat a (great|fascinating|wonderful)\b",
              r"\bi apologi[sz]e for (the|any) (confusion|misunderstanding|mistake)\b",
              r"\b(good|great) catch\b"]},
    {"id": "banned-pattern", "label": "Filler / preamble pattern (\"it's important to note\", \"in today's ...\", \"let me break this down\")", "sev": "high",
     "note": "filler",
     "fix": "Cut the preamble and state the thing. If it's worth noting, just note it.",
     "pats": [r"\bit'?s (important|worth) (to note|noting|mentioning|pointing out)\b",
              r"\b(it'?s |it is )?important to (note|remember|understand|recognize)\b",
              r"\bin today'?s\b", r"\blet me break (this|it) down\b",
              r"\bimagine a world where\b", r"\bpicture this\b",
              r"\bat the end of the day\b", r"\bthat being said\b", r"\bneedless to say\b",
              r"\bwith that in mind\b"]},
    {"id": "bookend-offer", "label": "Bookending / trailing offer (\"I hope this helps\", \"Let me know if ...\", \"Would you like me to\")", "sev": "high",
     "note": "bookend; stop at the last real sentence",
     "fix": "Delete the sign-off and the meta-offer. If the answer is done, stop.",
     "pats": [r"\bi hope this helps\b", r"\bhope (this|it|you'?re) .{0,20}(helps|finds? you well)\b",
              r"\blet me know if you'?d?\s*(like|need|want|have)\b",
              r"\bwould you like me to\b", r"\bis there anything else\b",
              r"\bfeel free to (ask|reach|let me)\b",
              r"\bhappy to answer\b"]},

    {"id": "citation-markup", "label": "Leaked chatbot citation or renderer markup", "sev": "high",
     "note": "tool-output residue; quoted examples still pass",
     "fix": "Delete the markup and restore the real citation. Do not invent a source.",
     "pats": [r"\b(contentReference|oaicite|oai_citation|turn0search\d+|attributableIndex|grok[-_]card|grok_render_citation_card_json|ppl-ai-file-upload)\b",
              r"\[cite:\s*\d+(?:\s*,\s*\d+)*\s*\]", r"\[span_\d+\]\(start_span\)"]},

    # ---------- MEDIUM: use sparingly / formatting tic (advisory) ----------
    {"id": "frequency-words", "label": "Frequency-sensitive word cluster", "sev": "medium",
     "min_hits": 2, "window_words": 300,
     "note": "one passes; two or more within 300 words are advisory",
     "fix": "Review the local cluster. crucial/vital/essential->important or describe the stakes; essentially/fundamentally->cut; various->name them.",
     "pats": [r"\bcrucial(ly)?\b", r"\bvital(ly)?\b", r"\bessential(ly)?\b", r"\bfundamental(ly)?\b",
              r"\bvarious\b", r"\bversatile\b", r"\bsignificant(ly)?\b", r"\bgenuinely\b",
              r"\bnuanc(e|es|ed)\b", r"\bmeticulous(ly)?\b", r"\bshowcas(e|es|ing|ed)\b",
              r"\bstraightforward\b", r"\bprecisely\b", r"\bdramatically\b", r"\bincredibly\b",
              r"\bparticularly\b", r"\bultimately\b"]},
    {"id": "current-era-cluster", "label": "Mid-2026 vocabulary cluster", "sev": "medium",
     "min_hits": 3, "window_words": 300, "distinct": True,
     "note": "three distinct terms in 300 words; moderate evidence from a review blog cited by Wikipedia",
     "fix": "Read the passage for generic phrasing. Keep ordinary words that do real work.",
     "pats": [r"\b(challenge|clearer|dependable|echoed|foster|leverage|matters|multifaceted|practical|prioritize|quietly|steady|universally)\b"]},
    {"id": "staged-reveal", "label": "Staged reveal", "sev": "medium",
     "note": "routine claim presented as a revelation",
     "fix": "State the result or answer directly; keep a real question when the reader needs it.",
     "pats": [r"(^|[.?!]\s+)\s*the (result|catch|kicker|payoff|twist|answer|truth)[?:]"]},
    {"id": "significance-tail", "label": "Unsupported significance tail", "sev": "medium",
     "note": "check whether the source supports the attached inference",
     "fix": "Delete the tail unless it adds a supported relationship or fact.",
     "pats": [r",\s+(highlighting|underscoring|reflecting|symbolizing|showcasing|emphasizing)\s+(the|its|their|a)\b"]},
    {"id": "bolded-label-list", "label": "Consecutive bolded-label bullets", "sev": "low",
     "consecutive": 3,
     "note": "three or more consecutive Markdown items with bolded labels",
     "fix": "Check whether the labels help scanning. Remove them when they split prose into artificial mini-sections.",
     "pats": [r"^\s*(?:[-*+]\s+|\d+\.\s+)\*\*[^*\n]{2,40}(?::\*\*\s|\*\*\s*:\s)"]},
    {"id": "softener", "label": "Softener (\"simply\" / \"just\" before a verb) that undercuts the instruction", "sev": "medium",
     "note": "softener",
     "fix": "Drop it. 'Simply run X' is 'Run X'. The word adds nothing and implies it is trivial.",
     "pats": [r"\bsimply\s+(run|use|add|do|call|set|click|open|type|install|copy|edit|change)\b",
              r"\bjust\s+(run|use|add|do|call|set|click|open|type|install|copy)\b"]},
    {"id": "bolded-lead-in", "label": "Bolded lead-in label (**Word:** then a sentence)", "sev": "medium",
     "note": "chat-formatting tic", "skip_list": True,
     "fix": "Write a normal sentence without the boldface label. Reserve bold for true terms of art or warnings. (One or two bolded-label bullets pass; runs of three get a separate advisory.)",
     "pats": [r"(^|\s)\*\*[^*\n]{2,40}:\*\*\s", r"(^|\s)\*\*[^*\n]{2,40}\*\*\s*:"]},
    {"id": "listicle-scaffold", "label": "Listicle scaffolding (\"5 ways to ...\", \"7 signs ...\")", "sev": "medium",
     "note": "list-as-default-shape",
     "fix": "Write prose. Reserve bullets for genuinely list-like content.",
     # High-signal nouns (ways/tips/signs/...) match anywhere. Ambiguous count-nouns
     # (things/steps/rules) also appear in plain prose ("15 rules files", "3 steps in the
     # pipeline"), so they only flag in a heading or before a listicle continuation word.
     # This kills the "N rules"/"N things" false positive without missing real listicles.
     "pats": [r"\b\d+\s+(ways|tips|signs|reasons|tricks|secrets|lessons|mistakes)\b",
              r"(^|\n)\s{0,3}#{1,4}\s+\d+\s+(ways|tips|signs|reasons|things|steps|tricks|secrets|lessons|mistakes|rules)\b",
              r"\b\d+\s+(things|steps|rules)\s+(to|for|that|you|your|why|i|we|every)\b"]},
    {"id": "emoji-decoration", "label": "Emoji as a bullet, icon, or in a heading", "sev": "medium",
     "note": "decorative emoji (banned unless the user used them first)",
     "fix": "Use plain headers and real list markers. An emoji in a sentence where a person would use one is fine; emoji as structure is not.",
     "pats": [r"^\s{0,3}#{1,6}\s*[" + EMOJI + r"]", r"^\s{0,3}[" + EMOJI + r"]\s+\S",
              r"[" + EMOJI + r"]\s*\*\*", r"\*\*\s*[" + EMOJI + r"]"]},
    {"id": "in-conclusion", "label": "\"In conclusion\" / \"in summary\" / \"to summarize\" closer", "sev": "medium",
     "note": "signposted recap",
     "fix": "End on a real last point. If the reader needs a summary, the piece is too long.",
     "pats": [r"\bin (conclusion|summary)\b", r"\bto (summari[sz]e|conclude|wrap (this |it )?up)\b", r"\bin closing\b"]},
    {"id": "hedge", "label": "Hedging when you have a view (\"you might want to consider\", \"it may be worth\", \"perhaps\", \"on one hand ... on the other\")", "sev": "medium",
     "note": "hedge; take a position",
     "fix": "State the take. List a real trade-off if it matters, but say what you would do.",
     "pats": [r"\byou might want to consider\b", r"\byou could potentially\b",
              r"\bit may be worth\b", r"\bperhaps you\b",
              r"\bon (the )?one hand\b[^.\n]{0,120}\bon the other\b", r"\bit (really )?depends\b"]},
    {"id": "social-template", "label": "Worn social-post template (\"the guide I wish existed\", \"I kept seeing X, so I built Y\")", "sev": "medium",
     "note": "Reddit/HN launch-post cliche; review especially closely in short outreach copy",
     "fix": "Say what the thing is and what it covers. The origin story ('I saw a gap, so I made this') is the most-reused launch template on the internet; cut it.",
     "pats": [r"\bi wish existed\b", r"\bwish i('d| had) (had|found)\b",
              r"\bi kept (seeing|getting|hearing)\b[^.?!\n]{0,80}\bso i\b",
              r"\bi (saw|noticed|found) (a |the )?(gap|problem|need)\b[^.?!\n]{0,80}\bso i (built|made|created|wrote)\b"]},
    {"id": "split-antithesis", "label": "Cross-sentence antithesis (\"The value was not X. It was Y.\" / \"not the X part. The X was ...\")", "sev": "medium",
     "note": "the not-X-but-Y cadence split over two sentences; the one-sentence form is the high-tier 'antithesis' check",
     "fix": "Say Y directly and drop the negated setup sentence.",
     "pats": [r"\b(was|is|were|are)(n'?t| not)\s+[^.?!\n]{2,50}\.\s+(it|that|this)\s+(was|is|'s)\b",
              r"\bnot the ([a-z][a-z ]{2,30}?)\.\s+the \1\b"]},
    {"id": "hype-marketing", "label": "Marketing hype (revolutionary, transformative, supercharge, to the next level)", "sev": "medium",
     "note": "landing-page voice",
     "fix": "Say what the thing literally does, with a specific. Strip the promotional adjective.",
     "pats": [r"\brevolution(ary|i[sz]e)\b", r"\btransform(ative)\b", r"\btransform your (life|business|workflow)\b",
              r"\bto the next level\b", r"\bsupercharge\b", r"\bsay goodbye to\b", r"\blook no further\b"]},
    {"id": "c2-flourish", "label": "Literary/native flourish (whilst, endeavour, notwithstanding: check it against the byline)", "sev": "medium",
     "note": "byline mismatch; see references/voice-profile.md",
     "fix": "Use the everyday word: whilst->while, amongst->among, endeavour->try, ascertain->find out, notwithstanding->even so. If the named author's real register is plainer than this vocabulary (a non-native writer, a terse operator), the polish itself is the tell.",
     "pats": [r"\bwhilst\b", r"\bamongst\b", r"\bendeavou?r(s|ed|ing)?\b", r"\bascertain(s|ed|ing)?\b",
              r"\belucidat(e|es|ed|ing)\b", r"\bquintessential(ly)?\b", r"\bnotwithstanding\b",
              r"\bhenceforth\b", r"\bhitherto\b", r"\bwhereby\b", r"\bthereby\b", r"\bwherein\b",
              r"\balbeit\b", r"\bone might\b"]},

    # ---------- LOW: weak / contextual (advisory) ----------
    {"id": "copula-avoidance", "label": "Copula avoidance", "sev": "low",
     "note": "weak contextual advisory; a real function may justify the phrase",
     "fix": "Use is or are when the phrase only renames the subject.",
     "pats": [r"\b(serves|stands) as (a|an|the)\b"]},
    {"id": "generic-diction", "label": "Inflated generic diction (facilitate, paramount, pivotal, intricacies)", "sev": "low",
     "note": "prefer the plain word",
     "fix": "facilitate->help/let, paramount->matters most, pivotal->describe the moment.",
     "pats": [r"\bfacilitat(e|es|ing|ed)\b", r"\bparamount\b", r"\bpivotal\b",
              r"\bintricac(y|ies)\b"]},
    {"id": "preamble", "label": "Work-announcement preamble (\"Let me ...\", \"I'll start by ...\", \"Here's what I ...\")", "sev": "low",
     "note": "narrating intent; just do it",
     "fix": "Do the thing. The reader sees the result. No 'Let me take a look', no 'Here's a breakdown of'.",
     "pats": [r"(^|\n)\s*let me (take a look|start|check|see|explain|walk you)\b",
              r"(^|\n)\s*i'?ll (start by|begin by|go ahead)\b",
              r"(^|\n)\s*here'?s (a breakdown|what i (found|changed|did))\b"]},
    {"id": "honestly-opener", "label": "Fake-relatability opener (\"Honestly, ...\", \"Look, I get it\")", "sev": "low",
     "note": "throat-clearing",
     "fix": "Cut it and start with the point.",
     "pats": [r"(^|\n)\s*honestly,\s", r"\blook,\s+i (get it|know)\b", r"\blet'?s be (honest|real)\b"]},
]

def compile_rules(min_sev):
    order = ["high", "medium", "low"]
    floor = order.index(min_sev) if min_sev else len(order) - 1
    out = []
    for r in RULES:
        if order.index(r["sev"]) > floor:
            continue
        r = dict(r)
        r["min_hits"] = r.get("min_hits", 1)
        r["rx"] = [re.compile(p, re.IGNORECASE) for p in r["pats"]]
        out.append(r)
    return out

def iter_files(path):
    if os.path.isfile(path):
        yield path; return
    for root, dirs, files in os.walk(path):
        parts = os.path.normpath(os.path.abspath(root)).split(os.sep)
        under_test = any(part in {"test", "tests"} for part in parts)
        if any(part == "fixtures" and any(p in {"test", "tests"} for p in parts[:i])
               for i, part in enumerate(parts)):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not (under_test and d == "fixtures")]
        for f in files:
            if os.path.splitext(f)[1].lower() in EXTS:
                yield os.path.join(root, f)

def strip_noise(line, in_code, in_quote):
    """Blank what the author is quoting or showing as a literal example, so the prose
    rules lint the author's own sentences. Inline-code spans (backticks) and double-quoted
    spans are removed, and the open/closed state carries across lines. State resets at every
    blank line, so an unbalanced quote can never swallow more than one paragraph."""
    out = []
    for ch in line:
        if in_code:
            if ch == "`":
                in_code = False
            out.append(" ")
        elif ch == "`":
            in_code = True
            out.append(" ")
        elif ch in "\"“”":
            in_quote = not in_quote
            out.append(" ")
        else:
            out.append(" " if in_quote else ch)
    return "".join(out), in_code, in_quote

def literal_vocab(target, match):
    """Narrow literal/technical exceptions, not a semantic classifier."""
    word = match.group(0).lower()
    before = target[max(0, match.start() - 70):match.start()].lower()
    after = target[match.end():match.end() + 70].lower()
    if word.startswith("tapestr"):
        if re.search(r"\brich\s+$", before) or re.match(r"\s+(?:of\s+(?:ideas|stories|cultures|experiences|life)|celebrating)\b", after):
            return False
        return bool(re.search(r"\b(?:woven|hand(?:woven)?|silk|wool|medieval|bought|restored)(?:\s+a)?\s+$", before)
                    or re.match(r"\s+(?:hangs?|hung|on the wall|from (?:iran|persia))\b", after)
                    or re.match(r"\s+of\b[^.?!]{0,45}\b(?:covers|hangs on) the wall\b", after))
    if word.startswith("paradigm"):
        return bool(re.search(r"\b(programming|computing|software|scientific|functional|object[- ]oriented|dataflow|logic|imperative|declarative)\s+$", before))
    if word == "beacon":
        return bool(re.search(r"\b(radio|bluetooth|emergency|distress|navigation|homing|lighthouse|gps)\s+$", before)
                    or re.match(r"\s+(flashes|flashed|transmits|transmitted)\b", after))
    if word == "realm":
        return bool(re.search(r"\b(kerberos|dns|authentication)\s+$", before))
    if word == "testament":
        return bool(re.search(r"\b(old|new)\s+$", before))
    return False

def eligible_findings(findings, rules):
    groups = {}
    for finding in findings:
        groups.setdefault((finding["file"], finding["rule"]), []).append(finding)
    policy = {r["id"]: r for r in rules}
    keep = set()
    for (_, rid), items in groups.items():
        rule = policy[rid]
        if rule.get("consecutive"):
            start = 0
            for end in range(1, len(items) + 1):
                if end < len(items) and items[end]["_item"] == items[end - 1]["_item"] + 1:
                    continue
                if end - start >= rule["consecutive"]:
                    keep.update(id(f) for f in items[start:end])
                start = end
        elif rule["min_hits"] > 1:
            end = 0
            for start, first in enumerate(items):
                while end < len(items) and items[end]["_word"] - first["_word"] < rule["window_words"]:
                    end += 1
                window = items[start:end]
                count = len({f["match"].lower() for f in window}) if rule.get("distinct") else len(window)
                if count >= rule["min_hits"]:
                    keep.update(id(f) for f in window)
        else:
            keep.update(id(f) for f in items)
    return [{k: v for k, v in f.items() if not k.startswith("_")} for f in findings if id(f) in keep]

class ProseHTML(HTMLParser):
    """Mask tags and script/style bodies without moving source characters."""
    def __init__(self, text):
        super().__init__(convert_charrefs=False)
        self.source = text
        self.output = list(text)
        self.citations = list(text)
        self.starts = [0] + [m.end() for m in re.finditer("\n", text)]
        self.hidden = None
        self.feed(text)
        self.close()

    def mask(self, length, boundary=False, keep_citation=False):
        row, column = self.getpos()
        start = self.starts[row - 1] + column
        for i in range(start, start + length):
            if self.output[i] != "\n":
                self.output[i] = " "
            if not keep_citation:
                self.citations[i] = self.output[i]
        if boundary and length:
            self.output[start] = "\n"

    def handle_starttag(self, tag, attrs):
        self.mask(len(self.get_starttag_text()), tag in {"p", "div", "br", "li", "h1", "h2", "h3"}, tag == "grok-card")
        if tag in {"script", "style"}:
            self.hidden = tag

    def handle_endtag(self, tag):
        row, column = self.getpos()
        start = self.starts[row - 1] + column
        end = self.source.find(">", start)
        self.mask(end - start + 1, tag in {"p", "div", "li"}, tag == "grok-card")
        if tag == self.hidden:
            self.hidden = None

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag == self.hidden:
            self.hidden = None

    def handle_data(self, data):
        if self.hidden:
            self.mask(len(data))

    def handle_comment(self, data):
        self.mask(len(data) + 7)


def strip_code(line, in_code):
    out = []
    for ch in line:
        if ch == "`":
            in_code = not in_code
            out.append(" ")
        else:
            out.append(" " if in_code else ch)
    return "".join(out), in_code


def citation_prose(line, in_code, in_quote):
    """Keep JSON citation keys, but retain ordinary quote and code escapes."""
    code_free, _ = strip_code(line, in_code)
    protected = list(line)
    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", code_free):
        _, _, quoted = strip_noise(line[:match.start()], in_code, in_quote)
        if quoted:
            continue
        try:
            _, length = decoder.raw_decode(code_free[match.start():])
        except ValueError:
            continue
        for i in range(match.start(), match.start() + length):
            if protected[i] == '"':
                protected[i] = " "
    return strip_noise("".join(protected), in_code, in_quote)[0]


def scan(path, min_sev):
    rules = compile_rules(min_sev)
    line_rules = {"bolded-label-list", "bolded-lead-in", "emoji-decoration", "preamble",
                  "honestly-opener", "transition-openers", "listicle-scaffold"}
    findings = []
    total_words = 0
    for fp in iter_files(path):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                source = fh.read()
        except OSError:
            continue
        raw_lines = source.splitlines()
        starts = [0] + [m.end() for m in re.finditer("\n", source)]
        html = ProseHTML(source)
        markup = "".join(html.output)
        citation_markup = "".join(html.citations)
        # splitlines() would treat inserted HTML boundaries as extra source lines.
        lines = [markup[start:starts[i + 1] if i + 1 < len(starts) else len(markup)]
                 for i, start in enumerate(starts)]
        fm_end = 0
        if raw_lines and raw_lines[0].strip() == "---":
            for j in range(1, len(raw_lines)):
                if raw_lines[j].strip() == "---":
                    fm_end = j + 1
                    break
        in_fence = in_code = in_quote = False
        paragraph = []
        item = 0
        list_indent = None

        def emit(rule, target, mapping, is_list=False, item_number=0):
            if rule.get("skip_list") and is_list:
                return
            matches = {}
            for rx in rule["rx"]:
                for m in rx.finditer(target):
                    if rule["id"] == "era-vocab" and literal_vocab(target, m):
                        continue
                    matches[(m.start(), m.end(), m.group(0))] = m
            for _, m in sorted(matches.items()):
                position = m.start() + len(m.group(0)) - len(m.group(0).lstrip(" .?!\n\t"))
                line = mapping[min(position, len(mapping) - 1)]
                findings.append({"rule": rule["id"], "label": rule["label"], "sev": rule["sev"],
                                 "note": rule["note"], "fix": rule["fix"], "file": fp, "line": line,
                                 "match": m.group(0).strip()[:60], "snippet": raw_lines[line - 1].strip()[:160],
                                 "_word": total_words + len(re.findall(r"\b[\w'-]+\b", target[:m.start()])),
                                 "_item": item_number})

        def flush():
            nonlocal total_words
            if not paragraph:
                return
            text = "".join(part[0] for part in paragraph)
            text = re.sub(r"(?<!\w)(\*\*|__|\*|_)(?=\S)(.+?)(?<=\S)\1(?!\w)",
                          lambda m: " " * len(m[1]) + m[2] + " " * len(m[1]), text)
            mapping = [line for part, line, _ in paragraph for _ in part]
            normalized, normalized_map = [], []
            for m in re.finditer(r"\s+|\S+", text):
                chunk = " " if m.group().isspace() else m.group().replace("’", "'")
                normalized.extend(chunk)
                normalized_map.extend([mapping[m.start()]] if m.group().isspace() else mapping[m.start():m.end()])
            text = "".join(normalized)
            for rule in rules:
                if not rule.get("raw") and rule["id"] not in line_rules | {"citation-markup"}:
                    emit(rule, text, normalized_map, paragraph[0][2])
            total_words += len(re.findall(r"\b[\w'-]+\b", text))
            paragraph.clear()

        for i, (raw, visible) in enumerate(zip(raw_lines, lines), 1):
            if i <= fm_end:
                continue
            stripped = raw.strip()
            if not stripped:
                flush()
                in_code = in_quote = False
                continue
            if stripped.startswith(("```", "~~~")):
                flush()
                item += 1
                in_fence = not in_fence
                in_code = in_quote = False
                continue
            if in_fence:
                continue
            bullet = re.match(r"^(\s*)(?:[-*+]\s+|\d+\.\s+)", raw)
            if bullet:
                flush()
                item += 1
                list_indent = len(bullet.group(0))
            elif stripped and (list_indent is None or len(raw) - len(raw.lstrip()) < list_indent):
                item += 1
                list_indent = None
            if "unslop-ignore" in raw.lower() or "voice-allow" in raw.lower():
                flush()
                _, in_code, in_quote = strip_noise(visible, in_code, in_quote)
                continue
            is_quote = stripped.startswith(">")
            for rule in rules:
                if rule.get("raw"):
                    emit(rule, raw, [i] * len(raw))
                elif rule["id"] == "citation-markup" and not is_quote:
                    start = starts[i - 1]
                    citation_line = citation_markup[start:starts[i] if i < len(starts) else len(source)]
                    emit(rule, citation_prose(citation_line, in_code, in_quote), [i] * len(citation_line))
            prose, in_code, in_quote = strip_noise(visible, in_code, in_quote)
            if is_quote:
                flush()
                continue
            for rule in rules:
                if rule["id"] in line_rules:
                    normalized_line = re.sub(r"[ \t]+", " ", prose).replace("’", "'")
                    emit(rule, normalized_line, [i] * len(normalized_line), bool(bullet), item)
            if bullet:
                prose = " " * bullet.end() + prose[bullet.end():]
            prose = re.sub(r"^(\s{0,3})#{1,6}\s+", lambda m: " " * len(m[0]), prose)
            # A source newline is a soft wrap; inserted HTML newlines are boundaries.
            if prose.endswith("\n"):
                prose = prose[:-1]
            parts = prose.split("\n")
            for index, part in enumerate(parts):
                if part.strip():
                    paragraph.append((part + " ", i, bool(bullet)))
                if index < len(parts) - 1:
                    flush()
        flush()
    return eligible_findings(findings, rules), total_words

def density(weighted, words):
    return weighted / max(words, 1) * 1000.0

def verdict(by_sev, weighted, words):
    hi, med = by_sev.get("high", 0), by_sev.get("medium", 0)
    if weighted == 0:
        return "Clean under the configured rules"
    dens = density(weighted, words)
    if hi == 0 and med == 0:
        return "Mostly clean, minor style advisories"
    if hi >= 3 or weighted >= 15 or (words >= 300 and dens >= 10):
        return "High concentration of configured style violations"
    if hi >= 1:
        return "Configured style violations present"
    if weighted >= 6 and not (words >= 600 and dens < 2.0):
        return "Several advisory style patterns present"
    return "Mostly clean, minor style advisories"

def compare_text(original, rewrite):
    """Advisory token inventories. A human still checks meaning and attribution."""
    from collections import Counter
    patterns = {
        "numbers": r"(?<![\w.])[+-]?(?:\d+(?:[.,]\d+)*|\.\d+)(?:[eE][+-]?\d+)?%?",
        "URLs": r"https?://[^\s<>\"\[\]]+",
        "negations": r"\b(?:cannot|not|never|no|\w+n['’]t)\b",
        "modals": r"\b(?:can(?!['’]t\b)|must|should|may)\b",
    }
    texts = []
    for path in (original, rewrite):
        with open(path, encoding="utf-8") as fh:
            texts.append(fh.read())
    def clean_url(token):
        token = token.rstrip(".,;:!?")
        while token.endswith(")") and token.count(")") > token.count("("):
            token = token[:-1].rstrip(".,;:!?")
        return token

    differences = []
    for label, pattern in patterns.items():
        inventories = [Counter(token.lower().replace("’", "'") if label in ("negations", "modals") else
                               clean_url(token) if label == "URLs" else token
                               for token in re.findall(pattern, text, re.IGNORECASE)) for text in texts]
        for side, left, right in (("original", 0, 1), ("rewrite", 1, 0)):
            for token, count in sorted((inventories[left] - inventories[right]).items()):
                differences.append(f"{label} only in {side}: {token} ({count})")
    return differences

def main():
    ap = argparse.ArgumentParser(description="Scan prose against the configured writing-style rules.")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--compare", nargs=2, metavar=("ORIGINAL", "REWRITE"),
                    help="advisory numbers/URLs/negations/modals comparison (exit 0)")
    ap.add_argument("--severity", choices=["high", "medium", "low"], default="low",
                    help="minimum severity to report (default: low = everything)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max", type=int, default=10, help="max examples shown per rule (text mode)")
    args = ap.parse_args()

    if args.compare:
        if args.path or args.json:
            ap.error("--compare takes two files and cannot be combined with path or --json")
        try:
            differences = compare_text(*args.compare)
        except (OSError, UnicodeError) as exc:
            ap.error(str(exc))
        print("Meaning-check advisory: token inventories only; verify facts and meaning by hand.")
        print("\n".join(differences) if differences else "No token inventory differences found.")
        return
    if not args.path:
        ap.error("path is required unless --compare is used")
    if not os.path.exists(args.path):
        print(f"path not found: {args.path}", file=sys.stderr); sys.exit(2)

    findings, total_words = scan(args.path, args.severity)
    by_sev, by_rule = {}, {}
    for f in findings:
        by_sev[f["sev"]] = by_sev.get(f["sev"], 0) + 1
        by_rule.setdefault(f["rule"], []).append(f)
    weighted = sum(W[s] * n for s, n in by_sev.items())
    files_scanned = sum(1 for _ in iter_files(args.path))
    dens = round(density(weighted, total_words), 1)

    if args.json:
        print(json.dumps({"path": args.path, "files_scanned": files_scanned,
                          "words": total_words, "counts": by_sev,
                          "configured_style_score": weighted,
                          "density_per_1k_words": dens,
                          "verdict": verdict(by_sev, weighted, total_words),
                          "findings": findings}, indent=2))
        sys.exit(1 if by_sev.get("high", 0) else 0)

    sev_order = {"high": 0, "medium": 1, "low": 2}
    rule_ids = sorted(by_rule, key=lambda rid: (sev_order[by_rule[rid][0]["sev"]], -len(by_rule[rid])))
    print(f"\n  unslop-text scan: {args.path}")
    print(f"  files scanned: {files_scanned}   words: {total_words}   findings: {len(findings)}")
    print(f"  configured style score: {weighted}   density: {dens}/1k authored words")
    print(f"  verdict: {verdict(by_sev, weighted, total_words)}")
    print(f"  high: {by_sev.get('high',0)}   medium: {by_sev.get('medium',0)}   low: {by_sev.get('low',0)}")
    print("  (high is the gated tier; medium/low are advisory)\n")
    if not findings:
        print("  Nothing flagged. The scanner cannot judge authorship, rhythm, originality,\n"
              "  factual value, or whether each paragraph earns its space. Run the structural\n"
              "  and concision pass in references/tells.md.\n")
        return
    for rid in rule_ids:
        items = by_rule[rid]
        f0 = items[0]
        print(f"  [{f0['sev'].upper()}] {f0['label']}  ({len(items)} hit{'s' if len(items)!=1 else ''})  [{f0['note']}]")
        print(f"        fix: {f0['fix']}")
        for it in items[:args.max]:
            print(f"        {it['file']}:{it['line']}  ({it['match']})  {it['snippet']}")
        if len(items) > args.max:
            print(f"        ... +{len(items) - args.max} more")
        print()
    top = [by_rule[rid][0]['label'] for rid in rule_ids[:3]]
    print("  Top things to change: " + "; ".join(top))
    print("  Rhythm, substance, factual value, and authorship need a human pass. See references/tells.md.\n")
    sys.exit(1 if by_sev.get("high", 0) else 0)

if __name__ == "__main__":
    main()
