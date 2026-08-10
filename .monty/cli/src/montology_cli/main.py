"""The montology CLI — an ontology context layer for any monorepo.

Every message assumes the reader is naming things in a codebase and wants
to be told, quickly, whether a name is safe and what to do when it is not.
Errors carry their repair.
"""

from __future__ import annotations

import json
import os

import typer


def run() -> None:
    """The console entry: load the workspace .env, run the app, and turn a
    missing workspace into its repair instead of a traceback."""
    from montology_core import WorkspaceError, load_env

    load_env()
    try:
        app()
    except WorkspaceError as e:
        typer.echo(str(e), err=True)
        raise SystemExit(2) from None


app = typer.Typer(
    name="montology",
    help="The ontology layer: a vocabulary as a database, enforced against the code.",
    no_args_is_help=True,
)

onto_app = typer.Typer(help="The vocabulary: check, add, rule, list.", no_args_is_help=True)
app.add_typer(onto_app, name="onto")


@app.command()
def init(path: str = typer.Argument(".", help="The repo to initialize (default: here)."),
         name: str = typer.Option("", "--name", help="Workspace name (default: the repo's)."),
         yes: bool = typer.Option(False, "--yes", help="Non-interactive: no prompts."),
         json_out: bool = typer.Option(False, "--json", help="Machine summary (implies --yes)."),
         agents: str = typer.Option("", "--agents", help="Harnesses to wire: claude,cursor,codex (default: detected).")) -> None:
    """Initialize the ontology layer into this repo: .monty/, agent wiring, the words skill."""
    from .init import init_command

    init_command(path, name, yes or json_out, json_out, agents)


@app.command()
def doctor() -> None:
    """Is everything set up? Says what is missing and how to fix it."""
    import shutil as _shutil

    from montology_core import find_root
    from montology_ontology import db_path, words

    root = find_root()
    checks = [
        (root is not None, "workspace",
         "run `monty init` in your repo — every command needs a root (.monty/)"),
        (root is not None and db_path().exists(), "ontology database",
         "run `monty init` (or `monty onto add` your first word)"),
        (root is not None and (root / ".claude" / "skills" / "words" / "SKILL.md").exists(),
         "words skill", "run `monty sync` — the agent reads the vocabulary from it"),
        (_shutil.which("ast-grep") is not None or _shutil.which("sg") is not None,
         "ast-grep (structural search)", "brew install ast-grep"),
        (_gen_backend_ok(), "gen backend (optional — definitions draft locally when present)",
         "install Ollama and `ollama pull gemma3:270m`, or set MONTOLOGY_MODEL_URL"),
    ]
    if root is not None:
        checks.insert(2, (bool(words()), "vocabulary",
                          "empty — `monty scan --candidates` lists what the code is asking for"))
    for ok, label, repair in checks:
        mark = "ok " if ok else "MISSING"
        typer.echo(f"[{mark}] {label}" + ("" if ok else f" — {repair}"))


def _gen_backend_ok() -> bool:
    import urllib.request

    if os.environ.get("MONTOLOGY_MODEL_URL"):
        return True
    try:
        urllib.request.urlopen("http://localhost:11434/api/tags", timeout=2)
        return True
    except Exception:  # noqa: BLE001
        return False


@onto_app.command("check")
def onto_check(name: str) -> None:
    """Is this name free, ours, or ruled on? Run BEFORE naming anything."""
    from montology_ontology import check

    findings = check(name)
    if not findings:
        typer.echo(f"FREE  '{name}' is not spoken for.")
        raise typer.Exit(0)
    for f in findings:
        typer.echo(f)
    raise typer.Exit(1)


@onto_app.command("add")
def onto_add(
    name: str,
    definition: str,
    test: str = typer.Option("", help="The one-line 'what is it' test."),
    note: str = typer.Option("", help="Context worth keeping with the word."),
    kind: str = typer.Option("custom", help="core | inner | adopted | custom."),
    owner: str = typer.Option("", help="The word this one lives inside (must exist)."),
    code: str = typer.Option("", help="A dotted code (prefix must resolve)."),
) -> None:
    """Author a word — check-first; a taken name is refused with findings."""
    from montology_ontology import add

    got = add(name, definition, test=test or None, note=note or None, kind=kind,
              owner=owner or None, code=code or None)
    typer.echo(got)
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    from montology_gen import sync as _sync

    typer.echo(_sync())


@onto_app.command("rule")
def onto_rule(dont_say: str, say: str,
              why: str = typer.Option("", help="Why the ruling holds.")) -> None:
    """Record an overload ruling: do not say X, say Y."""
    from montology_gen import sync as _sync
    from montology_ontology import rule

    typer.echo(rule(dont_say, say, why or None))
    typer.echo(_sync())


