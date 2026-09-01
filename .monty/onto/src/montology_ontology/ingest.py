"""Ingest: another vocabulary's terms, in this database, marked as theirs.

`sources.py` is a CATALOGUE — it says what exists, where the data lives, and
whether you may ship against it. This is the other half, for the two sources
an open question actually needs: fetch the published file, parse it, and put
every term into the vocabulary as an ADOPTED word carrying the source it came
from.

The answer that justifies the work is one line long. `monty onto check
Activity` has to be able to say "that is PROV-O's word, and this is what
PROV-O means by it" instead of "free" — because a name that is free here and
taken by the standard its domain already agreed on is not free, it is a
synonym waiting to be minted. A catalogue cannot give that answer; only the
terms can.

CUSTODY, the discipline `upstream.py` already keeps:

  * every ingested row carries ``origin = taxonomy:<id>``, so an adopted word
    is never mistaken for one this repo authored;
  * re-ingesting REPLACES that source's rows wholesale — a standard is the
    standard's to change, and a half-refreshed vocabulary is worse than a
    stale one;
  * a name this repo already owns (``origin`` NULL) is never overwritten:
    local wins, loudly, and every conflict is named in the report;
  * a retired name stays retired — the rename ledger outranks an import, or
    an ingest would resurrect exactly what a rename put down.

ATTRIBUTION IS NOT A FOOTNOTE. Schema.org is CC BY-SA 3.0, whose share-alike
reaches into anything derived from it, and PROV-O is under the W3C Software
and Document Licence. So the licence and what it obliges travel with the
words: the ingest report says it, `monty onto check` says it for any adopted
name, and the rendered words skill cites it rather than listing the terms.
Being allowed to READ a vocabulary and being allowed to SHIP one are
different permissions, which is why `sources.py` records a verdict per entry
and why nothing here is allowed to lose it.

WHY ONLY TWO SOURCES. An ingester is written per source because each one
publishes a different shape — this is RDF/XML and JSON-LD, not two dialects
of a single "ontology file" — and a parser nobody has run against the real
payload is a guess. Fifty-six of those would be a worse artefact than two
that are right. The rest stay a catalogue until something needs them, and an
id with no ingester is refused with the ones that have one.
"""

from __future__ import annotations

import html
import json
import re
import sqlite3
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from montology_core import find_root

from .db import connect, db_path
from .sources import COMMERCIAL_MEANING, SOURCES, TaxonomySource

#: What an ingested word's `origin` starts with. Prefixed rather than bare so
#: nothing confuses a public standard with an org's upstream database — the
#: other thing `origin` holds, which `monty onto pull` refreshes and this must
#: never touch.
ORIGIN_PREFIX = "taxonomy:"

#: Where a fetched payload lands. Under `.monty/cache/` because that directory
#: is already gitignored and already means "refetchable, never tracked": a
#: 1.5 MB vocabulary file is someone else's artefact, not our source.
CACHE_REL = Path(".monty") / "cache" / "sources"

# How much of a source's prose a word carries. Schema.org comments run past
# four thousand characters, and every surface that shows a definition shows it
# on a line — `onto check`, the words skill, the canvas. The authoritative full
# text lives at the term's own page, which the report and the check both name.
DEFINITION_CAP = 600

_TAG = re.compile(r"<[^>]+>")


@dataclass(frozen=True, slots=True)
class Term:
    """One term as its publisher states it, before this database has an
    opinion about it. `pos` is filled only where the source's own structure
    settles it — see `_POS`."""
    name: str
    definition: str
    pos: str | None
    url: str


@dataclass(frozen=True, slots=True)
class Ingester:
    """How one registry entry is turned into terms. `data` is deliberately not
    the registry's `url`: that field points at the page a person reads, and a
    parser needs the file a machine reads."""
    source: str
    data: str
    suffix: str
    parse: Callable[[bytes], tuple[list[Term], list[str]]]
    credit: str


# WHY A CLASS GETS A PART OF SPEECH AND A PROPERTY DOES NOT. `pos` is what a
# collision is judged on, and it is a judgement in the REGISTER OF THE REPO
# adopting the word. A class names a thing in both sources — that mapping
# cannot be wrong, so it is made. A property is a different matter: Schema.org's
# `author` is plainly a noun and PROV-O's `wasGeneratedBy` is plainly a verb,
# and inventing a part of speech for fifteen hundred of them would poison the
# one dimension the gate uses to judge. An unjudged word carries no judgement.
_POS = "noun"


