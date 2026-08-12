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
console_err = Console(stderr=True, highlight=False, soft_wrap=True)

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
    ("AMENDED", "yellow"),
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
    ("amended", "green"),
    ("ruled", "green"),
    ("mapped", "green"),
    ("design:", "bold cyan"),
    ("semantics:", "bold cyan"),
    ("gen lint:", "bold cyan"),
    ("✔", "bold green"),
    ("montology guard:", "bold red"),
    ("verdict: TENDED", "bold green"),
    ("verdict: DRIFTING", "bold yellow"),
    ("verdict: UNTENDED", "bold red"),
    ("•", "bold yellow"),
)


_ACCENTS = re.compile(
    r"(?P<hex>#[0-9a-fA-F]{6}\b)"          # a color -> swatch + code
    r"|'(?P<name>[^']{1,40})'"               # a quoted word -> bold yellow
    r"|(?P<score>\(Δ?\d+(?:\.\d+)?\))"  # (0.74) / (Δ2) -> bold
    r"|(?P<count>\b\d+×)"                  # 11× -> bold
)


def _swatched(text: str, base_style: str = "") -> Text:
    """The line as rich Text: hex colors carry swatches, quoted names read
    bold yellow, scores and counts carry weight — the FINDING is the
    payoff and must not whisper."""
    out = Text()
    pos = 0
    for m in _ACCENTS.finditer(text):
        out.append(text[pos:m.start()], style=base_style)
        if m.group("hex"):
            out.append("▉▉", style=m.group("hex").lower())
            out.append(" " + m.group("hex"), style=base_style)
        elif m.group("name") is not None:
            out.append("'", style=base_style)
            out.append(m.group("name"), style="bold yellow")
            out.append("'", style=base_style)
        else:
            out.append(m.group(0), style="bold")
        pos = m.end()
    out.append(text[pos:], style=base_style)
    return out


# prefixes whose ENTIRE line (including wrapped continuations) reads dim —
# secondary information should never shout in white
_DIM_WHOLE = ("note", "  [", "  command", "  args", "recipes:", "(")


def emit(line: str) -> None:
    """One engine line, styled by its severity prefix, swatches inline.
    Prefixes match past indentation, so nested output stays designed."""
    indent = line[:len(line) - len(line.lstrip())]
    body = line.lstrip()
    for prefix, style in _PREFIX_STYLES:
        if body.startswith(prefix):
            rest_style = "dim" if prefix in ("note",) else ""
            styled = Text(indent) + Text(prefix, style=style)
            styled.append_text(_swatched(body[len(prefix):], rest_style))
            console.print(styled)
            return
    for prefix in _DIM_WHOLE:
        if line.startswith(prefix):
            console.print(_swatched(line, "dim"))
            return
    console.print(_swatched(line))


def emit_all(lines) -> None:
    for line in lines:
        emit(line)


def next_steps(steps: list[tuple[str, str]]) -> None:
    """The what-now block: unmissable, one command per line, the command
    loud and the why quiet. Suggestions that whisper don't get run."""
    console.print()
    console.print(Text("  ── what now ", style="bold") +
                  Text("─" * 42, style="dim"))
    for cmd, why in steps:
        row = Text("   → ", style="bold yellow")
        row.append(f"{cmd:<28}", style="bold cyan")
        row.append(why, style="dim")
        console.print(row)


def emit_err(line: str) -> None:
    """emit, but to stderr — styled for a human, stripped for a pipe."""
    indent = line[:len(line) - len(line.lstrip())]
    body = line.lstrip()
    for prefix, style in _PREFIX_STYLES:
        if body.startswith(prefix):
            styled = Text(indent) + Text(prefix, style=style)
            styled.append_text(_swatched(body[len(prefix):]))
            console_err.print(styled)
            return
    console_err.print(_swatched(line))
