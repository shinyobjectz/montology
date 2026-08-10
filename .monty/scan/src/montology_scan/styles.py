"""The style surface: what the code SAYS visually, measured.

Design values are vocabulary — a hex code is a word that means one thing —
and this module gives the ontology eyes for them. Three collectors, all
structural:

  * CSS/SCSS via tree-sitter's css grammar: colors (`color_value`, rgb()),
    spacing (px/rem on margin/padding/gap), font families, custom
    properties and their `var()` uses, and every class DEFINED.
  * Markup via the existing JS/TSX/HTML parses: every class USED
    (class/className strings), inline `style="…"`, `style={{…}}` objects.
  * Tailwind, from the used classes: utilities counted, arbitrary-value
    escapes (`p-[13px]`, `text-[#123456]`) recorded — each escape is a
    value that left the scale.

`design_lint` is where tokens bite: rogue values name their NEAREST
token, near-duplicates cluster, undefined classes surface. Advisory by
default — a repo without a design ontology gets statistics, not failures;
`[design] enforce = true` in montology.toml promotes rogues to FAILs.
"""

from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from montology_core import workspace_root

from .surface import _iter_files, _scan_config, MAX_BYTES

STYLE_EXTS = {".css": "css", ".scss": "scss"}
MARKUP_EXTS = {".jsx": "javascript", ".tsx": "tsx", ".js": "javascript",
               ".ts": "typescript", ".html": "html", ".vue": "html"}

SPACING_PROPS = ("margin", "padding", "gap", "inset", "top", "right", "bottom", "left")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
RGB_RE = re.compile(r"rgba?\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)")
PX_RE = re.compile(r"\b(\d+(?:\.\d+)?)(px|rem)\b")
TW_ARBITRARY_RE = re.compile(r"\[([^\]]+)\]")

# the actual Tailwind utility namespace (stems) — "ghost-panel" is kebab-case
# but NOT a utility, and the undefined-class law must know the difference
_TW_STEMS = {
    "p", "px", "py", "pt", "pr", "pb", "pl", "m", "mx", "my", "mt", "mr",
    "mb", "ml", "w", "h", "min", "max", "flex", "grid", "block", "inline",
    "hidden", "table", "gap", "space", "items", "justify", "content", "self",
    "place", "text", "font", "leading", "tracking", "align", "whitespace",
    "break", "bg", "from", "via", "to", "border", "divide", "outline", "ring",
    "rounded", "shadow", "opacity", "mix", "blur", "brightness", "contrast",
    "drop", "grayscale", "transition", "duration", "ease", "delay", "animate",
    "scale", "rotate", "translate", "skew", "origin", "cursor", "select",
    "resize", "list", "appearance", "columns", "col", "row", "order", "float",
    "clear", "object", "overflow", "overscroll", "position", "top", "right",
    "bottom", "left", "inset", "z", "basis", "grow", "shrink", "sticky",
    "static", "fixed", "absolute", "relative", "visible", "invisible", "sr",
    "not", "container", "aspect", "size", "truncate", "underline", "uppercase",
    "lowercase", "capitalize", "italic", "antialiased", "decoration", "fill",
    "stroke", "accent", "caret", "pointer", "touch", "will", "snap", "scroll",
}


def _is_utility(cls: str) -> bool:
    """Tailwind-shaped: variant prefixes stripped, the stem must be REAL."""
    base = cls.split(":")[-1].lstrip("-!")
    if "[" in base:
        return True  # arbitrary-value escapes are utilities by construction
    return base.split("-")[0] in _TW_STEMS


def norm_color(text: str) -> str | None:
    """#abc / #aabbcc / rgb(r,g,b) → lowercase #rrggbb; None if not a color."""
    text = text.strip()
    m = RGB_RE.match(text)
    if m:
        return "#" + "".join(f"{min(255, int(v)):02x}" for v in m.groups())
    if text.startswith("#"):
        h = text[1:].lower()
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h[:3])
        if len(h) == 8:
            h = h[:6]
        if len(h) == 6 and all(c in "0123456789abcdef" for c in h):
            return "#" + h
    return None


def color_distance(a: str, b: str) -> int:
    """Channel-sum distance between two #rrggbb strings (0..765)."""
    av = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    bv = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return sum(abs(x - y) for x, y in zip(av, bv))