def _plain(text: str) -> str:
    """Publisher prose as one line: markup out, entities decoded, whitespace
    collapsed. Their text is kept as written otherwise — an adopted definition
    that has been paraphrased is no longer the source's definition."""
    return re.sub(r"\s+", " ", html.unescape(_TAG.sub("", text or ""))).strip()


def _cut(text: str, cap: int = DEFINITION_CAP) -> str:
    """Long prose at a word boundary, with the ellipsis said out loud."""
    if len(text) <= cap:
        return text
    return text[:cap].rsplit(" ", 1)[0] + "…"


# ── the parsers, one per shape ──────────────────────────────────────────────

_PROV = "{http://www.w3.org/ns/prov#}"
_RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
_RDFS = "{http://www.w3.org/2000/01/rdf-schema#}"
_OWL = "{http://www.w3.org/2002/07/owl#}"
_XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"

_PROV_NS = "http://www.w3.org/ns/prov#"
_PROV_O = "http://www.w3.org/ns/prov-o#"
_PROV_SHAPES = {_OWL + "Class": _POS, _OWL + "ObjectProperty": None,
                _OWL + "DatatypeProperty": None}


def _prov_local(iri: str) -> str:
    return iri.rsplit("#", 1)[-1]


def _prov_prose(node: ET.Element) -> str:
    """PROV-O's definition for one term, in the order the ontology means them.

    `prov:definition` is the normative text. An `rdfs:comment` is the fallback,
    and the ENGLISH one is preferred because several terms carry an untagged
    editorial note first — `hadActivity`'s says only that its domains suit
    multiple OWL profiles, which would make a fine footnote and a useless
    definition."""
    stated = node.find(_PROV + "definition")
    if stated is not None and (stated.text or "").strip():
        return _plain(stated.text)
    comments = node.findall(_RDFS + "comment")
    for comment in comments:
        if comment.get(_XML_LANG) == "en" and (comment.text or "").strip():
            return _plain(comment.text)
    for comment in comments:
        if (comment.text or "").strip():
            return _plain(comment.text)
    return ""


def _prov_relation(node: ET.Element) -> str:
    """What the ontology says about a term when it publishes no prose for it.

    Ten PROV-O terms have neither a definition nor a comment — `wasGeneratedBy`
    among them, which is one of the terms people come here for. The honest
    answer is the ontology's own structure (its domain and range) plus the spec
    entry, never a definition written here: a definition invented for someone
    else's term is the failure this whole file exists to prevent."""
    ends = []
    for field in ("domain", "range"):
        edge = node.find(_RDFS + field)
        target = edge.get(_RDF + "resource") if edge is not None else None
        if target:
            ends.append(f"prov:{_prov_local(target)}")
    return " to ".join(ends)


def parse_prov_o(raw: bytes) -> tuple[list[Term], list[str]]:
    """PROV-O out of the RDF/XML at `https://www.w3.org/ns/prov.rdf`.

    That file is the whole PROV namespace — PROV-O plus prov-aq, prov-dc,
    prov-dictionary and prov-links, and the annotation properties the file uses
    to describe itself (`definition`, `category`, `component`). Ingesting all of
    it would put `label`, `comment` and `todo` in the vocabulary as if W3C had
    standardised them. So terms are taken only where the file itself says
    `rdfs:isDefinedBy prov-o#`, which is PROV-O's own 80: 30 classes and 50
    properties, the set the specification documents.

    RDF/XML rather than the Turtle at `prov-o.ttl` for one reason: the standard
    library parses XML and does not parse Turtle, and a hand-rolled Turtle
    reader is a dependency with none of the testing."""
    root = ET.fromstring(raw)
    found: dict[str, Term] = {}
    for node in root:
        about = node.get(_RDF + "about") or ""
        if node.tag not in _PROV_SHAPES or not about.startswith(_PROV_NS):
            continue
        pos = _PROV_SHAPES[node.tag]
        defined_by = node.find(_RDFS + "isDefinedBy")
        if defined_by is None or defined_by.get(_RDF + "resource") != _PROV_O:
            continue
        name = _prov_local(about)
        url = f"https://www.w3.org/TR/prov-o/#{name}"
        prose = _prov_prose(node)
        if not prose:
            ends = _prov_relation(node)
            shape = "class" if pos else "property"
            prose = (f"PROV-O publishes no prose definition for this {shape}"
                     + (f"; it relates {ends}" if ends else "")
                     + f". The specification entry is {url}.")
        # The file merges its imports, so a term can appear more than once —
        # `Thing`, `SoftwareAgent`, `hadUsage`. The occurrence carrying prose is
        # the one worth keeping, and the first such occurrence wins so two runs
        # over one payload never disagree.
        if name not in found or found[name].definition.startswith("PROV-O publishes no"):
            found[name] = Term(name, _cut(prose), pos, url)
    dropped = ["the prov-aq, prov-dc, prov-dictionary and prov-links extensions, and the "
               "annotation properties the file describes itself with — this is PROV-O, "
               "which the payload marks with rdfs:isDefinedBy"]
    return sorted(found.values(), key=lambda t: t.name), dropped


