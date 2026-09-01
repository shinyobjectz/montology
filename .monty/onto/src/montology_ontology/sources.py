"""Every public taxonomy montology knows about, with two rulings on each.

THE REGISTRY IS THE TRIAGE. Candidate taxonomies arrive faster than anyone
can evaluate them, so each entry carries a status and the reason for it:

  * ``core``     — the ones worth reaching for first
  * ``extra``    — pertinent, but not everyone's need
  * ``evaluate`` — known, looks promising, NOT recommended yet; the note
                   says what question must be answered first
  * ``skip``     — considered and declined, with the reason, so it is not
                   re-litigated every time someone finds the repo

A status is a decision, and moving a source between statuses is a reviewed
change — that is the whole point of it being code rather than a wiki page.

THE SECOND RULING IS THE LICENCE, and it is here because it was NOT here
for the registry's whole first life. Every earlier version carried only
relevance ("is this a real taxonomy, does it fit"), which is the question
that matters least to somebody deciding whether they may SHIP against it.

All 27 were checked, so there is no "unknown" verdict to hide behind.
Four things fell out of doing it:

  * the IAB taxonomies — three of the five `core` entries — declare CC BY
    3.0 in their repo README and ship no LICENSE file, so every automated
    licence scan reports them as unlicensed. Attribution is required and
    almost nobody knows it.
  * `google-product` grants nothing: a bare .txt on www.google.com with no
    licence and no terms page, and developers.google.com's CC BY 4.0 site
    policy does not reach it. It is published so you can build a feed;
    that is not permission to ship it inside your own product.
  * `schemaorg` is CC BY-SA 3.0. Share-alike is a real constraint on a
    derived vocabulary, and it is the one licence here that can reach back
    into what a user builds on top of it.
  * NAICS and SIC now point at the Census and the SEC rather than at
    convenience repackagings that declare no licence. The authority is a
    US federal work and therefore public domain; there was never a reason
    to inherit somebody's unlicensed copy of it.

`commercial` is the practical verdict and `licence` is the evidence for
it. An UNSTATED licence is never read as a permissive one — `unlicensed`
means the publisher grants nothing, which is a finding, not a gap.

None of this is legal advice, and the registry says so in the one place it
matters — the verdict is a starting point for your own check, not a
substitute for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["core", "extra", "evaluate", "skip"]
Commercial = Literal["public-domain", "yes", "yes-attribution", "yes-sharealike",
                     "unlicensed", "proprietary", "gone"]

#: What each `commercial` verdict actually obliges you to do.
#:
#: There is deliberately no "unknown" here. An earlier cut of this registry
#: had one, and it hid two completely different states behind one word:
#: "nobody looked" and "we looked and the publisher grants nothing". The
#: second is a finding — `google-product` is the live example, a bare .txt
#: with no licence and no terms page — and it is the finding a person most
#: needs, because the absence of a licence is not permission.
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
    "gone": "the source no longer resolves; nothing to license",
}


@dataclass(frozen=True, slots=True)
class TaxonomySource:
    id: str                 # namespace it would occupy — e.g. "iab-content"
    name: str
    url: str                # where the data actually lives
    fmt: Literal["tsv", "json", "txt", "markdown", "rdf", "yaml", "csv"]
    status: Status
    why: str                # the relevance ruling, one sentence
    licence: str            # as published, or "none declared"
    commercial: Commercial  # the practical verdict
    domain: str             # the industry or field it speaks for


SOURCES: tuple[TaxonomySource, ...] = (
    # ── core ────────────────────────────────────────────────────────────
    TaxonomySource(
        "iab-content", "IAB Content Taxonomy 3.1",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "core",
        "THE contextual-targeting and brand-safety vocabulary; what OpenRTB speaks.",
        "CC BY 3.0", "yes-attribution", "advertising · media",
    ),
    TaxonomySource(
        "iab-audience", "IAB Audience Taxonomy 1.1",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "core",
        "The segmentation counterpart to iab-content; audience descriptions marketers already use.",
        "CC BY 3.0", "yes-attribution", "advertising · audience",
    ),
    TaxonomySource(
        "iab-adproduct", "IAB Ad Product Taxonomy 2.0",
        "https://github.com/InteractiveAdvertisingBureau/Taxonomies",
        "tsv", "core",
        "Names the thing being sold; completes the IAB triple.",
        "CC BY 3.0", "yes-attribution", "advertising · inventory",
    ),
    TaxonomySource(
        "google-product", "Google Product Taxonomy",
        "https://www.google.com/basepages/producttype/taxonomy.en-US.txt",
        "txt", "core",
        "5k+ categories every Shopping feed must speak; e-commerce lives here. "
        "Published FOR building feeds; that is not a licence to redistribute it "
        "inside your own product, and Google grants none.",
        "none — a bare .txt on www.google.com, no licence, no terms page, and "
        "developers.google.com's CC BY 4.0 site policy does not reach it",
        "unlicensed", "retail · e-commerce",
    ),
    TaxonomySource(
        "google-topics", "Google Topics API Taxonomy",
        "https://github.com/patcg-individual-drafts/topics",
        "markdown", "core",
        "~470 ad-relevant topics; small, curated, and what Chrome's interest signals emit.",
        "W3C Software and Document Licence", "yes", "advertising · web platform",
    ),

    # ── extra ───────────────────────────────────────────────────────────
    TaxonomySource(
        "shopify-product", "Shopify Product Taxonomy",
        "https://github.com/Shopify/product-taxonomy",
        "json", "extra",
        "10k+ categories with attributes — richer than Google's tree; heavy, so opt-in.",
        "MIT", "yes", "retail · e-commerce",
    ),
    TaxonomySource(
        "openooh-venue", "OpenOOH Venue Taxonomy",
        "https://github.com/openooh/venue-taxonomy",
        "json", "extra",
        "Digital-out-of-home venue types; niche channel, real standard.",
        "Apache-2.0", "yes", "advertising · out-of-home",
    ),
    TaxonomySource(
        "google-nlp-categories", "Google NLP Content Categories",
        "https://cloud.google.com/natural-language/docs/categories",
        "txt", "extra",
        "~620 labels Google's classifier emits — useful as a mapping TARGET, not a house vocabulary.",
        "CC BY 4.0 (Google Cloud docs)", "yes-attribution", "content classification",
    ),
    TaxonomySource(
        "schemaorg", "Schema.org vocabulary (types + properties)",
        "https://schema.org/version/latest/schemaorg-current-https.jsonld",
        "json", "extra",
        "The universal web vocabulary every industry structures data in; 2,454 "
        "classes and properties, and what SEO structured-data work speaks.",
        "CC BY-SA 3.0", "yes-sharealike", "cross-industry · web",
    ),
    TaxonomySource(
        "naics", "NAICS (North American Industry Classification System)",
        "https://www.census.gov/naics/",
        "json", "extra",
        "Industry classification — firmographics for B2B. Take it from the Census: "
        "the convenience repackaging at CompileInc/naics-codes declares no licence, "
        "and there is no reason to inherit that when the authority is public domain.",
        "US federal work — public domain (17 U.S.C. §105)", "public-domain",
        "cross-industry · government",
    ),
    TaxonomySource(
        "sic", "SIC codes",
        "https://www.sec.gov/corpfin/division-of-corporation-finance-standard-industrial-classification-sic-code-list",
        "json", "extra",
        "NAICS's predecessor, still what many registries file under. From the SEC "
        "for the same reason NAICS comes from the Census.",
        "US federal work — public domain (17 U.S.C. §105)", "public-domain",
        "cross-industry · government",
    ),

    # ── evaluate ────────────────────────────────────────────────────────
    TaxonomySource(
        "cid-classifications", "Harvard Growth Lab classifications (ISIC/HS/SITC/O*NET)",
        "https://github.com/cid-harvard/classifications",
        "csv", "evaluate",
        "Many systems, one cleaned repo — incl. O*NET occupations for workforce "
        "mapping. Heavy; take one system when a concrete need names it.",
        "BSD-3-Clause", "yes", "trade · occupations",
    ),
    TaxonomySource(
        "iptc-media-topics", "IPTC Media Topics",
        "https://iptc.org/standards/media-topics/",
        "rdf", "evaluate",
        "1,200 terms, 13 languages, real standard — but RDF/SKOS parsing is its own "
        "project; decide when PR or content work needs it.",
        "CC BY 4.0 — IPTC states it for all NewsCodes", "yes-attribution",
        "news · media",
    ),
    TaxonomySource(
        "iab-mapper", "IABTechLab/iab-mapper (2.x → 3.0 mappings)",
        "https://github.com/IABTechLab/iab-mapper",
        "json", "evaluate",
        "Mappings, not a taxonomy — pertinent the day you meet 2.x codes in the wild.",
        "BSD-2-Clause", "yes", "advertising · migration",
    ),
    TaxonomySource(
        "wikidata-taxonomy", "wikidata-taxonomy (extraction CLI)",
        "https://github.com/nichtich/wikidata-taxonomy",
        "json", "evaluate",
        "A tool, not a dataset — could mint niche taxonomies on demand; decide if a "
        "real need appears.",
        "MIT (the tool; Wikidata's own data is CC0)", "yes", "general knowledge",
    ),
    TaxonomySource(
        "icb", "Industry Classification Benchmark (FTSE/Dow Jones)",
        "https://gist.github.com/mysticmind/bf3acd436bbaddca62ca1f3e01e890c9",
        "json", "evaluate",
        "The open GICS-alternative investors reference — but a personal gist is not "
        "an authority, and ICB itself is FTSE Russell's property. Find a durable, "
        "licensed source before touching it.",
        "ICB is proprietary to FTSE Russell; the gist republishes it without "
        "a licence to do so", "proprietary", "finance",
    ),
    # ── skip: considered, declined — with the licence checked anyway, because
    #    "we declined it" and "we never looked" are different sentences and a
    #    reader cannot tell them apart from a blank field.
    TaxonomySource(
        "adtech-crosswalk", "IAB ↔ Google crosswalk (markomma)",
        "https://github.com/markomma/adtech-crosswalk",
        "json", "skip",
        "404 as of 2026-09-01. Bidirectional IAB/Google mappings would join two "
        "core sources; this one is gone, so find a live equivalent to reopen it.",
        "n/a — the repository no longer exists", "gone", "advertising · migration",
    ),
    TaxonomySource(
        "ipullrank-iab-json", "iPullRank IAB-as-JSON",
        "https://github.com/iPullRank-dev/iab-taxonomy",
        "json", "skip",
        "Repackaging of what the official TSVs already give; a second copy is a drift risk.",
        "MIT", "yes", "advertising",
    ),
    TaxonomySource(
        "eai-taxonomy", "Essential-AI web-content taxonomy",
        "https://github.com/Essential-AI/eai-taxonomy",
        "json", "skip",
        "Built for pretraining-data curation; wrong audience for its categories.",
        "none — the README's Licence section is an unfilled '[License information]' placeholder, so nothing is granted", "unlicensed", "ML data curation",
    ),
    TaxonomySource(
        "oss-taxonomy", "ecosyste.ms OSS taxonomy",
        "https://github.com/ecosyste-ms/oss-taxonomy",
        "yaml", "skip",
        "Classifies open-source projects; no user vocabulary joins against it yet. "
        "Reopens with a concrete use.",
        "CC0-1.0", "public-domain", "open source",
    ),
    TaxonomySource(
        "misp", "MISP threat-intel taxonomies",
        "https://github.com/MISP/misp-taxonomies",
        "json", "skip",
        "Security tagging for CERTs; no business-vocabulary surface. Revisit only if "
        "trust-and-safety work lands.",
        "CC0 1.0 (dual-licensed, CC0 or BSD)", "public-domain", "security",
    ),
    TaxonomySource(
        "classifast", "classifast (UNSPSC/NAICS/ISIC/ETIM classifier)",
        "https://github.com/DmitryMatv/classifast",
        "json", "skip",
        "An app that classifies against standards, not the standards themselves.",
        "MIT", "yes", "classification tooling",
    ),
    TaxonomySource(
        "naics-gh", "NAICS-GH labeled-repos dataset",
        "https://huggingface.co/datasets/aquiro1994/naics-gh",
        "csv", "skip",
        "An ML training dataset, not a taxonomy; naics itself is the source here.",
        "CC BY 4.0", "yes-attribution", "ML data",
    ),
    TaxonomySource(
        "sic-naics-finance-macros", "SIC/NAICS/GICS/Fama-French SAS crosswalk",
        "https://gist.github.com/mgao6767/4134ce36793b9e932a219ff07d7a3c7f",
        "csv", "skip",
        "Finance-research tooling in SAS; the crosswalk idea returns via "
        "cid-classifications if mapping work lands.",
        "none — a gist carries no licence unless its author writes one, and this "
        "one does not", "unlicensed", "finance research",
    ),
    TaxonomySource(
        "instructlab-taxonomy", "InstructLab knowledge taxonomy",
        "https://github.com/instructlab/taxonomy",
        "yaml", "skip",
        "A tuning-data organisation scheme, not a domain vocabulary.",
        "Apache-2.0", "yes", "ML tuning",
    ),
    TaxonomySource(
        "dmoz-curlie", "DMOZ / Curlie web directory",
        "https://curlie.org/",
        "rdf", "skip",
        "Legacy; Topics API is the modern descendant of this idea.",
        "CC BY 3.0 Unported", "yes-attribution", "web directory",
    ),
    TaxonomySource(
        "tabiya", "Tabiya occupations/skills taxonomy",
        "https://docs.tabiya.org/our-tech-stack/inclusive-livelihoods-taxonomy/open-taxonomy-platform",
        "json", "skip",
        "Occupations and livelihoods; adjacent at best — revisit with a concrete use.",
        "MIT for the platform code; the taxonomy itself derives from the EU's "
        "ESCO and carries the Commission's reuse terms", "yes-attribution",
        "occupations · skills",
    ),
)

DISCLAIMER = (
    "All 27 licences were checked against the source on 2026-09-01 and are "
    "recorded AS PUBLISHED. This is a starting point for your own diligence, "
    "not legal advice — terms change, and an unstated licence is never a "
    "permissive one."
)


def by_status(status: Status | str = "") -> list[TaxonomySource]:
    """The registry, optionally filtered — core first, then the rest."""
    order = {"core": 0, "extra": 1, "evaluate": 2, "skip": 3}
    rows = [s for s in SOURCES if not status or s.status == status]
    return sorted(rows, key=lambda s: (order[s.status], s.id))


def render(status: Status | str = "") -> list[str]:
    """The registry as lines — what `monty onto sources` prints."""
    rows = by_status(status)
    if not rows:
        return [f"no sources with status {status!r}. "
                f"Known: core, extra, evaluate, skip."]
    out: list[str] = []
    current = ""
    for s in rows:
        if s.status != current:
            current = s.status
            out.append(f"\n── {current} ──")
        out.append(f"  {s.id:26} {s.name}")
        out.append(f"  {'':26} {s.domain} · {s.licence} · {s.commercial}")
        out.append(f"  {'':26} {s.url}")
    out.append("")
    out.append(DISCLAIMER)
    return out