def _style_files(root: Path) -> tuple[list[Path], list[Path]]:
    cfg = _scan_config(root)
    stack = [root] + [root / inc for inc in cfg.get("include", []) if (root / inc).is_dir()]
    css, markup = [], []
    from .surface import EXCLUDE_DIRS

    exclude = EXCLUDE_DIRS | set(cfg.get("exclude", []))
    while stack:
        d = stack.pop()
        try:
            entries = sorted(d.iterdir())
        except OSError:
            continue
        for e in entries:
            if e.name in exclude or e.name.startswith("."):
                continue
            if e.is_dir():
                stack.append(e)
            elif e.suffix in STYLE_EXTS:
                css.append(e)
            elif e.suffix in MARKUP_EXTS:
                markup.append(e)
    return css, markup


def style_surface(root: Path) -> dict:
    """Everything the code says visually, with first-seen locations."""
    from tree_sitter_language_pack import get_parser

    colors: Counter[str] = Counter()
    spacing: Counter[str] = Counter()
    fonts: Counter[str] = Counter()
    where: dict[str, str] = {}          # value -> "file:line" first seen
    defined_classes: set[str] = set()
    used_classes: Counter[str] = Counter()
    custom_props: dict[str, str] = {}
    arbitrary: list[dict] = []

    def note(value: str, f: Path, line: int) -> None:
        where.setdefault(value, f"{f.relative_to(root)}:{line}")

    css_files, markup_files = _style_files(root)

    for f in css_files:
        if f.stat().st_size > MAX_BYTES:
            continue
        try:
            tree = get_parser(STYLE_EXTS[f.suffix]).parse(f.read_bytes())
        except Exception:  # noqa: BLE001
            continue
        stack = [tree.root_node]
        while stack:
            n = stack.pop()
            stack.extend(n.children)
            if n.type == "class_selector":
                name = n.text.decode(errors="replace").lstrip(".")
                defined_classes.add(name)
            elif n.type == "declaration":
                prop = n.child(0).text.decode(errors="replace")
                value_text = n.text.decode(errors="replace")
                line = n.start_point[0] + 1
                if prop.startswith("--"):
                    custom_props[prop] = value_text.partition(":")[2].strip(" ;")
                for raw in HEX_RE.findall(value_text) + \
                        [m.group(0) for m in RGB_RE.finditer(value_text)]:
                    c = norm_color(raw)
                    if c:
                        colors[c] += 1
                        note(c, f, line)
                if prop.split("-")[0] in SPACING_PROPS:
                    for num, unit in PX_RE.findall(value_text):
                        spacing[num + unit] += 1
                        note(num + unit, f, line)
                if prop in ("font-family", "font"):
                    fam = value_text.partition(":")[2].split(",")[0].strip(" ;'\"")
                    if fam and not fam.startswith("var("):
                        fonts[fam] += 1

    class_attr_re = re.compile(
        r'(?:class|className)\s*=\s*["\']([^"\']+)["\']')
    style_attr_re = re.compile(r'style\s*=\s*["\']([^"\']+)["\']')
    style_obj_re = re.compile(r"style=\{\{(.*?)\}\}", re.S)
    for f in markup_files:
        if f.stat().st_size > MAX_BYTES:
            continue
        try:
            text = f.read_text(errors="replace")
        except OSError:
            continue
        for m in class_attr_re.finditer(text):
            line = text[:m.start()].count("\n") + 1
            for cls in m.group(1).split():
                used_classes[cls] += 1
                for arb in TW_ARBITRARY_RE.findall(cls):
                    arbitrary.append({"class": cls, "file": f"{f.relative_to(root)}:{line}"})
                    c = norm_color(arb)
                    if c:
                        colors[c] += 1
                        note(c, f, line)
        for m in list(style_attr_re.finditer(text)) + list(style_obj_re.finditer(text)):
            line = text[:m.start()].count("\n") + 1
            for raw in HEX_RE.findall(m.group(1)):
                c = norm_color(raw)
                if c:
                    colors[c] += 1
                    note(c, f, line)
            for num, unit in PX_RE.findall(m.group(1)):
                spacing[num + unit] += 1
                note(num + unit, f, line)

    return {"colors": colors, "spacing": spacing, "fonts": fonts, "where": where,
            "defined_classes": defined_classes, "used_classes": used_classes,
            "custom_props": custom_props, "arbitrary": arbitrary,
            "files": len(css_files) + len(markup_files)}


