"""The second tier: every ontology OBO Foundry publishes, as ITS PUBLISHER
describes it — harvested, never read.

`sources` is the shortlist and stays one: 56 entries somebody opened, and
the reason a registry that lists everything is a search engine nobody
needs. But "nothing here fits" is a different question from "what should I
join", and answering it from a 56-row list means answering it wrong. OBO
Foundry publishes 267 records in one machine-readable file; this indexes
them so `--search` can say "there is a phenotype ontology, go and look"
without anyone pretending to have vouched for it.

THE TWO TIERS MEAN DIFFERENT THINGS AND MUST NEVER BE PRINTED AS ONE.

  * tier 1 — the shortlist. Read, with a relevance ruling and a commercial
    verdict checked against the source. "Use this."
  * tier 2 — this. A title, a blurb and a licence label lifted verbatim
    out of somebody else's registry. Nobody here opened it, nobody here
    checked the licence against the LICENSE file, and the commercial
    verdict `sources` carries is deliberately absent rather than guessed.
    "This exists. Here is what its publisher claims."

WHAT IS DROPPED, AND WHY IT IS COUNTED. Three filters run; all three report
a tally, including the ones that caught nothing, rather than quietly
shrinking the list — a harvest that says 177 when the file holds 267 has to
say where the other 90 went, or the number is a claim instead of a
measurement.

  * not active — OBO marks a record `inactive` or `orphaned` when it is
    unmaintained or has lost its maintainer. Indexing those hands people a
    dead ontology with no signal that it is dead.
  * no declared licence — an entry you cannot use is not a finding here
    the way it is in `sources`, where `unlicensed` is a CHECKED verdict.
    A registry record with no licence field is an unchecked blank, and
    this tier has no business turning a blank into a verdict.
  * already in the shortlist — 14 OBO ontologies are tier 1 entries.
    Listing them twice would put a vetted ruling and an unvetted claim
    beside each other under the same id, which is exactly the confusion
    the tier split exists to prevent.

The fetched JSON is cached under `.monty/cache/`, which is gitignored and
refetchable by definition. After the first run the index works offline;
`--refresh` re-fetches, and a refresh that cannot reach the network falls
back to the cache and SAYS the answer is stale rather than failing on a
question the disk could already answer.

None of this is legal advice, and the licences here are weaker evidence
than the shortlist's — they are labels off a third-party registry, not
verdicts anyone reached.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from montology_core import workspace_root

from .sources import SOURCES, TaxonomySource

#: The whole OBO Foundry registry in one document — 267 records, one fetch.
OBO_REGISTRY = "https://obofoundry.org/registry/ontologies.jsonld"

#: Under `.monty/cache/`, which .gitignore already excludes: this is a copy
#: of someone else's file, refetchable on demand, and tracking it would put
#: 600KB of third-party registry into every clone for no gain.
CACHE = Path("cache") / "obo-registry.jsonld"

#: The three filters, in the order they run and the order they report. They
#: are constants rather than strings written at the point of the drop because
#: `render_harvest` prints them verbatim: the tally IS the explanation.
FILTERS: tuple[str, ...] = (
    "not active — OBO calls it inactive or orphaned",
    "no declared licence — a blank field, not a checked verdict",
    "already in the shortlist, where it carries a real ruling",
)

#: Printed above tier-2 results, every time, because a reader who lands on
#: the second block without the first has no way to know the two lists were
#: assembled to different standards.
UNVETTED = ("harvested from OBO Foundry — the publisher's own words, not a "
            "recommendation. Nothing below was read or licence-checked here.")


@dataclass(frozen=True, slots=True)
class IndexEntry:
    """One harvested record. Every field is the registry's, verbatim."""

    id: str            # the OBO prefix — `hp`, `chebi`, `pato`
    name: str          # `title`, as published
    domain: str        # OBO's own bucket — `health`, `phenotype`, `upper`
    blurb: str         # `description`, untouched; long, and searched whole
    licence: str       # the label the record declares, and only that
    url: str           # `ontology_purl` — where the OWL actually lives
    homepage: str


