# montology — everything runs through here. `just` lists the recipes.

default:
    @just --list

# Fetch deps for every workspace package (one lock at the root)
setup:
    uv sync

# What must pass before a commit
check:
    uv run python -m compileall -q cli ontology zoo server tools warehouse gen && echo "syntax ok"
    uv run monty onto check montology > /dev/null 2>&1; test $? -eq 1 && echo "ontology answers"
    uv run python -c "import json; json.load(open('plugin.json')); json.load(open('mcp.json')); print('plugin manifests parse')"
    uv run monty gen lint
    uv run pytest tests -m "not integration"

# Seed the vocabulary and pull every core taxonomy
data-pull:
    uv run monty data pull

# The MCP server, stdio (what mcp.json runs)
serve:
    uv run montology-mcp

# The MCP server, stateless Streamable HTTP
serve-http:
    uv run montology-mcp --http

# The committed proofs — offline fast suite (integration runs too when models are pulled)
test:
    uv run pytest tests

# Is everything set up?
doctor:
    uv run monty doctor
