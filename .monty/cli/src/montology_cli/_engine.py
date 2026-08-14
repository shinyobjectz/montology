"""Where a workspace gets its engine from — one pin, stated once.

Everything that launches montology outside this process (the scaffolded
`.mcp.json`, `.plugin/mcp.json`) resolves the engine through this spec.
Until the packages are on PyPI the pin is the public git repo; at first
PyPI release it becomes ``montology==<version>`` and every new `monty
init` picks that up. ``MONTY_FROM`` overrides for development — the same
knob the npm shim honors.
"""

from __future__ import annotations

import os

ENGINE_SPEC = "git+https://github.com/shinyobjectz/montology@main#subdirectory=.monty/cli"


def engine_spec() -> str:
    return os.environ.get("MONTY_FROM", "").strip() or ENGINE_SPEC
