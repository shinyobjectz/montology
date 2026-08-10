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
def draft_skill(package_surface: dict, duck_shape: dict, house_rules: list[str],
                skill_name: str, description_of_users: str) -> str:
    """Write a complete Agent Skills std SKILL.md for this package.

    Output: YAML frontmatter (name: exactly skill_name; description: one
    dense sentence saying what the tools cover and WHEN to use the skill),
    then a markdown body teaching an agent the METHOD: which function from
    package_surface answers which marketing question, in what order, with
    what caveats. Name only functions present in package_surface. Name only
    environment variables that appear in the surface docs. Where duck_shape
    shows real tables, teach joining results against them. End with the
    house_rules verbatim under '## Rules'. The reader is an agent serving a
    non-technical marketer: method and judgment, never installation lore.
    """
    ...


@generative
def revise_skill(draft: str, failures: list[str]) -> str:
    """Return the draft SKILL.md corrected so every listed failure no longer
    holds. Change nothing that was not failing. Keep frontmatter first."""
    ...


@generative
def define_word(name: str, usage_context: str, existing_words: list[str]) -> str:
    """Define one vocabulary word for a marketing ontology.

    Output exactly one line, 'name: definition' — the definition ONE
    sentence stating what the word means in this system, distinct from
    every word in existing_words, grounded in how usage_context actually
    uses it. No vendor names; a word means one thing.
    """
    ...


@generative
def describe_skill(skill_name: str, tool_names: list[str], tool_docs: list[str]) -> str:
    """One sentence for a skill roster: what these tools cover and WHEN a
    marketer's agent should reach for this skill. Dense, concrete, under
    forty words, no markdown, no leading 'This skill'."""
    ...


@generative
def tool_method(tool_signature: str, tool_doc: str, skill_name: str) -> str:
    """Two to four plain sentences of METHOD for this one tool: which
    marketing question it answers, what to pass, and the one caveat that
    prevents misuse. Mention only this tool. No markdown headings."""
    ...


@generative
def package_doc(package_surface: dict, pyproject_description: str) -> str:
    """Write the one-paragraph README section for this package: what it is,
    the two or three functions that matter most from package_surface and
    the question each answers. Consistent with pyproject_description;
    plain prose; no headings; no installation instructions."""
    ...
