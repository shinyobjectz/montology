"""montology-scan: what the code claims, measured.

The multiast layer, two engines with one division of labour:

  * **tree-sitter** (via tree-sitter-language-pack: 100+ maintained
    grammars, zero grammar-writing) powers the INSTRUMENTS — every
    declaration in every language, as rows.
  * **ast-grep** (invoked, never linked — a single fast binary) powers
    structural SEARCH: agents ask for patterns, not regexes.

The lint is where the ontology bites the codebase: a declaration named
after a word that means something else is a COLLISION and fails the
build, with the repair attached.
"""

from .surface import declarations, languages_covered
from .lint import lint, candidates
from .astgrep import sg
from .rename import migrate
from .styles import design_candidates, design_lint, style_surface

__all__ = ["candidates", "declarations", "languages_covered", "design_candidates", "design_lint", "lint", "migrate", "sg", "style_surface"]
