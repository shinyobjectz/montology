# Research notes — 2026-08-10

Three tracks investigated: instruments built, first measurements taken,
prior art checked. Every number below was produced by an instrument in
this repo on this date; nothing is projected.

## Track 1 — Drift dynamics (`monty drift`)

**Question.** How fast does a codebase's meaning drift — its lexicon of
declared names, its design vocabulary — and what does the curve look
like over years?

**Prior art.** Structural decay under AI assistance is measured:
GitClear's longitudinal studies (211M changed lines) found duplicated
code blocks up ~8x in 2024, copy/paste exceeding refactored code for the
first time on record, and churn roughly doubling from the pre-AI
baseline. Identifier-quality research (e.g. a 9,801-project study across
nine languages) established that naming consistency *decreases with
project evolution* — but statically, pre-AI-era, and with no design
dimension. Nobody publishes drift curves for design vocabularies, and
nobody has agent-era semantic time series.

**Instrument.** `monty drift --samples N`: samples the git history at N
evenly spaced first-parent commits (read-only worktrees), measuring at
each point the declaration lexicon (count, distinct names, type-token
ratio) and the design vocabulary (distinct colors, spacing values,
Tailwind arbitrary escapes).

**First observation (excalidraw, full history, 10 samples).** The
palette fragmented ~10x in two years — 4 (2021) → 11 (2022) → 27 (late
2022) → 42 (2023) distinct colors — while declarations merely doubled.
And the 2020 samples show a cleanup (17 → 5, the move to CSS variables)
that *did not hold*: fragmentation returned worse than before the
cleanup. An untended design vocabulary grows super-linearly with code,
and one-off cleanups without enforcement regress. This is precisely the
curve the guard exists to flatten.

**Open.** Human-era vs agent-era slope comparison on repos with known
heavy AI authorship; palette-fragmentation rates across a corpus; drift
curves before/after montology adoption in live repos.

## Track 2 — Institutions vs context (the guard log)

**Question.** Do agents follow *enforced* norms better than *retrieved*
guidance — and how often do settled decisions get re-litigated under
each regime?

**Prior art.** The agent-memory literature converged on an
episodic/semantic/procedural taxonomy, and names the failure mode this
track targets: the **text-action disconnect** — agents "comprehend
retrieved instructions yet fail to strictly act upon them." Proposed
remedies are memory-side (procedural memory, workflow compression,
governed memory frameworks). Enforcement-side remedies — the norm
checked at the point of action, comply-or-the-write-fails — are not
studied, and *re-litigation rate* appears to be an unclaimed metric.

**Instrument.** Every guard decision is logged (`guard_runs`: timestamp,
path, verdict, findings) — failing open, never blocking an edit.
`monty guard --stats` computes **repair-following**: a denial followed by
a clean edit to the same file within 30 minutes is a complied denial.
The compliance dataset accumulates from ordinary usage; no experiment
harness needed.

**First measurement.** The instrument's first logged pair (deny with
nearest-token repair → corrected edit → allow) measured 1/1 complied.
Trivial n, but the pipeline is live: every montology workspace with the
hook now contributes compliance data.

**Open (protocol sketch).** Same agent, same tasks, three arms: (a)
norms as CLAUDE.md prose, (b) norms as the words skill (retrieved), (c)
norms enforced by the guard. Measure naming-consistency, re-litigation
rate (settled decisions re-argued or silently reversed), and
task-completion overhead. The hypothesis: (c) closes the text-action
disconnect at near-zero overhead because the repair ships inside the
denial.

## Track 3 — Convergence (research/convergence.py)

**Question.** Does a codebase's *concept lexicon* reach a fixed point
under maintenance, and what bends the curve?

**Prior art.** Vocabulary growth in software follows Heaps' law
(sublinear, like natural language); identifiers obey Zipf/Heaps scaling
in Java/C/C++ corpora. So sublinear growth is the expected baseline —
the open questions are at the *concept* level (recurring, noise-filtered
names — the ontology-eligible lexicon), the design level (track 1 shows
palettes can grow super-linearly, i.e. AGAINST the Heaps expectation),
and the effect of enforcement.

**Instrument.** `research/convergence.py <repo> [samples]`: replays
history; at each sample, mined concepts (the product's candidate filter:
recurring, non-noise, ≥2 declarations) are adopted into a cumulative
vocabulary; reports new-concepts-per-100-new-declarations per interval.

**First measurement (flask, 15 years, 12 samples).** Strong natural
convergence in a well-tended codebase: 49 cumulative concepts after 14
years; new-per-sample declining to 1–3; the vocabulary essentially flat
since 2019 (44 → 49) while declarations grew 1,480 → 1,577. Flask —
human-curated, strong review culture — behaves like a converged
vocabulary.

**The contrast already visible.** Flask's *naming* lexicon converges
(tended); excalidraw's *design* lexicon diverges (untended). Same
instrument family, opposite curves — evidence that convergence is a
property of tending, not of software per se. The flagship open
experiment: run the closed loop (candidates → adoption → guard →
migrate) autonomously on a drifting repo and measure whether enforcement
produces the flask curve where the excalidraw curve would otherwise
occur.

## The position, after investigating

- The structural decay of AI-assisted code is established (GitClear);
  the **semantic** dimension is unmeasured — montology's instruments are
  first movers there, and the first observations (palette fragmentation
  10x/2y; cleanup-regression; tended-lexicon convergence) are real.
- The agent-memory field names the failure (text-action disconnect) but
  pursues memory-side fixes; **enforcement at the point of action** is
  the unoccupied position, and the guard log turns every workspace into
  a passive data collector for it.
- Heaps-law convergence is the known baseline for raw vocabulary; the
  concept-level and design-level curves, and whether enforcement bends
  them, are open — and both instruments needed to answer are now in
  this repo.
