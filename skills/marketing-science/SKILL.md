---
name: marketing-science
description: Data science that stays marketing-shaped — rates over raws, uncertainty always, segments from embeddings, taxonomy joins before comparisons, effect sizes in currency. Use whenever the marketer asks to analyze performance, compare campaigns or creatives, test whether something "worked", segment customers, or forecast — the method here decides which numbers are allowed to be spoken.
---

# Marketing science

The stack: DuckDB (`monty sql` / `query_warehouse`) is the store, polars
the frame when you write Python, scipy/statsmodels the stats, scikit-learn
the segmentation, plotly→`chart_artifact` the picture. All of it obeys the
house rule: a number you speak is a number that a query or a script printed
this session.

## Rates, never raws

Raw counts are not comparable and must not be compared. Before any
comparison, name the denominator:

| never say | say | denominator |
|---|---|---|
| "this post got 5,000 likes" | engagement rate | followers at post time |
| "campaign A got more clicks" | CTR, CPC | impressions, spend |
| "we made $40k from ads" | ROAS, CPA | spend, conversions |
| "signups went up" | rate vs. same weekday/period | traffic, seasonality |

## Uncertainty is part of the number

- A difference without an interval is an anecdote. Two-sample comparisons
  get a scipy test AND a bootstrap CI; report the interval, not the p-value
  alone.
- **Minimum floors before declaring a winner**: no A/B verdict under ~100
  conversions per arm or a CI that excludes zero — below that, say
  "indistinguishable so far" and compute how much more data is needed.
- Effect size in currency beats significance in stars: "B beats A by
  $0.40–$1.10 CPA (95% CI)" is the sentence; "p<0.05" alone is banned.

## Segments come from embeddings, names come from terms

Customer/content segmentation: embed the texts with the zoo
(`embed_text("text-minilm", …)` or embeddinggemma), cluster with KMeans
(scikit-learn), then NAME each cluster from its distinguishing terms
(BERTopic/keyphrases) — never from vibes. Report cluster sizes; a segment
under ~5% of rows is noise until it recurs.

## Join the taxonomy before comparing categories

"Which categories perform?" requires categories that mean something:
classify or join against `ontology.taxonomy` (IAB, Google Product,
Schema.org) FIRST, then aggregate. A hand-typed category column is a
spelling contest, not a dimension.

## Time is never flat

- Week-over-week compares the same weekday-mix; month totals hide it.
- Before "the campaign worked": check the same window last period and
  `statsmodels` seasonal decomposition when there is a year of history.
- Cohort views (by first-touch week) for anything retention-shaped.

## The picture is an artifact

Charts go through `chart_artifact(sql, kind, x, y)` — self-contained HTML
the client renders. A chart's query is its provenance; never chart numbers
that did not come from the stated query.

## Rules

- Numbers come from tools, never from memory — if a tool did not return it in this session, do not state it.
- Categories are looked up, not guessed; taxonomy_search output is a category, a hunch is not.
- When a key or dependency is missing, relay the repair the tool gives — do not improvise workarounds.
