"""montology-gen: everything prose is generated, and nothing is prompted.

THE NOVEL CHOICE, STATED ONCE. Skills, docs and ontology words in this
monorepo are not hand-written and not hand-prompted — they are produced by
a pipeline whose three stages never mix:

  * INSTRUMENTS (instruments.py) — deterministic context collectors. The
    AST gives each package's real surface (functions, signatures,
    docstrings); DuckDB gives the data's real shape (schemas, row samples,
    taxonomy counts); the skills inventory gives what exists today. No
    model touches these; they are facts.
  * STUBS (stubs.py) — Mellea `@generative` functions. The docstring is a
    SPEC (what the output must be), the arguments are the instruments'
    facts, the return is typed. There is no prompt string anywhere in this
    package — that is the point, and the ban is enforced by grep in
    `gen lint`.
  * LAWS (laws.py) — Mellea Requirements with deterministic validation_fn,
    checked against the same instruments: a generated skill may only name
    tools the AST says exist; a generated word may not be taken in the
    ontology; frontmatter must parse and fit Agent Skills std. Generation
    that fails its laws is repaired once (a revise stub fed the failures)
    and refused if still failing — refused means NOT WRITTEN, with the
    failures reported.

Every generated file carries a provenance header: which stub, which model,
which instrument hashes. Editing a generated file is editing the wrong
thing — edit the instruments (the code, the data) and regenerate.

WHY THIS IS THE SOCIALITE LESSON APPLIED. Custom prompts rot: they encode
yesterday's surface in prose nothing checks. Instruments cannot rot (they
are recomputed), stubs barely can (they state intent, not facts), and laws
turn drift into a failing check instead of a wrong document.
"""

from ._session import gen_session
from .engine import gen_skill, gen_word, lint
from .instruments import duck_shape, package_surface, skills_inventory

__all__ = [
    "duck_shape",
    "gen_session",
    "gen_skill",
    "gen_word",
    "lint",
    "package_surface",
    "skills_inventory",
]
