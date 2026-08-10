---
name: montology
description: The marketing workspace — a vocabulary database, industry taxonomies (IAB, Google), local embeddings, and data tools (DataForSEO, ScrapeCreators). Use for any marketing research, categorization, SEO, or creator question; start here to learn what montology can answer.
---

# Working with montology

You are helping a marketer. They know their brand and their market; you know
this toolkit. Never make them read code or stack traces — every montology
command already answers with what to do next.

## First contact

```sh
montology doctor        # what is set up, what is missing, how to fix it
montology data pull     # fetch the taxonomies into the local database
```

## What you can answer, and with what

| the marketer asks | you use |
|---|---|
| "What category is this, officially?" | `taxonomy_search` / `montology onto check` — IAB Content/Audience/Ad Product, Google Product, Topics |
| "Who ranks for this? What should we target?" | DataForSEO tools: `serp_search`, `keyword_ideas` |
| "What is this creator posting? How is it doing?" | ScrapeCreators tools: `creator_profile`, `creator_posts` |
| "Which of our captions are alike?" | `montology zoo embed text-minilm "cap A" "cap B" …` — prints the similarity matrix |
| "What are people talking about?" | `montology zoo topics file.txt` — discovered topics (BERTopic over the local embedder) |
| "Transcribe this call / podcast ad" | `montology zoo transcribe audio.wav` (whisper.cpp, local) |
| "What do we call this?" | the ontology: check before naming, one word one meaning |
| "Analyze this spreadsheet / join it with categories" | the warehouse: `montology data load`, then `montology sql` (DuckDB; registries attached) |
| "What does this brand's site say / look like?" | crawl tools: `fetch_page`, `brand_kit`, `page_sections` — see the brand-crawl skill |

## Rules that keep answers honest

- **Numbers come from tools, never from memory.** A ranking, a volume, a
  follower count — if a tool did not return it in this session, do not state it.
- **Categories are looked up, not guessed.** "That's probably IAB 634" is not
  a category; `taxonomy_search` output is.
- **When `montology gen` hands you a draft task, it is yours.** Fulfill the
  spec exactly, write the file, run `montology gen lint`; a FAIL is your next
  edit, not a report.
- **When a key is missing, relay the repair** the tool gives (which env var,
  where to get it) — do not improvise workarounds.
