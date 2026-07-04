# E3 results — real-data fit + GOF on Binance (N1 substrate)

Code: `binance_fit.py` (reuses `hawkes_core.py` from E2 **unchanged** — only the
data-loading/adapter section is Binance-specific, per the roadmap's
adapter-only-variation invariant). Data: `experiments/e1-substrate-recon/binance_BTCUSDT_aggTrades_2024-06-01.zip`.

## Method

Univariate, unmarked event times (price/quantity/side dropped). Simultaneous
same-millisecond aggTrades prints collapsed to one event (39% of consecutive
Binance events tie at the same ms per E1 — a timestamp-resolution artifact of
the exchange's export format, not real simultaneity; standard tick-Hawkes
practice, not a marks/multivariate extension).

## Primary window: 01:00–02:00 UTC (E1's flagged near-stationary segment)

- 18,321 raw prints → **11,873 unique-ms events** over 3600s (right at the ~10⁴ target)
- Fit: μ=2.204, α=42.660, β=128.547
- **Branching ratio n = α/β = 0.332** — valid, in (0,1) ✅
- **KS test on time-rescaled residuals vs Exp(1): D=0.0583, p≈0.0000 — FAILS the p>0.05 bar** ❌

## Robustness check: 14:00–15:00 UTC (busier session)

Ran the identical procedure on a second, independent window to rule out a
window-choice fluke:

- 15,024 unique-ms events
- Fit: μ=3.249, α=35.364, β=159.630, **n=0.222** (valid)
- **KS D=0.0352, p≈0.0000 — fails identically**

Two independent windows, both valid branching ratios, both clean rejections.
Consistent, reproducible signal — not noise from one window's idiosyncrasies.

## Interpretation: why a "small" D is a decisive failure here

KS's critical D at α=0.05 scales as ≈1.36/√n. At n≈11,873 that's ≈0.0125 — so
the observed D=0.0583 (01-02 UTC) is **~4.7× the rejection threshold**, not a
borderline call. This is the well-known empirical result from the market-
microstructure Hawkes literature (Bacry, Muzy et al.): single-exponential
kernels are typically insufficient for real order-flow clustering, because
excitation genuinely decays slower than pure-exponential at longer lags
(power-law-like tails). The failure is a real kernel-shape misspecification,
not a bug — it reproduces cleanly across two independent windows/sessions and
the branching ratio (the part the exponential form gets approximately right)
lands in a sane range both times.

## N3 decision

Per ROADMAP.md's N3 decision rule, this is **parametric-insufficient**, not
**data-unsuitable** (data-unsuitable is reserved for cases where preprocessing
eats the timebox or no usable segment exists — neither happened; the fit
converged cleanly and reproducibly on two windows). This **activates N3-alt**
(the nonparametric branch), whose experiment card E5 was deliberately left
unwritten per the roadmap's lazy-elaboration rule until this exact moment.

**Stopping here to flag, not improvising E5** — writing a new experiment card
for nonparametric kernel estimation is a real scope/design decision (what
estimator family: kernel-basis EM, Wiener-Hopf/nonparametric MLE, etc.; how it
changes the manifesto stubs) that the roadmap's own design reserves for
explicit sign-off rather than silent continuation.