def _jsonld_text(value) -> str:
    """One string out of a JSON-LD value that may be language-tagged."""
    if isinstance(value, dict):
        value = value.get("@value", "")
    if isinstance(value, list):
        value = value[0] if value else ""
    return _plain(str(value))


def parse_schemaorg(raw: bytes) -> tuple[list[Term], list[str]]:
    """Schema.org out of `schemaorg-current-https.jsonld`.

    Classes and properties: the 2,454 terms the registry entry counts. The
    enumeration MEMBERS in the same graph (`Monday`, `InStock`) are instances of
    those classes rather than terms of the vocabulary, and a check that answered
    "taken — Schema.org's Monday" would be noise standing where an answer goes.

    SUPERSEDED TERMS ARE SKIPPED. Schema.org marks its retired terms with
    `supersededBy` and keeps publishing them; adopting one would let this
    database answer a naming question with a word its own publisher has put
    down. That is the same ruling the rename ledger makes about our names."""
    graph = json.loads(raw.decode("utf-8"))["@graph"]
    terms: list[Term] = []
    superseded = 0
    for node in graph:
        ident = str(node.get("@id", ""))
        kinds = node.get("@type", [])
        kinds = kinds if isinstance(kinds, list) else [kinds]
        if not ident.startswith("schema:") or not ({"rdfs:Class", "rdf:Property"} & set(kinds)):
            continue
        if "schema:supersededBy" in node:
            superseded += 1
            continue
        name = _jsonld_text(node.get("rdfs:label")) or ident.split(":", 1)[-1]
        url = f"https://schema.org/{name}"
        prose = _jsonld_text(node.get("rdfs:comment"))
        terms.append(Term(name, _cut(prose or f"A Schema.org term published without a "
                                              f"description. Its page is {url}."),
                          _POS if "rdfs:Class" in kinds else None, url))
    dropped = [f"{superseded} superseded term(s) the publisher has retired",
               "the enumeration members (Monday, InStock) — instances of the classes, "
               "not terms of the vocabulary"]
    return sorted(terms, key=lambda t: t.name), dropped


INGESTERS: dict[str, Ingester] = {
    "prov-o": Ingester(
        "prov-o", "https://www.w3.org/ns/prov.rdf", ".rdf", parse_prov_o,
        "PROV-O is © W3C under the W3C Software and Document Licence — keep the "
        "notice and the copyright when these words travel.",
    ),
    "schemaorg": Ingester(
        "schemaorg", "https://schema.org/version/latest/schemaorg-current-https.jsonld",
        ".jsonld", parse_schemaorg,
        "Schema.org is CC BY-SA 3.0 — credit Schema.org, and note that share-alike "
        "reaches anything you derive from these terms, including a vocabulary you ship.",
    ),
}


def _registry(source_id: str) -> TaxonomySource | None:
    return next((s for s in SOURCES if s.id == source_id), None)


def origin_of(source_id: str) -> str:
    """What an ingested word's `origin` column says."""
    return ORIGIN_PREFIX + source_id


