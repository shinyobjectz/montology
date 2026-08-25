# montology — `just` shows the action surface.

# What is live: the vocabulary, the scan, the gate
default:
    @echo "── montology ──────────────────────────────────────────"
    @uv run --no-sync monty doctor
    @echo ""
    @uv run --no-sync monty onto list | head -20
    @echo ""
    @echo "recipes: just --list   ·   the CLI: monty --help"

# Fetch deps (one lock at the root)
setup:
    uv sync

# Build the canvas bundle from canvas/ and stamp its provenance (needs Node;
# the OUTPUT is committed, so `monty canvas` works without one)
canvas:
    cd canvas && npm install --no-fund --no-audit --silent && npx vite build
    uv run monty canvas stamp

# What must pass before a commit
check:
    uv run python -m compileall -q .monty && echo "syntax ok"
    uv run python -c "import json; json.load(open('.plugin/plugin.json')); json.load(open('.plugin/mcp.json')); print('plugin manifests parse')"
    diff -rq .plugin/skills skills > /dev/null && echo "skills/ mirror in sync"
    uv run monty lint
    uv run pytest tests -q

test:
    uv run pytest tests

# Re-author montology's own vocabulary, then re-render the words skill
seed:
    uv run python -c "from montology_ontology.seed import seed; print(seed())"
    uv run monty sync

# The MCP server, stdio (what .plugin/mcp.json runs)
serve:
    uv run montology-mcp

doctor:
    uv run monty doctor

# Start the intake: the first question round opens in the browser (blocks until answered)
intake:
    uv run monty intake ask .plugin/skills/intake/phases/1-domain.json
