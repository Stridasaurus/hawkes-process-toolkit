# CLAUDE.md — Hawkes-Process Toolkit

Guidance for Claude Code working in this repo. The research *state* lives in
`ROADMAP.md`; this file is about **how to work here without breaking the phase
discipline**.

## What this repo is right now — decide phase, NOT library-building

The thesis: financial order flow, neural spike trains, and geomagnetic/seismic cascades
share one conditional-intensity (Hawkes) core. But **no `/manifesto` is locked yet** and
there is **no library API yet**. Everything under `experiments/` is scratch/throwaway
code that exists only to resolve open decision-tree branches. Do **not** start building
the toolkit's real package, and do **not** promote experiment code to a public API,
until a manifesto exists. Widening scope before the decision resolves is the main
failure mode here.

The one exception: **`hawkes_core.py`** (the fitting engine) is trusted and reused
unchanged by later experiments — E2 validated it (synthetic recovery, 8/9 clean under
the 10% bar, 9/9 KS). Reuse it; don't rewrite it.

## Orientation

1. **`README.md`** — thesis + phase status.
2. **`ROADMAP.md`** — **canonical.** Decision tree (N1–N4), experiment cards (E1–E7),
   manifesto stubs, and the pre-registered outcome maps. Read the N3-alt node before any
   experiment work — it governs what runs next and what each outcome means.
3. Per-experiment `experiments/<e>/RESULTS.md` for what a given spike found.
4. Vault handoff note `[[20260704-hawkes-toolkit-roadmap-handoff]]` (in Strider's
   Obsidian vault) for cross-session context.

## Environment & verification

```bash
conda env create -f environment.yml   # first time
conda activate hawkes-env
pytest -q                             # if/when tests exist for a spike
```

Never report a fit "passing GOF" or a spike "resolved" without running it in-session and
citing the actual statistic (D, p, branching ratio n) — RESULTS.md entries are held to
that standard.

## Current frontier (as of 2026-07-07) — the two cheap spikes

N3 resolved **parametric-insufficient** (E3: exp-kernel fails GOF on Binance tick data,
D ≈ 4.7× the rejection threshold, reproduced on an independent window). This activated
**N3-alt**. Before committing to E5 or a negative rescope, run two spikes:

- **E6** — LOBSTER exp-kernel generality (adapter-only reuse of E1's AAPL sample).
- **E7** — power-law long-memory kernel on Binance (M free weights on a fixed log-spaced
  rate grid, using the existing multi-exp machinery).

**Outcome map is pre-registered in `ROADMAP.md`'s N3-alt node — read it and follow it;
do not invent a new decision rule:** E7 passes → parametric-with-long-memory sufficient →
manifesto = Stub B (kernel-pluggable engine). E7 fails / E6 passes → exp failure is
crypto-specific → promote LOBSTER to primary substrate. Both fail → return to Strider
with the E5-vs-rescope decision.

## Working disciplines

- **Pre-register before you look.** Outcome mappings and thresholds are pinned in
  `ROADMAP.md` before a spike runs. Do not adjust a rule after seeing a result.
- **Branching-ratio convention and E7 parametrization are pinned** — check the ROADMAP
  before choosing either; they were fixed deliberately.
- **Kill criteria are real** — if two substrates in a row prove data-unsuitable, the
  frontier returns to N1 with the criteria themselves under review. Don't keep burning
  substrates against an unexamined rule.
- Public repo (`github.com/Stridasaurus/hawkes-process-toolkit`) — portfolio-relevant
  for Aug-2026 quant applications; keep experiment RESULTS.md honest and citable.