def source_citation(origin: str | None) -> dict | None:
    """Whose word this is, and what saying it obliges — for every surface that
    reports an adopted word. None where the origin is not a taxonomy, because
    an org's upstream word and a public standard's word are different custody
    and must not be reported as one thing."""
    if not origin or not origin.startswith(ORIGIN_PREFIX):
        return None
    source_id = origin[len(ORIGIN_PREFIX):]
    entry = _registry(source_id)
    if entry is None:
        return None
    ingester = INGESTERS.get(source_id)
    return {"source": source_id, "name": entry.name, "url": entry.url,
            "licence": entry.licence, "commercial": entry.commercial,
            "obligation": COMMERCIAL_MEANING[entry.commercial],
            "credit": ingester.credit if ingester else ""}


def ingested() -> list[dict]:
    """The taxonomies ingested HERE, with how many words each holds — the fact
    the words skill cites and `monty onto sources` marks its entries with."""
    if not db_path().exists():
        return []
    try:
        conn = connect(readonly=True)
        rows = conn.execute(
            "SELECT origin, COUNT(*) AS n FROM word WHERE origin LIKE ? "
            "GROUP BY origin ORDER BY origin", (ORIGIN_PREFIX + "%",)).fetchall()
    except sqlite3.OperationalError:
        return []
    out = []
    for row in rows:
        cited = source_citation(row["origin"]) or {"source": row["origin"], "name": row["origin"],
                                                   "licence": "unknown", "obligation": "",
                                                   "credit": "", "url": ""}
        out.append({**cited, "words": row["n"]})
    return out


def cache_file(source_id: str, root: Path | None = None) -> Path:
    """Where this source's payload is kept between runs."""
    root = root or find_root() or Path.cwd()
    return root / CACHE_REL / (source_id + INGESTERS[source_id].suffix)


def payload(source_id: str, *, refresh: bool = False,
            root: Path | None = None) -> tuple[bytes, Path, bool]:
    """The source's file as bytes, from the cache when it is there.

    Cached on the first fetch so every run after it is offline: a vocabulary
    gate that needs the network to answer "whose word is this" is a gate that
    fails on a plane. Raises ValueError carrying the repair."""
    ingester = INGESTERS[source_id]
    path = cache_file(source_id, root)
    if path.exists() and not refresh:
        return path.read_bytes(), path, False
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with urllib.request.urlopen(ingester.data, timeout=180) as response:
            raw = response.read()
    except Exception as e:  # noqa: BLE001 — every failure here is one answer
        raise ValueError(
            f"could not fetch {ingester.data}: {e}. Repair: check the network, or put "
            f"the file at {path} yourself — ingest reads the cache first, so a payload "
            "you already have is never fetched again.") from None
    path.write_bytes(raw)
    return raw, path, True


def _fold(terms: list[Term]) -> tuple[list[Term], list[str]]:
    """One row per name, read case-insensitively — which is how this gate reads
    a name. Schema.org spells 51 of its terms twice, once as a class and once as
    a property (`Distance` and `distance`); PROV-O spells three that way. Both
    rows would answer to one check, so the class is kept — it names the thing —
    and the folded names are reported rather than dropped quietly."""
    kept: dict[str, Term] = {}
    folded: list[str] = []
    for term in sorted(terms, key=lambda t: (t.pos != _POS, t.name.lower())):
        low = term.name.lower()
        if low in kept:
            folded.append(term.name)
            continue
        kept[low] = term
    return [kept[low] for low in sorted(kept)], sorted(folded)


def _no_ingester(source_id: str) -> str:
    have = ", ".join(sorted(INGESTERS))
    known = _registry(source_id) is not None
    if known:
        return (f"REFUSED — {source_id!r} is in the registry but has no ingester. "
                f"Ingestable today: {have}. An ingester is written per source because "
                "each publishes a different shape, and a parser nobody has run against "
                "the real payload is a guess.")
    return (f"REFUSED — {source_id!r} is not a registry id. Ingestable today: {have}; "
            "`monty onto sources` lists all 56, ingestable or not.")


