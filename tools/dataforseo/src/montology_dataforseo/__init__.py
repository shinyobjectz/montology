"""DataForSEO as Mellea tools.

Credentials come from the environment at call time — DATAFORSEO_LOGIN and
DATAFORSEO_PASSWORD (the API uses HTTP Basic auth) — and are never stored.
A missing credential answers with the repair, not a stack trace, because the
person reading it is a marketer, not an engineer.

Each @tool is also a plain function, so the MCP server exposes the same
surface without a second wrapper.
"""

from .tools import serp_search, keyword_ideas, mellea_tools

__all__ = ["mellea_tools", "serp_search", "keyword_ideas"]
