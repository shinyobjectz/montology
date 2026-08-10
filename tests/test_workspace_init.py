"""The workspace contract: discovery walks up like git; .env never outranks
the shell."""

from __future__ import annotations

import pytest

from montology_core import MARKER, WorkspaceError, find_root, load_env, workspace_root


def test_find_root_walks_up_like_git(tmp_path, monkeypatch):
    monkeypatch.delenv("MONTOLOGY_WORKSPACE", raising=False)
    ws = tmp_path / "acme"
    deep = ws / "packages" / "web" / "src"
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
