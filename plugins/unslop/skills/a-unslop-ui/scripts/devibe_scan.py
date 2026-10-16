#!/usr/bin/env python3
"""
devibe_scan.py - scan a web codebase for "vibe-coded" / AI-generated design tells.

Forked (MIT) from github.com/JCarterJohnson/vibecoded-design-tells.

Plain Python, standard library only. Adapted from the credited Reddit study, with current design guidance added. Severity reflects judged risk and pattern precision, not complaint frequency or a calibrated probability of AI authorship.

Usage:
    python3 devibe_scan.py <path>                 # scan a dir or file
    python3 devibe_scan.py <path> --severity high # only high-signal tells
    python3 devibe_scan.py <path> --json          # machine-readable (for CI)
    python3 devibe_scan.py <path> --max 8         # cap examples shown per rule

Exit code is the number of HIGH-severity findings (0 = none), so CI can gate on it.
"""
import os, re, sys, json, argparse
from html import unescape

EXTS = {".html", ".htm", ".css", ".scss", ".sass", ".less", ".js", ".jsx",
        ".ts", ".tsx", ".vue", ".svelte", ".astro", ".mdx"}
SKIP_DIRS = {"node_modules", ".git", "dist", "build", ".next", "out", "vendor",
             "coverage", ".svelte-kit", ".astro", ".turbo", ".cache", "__pycache__",
             # Not shipped UI. Design comps, palette swatch pages and superseded
             # redesigns describe a look rather than serve it, so a tell inside one
             # is a quotation, not a defect. Scanning them buried the real findings.
             "docs", "_archive", "archive", "mockups", "examples", "_demo", "demo", "demos",
             ".storybook", "storybook-static", "__snapshots__", "fixtures"}

