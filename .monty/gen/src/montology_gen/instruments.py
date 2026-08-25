"""Instruments: deterministic context collectors. Facts in, facts out.

Everything a stub or a rendered file is allowed to know arrives through
here — the vocabulary from the database, the code surface from the scan.
An instrument never calls a model and never guesses: if it cannot measure
something, the field is absent, not invented. `fingerprint()` hashes what
was collected so a generated file can say exactly which facts produced it.
"""

from __future__ import annotations

import hashlib
import json
import re

import yaml

# the env vars that exist; generated prose may name no others
KNOWN_ENV = (
    "MONTOLOGY_WORKSPACE", "MONTOLOGY_MODEL_URL", "MONTOLOGY_MODEL",
    "MONTOLOGY_MODEL_KEY", "MONTOLOGY_MODEL_TINY", "MONTY_FROM",
)


def vocabulary() -> dict:
    """The ontology as facts: words, doctrine, rulings — what sync renders
    and what a word draft must not collide with."""
    from montology_ontology import (collisions, doctrines, exceptions, genera,
                                    overloads, renames, tokens, words)

    return {"words": words(), "doctrine": doctrines(), "overloads": overloads(),
            "collisions": collisions(), "renames": renames(), "tokens": tokens(),
            "exceptions": exceptions(), "genera": genera()}


def code_surface() -> dict:
    """The workspace's declarations, via the scan package."""
    from montology_core import workspace_root
    from montology_scan import declarations

    return declarations(workspace_root())


def read_settings() -> dict:
    """`.monty/montology.toml`, as a dict. Absent or unreadable is empty.

    An instrument, so it follows the rule the others do: what cannot be measured
    is absent rather than invented. A repo with no settings file is a repo whose
    every setting is the default, which is a fact and not a failure.
    """
    import tomllib

    from montology_core import workspace_root

    path = workspace_root() / ".monty" / "montology.toml"

    if not path.exists():
        return {}

    try:
        return tomllib.loads(path.read_text())
    except Exception:
        return {}


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Frontmatter dict + body. No fence parses as all-body — never an error."""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.DOTALL)
    if not m:
        return {}, text
    try:
        return (yaml.safe_load(m.group(1)) or {}), m.group(2)
    except yaml.YAMLError:
        return {}, text


def fingerprint(*facts) -> str:
    """A stable hash of the facts a generation consumed — its provenance."""
    blob = json.dumps(facts, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:16]
