"""What a workspace has been TUNED to, and how to change it without a
hand-edit.

`.monty/montology.toml` was readable from four places and writable from
none: to move the gate from advisory to enforced you opened the file, and
an agent asked to do it either guessed the key or silently did nothing.
A setting nobody can name is a setting nobody changes, and a gate nobody
can tune is one a team turns off wholesale the first time it is wrong.

So the knobs are a SCHEMA — every key with its allowed values, its
default and what it actually does — and the writer edits the file in
place, by line, so the comments montology wrote into it survive. There is
no round-trip TOML dependency here on purpose: this package has none, and
the only file it edits is one montology authored.

An unknown key is refused with the list of real ones; a bad value is
refused with the allowed set. Both are the ground rule — an error is data
with the repair attached.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CONFIG_NAME = "montology.toml"


@dataclass(frozen=True)
class Setting:
    """One knob: where it lives, what it may be, and what it does."""

    section: str
    key: str
    default: Any
    effect: str
    choices: tuple[str, ...] = ()
    kind: str = "str"                       # str | bool | list
    item_choices: tuple[str, ...] = field(default=(), repr=False)

    @property
    def name(self) -> str:
        return f"{self.section}.{self.key}"


SETTINGS: dict[str, Setting] = {
    s.name: s for s in (
        Setting("guard", "names", "block",
                "the pre-write firewall on names. A RETIRED word blocks whatever "
                "this says — a rename is a ruling, and a ruling includes the future.",
                choices=("block", "warn", "off")),
        Setting("guard", "design", "block",
                "the pre-write firewall on rogue design values. Silent until "
                "tokens exist, so it costs an untended repo nothing.",
                choices=("block", "warn", "off")),
        Setting("scan", "collisions", "advisory",
                "whether a declaration colliding with a word FAILS the gate or "
                "only reports. Start advisory; enforce once the words are real.",
                choices=("advisory", "enforce")),
        Setting("scan", "enforced_kinds", ["core", "inner"],
                "which kinds of word a code declaration may not be named after.",
                kind="list", item_choices=("core", "inner", "adopted", "custom")),
        Setting("scan", "exclude", [],
                "globs the scan must not read — generated code, vendored trees, "
                "fixtures. Without these the first candidate list is dominated "
                "by code nobody writes.",
                kind="list"),
        Setting("scan", "include", [],
                "extra roots to read, hidden ones included.", kind="list"),
        Setting("scan", "allow", [],
                "the OLD reasonless allow-list, still honoured and still "
                "reported. Prefer `monty onto except WORD --where … --why …`, "
                "which records the reason and the place.",
                kind="list"),
        Setting("design", "enforce", False,
                "promote design findings from advisory to law.", kind="bool"),
    )
}


def config_path(root: Path) -> Path:
    return root / ".monty" / CONFIG_NAME


def read(root: Path) -> dict:
    """The whole config, or {} — a missing or unparsable file is the
    defaults, never a crash: every command needs to keep working."""
    f = config_path(root)
    if not f.is_file():
        return {}
    try:
        return tomllib.loads(f.read_text())
    except tomllib.TOMLDecodeError:
        return {}


def effective(root: Path) -> list[dict]:
    """Every setting with its value and where that value came from."""
    data = read(root)
    out = []
    for s in SETTINGS.values():
        section = data.get(s.section, {})
        set_here = isinstance(section, dict) and s.key in section
        out.append({
            "name": s.name,
            "value": section[s.key] if set_here else s.default,
            "source": CONFIG_NAME if set_here else "default",
            "allowed": list(s.choices or s.item_choices) or s.kind,
            "effect": s.effect,
        })
    return out


def parse(setting: Setting, raw: str) -> Any:
    """A command-line string as the setting's type — refused with the
    allowed set, never coerced into something that silently means nothing."""
    text = raw.strip()
    if setting.kind == "bool":
        if text.lower() in ("true", "yes", "on", "1"):
            return True
        if text.lower() in ("false", "no", "off", "0"):
            return False
        raise ValueError(f"{setting.name} is a true/false setting — got {raw!r}.")
    if setting.kind == "list":
        items = [p.strip() for p in text.split(",") if p.strip()]
        if setting.item_choices:
            bad = [i for i in items if i not in setting.item_choices]
            if bad:
                raise ValueError(
                    f"{setting.name}: {', '.join(bad)} is not a kind. "
                    f"Allowed: {', '.join(setting.item_choices)}.")
        return items
    if setting.choices and text not in setting.choices:
        raise ValueError(
            f"{setting.name} is one of {' | '.join(setting.choices)} — got {raw!r}.")
    return text


def _render(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        return "[" + ", ".join(f'"{v}"' for v in value) + "]"
    return f'"{value}"'


def write(root: Path, name: str, raw: str) -> str:
    """Set one key, in place, keeping every comment the file already has.

    Line-oriented rather than a TOML round-trip: the only file this edits
    is one montology wrote, and the comments in it are half of what makes
    the config readable. A commented-out key is left alone — a line that
    starts with `#` is documentation, and a writer that overwrote it would
    delete the explanation of the very key it was setting.
    """
    setting = SETTINGS.get(name)
    if setting is None:
        raise KeyError(
            f"no such setting {name!r}. Known: {', '.join(sorted(SETTINGS))}.")
    value = parse(setting, raw)
    line = f"{setting.key} = {_render(value)}"

    f = config_path(root)
    if not f.is_file():
        raise FileNotFoundError(
            f"no {CONFIG_NAME} at {f} — run `monty init` first.")
    lines = f.read_text().splitlines()

    section_at, end_at = None, None
    for i, text in enumerate(lines):
        stripped = text.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            if section_at is not None and end_at is None:
                end_at = i
            if stripped == f"[{setting.section}]":
                section_at = i
    if section_at is not None and end_at is None:
        end_at = len(lines)

    if section_at is None:                      # no section yet — append one
        if lines and lines[-1].strip():
            lines.append("")
        lines += [f"[{setting.section}]", line]
    else:
        for i in range(section_at + 1, end_at):
            head = lines[i].strip()
            if head.startswith("#"):
                continue                        # documentation, not a setting
            if head.split("=")[0].strip() == setting.key:
                lines[i] = line
                break
        else:                                   # in the section, not yet set
            insert = end_at
            while insert > section_at + 1 and not lines[insert - 1].strip():
                insert -= 1
            lines.insert(insert, line)

    f.write_text("\n".join(lines) + "\n")
    return f"{name} = {_render(value)}  ({CONFIG_NAME})"
