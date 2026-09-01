"""Every harness gets the whole firewall, or is told it did not.

Montology's post-hoc half (lint, vitals, explain) is harness-agnostic; the
pre-write half is not — it is a hook, and a hook has a dialect. For a long
time only Claude Code got one, so the same repo was ENFORCED under one
agent and merely advisory under another, with nothing anywhere saying so.
These cases pin the two dialects, the tools each covers, and the rule that
outranks both: the guard fails open rather than break someone's editor.
"""

import json

import pytest


@pytest.fixture()
def repo(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    monkeypatch.setattr("montology_ontology.db.DB_PATH",
                        tmp_path / ".monty" / "ontology.db")
    (tmp_path / ".git").mkdir()
    return tmp_path


def _init(repo, agents, capsys):
    from montology_cli.init import init_command

    init_command(str(repo), yes=True, as_json=True, agents=agents)
    return json.loads(capsys.readouterr().out)


# ── the wiring ──────────────────────────────────────────────────────────

def test_claude_gets_the_guard_on_every_tool_that_writes(repo, capsys, onto_db):
    """NotebookEdit was missing for as long as the hook existed, so a name
    written into a .ipynb cell walked past a firewall the repo believed was
    closed. A gate with a door in it teaches the agent the gate is optional."""
    _init(repo, "claude", capsys)
    settings = json.loads((repo / ".claude" / "settings.json").read_text())
    entry = next(h for h in settings["hooks"]["PreToolUse"]
                 if "monty guard" in json.dumps(h))
    for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        assert tool in entry["matcher"]


def test_cursor_gets_the_firewall_and_not_only_the_mcp_server(repo, capsys, onto_db):
    """Cursor wiring was MCP-only: the half that runs after the fact worked,
    the half that runs before the write did not, and nothing said which."""
    _init(repo, "cursor", capsys)
    assert (repo / ".cursor" / "mcp.json").exists()
    hooks = json.loads((repo / ".cursor" / "hooks.json").read_text())
    assert hooks["version"] == 1
    entry = hooks["hooks"]["preToolUse"][0]
    assert "monty guard" in entry["command"]
    assert "Write" in entry["matcher"]


def test_cursor_hooks_are_merge_safe(repo, capsys, onto_db):
    (repo / ".cursor").mkdir()
    (repo / ".cursor" / "hooks.json").write_text(json.dumps(
        {"version": 1, "hooks": {"beforeShellExecution": [{"command": "./theirs.sh"}],
                                 "preToolUse": [{"command": "./also-theirs.sh"}]}}))
    _init(repo, "cursor", capsys)
    hooks = json.loads((repo / ".cursor" / "hooks.json").read_text())
    assert hooks["hooks"]["beforeShellExecution"] == [{"command": "./theirs.sh"}]
    commands = [e["command"] for e in hooks["hooks"]["preToolUse"]]
    assert "./also-theirs.sh" in commands                 # theirs survived
    assert any("monty guard" in c for c in commands)      # ours arrived


def test_wiring_twice_installs_one_hook_per_harness(repo, capsys, onto_db):
    _init(repo, "claude,cursor", capsys)
    _init(repo, "claude,cursor", capsys)
    settings = json.loads((repo / ".claude" / "settings.json").read_text())
    cursor = json.loads((repo / ".cursor" / "hooks.json").read_text())
    assert sum("monty guard" in json.dumps(h)
               for h in settings["hooks"]["PreToolUse"]) == 1
    assert sum("monty guard" in json.dumps(h)
               for h in cursor["hooks"]["preToolUse"]) == 1


def test_an_older_narrower_matcher_is_widened_not_duplicated(repo, capsys, onto_db):
    """A repo initialized before notebooks were covered must end up with one
    hook that covers them, never two hooks running the same check."""
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text(json.dumps(
        {"hooks": {"PreToolUse": [{"matcher": "Write|Edit|MultiEdit",
                                   "hooks": [{"type": "command",
                                              "command": "monty guard"}]}]}}))
    _init(repo, "claude", capsys)
    hooks = json.loads((repo / ".claude" / "settings.json").read_text())["hooks"]["PreToolUse"]
    assert len(hooks) == 1
    assert "NotebookEdit" in hooks[0]["matcher"]


def test_an_unparsable_settings_file_is_reported_never_overwritten(repo, capsys, onto_db):
    (repo / ".claude").mkdir()
    (repo / ".claude" / "settings.json").write_text("{ not json")
    out = _init(repo, "claude", capsys)
    assert (repo / ".claude" / "settings.json").read_text() == "{ not json"
    assert any("SKIPPED .claude/settings.json" in c for c in out["created"])


# ── the payloads ────────────────────────────────────────────────────────

@pytest.fixture()
def ws(tmp_path, onto_db, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path))
    (tmp_path / ".monty").mkdir()
    monkeypatch.setattr(onto_db, "DB_PATH", tmp_path / ".monty" / "ontology.db")
    onto_db.add("cell", "the network-blocked sandbox", kind="core", pos="noun")
    conn = onto_db.connect()
    conn.execute("INSERT INTO renamed (was, now, renamed_on, why) "
                 "VALUES ('artifact','dossier','2026-08-10','field name')")
    conn.commit()
    return tmp_path


