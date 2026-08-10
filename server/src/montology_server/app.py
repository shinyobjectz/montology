"""The montology MCP server.

FastMCP, because it is the Python MCP framework with first-class stateless
HTTP — `montology-mcp --http` serves Streamable HTTP with no per-session
state, which is what lets a host scale it or a client reconnect without
ceremony. Default is stdio, which is what `mcp.json` declares for plugin
clients.

ARTIFACTS ARE MCP APPS RESOURCES (mcp-ui). A tool that has something visual
to say — a taxonomy tree, a SERP comparison — returns a UI resource the host
renders sandboxed. Any frontend framework may author the HTML; the protocol
only carries it.

The tool surface reuses the Mellea-wrapped functions from the tools
packages unchanged — one implementation, two transports (Mellea programs
and MCP clients).
"""

from __future__ import annotations

import argparse
import html

from fastmcp import FastMCP

from montology_ontology import DB_PATH, check as onto_check, connect

mcp = FastMCP(
    "montology",
    instructions=(
        "Marketing vocabulary, industry taxonomies (IAB and friends), and "
        "marketing data tools. Look up what a term means, find the taxonomy "
        "category a thing belongs to, and pull SERP/creator data."
    ),
)


@mcp.tool
def ontology_check(name: str) -> str:
    """Is this marketing term already defined — by us or by an industry taxonomy?"""
    findings = onto_check(name)
    if not findings:
        return f"'{name}' is not spoken for — free to define."
    return "\n".join(findings)


@mcp.tool
def taxonomy_search(query: str, source: str = "") -> str:
    """Find taxonomy categories by name — e.g. where 'cookware' sits in IAB or Google's trees.

    Args:
        query: The category or topic to look for.
        source: Optional source id to narrow (e.g. 'iab-content', 'google-product').
    """
    if not DB_PATH.exists():
        return "The taxonomy database has not been pulled yet. Repair: run `montology data pull`."
    conn = connect(readonly=True)
    sql = "SELECT source, code, name, path FROM taxonomy WHERE name LIKE ?"
    args: list = [f"%{query}%"]
    if source:
        sql += " AND source = ?"
        args.append(source)
    rows = conn.execute(sql + " LIMIT 40", args).fetchall()
    if not rows:
        return f"nothing matching {query!r}. Try a broader term, or `montology data pull` more sources."
    return "\n".join(f"{r['source']}:{r['code']}  {r['path'] or r['name']}" for r in rows)


# DataForSEO / ScrapeCreators: the same plain functions Mellea programs wrap
# (tools.mellea_tools()), registered directly — FastMCP reads the signature
# and docstring. One implementation, two transports.
from montology_dataforseo.tools import keyword_ideas, serp_search  # noqa: E402
from montology_scrapecreators.tools import creator_posts, creator_profile  # noqa: E402

for fn in (serp_search, keyword_ideas, creator_profile, creator_posts):
    mcp.tool(fn)


@mcp.tool
def query_warehouse(sql: str) -> str:
    """SQL over the marketer's local data (DuckDB) plus the attached
    registries: ontology.word, ontology.taxonomy, zoo.model, zoo.artifact,
    and any table loaded via `montology data load`.

    Args:
        sql: The query. Reads files directly too: SELECT * FROM 'file.csv'.
    """
    from montology_warehouse import query

    return query(sql)


# Crawl tools register softly: montology-crawl brings Playwright, and a
# server missing it should serve everything else rather than die.
try:
    from montology_crawl import brand_kit, fetch_page, page_sections

    for fn in (fetch_page, brand_kit, page_sections):
        mcp.tool(fn)
except ImportError:
    pass


@mcp.tool
def taxonomy_tree_artifact(source: str = "iab-content", top: str = "") -> dict:
    """An interactive taxonomy tree as an MCP Apps artifact (mcp-ui).

    Args:
        source: Which taxonomy to render.
        top: Optional top-tier name to focus on.
    """
    from mcp_ui_server import create_ui_resource

    if not DB_PATH.exists():
        rows = []
    else:
        conn = connect(readonly=True)
        sql = "SELECT code, name, path, tier FROM taxonomy WHERE source=?"
        args: list = [source]
        if top:
            sql += " AND path LIKE ?"
            args.append(f"{top}%")
        rows = conn.execute(sql + " ORDER BY path LIMIT 500", args).fetchall()

    items = "".join(
        f"<li style='margin-left:{((r['tier'] or 1) - 1) * 16}px'>"
        f"<code>{html.escape(str(r['code']))}</code> {html.escape(r['name'])}</li>"
        for r in rows
    ) or "<li>No data — run <code>montology data pull</code> first.</li>"

    page = (
        "<!doctype html><meta charset='utf-8'>"
        f"<h2 style='font-family:system-ui'>{html.escape(source)}</h2>"
        f"<ul style='font-family:system-ui;list-style:none;padding:0'>{items}</ul>"
    )
    return create_ui_resource(
        {
            "uri": f"ui://montology/taxonomy/{source}",
            "content": {"type": "rawHtml", "htmlString": page},
            "encoding": "text",
        }
    )


def main() -> None:
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
