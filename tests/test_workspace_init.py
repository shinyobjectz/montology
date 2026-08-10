"""The workspace contract: discovery walks up like git, init materializes
everything, re-runs repair and never clobber user data."""

from __future__ import annotations

import json

import pytest

from montology_core import MARKER, WorkspaceError, find_root, load_env, workspace_root


def test_find_root_walks_up_like_git(tmp_path, monkeypatch):
    monkeypatch.delenv("MONTOLOGY_WORKSPACE", raising=False)
    ws = tmp_path / "acme"
    deep = ws / "projects" / "shopify" / "components"
    deep.mkdir(parents=True)
    (ws / MARKER).mkdir()
    assert find_root(deep) == ws
    assert find_root(tmp_path) is None


def test_env_override_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("MONTOLOGY_WORKSPACE", str(tmp_path / "pinned"))
    assert find_root(tmp_path) == tmp_path / "pinned"


def test_no_workspace_is_an_error_with_the_repair(tmp_path, monkeypatch):
    monkeypatch.delenv("MONTOLOGY_WORKSPACE", raising=False)
    with pytest.raises(WorkspaceError, match="monty init"):
        workspace_root(tmp_path)


def test_load_env_never_overrides_the_environment(tmp_path, monkeypatch):
    (tmp_path / MARKER).mkdir()
    (tmp_path / ".env").write_text('A_KEY="from-file"\nB_KEY=fresh\n# comment\n')
    monkeypatch.setenv("A_KEY", "from-shell")
    monkeypatch.delenv("B_KEY", raising=False)
    load_env(tmp_path)
    import os
    assert os.environ["A_KEY"] == "from-shell"   # the shell outranks the file
    assert os.environ["B_KEY"] == "fresh"        # quotes stripped, comment skipped
    monkeypatch.delenv("B_KEY")


def test_materialize_lays_down_the_whole_shape(tmp_path):
    from montology_cli._scaffold import materialize

    result = materialize(tmp_path / "ws", "acme")
    ws = tmp_path / "ws"
    for expected in (".monty/workspace.toml", ".monty/cache/models",
                     ".plugin/plugin.json", ".plugin/skills/montology/SKILL.md",
                     "data/ontology.db", "data/zoo.db", "design/package.json",
                     "projects/README.md", ".justfile", "CLAUDE.md",
                     ".gitignore", ".env.example", ".mcp.json"):
        assert (ws / expected).exists(), expected
    assert (ws / ".claude" / "skills").is_symlink()
    assert (ws / ".claude" / "skills" / "montology" / "SKILL.md").exists()
    assert "acme" in (ws / ".justfile").read_text()
    # the scaffolded MCP door pins the same engine the shim runs
    mcp = json.loads((ws / ".mcp.json").read_text())
    assert "--from" in mcp["mcpServers"]["montology"]["args"]
    assert result["made"]


def test_rerun_repairs_and_never_clobbers_user_data(tmp_path):
    from montology_cli._scaffold import materialize

    ws = tmp_path / "ws"
    materialize(ws, "acme")
    # the user's ontology grew; a re-run must keep it
    (ws / "data" / "ontology.db").write_bytes(b"the user's own words")
    (ws / ".justfile").write_text("# user-edited\n")
    (ws / "CLAUDE.md").unlink()  # …and repair what is missing
    materialize(ws, "acme")
    assert (ws / "data" / "ontology.db").read_bytes() == b"the user's own words"
    assert (ws / ".justfile").read_text() == "# user-edited\n"
    assert (ws / "CLAUDE.md").exists()


def test_init_yes_json_is_the_agent_contract(tmp_path, monkeypatch, capsys):
    from montology_cli.init import init_command

    monkeypatch.delenv("MONTOLOGY_WORKSPACE", raising=False)
    monkeypatch.setenv("SCRAPECREATORS_API_KEY", "sk-test")
    init_command(str(tmp_path / "ws"), name="acme", yes=True, as_json=True,
                 no_install=True)
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["workspace"].endswith("ws")
    assert "ontology.db" in out["created"]
    for m in out["missing"]:
        assert m["repair"], "a gap without a repair is a loop"
    # env-only secrets landed in .env, mode 600
    env_file = tmp_path / "ws" / ".env"
    assert "SCRAPECREATORS_API_KEY=sk-test" in env_file.read_text()
    assert (env_file.stat().st_mode & 0o777) == 0o600
