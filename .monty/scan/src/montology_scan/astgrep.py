"""ast-grep, invoked never linked: structural search for agents.

A pattern beats a regex because it parses: `sg('def $F($$$): $$$', 'python')`
matches code shape, not text shape. The binary is the user's (single
static executable); absence answers with the repair.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from montology_core import workspace_root

_NO_SG = ("ast-grep is not installed. Repair: `brew install ast-grep` "
          "(or cargo install ast-grep — one static binary), then retry.")


def sg(pattern: str, lang: str = "", root: Path | None = None,
       max_lines: int = 200) -> str:
    """Run an ast-grep structural pattern over the workspace; matches as
    file:line lines, capped and saying so."""
    binary = shutil.which("ast-grep") or shutil.which("sg")
    if binary is None:
        return _NO_SG
    root = root or workspace_root()
    cmd = [binary, "run", "--pattern", pattern]
    if lang:
        cmd += ["--lang", lang]
    cmd.append(str(root))
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return "ast-grep timed out after 120s — narrow the pattern or pass a language."
    if r.returncode not in (0, 1):
        return f"ast-grep failed: {r.stderr.strip()[-300:]}"
    lines = r.stdout.splitlines()
    if not lines:
        return "no matches."
    shown = lines[:max_lines]
    tail = f"\n… {len(lines) - max_lines} more line(s) capped" if len(lines) > max_lines else ""
    return "\n".join(shown) + tail