DRIFT = "class Artifact:\n    pass\n"


def test_the_claude_envelope_still_denies(ws, capsys):
    from montology_scan import guard

    payload = json.dumps({"tool_name": "Write", "hook_event_name": "PreToolUse",
                          "tool_input": {"file_path": str(ws / "a.py"),
                                         "content": DRIFT}})
    assert guard.run_hook(payload) == 2
    assert "dossier" in capsys.readouterr().err


def test_the_cursor_envelope_denies_and_says_so_in_cursors_words(ws, capsys):
    """Cursor honours exit 2 AND reads a verdict on stdout. The agent_message
    is what reaches the model — a denial the model never sees is a denial it
    cannot repair, so both halves have to be there."""
    from montology_scan import guard

    payload = json.dumps({"hook_event_name": "preToolUse",
                          "cursor_version": "2.0.0", "tool_name": "Write",
                          "tool_input": {"file_path": str(ws / "a.py"),
                                         "content": DRIFT}})
    assert guard.run_hook(payload) == 2
    captured = capsys.readouterr()
    verdict = json.loads(captured.out.strip())
    assert verdict["permission"] == "deny"
    assert "dossier" in verdict["agent_message"]
    assert "dossier" in captured.err          # and the plain repair, as always


def test_a_top_level_edit_payload_is_read_too(ws):
    """Cursor's file hooks put file_path and edits at the top level rather
    than inside a tool_input wrapper. Reading the SHAPE instead of keying off
    the harness is what keeps one guard honest in both."""
    from montology_scan import guard

    payload = json.dumps({"hook_event_name": "afterFileEdit",
                          "cursor_version": "2.0.0",
                          "file_path": str(ws / "a.py"),
                          "edits": [{"old_string": "", "new_string": DRIFT}]})
    assert guard.run_hook(payload) == 2


def test_a_claude_verdict_carries_no_cursor_json(ws, capsys):
    """The JSON verdict is additive for Cursor and would be noise on stdout
    for a harness that does not read it."""
    from montology_scan import guard

    payload = json.dumps({"tool_name": "Write", "hook_event_name": "PreToolUse",
                          "tool_input": {"file_path": str(ws / "a.py"),
                                         "content": DRIFT}})
    guard.run_hook(payload)
    assert capsys.readouterr().out.strip() == ""


# ── the plugin's own copy ───────────────────────────────────────────────

def test_the_plugin_ships_the_firewall_it_advertises():
    """A plugin install has no `monty init` to run, so the hook has to arrive
    with the plugin or the firewall is documentation."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1] / ".plugin"
    hooks = json.loads((root / "hooks" / "hooks.json").read_text())
    entry = hooks["hooks"]["PreToolUse"][0]
    for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        assert tool in entry["matcher"]
    script = root / "scripts" / "guard.sh"
    assert entry["hooks"][0]["command"].endswith("/scripts/guard.sh")
    assert script.exists() and script.stat().st_mode & 0o111, "must be executable"


def test_the_plugin_hook_is_silent_and_instant_outside_a_workspace(tmp_path):
    """It runs on every edit in every repo the user opens. Paying a Python
    import to discover "not a workspace" taxes people who never asked for
    montology, and a slow hook is a hook that gets deleted."""
    import subprocess
    from pathlib import Path

    script = Path(__file__).resolve().parents[1] / ".plugin" / "scripts" / "guard.sh"
    done = subprocess.run([str(script)], cwd=tmp_path, input="{}", text=True,
                          capture_output=True, timeout=10)
    assert done.returncode == 0
    assert done.stdout == "" and done.stderr == ""
