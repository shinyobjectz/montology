"""The montology CLI — written for marketers, exercised by agents.

Every message assumes the reader knows marketing and not Python: say what
happened, and when something is missing, say exactly what to do about it.
"""

from __future__ import annotations

import os

import typer

app = typer.Typer(
    name="montology",
    help="Marketing + monorepo + ontology. Data pulls, vocabulary checks, models, serving.",
    no_args_is_help=True,
)

data_app = typer.Typer(help="The taxonomy database.", no_args_is_help=True)
onto_app = typer.Typer(help="The vocabulary.", no_args_is_help=True)
zoo_app = typer.Typer(help="Local embedding models.", no_args_is_help=True)
app.add_typer(data_app, name="data")
app.add_typer(onto_app, name="onto")
app.add_typer(zoo_app, name="zoo")


@app.command()
def doctor() -> None:
    """Is everything set up? Says what is missing and how to fix it."""
    from montology_ontology import DB_PATH

    checks = [
        (DB_PATH.exists(), "taxonomy database", "run: montology data pull"),
        (bool(os.environ.get("DATAFORSEO_LOGIN")), "DataForSEO login",
         "export DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (app.dataforseo.com/api-access)"),
        (bool(os.environ.get("SCRAPECREATORS_API_KEY")), "ScrapeCreators key",
         "export SCRAPECREATORS_API_KEY (scrapecreators.com)"),
    ]
    for ok, name, repair in checks:
        mark = "ok " if ok else "MISSING"
        typer.echo(f"[{mark}] {name}" + ("" if ok else f" — {repair}"))


@app.command()
def serve(http: bool = typer.Option(False, help="Streamable HTTP instead of stdio.")) -> None:
    """Run the montology MCP server."""
    from montology_server.app import main as serve_main
    import sys

    sys.argv = ["montology-mcp"] + (["--http"] if http else [])
    serve_main()


@data_app.command("pull")
def data_pull(source: str = typer.Argument("", help="One source id, or empty for every core source.")) -> None:
    """Fetch taxonomies into the local database (seeds the vocabulary too)."""
    from montology_ontology import pull, seed

    typer.echo(seed())
    for line in pull(source or None):
        typer.echo(line)


@data_app.command("sources")
def data_sources() -> None:
    """Every taxonomy montology knows about, and the ruling on each."""
    from montology_ontology import SOURCES

    for s in SOURCES:
        typer.echo(f"{s.status:<8} {s.id:<22} {s.name}")
        typer.echo(f"         {s.why}")


@onto_app.command("check")
def onto_check(name: str) -> None:
    """Is this name free, ours, or an industry category already?"""
    from montology_ontology import check

    findings = check(name)
    if not findings:
        typer.echo(f"FREE  '{name}' is not spoken for.")
        raise typer.Exit(0)
    for f in findings:
        typer.echo(f)
    raise typer.Exit(1)


@zoo_app.command("list")
def zoo_list() -> None:
    """The registered embedding models."""
    from montology_zoo import MODELS

    for m in MODELS:
        typer.echo(f"{m.id:<16} {m.backend:<5} {m.dims:>5}d  {m.modality:<11} {m.role}")
        typer.echo(f"                 {m.note}")


@zoo_app.command("pull")
def zoo_pull(model_id: str) -> None:
    """Download a model's weights from HuggingFace."""
    from montology_zoo.pull import pull

    typer.echo(pull(model_id))
