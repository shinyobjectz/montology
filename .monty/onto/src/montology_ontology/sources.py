"""Public taxonomies worth joining, grouped by the domain they speak for.

Your vocabulary rarely starts from nothing. Where an industry has already
agreed on a word, joining that standard beats minting a synonym — so this
is the shortlist, and it is a SHORTLIST on purpose: a registry that lists
everything is a search engine, and nobody needs another one.

THREE RULINGS PER ENTRY, and the last is the one people skip.

  * ``group``  — who it is for. ``core`` means any business, in any
                 industry, can use it; everything else names its domain.
  * ``status`` — ``ready`` to reach for, or ``evaluate`` with the open
                 question stated.
  * ``licence``/``commercial`` — whether you may SHIP against it. Every
    entry was checked against its source, so there is no "unknown"
    verdict to hide in. An unstated licence is never read as permission:
    ``unlicensed`` means the publisher grants nothing, which is a
    finding, not a gap.

WHAT `core` MEANT BEFORE, AND WHY IT CHANGED. The first cut of this
registry called five things core: three IAB taxonomies and two Google
ones. That is an ADVERTISING core, inherited from what this repo used to
be, and it told a backend team with no ad spend that the first thing they
should reach for was a brand-safety vocabulary. Core now means what it
says — Schema.org for structure, NAICS and SIC for "what industry is
this" — and advertising is a domain like any other.

DECLINED SOURCES ARE NOT LISTED. An earlier version kept a ``skip`` tier
so a rejected candidate would not be re-proposed every time somebody
found it. That reasoning is sound and the cost was worse: a third of the
registry was things nobody should use, which makes the whole page read as
a search result rather than a recommendation. The declines and their
reasons live in this file's git history instead.

None of this is legal advice. The verdict is a starting point for your own
check, not a substitute for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["ready", "evaluate"]
Commercial = Literal["public-domain", "yes", "yes-attribution", "yes-sharealike",
                     "unlicensed", "proprietary"]

#: What each `commercial` verdict actually obliges you to do.
COMMERCIAL_MEANING: dict[str, str] = {
    "public-domain": "no rights reserved (CC0, or a US federal work) — use freely",
    "yes": "permissive licence, no obligations beyond keeping the notice",
    "yes-attribution": "usable commercially IF you credit the source",
    "yes-sharealike": "usable commercially, but derivatives inherit the licence — "
                      "check before folding it into a vocabulary you ship",
    "unlicensed": "CHECKED: the publisher grants no licence at all, so ordinary "
                  "copyright applies and you may not redistribute it. Consuming "
                  "it for the purpose it is published for is a separate question "
                  "from shipping it inside your own product.",
    "proprietary": "someone's property, licensed commercially — not free to use",
}

#: Groups in the order they should be read: everyone first, then by domain.
GROUPS: tuple[str, ...] = (
    "core",
    "advertising & media",
    "retail & e-commerce",
    "trade & occupations",
    "general knowledge",
)


@dataclass(frozen=True, slots=True)
class TaxonomySource:
    id: str                 # namespace it would occupy — e.g. "iab-content"
    name: str
    url: str                # where the data actually lives
    fmt: Literal["tsv", "json", "txt", "markdown", "rdf", "yaml", "csv"]
    group: str              # `core`, or the domain it speaks for
    status: Status
    why: str                # the relevance ruling, one sentence
    licence: str            # as published
    commercial: Commercial  # the practical verdict


SOURCES: tuple[TaxonomySource, ...] = (
    # ── core: any business, any industry ────────────────────────────────
    TaxonomySource(
        "schemaorg", "Schema.org vocabulary (types + properties)",
        "https://schema.org/version/latest/schemaorg-current-https.jsonld",
        "json", "core", "ready",
        "The universal web vocabulary every industry structures data in — 2,454 "
        "classes and properties, and what SEO structured-data work speaks. If you "
        "join one thing on this page, join this.",
        "CC BY-SA 3.0", "yes-sharealike",
    ),
    TaxonomySource(
        "naics", "NAICS (North American Industry Classification System)",
        "https://www.census.gov/naics/",
        "json", "core", "ready",
        "What industry is this? Firmographics for B2B, and the answer every "
        "registry and filing expects. Take it from the Census: the convenience "
        "repackagings declare no licence, and the authority is public domain.",
        "US federal work — public domain (17 U.S.C. §105)", "public-domain",
    ),
    TaxonomySource(
        "sic", "SIC codes",
        "https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list",
        "json", "core", "ready",
        "NAICS's predecessor, still what many registries and filings use. From "
        "the SEC for the same reason NAICS comes from the Census.",
        "US federal work — public domain (17 U.S.C. §105)", "public-domain",
    ),

    # ── advertising & media ─────────────────────────────────────────────
    TaxonomySource(
        "iab-content", "IAB Content Taxonomy 3.1",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "advertising & media", "ready",
        "THE contextual-targeting and brand-safety vocabulary; what OpenRTB speaks.",
        "CC BY 3.0 (stated in the repo README, no LICENSE file — so every "
        "automated scan calls it unlicensed)", "yes-attribution",
    ),
    TaxonomySource(
        "iab-audience", "IAB Audience Taxonomy 1.1",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "advertising & media", "ready",
        "The segmentation counterpart to iab-content; audience descriptions "
        "marketers already use.",
        "CC BY 3.0 (as above)", "yes-attribution",
    ),
    TaxonomySource(
        "iab-adproduct", "IAB Ad Product Taxonomy 2.0",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "advertising & media", "ready",
        "Names the thing being sold; completes the IAB triple.",
        "CC BY 3.0 (as above)", "yes-attribution",
    ),
    TaxonomySource(
        "google-topics", "Google Topics API Taxonomy",
        "https://github.com/patcg-individual-drafts/topics",
        "markdown", "advertising & media", "ready",
        "~470 ad-relevant topics; small, curated, and what Chrome's interest "
        "signals emit.",
        "W3C Software and Document Licence", "yes",
    ),
    TaxonomySource(
        "openooh-venue", "OpenOOH Venue Taxonomy",
        "https://github.com/openooh/venue-taxonomy",
        "json", "advertising & media", "ready",
        "Digital-out-of-home venue types; niche channel, real standard.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "google-nlp-categories", "Google NLP Content Categories",
        "https://cloud.google.com/natural-language/docs/categories",
        "txt", "advertising & media", "ready",
        "~620 labels Google's classifier emits — useful as a mapping TARGET, "
        "not a house vocabulary.",
        "CC BY 4.0 (Google Cloud docs)", "yes-attribution",
    ),
    TaxonomySource(
        "iptc-media-topics", "IPTC Media Topics",
        "https://iptc.org/standards/media-topics/",
        "rdf", "advertising & media", "evaluate",
        "1,200 terms, 13 languages, a real standard — the open question is "
        "RDF/SKOS parsing, which is its own project. Decide when PR or content "
        "work needs it.",
        "CC BY 4.0 — IPTC states it for all NewsCodes", "yes-attribution",
    ),
    TaxonomySource(
        "iab-mapper", "IABTechLab/iab-mapper (2.x → 3.0 mappings)",
        "https://github.com/IABTechLab/iab-mapper",
        "json", "advertising & media", "evaluate",
        "Mappings, not a taxonomy — the open question is whether you have 2.x "
        "codes in the wild. Pertinent the day you meet one.",
        "BSD-2-Clause", "yes",
    ),

    # ── retail & e-commerce ─────────────────────────────────────────────
    TaxonomySource(
        "shopify-product", "Shopify Product Taxonomy",
        "https://github.com/Shopify/product-taxonomy",
        "json", "retail & e-commerce", "ready",
        "10k+ categories with attributes — richer than Google's tree, and the "
        "one in this pair you may actually redistribute.",
        "MIT", "yes",
    ),
    TaxonomySource(
        "google-product", "Google Product Taxonomy",
        "https://www.google.com/basepages/producttype/taxonomy.en-US.txt",
        "txt", "retail & e-commerce", "ready",
        "5k+ categories every Shopping feed must speak. Listed because you will "
        "need it and because the licence is a trap: published FOR building feeds, "
        "which is not permission to ship it inside your own product. Reach for "
        "shopify-product when you need one you may redistribute.",
        "none — a bare .txt on www.google.com, no licence, no terms page, and "
        "developers.google.com's CC BY 4.0 site policy does not reach it",
        "unlicensed",
    ),

    # ── trade & occupations ─────────────────────────────────────────────
    TaxonomySource(
        "cid-classifications", "Harvard Growth Lab classifications (ISIC/HS/SITC/O*NET)",
        "https://github.com/cid-harvard/classifications",
        "csv", "trade & occupations", "evaluate",
        "Many systems in one cleaned repo — incl. O*NET occupations for workforce "
        "mapping. The open question is which one you need: it is heavy, and taking "
        "all of it is taking four vocabularies you did not ask for.",
        "BSD-3-Clause", "yes",
    ),

    # ── general knowledge ───────────────────────────────────────────────
    TaxonomySource(
        "wikidata-taxonomy", "wikidata-taxonomy (extraction CLI)",
        "https://github.com/nichtich/wikidata-taxonomy",
        "json", "general knowledge", "evaluate",
        "A tool, not a dataset — it mints a niche taxonomy out of Wikidata on "
        "demand. The open question is whether the niche you need is actually in "
        "there; Wikidata's coverage is wide and its depth is uneven.",
        "MIT (the tool; Wikidata's own data is CC0)", "yes",
    ),
)

DISCLAIMER = (
    "Every licence here was checked against its source on 2026-09-01 and is "
    "recorded AS PUBLISHED. This is a starting point for your own diligence, "
    "not legal advice — terms change, and an unstated licence is never a "
    "permissive one."
)


def by_group(group: str = "") -> list[TaxonomySource]:
    """The registry, optionally filtered — core first, then by domain."""
    rows = [s for s in SOURCES if not group or s.group == group]
    return sorted(rows, key=lambda s: (GROUPS.index(s.group), s.status != "ready", s.id))


def groups() -> list[str]:
    """The groups actually present, in reading order."""
    present = {s.group for s in SOURCES}
    return [g for g in GROUPS if g in present]


def render(group: str = "") -> list[str]:
    """The registry as lines — what `monty onto sources` prints."""
    if group and group not in groups():
        return [f"no group {group!r}. Known: {', '.join(groups())}."]
    out: list[str] = []
    current = ""
    for s in by_group(group):
        if s.group != current:
            current = s.group
            label = ("core — any business, any industry" if current == "core"
                     else current)
            out.append(f"\n── {label} ──")
        flag = "" if s.status == "ready" else "   [evaluate]"
        out.append(f"  {s.id:24} {s.name}{flag}")
        out.append(f"  {'':24} {s.commercial} · {s.licence}")
        out.append(f"  {'':24} {s.url}")
    out.append("")
    out.append(DISCLAIMER)
    return out
