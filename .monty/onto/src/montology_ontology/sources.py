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
    "health & life sciences",
    "finance",
    "retail & e-commerce",
    "advertising & media",
    "agriculture & food",
    "environment & climate",
    "software & infrastructure",
    "security",
    "AI, ML & data science",
    "geography",
    "trade & occupations",
    "research & information",
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
    TaxonomySource(
        "dublin-core", "DCMI Metadata Terms (Dublin Core)",
        "https://www.dublincore.org/specifications/dublin-core/dcmi-terms/",
        "rdf", "core", "ready",
        "The 25-year-old lingua franca for describing ANY resource — title, "
        "creator, date, subject, rights. If your system has records, it already "
        "half-speaks this.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "skos", "SKOS — Simple Knowledge Organization System (W3C)",
        "https://www.w3.org/TR/skos-reference/",
        "rdf", "core", "ready",
        "Not a vocabulary but the standard SHAPE of one: concepts, broader/"
        "narrower, preferred and alternate labels. Half the taxonomies on this "
        "page are published in it, and it is what to publish yours in.",
        "W3C Software and Document Licence", "yes",
    ),
    TaxonomySource(
        "prov-o", "PROV-O — the Provenance Ontology (W3C)",
        "https://www.w3.org/TR/prov-o/",
        "rdf", "core", "ready",
        "Who made this, from what, and when. Every audit, lineage and "
        "reproducibility story reinvents this badly; it is already standard.",
        "W3C Software and Document Licence", "yes",
    ),
    TaxonomySource(
        "qudt", "QUDT — Quantities, Units, Dimensions and Types",
        "https://github.com/qudt/qudt-public-repo",
        "rdf", "core", "ready",
        "Units and what they measure, done properly. Any system carrying a "
        "number with a unit has this problem, and almost all of them solve it "
        "with a string column.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "bfo", "BFO — Basic Formal Ontology",
        "https://obofoundry.org/ontology/bfo.html",
        "rdf", "core", "ready",
        "The upper ontology (ISO/IEC 21838-2) most serious domain ontologies "
        "sit on: continuant vs occurrent, the distinctions you otherwise argue "
        "about from scratch. Reach for it when your ontology needs a spine.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "ro", "RO — the Relation Ontology",
        "https://obofoundry.org/ontology/ro.html",
        "rdf", "core", "ready",
        "Standard relations — part_of, derives_from, participates_in — so your "
        "edges mean what everyone else's edges mean. The counterpart to BFO's "
        "nouns, and montology's own `onto relate` is the same idea.",
        "CC0 1.0", "public-domain",
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

    # ── software & infrastructure ───────────────────────────────────────
    TaxonomySource(
        "otel-semconv", "OpenTelemetry Semantic Conventions",
        "https://opentelemetry.io/docs/specs/semconv/",
        "yaml", "software & infrastructure", "ready",
        "The one to reach for. Names services, hosts, containers, cloud "
        "providers, HTTP, RPC, databases, messaging and their attributes — the "
        "vocabulary your telemetry already emits, which makes it the vocabulary "
        "your infrastructure already speaks whether you wrote it down or not.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "purl", "purl — Package URL specification",
        "https://github.com/package-url/purl-spec",
        "json", "software & infrastructure", "ready",
        "One identity for a package across every ecosystem: "
        "pkg:npm/foo@1.2.3. The join key the whole supply chain agreed on, and "
        "the answer to 'is this the same dependency' across tools.",
        "MIT", "yes",
    ),
    TaxonomySource(
        "cyclonedx", "OWASP CycloneDX",
        "https://cyclonedx.org/specification/overview/",
        "json", "software & infrastructure", "ready",
        "Bill of materials for software, services, hardware and ML models — "
        "what a component IS, what it depends on and where it came from.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "spdx", "SPDX — specification and licence list",
        "https://spdx.org/licenses/",
        "json", "software & infrastructure", "ready",
        "The canonical identifiers for software licences (`Apache-2.0`, "
        "`CC-BY-4.0`) plus the SBOM spec around them. Every licence string in "
        "montology's own registry is an SPDX id.",
        "Community Specification Licence 1.0; pre-existing portions CC BY 3.0",
        "yes-attribution",
    ),
    TaxonomySource(
        "openapi", "OpenAPI Specification",
        "https://spec.openapis.org/oas/latest.html",
        "yaml", "software & infrastructure", "ready",
        "The vocabulary of an HTTP API — operation, path, parameter, schema, "
        "response, security scheme. Whatever your service calls these things "
        "internally, this is what its consumers call them.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "asyncapi", "AsyncAPI Specification",
        "https://www.asyncapi.com/docs/reference/specification/latest",
        "yaml", "software & infrastructure", "ready",
        "OpenAPI's counterpart for event-driven systems: channels, messages, "
        "operations, bindings. The names for the half of a distributed system "
        "that is not request/response.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "json-schema", "JSON Schema",
        "https://json-schema.org/specification",
        "json", "software & infrastructure", "ready",
        "How to say what a document must look like — the shape language "
        "OpenAPI, AsyncAPI and Croissant all build on.",
        "BSD-style (JSON Schema Specification Authors)", "yes",
    ),
    TaxonomySource(
        "cdevents", "CDEvents (Continuous Delivery Foundation)",
        "https://cdevents.dev/",
        "json", "software & infrastructure", "ready",
        "A common vocabulary for what happens in a pipeline — build queued, "
        "artifact published, service deployed — so tools from different vendors "
        "describe the same event the same way.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "conventional-commits", "Conventional Commits",
        "https://www.conventionalcommits.org/",
        "markdown", "software & infrastructure", "ready",
        "A tiny, near-universal taxonomy of CHANGE: feat, fix, refactor, chore, "
        "and what each implies for a version. The smallest useful vocabulary on "
        "this page and probably the most widely adopted.",
        "MIT", "yes",
    ),
    TaxonomySource(
        "semver", "Semantic Versioning",
        "https://semver.org/",
        "markdown", "software & infrastructure", "ready",
        "What MAJOR, MINOR and PATCH mean — a three-term vocabulary that ends "
        "the argument about whether a change is breaking.",
        "CC BY 3.0", "yes-attribution",
    ),
    TaxonomySource(
        "swo", "SWO — the Software Ontology",
        "https://obofoundry.org/ontology/swo.html",
        "rdf", "software & infrastructure", "ready",
        "What a piece of software IS — its licence, version, inputs, outputs "
        "and the task it performs. OBO-reviewed, which almost nothing else in "
        "this group is.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "doap", "DOAP — Description of a Project",
        "https://github.com/ewilderj/doap",
        "rdf", "software & infrastructure", "evaluate",
        "The RDF vocabulary for describing a software project — repository, "
        "release, maintainer, language. A finished, stable spec rather than an "
        "abandoned one, but the open question is whether you need RDF at all "
        "when purl and SPDX cover identity and licensing already.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "tosca", "OASIS TOSCA (Topology and Orchestration Specification)",
        "https://github.com/oasis-open/tosca-community-contributions",
        "yaml", "software & infrastructure", "evaluate",
        "A vendor-neutral vocabulary for cloud application topology — nodes, "
        "relationships, capabilities, requirements. The open question is "
        "adoption: it is a real OASIS standard that most teams have replaced "
        "with their orchestrator's own nouns.",
        "Apache-2.0", "yes",
    ),

    # ── AI, ML & data science ───────────────────────────────────────────
    TaxonomySource(
        "croissant", "Croissant — ML dataset metadata (MLCommons)",
        "https://github.com/mlcommons/croissant",
        "json", "AI, ML & data science", "ready",
        "Describes an ML dataset: its records, fields, splits, provenance and "
        "licence. Built on Schema.org, adopted by Hugging Face, Kaggle and "
        "OpenML — the closest thing to a standard a dataset has.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "edam", "EDAM — data, operations, formats and identifiers",
        "https://edamontology.org/",
        "rdf", "AI, ML & data science", "ready",
        "What an analysis DOES and what it consumes and produces: operations, "
        "data types, formats, identifiers. Grew up in bioinformatics and the "
        "operation/format halves are domain-neutral.",
        "CC BY-SA 4.0", "yes-sharealike",
    ),
    TaxonomySource(
        "stato", "STATO — the Statistical Methods Ontology",
        "https://obofoundry.org/ontology/stato.html",
        "rdf", "AI, ML & data science", "ready",
        "Names statistical tests, distributions, model parameters and what a "
        "result means — so 'significant' and 'confidence interval' stop being "
        "whatever the last analyst meant by them.",
        "CC BY 3.0", "yes-attribution",
    ),
    TaxonomySource(
        "mitre-atlas", "MITRE ATLAS — adversarial threats to AI systems",
        "https://atlas.mitre.org/",
        "json", "AI, ML & data science", "ready",
        "ATT&CK's shape applied to machine learning: prompt injection, model "
        "evasion, data poisoning, model theft, named and structured. The "
        "nearest thing to a settled vocabulary for how AI systems get attacked.",
        "Apache-2.0", "yes",
    ),
    TaxonomySource(
        "owasp-llm", "OWASP Top 10 for LLM Applications",
        "https://genai.owasp.org/llm-top-10/",
        "markdown", "AI, ML & data science", "ready",
        "The risk vocabulary LLM application teams actually cite — prompt "
        "injection, insecure output handling, excessive agency. A ranked list "
        "rather than an ontology, and it is what people mean by these terms.",
        "CC BY-SA 4.0", "yes-sharealike",
    ),

    # ── health & life sciences ──────────────────────────────────────────
    TaxonomySource(
        "mondo", "Mondo Disease Ontology",
        "https://obofoundry.org/ontology/mondo.html",
        "rdf", "health & life sciences", "ready",
        "One disease vocabulary merging OMIM, Orphanet, DOID and NCIt — built "
        "precisely because those disagreed. The reference for naming a disease.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "doid", "Human Disease Ontology",
        "https://obofoundry.org/ontology/doid.html",
        "rdf", "health & life sciences", "ready",
        "The long-standing disease vocabulary Mondo builds on; CC0, so the one "
        "to take when attribution is inconvenient.",
        "CC0 1.0", "public-domain",
    ),
    TaxonomySource(
        "ncit", "NCI Thesaurus (OBO edition)",
        "https://obofoundry.org/ontology/ncit.html",
        "rdf", "health & life sciences", "ready",
        "The US National Cancer Institute's reference terminology — broad "
        "clinical and biomedical coverage, far past oncology.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "go", "Gene Ontology",
        "https://obofoundry.org/ontology/go.html",
        "rdf", "health & life sciences", "ready",
        "The most-used ontology in science, full stop: molecular function, "
        "biological process, cellular component. The proof that a maintained "
        "vocabulary compounds in value.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "chebi", "ChEBI — Chemical Entities of Biological Interest",
        "https://obofoundry.org/ontology/chebi.html",
        "rdf", "health & life sciences", "ready",
        "Molecules and their roles, from EMBL-EBI. What to join if anything in "
        "your system is a compound, a drug or an ingredient.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "uberon", "Uberon multi-species anatomy ontology",
        "https://obofoundry.org/ontology/uberon.html",
        "rdf", "health & life sciences", "ready",
        "Anatomy across species, cross-referenced to the species-specific ones. "
        "The anatomical vocabulary with the widest reach.",
        "CC BY 3.0", "yes-attribution",
    ),

    # ── finance ─────────────────────────────────────────────────────────
    TaxonomySource(
        "fibo", "FIBO — Financial Industry Business Ontology",
        "https://github.com/edmcouncil/fibo",
        "rdf", "finance", "ready",
        "The EDM Council's model of financial instruments, entities, contracts "
        "and market roles — the serious answer to what a 'counterparty' or a "
        "'derivative' IS. MIT-licensed, which is unusual for finance and the "
        "reason this replaced the proprietary ICB that used to sit here.",
        "MIT", "yes",
    ),

    # ── agriculture & food ──────────────────────────────────────────────
    TaxonomySource(
        "foodon", "FoodOn — the Food Ontology",
        "https://obofoundry.org/ontology/foodon.html",
        "rdf", "agriculture & food", "ready",
        "Food products, sources and processing — for menus, supply chains, "
        "nutrition and recall traceability alike.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "agro", "AGRO — the Agronomy Ontology",
        "https://obofoundry.org/ontology/agro.html",
        "rdf", "agriculture & food", "ready",
        "Agronomic practices, traits and inputs; joins FoodOn upstream of the "
        "plate.",
        "CC BY 4.0", "yes-attribution",
    ),

    # ── environment & climate ───────────────────────────────────────────
    TaxonomySource(
        "envo", "ENVO — the Environment Ontology",
        "https://obofoundry.org/ontology/envo.html",
        "rdf", "environment & climate", "ready",
        "Biomes, environmental materials and features — the vocabulary for "
        "where something is, in ESG, climate and sustainability reporting.",
        "CC0 1.0", "public-domain",
    ),

    # ── security ────────────────────────────────────────────────────────
    TaxonomySource(
        "mitre-attack", "MITRE ATT&CK",
        "https://attack.mitre.org/",
        "json", "security", "ready",
        "Adversary tactics and techniques — the vocabulary every detection, "
        "threat-intel and red-team report already speaks. MITRE grants a "
        "royalty-free commercial licence explicitly.",
        "MITRE royalty-free licence (research, development AND commercial; "
        "reproduce the copyright designation)", "yes-attribution",
    ),
    TaxonomySource(
        "cwe", "CWE — Common Weakness Enumeration",
        "https://cwe.mitre.org/",
        "json", "security", "ready",
        "The classification of software weakness TYPES — what class of bug this "
        "is, as opposed to CVE's which instance. What every scanner reports in.",
        "MITRE royalty-free licence (research, development AND commercial; "
        "reproduce the copyright designation)", "yes-attribution",
    ),
    TaxonomySource(
        "cve", "CVE — Common Vulnerabilities and Exposures",
        "https://www.cve.org/",
        "json", "security", "ready",
        "The identifier for a specific vulnerability instance — the WHICH to "
        "CWE's what-class-of-bug. CC0, so nothing constrains reuse.",
        "CC0 1.0", "public-domain",
    ),
    TaxonomySource(
        "d3fend", "MITRE D3FEND — defensive countermeasures",
        "https://d3fend.mitre.org/",
        "rdf", "security", "ready",
        "The counterpart to ATT&CK: what you DO about a technique, as a real "
        "ontology with typed relations back to the attacks it addresses.",
        "MIT", "yes",
    ),

    # ── geography ───────────────────────────────────────────────────────
    TaxonomySource(
        "geonames", "GeoNames ontology + gazetteer",
        "https://www.geonames.org/ontology/documentation.html",
        "rdf", "geography", "ready",
        "11M+ place names with a feature-type vocabulary (country, city, "
        "admin division, landmark). The open answer to 'what kind of place "
        "is this'.",
        "CC BY 4.0", "yes-attribution",
    ),

    # ── research & information ──────────────────────────────────────────
    TaxonomySource(
        "iao", "IAO — Information Artifact Ontology",
        "https://obofoundry.org/ontology/iao.html",
        "rdf", "research & information", "ready",
        "Documents, datasets, identifiers, measurements — what an information "
        "thing IS, as opposed to what it is about. The distinction most data "
        "models blur.",
        "CC BY 4.0", "yes-attribution",
    ),
    TaxonomySource(
        "dcat", "DCAT — Data Catalog Vocabulary (W3C)",
        "https://www.w3.org/TR/vocab-dcat-3/",
        "rdf", "research & information", "ready",
        "How to describe a dataset and a catalogue of them — what every "
        "government open-data portal publishes in, and what a data catalogue "
        "should not reinvent.",
        "W3C Software and Document Licence", "yes",
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
