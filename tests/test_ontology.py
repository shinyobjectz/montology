"""Authoring, mapping, and every parser — offline, from fixture payloads."""
import io
import tarfile

import importlib

from montology_ontology import db as odb
from montology_ontology.sources import SOURCES, TaxonomySource

opull = importlib.import_module("montology_ontology.pull")


def test_add_check_map_loop(onto_db):
    assert onto_db.check("flight") == []
    got = onto_db.add("flight", "the dated window a campaign's ads run in")
    assert got.startswith("added")
    assert onto_db.add("flight", "again") .startswith("REFUSED")
    conn = onto_db.connect()
    conn.execute("INSERT OR REPLACE INTO taxonomy VALUES ('iab-content','634','Travel',NULL,1,'Travel')")
    conn.commit()
    assert onto_db.map_word("flight", "iab-content", "634").startswith("mapped")
    assert onto_db.map_word("flight", "iab-content", "999").startswith("REFUSED")
    assert onto_db.map_word("ghost", "iab-content", "634").startswith("REFUSED")
    findings = onto_db.check("flight")
    assert any("maps to iab-content:634" in f for f in findings)


def test_add_owner_and_code_rules(onto_db):
    onto_db.add("campaign", "a grouping of ads measured together")
    assert onto_db.add("flightx", "d", owner="nope").startswith("REFUSED")
    assert onto_db.add("flighty", "a dated window", owner="campaign", code="cmp.flight").startswith("added")
    assert onto_db.add("other", "d", code="cmp.flight").startswith("REFUSED")


def _run_parser(onto_db, monkeypatch, source_id, fixture, binary=None):
    src = next(s for s in SOURCES if s.id == source_id)
    monkeypatch.setattr(opull, "_fetch", lambda url: fixture)
    if binary is not None:
        class R:  # tarball path uses httpx.get(...).content
            content = binary
        monkeypatch.setattr(opull.httpx, "get", lambda *a, **k: R())
    conn = onto_db.connect()
    n = opull._ingest(src, conn)
    conn.commit()
    return n, conn


def test_iab_tsv_parser(onto_db, monkeypatch):
    tsv = "Unique ID\tParent\tName\tTier 1\tTier 2\n1\t\tAutomotive\tAutomotive\t\n2\t1\tAuto Body Styles\tAutomotive\tAuto Body Styles\n"
    n, conn = _run_parser(onto_db, monkeypatch, "iab-content", tsv)
    assert n == 2
    row = conn.execute("SELECT * FROM taxonomy WHERE code='2'").fetchone()
    assert row["parent"] == "1" and "Auto Body" in row["path"]


def test_google_product_and_topics_parsers(onto_db, monkeypatch):
    n, _ = _run_parser(onto_db, monkeypatch, "google-product",
                       "# comment\nHome & Garden > Kitchen & Dining > Cookware\n")
    assert n == 1
    n, _ = _run_parser(onto_db, monkeypatch, "google-topics",
                       "|ID|Topic|\n|---|---|\n|509|/Home & Garden/Kitchen|\n")
    assert n == 1


def test_schemaorg_parser(onto_db, monkeypatch):
    jsonld = '{"@graph": [{"@id": "schema:Organization", "@type": "rdfs:Class", "rdfs:label": "Organization", "rdfs:subClassOf": {"@id": "schema:Thing"}}]}'
    n, conn = _run_parser(onto_db, monkeypatch, "schemaorg", jsonld)
    assert n == 1
    row = conn.execute("SELECT * FROM taxonomy WHERE source='schemaorg'").fetchone()
    assert row["code"] == "Organization" and row["parent"] == "Thing"


def test_naics_tarball_parser(onto_db, monkeypatch):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for code, name in [("11", "Agriculture"), ("111", "Crop Production")]:
            data = f'code = "{code}"\nname = "{name}"\n'.encode()
            info = tarfile.TarInfo(f"repo/{code}.toml")
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    n, conn = _run_parser(onto_db, monkeypatch, "naics", "", binary=buf.getvalue())
    assert n == 2
    assert conn.execute("SELECT parent FROM taxonomy WHERE code='111'").fetchone()[0] == "11"


def test_shopify_and_openooh_parsers(onto_db, monkeypatch):
    shop = '{"verticals": [{"name": "x", "categories": [{"id": "gid://shopify/TaxonomyCategory/ap", "level": 0, "name": "Animals", "full_name": "Animals", "parent_id": null}]}]}'
    n, _ = _run_parser(onto_db, monkeypatch, "shopify-product", shop)
    assert n == 1
    oo = '{"openooh_venue_taxonomy": {"specification": {"categories": [{"name": "Transit", "enumeration_id": 1, "children": [{"name": "Airports", "enumeration_id": 101}]}]}}}'
    n, conn = _run_parser(onto_db, monkeypatch, "openooh-venue", oo)
    assert n == 2
    assert conn.execute("SELECT parent FROM taxonomy WHERE code='101'").fetchone()[0] == "1"


def test_skip_sources_refuse_to_pull(onto_db):
    skip = next(s for s in SOURCES if s.status == "skip")
    got = opull.pull(skip.id)
    assert "status=skip" in got[0]
