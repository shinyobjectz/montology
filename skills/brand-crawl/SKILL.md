---
name: brand-crawl
description: Crawl a brand's site into usable assets — LLM-ready markdown, a measured brand kit, a FULL multi-page audit (colors, fonts, Tailwind config, spacing/radii, a typed component inventory with source HTML), and a React component library in the brand's own tokens, up to complete landing pages. Use when the marketer asks to analyze a brand's site, build on-brand components or pages, audit a competitor's positioning, or pull site content for research.
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

## The complete library (audit → candidates → convert → compose)

For the FULL system, audit instead of kit — it measures multiple pages,
every stylesheet, Tailwind usage (the site's own utility frequency IS its
config), spacing/radius/shadow tokens, the button recipe, and a typed
component INVENTORY with each candidate's source HTML saved to
`sources/`:

```sh
montology crawl audit https://brand.com > audit.json
montology brand scaffold brandname audit.json    # tokens + 10-20 candidates
montology brand lint brandname                   # "0 built, N candidates awaiting conversion"
```

Then convert candidates one by one: read `sources/<candidate>.html`, write
the component in `components/` (tokens only — if the audit detected
Tailwind, mirror the site's own utilities listed in tokens.ts), register
with the candidate's type, lint. The lint line tracks built vs candidates
until the library is complete.

## Landing pages are compositions

A landing page is a `page`-type entry in `pages/` that imports ONLY library
components and tokens — `<Nav/><Hero/><Features/><Pricing/><CTA/><Footer/>`
with props for the copy. Register it like any component
(`montology brand register brandname Landing page pages/Landing.tsx`); the
same lint gates it. One design system: the page, the email, and the video
ad all shop the same manifest.

## Video ads

The remotion-ads skill (folded, with voiceover/captions/formats) consumes
this library: its brand config is FILLED from tokens.ts and manifest.json —
never re-asked — and `video-*` components drop into its compositions.

## The component-library pipeline (scaffold → components → lint → ship)

```sh
montology crawl brand https://brand.com > kit.json      # measure
montology brand scaffold brandname kit.json             # tokens.ts + manifest
# …you write components/ (below)…
montology brand register brandname Hero hero components/Hero.tsx --source https://brand.com
montology brand lint brandname                          # the gate
```

Components are stored BY BRAND AND BY TYPE (`manifest.json`) so downstream
frameworks shop the library:

- **Emails** — the `email-header` / `email-body` / `email-footer` types are
  react-email's ingredients: compose them under react-email's `<Html>`,
  render, send.
- **Video** — the `video-title` / `video-lower-third` / `video-endcard`
  types drop into Remotion compositions (use the remotion skill where
  installed); they are ordinary React, tokens and all.
- **Graphics / pages** — hero, card, pricing, banner render anywhere React
  renders; static-export for graphic design crops.

The gate (`brand lint`) is what keeps the library real: every component
must import `../tokens` (no scraped hex — tokens are the contract), carry a
type from the taxonomy, and exist where the manifest says.

## Writing the components

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
