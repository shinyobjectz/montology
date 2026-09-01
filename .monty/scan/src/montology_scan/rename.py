"""Ontology migration: propagate a rename through the code.

The rename ledger's other half. The engine is our own tree-sitter parse —
not a text replace, and not a pattern shell-out: identifier-class TOKENS
with the exact old text are rewritten in every position a name can occupy
(expression, type, property, field, constant), across every language the
scan covers, while strings and comments are structurally untouchable.

Montology never edits code silently: the default is a sweep that reports
file-by-file counts; ``apply=True`` writes, and the message says to do
that on a clean git tree — the diff is the review.
"""

from __future__ import annotations

from pathlib import Path

from montology_core import workspace_root

from .surface import LANG_BY_EXT, MAX_BYTES, _iter_files

# every node type an identifier travels as, across the covered grammars.
# `simple_identifier` is Swift's and Kotlin's spelling of the plain name — its
# absence made `monty migrate` report a Swift tree as already clean while every
# function, property and enum case still said the old word, which is the worst
# way for a sweep to fail: a confident "clean" over files it could not see.
IDENT_TYPES = {
    "identifier", "type_identifier", "property_identifier",
    "field_identifier", "constant", "alias", "atom",
    "shorthand_property_identifier", "shorthand_property_identifier_pattern",
    "statement_identifier", "simple_identifier",
}


def _variants(was: str, now: str) -> list[tuple[str, str]]:
    """The case shapes an identifier travels in: snake, Pascal, UPPER."""
    def pascal(s: str) -> str:
        return "".join(w.title() for w in s.replace("-", "_").split("_"))

    pairs = [(was, now), (pascal(was), pascal(now)), (was.upper(), now.upper())]
    seen, out = set(), []
    for a, b in pairs:
        if a != b and a not in seen:
            seen.add(a)
            out.append((a, b))
    return out


def _hits(node, targets: dict[bytes, bytes]) -> list[tuple[int, int, bytes]]:
    """(start, end, replacement) for every identifier leaf matching a target."""
    out = []
    stack = [node]
    while stack:
        n = stack.pop()
        if n.child_count == 0:
            if n.type in IDENT_TYPES and n.text in targets:
                out.append((n.start_byte, n.end_byte, targets[n.text]))
        else:
            stack.extend(n.children)
    return out


def migrate(was: str, now: str, apply: bool = False, root: Path | None = None) -> str:
    """Sweep (default) or rewrite (apply=True) every case variant of a
    renamed identifier, by token, in every covered language."""
    from tree_sitter_language_pack import get_parser

    root = root or workspace_root()
    targets = {a.encode(): b.encode() for a, b in _variants(was, now)}
    per_variant: dict[bytes, int] = {t: 0 for t in targets}
    touched: list[str] = []
    parsers: dict[str, object] = {}

    for f in _iter_files(root):
        lang = LANG_BY_EXT[f.suffix]
        try:
            if lang not in parsers:
                parsers[lang] = get_parser(lang)
            if f.stat().st_size > MAX_BYTES:
                continue
            source = f.read_bytes()
            tree = parsers[lang].parse(source)  # type: ignore[union-attr]
            hits = _hits(tree.root_node, targets)
        except Exception:  # noqa: BLE001 — an unparsable file is skipped, not fatal
            continue
        if not hits:
            continue
        for start, end, _ in hits:
            per_variant[source[start:end]] += 1
        touched.append(f"  {f.relative_to(root)}: {len(hits)} occurrence(s)"
                       + (" REWRITTEN" if apply else ""))
        if apply:
            for start, end, replacement in sorted(hits, reverse=True):
                source = source[:start] + replacement + source[end:]
            f.write_bytes(source)

    report = [f"  {a} -> {b}: {per_variant[a.encode()]} occurrence(s)"
              if per_variant[a.encode()] else f"  {a} -> {b}: clean"
              for a, b in _variants(was, now)]
    report += touched
    total = sum(per_variant.values())
    if total and not apply:
        report.append(f"apply with: monty migrate {was} {now} --apply  "
                      "(on a CLEAN git tree — review the diff, then commit)")
    if not total:
        report.append("the code is already clean of the old name.")
    return "\n".join(report)
