"""montology-crawl: local crawling for brand intelligence.

TWO RULINGS, MADE ONCE:

  * **crawl4ai over crawlee-python.** Both drive Playwright; the difference
    is what comes out. Crawlee is crawl INFRASTRUCTURE (queues, storage,
    proxies) built for production scrapers; crawl4ai's whole design goal is
    LLM-READY OUTPUT — clean markdown per page — which is what an agent
    consumes. We are feeding an agent, not running a scraping farm.
  * **Two component tiers, one registry (capture.py refined the old
    "agent writes the React" ruling).** CAPTURED components are mechanical
    HTML→JSX conversions — faithful evidence, renderable immediately,
    filling the shadcn-shaped registry at scaffold time. BUILT components
    are the agent's idiomatic, tokenised rebuilds — the only tier the
    design laws (tokens import, no literal hex) gate, and the only tier
    deliverables come from. Conversion lost meaning as DESIGN; as EVIDENCE
    it is exactly right.

Playwright's browser is a one-time explicit download: `monty crawl
setup`. Every tool answers a missing browser with that repair.
"""

from .audit import brand_audit
from .capture import capture_component, html_to_jsx
from .logos import logo_fetch, logo_search
from .socials import brand_index, discover_socials
from .render import render as brand_render, render_setup as brand_render_setup
from .creative import FORMATS, assets as brand_assets, brief as brand_brief
from .brand import COMPONENT_TYPES, lint as brand_lint, register as brand_register, scaffold as brand_scaffold
from .tools import brand_kit, fetch_page, mellea_tools, page_sections

__all__ = ["COMPONENT_TYPES", "FORMATS", "brand_assets", "brand_audit", "brand_brief", "brand_render", "brand_render_setup", "brand_kit", "brand_lint", "brand_register", "brand_scaffold", "brand_index", "capture_component", "discover_socials", "fetch_page", "html_to_jsx", "logo_fetch", "logo_search", "mellea_tools", "page_sections"]
