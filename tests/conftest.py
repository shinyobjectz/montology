"""Offline fixtures: every db pinned into tmp, the workspace pinned by env."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for member in ("core", "onto", "scan", "gen", "cli"):
    sys.path.insert(0, str(ROOT / ".monty" / member / "src"))


@pytest.fixture()
def onto_db(tmp_path, monkeypatch):
    from montology_ontology import db as odb

    monkeypatch.setattr(odb, "DB_PATH", tmp_path / "ontology.db")
    return odb
