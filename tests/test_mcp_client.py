"""A real MCP client over stdio — the protocol, not introspection."""
import asyncio
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration


def test_stdio_client_lists_and_calls():
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport

    async def run():
        t = StdioTransport("uv", ["run", "--no-sync", "montology-mcp"],
                           cwd=str(Path(__file__).resolve().parents[1]))
        async with Client(t) as c:
            tools = {x.name for x in await c.list_tools()}
            assert {"ontology_check", "taxonomy_search", "query_warehouse"} <= tools
            got = await c.call_tool("ontology_check", {"name": "zzz-definitely-free"})
            assert "not spoken for" in got.content[0].text

    asyncio.run(run())
