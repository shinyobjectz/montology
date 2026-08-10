"""Fetch registered taxonomy sources into the database.

FETCHED, NOT VENDORED. IAB Tech Lab and Google license their taxonomies for
use with attribution; this repo ships the pointer and the parser, and the
data lands on the user's disk at pull time. That keeps a public repo clean
and the data current.

Each format gets one parser; a source whose parser is not written yet says
so instead of pretending (errors carry their repair).
"""

from __future__ import annotations

import csv
import io

import httpx

from .db import connect
from .sources import SOURCES, TaxonomySource, by_status, get


def pull(source_id: str | None = None) -> list[str]:
    """Pull one source by id, or every ``core`` source. Returns report lines."""
    if source_id:
        src = get(source_id)
        if src is None:
            known = ", ".join(s.id for s in SOURCES)
            return [f"no source named {source_id!r}. Known: {known}"]
        if src.status == "skip":
            return [f"{src.id} is status=skip — {src.why}"]
        targets = [src]
    else:
        targets = list(by_status("core"))

    conn = connect()
    report = []
    for src in targets:
        try:
            n = _ingest(src, conn)
            report.append(f"{src.id}: {n} rows")
        except NotImplementedError as e:
            report.append(f"{src.id}: not pulled — {e}")
        except httpx.HTTPError as e:
            report.append(f"{src.id}: fetch failed ({e}) — check the URL in sources.py, or retry")
    conn.commit()
    return report


def _ingest(src: TaxonomySource, conn) -> int:
    if src.id == "schemaorg":
        return _ingest_schemaorg(src, conn)
    if src.id in ("naics", "sic"):
        return _ingest_code_tarball(src, conn)
    if src.id == "shopify-product":
        return _ingest_shopify(src, conn)
    if src.id == "openooh-venue":
        return _ingest_openooh(src, conn)
    if src.id == "google-nlp-categories":
        return _ingest_google_nlp(src, conn)
    if src.fmt == "tsv":
        return _ingest_iab_tsv(src, conn)
    if src.fmt == "txt" and src.id == "google-product":
        return _ingest_google_product(src, conn)
    if src.fmt == "markdown" and src.id == "google-topics":
        return _ingest_google_topics(src, conn)
    raise NotImplementedError(
        f"no parser for fmt={src.fmt} yet — add one in pull.py (they are ~20 lines each)"
    )


def _ingest_schemaorg(src: TaxonomySource, conn) -> int:
    """The Schema.org JSON-LD graph: every Class and Property becomes a row.

    code = the bare @id (schema:Thing -> Thing), parent = first subClassOf /
    subPropertyOf, path = 'Class' or 'Property' plus the parent for display.
    """
    import json as _json

    graph = _json.loads(_fetch(src.url)).get("@graph", [])
    n = 0
    for node in graph:
        types = node.get("@type", [])
        types = types if isinstance(types, list) else [types]
        is_class = "rdfs:Class" in types
        is_prop = "rdf:Property" in types
        if not (is_class or is_prop):
            continue
        code = str(node.get("@id", "")).removeprefix("schema:")
        label = node.get("rdfs:label", "")
        label = label.get("@value", "") if isinstance(label, dict) else str(label)
        if not code or not label:
            continue
        parent_key = "rdfs:subClassOf" if is_class else "rdfs:subPropertyOf"
        parents = node.get(parent_key, [])
        parents = parents if isinstance(parents, list) else [parents]
        parent = str(parents[0].get("@id", "")).removeprefix("schema:") if parents else None
        kind = "Class" if is_class else "Property"
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
            (src.id, code, label, parent, None,
             f"{kind}" + (f" < {parent}" if parent else "")),
        )
        n += 1
    return n


def _ingest_code_tarball(src: TaxonomySource, conn) -> int:
    """CompileInc NAICS/SIC: a repo tarball of per-code TOML files
    (`code = "11"` / `name = "..."`). Parent = the code minus its last digit
    when that code exists — the hierarchy IS the code string."""
    import io
    import tarfile
    import tomllib

    raw = httpx.get(src.url, follow_redirects=True, timeout=120).content
    rows: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not member.name.endswith(".toml"):
                continue
            f = tar.extractfile(member)
            if f is None:
                continue
            try:
                data = tomllib.loads(f.read().decode())
            except (tomllib.TOMLDecodeError, UnicodeDecodeError):
                continue
            code, name = str(data.get("code", "")), str(data.get("name", ""))
            if code and name:
                rows[code] = name
    n = 0
    for code, name in rows.items():
        parent = next((code[:i] for i in range(len(code) - 1, 1, -1) if code[:i] in rows), None)
        conn.execute("INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
                     (src.id, code, name, parent, len(code) - 1, f"{code} {name}"))
        n += 1
    return n


