---
name: creative-production
description: The full creative pipeline from a brand URL to shippable deliverables — web banner ads (IAB sizes), social statics, social video ads, React email drafts, and a React landing page — all designed inside the brand's MEASURED system. Use when the marketer wants ads, an email, a landing page, or a whole campaign built for a brand; this skill is the workflow, the others (brand-crawl, remotion-ads, marketing-science) are its organs.
---

# Creative production

One doctrine governs everything here: **scrape to measure, design to make.**
The website gives the system (tokens, voice, assets, component shapes); the
deliverable is NEW creative you design inside it. Pasting a scraped section
into an ad fails the spirit; literal hex fails the lint.

## The pipeline (once per brand)

```sh
montology crawl audit https://brand.com > audit.json   # the measured system
montology brand scaffold acme audit.json               # tokens + candidates
montology brand assets acme audit.json                 # real images, on disk
montology brand lint acme                              # know your starting state
```

Convert the 3–5 candidates the deliverables will lean on (nav, hero,
footer at minimum) so the brand's shapes exist as reference components.

## Per deliverable (repeat per ask)

```sh
montology brand brief acme banner  --goal "…"   # or social | video | email | landing
```

The brief carries everything measured — treat it as the client folder.
Then design, register, lint:

| deliverable | formats | build notes |
|---|---|---|
| **banner** | 300×250, 728×90, 160×600, 300×600, 970×250, 320×50 | one component per size, `<Name>-<w>x<h>.tsx`, frame declared inside; ~5 words + one CTA — a banner is a glance |
| **social** | 1080×1080, 1080×1350, 1080×1920, 1200×628 | same frame rules; type can be 3× larger than web; hook in the first read-line |
| **video** | reel 9:16 · square 1:1 · landscape 16:9 | hand off to the remotion-ads skill — its brand config fills from tokens.ts, `video-*` components drop in, copy per its frameworks |
| **email** | 600px width | react-email components typed `email-header/body/footer`; inline-safe styles; one goal per email |
| **landing** | responsive | a `page` composition in `pages/` importing ONLY library components + tokens; the ad's promise above the fold, same words as the ad |

Register every artifact (`montology brand register acme Name <type> <file>`)
and run `montology brand lint acme` — FAIL lines are the next edit, and the
frame law checks fixed-size ads declare their true dimensions.

## Campaign coherence

An ad, its landing page, and the follow-up email are ONE argument: the
banner's five words reappear in the hero's headline; the email continues
the same claim. Numbers in any of them obey marketing-science (a tool
printed them this session). Assets come from `assets/` (local, in the
ledger) — never hotlinked.

## Rules

- Numbers come from tools, never from memory — if a tool did not return it in this session, do not state it.
- Categories are looked up, not guessed; taxonomy_search output is a category, a hunch is not.
- When a key or dependency is missing, relay the repair the tool gives — do not improvise workarounds.
