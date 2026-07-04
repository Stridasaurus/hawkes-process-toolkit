"""
Throwaway E2 spike: exp-kernel Hawkes simulator + MLE + time-rescaling GOF.

Parameterization (fixed by ROADMAP.md glossary): phi(t) = alpha * exp(-beta*t),
branching ratio n = alpha/beta, stationarity requires alpha < beta.

Not library code -- this exists to resolve N2 (does the derivation recover known
parameters on synthetic data). See derivations.md for the math each function here
implements directly.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import kstest


def simulate_hawkes(mu, alpha, beta, t_max, rng=None):
    """Ogata's modified thinning algorithm (exact). Returns sorted event times."""
    if rng is None:
        rng = np.random.default_rng()
    t = 0.0
    R = 0.0
    events = []
    while True:
        lam_bar = mu + alpha * R
        u = rng.exponential(1.0 / lam_bar)
        t_candidate = t + u
        if t_candidate > t_max:
            break
        decay = np.exp(-beta * (t_candidate - t))
        lam_candidate = mu + alpha * R * decay
        d = rng.uniform()
        if d <= lam_candidate / lam_bar:
            R = R * decay + 1.0
            events.append(t_candidate)
        else:
            R = R * decay
        t = t_candidate
    return np.array(events)


def _R_sequence_for_beta(event_times, beta):
    n = len(event_times)
    R = np.zeros(n)
    for i in range(1, n):
        dt = event_times[i] - event_times[i - 1]
        R[i] = np.exp(-beta * dt) * (1.0 + R[i - 1])
    return R


def neg_log_lik(params, event_times, t_max):
    mu, alpha, beta = params
    if mu <= 0 or alpha <= 0 or beta <= 0:
        return np.inf
    R = _R_sequence_for_beta(event_times, beta)
    lam_at_events = mu + alpha * R
    if np.any(lam_at_events <= 0):
        return np.inf
    term1 = np.sum(np.log(lam_at_events))
    term2 = mu * t_max
    term3 = (alpha / beta) * np.sum(1.0 - np.exp(-beta * (t_max - event_times)))
    return -(term1 - term2 - term3)


def fit_mle(event_times, t_max, x0=None, n_restarts=5, rng=None):
    """Multi-start L-BFGS-B on neg_log_lik. Returns best-fit (mu, alpha, beta)."""
    if rng is None:
        rng = np.random.default_rng()
    bounds = [(1e-6, None), (1e-6, None), (1e-6, None)]
    starts = []
    if x0 is not None:
        starts.append(x0)
    n = len(event_times)
    mean_rate = n / t_max
    for _ in range(n_restarts):
        starts.append([
            mean_rate * rng.uniform(0.2, 0.8),
            rng.uniform(0.1, 2.0),
            rng.uniform(0.5, 3.0),
        ])
    best = None
    for s in starts:
        res = minimize(
            neg_log_lik, s, args=(event_times, t_max),
            method="L-BFGS-B", bounds=bounds,
        )
        if res.success and (best is None or res.fun < best.fun):
            best = res
    if best is None:
        raise RuntimeError("MLE failed to converge from all restarts")
    return best.x, best.fun


def time_rescale(event_times, t_max, mu, alpha, beta):
    """tau_i = mu*t_i + (alpha/beta)*sum_{j<=i}(1-exp(-beta*(t_i-t_j))), via R-recursion.
    Returns inter-rescaled-time gaps u_i = tau_i - tau_{i-1} (should be ~Exp(1))."""
    n = len(event_times)
    R = _R_sequence_for_beta(event_times, beta)
    # tau_i itself also needs sum_{j<=i}(1 - exp(-beta*(t_i-t_j))) = R_i_inclusive - like term.
    # Build the inclusive compensator directly via cumulative recursion S_i:
    # S_i = sum_{j<=i} (1 - exp(-beta*(t_i - t_j)))
    #     = i - [sum_{j<=i} exp(-beta*(t_i-t_j))]
    #     = i - (R_i + 1)   since R_i = sum_{j<i} exp(-beta*(t_i-t_j)), plus the j=i term = 1
    idx = np.arange(1, n + 1)
    S = idx - (R + 1.0)
    tau = mu * event_times + (alpha / beta) * S
    tau_full = np.concatenate(([0.0], tau))
    u = np.diff(tau_full)
    return u


def ks_test_exp1(u):
    """One-sample KS test of u against Exp(1) (rate=1). Returns (D, p)."""
    return kstest(u, "expon")
