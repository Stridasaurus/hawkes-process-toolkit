# Reconsidering the N3 GOF bar — decisive result

Code: `gof_bar_reconsidered.py`. Question (Strider's chosen path after N3/N3-alt
both failed at the pre-registered `KS p>0.05` bar): is that bar simply too
strict at the large n (~12k) real substrates hand us, given KS's power scales
with n and published Hawkes/microstructure papers typically fit on n~1e3-3e3?

## Method

Subsample the already-fitted models' time-rescaled residuals down to a
reference sample size (contiguous windows, preserving temporal structure),
re-run the KS test at that size, repeat 1000x per size, report the pass
fraction (fraction of subsamples with p>0.05).

## Result: the bar is not the problem

| Reference n | 1-exp median p | 1-exp pass fraction |
|---|---|---|
| 300 | 0.0064 | 0.299 |
| 500 | 0.0016 | 0.211 |
| 1000 | 0.0000 | 0.122 |
| 2000 | 0.0000 | 0.000 |
| 5000 | 0.0000 | 0.000 |

**Under a correctly-specified model, KS pass fraction should be ≈0.95 at any
n** — that's what a p>0.05 threshold means by construction. Instead, pass
fraction *declines monotonically* from 0.30 at n=300 to 0.00 at n≥2000. This
is not the signature of "an adequate model rejected only because n is huge" —
that story would predict roughly constant, near-0.95 pass rates at small n
and a decline only once n gets large. What's actually observed is a model
that's misspecified at every scale tested, with the small-n pass fraction
elevated only because a test at n=300 lacks the power to reliably detect the
mismatch, not because the fit is good there.

**Reconsidering the bar answered the question decisively — the answer is
no.** The pre-registered `p>0.05` bar was not unfair; both the 1-exponential
and 2-exponential fits genuinely do not describe this Binance order-flow
window's arrival process, even at sample sizes matching typical published
Hawkes/microstructure studies.

## One documented limitation, not chased further

Simultaneous same-millisecond trades were deduplicated (39% of consecutive
Binance events, see E3). Dedup only removes near-zero rescaled gaps (the
short end); the observed GOF failure is concentrated entirely in the long
tail (rescaled gaps larger than the model predicts — arrivals the model
expects that don't come). A short-end preprocessing choice cannot produce a
long-tail excess, so dedup is not a plausible driver of this result — but
jittering instead of deduplicating was not tried, and is recorded here as an
open limitation rather than investigated further (see "no further diagnostics"
below).

## Where this leaves N3 — and why no further diagnostics were run

Three independent tests (1-exp fit, 2-exp fit, bar-reconsideration via
multi-scale subsampling) all converge on the same conclusion: this is a real,
robust parametric-model failure on Binance order flow, not a bug, not a
large-n statistical artifact, and not decisively resolved by kernel
enrichment. *Why* it fails (kernel-shape misspecification vs. baseline
non-stationarity vs. something else) is a genuine open research question
that doesn't have a cheap clean test (an attempted count-homogeneity check
was tried and discarded as invalid — see the sibling `RESULTS.md`). Chasing
the mechanism further is not required to resolve N3 and was stopped here as
scope creep beyond the roadmap's own decision rule, which only asks whether
GOF passes, not why it does or doesn't.

## N3 final status

**Parametric estimation (both 1-exp and 2-exp) is insufficient on the first
substrate (Binance), robustly, and this does not resolve by reconsidering
the GOF bar.** This outcome sits outside all three manifesto stubs' assumed
starting point (each assumes the toolkit gets *past* N3 with a passing real-
data fit) — the tree cannot self-resolve further without a scope decision:
try the runner-up substrate (LOBSTER), commit to full nonparametric
estimation (E5), or accept this as the project's negative result and rescope
the manifesto around it (deeper than Stub C anticipated, since Stub C still
assumed a passing finance-only fit). This decision is handed off, not
resolved, per this project's explicit design (stop-and-flag rather than
improvise past a pre-registered branch).
