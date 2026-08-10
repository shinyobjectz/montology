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

First use needs the browser: `monty crawl setup` (one download).

## The complete library (audit → candidates → convert → compose)

For the FULL system, audit instead of kit — it measures multiple pages
(one per KIND: a listing, a product detail, an about page), every
stylesheet, Tailwind usage (the site's own utility frequency IS its
config), spacing/radius/shadow tokens, the button recipe, and a typed
component INVENTORY. Scaffold turns that into the BRAND BOOK at
`brands/<name>/` — and the registry fills IMMEDIATELY:

```sh
monty crawl audit https://brand.com > audit.json
monty brand scaffold brandname audit.json
# -> design/tokens.ts + a shadcn-shaped registry: design/components/
#    captured/Hero.tsx, Nav.tsx, Footer.tsx… (the site's own sections,
#    converted to React on the spot), source HTML in data/sources/
monty brand lint brandname     # "0 built, N captured awaiting idiomatic rebuild"
```

CAPTURED components are evidence: faithful, renderable, exempt from the
design laws. To ship a component in a deliverable, REBUILD it
idiomatically — tokens only, no literal hex (if the audit detected
Tailwind, mirror the site's own utilities listed in tokens.ts) — into
`design/components/`, register it (status becomes built), lint. The lint
line tracks built vs captured until the registry is idiomatic.

## Landing pages are compositions

A landing page is a `page`-type entry in `design/web/` that imports ONLY
library components and tokens — `<Nav/><Hero/><Features/><Pricing/><CTA/>
<Footer/>` with props for the copy. Register it like any component
(`monty brand register brandname Landing page design/web/Landing.tsx`); the
same lint gates it. One design system: the page, the email, and the video
ad all shop the same manifest.

## Video ads

The remotion-ads skill (folded, with voiceover/captions/formats) consumes
this library: its brand config is FILLED from tokens.ts and manifest.json —
never re-asked — and `video-*` components drop into its compositions.

## The component-library pipeline (scaffold → components → lint → ship)

```sh
monty crawl brand https://brand.com > kit.json      # measure
monty brand scaffold brandname kit.json             # tokens + registry
# …you rebuild captured components idiomatically (below)…
monty brand register brandname Hero hero design/components/Hero.tsx --source https://brand.com
monty brand lint brandname                          # the gate
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

The gate (`brand lint`) is what keeps the library real: every BUILT
component must import the brand tokens (no scraped hex — tokens are the
contract), carry a type from the taxonomy, and exist where the manifest
says. Captured components need only exist — they are evidence.

## Writing the components

Two tiers, one ruling refined. CAPTURED components arrive mechanically at
scaffold time — faithful evidence, good for rendering and reference,
never for shipping. BUILT components YOU write — converted meaning, not
markup: idiomatic JSX in the brand's own tokens. Rebuilding is the work:

1. Open the captured component (`design/components/captured/Hero.tsx`) and
   its source (`data/sources/`), beside `design/tokens.ts` — name the
   palette roles (primary, surface, accent) from how the site uses them.
2. Write the rebuild into `design/components/Hero.tsx` — tokens only,
   never inline hex copied from the scrape. Name components by ROLE
   (Hero, LogoRow, PricingTier), not by page.
3. Register (status becomes built), lint, and render — every render lands
   pixels in `design/out/`, fixed-frame files at their declared size,
   everything else full-page.

Then fill the rest of the book: `monty brand logo <brand> <name>` (quality
vectors with provenance) and `monty brand index <brand>` — socials
discovered from the site, posts and media pulled into `design/image|video`,
zoo embeddings into the warehouse's `brand_index` table so the whole book
is searchable.
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
