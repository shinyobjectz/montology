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
        "This repo's vocabulary as a database, enforced against the code — "
        "ALL of the code, in every language the scan parses (Python, "
        "TypeScript, Go, Rust, Swift, Java, Ruby, Elixir, C/C++), backend "
        "and infra as much as UI. CHECK BEFORE NAMING ANYTHING "
        "(ontology_check) — a class, struct, function, type, module, table, "
        "column, endpoint, event or plain concept. repo_explain orients you "
        "on an unfamiliar codebase; scan_candidates lists names the code is "
        "asking to have defined; ontology_lint reports collisions with their "
        "repair; workspace_config shows and changes what the gate enforces. "
        "Design tokens live here too, as one kind of word among many."
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
                 owner: str = "", code: str = "", pos: str = "") -> str:
    """Author a word — check-first: a taken name is refused with findings.
    `pos` is what the word NAMES (verb | noun | value), which is how a
    collision on it is judged; `kind` is whose word it is. Re-renders the
    words skill on success."""
    from montology_gen import sync
    from montology_ontology import add

    got = add(name, definition, test=test or None, kind=kind,
              owner=owner or None, code=code or None, pos=pos or None)
    if got.startswith("REFUSED"):
        return got
    return got + "\n" + sync()


@mcp.tool
def ontology_amend(name: str, definition: str = "", test: str = "", note: str = "",
                   code: str = "", owner: str = "", pos: str = "", why: str = "") -> str:
    """Correct what a word already says — a later ruling narrowed it, the
    test was loose, the code was filed wrong. The name stays; the text it
    replaces is ledgered. An unknown name is refused (that is ontology_add),
    and so is an amendment that changes nothing. Re-renders the words skill."""
    from montology_gen import sync
    from montology_ontology import amend

    # "" is how MCP says "not given" here — the CLI can still clear a field
    # with an explicit empty string, which no tool call can express.
    got = amend(name, definition=definition or None, test=test or None,
                note=note or None, code=code or None, owner=owner or None,
                pos=pos or None, why=why or None)
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
def repo_vitals() -> str:
    """The state of this repo's meaning: one verdict (TENDED / DRIFTING /
    UNTENDED) with every reason carrying its repair. Run FIRST when asked
    how a repo is doing."""
    from montology_scan import vitals

    return "\n".join(vitals())


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


@mcp.tool
def ontology_sources(status: str = "") -> str:
    """Public taxonomies montology knows about (status: core | extra |
    evaluate | skip; empty for all) — the domain each covers, where the
    data lives, the licence as published, and whether it is commercially
    usable. Reach for one when a user's vocabulary needs to join an
    industry standard rather than be invented. Relay the licence with the
    recommendation: three of the five `core` entries are CC BY 3.0 and
    require attribution, and `schemaorg` is share-alike."""
    from montology_ontology import render_sources

    return "\n".join(render_sources(status))


@mcp.tool
def repo_explain() -> str:
    """The one-shot anatomy of this repo: surface, vocabulary had and
    asked-for, semantic clusters vs directory structure, design system,
    contradictions. Run FIRST on an unfamiliar codebase — it is the fastest
    orientation montology offers."""
    from montology_scan import explain

    return "\n".join(explain())


@mcp.tool
def ontology_similar(query: str, top: int = 8) -> str:
    """Does this meaning already have a word? Run BEFORE authoring one.
    String checks enforce one-word-one-meaning; this hears the dual — one
    meaning, one word — which no string check can. Needs the [semantics]
    extra, and says so with the repair when it is missing."""
    from montology_ontology import semantic_similar

    return semantic_similar(query, top=top)


@mcp.tool
def ontology_rule(dont_say: str, say: str, why: str = "") -> str:
    """Record an overload ruling: from now on, X is said as Y. This is how
    a naming argument ENDS — ontology_check on the losing term answers with
    the ruling from then on, so the choice is inherited, never re-argued."""
    from montology_ontology import rule

    return rule(dont_say, say, why or None)


@mcp.tool
def workspace_config(key: str = "", value: str = "") -> str:
    """What this workspace is tuned to, and how to change it. No arguments
    lists every setting with its value, source and effect; a key reads one;
    a key and a value set it. An unknown key or a disallowed value is
    refused with the allowed set — never coerced into something meaningless.
    """
    from montology_core import settings as cfg
    from montology_core import workspace_root

    root = workspace_root()
    if key and value:
        try:
            return "set  " + cfg.write(root, key, value)
        except (KeyError, ValueError, FileNotFoundError) as e:
            return f"REFUSED — {e.args[0]}"
    rows = cfg.effective(root)
    if key:
        rows = [r for r in rows if r["name"] == key]
        if not rows:
            return (f"REFUSED — no such setting {key!r}. "
                    f"Known: {', '.join(sorted(cfg.SETTINGS))}.")
    return "\n".join(
        f"{r['name']:<20} {r['value']!r:<20} ({r['source']}) — {r['effect']}"
        for r in rows)


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
