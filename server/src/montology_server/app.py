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
from montology_scrapecreators.tools import creator_posts, creator_profile, sc_api  # noqa: E402

for fn in (serp_search, keyword_ideas, creator_profile, creator_posts, sc_api):
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


@mcp.tool
def chart_artifact(sql: str, kind: str = "bar", x: str = "", y: str = "",
                   title: str = "") -> dict:
    """A chart from a warehouse query, as an MCP Apps artifact.

    Args:
        sql: The query (registries attached: ontology.*, zoo.*, your tables).
        kind: bar | line | scatter | pie.
        x: Column for the x axis (default: first column).
        y: Column for the y axis (default: second column).
        title: Chart title.
    """
    from mcp_ui_server import create_ui_resource

    from montology_warehouse import connect

    try:
        import plotly.express as px
    except ImportError:
        return {"error": "charts need the science lane: uv sync --extra science"}
    try:
        rel = connect().sql(sql)
        cols = [d[0] for d in rel.description]
        rows = rel.fetchmany(500)
    except Exception as e:  # noqa: BLE001
        return {"error": f"SQL error: {e}"}
    if not rows:
        return {"error": "the query returned no rows"}
    x = x or cols[0]
    y = y or (cols[1] if len(cols) > 1 else cols[0])
    data = {c: [r[i] for r in rows] for i, c in enumerate(cols)}
    fig = {"bar": px.bar, "line": px.line, "scatter": px.scatter,
           "pie": lambda **k: px.pie(names=k.pop("x"), values=k.pop("y"), **k)
           }.get(kind, px.bar)(x=data[x] if kind != "pie" else data[x],
                               y=data[y] if kind != "pie" else data[y], title=title or sql[:80])
    page = fig.to_html(full_html=True, include_plotlyjs=True)
    return create_ui_resource({
        "uri": "ui://montology/chart",
        "content": {"type": "rawHtml", "htmlString": page},
        "encoding": "text",
    })


@mcp.tool
def zoo_fit_artifact() -> dict:
    """The model shelf's fit table for THIS machine, as an MCP Apps artifact —
    which local models run here, with measured sizes and estimated peaks."""
    from mcp_ui_server import create_ui_resource

    from montology_zoo import fit_report

    rows = ""
    for line in fit_report():
        s = line.strip()
        if not s or s.startswith(("this machine", "peak figures")):
            continue
        cells = s.split(None, 2)
        verdict = cells[0] if cells else ""
        color = {"fits": "#15803d", "tight": "#b45309", "no": "#b91c1c",
                 "no-disk": "#b91c1c"}.get(verdict, "#334155")
        rows += (f"<tr><td style='color:{color};font-weight:600'>{html.escape(verdict)}</td>"
                 f"<td>{html.escape(cells[1] if len(cells) > 1 else '')}</td>"
                 f"<td>{html.escape(cells[2] if len(cells) > 2 else '')}</td></tr>")
    head = html.escape(fit_report()[0])
    page = ("<!doctype html><meta charset='utf-8'>"
            "<div style='font-family:system-ui;padding:12px'>"
            f"<h2>zoo fit</h2><p>{head}</p>"
            "<table style='border-collapse:collapse;font-size:14px' cellpadding='6'>"
            f"<tr><th>verdict</th><th>model</th><th>detail</th></tr>{rows}</table></div>")
    return create_ui_resource({
        "uri": "ui://montology/zoo/fit",
        "content": {"type": "rawHtml", "htmlString": page},
        "encoding": "text",
    })


@mcp.tool
def gen_assay_artifact() -> dict:
    """Every generation outcome on record, per model — the assay as a page:
    which drafter earned which tier, with the failed laws named."""
    from mcp_ui_server import create_ui_resource

    from montology_warehouse import connect

    try:
        rows = connect().execute(
            "SELECT strftime(ran_at, '%m-%d %H:%M') t, task, target, model, outcome, "
            "laws_failed FROM gen_runs ORDER BY ran_at DESC LIMIT 60"
        ).fetchall()
    except Exception:  # noqa: BLE001 — an empty assay is a fine page
        rows = []
    body = "".join(
        f"<tr><td>{html.escape(str(r[0]))}</td><td>{html.escape(str(r[1]))}</td>"
        f"<td>{html.escape(str(r[2]))}</td><td>{html.escape(str(r[3]))}</td>"
        f"<td style='font-weight:600;color:"
        f"{ {'accepted': '#15803d', 'handoff': '#334155'}.get(str(r[4]), '#b91c1c') }'>"
        f"{html.escape(str(r[4]))}</td><td>{html.escape(', '.join(r[5] or []))}</td></tr>"
        for r in rows
    ) or "<tr><td colspan='6'>no generations recorded yet — run montology gen</td></tr>"
    page = ("<!doctype html><meta charset='utf-8'>"
            "<div style='font-family:system-ui;padding:12px'><h2>gen assay</h2>"
            "<table style='border-collapse:collapse;font-size:14px' cellpadding='6'>"
            "<tr><th>when</th><th>task</th><th>target</th><th>model</th><th>outcome</th>"
            f"<th>laws failed</th></tr>{body}</table></div>")
    return create_ui_resource({
        "uri": "ui://montology/gen/assay",
        "content": {"type": "rawHtml", "htmlString": page},
        "encoding": "text",
    })


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
