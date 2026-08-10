"""sync renders the db; lint catches drift; init is minimal and merge-safe."""

import json
from pathlib import Path

import pytest


@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    return tmp_path


def test_sync_renders_and_drift_fails(ws, onto_db):
    from montology_gen import lint, sync

    onto_db.add("thread", "a stateful session", kind="core", test="what a session is")
    assert sync().startswith("synced")
    skill = ws / ".claude" / "skills" / "words" / "SKILL.md"
    text = skill.read_text()
    assert "GENERATED" in text and "thread" in text and "monty onto check" in text
    assert lint()[-1].endswith("ok")

    onto_db.add("plan", "a proposal", kind="core")   # the db moves on…
    report = lint()
    assert any("STALE" in r and "monty sync" in r for r in report)  # …the gate bites
    sync()
    assert lint()[-1].endswith("ok")


def test_sync_renders_collisions_and_renames(ws, onto_db):
    from montology_gen import render_words_skill

    onto_db.collide("Artifact", "mellea", "a file out of the sandbox",
                    "WE MOVED — ours became Dossier")
    onto_db.add("output", "what a task produces", kind="core")
    onto_db.rename_word("output", "dossier", "one word for the deliverable")
    text = render_words_skill("t")
    assert "Collisions, ruled on" in text and "WE MOVED" in text
    assert "Renamed — what older material means" in text and "output" in text
    assert "**dossier**" in text


def test_empty_ontology_renders_the_method(ws):
    from montology_gen import render_words_skill

    text = render_words_skill("target")
    assert "No words yet" in text and "monty onto add" in text


def test_init_is_minimal_and_merge_safe(tmp_path, onto_db, monkeypatch, capsys):
    from montology_cli.init import init_command

    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    # the repo already has a CLAUDE.md and an .mcp.json — init must not clobber
    (tmp_path / ".git").mkdir()
    (tmp_path / "CLAUDE.md").write_text("# Their instructions\n\nTheir rules.\n")
    (tmp_path / ".mcp.json").write_text(json.dumps(
        {"mcpServers": {"theirs": {"command": "x"}}}))
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "settings.json").write_text(json.dumps(
        {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "theirs"}]}]}}))
    monkeypatch.setattr("montology_ontology.db.DB_PATH", tmp_path / ".monty" / "ontology.db")

    init_command(str(tmp_path), yes=True, as_json=True, agents="claude,codex")
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True

    claude_md = (tmp_path / "CLAUDE.md").read_text()
    assert claude_md.startswith("# Their instructions")       # untouched…
    assert "montology:begin" in claude_md                     # …appended
    mcp = json.loads((tmp_path / ".mcp.json").read_text())
    assert "theirs" in mcp["mcpServers"] and "montology" in mcp["mcpServers"]
    assert (tmp_path / ".monty" / "montology.toml").exists()
    assert (tmp_path / ".monty" / "ontology.db").exists()
    assert (tmp_path / "AGENTS.md").exists()                  # codex asked
    assert any("config.toml" in n for n in out["notes"])      # never edits global
    assert (tmp_path / ".claude" / "skills" / "words" / "SKILL.md").exists()

    # the guard hook merged into settings.json, preserving what was there
    settings = json.loads((tmp_path / ".claude" / "settings.json").read_text())
    hooks = settings["hooks"]["PreToolUse"]
    assert any("monty guard" in json.dumps(h) for h in hooks)   # ours arrived
    assert any("theirs" in json.dumps(h) for h in hooks)        # theirs survived

    # idempotent: a second run appends nothing twice
    init_command(str(tmp_path), yes=True, as_json=True, agents="claude")
    assert (tmp_path / "CLAUDE.md").read_text().count("montology:begin") == 1
