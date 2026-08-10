"""Workspace discovery — the one fact every package needs.

A montology WORKSPACE is a directory `monty init` has scaffolded: `.monty/`
(engine cache), `.plugin/` (the agent-facing plugin), `data/` (the tracked
dbs), `design/` (node mediums), `projects/` (engagements). Any command run
from anywhere inside it finds the root by walking up for the `.monty`
marker, the way git finds `.git`. Nothing is ever resolved relative to the
installed package — a wheel lives in a venv, and a venv is not a workspace.

`MONTOLOGY_WORKSPACE` overrides the walk (agents pinning a root, tests).
No workspace is an error with the repair attached, per the ground rule.
"""

from __future__ import annotations

import os
from pathlib import Path

MARKER = ".monty"

NO_WORKSPACE = (
    "Not inside a montology workspace (no `.monty/` found walking up from "
    "here, and MONTOLOGY_WORKSPACE is unset). Repair: `cd` into a workspace, "
    "or create one right here with `monty init`."
)


class WorkspaceError(RuntimeError):
    """Raised where a command needs a workspace and none exists."""


def find_root(start: Path | None = None) -> Path | None:
    """The workspace root, or None. Env override first, then the walk."""
    env = os.environ.get("MONTOLOGY_WORKSPACE", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    here = (start or Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / MARKER).is_dir():
            return candidate
    return None


def workspace_root(start: Path | None = None) -> Path:
    """The workspace root, or WorkspaceError carrying the repair."""
    root = find_root(start)
    if root is None:
        raise WorkspaceError(NO_WORKSPACE)
    return root


def load_env(root: Path | None = None) -> None:
    """Read the workspace `.env` into os.environ, never overriding what is
    already set — the environment outranks the file, so an agent exporting
    a key wins over a stale one on disk. A missing file is the normal case,
    not an error. KEY=VALUE lines only; quotes stripped; `#` comments and
    blanks skipped."""
    root = root or find_root()
    if root is None:
        return
    env_file = root / ".env"
    if not env_file.is_file():
        return
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value
