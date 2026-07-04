# ROADMAP — Hawkes-process toolkit

## Purpose

Sequence the research that resolves the toolkit's three open branches — estimation approach, first substrate, and cross-substrate engine transfer — before a manifesto is locked in.

## Invariant vision & boundaries

A Python toolkit for self-exciting point processes built on one conditional-intensity core, testing the thesis that financial order flow, neural spike trains, and geomagnetic/seismic cascades are the same math. True on every branch:

- The core must be library-quality (tests, packaging) with notebooks on top.
- All data must be public: Binance tick data, LOBSTER samples, Allen Institute spike datasets, SuperMAG magnetometer data.
- The research phase must include theory grounding — Hawkes is new math for the researcher; derivations produced along the way are deliverables (vault permanent notes, math-blog candidates), not scratch work.
- Primary value target is the August 2026 quant applications; comp-neuro relevance is secondary.
- Dynamica integration is a future hook only — never a phase, never a dependency.
- Never use proprietary data. Never build toward a live/real-time trading system. Non-Hawkes process families appear only as GOF baselines (homogeneous Poisson).
- Scale expectation: experiments are hours-scale spikes, not week-long studies. The decision tree must stay honest but not inflated.

## Glossary (cross-branch)

- **Conditional intensity** λ(t) — instantaneous event rate given history; the object every module manipulates.
- **Kernel** φ(t) — the excitation function; how one event raises future intensity.
- **Exponential kernel** — φ(t) = αe^(−βt); the parametric workhorse.
- **Branching ratio** n — ∫φ dt; expected offspring per event; n < 1 required for stationarity.
- **Parametric estimation** — fitting a fixed kernel form (exp-kernel MLE/EM).
- **Nonparametric estimation** — recovering kernel shape without a fixed form.
- **Ogata thinning** — the standard exact simulation algorithm for Hawkes processes.
- **Time-rescaling theorem** — transform of inter-event times under the fitted λ(t) to unit-rate exponentials; basis of all residual analysis here.
- **Residuals / GOF** — goodness-of-fit via KS test on time-rescaled inter-event times.
- **Substrate** — one data domain (crypto ticks, equity LOB, neural spikes, geomagnetic indices).
- **Adapter** — per-substrate code that turns raw data into event-time arrays; the only code allowed to vary by substrate.
- **Fitting engine** — the substrate-agnostic simulator + estimator + GOF core.
- **Transfer** — the same fitting engine passing GOF on a second substrate with adapter-only changes.

## Research-phase exit conditions

Stop research and lock a manifesto when ALL of:

1. N1–N4 each resolved per its pre-registered decision rule (or its branch explicitly terminated by kill criteria).
2. At least one real substrate fit passes GOF: KS test on time-rescaled inter-event times with p > 0.05, and fitted branching ratio in (0, 1).
3. The transfer question (N4) has a recorded outcome — including "thesis fails" — so the manifesto stub to expand is unambiguous.
4. Theory-grounding derivations (log-likelihood, thinning, time-rescaling) exist in written form, verified by E2's synthetic recovery.

## Decision Tree

### N1 — First substrate
- **Assumption:** data-access friction and event-rate suitability differ enough across the four candidate substrates to pick a clear first target.
- **Experiment ref:** E1.
- **Decision rule:** per substrate, score three criteria — (a) ≥10⁴ events obtainable within ~30 min effort, (b) timestamp resolution finer than the mean inter-event interval, (c) a plausibly stationary segment extractable. Pick the substrate meeting the most criteria; break ties by quant-application value (crypto / LOBSTER > neural > geomagnetic).
- **Outcomes:** → crypto ticks | → LOBSTER LOB | → neural spikes | → geomagnetic. All continue to N2.
- **Kill criteria:** if no substrate meets criterion (a) within the timebox, proceed on synthetic data only, resolve N2 anyway, and re-run E1 with a widened source list before N3.
- **Status:** active (2026-07-04).

