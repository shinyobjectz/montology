"""The brand component library: scaffold, manifest, and the lint gate.

THE DIVISION OF LABOR, same as gen: montology builds STRUCTURE
deterministically (tokens from the measured kit, the manifest, the gate);
the AGENT writes the React (the ruling recorded in __init__ — mechanical
HTML→JSX conversion loses meaning). Components are stored BY BRAND AND BY
TYPE so downstream frameworks can shop the library: react-email consumes
the email-* types, Remotion the video-* types, pages the rest.

`brand lint` is the gate: a component that skips the tokens, claims an
unknown type, or is missing from disk fails with the repair named — the
same failing-build hook that keeps skills honest keeps libraries honest.
"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path

from montology_core import workspace_root

# Tests pin BRANDS_DIR directly; when None it resolves lazily from the
# workspace. brands/ is the BRAND BOOK — everything indexed about a brand
# (data/ measured + pulled, design/ the component registry and mediums);
# projects/ stay engagements, the work made FOR someone.
BRANDS_DIR: Path | None = None


def brands_dir() -> Path:
    if BRANDS_DIR is not None:
        return BRANDS_DIR
    return workspace_root() / "brands"

# The type taxonomy downstream frameworks shop by. Small on purpose;
# extend by decision, not accretion.
COMPONENT_TYPES = (
    "hero", "nav", "footer", "card", "pricing", "cta", "testimonial",
    "feature", "banner", "logo-row",
    "email-header", "email-body", "email-footer",
    "video-title", "video-lower-third", "video-endcard",
    "page",       # a COMPOSITION of library components — landing pages live here
    "ad-banner",  # fixed-frame display creative (IAB sizes)
    "ad-social",  # fixed-frame social statics
)


def scaffold(brand: str, kit_json: str) -> str:
    """brands/<brand>/ from a measured kit: tokens.ts, manifest.json, README.

    Tokens carry the MEASUREMENTS (hex + count, family + count); naming
    roles (primary/surface/accent) is the agent's judgment call, made in
    tokens.ts where the evidence sits beside the decision.
    """
    try:
        kit = json.loads(kit_json) if kit_json.strip().startswith("{") \
            else json.loads(Path(kit_json).read_text())
    except (json.JSONDecodeError, OSError) as e:
        return f"could not read the kit ({e}). Pass brand_kit's JSON output or a path to it."

    if not re.match(r"^[a-z0-9][a-z0-9-]*$", brand):
        return f"brand {brand!r} must be lowercase-kebab (it becomes a directory and an import path)"

    root = brands_dir() / brand
    design = root / "design"
    data = root / "data"
    for d in ("components", "components/captured", "image", "video",
              "email", "web", "presentation", "logos", "out"):
        (design / d).mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)

    # an AUDIT (brand_audit) carries the full system; a KIT just the basics.
    is_audit = "components" in kit and "tailwind" in kit
    colors = kit.get("colors", [])
    if is_audit:  # audit colors are {"value": ...}; normalise to kit shape
        colors = [{"hex": c["value"], "count": c["count"]} for c in colors
                  if str(c.get("value", "")).startswith("#")]
    fonts = kit.get("fonts", [])
    if isinstance(fonts, dict):
        fonts = fonts.get("families", [])
    tokens = ["// GENERATED scaffold from a measured brand kit — monty brand scaffold",
              f"// source: {kit.get('url', '?')}  derived: {datetime.now(UTC).date()}",
              "// Counts are the evidence. NAME THE ROLES (primary/surface/accent/ink)",
              "// yourself — the measurement cannot know which color is the brand.",
              "export const palette = {"]
    tokens += [f"  c{i}: \"{c['hex']}\", // seen {c['count']}x" for i, c in enumerate(colors[:12])]
    tokens += ["} as const;", "", "export const fonts = {"]
    tokens += [f"  f{i}: \"{f['family']}\", // seen {f['count']}x" for i, f in enumerate(fonts[:6])]
    tokens += ["} as const;", ""]
    if is_audit:
        for name, key, field in (("spacing", "spacing", "value"), ("radii", "radii", "value"),
                                 ("shadows", "shadows", "value")):
            vals = kit.get(key, [])[:8]
            tokens += [f"export const {name} = {{"]
            tokens += [f"  v{i}: \"{v[field]}\", // seen {v['count']}x" for i, v in enumerate(vals)]
            tokens += ["} as const;", ""]
        bps = [b["value"] for b in kit.get("breakpoints", [])[:6]]
        tokens += [f"export const breakpoints = {json.dumps(bps)} as const;", ""]
        tw = kit.get("tailwind", {})
        if tw.get("detected"):
            tokens += [f"// TAILWIND DETECTED (utility density {tw.get('utility_density')}) —",
                       "// the site's own top utilities, i.e. its de-facto config:",
                       "// " + ", ".join(u["class"] for u in tw.get("top_utilities", [])[:14]), ""]
    (design / "tokens.ts").write_text("\n".join(tokens))
    if kit.get("inline_css"):
        (data / "site-inline.css").write_text(kit["inline_css"])
    (data / "audit.json").write_text(json.dumps(
        {k: v for k, v in kit.items() if k != "inline_css"}, indent=1))

    # THE REGISTRY, shadcn-shaped: one canonical component per TYPE slot
    # (Hero.tsx, Nav.tsx, Footer.tsx…), extras numbered. Each candidate's
    # source HTML lands in data/sources/ as evidence, and a CAPTURED React
    # component lands in design/components/captured/ immediately — the
    # agent's idiomatic rebuilds (status=built) replace them over time.
    from .capture import capture_component, component_name

    registry = []
    if is_audit:
        (data / "sources").mkdir(exist_ok=True)
        # THE CANONICAL SLOT GOES TO THE SUBSTANTIVE CANDIDATE: within a
        # type, rank by source size — a site's first DOM "nav" is often the
        # a11y skip link, and Nav.tsx must be the real navigation, not that.
        ranked = sorted(kit.get("components", []),
                        key=lambda c: -len(c.get("source_html", "")))
        slot_counts: dict[str, int] = {}
        for comp in ranked:
            ctype = comp["type"]
            slot_counts[ctype] = slot_counts.get(ctype, 0) + 1
            n = slot_counts[ctype]
            slot = component_name(ctype) + ("" if n == 1 else str(n))
            (data / "sources" / f"{comp['candidate']}.html").write_text(
                comp.get("source_html", ""))
            tsx = design / "components" / "captured" / f"{slot}.tsx"
            tsx.write_text(capture_component(
                slot, comp.get("source_html", ""), kit.get("url", "")))
            registry.append({
                "name": slot, "type": ctype, "status": "captured",
                "file": f"design/components/captured/{slot}.tsx",
                "source_html": f"data/sources/{comp['candidate']}.html",
                "seen_on": comp.get("seen_on", []),
            })

    manifest = {
        "brand": brand,
        "source": kit.get("url", ""),
        "derived": str(datetime.now(UTC).date()),
        "logo": kit.get("logo", ""),
        "pages_measured": kit.get("pages_measured", []),
        "stylesheets": kit.get("stylesheets", []),
        "voice_sample": kit.get("voice_sample", ""),
        "components": registry,
    }
    (root / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (root / "README.md").write_text(
        f"# {brand} — the brand book\n\nDerived from {kit.get('url', '?')} on "
        f"{manifest['derived']}.\n\n- `design/components/` — the registry "
        "(shadcn-shaped): captured/ holds the site's own sections as React; "
        "idiomatic rebuilds registered as status=built replace them.\n"
        "- `design/tokens.ts` — the measured system; `design/image|video|email|"
        "web|presentation/` — the book by medium; `design/logos/` — fetched "
        "vectors with provenance.\n- `data/` — the audit, source HTML, and "
        "social pulls.\n\nRun `monty brand lint " + brand + "` before shipping.\n"
    )
    extra = f", {len(registry)} captured component(s) in design/components/captured/" if registry else ""
    return (f"scaffolded brands/{brand}/ — design/tokens.ts ({len(colors[:12])} colors, "
            f"{len(fonts[:6])} fonts, roles unnamed on purpose){extra}")


def register(brand: str, name: str, ctype: str, file: str, source_url: str = "") -> str:
    """Add a component to the brand's manifest — the library's ledger."""
    root = brands_dir() / brand
    mf = root / "manifest.json"
    if not mf.exists():
        return f"no manifest at brands/{brand}/ — run `monty brand scaffold {brand} <kit>` first"
    if ctype not in COMPONENT_TYPES:
        return f"type {ctype!r} is not in the taxonomy: {', '.join(COMPONENT_TYPES)}"
    manifest = json.loads(mf.read_text())
    manifest["components"] = [c for c in manifest["components"] if c["name"] != name]
    manifest["components"].append({
        "name": name, "type": ctype, "file": file,
        "source": source_url, "added": str(datetime.now(UTC).date()),
    })
    mf.write_text(json.dumps(manifest, indent=1))
    return f"registered {name} ({ctype}) -> {file}"


def lint(brand: str) -> list[str]:
    """The deterministic gate. FAIL lines carry their repair."""
    root = brands_dir() / brand
    report: list[str] = []
    mf = root / "manifest.json"
    if not mf.exists():
        return [f"FAIL brands/{brand}: no manifest.json — scaffold first"]
    try:
        manifest = json.loads(mf.read_text())
    except json.JSONDecodeError as e:
        return [f"FAIL brands/{brand}/manifest.json does not parse: {e}"]

    if not manifest.get("source") or not manifest.get("derived"):
        report.append(f"FAIL brands/{brand}: manifest missing source/derived — provenance is not optional")
    if not (root / "design" / "tokens.ts").exists():
        report.append(f"FAIL brands/{brand}: no design/tokens.ts — components have nothing to import")

    built = captured = 0
    for comp in manifest.get("components", []):
        f = root / comp.get("file", "")
        tag = f"brands/{brand}/{comp.get('file', '?')}"
        if comp.get("type") not in COMPONENT_TYPES:
            report.append(f"FAIL {tag}: type {comp.get('type')!r} not in the taxonomy")
        if comp.get("status") in ("candidate", "captured"):
            # evidence tier: must exist and render, exempt from the design laws
            captured += 1
            if not f.exists():
                report.append(f"FAIL {tag}: captured component missing on disk")
            continue
        built += 1
        if not f.exists():
            report.append(f"FAIL {tag}: listed in the manifest but missing on disk")
            continue
        text = f.read_text()
        if not text.strip():
            report.append(f"FAIL {tag}: empty file")
        if "tokens" not in text:
            report.append(f"FAIL {tag}: does not import the brand tokens — "
                          "hex codes copied from a scrape are drift, tokens are the contract")
        if re.search(r"#[0-9a-fA-F]{3,6}\b", re.sub(r"//[^\n]*", "", text)):
            report.append(f"FAIL {tag}: literal hex color in JSX — use the palette from tokens.ts")
        if comp.get("type") in ("ad-banner", "ad-social"):
            m = re.search(r"-(\d{2,4})x(\d{2,4})\.tsx$", comp.get("file", ""))
            if not m:
                report.append(f"FAIL {tag}: fixed-frame ads are named <name>-<w>x<h>.tsx "
                              "so the format is legible from the filename")
            elif f"{m.group(1)}" not in text or f"{m.group(2)}" not in text:
                report.append(f"FAIL {tag}: the file claims {m.group(1)}x{m.group(2)} but those "
                              "dimensions do not appear in the component — declare the frame")

    report.append(("FAIL" if any(r.startswith("FAIL") for r in report) else "ok")
                  + f" — {built} built, {captured} captured awaiting idiomatic rebuild, "
                  f"tokens {'present' if (root / 'design' / 'tokens.ts').exists() else 'MISSING'}")
    return report
