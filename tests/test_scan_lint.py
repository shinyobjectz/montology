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


def test_collision_is_advisory_by_default(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "what a tenant holds", kind="core", pos="noun")
    report = lint(repo)
    assert any(r.startswith("warn") and "Atlas" in r and "advisory" in r for r in report)
    assert report[-1].startswith("ok") and "advisory collision" in report[-1]


def test_collision_fails_with_repair(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "what a tenant holds", kind="core", pos="noun")
    (repo / ".monty" / "montology.toml").write_text('[scan]\ncollisions = "enforce"\n')
    report = lint(repo)
    fails = [r for r in report if r.startswith("FAIL")]
    assert any("a.py" in f and "Atlas" in f and "rename" in f.lower() for f in fails)
    assert report[-1].startswith("FAIL")


def test_allow_records_the_exception(repo, onto_db):
    from montology_scan import lint

    onto_db.add("atlas", "what a tenant holds", kind="core", pos="noun")
    (repo / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\ncollisions = "enforce"\nallow = ["atlas"]\n')
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


def test_migrate_variants_cover_the_case_shapes():
    from montology_scan.rename import _variants

    got = _variants("artifact", "dossier")
    assert ("artifact", "dossier") in got
    assert ("Artifact", "Dossier") in got
    assert ("ARTIFACT", "DOSSIER") in got


def test_migrate_rewrites_every_position_a_name_occupies(repo):
    from montology_scan import migrate

    got = migrate("atlas", "chart", root=repo)
    assert "occurrence(s)" in got and "--apply" in got
    got = migrate("atlas", "chart", apply=True, root=repo)
    assert "REWRITTEN" in got
    assert "class Chart" in (repo / "a.py").read_text()          # class position
    assert "function chart()" in (repo / "b.ts").read_text()     # ts identifier
    # strings and comments are structurally untouchable
    (repo / "s.py").write_text('x = "atlas"  # atlas\natlas = 1\n')
    migrate("atlas", "chart", apply=True, root=repo)
    text = (repo / "s.py").read_text()
    assert 'x = "atlas"' in text and "# atlas" in text and "chart = 1" in text


def test_drift_measures_history(tmp_path):
    import subprocess

    from montology_scan import measure_history, render_drift

    repo = tmp_path / "r"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    env = ["git", "-c", "user.email=t@t", "-c", "user.name=t", "-C", str(repo)]
    (repo / "a.py").write_text("class One:\n    pass\n")
    subprocess.run([*env, "add", "-A"], check=True)
    subprocess.run([*env, "commit", "-qm", "one"], check=True)
    (repo / "b.css").write_text(".x { color: #061a1c; } .y { color: #ff0000; }")
    (repo / "a.py").write_text("class One:\n    pass\n\nclass Two:\n    pass\n")
    subprocess.run([*env, "add", "-A"], check=True)
    subprocess.run([*env, "commit", "-qm", "two"], check=True)

    rows = measure_history(repo, samples=2)
    assert len(rows) == 2
    assert rows[0]["decls"] == 1 and rows[1]["decls"] == 2
    assert rows[0]["colors"] == 0 and rows[1]["colors"] == 2
    out = "\n".join(render_drift(rows))
    assert "drift:" in out and "lexicon 1" in out


def test_exclude_matches_the_globs_it_documents(tmp_path, monkeypatch):
    """Every workspace writes `exclude` in globs — `**/dist/**`, `_archive/**`
    — and for a long time only a BARE NAME did anything, so every glob matched
    nothing. The worst way for a filter to fail: the scan reported a confident
    count over files nobody meant to include. qubie's config claimed to drop
    2,159 vendor declarations and dropped none of them.
    """
    from montology_scan.surface import _iter_files

    (tmp_path / ".monty").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "real.py").write_text("class Real: pass")
    (tmp_path / "build" / "dist").mkdir(parents=True)
    (tmp_path / "build" / "dist" / "bundle.py").write_text("class Bundled: pass")
    (tmp_path / "_archive").mkdir()
    (tmp_path / "_archive" / "old.py").write_text("class Old: pass")
    (tmp_path / "vendored.min.js").write_text("var a=1")
    (tmp_path / ".monty" / "montology.toml").write_text(
        'name = "t"\n[scan]\nexclude = ["**/dist/**", "_archive/**", "**/*.min.js"]\n')

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    got = {p.name for p in _iter_files(tmp_path)}
    assert got == {"real.py"}


def test_no_exclude_reads_everything(tmp_path, monkeypatch):
    from montology_scan.surface import _iter_files

    (tmp_path / ".monty").mkdir()
    (tmp_path / "a.py").write_text("class A: pass")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.py").write_text("class B: pass")
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    assert {p.name for p in _iter_files(tmp_path)} == {"a.py", "b.py"}
