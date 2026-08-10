"""The house vocabulary. THE one place montology's own words are authored.

Small on purpose: the industry taxonomies carry the category systems, and a
house word earns its row by meaning something none of them say. A starter
set, marked as such — grow it by decision, not by accretion.
"""

from __future__ import annotations

from .db import connect

WORDS = [
    # (name, kind, owner, definition, test)
    ("montology", "core", None,
     "marketing + monorepo + ontology — this system", "what this repo is"),
    ("source", "core", None,
     "a registered external taxonomy, with a status ruling (core/extra/evaluate/skip)",
     "whose words are these"),
    ("word", "core", None,
     "one house term with one meaning, authored in seed.py", "what we mean"),
    ("mapping", "core", None,
     "a house word pinned to the taxonomy rows the industry uses for the same idea",
     "how our word trades"),
    ("zoo", "core", None,
     "the local embedding models: registered, downloaded, run on-device",
     "what makes text comparable"),
    ("skill", "adopted", None,
     "an Agent Skills folder: SKILL.md frontmatter, body, scripts/",
     "how the agent learns a method"),
    ("gen", "core", None,
     "the generative system: skills, docs and words produced by Mellea from instruments, law-checked, never hand-prompted",
     "how prose stays true"),
    ("instrument", "core", None,
     "a deterministic context collector — AST surface, warehouse shape, skill inventory — whose measured output is all a stub may know",
     "where facts come from"),
    ("plugin", "adopted", None,
     "the Agent Plugins 1.0.0 package: plugin.json + skills/ + mcp.json — how montology ships",
     "how it installs"),
    ("workspace", "core", None,
     "the directory `monty init` lays down — .monty/ (cache), .plugin/ (the agent face), data/, design/, projects/ — found from anywhere inside by walking up for .monty, the way git finds .git",
     "where work happens"),
]


def seed() -> str:
    conn = connect()
    for name, kind, owner, definition, test in WORDS:
        conn.execute(
            "INSERT OR REPLACE INTO word (name, kind, owner, definition, test, note) VALUES (?,?,?,?,?,NULL)",
            (name, kind, owner, definition, test),
        )
    conn.commit()
    return f"seeded {len(WORDS)} words"
