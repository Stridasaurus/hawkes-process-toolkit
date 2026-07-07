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
- **Status:** resolved (2026-07-04) → crypto ticks (Binance).

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
- **Status:** resolved (2026-07-04) → parametric-insufficient. See `experiments/e3-real-data-gof/RESULTS.md`: exp-kernel fit on Binance 01:00-02:00 UTC (11,873 events) gives a valid branching ratio (n=0.332) but fails GOF decisively (KS D=0.0583, p≈0.0000; critical D at this n is ≈0.0125, so D is ~4.7x the rejection threshold). Reproduced on an independent window (14:00-15:00 UTC, n=0.222, D=0.0352, p≈0.0000) — not a window-choice fluke. **Activates N3-alt.**

### N3-alt — Nonparametric branch *(activated 2026-07-04 by N3's parametric-insufficient result)*
- **Assumption:** a nonparametric estimator passes GOF where the exp kernel failed. Eventual experiment: E5.
- **Status:** decision made (2026-07-07, Strider): before committing to E5 or a negative rescope, run two cheap spikes — **E6** (LOBSTER exp-kernel generality) and **E7** (power-law long-memory kernel on Binance). Rationale: the E3 QQ signature (clean ~98% bulk, smooth top-~2% tail excess) plus the multi-scale misfit points at **long memory**, not short-scale kernel shape — the 2-exp attempt's slow component (~939ms) never tested seconds-to-minutes memory; and exp-Hawkes failing GOF on tick data while power-law kernels fit is documented microstructure literature (Hardiman & Bouchaud; Bacry–Mastromatteo–Muzy 2015 review), so the standalone negative result is weaker portfolio material than the three-option handoff assumed, while the standard fix is cheaply testable with the existing multi-exp machinery.
- **Outcome mapping (pre-registered before either experiment runs):**
  - **E7 passes GOF** → parametric-with-long-memory is sufficient → manifesto = **Stub B** (kernel-pluggable engine), with E6's result feeding the kernel-selection guide either way; N4 proceeds with the passing engine configuration.
  - **E7 fails, E6 passes** → the exp-kernel failure is crypto-specific → N1 amended: LOBSTER promoted to primary substrate, parametric path resumes toward N4 with Binance as the transfer target.
  - **Both fail** → return to Strider with exactly two options: E5 (full nonparametric) or negative-result rescope (deeper than Stub C). Pre-registered: no third parametric kernel attempt.