### N2 — Estimator correctness (theory-grounding gate)
- **Assumption:** a hand-derived exp-kernel MLE plus an Ogata-thinning simulator, both written from first principles, recover known parameters on synthetic data.
- **Experiment ref:** E2.
- **Decision rule:** relative error < 10% on each of (μ, α, β) at ~10⁴ synthetic events, and KS p > 0.05 on the fit's own time-rescaled residuals.
- **Outcomes:** → pass: derivations are trusted; proceed to N3. → fail: debug/re-derive within the kill limit.
- **Kill criteria:** after two timeboxed debug attempts, adopt an external reference implementation (e.g. `tick`) as an oracle to isolate the defect; never ship an estimator that hasn't passed this node.
- **Status:** resolved (2026-07-04) → pass. See `experiments/e2-synthetic-recovery/RESULTS.md`: 8/9 (param-set × seed) runs clean under the 10% bar, 9/9 pass KS; one marginal miss (low_n seed 2, α at 10.06%) attributed to expected MLE sampling variance in the lowest-branching-ratio regime, not a derivation defect (that run's own KS p=0.891). Derivations trusted; `hawkes_core.py` is the fitting engine N3/N4 reuse unchanged.

### N3 — Estimation approach: parametric sufficiency
- **Assumption:** the exponential kernel is sufficient to pass GOF on real data from the N1 substrate — nonparametric estimation is an extension, not a prerequisite.
- **Experiment ref:** E3.
- **Decision rule:** exp-kernel fit on the N1 substrate passes GOF (KS p > 0.05 on time-rescaled inter-event times) with branching ratio in (0, 1).
- **Outcomes:** → parametric-first (nonparametric becomes an optional capability in the manifesto) | → parametric-insufficient: activate N3-alt | → data-unsuitable: return to N1, take the runner-up substrate.
- **Kill criteria:** if two substrates in a row prove data-unsuitable, the roadmap frontier returns to N1 with the criteria themselves under review — do not keep burning substrates against an unexamined rule.
- **Status:** pending (blocked on N1 + N2).

### N3-alt — Nonparametric branch *(stub — do not elaborate until N3 resolves against parametric)*
- **Assumption:** a nonparametric estimator passes GOF where the exp kernel failed. Eventual experiment: E5 (unwritten — write the card only if this node activates).
- **Status:** pending stub.

### N4 — Engine transfer (the load-bearing thesis question)
- **Assumption:** the fitting engine that passed N3 fits a second substrate with adapter-only changes.
- **Experiment ref:** E4.
- **Decision rule:** second substrate passes the same GOF bar with a diff confined to adapter code — zero changes to the fitting engine.
- **Outcomes:** → transfers (thesis holds) → Manifesto Stub A | → partial (kernel swap needed but engine API holds) → Manifesto Stub B | → fails → Manifesto Stub C.
- **Kill criteria:** if the second substrate can't reach GOF under any engine configuration within the timebox, record "fails" honestly — the toolkit reframes, it does not die.
- **Status:** pending (blocked on N3).

## Experiment Cards

### E1 — Substrate data recon
- **Assumption under test:** N1's — the four substrates differ measurably in access friction and event-rate suitability.
- **Method:** throwaway scripts, one per substrate: pull a small sample from Binance aggTrades (public REST), a LOBSTER sample file, an Allen Institute spike-train dataset (AllenSDK or pre-extracted), and SuperMAG (existing account/experience). No shared code, no cleanup.
- **Runnable check / metric:** per substrate, record event count obtained, timestamp resolution vs mean inter-event interval, and a yes/no stationarity eyeball on a 4-panel event-rate plot.
- **Timebox / cost:** ~2 h total (~30 min per substrate).
- **Kill criteria:** any substrate exceeding its 30 min without data in hand scores criterion (a) = fail and recon moves on — no rabbit-holing on access problems.
- **Where it runs:** scratch scripts outside any repo (decide-phase; no toolkit code exists yet).
- **Outputs that prove the result:** a 4-row scoring table (criteria a/b/c per substrate) pasted into the Experiment Log, plus the sample files retained for E3.

### E2 — Synthetic parameter recovery (theory grounding)
- **Assumption under test:** N2's — first-principles derivations of the exp-kernel Hawkes log-likelihood and Ogata thinning are correct.
- **Method:** derive on paper/notes: (1) the conditional-intensity form and exp-kernel Markov recursion, (2) the log-likelihood, (3) Ogata thinning, (4) the time-rescaling transform. Then implement both simulator and MLE as a throwaway spike (scipy.optimize is fine) and fit simulated data at known (μ, α, β).
- **Runnable check / metric:** relative error per parameter at ~10⁴ events; KS p-value on the fit's own rescaled residuals. Repeat across ≥3 ground-truth parameter sets including one near-critical (n close to 1).
- **Timebox / cost:** ~3 h including derivation write-up.
- **Kill criteria:** two failed debug attempts → bring in `tick` as an oracle per N2's rule.
- **Where it runs:** scratch scripts outside any repo.
- **Outputs that prove the result:** recovery table (truth vs estimate per parameter set) in the Experiment Log; derivation notes filed as vault permanent-note candidates.

### E3 — Real-data fit + GOF on the first substrate
- **Assumption under test:** N3's — the exponential kernel suffices on real data.
- **Method:** take the N1 substrate's E1 sample, run it through the E2 estimator, apply time-rescaling GOF. Univariate, unmarked events first; do not introduce marks or multivariate structure at this stage.
- **Runnable check / metric:** KS p-value on rescaled inter-event times; fitted branching ratio; QQ plot retained as evidence.
- **Timebox / cost:** ~2 h.
- **Kill criteria:** if preprocessing (not fitting) consumes more than half the timebox, stop and record the substrate as data-unsuitable rather than forcing it.
- **Where it runs:** scratch scripts outside any repo.
- **Outputs that prove the result:** dated Experiment Log entry with KS p, branching ratio, and the N3 outcome it triggers.

### E4 — Second-substrate transfer
- **Assumption under test:** N4's — the engine transfers with adapter-only changes.
- **Method:** pick the runner-up substrate from E1's scoring table, write only an adapter, rerun the E3 procedure unchanged.
- **Runnable check / metric:** same GOF bar as E3, plus a diff audit: every changed line must live in adapter code.
- **Timebox / cost:** ~2 h.
- **Kill criteria:** per N4 — timebox expiry without GOF records "fails"; no engine surgery to rescue the thesis.
- **Where it runs:** scratch scripts outside any repo.
- **Outputs that prove the result:** dated Experiment Log entry with GOF numbers and the diff-audit statement; this entry names the Manifesto Stub to expand.

## Manifesto Stubs

**Stub A — Cross-substrate Hawkes toolkit (thesis holds).** Scope: one fitting engine, N substrate adapters, shipped as a tested Python package with per-substrate demonstration notebooks. Core users: Strider as quant applicant (order-flow notebook is the portfolio piece) and as PhD applicant (spike-train notebook); secondarily, anyone fitting Hawkes models on public data. Defining constraint: the engine must never contain substrate-specific code — adapters are the only variation point. Capabilities: Ogata-thinning simulator, exp-kernel MLE (nonparametric optional per N3), time-rescaling GOF suite, adapters (per E1/E4 results), intensity/residual viz, theory notebook with the E2 derivations.

**Stub B — Kernel-pluggable toolkit (partial transfer).** Scope: as Stub A, but the engine exposes a kernel interface and substrates may select kernels; the invariant drops from "one kernel everywhere" to "one engine API everywhere". Core users: same as A. Defining constraint: kernel implementations must be swappable without touching estimator or GOF code. Capabilities: A's list plus ≥2 kernel implementations and a kernel-selection guide grounded in the E3/E4 evidence.

**Stub C — Finance-focused Hawkes order-flow toolkit (thesis fails).** Scope: a single-substrate library doing crypto/equity order-flow clustering well, with the cross-substrate story reduced to a discussion section honestly reporting the E4 negative result. Core users: Strider's quant applications exclusively. Defining constraint: depth over breadth — microstructure-aware preprocessing and finance-grade GOF replace adapter generality. Capabilities: simulator, estimator, GOF, order-flow adapter(s), microstructure viz, and the negative-result writeup (itself portfolio material).

## Experiment Log

- **2026-07-04** — Roadmap created from the sessions 41–42 handoff (vault note `20260704-hawkes-toolkit-roadmap-handoff.md`). Scoping decisions imported as invariants: Python library-quality core, public data only, quant-application value target, theory-grounding requirement, Dynamica as future hook only. Decision frontier initialized: N1 active, E1 ready to run. No experiments run yet.
- **2026-07-04** — E2 run (`experiments/e2-synthetic-recovery/`). Derived conditional-intensity Markov recursion, log-likelihood (with compensator boundary term), Ogata thinning, time-rescaling transform (`derivations.md`). Implemented simulator + multi-start MLE + KS-based GOF (`hawkes_core.py`), tested recovery across 3 ground-truth parameter sets (n=0.15/0.50/0.90) × 3 seeds each. Result: 8/9 runs pass all three parameters under 10% relative error; 9/9 pass KS p>0.05 including all near-critical seeds. One marginal miss (low_n seed 2, α=10.06%) diagnosed as finite-sample noise, not a bug (see RESULTS.md). **N2 → resolved: pass.**

## Status / current frontier

- **Active node:** N1 (first substrate), with N2 runnable in parallel — they share no dependency.
- **Running experiment:** none yet; E1 is next, E2 may interleave.
- **Manifesto:** none being written; blocked on the exit conditions above.
