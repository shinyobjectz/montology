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
    if src.fmt == "tsv":
        return _ingest_iab_tsv(src, conn)
    if src.fmt == "txt" and src.id == "google-product":
        return _ingest_google_product(src, conn)
    if src.fmt == "markdown" and src.id == "google-topics":
        return _ingest_google_topics(src, conn)
    raise NotImplementedError(
        f"no parser for fmt={src.fmt} yet — add one in pull.py (they are ~20 lines each)"
    )


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