def ingest(source_id: str, *, refresh: bool = False, root: Path | None = None) -> str:
    """Load one public taxonomy into the vocabulary as adopted words."""
    if source_id not in INGESTERS:
        return _no_ingester(source_id)
    entry = _registry(source_id)
    ingester = INGESTERS[source_id]
    if entry is None:
        # An ingester keyed to an id the registry does not carry would import
        # terms with no licence and no attribution behind them, which is the
        # one thing this file may never do.
        return (f"REFUSED — {source_id!r} has an ingester but no registry entry, so its "
                "licence and attribution are unknown. That is a defect in ingest.py, not "
                "in your workspace.")

    try:
        raw, path, fetched = payload(source_id, refresh=refresh, root=root)
    except ValueError as e:
        return f"REFUSED — {e}"
    try:
        terms, dropped = ingester.parse(raw)
    except Exception as e:  # noqa: BLE001 — a bad payload is data, not a traceback
        return (f"REFUSED — {path} did not parse as {source_id} ({type(e).__name__}: {e}). "
                f"A truncated download is the usual cause. Repair: monty onto sources "
                f"ingest {source_id} --refresh")
    if not terms:
        return (f"REFUSED — {path} parsed to no terms. Either the payload is not what "
                f"{source_id} publishes, or the publisher changed its shape; the parser "
                "is the thing to fix, and it is in ingest.py.")

    kept, folded = _fold(terms)
    origin = origin_of(source_id)
    conn = connect()
    # Wholesale, before anything is read back: a re-ingest is a refresh of the
    # standard, and rows from the last run are not evidence about this one.
    conn.execute("DELETE FROM word WHERE origin = ?", (origin,))
    taken = {row["name"].lower(): row["origin"]
             for row in conn.execute("SELECT name, origin FROM word")}
    try:
        retired = {row[0].lower() for row in conn.execute("SELECT was FROM renamed")}
    except sqlite3.OperationalError:
        retired = set()

    ours: list[str] = []
    elsewhere: list[str] = []
    revived: list[str] = []
    rows: list[tuple] = []
    for term in kept:
        low = term.name.lower()
        if low in taken:
            (ours if taken[low] is None else elsewhere).append(term.name)
        elif low in retired:
            revived.append(term.name)
        else:
            rows.append((term.name, "adopted", term.definition, term.pos, origin))
    conn.executemany(
        "INSERT INTO word (name, kind, definition, pos, origin) VALUES (?,?,?,?,?)", rows)
    conn.commit()

    report = [f"ingested  {len(rows)} term(s) from {entry.name} as adopted words "
              f"(origin {origin})",
              f"  payload  {path} ({'fetched now' if fetched else 'cached'}"
              f"{'' if fetched else ' — --refresh re-fetches'})",
              f"  licence  {entry.licence} — {entry.commercial}: "
              f"{COMMERCIAL_MEANING[entry.commercial]}",
              f"  credit   {ingester.credit}"]
    for line in dropped:
        report.append(f"  skipped  {line}")
    if folded:
        report.append(f"  folded   {len(folded)} name(s) the source spells twice, once as a "
                      f"class and once as a property; the class was kept because this gate "
                      f"reads a name case-insensitively: {', '.join(folded[:8])}"
                      + (" …" if len(folded) > 8 else ""))
    if ours:
        report.append(f"  LOCAL WINS  {len(ours)} name(s) this repo already owns; the ingest "
                      f"left every one of them alone: {', '.join(ours[:8])}"
                      + (" …" if len(ours) > 8 else "")
                      + ". Rule on each one deliberately — `monty onto collide <term> "
                      f"{source_id} \"<their meaning>\" \"<the ruling>\"`.")
    if elsewhere:
        report.append(f"  ALREADY ADOPTED  {len(elsewhere)} name(s) belong to another "
                      f"ingested source and were left with it: {', '.join(elsewhere[:8])}"
                      + (" …" if len(elsewhere) > 8 else "")
                      + ". One name means one thing here, whoever said it first.")
    if revived:
        report.append(f"  RETIRED  {len(revived)} name(s) this repo has renamed away and did "
                      f"not take back: {', '.join(revived[:8])}"
                      + (" …" if len(revived) > 8 else ""))
    report.append(f"  read it  monty onto check {kept[0].name}   ·   monty onto list adopted")
    report.append("  note     adopted words are stored, not resident: `monty sync` cites the "
                  "source, the count and the licence on the words skill rather than spending "
                  "every agent's context on rows nobody reads one at a time.")
    return "\n".join(report)
