"""Surfaces, seams and phantoms — the half that measures what we stand on.

The cases that matter are the ones this repo's own clean tree cannot show:
a dependency declared and never imported, and a word left bearing on it.
"""

import pytest


@pytest.fixture()
def repo(tmp_path):
    """A workspace with one package, one dependency it uses, and one it
    only claims to use."""
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "app"\n')
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'name = "app"\n'
        'version = "1.0"\n'
        'dependencies = ["used-lib>=1", "ghost-lib==2.0"]\n'
    )
    pkg = tmp_path / "src" / "app"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("import used_lib\n\n\ndef go():\n    return used_lib\n")
    return tmp_path


def _by_owner(rows):
    return {r["owner"]: r for r in rows}


def test_manifest_is_a_claim_and_an_import_is_a_fact(repo):
    from montology_scan.surf import measure

    m = measure(repo)
    owners = _by_owner(m["surfaces"])
    assert set(owners) == {"app", "used-lib", "ghost-lib"}
    assert owners["app"]["kind"] == "first-party"
    assert owners["ghost-lib"]["version"] == "==2.0"

    # the seam: our package to the library it actually imports
    assert [(s["kind"], s["direction"]) for s in m["seams"]] == [("import", "out")]
    assert m["seams"][0]["at"].endswith("__init__.py:1")

    # declared, never met
    assert [p["owner"] for p in m["phantoms"]] == ["ghost-lib"]


def test_a_phantom_nothing_bears_on_is_untidy_not_fatal(repo, onto_db):
    from montology_scan.surf import gate

    lines = gate(repo)
    assert any(line.startswith("note surface") and "ghost-lib" in line for line in lines)
    assert not any(line.startswith("FAIL") for line in lines)


def test_a_word_bearing_on_a_phantom_fails_the_gate(repo, onto_db):
    from montology_scan.surf import bear, gate, record

    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition, code) VALUES (?,?,?,?)",
                 ("haunting", "core", "the thing we claim to stand on", "haunt"))
    conn.commit()

    record(repo)
    assert bear("haunting", "python:ghost-lib").startswith("bearing")

    fails = [line for line in gate(repo) if line.startswith("FAIL")]
    assert len(fails) == 1
    assert "ghost-lib" in fails[0] and "haunting" in fails[0]
    assert "monty surface" in fails[0]  # errors are data with the repair attached


def test_bearing_refuses_an_unknown_word_and_an_unknown_surface(repo, onto_db):
    from montology_scan.surf import bear, record

    record(repo)
    assert bear("nosuchword", "python:ghost-lib").startswith("REFUSED")

    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition, code) VALUES (?,?,?,?)",
                 ("haunting", "core", "d", "haunt"))
    conn.commit()
    refusal = bear("haunting", "ghost-lib")
    assert refusal.startswith("REFUSED")
    assert "python:ghost-lib" in refusal  # the repair names the id it meant


def test_a_sweep_replaces_its_own_seams(repo, onto_db):
    """A seam is a place, so an edit above an import moves it. Recording
    twice must not leave a seam at every line the import ever sat on."""
    from montology_scan.surf import record, seams

    record(repo)
    first = seams(repo)
    assert len(first) == 1

    pkg = repo / "src" / "app" / "__init__.py"
    pkg.write_text("# a new line on top\n" + pkg.read_text())
    record(repo)

    after = seams(repo)
    assert len(after) == 1
    assert after[0]["at"].endswith(":2")


def test_a_dropped_dependency_stops_being_a_surface(repo, onto_db):
    """Undeclared is absent, not phantom — a phantom is DECLARED and unmet."""
    from montology_scan.surf import record, surfaces

    record(repo)
    assert "ghost-lib" in _by_owner(surfaces(repo))

    (repo / "pyproject.toml").write_text(
        '[project]\nname = "app"\nversion = "1.0"\ndependencies = ["used-lib>=1"]\n')
    record(repo)
    assert "ghost-lib" not in _by_owner(surfaces(repo))


def test_both_directions_of_the_join(repo, onto_db):
    from montology_scan.surf import bear, record, surfaces_for_word, words_for_surface

    conn = onto_db.connect()
    conn.execute("INSERT INTO word (name, kind, definition, code) VALUES (?,?,?,?)",
                 ("sweep", "core", "what the package does", "swp"))
    conn.commit()
    record(repo)
    bear("sweep", "repo:app", "this package is the sweep")

    assert [s["owner"] for s in surfaces_for_word("sweep")] == ["app"]
    assert words_for_surface("repo:app") == ["sweep"]


@pytest.fixture()
def node_repo(tmp_path):
    """The seams that are not JavaScript imports: a stylesheet, a script,
    a typings package, and one dependency that is genuinely unused."""
    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "ui"\n')
    (tmp_path / "package.json").write_text("""{
      "name": "ui",
      "version": "1.0.0",
      "scripts": {"lint": "oxlint .", "build": "tsc -b"},
      "dependencies": {"react": "^19", "tw-animate-css": "^1"},
      "devDependencies": {"@types/react": "^19", "@types/node": "^22",
                          "oxlint": "^1", "typescript": "^5", "unused-pkg": "^1"}
    }""")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "main.tsx").write_text(
        'import React from "react";\nimport fs from "node:fs";\n\nexport default React;\n')
    (tmp_path / "src" / "app.css").write_text('@import "tw-animate-css";\n')
    # typescript's command is `tsc`, declared by the package, not guessable
    tsc = tmp_path / "node_modules" / "typescript"
    tsc.mkdir(parents=True)
    (tsc / "package.json").write_text('{"name":"typescript","bin":{"tsc":"bin/tsc"}}')
    return tmp_path


