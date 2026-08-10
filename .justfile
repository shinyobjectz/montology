# montology — `just` shows the action surface: what is live, what exists, what to do.

# What is live right now: tools, models, data, projects
default:
    @echo "── montology ──────────────────────────────────────────"
    @uv run --no-sync monty doctor
    @echo ""
    @echo "── projects (engagements) ─────────────────────────────"
    @ls -1 projects 2>/dev/null | grep -v node_modules || echo "  none yet — monty crawl audit <url> && monty brand scaffold <name> audit.json"
    @echo ""
    @echo "── skills the agent carries ───────────────────────────"
    @ls -1 .plugin/skills
    @echo ""
    @echo "── data (tracked central store) ───────────────────────"
    @du -h data/* 2>/dev/null | sed 's/^/  /' || true
    @echo ""
    @echo "recipes: just --list   ·   the CLI: monty --help"

# Fetch deps for every workspace package (one lock at the root)
setup:
    uv sync

# What must pass before a commit
check:
    uv run python -m compileall -q .monty && echo "syntax ok"
    uv run monty onto check montology > /dev/null 2>&1; test $? -eq 1 && echo "ontology answers"
    uv run python -c "import json; json.load(open('.plugin/plugin.json')); json.load(open('.plugin/mcp.json')); print('plugin manifests parse')"
    uv run monty gen lint
    uv run pytest tests -m "not integration"

# The committed proofs — full suite (integration too, where models are pulled)
test:
    uv run pytest tests

# Seed the vocabulary and pull every core taxonomy into data/
data-pull:
    uv run monty data pull

# The MCP server, stdio (what .plugin/mcp.json runs)
serve:
    uv run montology-mcp

# Is everything set up?
doctor:
    uv run monty doctor