@onto_app.command("collide")
def onto_collide(term: str, theirs: str = typer.Argument(..., help="Whose word collides (the framework/system)."),
                 meaning: str = typer.Argument(..., help="What the term means in THEIR system."),
                 ruling: str = typer.Argument(..., help="Which side moved, and what to say now.")) -> None:
    """Record a boundary collision ruling: whose word, what theirs means, who moved."""
    from montology_gen import sync as _sync
    from montology_ontology import collide

    typer.echo(collide(term, theirs, meaning, ruling))
    typer.echo(_sync())


@onto_app.command("rename")
def onto_rename(was: str, now: str,
                why: str = typer.Argument(..., help="Required — a rename without a reason is churn.")) -> None:
    """Rename a word and ledger it — the old name retires, old material stays readable."""
    from montology_gen import sync as _sync
    from montology_ontology import rename_word

    got = rename_word(was, now, why)
    typer.echo(got)
    if got.startswith("REFUSED"):
        raise typer.Exit(1)
    typer.echo(_sync())
    from montology_scan import migrate as _migrate

    typer.echo("where the code still says the old name:")
    typer.echo(_migrate(was, now))


@onto_app.command("list")
def onto_list(kind: str = typer.Argument("", help="Filter: core | inner | adopted | custom.")) -> None:
    """The vocabulary as rows."""
    from montology_ontology import words

    rows = words(kind or None)
    if not rows:
        typer.echo("(no words yet — monty onto add NAME \"definition\", or monty scan --candidates)")
    for w in rows:
        code = f" [{w['code']}]" if w["code"] else ""
        typer.echo(f"{w['kind']:<8} {w['name']:<24}{code} {w['definition']}")


@app.command()
def scan(candidates: int = typer.Option(0, "--candidates", help="List the top N words the code is asking for.")) -> None:
    """The multiast sweep: what the code declares, measured."""
    from montology_core import workspace_root
    from montology_scan import candidates as scan_candidates
    from montology_scan import declarations

    if candidates:
        rows = scan_candidates(top=candidates)
        if not rows:
            typer.echo("no candidates — every recurring declared name has a word (or is noise)")
        for c in rows:
            typer.echo(f"{c['count']:>4}x  {c['name']:<28} ({c['kind']})  — free: monty onto check {c['name']}")
        return
    got = declarations(workspace_root())
    by_lang: dict[str, int] = {}
    for d in got["decls"]:
        by_lang[d["lang"]] = by_lang.get(d["lang"], 0) + 1
    typer.echo(f"{len(got['decls'])} declarations in {got['files']} files"
               + (f" ({got['errors']} unparsable)" if got["errors"] else ""))
    for lang, n in sorted(by_lang.items(), key=lambda kv: -kv[1]):
        typer.echo(f"  {lang:<12} {n}")
    for lang, n in got["skipped_langs"].items():
        typer.echo(f"  {lang:<12} {n} file(s) SKIPPED — no declaration query yet")


@app.command()
def lint() -> None:
    """The gate: collisions, code resolution, drift. Exit 1 on FAIL — put it in CI."""
    from montology_gen import lint as gen_lint
    from montology_scan import lint as scan_lint

    lines = scan_lint() + gen_lint()
    for line in lines:
        typer.echo(line)
    if any(line.startswith("FAIL") or line.endswith("FAILED") for line in lines):
        raise typer.Exit(1)


@app.command()
def sync() -> None:
    """Render the words skill from the database (prose is output, never source)."""
    from montology_gen import sync as gen_sync

    typer.echo(gen_sync())


@app.command()
def grep(pattern: str,
         lang: str = typer.Option("", "--lang", help="Language for the pattern (python, typescript…).")) -> None:
    """Structural search via ast-grep: `monty grep 'def $F($$$)' --lang python`."""
    from montology_scan import sg

    typer.echo(sg(pattern, lang))


@app.command()
def gen(name: str = typer.Argument(..., help="The word to draft a definition for."),
        context: str = typer.Option("", help="Usage context grounding the draft.")) -> None:
    """Draft ONE definition on the atomic tier — law-checked, refused over written wrong."""
    from montology_gen import gen_word

    typer.echo(gen_word(name, context))


@app.command()
def migrate(was: str, now: str,
            apply: bool = typer.Option(False, "--apply", help="Rewrite in place (clean git tree first).")) -> None:
    """Propagate a rename through the code: sweep every case variant; --apply rewrites."""
    from montology_scan import migrate as scan_migrate

    typer.echo(scan_migrate(was, now, apply))


@app.command()
def serve(http: bool = typer.Option(False, help="Streamable HTTP instead of stdio.")) -> None:
    """Run the montology MCP server."""
    import sys

    from montology_cli.mcp_server import main as serve_main

    sys.argv = ["montology-mcp"] + (["--http"] if http else [])
    serve_main()
