"""
N3-alt attempt 1 (Strider's sanctioned fast path): sum-of-2-exponentials kernel.

phi(t) = alpha1*exp(-beta1*t) + alpha2*exp(-beta2*t)

Still parametric and still Markovian (two independent R-state recursions,
one per component) -- NOT the nonparametric branch as originally scoped in
ROADMAP.md's N3-alt stub. This is a cheaper richer-kernel test run first,
per Strider's explicit choice, before committing to full nonparametric
estimation (E5). Mirrors hawkes_core.py's structure/API but is deliberately
a separate module, since hawkes_core.py is E2's validated, frozen single-
exponential engine and must not be silently changed underneath E3's result.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.stats import kstest


def simulate_hawkes_2exp(mu, alpha1, beta1, alpha2, beta2, t_max, rng=None):
    if rng is None:
        rng = np.random.default_rng()
    t = 0.0
    R1 = R2 = 0.0
    events = []
    while True:
        lam_bar = mu + alpha1 * R1 + alpha2 * R2
        u = rng.exponential(1.0 / lam_bar)
        t_candidate = t + u
        if t_candidate > t_max:
            break
        dt = t_candidate - t
        decay1 = np.exp(-beta1 * dt)
        decay2 = np.exp(-beta2 * dt)
        lam_candidate = mu + alpha1 * R1 * decay1 + alpha2 * R2 * decay2
        d = rng.uniform()
        if d <= lam_candidate / lam_bar:
            R1 = R1 * decay1 + 1.0
            R2 = R2 * decay2 + 1.0
            events.append(t_candidate)
        else:
            R1 = R1 * decay1
            R2 = R2 * decay2
        t = t_candidate
    return np.array(events)


def _R_sequence(event_times, beta):
    n = len(event_times)
    R = np.zeros(n)
    for i in range(1, n):
        dt = event_times[i] - event_times[i - 1]
        R[i] = np.exp(-beta * dt) * (1.0 + R[i - 1])
    return R


def neg_log_lik(params, event_times, t_max):
    mu, alpha1, beta1, alpha2, beta2 = params
    if min(mu, alpha1, beta1, alpha2, beta2) <= 0:
        return np.inf
    R1 = _R_sequence(event_times, beta1)
    R2 = _R_sequence(event_times, beta2)
    lam = mu + alpha1 * R1 + alpha2 * R2
    if np.any(lam <= 0):
        return np.inf
    term1 = np.sum(np.log(lam))
    term2 = mu * t_max
    term3 = (alpha1 / beta1) * np.sum(1.0 - np.exp(-beta1 * (t_max - event_times)))
    term4 = (alpha2 / beta2) * np.sum(1.0 - np.exp(-beta2 * (t_max - event_times)))
    return -(term1 - term2 - term3 - term4)


def fit_mle_2exp(event_times, t_max, n_restarts=10, rng=None):
    """Multi-start fit. Initial betas deliberately separated (fast/slow) to
    fight the label-swap/collapse-to-1-exp degeneracy; result is re-sorted
    so component 1 is always the faster (larger beta) one for reporting."""
    if rng is None:
        rng = np.random.default_rng()
    bounds = [(1e-6, None)] * 5
    n = len(event_times)
    mean_rate = n / t_max
    best = None
    for _ in range(n_restarts):
        s = [
            mean_rate * rng.uniform(0.2, 0.8),
            rng.uniform(0.1, 2.0), rng.uniform(20, 300),    # fast component
            rng.uniform(0.05, 1.0), rng.uniform(0.5, 15),   # slow component
        ]
        res = minimize(neg_log_lik, s, args=(event_times, t_max),
                        method="L-BFGS-B", bounds=bounds)
        if res.success and (best is None or res.fun < best.fun):
            best = res
    if best is None:
        raise RuntimeError("2-exp MLE failed to converge from all restarts")
    mu, a1, b1, a2, b2 = best.x
    if b1 < b2:  # ensure component 1 = fast (larger beta)
        a1, b1, a2, b2 = a2, b2, a1, b1
    return np.array([mu, a1, b1, a2, b2]), best.fun


def time_rescale_2exp(event_times, t_max, mu, alpha1, beta1, alpha2, beta2):
    n = len(event_times)
    R1 = _R_sequence(event_times, beta1)
    R2 = _R_sequence(event_times, beta2)
    idx = np.arange(1, n + 1)
    S1 = idx - (R1 + 1.0)
    S2 = idx - (R2 + 1.0)
    tau = mu * event_times + (alpha1 / beta1) * S1 + (alpha2 / beta2) * S2
    tau_full = np.concatenate(([0.0], tau))
    return np.diff(tau_full)


def ks_test_exp1(u):
    return kstest(u, "expon")
