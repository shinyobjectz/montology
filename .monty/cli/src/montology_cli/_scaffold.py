"""Materialize a workspace: the files `monty init` lays down.

Two sources, one relative layout. Installed as a wheel, the assets ride at
``montology_cli/_scaffold`` (see the cli pyproject's force-include); in a
repo checkout, the repo root itself carries the same paths. Either way the
materializer copies `.plugin/`, `data/*.db` and `design/` and renders the
workspace-local files (justfile, CLAUDE.md, .mcp.json, .gitignore).

IDEMPOTENT, and careful about ownership: engine-owned files (skills, the
render harness) refresh on every init; user-owned files (the data dbs once
present, anything the templates would clobber) are written only when
absent. A re-run repairs what is missing and touches nothing else.
"""

from __future__ import annotations

import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from ._engine import engine_spec

JUSTFILE = """# {name} — `just` shows the action surface: what is live, what exists, what to do.

set dotenv-load := true

# What is live right now: tools, models, data, projects
default:
    @echo "── {name} ─────────────────────────────────────────────"
    @monty doctor
    @echo ""
    @echo "── projects (engagements) ─────────────────────────────"
    @ls -1 projects 2>/dev/null | grep -v -e node_modules -e README || echo "  none yet — monty crawl audit <url> && monty brand scaffold <name> audit.json"
    @echo ""
    @echo "── skills the agent carries ───────────────────────────"
    @ls -1 .plugin/skills | grep -v README
    @echo ""
    @echo "── data (the central store) ───────────────────────────"
    @du -h data/* 2>/dev/null | sed 's/^/  /' || true
    @echo ""
    @echo "recipes: just --list   ·   the CLI: monty --help"

# Is everything set up? Says what is missing and how to fix it.
doctor:
    monty doctor

# Crawl a brand site end to end and scaffold its project
brand url:
    monty crawl audit {{{{url}}}} > /tmp/monty-audit.json && monty brand scaffold $(basename {{{{url}}}} | tr -d .) /tmp/monty-audit.json

# The MCP server by hand (agents normally launch it via .mcp.json)
serve:
    monty serve
"""

CLAUDE_MD = """# {name} — a montology workspace

Marketing work happens here through `monty` (the montology CLI) and the
skills under `.plugin/skills/` — they are the method; read them before
improvising. Run `just` alone to see the action surface: what tools are
live, which projects exist, what data is loaded.

- **`projects/`** — engagements: one folder per brand, holding its measured
  tokens, components, deliverables and rendered output.
- **`data/`** — the registries (vocabulary, taxonomies, model shelf) and
  your DuckDB warehouse. Query with `monty sql "..."`.
- **`design/`** — the shared react render harness and mediums. Components
  import `@brand/*`, bound per project at render time.
- **`.monty/cache/`** — refetchable weights and browsers, never committed.

Ground rules: numbers come from tools, never memory. Categories are looked
up (`monty onto check`, taxonomy search), not guessed. When a tool answers
with a repair, relay it — do not improvise workarounds.
"""

ENV_EXAMPLE = """# Copy to .env (gitignored) — or export these in your shell.
# Vendor keys are optional; every montology tool says what it needs.
DATAFORSEO_LOGIN=
DATAFORSEO_PASSWORD=
SCRAPECREATORS_API_KEY=
# A served OpenAI-compatible model endpoint (optional — the host agent
# drafts by default, and gemma3:270m via Ollama covers one-line stubs).
MONTOLOGY_MODEL_URL=
"""

GITIGNORE = """__pycache__/
*.pyc
.DS_Store

# keys — never commit
.env
.env.*
!.env.example

# refetchable: weights, browsers, embeddings
.monty/cache/

# the registries (ontology.db, zoo.db) ARE tracked; the warehouse is
# your analytical scratch and stays local
data/warehouse.duckdb

# node
design/node_modules/
"""

PROJECTS_README = """# projects/

One folder per engagement: a brand's measured tokens (`tokens.ts`), its
component library (`components/`), deliverables, assets and rendered
output. Start one:

    monty crawl audit https://thebrand.com > audit.json
    monty brand scaffold thebrand audit.json
"""


def scaffold_source() -> Path:
    """Where the assets live: the wheel's _scaffold dir, or the repo root."""
    wheel = Path(__file__).resolve().parent / "_scaffold"
    if wheel.is_dir():
        return wheel
    repo = Path(__file__).resolve().parents[4]
    if (repo / ".plugin").is_dir():
        return repo
    raise RuntimeError(
        "scaffold assets not found — neither the wheel's _scaffold nor a "
        "repo checkout. Reinstall montology (`uvx --refresh --from ... monty`)."
    )


def _write_if_absent(path: Path, content: str, made: list[str]) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    made.append(str(path.name))


def materialize(ws: Path, name: str) -> dict:
    """Lay down the workspace at `ws`. Returns what happened, for the summary."""
    src = scaffold_source()
    made: list[str] = []
    ws.mkdir(parents=True, exist_ok=True)

    # the marker first — everything else resolves through it
    (ws / ".monty" / "cache" / "models").mkdir(parents=True, exist_ok=True)
    meta = ws / ".monty" / "workspace.toml"
    if not meta.exists():
        meta.write_text(
            f'name = "{name}"\ncreated = "{datetime.now(UTC).date()}"\n'
            f'engine = "{engine_spec()}"\n'
        )
        made.append("workspace.toml")

    # engine-owned: refreshes on every init; user additions survive
    shutil.copytree(src / ".plugin", ws / ".plugin", dirs_exist_ok=True)
    for sub in ("package.json", "package-lock.json", "render.mjs",
                "components", "email", "image", "presentation", "video", "web"):
        s = src / "design" / sub
        if not s.exists():
            continue
        if s.is_dir():
            shutil.copytree(s, ws / "design" / sub, dirs_exist_ok=True)
        else:
            (ws / "design").mkdir(parents=True, exist_ok=True)
            shutil.copy2(s, ws / "design" / sub)
    made.append(".plugin + design refreshed")

    # user-owned once present: the registries are a starting point, and a
    # workspace's ontology grows — never clobber it
    (ws / "data").mkdir(exist_ok=True)
    for db in ("ontology.db", "zoo.db"):
        if not (ws / "data" / db).exists():
            shutil.copy2(src / "data" / db, ws / "data" / db)
            made.append(db)

    (ws / "projects").mkdir(exist_ok=True)
    _write_if_absent(ws / "projects" / "README.md", PROJECTS_README, made)
    _write_if_absent(ws / ".justfile", JUSTFILE.format(name=name), made)
    _write_if_absent(ws / "CLAUDE.md", CLAUDE_MD.format(name=name), made)
    _write_if_absent(ws / ".gitignore", GITIGNORE, made)
    _write_if_absent(ws / ".env.example", ENV_EXAMPLE, made)

    # Claude Code auto-discovery: the MCP door and the skills, zero ceremony
    mcp = ws / ".mcp.json"
    if not mcp.exists():
        mcp.write_text(json.dumps({
            "mcpServers": {"montology": {
                "command": "uvx",
                "args": ["--from", engine_spec(), "montology-mcp"],
            }}
        }, indent=2) + "\n")
        made.append(".mcp.json")
    skills_link = ws / ".claude" / "skills"
    if not skills_link.exists():
        skills_link.parent.mkdir(exist_ok=True)
        skills_link.symlink_to(Path("..") / ".plugin" / "skills")
        made.append(".claude/skills -> .plugin/skills")

    return {"root": str(ws), "made": made}
