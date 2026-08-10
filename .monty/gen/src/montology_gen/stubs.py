"""Stubs: every generation in this monorepo, as typed Mellea functions.

THE DOCSTRING IS A SPEC, NOT A PROMPT. It states what the output must be;
the facts arrive as ARGUMENTS (instrument output), and the laws — not the
wording here — decide acceptance. Nobody tunes these docstrings against a
model; they change only when the CONTRACT of the output changes. `gen lint`
greps this package for prompt-shaped strings — persona openers, polite
imperatives, role-play framing — and fails the build on them. (Their
literal forms are not written here for exactly that reason.)

Each stub has a revise twin taking the draft plus the failures the laws
found — Mellea's repair pattern, with the feedback being law output rather
than judge prose.
"""

from __future__ import annotations

from mellea import generative


@generative
def define_word(name: str, usage_context: str, existing_words: list[str]) -> str:
    """Define one vocabulary word for a codebase's ontology.

    Output exactly one line, 'name: definition' — the definition ONE
    sentence stating what the word means in this system, distinct from
    every word in existing_words, grounded in how usage_context actually
    uses it. No vendor names; a word means one thing.
    """
    ...