def _ingest_shopify(src: TaxonomySource, conn) -> int:
    """Shopify dist taxonomy.json: verticals -> categories with full_name."""
    import json as _json

    data = _json.loads(_fetch(src.url))
    n = 0
    for vertical in data.get("verticals", []):
        for cat in vertical.get("categories", []):
            code = str(cat.get("id", "")).rsplit("/", 1)[-1]
            parent = cat.get("parent_id")
            parent = str(parent).rsplit("/", 1)[-1] if parent else None
            full = cat.get("full_name", cat.get("name", ""))
            if not code or not full:
                continue
            conn.execute("INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
                         (src.id, code, cat.get("name", full), parent,
                          int(cat.get("level", 0)) + 1, full.replace(" > ", " > ")))
            n += 1
    return n


def _ingest_openooh(src: TaxonomySource, conn) -> int:
    """OpenOOH specification.json: nested categories with enumeration ids."""
    import json as _json

    spec = _json.loads(_fetch(src.url))["openooh_venue_taxonomy"]["specification"]

    n = 0

    def walk(cats, parent_code, path):
        nonlocal n
        for cat in cats or []:
            code = str(cat.get("enumeration_id", cat.get("name", "")))
            name = cat.get("name", "")
            here = f"{path} > {name}" if path else name
            conn.execute("INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
                         (src.id, code, name, parent_code,
                          here.count(">") + 1, here))
            n += 1
            walk(cat.get("children"), code, here)

    walk(spec.get("categories"), None, "")
    return n


def _ingest_google_nlp(src: TaxonomySource, conn) -> int:
    """The categories page: scrape /Path/Like/This strings from the HTML."""
    import re as _re

    html = _fetch(src.url)
    paths = sorted({m for m in _re.findall(r"(/[A-Z][\w&' ]+(?:/[\w&'\-, ]+)*)", html)
                    if m.count("/") >= 1 and "http" not in m and len(m) < 120})
    n = 0
    for path in paths:
        parts = [p for p in path.split("/") if p]
        if not parts:
            continue
        parent = "/" + "/".join(parts[:-1]) if len(parts) > 1 else None
        conn.execute("INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
                     (src.id, path, parts[-1], parent, len(parts), " > ".join(parts)))
        n += 1
    return n


def _fetch(url: str) -> str:
    r = httpx.get(url, follow_redirects=True, timeout=60)
    r.raise_for_status()
    return r.text


def _ingest_iab_tsv(src: TaxonomySource, conn) -> int:
    """IAB TSVs: Unique ID / Parent / Name / Tier 1..4 columns."""
    text = _fetch(src.url)
    rows = list(csv.reader(io.StringIO(text), delimiter="\t"))
    header = next((i for i, r in enumerate(rows) if r and "unique id" in r[0].lower()), 0)
    cols = [c.strip().lower() for c in rows[header]]

    def col(row, *names):
        for n in names:
            if n in cols:
                got = row[cols.index(n)].strip() if cols.index(n) < len(row) else ""
                if got:
                    return got
        return ""

    n = 0
    for row in rows[header + 1:]:
        if not row or not col(row, "unique id"):
            continue
        code = col(row, "unique id")
        tiers = [col(row, f"tier {i}") for i in range(1, 5)]
        tiers = [t for t in tiers if t]
        name = col(row, "name") or (tiers[-1] if tiers else "")
        if not name:
            continue
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
            (src.id, code, name, col(row, "parent") or None,
             len(tiers) or None, " > ".join(tiers) or None),
        )
        n += 1
    return n


def _ingest_google_product(src: TaxonomySource, conn) -> int:
    """Google's taxonomy.txt: one 'A > B > C' path per line."""
    n = 0
    for line in _fetch(src.url).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split(">")]
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
            (src.id, line, parts[-1],
             " > ".join(parts[:-1]) or None, len(parts), line),
        )
        n += 1
    return n


def _ingest_google_topics(src: TaxonomySource, conn) -> int:
    """The Topics API taxonomy markdown: a |ID|path| table."""
    n = 0
    for line in _fetch(src.url).splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0].isdigit():
            continue
        path = cells[1].strip("/").replace("/", " > ")
        parts = [p.strip() for p in path.split(">")]
        conn.execute(
            "INSERT OR REPLACE INTO taxonomy VALUES (?,?,?,?,?,?)",
            (src.id, cells[0], parts[-1],
             " > ".join(parts[:-1]) or None, len(parts), path),
        )
        n += 1
    return n
