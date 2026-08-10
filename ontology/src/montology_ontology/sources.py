"""Every taxonomy montology knows about, with a ruling on each.

THE REGISTRY IS THE TRIAGE. Candidate taxonomies arrive faster than anyone
can evaluate them, so each entry carries a status and the reason for it:

  * ``core``     — ingested by ``montology data pull`` by default
  * ``extra``    — ingestable on request (``data pull <id>``), pertinent but
                   not everyone's need
  * ``evaluate`` — known, looks promising, NOT ingested; the note says what
                   question must be answered first
  * ``skip``     — considered and declined, with the reason (so it is not
                   re-litigated every time someone finds the repo)

A status is a decision, and moving a source between statuses is a reviewed
change — that is the whole point of it being code.

SCOPE (widened 2026-08-10): marketing-first, business-wide. Industry,
product, occupation and web-vocabulary systems belong here too — a user
building their own ontology joins it to whatever classification their
business already speaks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Status = Literal["core", "extra", "evaluate", "skip"]


@dataclass(frozen=True, slots=True)
class TaxonomySource:
    id: str                # namespace inside ontology.db — e.g. "iab-content"
    name: str
    url: str               # where the data actually lives
    fmt: Literal["tsv", "json", "txt", "markdown", "rdf", "yaml"]
    status: Status
    why: str               # the ruling, one sentence


SOURCES: tuple[TaxonomySource, ...] = (
    # ── core: the language ad tech actually transacts in ───────────────────
    TaxonomySource(
        "iab-content", "IAB Content Taxonomy 3.1",
        "https://raw.githubusercontent.com/InteractiveAdvertisingBureau/Taxonomies/main/Content%20Taxonomies/Content%20Taxonomy%203.1.tsv",
        "tsv", "core",
        "THE contextual-targeting and brand-safety vocabulary; what OpenRTB speaks.",
    ),
    TaxonomySource(
        "iab-audience", "IAB Audience Taxonomy 1.1",
        "https://raw.githubusercontent.com/InteractiveAdvertisingBureau/Taxonomies/main/Audience%20Taxonomies/Audience%20Taxonomy%201.1.tsv",
        "tsv", "core",
        "The segmentation counterpart to iab-content; audience descriptions marketers already use.",
    ),
    TaxonomySource(
        "iab-adproduct", "IAB Ad Product Taxonomy 2.0",
        "https://raw.githubusercontent.com/InteractiveAdvertisingBureau/Taxonomies/main/Ad%20Product%20Taxonomies/Ad%20Product%20Taxonomy%202.0.tsv",
        "tsv", "core",
        "Names the thing being sold; completes the IAB triple.",
    ),
    TaxonomySource(
        "google-product", "Google Product Taxonomy",
        "https://www.google.com/basepages/producttype/taxonomy.en-US.txt",
        "txt", "core",
        "5k+ categories every Shopping feed must speak; e-commerce marketing lives here.",
    ),
    TaxonomySource(
        "google-topics", "Google Topics API Taxonomy",
        "https://raw.githubusercontent.com/patcg-individual-drafts/topics/main/taxonomy_v2.md",
        "markdown", "core",
        "~470 ad-relevant topics; small, curated, and what Chrome's interest signals emit.",
    ),

    # ── extra: pertinent, pull on request ───────────────────────────────────
    TaxonomySource(
        "shopify-product", "Shopify Product Taxonomy",
        "https://raw.githubusercontent.com/Shopify/product-taxonomy/main/dist/en/taxonomy.json",
        "json", "extra",
        "10k+ categories with attributes — richer than Google's tree; heavy, so opt-in.",
    ),
    TaxonomySource(
        "openooh-venue", "OpenOOH Venue Taxonomy",
        "https://raw.githubusercontent.com/openooh/venue-taxonomy/main/specification.json",
        "json", "extra",
        "Digital-out-of-home venue types; niche channel, real standard.",
    ),
    TaxonomySource(
        "google-nlp-categories", "Google NLP Content Categories",
        "https://cloud.google.com/natural-language/docs/categories",
        "txt", "extra",
        "~620 labels Google's classifier emits — useful as a mapping TARGET, not a house vocabulary.",
    ),

    # ── extra: cross-industry (business-wide, pull on request) ─────────────
    TaxonomySource(
        "schemaorg", "Schema.org vocabulary (types + properties)",
        "https://schema.org/version/latest/schemaorg-current-https.jsonld",
        "json", "extra",
        "The universal web vocabulary every industry structures data in; also what "
        "SEO structured-data work speaks.",
    ),
    TaxonomySource(
        "naics", "NAICS (North American Industry Classification System)",
        "https://codeload.github.com/CompileInc/naics-codes/tar.gz/refs/heads/master",
        "json", "extra",
        "Industry classification — firmographics for B2B. Ingested from the repo "
        "tarball (one fetch, not two thousand API calls).",
    ),
    TaxonomySource(
        "sic", "SIC codes",
        "https://codeload.github.com/CompileInc/sic-codes/tar.gz/refs/heads/master",
        "json", "extra",
        "NAICS's predecessor, still what many registries file under; same tarball "
        "ingest as naics.",
    ),

    # ── evaluate: promising, question unanswered ────────────────────────────
    TaxonomySource(
        "cid-classifications", "Harvard Growth Lab classifications (ISIC/HS/SITC/O*NET)",
        "https://github.com/cid-harvard/classifications",
        "csv", "evaluate",
        "Many systems, one cleaned repo — incl. O*NET occupations for workforce "
        "mapping. Heavy; ingest per-system when a concrete need names one.",
    ),
    TaxonomySource(
        "icb", "Industry Classification Benchmark (FTSE/Dow Jones)",
        "https://gist.github.com/mysticmind/bf3acd436bbaddca62ca1f3e01e890c9",
        "json", "evaluate",
        "The open GICS-alternative investors reference — but a personal gist is "
        "not an authority; find a durable source before ingesting.",
    ),
    TaxonomySource(
        "iptc-media-topics", "IPTC Media Topics",
        "https://iptc.org/standards/media-topics/",
        "rdf", "evaluate",
        "1,200 terms, 13 languages, real standard — but RDF/SKOS ingest is its own project; decide when PR/content work needs it.",
    ),
    TaxonomySource(
        "iab-mapper", "IABTechLab/iab-mapper (2.x → 3.0 mappings)",
        "https://github.com/IABTechLab/iab-mapper",
        "json", "evaluate",
        "Mappings, not a taxonomy — pertinent the day we meet 2.x codes in the wild; ingest then.",
    ),
    TaxonomySource(
        "adtech-crosswalk", "IAB ↔ Google crosswalk (markomma)",
        "https://github.com/markomma/adtech-crosswalk",
        "json", "evaluate",
        "Bidirectional IAB/Google mappings would join our core sources — verify quality first; LLM-assisted mappings need spot-checking.",
    ),
    TaxonomySource(
        "wikidata-taxonomy", "wikidata-taxonomy (extraction CLI)",
        "https://github.com/nichtich/wikidata-taxonomy",
        "json", "evaluate",
        "A tool, not a dataset — could mint niche taxonomies on demand; decide if a real need appears.",
    ),

    # ── skip: considered, declined ──────────────────────────────────────────
    TaxonomySource(
        "ipullrank-iab-json", "iPullRank IAB-as-JSON",
        "https://github.com/iPullRank-dev/iab-taxonomy",
        "json", "skip",
        "Repackaging of what we ingest from the official TSVs; a second copy is a drift risk.",
    ),
    TaxonomySource(
        "eai-taxonomy", "Essential-AI web-content taxonomy",
        "https://github.com/Essential-AI/eai-taxonomy",
        "json", "skip",
        "Built for pretraining-data curation, not marketing; wrong audience for its categories.",
    ),
    TaxonomySource(
        "oss-taxonomy", "ecosyste.ms OSS taxonomy",
        "https://github.com/ecosyste-ms/oss-taxonomy",
        "yaml", "skip",
        "Classifies open-source projects; even business-wide, none of our users' "
        "vocabularies join against it yet. Reopens with a concrete use.",
    ),
    TaxonomySource(
        "misp", "MISP threat-intel taxonomies",
        "https://github.com/MISP/misp-taxonomies",
        "json", "skip",
        "Security tagging for CERTs; no business-vocabulary surface here. Revisit "
        "only if trust-and-safety work lands.",
    ),
    TaxonomySource(
        "classifast", "classifast (UNSPSC/NAICS/ISIC/ETIM classifier)",
        "https://github.com/DmitryMatv/classifast",
        "json", "skip",
        "An app that classifies against standards, not the standards themselves — "
        "we ingest sources, and the zoo owns classification.",
    ),
    TaxonomySource(
        "naics-gh", "NAICS-GH labeled-repos dataset",
        "https://huggingface.co/datasets/aquiro1994/naics-gh",
        "csv", "skip",
        "An ML training dataset, not a taxonomy; naics itself is the source here.",
    ),
    TaxonomySource(
        "sic-naics-finance-macros", "SIC/NAICS/GICS/Fama-French SAS crosswalk",
        "https://gist.github.com/mgao6767/4134ce36793b9e932a219ff07d7a3c7f",
        "csv", "skip",
        "Finance-research tooling in SAS; the crosswalk idea returns via "
        "cid-classifications if mapping work lands.",
    ),
    TaxonomySource(
        "instructlab-taxonomy", "InstructLab knowledge taxonomy",
        "https://github.com/instructlab/taxonomy",
        "yaml", "skip",
        "A tuning-data organization scheme, not a domain vocabulary.",
    ),
    TaxonomySource(
        "dmoz-curlie", "DMOZ / Curlie web directory",
        "https://curlie.org/",
        "rdf", "skip",
        "Legacy; Topics API already gives us the modern descendant of this idea.",
    ),
    TaxonomySource(
        "tabiya", "Tabiya occupations/skills taxonomy",
        "https://docs.tabiya.org/our-tech-stack/inclusive-livelihoods-taxonomy/open-taxonomy-platform",
        "json", "skip",
        "Occupations and livelihoods; adjacent to B2B targeting at best — revisit only with a concrete use.",
    ),
)


def by_status(status: Status) -> tuple[TaxonomySource, ...]:
    return tuple(s for s in SOURCES if s.status == status)


def get(source_id: str) -> TaxonomySource | None:
    return next((s for s in SOURCES if s.id == source_id), None)
