"""Every registry writes to tmp — a test that touches the real dbs is a bug."""
import sys
from pathlib import Path

import pytest

for pkg in ("ontology", "zoo", "warehouse", "gen", "cli", "tools/dataforseo",
            "tools/scrapecreators", "tools/crawl", "server"):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / pkg / "src"))


@pytest.fixture()
def onto_db(tmp_path, monkeypatch):
    from montology_ontology import db as odb

    monkeypatch.setattr(odb, "DB_PATH", tmp_path / "ontology.db")
    return odb


@pytest.fixture()
def zoo_db(tmp_path, monkeypatch):
    from montology_zoo import db as zdb, seed as zseed

    monkeypatch.setattr(zdb, "DB_PATH", tmp_path / "zoo.db")
    return zdb, zseed


@pytest.fixture()
def warehouse(tmp_path, monkeypatch):
    from montology_warehouse import db as wdb

    monkeypatch.setattr(wdb, "WAREHOUSE_PATH", tmp_path / "warehouse.duckdb")
    monkeypatch.setattr(wdb, "_REGISTRIES", {})
    return wdb
