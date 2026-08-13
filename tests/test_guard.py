"""The firewall: drift cannot enter — and the guard always fails open."""

import json

import pytest

from montology_scan import guard


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    monkeypatch.setattr(onto_db, "DB_PATH", tmp_path / ".monty" / "ontology.db")
    onto_db.add("cell", "the network-blocked sandbox", kind="core", pos="noun")
    onto_db.add("dossier", "what a task produces", kind="core", pos="noun")
    onto_db.rename_word("artifact", "dossier2", "x") if False else None
    conn = onto_db.connect()
    conn.execute("INSERT INTO renamed (was, now, renamed_on, why) "
                 "VALUES ('artifact','dossier','2026-08-10','field name')")
    conn.commit()
    onto_db.token_add("brand", "color", "#061a1c")
    return tmp_path


def _payload(ws, name="x.py", content=""):
    return json.dumps({"tool_name": "Write",
                       "tool_input": {"file_path": str(ws / name), "content": content}})


def test_retired_word_always_blocks(ws, capsys):
    code = _payload(ws, "a.py", "class Artifact:\n    pass\n")
    assert guard.run_hook(code) == 2
    err = capsys.readouterr().err
    assert "RENAMED" in err and "'dossier'" in err and "retired" in err


def test_collision_advises_by_default_blocks_on_enforce(ws, capsys):
    code = _payload(ws, "a.py", "class Cell:\n    pass\n")
    assert guard.run_hook(code) == 0          # advisory culture: allowed…
    assert "collides" in capsys.readouterr().out   # …but said
    (ws / ".monty" / "montology.toml").write_text('[scan]\ncollisions = "enforce"\n')
    assert guard.run_hook(code) == 2          # enforce culture: stopped


def test_rogue_color_blocks_with_the_token_as_the_repair(ws, capsys):
    css = _payload(ws, "a.css", ".card { background: #06191b; }")
    assert guard.run_hook(css) == 2
    err = capsys.readouterr().err
    assert "#06191b" in err and "'brand'" in err and "Δ2" in err
    # a token-exact value passes silently
    ok = _payload(ws, "b.css", ".card { background: #061a1c; }")
    assert guard.run_hook(ok) == 0


def test_design_warn_mode_allows_but_says(ws, capsys):
    (ws / ".monty" / "montology.toml").write_text('[guard]\ndesign = "warn"\n')
    css = _payload(ws, "a.css", "b { color: #06191b; }")
    assert guard.run_hook(css) == 0
    assert "rogue color" in capsys.readouterr().out


def test_outside_a_workspace_the_guard_is_invisible(tmp_path, monkeypatch):
    monkeypatch.delenv("MONTOLOGY_WORKSPACE", raising=False)
    p = json.dumps({"tool_input": {"file_path": str(tmp_path / "x.py"),
                                   "content": "class Artifact: pass"}})
    assert guard.run_hook(p) == 0


def test_malformed_payloads_never_block(ws):
    assert guard.run_hook("not json at all") == 0
    assert guard.run_hook(json.dumps({"tool_input": {}})) == 0
