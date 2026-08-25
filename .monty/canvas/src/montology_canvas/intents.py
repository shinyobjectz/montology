"""What the canvas may ask the engine to do — and how it is not a second writer.

THE CANVAS HAS NO SQL. It posts an intent; the server calls the same function
`monty onto …` calls; the answer is whatever that function returned, refusal
text included. That is not tidiness — it is the whole thesis. One truth with
one gate stops being true the moment a second surface can write to the database
on its own terms, and a refusal re-worded in TypeScript is a second gate that
will drift from the first.

So the dispatch below is deliberately thin. Every entry names an existing
function and the fields it takes; there is no validation here that the engine
does not already do, because validation duplicated is validation that disagrees.
"""

from __future__ import annotations

from typing import Callable


def _intents() -> dict[str, tuple[Callable, tuple[str, ...], tuple[str, ...]]]:
    """intent -> (function, required fields, optional fields).

    Imported lazily: the ontology is the dependency, not the import graph.
    """
    from montology_ontology import (add, amend, except_add, genus_add, rigidity_set,
                                    route_add, rule, token_add)
    from montology_ontology import collide, rename_word

    return {
        "word.add":        (add,          ("name", "definition"),
                            ("kind", "owner", "code", "test", "note", "pos")),
        "word.amend":      (amend,        ("name",),
                            ("definition", "test", "note", "why")),
        "ruling.overload": (rule,         ("dont_say", "say"), ("why",)),
        "ruling.collision": (collide,     ("term", "theirs", "their_meaning", "ruling"),
                            ("decided",)),
        "ruling.rename":   (rename_word,  ("was", "now", "why"), ()),
        "ruling.except":   (except_add,   ("word", "why"), ("scope",)),
        "route.add":       (route_add,    ("from_term", "to_word"),
                            ("register", "scope", "why")),
        "genus.add":       (genus_add,    ("word", "genus"), ("why",)),
        "rigidity.set":    (rigidity_set, ("word", "value"), ()),
        "token.add":       (token_add,    ("name", "category", "value"), ("note",)),
    }


def catalogue() -> list[dict]:
    """What the canvas is allowed to ask for, as data — so the page renders its
    forms from what the engine actually accepts rather than from a copy of it
    that somebody has to remember to update."""
    return [{"intent": name, "required": list(req), "optional": list(opt)}
            for name, (_, req, opt) in sorted(_intents().items())]


def apply(kind: str, fields: dict) -> dict:
    """Run one intent. Never raises for a refusal — a refusal is an answer."""
    table = _intents()
    if kind not in table:
        return {"ok": False, "line": f"REFUSED — {kind!r} is not an intent. "
                                     f"Known: {', '.join(sorted(table))}"}
    fn, required, optional = table[kind]

    missing = [f for f in required if not str(fields.get(f, "")).strip()]
    if missing:
        return {"ok": False,
                "line": f"REFUSED — {kind} needs {', '.join(missing)}."}

    args = [fields[f] for f in required]
    kwargs = {f: fields[f] for f in optional
              if str(fields.get(f, "")).strip()}
    try:
        line = fn(*args, **kwargs)
    except TypeError:
        # positional-vs-keyword differs across the engine's writers; the ones
        # that take everything by keyword are handled here rather than by
        # keeping a second copy of each signature
        try:
            line = fn(**dict(zip(required, args)), **kwargs)
        except Exception as e:  # noqa: BLE001
            return {"ok": False, "line": f"REFUSED — {type(e).__name__}: {e}"}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "line": f"REFUSED — {type(e).__name__}: {e}"}

    text = str(line)
    return {"ok": not text.startswith("REFUSED"), "line": text}