# Keep source offsets when masking so every finding still points at its original line.
LITERAL = re.compile(r'''"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`''', re.DOTALL)
COMMENT = re.compile(r"/\*.*?(?:\*/|\Z)|<!--.*?(?:-->|\Z)|//[^\r\n]*", re.DOTALL)
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
ATTRS = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`|[^>"'`])*'''
W = {"high": 3, "medium": 2, "low": 1}

# Each rule: id, label, severity, fix, and patterns (case-insensitive by default).
# Keep patterns specific enough to avoid drowning the report in false positives.
RULES = [
    # ---- HIGH: the top concrete tells ----
    {"id": "shadcn-default-card", "label": "Untouched shadcn default Card / theme", "sev": "high",
     "fix": "Theme the tokens (primary, radius, neutrals, spacing). Stock defaults are the giveaway, not shadcn.",
     "pats": [r"--radius\s*:\s*0\.5rem"],
     "card": True, "config": True},
    {"id": "ai-purple", "label": "AI purple / indigo / violet as primary color", "sev": "high",
     "fix": "Pick a brand color outside the violet/indigo/purple band. It is Tailwind's default, so it reads as 'nobody chose this'.",
     "pats": [r"\b(bg|text|from|via|to|border|ring|fill|stroke|decoration|outline)-(indigo|violet|purple|fuchsia)-(400|500|600|700|800)\b",
              r"#(6366f1|4f46e5|818cf8|7c3aed|6d28d9|8b5cf6|a855f7|9333ea|7e22ce|c026d3|d946ef)\b"],
     # Someone else's brand is a fact, not a default. Hashnode, dev.to, Twitch and
     # Figma really are purple, so a platform/social swatch is not this tell.
     "suppress": r"\b(platform|brand|social|logo|icon)\b|devto|dev-to|hashnode|twitch|figma|discord|slack|viber|nubank|roku"},
    {"id": "gradient-text", "label": "Gradient-filled text (heading/hero)", "sev": "high",
     "fix": "Solid color on headings and copy. Gradient body text is one of the strongest AI tells.",
     "pats": [r"bg-clip-text\s+[^\"'`]*text-transparent", r"text-transparent\s+[^\"'`]*bg-clip-text",
              r"-webkit-background-clip\s*:\s*text", r"\bbackground-clip\s*:\s*text"]},
    {"id": "purple-blue-gradient", "label": "Purple-to-blue/pink gradient", "sev": "high",
     "fix": "Default to solid fills. If you must gradient, keep stops analogous and low-contrast, never the rainbow purple-to-blue.",
     "pats": [r"from-(purple|violet|indigo|fuchsia)-\d+\s+(via-[a-z]+-\d+\s+)?to-(blue|indigo|pink|cyan|sky)-\d+",
              r"linear-gradient\([^)]*#(6366f1|7c3aed|8b5cf6|a855f7)[^)]*\)"]},
    {"id": "claude-default-look", "label": "The 'tasteful default' cluster (cream / serif / green or clay)", "sev": "high",
     "fix": "Anchor color and type to the real brand or a reference. Mark deliberate choices unslop-ignore on their source lines.",
     "pats": [r"(?:background(?:-color)?|--background)\s*:\s*#(faf8f5|f5f1e8|f3eee3|fdfbf7|f7f3ec|faf6ef|f6f1e7|fbf7f0|f4efe4|f4f1ea)\b|\bbg-(stone|amber|orange)-(50|100)\b",
              r"\b(Instrument\s*Serif|Fraunces|Playfair\s*Display|Cormorant|Spectral|DM\s*Serif)\b",
              r"\b(?:bg|text|border|ring|fill|stroke)-(emerald|green)-(700|800|900)\b|#(d97757|c96442|cc785c|9caf88|87a878|2d4a3e|264e36)\b"],
     "min_signals": 2,
     "suppress": r"\b(warning|caution|alert|notice|error|danger|success|info|badge|toast|status|pending|tag|chip|highlight|mark)\b"},

    # ---- MEDIUM ----
    {"id": "hero-three-cards", "label": "Centered hero + three-feature-card grid skeleton", "sev": "medium",
     "fix": "Break the grid. Asymmetric hero with a real screenshot; vary sections instead of stacked 3-up icon cards.",
     "pats": [r"grid-cols-1\s+(sm:grid-cols-2\s+)?md:grid-cols-3"]},
    {"id": "rounded-everything", "label": "Large rounded corners / pill buttons everywhere", "sev": "medium",
     "fix": "Use a small, intentional radius scale by role. Not everything maximally rounded; pills only occasionally.",
     "pats": [r"\brounded-(2xl|3xl|full)\b", r"border-radius\s*:\s*(999\d*px|9999px)"],
     # rounded-full on a small sized box is a status dot / avatar / icon, not a pill button. Skip those.
     "suppress": r"\b[hw]-(\d|10|11|12|14|16)(\.5)?\b"},
    {"id": "fade-in-animations", "label": "Boilerplate fade-in / hover-grow / scroll animation", "sev": "medium",
     "fix": "Motion only when it communicates something; gate behind prefers-reduced-motion. Minor tell, noisier signal.",
     "pats": [r"initial=\{\{\s*opacity:\s*0", r"whileInView", r"whileHover=\{\{\s*scale",
              r"data-aos\s*=", r"\bhover:scale-1\d{2}\b"]},
    {"id": "neon-glow", "label": "Unprompted neon glow shadow", "sev": "medium",
     "fix": "Remove glow you did not deliberately design. Dark mode should rely on contrast, not glow.",
     # A glow is a zero-offset shadow in a saturated color. The old patterns matched any
     # shadow with a blur, so an ordinary soft drop shadow scored as neon: on one real
     # site that was 78 of 87 findings, every one of them black.
     "pats": [r"shadow-\[0_0_", r"drop-shadow-\[0_0_",
              r"text-shadow\s*:\s*0\s+0\s+\d{2,}px",
              r"box-shadow\s*:\s*0\s+0\s+\d{2,}px"],
     # Achromatic means soft shadow, not glow. `inset` is a fill or an inner border.
     "suppress": r"inset|rgba?\(\s*(\d{1,3})\s*,\s*\1\s*,\s*\1\b|#([0-9a-f])\2{2}\b|#([0-9a-f]{2})\3{2}\b"},
    {"id": "emoji-as-icons", "label": "Emoji used as icons / section bullets", "sev": "medium",
     "fix": "Use a real SVG icon set (Lucide/Phosphor/Heroicons) or none. Emoji-as-UI signals low effort.",
     "pats": [r"[\U0001F680✨⚡\U0001F525\U0001F4A1\U0001F512✅\U0001F3AF\U0001F31F\U0001F6E1\U0001F4C8\U0001F511\U0001F389\U0001F680]"]},
    {"id": "generic-font", "label": "Generic default font (Inter / Geist / Roboto / system)", "sev": "medium",
     "fix": "Choose one family or two for a reason. If two, make them clearly distinct. The starter font reads as 'no choice made'.",
     "pats": [r"font-family\s*:\s*['\"]?(Inter|Geist|Roboto)\b",
              r"\b(Inter|Geist|Geist_Mono|Roboto)\s*\(",
              r"fontFamily\s*:\s*\{[^}]*['\"](Inter|Geist|Roboto)"]},

    {"id": "eyebrow-chrome", "label": "Repeated tracked uppercase labels above headings", "sev": "medium",
     "fix": "Keep labels only when they add information; remove repeated decorative eyebrows.",
     "pats": [r"<(?P<eyebrow>p|span|div|small)\b(?P<attrs>" + ATTRS + r")>[^<]*</(?P=eyebrow)>\s*<h[1-6]\b"],
     "min_count": 3},
    {"id": "tinted-icon-tiles", "label": "Repeated rounded tinted icon tiles", "sev": "medium",
     "fix": "Use icons where they explain a feature; avoid repeating the same decorative tile.",
     "pats": [r"<(?P<tile>div|span)\b(?P<attrs>" + ATTRS + r")>\s*<(?P<icon>[A-Z][A-Za-z0-9]*)\b" + ATTRS + r"/\s*>\s*</(?P=tile)>"],
     "case_sensitive": True, "min_count": 3},

    # ---- LOW: copy + minor ----
    {"id": "middle-dot-meta", "label": "Repeated middle-dot metadata strings", "sev": "low",
     "fix": "Use metadata separators when the content needs them, not as template decoration.",
     "pats": [r"\b\w+ · \w+ · \w+\b"],
     "markup_text": True, "min_count": 2},
    {"id": "appended-arrow", "label": "Repeated arrows appended to links or buttons", "sev": "low",
     "fix": "Keep arrows when they clarify navigation; remove automatic arrows on every action.",
     "pats": [],
     "min_count": 3},
    {"id": "hype-copy", "label": "Generated marketing copy cliche", "sev": "low",
     "fix": "Say what the product literally does, with specifics. Cut the template hype words.",
     "pats": [r"\bTransform your\b", r"\bSupercharge\b", r"\bUnleash\b", r"\bEffortlessly\b",
              r"\breimagined\b", r"take your [^.]{0,30}to the next level", r"\bGame-?changer\b"]},
    {"id": "stock-illustration", "label": "Generic blob / stock illustration source", "sev": "low",
     "fix": "Use real screenshots or commissioned art instead of undraw-style blobs.",
     "pats": [r"undraw", r"storyset", r"\bdrawkit\b"]},
]

def compile_rules(min_sev):
    order = ["high", "medium", "low"]
    floor = order.index(min_sev) if min_sev else len(order) - 1
    out = []
    for r in RULES:
        if order.index(r["sev"]) > floor:
            continue
        r = dict(r)
        r["rx"] = [re.compile(p, 0 if r.get("case_sensitive") else re.IGNORECASE) for p in r["pats"]]
        r["suppress_rx"] = re.compile(r["suppress"], re.IGNORECASE) if r.get("suppress") else None
        out.append(r)
    return out

def iter_files(path):
    if os.path.isfile(path):
        yield path; return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".min.js") or f.endswith(".min.css"):
                continue
            if os.path.splitext(f)[1].lower() in EXTS or f == "components.json":
                yield os.path.join(root, f)

def blank(text):
    return re.sub(r"[^\r\n]", " ", text)

def code_comments(text):
    tokens = re.compile(LITERAL.pattern + "|" + COMMENT.pattern, re.DOTALL)
    return tokens.sub(lambda m: blank(m.group()) if COMMENT.fullmatch(m.group()) else m.group(), text)

def brace_end(text, start):
    depth, i = 1, start + 1
    while i < len(text):
        token = LITERAL.match(text, i) or COMMENT.match(text, i)
        if token:
            i = token.end()
            continue
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if not depth:
                return i + 1
        i += 1
    return len(text)

def tag_at(text, start):
    opener = re.match(r"<(/?)([A-Za-z][\w:.-]*|)(?=[\s/>])", text[start:])
    if not opener:
        return None
    i = start + opener.end()
    attrs_start = i
    while i < len(text):
        token = LITERAL.match(text, i) or COMMENT.match(text, i)
        if token:
            i = token.end()
            continue
        if text[i] == "{":
            i = brace_end(text, i)
            continue
        if text[i] == ">":
            return (i + 1, opener.group(2), text[attrs_start:i], bool(opener.group(1)))
        i += 1
    return None

def source_views(text, code):
    """Mask comments everywhere and code literals outside markup in a second view."""
    clean, markup = [], []
    stack = []
    i = 0
    while i < len(text):
        in_code = (code and not stack) or (stack and stack[-1].lower() in {"script", "style"})
        comment = COMMENT.match(text, i)
        if comment and (not comment.group().startswith("//") or in_code):
            masked = blank(comment.group())
            clean.append(masked)
            markup.append(masked)
            i = comment.end()
            continue
        literal = LITERAL.match(text, i) if in_code else None
        if literal:
            clean.append(literal.group())
            markup.append("?" + blank(literal.group())[1:])
            i = literal.end()
            continue
        tag = tag_at(text, i) if text[i] == "<" else None
        if tag:
            end, name, attrs, closing = tag
            chunk = code_comments(text[i:end])
            clean.append(chunk)
            markup.append(chunk)
            if closing:
                if name in stack:
                    del stack[stack.index(name):]
            elif name not in VOID_TAGS and not attrs.rstrip().endswith("/"):
                stack.append(name)
            i = end
            continue
        if text[i] == "{" and re.match(r"\{\s*/\*", text[i:]):
            end = brace_end(text, i)
            chunk = code_comments(text[i:end])
            if not chunk[1:-1].strip():
                clean.append(blank(chunk))
                markup.append(blank(chunk))
                i = end
                continue
        if not in_code and text[i] == "{":
            end = brace_end(text, i)
            chunk = code_comments(text[i:end])
            if not chunk[1:-1].strip():
                chunk = blank(chunk)
            clean.append(chunk)
            # Only the cheap, static arrow expression is needed by the suffix rule.
            static_arrow = re.fullmatch(r'''\{\s*(["'])→\1\s*\}''', chunk)
            masked = blank(chunk)
            if static_arrow:
                offset = chunk.index("→")
                masked = masked[:offset] + "→" + masked[offset + 1:]
            elif chunk.strip():
                masked = "?" + masked[1:]
            markup.append(masked)
            i = end
            continue
        clean.append(text[i])
        markup.append(text[i] if not in_code or text[i].isspace() else "?")
        i += 1
    return "".join(clean), "".join(markup)

def tags(text):
    i = 0
    while i < len(text):
        start = text.find("<", i)
        if start < 0:
            return
        tag = tag_at(text, start)
        if tag:
            yield (start, *tag)
            i = tag[0]
        else:
            i = start + 1

def attributes(attrs):
    """Read whole attribute values, never attributes quoted inside another value."""
    values = {}
    i = 0
    while i < len(attrs):
        m = re.match(r"\s*([\w:-]+)(?:\s*=\s*)?", attrs[i:])
        if not m:
            i += 1
            continue
        name = m.group(1)
        end = i + m.end()
        if "=" not in m.group():
            i = end
            continue
        literal = LITERAL.match(attrs, end)
        if literal:
            values[name] = ("literal", literal.group()[1:-1])
            i = literal.end()
        elif end < len(attrs) and attrs[end] == "{":
            i = brace_end(attrs, end)
            values[name] = ("expression", attrs[end + 1:i - 1])
        else:
            m = re.match(r"[^\s>]+", attrs[end:])
            i = end + len(m.group()) if m else end
    return values

def static_classes(attrs):
    values = attributes(attrs)
    kind, value = values.get("className", values.get("class", ("literal", "")))
    if kind == "expression":
        value = value.strip()
        call = re.fullmatch(r"(?:cn|clsx)\s*\((.*)\)\s*", value, re.DOTALL)
        if call:
            value = call.group(1)
        literals = list(LITERAL.finditer(value))
        remainder = LITERAL.sub("", value)
        if not literals or (remainder.strip(" \t\r\n,") if call else remainder.strip()):
            return set()
        value = " ".join(m.group()[1:-1] for m in literals)
    return set(value.split()) if "${" not in value else set()

def attribute_value(attrs, name):
    return attributes(attrs).get(name, ("literal", ""))[1]

def is_eyebrow(m):
    classes = static_classes(m.group("attrs"))
    style = attribute_value(m.group("attrs"), "style")
    uppercase = "uppercase" in classes or re.search(r'''(?:text-transform\s*:\s*uppercase\b|textTransform\s*:\s*["']uppercase["'])''', style)
    tracking = classes & {"tracking-wide", "tracking-wider", "tracking-widest"} or re.search(r'''(?:letter-spacing\s*:|letterSpacing\s*:\s*(?:["'][^"']+["']|[0-9.]+))''', style)
    return uppercase and tracking

def is_icon_tile(m, icons):
    classes = static_classes(m.group("attrs"))
    return (m.group("icon") in icons
            and any(re.fullmatch(r"bg-(?:primary|[a-z]+-500)/10", c) for c in classes)
            and any(re.fullmatch(r"rounded-[a-z0-9]+", c) for c in classes))

def accent_context(text, markup, match, rx):
    role = r"(?<![A-Za-z0-9])(?:primary|accent|brand|cta|btn|button|link|heading)(?![A-Za-z0-9])"
    for start, end, name, attrs, closing in tags(markup):
        if start <= match.start() < end and not closing:
            classes = static_classes(attrs)
            badge = any({f"bg-{c}-100", f"text-{c}-700"} <= classes for c in ("green", "emerald"))
            badge |= name.lower() == "span" and {"rounded-full", "text-xs"} <= classes
            if badge:
                return False
            value = " ".join(classes) + " " + attribute_value(attrs, "style")
            has_role = re.search(role, " ".join(classes), re.IGNORECASE) or name.lower() in {"a", "button", "link", "h1", "h2", "h3", "h4", "h5", "h6"}
            return bool(has_role and rx.search(value))
    left = text.rfind("{", 0, match.start())
    if left < 0 or text.rfind("}", 0, match.start()) > left:
        return False
    declaration = text[max(left, text.rfind(";", left, match.start())) + 1:match.end()]
    if re.match(r"\s*--(?:primary|accent|brand)(?:-[\w-]+)?\s*:", declaration):
        return True
    selector = text[max(text.rfind("}", 0, left), text.rfind("{", 0, left)) + 1:left]
    return bool(re.search(role, selector, re.IGNORECASE) or re.search(r"(?<![\w-])(?:a|button|h[1-6])(?![\w-])", selector, re.IGNORECASE))

def middle_dot_hits(text, rx):
    hits = []
    previous = 0
    for start, end, *_ in tags(text):
        run = text[previous:start]
        archive = re.fullmatch(r"\s*\d{4}\s*·\s*\w+\s*·\s*Archive\s*", run, re.IGNORECASE)
        hit = rx.search(text, previous, start)
        if hit and not archive:
            hits.append(hit)
        previous = end
    return hits

def arrow_positions(text):
    actions = []
    hits = []
    for start, end, name, attrs, closing in tags(text):
        if name.lower() not in {"a", "button", "link"}:
            continue
        if not closing and not attrs.rstrip().endswith("/"):
            actions.append((name, start, end))
        elif closing and actions and actions[-1][0] == name:
            _, action_start, body_start = actions.pop()
            body = text[body_start:start]
            pieces = []
            previous = 0
            for child_start, child_end, *_ in tags(body):
                pieces.append(body[previous:child_start])
                previous = child_end
            pieces.append(body[previous:])
            label = unescape("".join(pieces)).strip()
            if label.endswith("→") and label[:-1].strip():
                hits.append(action_start)
    return hits

def scan(path, min_sev):
    rules = compile_rules(min_sev)
    findings = []
    for fp in iter_files(path):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                lines = fh.readlines()
        except OSError:
            continue  # unreadable file: skip, not fatal
        if len(lines) == 1 and len(lines[0]) > 5000:   # likely minified
            continue
        source, markup_source = source_views("".join(lines), os.path.splitext(fp)[1].lower() in {".css", ".scss", ".sass", ".less", ".js", ".jsx", ".ts", ".tsx", ".json"})
        source_lines = source.splitlines(keepends=True)
        markup_lines = markup_source.splitlines(keepends=True)
        for r in rules:
            ignored = {i for i, line in enumerate(lines) if "unslop-ignore" in line.lower()
                       or (r["suppress_rx"] and r["suppress_rx"].search(source_lines[i]))}
            eligible = [blank(line) if i in ignored else line for i, line in enumerate(source_lines)]
            text = "".join(eligible)
            markup = "".join(blank(line) if i in ignored else line for i, line in enumerate(markup_lines))
            matches = []
            if r.get("min_signals") or r.get("min_count"):
                target = text if r.get("min_signals") else markup
                groups = [list(rx.finditer(target)) for rx in r["rx"]]
                if r["id"] == "claude-default-look":
                    groups[2] = [m for m in groups[2] if accent_context(text, markup, m, r["rx"][2])]
                if r.get("min_signals") and sum(bool(g) for g in groups) < r["min_signals"]:
                    continue
                hits = sorted((m for g in groups for m in g), key=lambda m: m.start())
                if r.get("markup_text"):
                    hits = middle_dot_hits(markup, r["rx"][0])
                if r["id"] == "eyebrow-chrome":
                    hits = [m for m in hits if is_eyebrow(m)]
                if r["id"] == "tinted-icon-tiles":
                    imports = re.findall(r"import\s*\{([^}]+)\}\s*from\s*[\"']lucide(?:-[a-z]+)*[\"']", text)
                    icons = {item.strip().split()[-1] for names in imports
                             for item in names.split(",") if item.strip()}
                    hits = [m for m in hits if is_icon_tile(m, icons)]
                positions = arrow_positions(markup) if r["id"] == "appended-arrow" else [m.start() for m in hits]
                if len(positions) < r.get("min_count", 1):
                    continue
                matches = [text.count("\n", 0, min(positions)) + 1]
            else:
                for i, line in enumerate(eligible, 1):
                    if any(rx.search(line) for rx in r["rx"]):
                        matches.append(i)
                if r.get("card"):
                    literals = [(m.start(), m.group()[1:-1]) for m in LITERAL.finditer(text)]
                    applies = [(m.start(), m.group(1)) for m in re.finditer(r"@apply\s+([^;{}]+)", text)]
                    for start, value in literals + applies:
                        classes = set(value.split())
                        count = bool(classes & {"rounded-lg", "rounded-xl"})
                        count += len(classes & {"border", "bg-card", "text-card-foreground", "shadow-sm"})
                        if count >= 4:
                            matches.append(text.count("\n", 0, start) + 1)
                if r.get("config") and os.path.basename(fp) == "components.json":
                    try:
                        config = json.loads(text)
                    except ValueError:
                        config = None
                    if isinstance(config, dict):
                        theme = config.get("tailwind", config)
                        if (isinstance(theme, dict)
                                and theme.get("baseColor") in ("slate", "zinc", "neutral", "gray", "stone")
                                and theme.get("cssVariables", theme.get("cssVars")) is True):
                            m = re.search(r'"baseColor"\s*:', text)
                            matches.append(text.count("\n", 0, m.start() if m else 0) + 1)
            for i in sorted(set(matches)):
                findings.append({"rule": r["id"], "label": r["label"], "sev": r["sev"],
                                 "fix": r["fix"], "file": fp, "line": i,
                                 "snippet": lines[i - 1].strip()[:160]})
    return findings

def verdict(by_sev, weighted):
    # Severity mix decides, not the weighted total. The total let a pile of low findings
    # read as STRONG with zero high ones, which is how the scanner lost its credibility.
    high, med = by_sev.get("high", 0), by_sev.get("medium", 0)
    if high >= 3 or (high >= 1 and med >= 5):
        return "STRONG AI-default look"
    if high >= 1 or med >= 3:
        return "Some AI defaults present"
    if weighted > 0:
        return "Mostly clean, minor tells"
    return "Clean, no tells detected"

def main():
    ap = argparse.ArgumentParser(description="Scan a web codebase for vibe-coded design tells.")
    ap.add_argument("path")
    ap.add_argument("--severity", choices=["high", "medium", "low"], default="low",
                    help="minimum severity to report (default: low = everything)")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--max", type=int, default=10, help="max examples shown per rule (text mode)")
    args = ap.parse_args()

    if not os.path.exists(args.path):
        print(f"path not found: {args.path}", file=sys.stderr); sys.exit(2)

    findings = scan(args.path, args.severity)
    by_sev = {}
    by_rule = {}
    for f in findings:
        by_sev[f["sev"]] = by_sev.get(f["sev"], 0) + 1
        by_rule.setdefault(f["rule"], []).append(f)
    weighted = sum(W[s] * n for s, n in by_sev.items())
    files_scanned = sum(1 for _ in iter_files(args.path))

    if args.json:
        print(json.dumps({"path": args.path, "files_scanned": files_scanned,
                          "counts": by_sev, "vibe_score": weighted,
                          "verdict": verdict(by_sev, weighted), "findings": findings}, indent=2))
        sys.exit(by_sev.get("high", 0))

    sev_order = {"high": 0, "medium": 1, "low": 2}
    rule_ids = sorted(by_rule, key=lambda rid: (sev_order[by_rule[rid][0]["sev"]], -len(by_rule[rid])))
    print(f"\n  unslop-ui scan: {args.path}")
    print(f"  files scanned: {files_scanned}   findings: {len(findings)}   vibe score: {weighted}")
    print(f"  verdict: {verdict(by_sev, weighted)}")
    print(f"  high: {by_sev.get('high',0)}   medium: {by_sev.get('medium',0)}   low: {by_sev.get('low',0)}\n")
    if not findings:
        print("  Nothing flagged. Either it is clean or the tells are layout/motion ones a regex"
              "\n  cannot see. Eyeball the hero layout and animations against references/tells.md.\n")
        return
    for rid in rule_ids:
        items = by_rule[rid]
        f0 = items[0]
        tag = f0["sev"].upper()
        print(f"  [{tag}] {f0['label']}  ({len(items)} hit{'s' if len(items)!=1 else ''})")
        print(f"        fix: {f0['fix']}")
        for it in items[:args.max]:
            print(f"        {it['file']}:{it['line']}  {it['snippet']}")
        if len(items) > args.max:
            print(f"        ... +{len(items) - args.max} more")
        print()
    top = [by_rule[rid][0]['label'] for rid in rule_ids[:3]]
    print("  Top things to change: " + "; ".join(top))
    print("  Layout and motion tells need eyes too. See references/tells.md.\n")
    sys.exit(by_sev.get("high", 0))

if __name__ == "__main__":
    main()
