"""The terminal face: severity colors, swatches, marks — honestly.

Engines emit PLAIN STRINGS (pipeable, testable, greppable); this layer
styles them at print time only. Rich strips styles when output is not a
TTY, so CI logs and redirects stay clean, and `--json` paths never come
through here. The one genuinely load-bearing flourish: every hex color in
a line gets an actual SWATCH — a drift report you can see is a drift
report you believe.
"""

from __future__ import annotations

import re

from rich.console import Console
from rich.text import Text

console = Console(highlight=False, soft_wrap=True)

_HEX = re.compile(r"#[0-9a-fA-F]{6}\b")

_PREFIX_STYLES = (
    ("FAIL", "bold red"),
    ("CONFLICTS", "bold red"),
    ("REFUSED", "bold red"),
    ("[MISSING]", "bold red"),
    ("warn", "bold yellow"),
    ("TAKEN", "yellow"),
    ("RULED", "yellow"),
    ("RENAMED", "yellow"),
    ("COLLISION", "yellow"),
    ("note", "dim"),
    ("ok", "bold green"),
    ("[ok ]", "bold green"),
    ("FREE", "bold green"),
    ("added", "green"),
    ("token", "green"),
    ("synced", "green"),
    ("inherited", "green"),
    ("ingested", "green"),
    ("renamed", "green"),
    ("ruled", "green"),
    ("mapped", "green"),
    ("design:", "bold cyan"),
    ("gen lint:", "bold cyan"),
    ("✔", "bold green"),
)


def _swatched(text: str, base_style: str = "") -> Text:
    """The line as rich Text, every #rrggbb preceded by a swatch in it."""
    out = Text()
    pos = 0
    for m in _HEX.finditer(text):
        out.append(text[pos:m.start()], style=base_style)
        out.append("▉▉", style=m.group(0).lower())
        out.append(" " + m.group(0), style=base_style)
        pos = m.end()
    out.append(text[pos:], style=base_style)
    return out


def emit(line: str) -> None:
    """One engine line, styled by its severity prefix, swatches inline."""
    for prefix, style in _PREFIX_STYLES:
        if line.startswith(prefix):
            styled = Text(prefix, style=style)
            styled.append_text(_swatched(line[len(prefix):]))
            console.print(styled)
            return
    console.print(_swatched(line))


def emit_all(lines) -> None:
    for line in lines:
        emit(line)