@dataclass(frozen=True, slots=True)
class Harvest:
    """The index plus the arithmetic that produced it: `fetched` is what the
    registry held, `skipped` is where the difference went, reason by reason."""

    entries: tuple[IndexEntry, ...]
    fetched: int
    skipped: dict[str, int] = field(default_factory=dict)
    origin: str = ""       # `obofoundry.org`, `cache`, or a stale-cache note
    fetched_on: str = ""   # when the cached copy was written, UTC date


def cache_path(root: Path | None = None) -> Path:
    """Where this workspace keeps its copy of the registry."""
    return (root or workspace_root()) / ".monty" / CACHE


def _registry(refresh: bool = False, root: Path | None = None) -> tuple[dict, str]:
    """The registry document and where it came from.

    Raises ValueError with the repair when there is neither network nor
    cache — the one state the index genuinely cannot answer from.
    """
    path = cache_path(root)
    if path.exists() and not refresh:
        return json.loads(path.read_text()), "cache"
    try:
        with urllib.request.urlopen(OBO_REGISTRY, timeout=60) as r:
            raw = r.read().decode()
        json.loads(raw)  # never overwrite a good cache with an error page
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(raw)
        return json.loads(raw), "obofoundry.org"
    except Exception as e:  # noqa: BLE001 — the network is data, not a crash
        if path.exists():
            return (json.loads(path.read_text()),
                    f"cache — STALE, the refresh failed ({type(e).__name__})")
        raise ValueError(
            f"could not reach {OBO_REGISTRY} ({e}) and nothing is cached at "
            f"{path}. Repair: run this once with a network, and every run "
            "after it works offline.") from None


def harvest(refresh: bool = False, root: Path | None = None) -> Harvest:
    """The index, with what was dropped and why."""
    doc, origin = _registry(refresh, root)
    records = doc.get("ontologies", [])
    curated = {s.id for s in SOURCES}
    entries: list[IndexEntry] = []
    # Seeded, so a filter that caught nothing today still reports itself. A
    # reason that only appears when it fires cannot be told apart from a
    # filter somebody deleted, and "0 dropped for no licence" is the whole
    # evidence that the licence check ran at all.
    skipped = dict.fromkeys(FILTERS, 0)

    for r in records:
        if r.get("activity_status") != "active":
            skipped[FILTERS[0]] += 1
            continue
        licence = ((r.get("license") or {}).get("label") or "").strip()
        if not licence:
            skipped[FILTERS[1]] += 1
            continue
        if r.get("id") in curated:
            skipped[FILTERS[2]] += 1
            continue
        entries.append(IndexEntry(
            id=r.get("id", ""),
            name=r.get("title", "") or r.get("id", ""),
            domain=r.get("domain", "") or "unstated",
            blurb=" ".join((r.get("description") or "").split()),
            licence=licence,
            url=r.get("ontology_purl", "") or r.get("homepage", ""),
            homepage=r.get("homepage", ""),
        ))

    path = cache_path(root)
    stamped = (datetime.fromtimestamp(path.stat().st_mtime, UTC).date().isoformat()
               if path.exists() else "")
    return Harvest(tuple(sorted(entries, key=lambda e: e.id)),
                   len(records), skipped, origin, stamped)


def _hit(query: str, *fields: str) -> int:
    """How well one row answers `query`, or 0. Rank is where the match
    landed, not how often — an id that IS the query beats a word buried in
    somebody's third paragraph, and counting occurrences would invert that
    for any record with a long enough description."""
    ident, name, domain, blurb = fields
    if ident == query:
        return 4
    if query in ident or query in name:
        return 3
    if query in domain:
        return 2
    return 1 if query in blurb else 0


