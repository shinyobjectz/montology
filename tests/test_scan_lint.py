"""The multiast sweep and the gate, against a polyglot fixture tree."""

from pathlib import Path

import pytest


@pytest.fixture()
def repo(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    (tmp_path / "a.py").write_text("class Atlas:\n    pass\n\ndef fetch_holdings():\n    pass\n")
    (tmp_path / "b.ts").write_text("interface Holding { id: string }\nfunction atlas(): void {}\n")
    (tmp_path / "c.go").write_text("package m\n\ntype Holding struct{}\n\nfunc Fetch() {}\n")
    (tmp_path / "d.rs").write_text("struct Ledger;\nfn holdings() {}\n")
    (tmp_path / "e.ex").write_text("defmodule Atlas.Holding do\n  def place(x), do: x\nend\n")
    return tmp_path


def test_declarations_across_languages(repo):
    from montology_scan import declarations

    got = declarations(repo)
    names = {(d["lang"], d["name"]) for d in got["decls"]}
    assert ("python", "Atlas") in names
    assert ("typescript", "Holding") in names
    assert ("go", "Holding") in names
    assert ("rust", "Ledger") in names
    assert ("elixir", "place") in names
    assert got["errors"] == 0


def test_collision_fails_with_repair(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "what a tenant holds", kind="core")
    report = lint(repo)
    fails = [r for r in report if r.startswith("FAIL")]
    assert any("a.py" in f and "Atlas" in f and "rename" in f.lower() for f in fails)
    assert report[-1].startswith("FAIL")


def test_allow_records_the_exception(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "what a tenant holds", kind="core")
    (repo / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\nallow = ["atlas"]\n')
    assert lint(repo)[-1].startswith("ok")


def test_custom_words_do_not_gate_by_default(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "their own meaning", kind="custom")
    assert lint(repo)[-1].startswith("ok")


def test_unresolvable_code_prefix_fails(repo, onto_db):
    from montology_scan import lint

    onto_db.add("harness", "the loop", code="har")
    onto_db.add("cell", "the sandbox", code="har.cell")
    conn = onto_db.connect()
    conn.execute("UPDATE word SET code='ghost.cell' WHERE name='cell'")
    conn.commit()
    report = lint(repo)
    assert any("ghost" in r and "prefix" in r for r in report)


def test_candidates_mine_the_vocabulary_the_code_wants(repo, onto_db):
    from montology_scan import candidates

    got = candidates(repo)
    names = [c["name"] for c in got]
    assert "holding" in names or "holdings" in names  # recurs across languages
    assert "main" not in names  # noise never surfaces


def test_missing_astgrep_carries_repair(monkeypatch):
    import shutil

    from montology_scan import sg

    monkeypatch.setattr(shutil, "which", lambda n: None)
    assert "brew install ast-grep" in sg("def $F($$$)", "python")
