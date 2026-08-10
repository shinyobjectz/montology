"""The org ontology: one vocabulary, N repos — custody proven."""

import sqlite3

import pytest


@pytest.fixture()
def org(tmp_path):
    """An org workspace whose db IS the artifact."""
    from montology_ontology import db as odb

    org_db = tmp_path / "org" / ".monty" / "ontology.db"
    org_db.parent.mkdir(parents=True)
    conn = odb.connect(org_db)
    conn.execute("INSERT INTO word (name, kind, owner, definition, test, note, code) "
                 "VALUES ('thread','core',NULL,'a stateful session','what a session is',NULL,'atl.thread')")
    conn.execute("INSERT INTO word (name, kind, owner, definition, test, note, code) "
                 "VALUES ('atlas','core',NULL,'what a tenant holds',NULL,NULL,'atl')")
    conn.execute("INSERT INTO token (name, category, value, note) "
                 "VALUES ('brand-primary','color','#061a1c',NULL)")
    conn.execute("INSERT INTO renamed (was, now, renamed_on, why) "
                 "VALUES ('artifact','dossier','2026-08-10','one word')")
    conn.commit()
    return tmp_path / "org"


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    from montology_ontology import db as odb

    r = tmp_path / "repo"
    (r / ".monty").mkdir(parents=True)
    (r / ".monty" / "montology.toml").write_text('name = "repo"\n')
    monkeypatch.setattr(odb, "DB_PATH", r / ".monty" / "ontology.db")
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(r))
    return r


def test_pull_inherits_and_pins(org, repo):
    from montology_ontology import pinned_upstream, pull, tokens, words

    got = pull(str(org), repo)
    assert got.startswith("inherited")
    assert {w["name"] for w in words()} == {"thread", "atlas"}
    assert tokens("color")[0]["name"] == "brand-primary"
    assert pinned_upstream(repo) == str(org)
    # the rename crosses the fleet with the exact command
    assert "monty migrate artifact dossier --apply" in got


def test_local_rows_survive_refresh_and_conflicts_are_loud(org, repo):
    from montology_ontology import add, pull, words
    from montology_ontology import db as odb

    pull(str(org), repo)
    add("journal", "the local repo's own word")
    # upstream evolves: new word + a redefined thread
    conn = sqlite3.connect(org / ".monty" / "ontology.db")
    conn.execute("INSERT INTO word (name, kind, definition) VALUES ('plan','core','a proposal')")
    conn.execute("UPDATE word SET definition='REDEFINED' WHERE name='thread'")
    conn.commit()
    got = pull(str(org), repo)  # pinned — no source arg needed after first pull? explicit here
    names = {w["name"]: w for w in words()}
    assert "journal" in names               # local survived
    assert "plan" in names                  # upstream addition arrived
    assert names["thread"]["definition"] == "REDEFINED"   # upstream refresh applied

    # a name defined in BOTH places: local wins, loudly
    local = odb.connect()
    local.execute("INSERT OR REPLACE INTO word (name, kind, definition, origin) "
                  "VALUES ('atlas','custom','our own atlas meaning',NULL)")
    local.commit()
    got = pull(str(org), repo)
    assert "CONFLICTS" in got and "word:atlas" in got
    assert words(None) and {w["name"]: w for w in words()}["atlas"]["definition"] == "our own atlas meaning"


def test_pull_without_pin_carries_repair(repo):
    from montology_ontology import pull

    assert "monty onto pull <source>" in pull(None, repo)


def test_bad_sources_carry_repairs(repo):
    from montology_ontology import pull

    assert "REFUSED" in pull("/nonexistent/place", repo)
