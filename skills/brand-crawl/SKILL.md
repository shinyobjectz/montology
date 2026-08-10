---
name: brand-crawl
description: Crawl a brand's site into usable assets — LLM-ready page markdown, a measured brand kit (colors, fonts, logo, voice), and a React component library in the brand's own tokens. Use when the marketer asks to analyze a brand's site, build on-brand components or pages, audit a competitor's positioning, or pull site content for research.
---

# Brand crawling and the component library

Three tools, one method. Everything is measured from the site itself —
colors are counted from the CSS, never guessed from the logo.

## The tools

- `fetch_page(url)` — any public page as clean markdown. Research and
  positioning audits start here.
- `brand_kit(url)` — the homepage's identity as JSON: top colors WITH
  counts, font families, logo, og metadata, a voice sample. The counts are
  the evidence; show them when a color choice matters.
- `page_sections(url)` — the page split into semantic sections (header,
  nav, section, footer) as cleaned HTML. This is component raw material.

First use needs the browser: `montology crawl setup` (one download).

## The component-library method

YOU write the React — that is the ruling, not an accident. (The mechanical
converter considered for this, html-to-react-components, is years dormant
and preserves markup while losing meaning; a section converted by hand
into idiomatic JSX with the brand's tokens is the entire value.)

1. `brand_kit(url)` → write `brands/<brand>/tokens.json` from it: the top
   counted colors become the palette (name them by role — primary, surface,
   accent — from how the site uses them), fonts become the type scale.
2. `page_sections(url)` on the pages that matter (home, product, pricing).
3. For each section worth keeping, write a React component into
   `brands/<brand>/components/` — idiomatic JSX, styled from tokens.json,
   never inline hex codes copied from the scrape. Name components by ROLE
   (Hero, LogoRow, PricingTier), not by page.
4. `brands/<brand>/index.ts` exports the library; a README lists each
   component with the URL and date it was derived from — provenance, so a
   redesign of their site is detectable.

## Rules

- Public pages only; a page that renders empty or blocks automation is
  reported as that finding — never worked around.
- Respect the site: crawl the pages the task needs, not the domain.
- Scraped copy is THEIR voice — quote it as competitive evidence; never
  republish it as the client's.
- The kit is measured: if a color feels wrong, re-run and show the counts
  rather than eyeballing a substitute.
