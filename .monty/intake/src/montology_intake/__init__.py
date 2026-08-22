"""montology-intake: the questions a workspace starts with, asked in a form.

The agent writes a PHASE (a JSON spec of questions); `ask` serves it as a
typeform-style page on localhost and blocks until submitted; the answers
are written to `.monty/answers/<phase>.answers.json` and the process exits
— which is the return path: run it in the background and the exit is the
notification, or watch the answers file. The agent reads the answers,
writes the next phase from them (and from `monty scan --candidates`), and
repeats. `glossary` closes the intake by rendering the whole ontology to
one page — words the intake produced land there only through
`monty onto add`, because prose is rendered, never authored.
"""

from .glossary import glossary, merged_answers, status
from .serve import ask
from .spec import intake_dir, render_form, validate_spec

__all__ = ["ask", "glossary", "intake_dir", "merged_answers", "render_form",
           "status", "validate_spec"]
