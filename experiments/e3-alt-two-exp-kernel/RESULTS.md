# N3-alt attempt 1 — sum-of-2-exponentials kernel on Binance

Code: `hawkes_core_2exp.py` (new module, sum-of-2-exponentials Markov recursion
+ MLE + time-rescaling; kept separate from E2's frozen `hawkes_core.py`),
`binance_fit_2exp.py`. Sanity-checked on synthetic data first (self-consistent:
KS p=0.82 on its own recovery test, though the fast component's individual
parameters are loosely identified at low branching ratios — a known
multi-timescale identifiability issue, not a bug; μ and the slow component
both recovered cleanly).

## Result on the same Binance window E3 used (01:00-02:00 UTC, 11,873 events)

- Fit: μ=1.229, α₁=50.306 β₁=173.28 (fast, ~5.8ms timescale), α₂=0.359 β₂=1.065
  (slow, ~939ms timescale)
- Branching ratio n = 0.627 (valid, in (0,1))
- **KS D=0.0466, p≈0.0000 — still fails**, though D improved from the
  single-exponential's 0.0583

**The QQ plot (`binance_2exp_residual_qq.png`) shows the same shape as the
single-exponential fit**: bulk near-perfect up to ~quantile 5, then a smooth,
progressively-widening tail deviation in the top ~2%. Adding a second,
much-slower timescale did not change the qualitative failure signature.

## What this does and doesn't establish

- **Both engines (1-exp, 2-exp) pass their own synthetic self-tests** — the
  real-data failures are a genuine model/data mismatch, not an implementation
  bug in either.
- **Kernel enrichment didn't rescue the fit.** This disfavors "the kernel
  shape is simply too restrictive" as the *sole* explanation — a genuinely
  richer parametric family barely moved D. It does not, by itself, confirm
  the competing hypothesis (within-window non-stationarity) either.
- A same-session attempt to test window homogeneity directly via a
  chi-square test on raw event counts across sub-bins was **run and
  discarded as methodologically invalid**: a stationary Hawkes process is
  overdispersed relative to a uniform/Poisson baseline *by construction*
  (that's what self-excitation is), so a count-homogeneity test rejects for
  any genuinely self-exciting process regardless of whether the baseline
  rate drifts — it cannot discriminate the two hypotheses and is not
  included as evidence here.
- **No cheap, clean test separates "kernel too simple" from "baseline
  non-stationary" was found this session.** Chasing the mechanism further
  is scope creep beyond what N3-alt's decision rule requires.

## The sharper framing of what's actually blocking

D≈0.047-0.058 at n≈11,873-15,024 events. KS's critical D at this sample size
is ≈0.0125 — so both fits are practically close (bulk of the distribution
fits almost exactly) but rejected because KS has very high power at this n,
not because the fit is grossly wrong. **A/B/C's manifesto stubs all assume
the toolkit gets *past* N3 with a passing real-data fit — none of them
covers "parametric GOF fails at the pre-registered p>0.05 bar on the first
substrate, on two kernel families, at this sample size."** If the bar stands
exactly as pre-registered, the stub structure itself is blocked — which is
evidence the *gate*, not necessarily the science, may need revisiting. That
is a pre-registration change and is flagged back to Strider rather than
silently relaxed.
