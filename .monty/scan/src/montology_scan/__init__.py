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
from .drift import csv as drift_csv
from .drift import measure_history, render as render_drift
from .vitals import build_vitals, vitals, vitals_json
from .explain import explain
from .guard import run_hook as guard_hook
from .rename import migrate
from .styles import (design_candidates, design_lint, ingest_theme,
                     recipe_candidates, style_surface, tailwind_theme)

__all__ = ["candidates", "declarations", "languages_covered", "design_candidates", "design_lint", "drift_csv", "explain", "guard_hook", "build_vitals", "measure_history", "vitals", "vitals_json", "ingest_theme", "lint", "migrate",
           "recipe_candidates", "sg", "style_surface", "tailwind_theme"]
