"""ScrapeCreators as Mellea tools.

SCRAPECREATORS_API_KEY from the environment at call time; a missing key
answers with the repair. Same design as montology-dataforseo: each @tool is
a plain function the MCP server can expose unchanged.
"""

from .tools import creator_profile, creator_posts, mellea_tools

__all__ = ["mellea_tools", "creator_profile", "creator_posts"]
