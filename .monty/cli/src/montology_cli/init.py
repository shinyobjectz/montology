"""`monty init` — link the ontology layer into an existing repo.

The footprint is deliberately minimal, because this runs inside SOMEONE
ELSE'S monorepo:

  * `.monty/` — the marker: ontology.db (fresh, empty) + montology.toml
    (name, engine pin, [scan] config). Everything discovers through it.
  * agent wiring, MERGE-SAFE: a repo that already has a CLAUDE.md gets a
    marked section appended, an existing .mcp.json gets one key merged —
    init never overwrites a file it did not author, and never touches
    anything outside the repo.
  * the words skill, rendered (empty vocabularies say so, and say what to
    do about it).

No downloads, no git init, no scaffolded directories — seconds, not
minutes. Non-interactive (`--yes`/no TTY): no prompts, `--json` summary,
idempotent re-runs.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import typer

from ._engine import engine_spec

AGENT_HARNESSES = ("claude", "cursor", "codex")

SECTION_BEGIN = "<!-- montology:begin -->"
SECTION_END = "<!-- montology:end -->"

CLAUDE_SECTION = """{begin}
## The vocabulary (montology)

This repo's words live in a database, not a doc. Before naming ANYTHING —
a class, a concept, a tag — check it: `monty onto check <name>`. The full
vocabulary is the `words` skill (generated — never hand-edit; `monty sync`
re-renders it). `monty lint` fails the build on collisions between code
and vocabulary; a FAIL line carries its repair. `monty scan --candidates`
lists recurring declared names that want a definition.
{end}"""

CODEX_MCP_NOTE = (
    "codex keeps MCP config globally — add this to ~/.codex/config.toml "
    "(init never edits files outside the repo):\n"
    "  [mcp_servers.montology]\n"
    '  command = "uvx"\n'
    '  args = ["--from", "{spec}", "montology-mcp"]'
)

TOML_TEMPLATE = """name = "{name}"
created = "{created}"
engine = "{spec}"

[guard]
# the firewall (agent pre-write hook): block | warn | off
names  = "block"   # retired words ALWAYS block; collisions follow [scan]
design = "block"   # rogue values vs tokens — only fires when tokens exist

