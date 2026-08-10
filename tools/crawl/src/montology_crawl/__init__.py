"""montology-crawl: local crawling for brand intelligence.

TWO RULINGS, MADE ONCE:

  * **crawl4ai over crawlee-python.** Both drive Playwright; the difference
    is what comes out. Crawlee is crawl INFRASTRUCTURE (queues, storage,
    proxies) built for production scrapers; crawl4ai's whole design goal is
    LLM-READY OUTPUT — clean markdown per page — which is what an agent
    consumes. We are feeding an agent, not running a scraping farm.
  * **The agent writes the React, not a converter.** html-to-react-components
    (roman01la) mechanically splits annotated HTML into component files — it
    is years dormant, JS-side, and mechanical conversion preserves markup
    while losing meaning. The valuable pipeline is: `page_sections` hands
    the agent clean section HTML + the brand kit, and the agent writes
    idiomatic, tokenised React into the brand's component library. The
    brand-crawl skill is that method.

Playwright's browser is a one-time explicit download: `montology crawl
setup`. Every tool answers a missing browser with that repair.
"""

from .brand import COMPONENT_TYPES, lint as brand_lint, register as brand_register, scaffold as brand_scaffold
from .tools import brand_kit, fetch_page, mellea_tools, page_sections

__all__ = ["COMPONENT_TYPES", "brand_kit", "brand_lint", "brand_register", "brand_scaffold", "fetch_page", "mellea_tools", "page_sections"]