def search(query: str, limit: int = 0, refresh: bool = False,
           root: Path | None = None) -> list[IndexEntry]:
    """Harvested entries matching `query` — id, title, domain, description.

    Substring, case-folded, and nothing cleverer: this tier is a finding
    aid, and a fuzzy match here would dress an unvetted row up as a
    judgement about what the searcher meant.
    """
    q = query.strip().casefold()
    if not q:
        return []
    scored = [(_hit(q, e.id.casefold(), e.name.casefold(),
                    e.domain.casefold(), e.blurb.casefold()), e)
              for e in harvest(refresh, root).entries]
    ranked = sorted(((s, e) for s, e in scored if s),
                    key=lambda pair: (-pair[0], pair[1].id))
    return [e for _, e in (ranked[:limit] if limit else ranked)]


def search_sources(query: str) -> list[TaxonomySource]:
    """Shortlist entries matching `query` — id, name, group and the ruling.

    The `why` text is searched too, which the harvested tier has no
    counterpart for: it is the one place a shortlist entry says what it is
    FOR, so 'sbom' finds cyclonedx even though neither its id nor its name
    contains the word.
    """
    q = query.strip().casefold()
    if not q:
        return []
    return [s for s in SOURCES
            if q in s.id.casefold() or q in s.name.casefold()
            or q in s.group.casefold() or q in s.why.casefold()]


def render_harvest(refresh: bool = False, root: Path | None = None) -> list[str]:
    """The harvest as lines: how many came in, how many stayed, where the
    rest went. Printed by `--refresh`, because a refresh whose only output
    is silence gives nobody a reason to believe it did anything."""
    try:
        got = harvest(refresh, root)
    except ValueError as e:
        return [f"REFUSED — {e}"]
    out = [f"harvested index — {len(got.entries)} of {got.fetched} OBO Foundry "
           f"records (from {got.origin}"
           + (f", fetched {got.fetched_on}" if got.fetched_on else "") + ")"]
    for reason in FILTERS:
        out.append(f"  skipped {got.skipped.get(reason, 0):4}  {reason}")
    out.append(f"  cached at   {cache_path(root)}")
    return out


def render_search(query: str, limit: int = 20,
                  root: Path | None = None) -> list[str]:
    """Both tiers for one query, labelled — what `monty onto sources
    --search` prints. The shortlist comes first and says it was read; the
    index follows and says it was not."""
    if not query.strip():
        return ["nothing to search for. Try: monty onto sources --search phenotype"]

    out: list[str] = []
    vouched = search_sources(query)
    out.append(f"\n── shortlist — read, ruled on, licence-checked ({len(vouched)}) ──")
    if not vouched:
        out.append("  nothing. The shortlist is 56 entries; most queries miss it.")
    for s in vouched:
        flag = "" if s.status == "ready" else "   [evaluate]"
        out.append(f"  {s.id:24} {s.name}{flag}")
        out.append(f"  {'':24} {s.commercial} · {s.licence}")
        out.append(f"  {'':24} {s.url}")

    try:
        found = search(query, root=root)
    except ValueError as e:
        out.append("\n── harvested index ──")
        out.append(f"  REFUSED — {e}")
        return out

    hits = found[:limit] if limit else found
    more = f", showing {len(hits)}" if len(found) > len(hits) else ""
    out.append(f"\n── harvested index — UNVETTED ({len(found)}{more}) ──")
    if hits:
        out.append(f"  {UNVETTED}")
    for e in hits:
        out.append(f"  {e.id:24} {e.name}   [{e.domain}]")
        out.append(f"  {'':24} licence AS DECLARED BY ITS PUBLISHER: {e.licence}")
        out.append(f"  {'':24} {_trim(e.blurb)}")
        out.append(f"  {'':24} {e.homepage}")
    if not hits:
        out.append("  nothing.")
    return out


def _trim(text: str, width: int = 96) -> str:
    """One line of somebody's abstract. The full text stays in the entry and
    is what search reads — this only decides how much of it a terminal row
    is worth, and a description runs to 650 characters."""
    return text if len(text) <= width else text[: width - 1].rstrip() + "…"