NEAR = 30  # channel-sum distance under which two colors are "the same blue"


def design_lint(root: Path | None = None) -> list[str]:
    """Where tokens bite the styles. Advisory unless [design] enforce."""
    from montology_ontology import tokens

    import tomllib

    root = root or workspace_root()
    enforce = False
    toml = root / ".monty" / "montology.toml"
    if toml.exists():
        try:
            enforce = tomllib.loads(toml.read_text()).get("design", {}).get("enforce", False)
        except tomllib.TOMLDecodeError:
            pass

    surface = style_surface(root)
    if not surface["files"]:
        return []
    report: list[str] = []
    toks = tokens()
    tok_colors = {t["name"]: norm_color(t["value"]) for t in toks
                  if t["category"] == "color" and norm_color(t["value"])}
    tag = "FAIL" if enforce else "note"

    # rogue values: literals that are not (exactly) a token, nearest named
    if tok_colors:
        values = set(tok_colors.values())
        for c, count in surface["colors"].most_common():
            if c in values:
                continue
            nearest = min(tok_colors.items(), key=lambda kv: color_distance(c, kv[1]))
            dist = color_distance(c, nearest[1])
            hint = (f"nearest token: {nearest[0]} {nearest[1]} (Δ{dist})"
                    if dist <= NEAR * 3 else "no token is close — name it or remove it")
            report.append(f"{tag} design: rogue color {c} ×{count} "
                          f"(first at {surface['where'].get(c, '?')}) — {hint}")

    # near-duplicates among observed colors: two names for one blue
    seen = [c for c, n in surface["colors"].most_common(40) if n >= 2]
    for i, a in enumerate(seen):
        for b in seen[i + 1:]:
            d = color_distance(a, b)
            if 0 < d <= NEAR:
                report.append(f"note design: {a} and {b} are Δ{d} apart "
                              f"({surface['colors'][a]}× / {surface['colors'][b]}×) — "
                              "one job, two values; pick one and tokenize it")

    # classes used but defined nowhere (and not utility-shaped)
    ghosts = [(cls, n) for cls, n in surface["used_classes"].most_common()
              if n >= 2 and cls not in surface["defined_classes"]
              and not _is_utility(cls)]
    for cls, n in ghosts[:10]:
        report.append(f"note design: class {cls!r} used {n}× but defined in no stylesheet")

    # arbitrary-value escapes: values that left the scale
    if surface["arbitrary"]:
        sample = ", ".join(a["class"] for a in surface["arbitrary"][:5])
        report.append(f"note design: {len(surface['arbitrary'])} Tailwind arbitrary "
                      f"value(s) — each left the scale ({sample}…) — tokenize or use scale steps")

    report.append(f"design: {sum(surface['colors'].values())} color use(s) "
                  f"({len(surface['colors'])} distinct), {len(surface['spacing'])} spacing "
                  f"value(s), {len(toks)} token(s), {len(surface['arbitrary'])} escape(s)")
    return report


def design_candidates(root: Path | None = None, top: int = 8) -> str:
    """The design vocabulary the code is asking for — adoption-ready."""
    root = root or workspace_root()
    from montology_ontology import tokens

    surface = style_surface(root)
    have = {norm_color(t["value"]) for t in tokens() if t["category"] == "color"}
    lines = []
    for c, n in surface["colors"].most_common(top):
        if c in have:
            continue
        lines.append(f"{n:>5}x  {c}   (first at {surface['where'].get(c, '?')})  "
                     f"— adopt: monty design token <name> color \"{c}\"")
    for s, n in surface["spacing"].most_common(top):
        lines.append(f"{n:>5}x  {s:<8}— adopt: monty design token <name> space \"{s}\"")
    for fam, n in surface["fonts"].most_common(3):
        lines.append(f"{n:>5}x  {fam:<24}— adopt: monty design token <name> font \"{fam}\"")
    return "\n".join(lines) or "no style surface found (no css/markup files)."