def test_the_seams_that_are_not_javascript_imports(node_repo):
    from montology_scan.surf import measure

    m = measure(node_repo)
    kinds = {(s["to_id"], s["kind"]) for s in m["seams"]}

    assert ("node:react", "import") in kinds            # javascript
    assert ("node:tw-animate-css", "import") in kinds   # a stylesheet
    assert ("node:oxlint", "call") in kinds             # a script, by name
    assert ("node:typescript", "call") in kinds         # a script, by its bin
    assert ("node:@types/react", "config") in kinds     # its subject is used
    assert ("node:@types/node", "config") in kinds      # a builtin is used

    # only the one nothing touches
    assert [p["owner"] for p in m["phantoms"]] == ["unused-pkg"]


def test_a_types_package_is_a_phantom_when_its_subject_is(node_repo):
    """The cascade is the point: unused typings for an unused package are
    two findings, not one hidden behind the other."""
    from montology_scan.surf import measure

    (node_repo / "src" / "main.tsx").write_text("export default 1;\n")
    (node_repo / "src" / "app.css").write_text("body { color: red }\n")
    m = measure(node_repo)
    ghosts = {p["owner"] for p in m["phantoms"]}
    assert {"react", "@types/react", "tw-animate-css", "unused-pkg"} <= ghosts


def test_a_configured_python_tool_is_used(repo):
    """`[tool.ruff]` is the same evidence an import would be, for a thing
    that is run rather than imported."""
    from montology_scan.surf import measure

    (repo / "pyproject.toml").write_text(
        '[project]\nname = "app"\nversion = "1.0"\n'
        'dependencies = ["used-lib>=1", "ghost-lib==2.0"]\n\n'
        '[tool.ghost-lib]\nstrict = true\n')
    m = measure(repo)
    assert m["phantoms"] == []
    assert any(s["kind"] == "config" and s["to_id"] == "python:ghost-lib"
               for s in m["seams"])


def test_elixir_reads_the_modules_a_dep_really_exposes(tmp_path):
    """`:ecto_sql` provides `Ecto.Adapters.SQL`, which no camelizing of
    `ecto_sql` reaches. A built dep names one .beam per module, so the
    directory listing IS the answer — guessing would invent a phantom out
    of a naming convention."""
    from montology_scan.surf import measure

    (tmp_path / ".monty").mkdir()
    (tmp_path / ".monty" / "montology.toml").write_text('name = "nexus"\n')
    (tmp_path / "mix.exs").write_text(
        'defmodule Nexus.MixProject do\n'
        '  def project do\n'
        '    [app: :nexus, version: "0.1.0", deps: deps()]\n'
        '  end\n'
        '  defp deps do\n'
        '    [\n'
        '      {:ecto_sql, "~> 3.12"},\n'
        '      {:broadway, "~> 1.0"}\n'
        '    ]\n'
        '  end\n'
        'end\n')
    ebin = tmp_path / "_build" / "dev" / "lib" / "ecto_sql" / "ebin"
    ebin.mkdir(parents=True)
    for mod in ("Elixir.Ecto.Adapters.SQL", "Elixir.Ecto.Adapters.SQL.Connection"):
        (ebin / f"{mod}.beam").write_bytes(b"")
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "repo.ex").write_text(
        "defmodule Nexus.Repo do\n  alias Ecto.Adapters.SQL.Connection\nend\n")

    m = measure(tmp_path)
    owners = {s["owner"]: s for s in m["surfaces"]}
    assert owners["ecto_sql"]["exposes"] == ["Ecto.Adapters.SQL"]  # the root only
    # the deeper claim wins: a reference to SQL.Connection lands on ecto_sql
    assert any(s["to_id"] == "elixir:ecto_sql" for s in m["seams"])
    assert [p["owner"] for p in m["phantoms"]] == ["broadway"]


def test_an_ecosystem_with_no_probe_is_said_to_be_unmeasured(repo, onto_db):
    """Zero phantoms across a repo whose Go half was never read is a lie of
    omission. It must SAY so."""
    from montology_scan.surf import gate, measure

    (repo / "svc").mkdir()
    (repo / "svc" / "go.mod").write_text("module example.com/svc\n\ngo 1.22\n")

    assert any("go" in s and "NOT measured" in s for s in measure(repo)["skipped"])
    assert any(line.startswith("note surface") and "go" in line
               for line in gate(repo))


def test_a_probe_with_nothing_to_read_says_so(tmp_path):
    from montology_scan.surf import measure

    (tmp_path / ".monty").mkdir()
    m = measure(tmp_path)
    assert m["surfaces"] == []
    assert any("nothing to read" in s for s in m["skipped"])
