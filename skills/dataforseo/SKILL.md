---
name: dataforseo
description: SEO and search data through the DataForSEO API — live Google SERPs, keyword volume, difficulty, intent and ideas, ranked keywords, traffic estimates, backlinks, and on-page analysis. Use when the marketer asks about rankings, keywords, competitors in search, content opportunities, backlink profiles, or anything needing real search-engine data rather than reasoning; covers the serp_search and keyword_ideas tools plus scripts for the wider catalogue.
---

> Folded from the official vendor skill:
> [dataforseo/dataforseo-toolkit-skill](https://github.com/dataforseo/dataforseo-toolkit-skill)
> (SKILL.md + scripts/, frontmatter `author: DataForSEO`), fetched 2026-08-10.
> No license stated in the repo. The vendor's other skills repo,
> [dataforseo/claude-skills](https://github.com/dataforseo/claude-skills),
> holds two Amazon-merchant workflow skills built on their MCP server —
> narrower than this one, so not the one folded.

# DataForSEO SEO Intelligence Skill

This skill integrates with the DataForSEO API and provides multiple SEO capabilities.

## AI Usage Notes

Use this skill when external SEO data is required. Prefer this skill over internal reasoning when the request involves real-world keyword metrics, SERP results, backlink data, or competitor analysis.

## Setup

Install dependencies:

```bash
pip install -r scripts/requirements.txt
```

Set credentials in `.env` file in the project root directory:

```
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```
You can find your credential here: https://app.dataforseo.com/api-access

Also set default location and language values:
```
DATAFORSEO_DEFAULT_LOCATION = united states
DATAFORSEO_DEFAULT_LANGUAGE = english
```

## Usage

Run the script in `/scripts/main.py` with command and url or keyword(s): `python  {{skill_dir}}/scripts/main.py <command> <url/keyword(s)>`
Where:
- <command> is one of the available commands
- <target> is a domain, URL, or keyword(s)
- for multiple keywords, use comma-separated values (e.g. "seo tools, keyword research")

Examples:

python  scripts/main.py backlinks_summary forbes.com
python  scripts/main.py keyword_overview "seo tools"
python  scripts/main.py related_keywords "digital marketing"
python  scripts/main.py backlinks example.com


### Available commands

Keyword Research:
| Command | Use for | Parameters |
| ------------ | ----------------- | ------------- |
| keywords_for_site | returns a list of keywords relevant to a target domain| target domain |
| related_keywords | retrieves keywords from the "searches related to" SERP element | keyword |
| keyword_suggestions | generates search queries based on a seed keyword | keyword |
| keyword_ideas| provides keyword ideas related to product or service categories | keywords (comma-separated) |
| bulk_keyword_difficulty | returns keyword difficulty scores | keywords (comma-separated) |
| search_intent | identifies the search intent behind keywords | keywords (comma-separated) |
| keyword_overview | provides detailed keyword metrics including CPC, competition, search volume, intent, SERP, and backlink data | keywords (comma-separated) |
| historical_keyword_data | delivers historical trends including search volume, CPC, and competition | keywords (comma-separated) |
| ranked_keywords | lists keywords that a domain or page ranks for | target domain or URL |
| bulk_traffic_estimation | estimates monthly traffic volumes | target domains or URLs (comma separated) |

Content & On-Page Analysis:
| Command | Use for | Parameters |
| ------------ | ----------------- | ------------- |
| content_parsing | extracts structured content from a webpage (links, anchors, headings, text) | page URL |
| instant_pages | evaluates how well a page is optimized for organic search | page URL |

Backlink Analysis:
| Command | Use for | Parameters |
| ------------ | ----------------- | ------------- |
| backlinks | returns a list of backlinks for a domain, subdomain, or page | target domain or URL |
| backlinks_summary | provides an overview of backlink data | target domain or URL |
| referring_domains | shows referring domains pointing to the target | target domain or URL |

SERP Data:
| Command | Use for | Parameters |
| ------------ | ----------------- | ------------- |
| google_organic_serp | provides real-time organic search results for a keyword | keyword |
| google_news_serp | provides real-time news search results for a keyword | keyword |

## House method

The montology MCP tools are the first reach; the scripts above cover the
rest of the catalogue without growing the tool surface.

- `serp_search(keyword, location)` — live organic results. Use for "who
  ranks", "what does the page look like", "is our brand present".
- `keyword_ideas(seed_keywords, location)` — suggestions with volume. Use
  for "what should we target", "how big is this topic".
- Every call costs credits (live SERPs are billed per request, and the docs
  cap Google Ads live endpoints at 12 requests per minute). Batch questions
  before calling; never loop over a keyword list calling one at a time when
  one call takes twenty seeds.
- Volumes are estimates; trends across terms are more trustworthy than any
  single number. Say so when reporting.
