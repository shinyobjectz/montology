# montology — everything runs through here. `just` lists the recipes.

default:
    @just --list

# Fetch deps for every workspace package (one lock at the root)
setup:
    uv sync

# What must pass before a commit
check:
    uv run python -m compileall -q cli ontology zoo server tools && echo "syntax ok"
    uv run montology onto check montology > /dev/null 2>&1; test $? -eq 1 && echo "ontology answers"
    uv run python -c "import json; json.load(open('plugin.json')); json.load(open('mcp.json')); print('plugin manifests parse')"

# Seed the vocabulary and pull every core taxonomy
data-pull:
    uv run montology data pull

# The MCP server, stdio (what mcp.json runs)
serve:
    uv run montology-mcp

# The MCP server, stateless Streamable HTTP
serve-http:
    uv run montology-mcp --http

# Is everything set up?
doctor:
    uv run montology doctor