**Full chain of evidence (2026-07-04), most decisive last:**
1. **Attempt 1 (sum-of-2-exponentials)** — `experiments/e3-alt-two-exp-kernel/RESULTS.md`. Same window, richer parametric kernel (fast ~5.8ms + slow ~939ms components, valid branching ratio n=0.627): KS D=0.0466, p≈0.0000 — same tail-only deviation shape as the single-exponential fit, barely moved. Both engines pass their own synthetic self-tests (real model/data mismatch, not a bug).
2. **Bar-reconsideration via multi-scale subsampled KS** — `experiments/e3-alt-two-exp-kernel/gof_bar_reconsidered_RESULTS.md`. Tested whether `p>0.05` is simply too strict at n~12k by subsampling residuals down to reference sizes matching typical published Hawkes/microstructure studies (n=300 to 5000). **Decisive result: pass fraction declines monotonically from 0.30 (n=300) to 0.00 (n≥2000)** — under a correctly-specified model this should stay ≈0.95 at every n. This is the signature of a model misspecified at every scale, not one merely over-rejected by a large-n-powered test. **Reconsidering the bar answered the question — the model is the problem, not the bar.**
3. A same-session attempt to test window non-stationarity via a count-homogeneity chi-square test was run and discarded as methodologically invalid (stationary Hawkes processes are overdispersed by construction, so that test can't discriminate kernel-shape from baseline-drift). *Why* the parametric family fails (kernel shape vs. non-stationarity vs. something else) remains a genuine open question with no cheap clean test found this session — chasing the mechanism further was stopped as scope creep beyond what N3's decision rule requires.

**Bottom line: parametric estimation (1-exp and 2-exp) is robustly insufficient on Binance — not a bug, not a large-n artifact, not rescued by kernel enrichment or by relaxing the GOF bar.** This sits outside all three manifesto stubs' assumed starting point (each assumes the toolkit gets *past* N3 with a passing fit). Handed off, not resolved — three live options for the next session: (a) try the runner-up substrate LOBSTER (does anything pass, or does it fail the same way — itself a cross-substrate finding), (b) commit to full nonparametric estimation (E5, now lower-EV given kernel enrichment barely moved D), (c) accept this as the project's negative result and rescope the manifesto around it (deeper than Stub C anticipated — Stub C assumed a passing finance-only fit, not one that fails the bar entirely).

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

### E6 — Exp-kernel generality spike on LOBSTER
- **Assumption under test:** N3-alt's — whether the parametric failure is specific to Binance/crypto microstructure or general across market microstructure.
- **Method:** adapter-only — write a LOBSTER adapter (E1's retained AAPL message-file sample → event-time array, mid-morning stationary window per E1's recon), then run the unchanged E3 procedure: exp-kernel MLE from `hawkes_core.py`, time-rescaling GOF. Zero changes to the fitting engine.
- **Runnable check / metric:** KS p on rescaled inter-event times; branching ratio in (0, 1); QQ plot retained and inspected for the same tail-excess shape as Binance; secondary: the multi-scale subsampled-KS pass-fraction profile, for direct comparison against Binance's 0.30→0.00 decline.
- **Timebox / cost:** ~2 h.
- **Kill criteria:** if preprocessing consumes more than half the timebox, record E6 as inconclusive (data-unsuitable) rather than forcing it — it is a spike, not a gate.
- **Where it runs:** `experiments/e6-lobster-generality/`.
- **Note:** E6 is *not* E4 — transfer (N4) requires a *passing* engine; E6 tests failure generality. Its adapter is reusable for E4 later.
- **Outputs that prove the result:** dated Experiment Log entry with KS numbers and an explicit same-vs-different failure-shape judgment vs E3.

### E7 — Power-law (long-memory) kernel on Binance
- **Assumption under test:** the E3 QQ tail excess is long-memory misfit — a power-law kernel φ(t) ∝ (t+c)^−(1+ε), approximated as a sum of M exponentials, passes GOF where 1-exp and 2-exp failed.
- **Method:** extend `hawkes_core.py`'s multi-exp path to M components with rates log-spaced over ~1 ms to ~10 min (M ≈ 6–8) and weights tied to (or initialized from) a power-law profile; the per-component Markov recursion keeps the likelihood O(n·M). MLE via the existing multi-start optimizer; same two windows as E3 (01:00–02:00 and 14:00–15:00 UTC).
- **Runnable check / metric:** primary — KS p > 0.05 on rescaled inter-event times AND branching ratio in (0, 1), on both E3 windows. Secondary (pre-registered here, not post-hoc): multi-scale subsampled-KS pass fraction ≈ 0.95 at every reference n. Also retain a plot of the fitted kernel over the rate grid — does it actually hold a power-law profile, or collapse to a few effective components?
- **Timebox / cost:** ~3 h.
- **Kill criteria:** optimizer non-convergence after multi-start within the timebox → record "power-law approximation infeasible with current machinery" and treat as *fail* in N3-alt's outcome mapping; no bespoke optimizer engineering.
- **Where it runs:** `experiments/e7-power-law-kernel/`.
- **Outputs that prove the result:** dated Experiment Log entry with KS numbers per window, branching ratio, fitted-kernel plot, and which N3-alt outcome-mapping row it triggers.

## Manifesto Stubs

**Stub A — Cross-substrate Hawkes toolkit (thesis holds).** Scope: one fitting engine, N substrate adapters, shipped as a tested Python package with per-substrate demonstration notebooks. Core users: Strider as quant applicant (order-flow notebook is the portfolio piece) and as PhD applicant (spike-train notebook); secondarily, anyone fitting Hawkes models on public data. Defining constraint: the engine must never contain substrate-specific code — adapters are the only variation point. Capabilities: Ogata-thinning simulator, exp-kernel MLE (nonparametric optional per N3), time-rescaling GOF suite, adapters (per E1/E4 results), intensity/residual viz, theory notebook with the E2 derivations.

**Stub B — Kernel-pluggable toolkit (partial transfer).** Scope: as Stub A, but the engine exposes a kernel interface and substrates may select kernels; the invariant drops from "one kernel everywhere" to "one engine API everywhere". Core users: same as A. Defining constraint: kernel implementations must be swappable without touching estimator or GOF code. Capabilities: A's list plus ≥2 kernel implementations and a kernel-selection guide grounded in the E3/E4 evidence.

**Stub C — Finance-focused Hawkes order-flow toolkit (thesis fails).** Scope: a single-substrate library doing crypto/equity order-flow clustering well, with the cross-substrate story reduced to a discussion section honestly reporting the E4 negative result. Core users: Strider's quant applications exclusively. Defining constraint: depth over breadth — microstructure-aware preprocessing and finance-grade GOF replace adapter generality. Capabilities: simulator, estimator, GOF, order-flow adapter(s), microstructure viz, and the negative-result writeup (itself portfolio material).

## Experiment Log

- **2026-07-04** — Roadmap created from the sessions 41–42 handoff (vault note `20260704-hawkes-toolkit-roadmap-handoff.md`). Scoping decisions imported as invariants: Python library-quality core, public data only, quant-application value target, theory-grounding requirement, Dynamica as future hook only. Decision frontier initialized: N1 active, E1 ready to run. No experiments run yet.
- **2026-07-04** — E2 run (`experiments/e2-synthetic-recovery/`). Derived conditional-intensity Markov recursion, log-likelihood (with compensator boundary term), Ogata thinning, time-rescaling transform (`derivations.md`). Implemented simulator + multi-start MLE + KS-based GOF (`hawkes_core.py`), tested recovery across 3 ground-truth parameter sets (n=0.15/0.50/0.90) × 3 seeds each. Result: 8/9 runs pass all three parameters under 10% relative error; 9/9 pass KS p>0.05 including all near-critical seeds. One marginal miss (low_n seed 2, α=10.06%) diagnosed as finite-sample noise, not a bug (see RESULTS.md). **N2 → resolved: pass.**

- **2026-07-04** — E1 substrate recon run (scripts + RESULTS.md in `experiments/e1-substrate-recon/`). Scoring table (criteria a/b/c, ≤30min/substrate):

  | Substrate | (a) ≥1e4 events | (b) resolution < mean IEI | (c) stationary segment |
  |---|---|---|---|
  | Binance aggTrades (BTCUSDT, 1 day) | PASS (554,441 events) | PASS (1ms res vs 155.8ms mean IEI) | PASS (hour-long sub-windows near-stationary) |
  | LOBSTER (AAPL message file, 1 day, 10 levels) | PASS (400,391 events) | PASS (1ns res vs 58.4ms mean IEI) | PASS (mid-morning window flat; open/close auctions non-stationary) |
  | Allen Institute (Cell Types single-neuron patch-clamp) | FAIL (779 spikes total for one cell — pooling cells isn't one coherent process) | PASS but moot | FAIL (trial-based evoked sweeps, not spontaneous) |
  | SuperMAG (1-min magnetometer, HBK/OTT) | FAIL (backend `shell_exec` crash on every call with the userid as given; likely a one-letter userid typo in the task brief — flagged for the user, not acted on) | N/A | N/A |

  Binance and LOBSTER both pass all three criteria; tie broken toward **Binance** (more event volume for the same pull, 24/7 continuous trading avoids equity-auction regime breaks, zero-friction access) with **LOBSTER as the designated runner-up substrate for E4** (transfer). N1 resolved → crypto ticks. Full detail, plots, and raw samples in `experiments/e1-substrate-recon/`.

- **2026-07-04** — E3 run (`experiments/e3-real-data-gof/`). Exp-kernel MLE (unchanged `hawkes_core.py` from E2) fit to Binance BTCUSDT aggTrades, 01:00-02:00 UTC window, 11,873 unique-ms events (simultaneous same-ms prints collapsed to one event — a timestamp-resolution artifact, not marks). Fit: μ=2.204, α=42.660, β=128.547, branching ratio n=0.332 (valid). **GOF fails decisively**: KS D=0.0583, p≈0.0000 (critical D at this n ≈0.0125, so D is ~4.7x the rejection threshold). Reproduced on an independent window (14:00-15:00 UTC, n=15,024 events, n_branch=0.222, D=0.0352, p≈0.0000) — ruling out a window-choice fluke. **QQ plot inspected** (not just generated): bulk of residuals (~98%) track Exp(1) almost exactly; deviation is a smooth, progressively-widening excess concentrated in the top ~2% tail. **N3 → resolved: parametric-insufficient. N3-alt activated.**
- **2026-07-04** — N3-alt attempt 1 (sum-of-2-exponentials) and bar-reconsideration (both Strider-directed). 2-exp kernel: same tail-deviation shape, D=0.0466 (barely moved from 1-exp's 0.0583) — disfavors kernel-shape as the sole culprit without confirming the alternative. Multi-scale subsampled-KS test of the GOF bar itself: pass fraction declines monotonically from 0.30 (n=300) to 0.00 (n≥2000), the signature of a model misspecified at every scale (a correctly-specified model would hold ≈0.95 pass fraction at any n) — **decisively rules out "the bar is just too strict for large n."** Full detail: `experiments/e3-alt-two-exp-kernel/RESULTS.md` and `gof_bar_reconsidered_RESULTS.md`. **N3/N3-alt final: parametric estimation is robustly insufficient on Binance — not a bug, not a large-n artifact, not rescued by kernel enrichment or bar reconsideration.** Off-map relative to all three manifesto stubs (each assumes a passing N3). Handed off for Strider's decision: try LOBSTER / commit to full nonparametric E5 / accept as the project's negative result and rescope.

- **2026-07-07** — **N3-alt decision made** (Strider, Fable session, decision structured via option review + AskUserQuestion): run **E6** (LOBSTER exp-kernel generality spike) + **E7** (power-law long-memory kernel on Binance via sum-of-M-exponentials) before any commitment to E5 or a negative rescope. Basis: the E3 QQ signature (clean bulk, smooth top-~2% tail excess) and the multi-scale misfit point at long memory rather than short-scale kernel shape; exp-Hawkes failing GOF on tick data is documented microstructure folklore while power-law kernels are the literature-standard fix (Hardiman & Bouchaud; Bacry–Mastromatteo–Muzy 2015) — so the negative result alone under-delivers as portfolio material and the standard fix is cheap with existing machinery. Outcome mapping pre-registered in the N3-alt node before either experiment runs (E7 pass → Stub B; E7 fail + E6 pass → LOBSTER promoted primary; both fail → E5 vs rescope returns to Strider, no third parametric attempt). Cards E6/E7 written and wired into the tree, card list, and frontier. No experiments run this session. Separately decided the same session: Dynamica reserves a *hook* for a future Hawkes cross-substrate triple (order flow / spike trains / cascades) — per this roadmap's invariant, that remains a future hook only, never a phase or dependency here.

## Status / current frontier

- **N1:** resolved → Binance (primary), LOBSTER (runner-up for E4).
- **N2:** resolved → pass. Derivations trusted, `hawkes_core.py` is the frozen fitting engine.
- **N3:** resolved → parametric-insufficient, robust to kernel enrichment (2-exp) and to GOF-bar reconsideration (multi-scale subsampled KS). Real, decisive negative result, not an execution gap.
- **N3-alt:** decision made (2026-07-07) → run **E6 + E7**, outcome mapping pre-registered in the node. Neither experiment has run yet — **E6 and E7 are the frontier**; either order works, E7 is the higher-information one.
- **N4:** blocked pending E7 (transfer needs a passing engine configuration).
- **Manifesto:** still blocked on exit condition 2 (no real substrate has passed GOF yet) and condition 3 (N4 has no outcome). If E7 passes, the expected stub is **Stub B** (kernel-pluggable) per N3-alt's outcome mapping.
