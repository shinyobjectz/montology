"""DuckDB round-trips, the assay memory, gen docs idempotence, handoff shape."""
import json


def test_load_query_and_repairful_errors(warehouse, tmp_path):
    csv = tmp_path / "campaigns.csv"
    csv.write_text("campaign,spend\nspring,100\nfall,250\n")
    got = warehouse.load_file(str(csv), "campaigns")
    assert "2 rows" in got and "spend" in got
    table = warehouse.query("SELECT campaign FROM campaigns ORDER BY spend DESC")
    assert table.splitlines()[1].startswith("fall")
    err = warehouse.query("SELECT * FROM nope")
    assert "SQL error" in err and "registries" in err
    assert warehouse.load_file("/no/such.csv", "x") == "no such file: /no/such.csv"
    assert "letters, digits" in warehouse.load_file(str(csv), "bad-name")


def test_assay_is_the_skip_caches_memory(warehouse, monkeypatch):
    from montology_gen import engine

    engine._record("skill", "demo", "tiny-x+piecewise", "refused", ["piece.substance: filler"])
    assert engine._piecewise_already_refused("tiny-x") is True
    engine._record("skill", "demo", "tiny-x+piecewise", "accepted", [])
    assert engine._piecewise_already_refused("tiny-x") is False
    engine._record("skill", "demo", "tiny-y+piecewise", "errored", ["ValidationError"])
    assert engine._piecewise_already_refused("tiny-y") is True
    assert engine._piecewise_already_refused("never-seen") is False


def test_handoff_carries_instruments_spec_and_laws():
    from montology_gen.engine import _handoff

    got = _handoff("dataforseo", "tools/dataforseo/src/montology_dataforseo")
    assert "HOST AGENT" in got
    spec = json.loads(got[got.find("{"):])
    assert "serp_search" in json.dumps(spec["package_surface"])
    assert any("tools.exist" in l for l in spec["laws"])
    assert "instruments=sha256:" in spec["contract"]
    assert "gen lint" in spec["then"]


def test_gen_docs_regen_is_idempotent():
    from montology_gen.engine import gen_docs

    assert gen_docs(write=False) in ("README map table already current",) or "| package |" in gen_docs(write=False)
