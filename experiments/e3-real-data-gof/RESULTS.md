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

## Why a "small" D is a decisive failure — and what the QQ shape actually shows

KS's critical D at α=0.05 scales as ≈1.36/√n. At n≈11,873 that's ≈0.0125 — so
the observed D=0.0583 (01-02 UTC) is **~4.7× the rejection threshold**, a real
rejection, not a borderline call inflated by sample size alone.

**`binance_residual_qq.png` (read, not just generated) shows a specific
shape**: the bulk of residuals (~98% of the distribution, rescaled quantile
≲4) track the Exp(1) reference line almost exactly. The deviation is
concentrated in the upper tail — a smooth, progressively widening excess
starting around the top ~2% of residuals, not a handful of isolated outliers
and not a uniform bend across the whole distribution.

This shape is a weaker match to "single-exponential kernel is globally the
wrong functional form" (Bacry/Muzy-style power-law excitation) than to
**within-window non-stationarity**: E1 only eyeballed the 01:00-02:00 UTC
window as "locally near-stationary" from a 5-second-bin event-rate histogram
— that was never a statistical test. A brief regime shift inside the hour
(a quiet lull, a small volatility burst) would show up exactly as an
otherwise-good fit with a heavy tail of anomalously large or small
rescaled gaps, which is what's observed. The fitted β≈128-160 (a 6-8ms
excitation timescale, right at the 1ms/dedup grid) is also consistent with
the exponential kernel mainly capturing the fastest microstructure scale
and not necessarily "missing a slower kernel component" — that's suggestive,
not proof.

**Net: the data rules out "parametric is simply fine," but does not cleanly
discriminate between "the kernel shape is wrong" (motivating N3-alt as
scoped — nonparametric) vs. "the window isn't as stationary as assumed"
(motivating a preprocessing fix, or a cheaper parametric extension like
sum-of-two-exponentials, before reaching for nonparametric estimation).**
This ambiguity, not just the GOF failure itself, is why the decision is being
flagged rather than resolved unilaterally.

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