[scan]
# which word kinds a code declaration may NOT be named after
enforced_kinds = ["core", "inner"]
# A symbol may share a word's name — but the reason and the place live in the
# database, not here: `monty onto except WORD --where "lib/**" --why "…"`.
# This list is the old reasonless form, still honoured, still reported.
allow = []
"""


def _detect_agents() -> list[str]:
    found = []
    if shutil.which("claude"):
        found.append("claude")
    if shutil.which("cursor") or Path("/Applications/Cursor.app").exists():
        found.append("cursor")
    if shutil.which("codex"):
        found.append("codex")
    return found


def _repo_root(path: Path) -> Path:
    """The enclosing repo (walk for .git), else the directory itself."""
    for candidate in (path, *path.parents):
        if (candidate / ".git").exists():
            return candidate
    return path


def _merge_mcp(path: Path, made: list[str]) -> None:
    """Add the montology server to an mcp.json WITHOUT disturbing the rest."""
    entry = {"command": "uvx", "args": ["--from", engine_spec(), "montology-mcp"]}
    if path.exists():
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError:
            made.append(f"SKIPPED {path.name}: does not parse — add the montology server yourself")
            return
        servers = data.setdefault("mcpServers", {})
        if "montology" in servers:
            return
        servers["montology"] = entry
    else:
        data = {"mcpServers": {"montology": entry}}
        path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")
    try:
        made.append(str(path.relative_to(Path.cwd())))
    except ValueError:
        made.append(path.name if path.parent.name == "" else
                    f"{path.parent.name}/{path.name}")


def _append_section(path: Path, made: list[str]) -> None:
    """Append the marked montology section unless one is already there."""
    text = path.read_text() if path.exists() else ""
    if SECTION_BEGIN in text:
        return
    section = CLAUDE_SECTION.format(begin=SECTION_BEGIN, end=SECTION_END)
    path.write_text((text.rstrip() + "\n\n" if text.strip() else "") + section + "\n")
    made.append(str(path.name) + (" (section appended)" if text else ""))


def _merge_guard_hook(root: Path, made: list[str]) -> None:
    """The firewall into .claude/settings.json — merge-safe: existing hooks
    survive; ours appends once."""
    settings = root / ".claude" / "settings.json"
    data: dict = {}
    if settings.exists():
        try:
            data = json.loads(settings.read_text())
        except json.JSONDecodeError:
            made.append("SKIPPED .claude/settings.json: does not parse — add the guard hook yourself")
            return
    cmd = "monty guard" if shutil.which("monty") else \
        f"uvx --from '{engine_spec()}' monty guard"
    hooks = data.setdefault("hooks", {}).setdefault("PreToolUse", [])
    if any("monty guard" in json.dumps(h) for h in hooks):
        return
    hooks.append({"matcher": "Write|Edit|MultiEdit",
                  "hooks": [{"type": "command", "command": cmd}]})
    settings.parent.mkdir(exist_ok=True)
    settings.write_text(json.dumps(data, indent=2) + "\n")
    made.append(".claude/settings.json (guard hook: agents cannot write drift)")


def wire_agents(root: Path, agents: tuple[str, ...]) -> dict:
    made: list[str] = []
    notes: list[str] = []
    if "claude" in agents:
        _merge_mcp(root / ".mcp.json", made)
        _append_section(root / "CLAUDE.md", made)
        _merge_guard_hook(root, made)
    if "cursor" in agents:
        _merge_mcp(root / ".cursor" / "mcp.json", made)
    if "cursor" in agents or "codex" in agents:
        _append_section(root / "AGENTS.md", made)
    if "codex" in agents:
        notes.append(CODEX_MCP_NOTE.format(spec=engine_spec()))
    return {"made": made, "notes": notes}


def init_command(path: str = ".", name: str = "", yes: bool = False,
                 as_json: bool = False, agents: str = "", upstream: str = "") -> None:
    from datetime import UTC, datetime

    target = _repo_root(Path(path).expanduser().resolve())
    from ._ui import emit

    interactive = sys.stdin.isatty() and sys.stdout.isatty() and not yes
    echo = (lambda *_: None) if as_json else (lambda s="": emit(str(s)))

    summary: dict = {"workspace": str(target), "created": [], "notes": [], "ok": True}

    ws_name = name or target.name
    if interactive:
        ws_name = typer.prompt("Workspace name", default=ws_name)
        detected = _detect_agents()
        default_agents = ",".join(detected) if detected else ",".join(AGENT_HARNESSES)
        raw = typer.prompt(
            f"Wire for which agent harnesses? ({', '.join(AGENT_HARNESSES)})",
            default=default_agents)
        chosen = tuple(a.strip() for a in raw.split(",") if a.strip() in AGENT_HARNESSES) \
            or tuple(AGENT_HARNESSES)
    else:
        wanted = [a.strip() for a in agents.split(",") if a.strip()]
        chosen = tuple(a for a in wanted if a in AGENT_HARNESSES) \
            or tuple(_detect_agents()) or AGENT_HARNESSES

    # the marker: db + config
    marker = target / ".monty"
    marker.mkdir(exist_ok=True)
    meta = marker / "montology.toml"
    if not meta.exists():
        meta.write_text(TOML_TEMPLATE.format(
            name=ws_name, created=datetime.now(UTC).date(), spec=engine_spec()))
        summary["created"].append(".monty/montology.toml")

    import os

    import montology_ontology as onto

    os.environ.setdefault("MONTOLOGY_WORKSPACE", str(target))
    db = marker / "ontology.db"
    if not db.exists():
        onto.connect(db).close()
        summary["created"].append(".monty/ontology.db (empty — yours to author)")

    if upstream:  # the org ontology: inherit before anything renders
        got = onto.pull(upstream, target)
        summary["created"].append(got.splitlines()[0])
        summary["notes"].extend(got.splitlines()[1:])

    # THE WEDGE: a Tailwind theme is a design vocabulary the repo already
    # wrote — adopt it so the very first lint is worth reading
    from montology_scan import ingest_theme, tailwind_theme

    try:
        if tailwind_theme(target):
            do_ingest = True
            if interactive:
                do_ingest = typer.confirm(
                    "  a Tailwind theme was found — adopt it as design tokens "
                    "(the theme becomes the law)?", default=True)
            if do_ingest:
                summary["created"].append(ingest_theme(target).splitlines()[0])
    except Exception as e:  # noqa: BLE001 — a broken config never blocks init
        summary["notes"].append(f"tailwind ingest skipped ({type(e).__name__})")

    wired = wire_agents(target, chosen)
    summary["created"].extend(wired["made"])
    summary["agents"] = list(chosen)
    summary["notes"].extend(wired["notes"])

    # the words skill — rendered even when empty (it says what to do)
    from montology_gen import sync as gen_sync

    summary["created"].append(gen_sync())

    missing = []
    if shutil.which("ast-grep") is None and shutil.which("sg") is None:
        missing.append({"bin": "ast-grep", "repair": "brew install ast-grep"})
    summary["missing"] = missing

    if as_json:
        typer.echo(json.dumps(summary, indent=2))
        return
    echo("")
    echo(f"✔ montology linked into {target.name}/")
    for c in summary["created"]:
        echo(f"  ✔ {c}")
    for n in summary["notes"]:
        for i, part in enumerate(str(n).splitlines()):
            echo(("  note: " if i == 0 else "  note  ") + part)
    for m in missing:
        echo(f"  warn missing: {m['bin']} — {m['repair']}")
    if not as_json:
        from ._ui import next_steps

        next_steps([
            ("monty lint", "the gate — drift with receipts; put it in CI"),
            ("monty design candidates", "the values your styles want named"),
            ("monty scan --candidates", "the words your code is asking for"),
            ("monty onto audit", "semantic hearing — meanings that collide"),
        ])
