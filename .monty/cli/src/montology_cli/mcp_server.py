"""The montology MCP server: the vocabulary and the scan, as agent tools.

FastMCP; stdio by default (what plugin clients declare), `--http` serves
stateless Streamable HTTP. The tool surface is the same functions the CLI
exposes — one implementation, two transports.
"""

from __future__ import annotations

import argparse

from fastmcp import FastMCP

mcp = FastMCP(
    "montology",
    instructions=(
        "This repo's vocabulary as a database, enforced against the code. "
        "CHECK BEFORE NAMING ANYTHING (ontology_check). The scan measures "
        "what the code declares; lint reports collisions with their repair; "
        "candidates lists names the codebase wants defined."
    ),
)


@mcp.tool
def ontology_check(name: str) -> str:
    """Is this name free, defined, or ruled on? Run BEFORE naming anything."""
    from montology_ontology import check

    findings = check(name)
    return "\n".join(findings) if findings else f"'{name}' is not spoken for — free to define."


@mcp.tool
def ontology_words(kind: str = "") -> str:
    """The vocabulary as rows (kind: core | inner | adopted | custom | empty for all)."""
    from montology_ontology import words

    rows = words(kind or None)
    if not rows:
        return "no words yet — ontology_add the first one, or scan_candidates for material."
    return "\n".join(
        f"{w['kind']:<8} {w['name']:<24}{' [' + w['code'] + ']' if w['code'] else ''} {w['definition']}"
        for w in rows)


@mcp.tool
def ontology_add(name: str, definition: str, test: str = "", kind: str = "custom",
                 owner: str = "", code: str = "") -> str:
    """Author a word — check-first: a taken name is refused with findings.
    Re-renders the words skill on success."""
    from montology_gen import sync
    from montology_ontology import add

    got = add(name, definition, test=test or None, kind=kind,
              owner=owner or None, code=code or None)
    if got.startswith("REFUSED"):
        return got
    return got + "\n" + sync()


@mcp.tool
def scan_surface() -> str:
    """What the code declares: counts by language, skips said out loud."""
    from montology_core import workspace_root
    from montology_scan import declarations

    got = declarations(workspace_root())
    by_lang: dict[str, int] = {}
    for d in got["decls"]:
        by_lang[d["lang"]] = by_lang.get(d["lang"], 0) + 1
    lines = [f"{len(got['decls'])} declarations in {got['files']} files"]
    lines += [f"  {lang}: {n}" for lang, n in sorted(by_lang.items(), key=lambda kv: -kv[1])]
    lines += [f"  {lang}: {n} file(s) skipped (no query yet)"
              for lang, n in got["skipped_langs"].items()]
    return "\n".join(lines)


@mcp.tool
def scan_candidates(top: int = 15) -> str:
    """Vocabulary the codebase is asking for: recurring declared names with no word."""
    from montology_scan import candidates

    rows = candidates(top=top)
    if not rows:
        return "no candidates — every recurring declared name has a word (or is noise)."
    return "\n".join(f"{c['count']:>4}x  {c['name']}  ({c['kind']})" for c in rows)


@mcp.tool
def ontology_lint() -> str:
    """The gate: collisions, code resolution, drift — each FAIL carries its repair."""
    from montology_gen import lint as gen_lint
    from montology_scan import lint as scan_lint

    return "\n".join(scan_lint() + gen_lint())


@mcp.tool
def structural_search(pattern: str, lang: str = "") -> str:
    """ast-grep over the repo: a pattern that PARSES, e.g. 'def $F($$$)' with lang=python."""
    from montology_scan import sg

    return sg(pattern, lang)


def main() -> None:
    from montology_core import load_env

    load_env()
    parser = argparse.ArgumentParser(description="The montology MCP server.")
    parser.add_argument("--http", action="store_true", help="serve stateless Streamable HTTP instead of stdio")
    parser.add_argument("--port", type=int, default=8848)
    args = parser.parse_args()
    if args.http:
        mcp.run(transport="http", host="127.0.0.1", port=args.port, stateless_http=True)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
