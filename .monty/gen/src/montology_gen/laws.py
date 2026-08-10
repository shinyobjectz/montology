"""Laws: what generated material must satisfy, checked deterministically.

Each law is a Mellea Requirement whose validation_fn reads the instruments
— never a model judging a model. The split follows Agent Skills std and
this repo's own rules:

  STRUCTURAL laws apply to every skill on disk (`gen lint`, in `just
  check`): frontmatter parses, the name is std-conformant, a description
  exists and fits, the body fits the disclosure budget.

  The DRIFT law applies to generated material: the file carries the hash
  of the facts that produced it, and lint recomputes — a database that
  moved on fails the build with the regenerate repair.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable

from .instruments import parse_frontmatter

NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DESCRIPTION_CAP = 1024      # Agent Skills std: metadata stays ~100 tokens
BODY_CAP = 24_000           # ~5k tokens: the std's instruction budget
VENDOR_WORDS = ("tree-sitter", "ast-grep", "sqlite", "ollama", "github",
                "openai", "mellea")  # fine in method prose, banned as ontology words


@dataclass(frozen=True, slots=True)
class Law:
    name: str
    description: str
    check: Callable[..., str | None]  # None = holds; str = the failure, stated

    def as_requirement(self):
        """The same law as Mellea's type, for instruct(requirements=...)."""
        from mellea.stdlib.requirements import Requirement

        return Requirement(
            self.description,
            validation_fn=lambda ctx, _c=self.check: _c(str(ctx.last_output())) is None,
            check_only=True,
        )


# ── structural: every skill, every lint ─────────────────────────────────────

def _frontmatter_parses(text: str) -> str | None:
    fm, _ = parse_frontmatter(text)
    if not fm:
        return "no parseable YAML frontmatter between --- fences"
    if not fm.get("name"):
        return "frontmatter has no name:"
    if not NAME_RE.match(str(fm["name"])):
        return f"name {fm['name']!r} is not Agent Skills std (^[a-z0-9]+(-[a-z0-9]+)*$)"
    return None


def _description_fits(text: str) -> str | None:
    fm, _ = parse_frontmatter(text)
    d = str(fm.get("description", ""))
    if not d.strip():
        return "frontmatter has no description: — it is the only thing in the agent's roster"
    if len(d) > DESCRIPTION_CAP:
        return f"description is {len(d)} chars; the roster budget is {DESCRIPTION_CAP}"
    return None


def _body_fits(text: str) -> str | None:
    _, body = parse_frontmatter(text)
    if len(body) > BODY_CAP:
        return f"body is {len(body)} chars; the disclosure budget is {BODY_CAP} (~5k tokens)"
    if not body.strip():
        return "the body is empty"
    return None


STRUCTURAL: tuple[Law, ...] = (
    Law("frontmatter.parses", "The skill's frontmatter parses and its name is std-conformant.",
        _frontmatter_parses),
    Law("description.fits", "The description exists and fits the roster budget.",
        _description_fits),
    Law("body.fits", "The body exists and fits the disclosure budget.", _body_fits),
)


def provenance_current(surface_hash: str) -> Law:
    """The drift detector: a generated skill's provenance names the surface
    hash it was drafted from; when the package's AST no longer matches, the
    skill is STALE and lint fails with the regenerate repair — this is the
    hook that forces regeneration, mechanically."""
    import re as _re

    def check(text: str) -> str | None:
        m = _re.search(r"instruments=sha256:([0-9a-f]{16})", text)
        if not m:
            return None  # provenance.present already fails a missing header
        if m.group(1) != surface_hash:
            return (f"STALE — drafted from surface {m.group(1)}, the package is now "
                    f"{surface_hash}. Repair: `monty sync`")
        return None

    return Law("provenance.current", "The skill matches the package surface it documents.",
               check)


def word_laws(taken: Callable[[str], list[str]]) -> tuple[Law, ...]:
    """Laws for a generated ontology word: free, one sentence, no vendors."""
    def _free(text: str) -> str | None:
        name = text.split(":", 1)[0].strip().lower()
        findings = taken(name)
        return f"'{name}' is already spoken for: {findings[0]}" if findings else None

    def _one_meaning(text: str) -> str | None:
        _, _, definition = text.partition(":")
        if definition.count(". ") > 1:
            return "a definition is ONE sentence; more means the word means two things"
        return None

    def _has_definition(text: str) -> str | None:
        _, sep, definition = text.partition(":")
        if not sep or len(definition.split()) < 4:
            return ("the shape is 'name: definition' with a real definition — "
                    "a bare word (observed from a 270M draft) is not one")
        return None

    def _no_vendors(text: str) -> str | None:
        low = text.lower()
        hits = [v for v in VENDOR_WORDS if v in low]
        return f"vendors are not vocabulary: {hits}" if hits else None

    return (
        Law("word.has_definition", "The output is 'name: definition', definition non-trivial.",
            _has_definition),
        Law("word.free", "The word is not already taken by us or a taxonomy.", _free),
        Law("word.one_meaning", "The definition is one sentence, one meaning.", _one_meaning),
        Law("word.no_vendors", "No vendor appears in the definition.", _no_vendors),
    )
