"""
E2 runnable check: simulate at known (mu, alpha, beta), fit via MLE, measure
relative error per parameter and KS p-value on the fit's own time-rescaled
residuals. Decision rule (ROADMAP.md N2): rel. error < 10% on each of
(mu, alpha, beta) at ~1e4 events, KS p > 0.05, across >= 3 parameter sets
including one near-critical (n close to 1).
"""
import json
import numpy as np

from hawkes_core import simulate_hawkes, fit_mle, time_rescale, ks_test_exp1

PARAM_SETS = {
    "low_n (n=0.15)":  dict(mu=0.5, alpha=0.3, beta=2.0),
    "mid_n (n=0.5)":   dict(mu=0.2, alpha=0.5, beta=1.0),
    "near_critical (n=0.9)": dict(mu=0.1, alpha=0.9, beta=1.0),
}

TARGET_EVENTS = 10_000
SEEDS = [0, 1, 2]


def target_t_max(mu, alpha, beta, target_n):
    n_branch = alpha / beta
    effective_rate = mu / (1.0 - n_branch)  # long-run average rate incl. offspring
    return target_n / effective_rate


def run_one(name, truth, seed):
    rng = np.random.default_rng(seed)
    t_max = target_t_max(truth["mu"], truth["alpha"], truth["beta"], TARGET_EVENTS)
    events = simulate_hawkes(truth["mu"], truth["alpha"], truth["beta"], t_max, rng=rng)
    n_events = len(events)

    x0 = [truth["mu"], truth["alpha"], truth["beta"]]
    fit, nll = fit_mle(events, t_max, x0=None, n_restarts=6, rng=rng)
    mu_hat, alpha_hat, beta_hat = fit

    rel_err = {
        "mu": abs(mu_hat - truth["mu"]) / truth["mu"],
        "alpha": abs(alpha_hat - truth["alpha"]) / truth["alpha"],
        "beta": abs(beta_hat - truth["beta"]) / truth["beta"],
    }

    u = time_rescale(events, t_max, mu_hat, alpha_hat, beta_hat)
    ks_stat, ks_p = ks_test_exp1(u)

    return {
        "param_set": name,
        "seed": seed,
        "n_events": n_events,
        "truth": truth,
        "fit": {"mu": mu_hat, "alpha": alpha_hat, "beta": beta_hat},
        "rel_err_pct": {k: round(v * 100, 2) for k, v in rel_err.items()},
        "all_under_10pct": all(v < 0.10 for v in rel_err.values()),
        "ks_stat": ks_stat,
        "ks_p": ks_p,
        "ks_pass": ks_p > 0.05,
    }


def main():
    results = []
    for name, truth in PARAM_SETS.items():
        for seed in SEEDS:
            r = run_one(name, truth, seed)
            results.append(r)
            print(f"{name} seed={seed}: n={r['n_events']} "
                  f"rel_err%={r['rel_err_pct']} "
                  f"pass10%={r['all_under_10pct']} "
                  f"KSp={r['ks_p']:.3f} pass={r['ks_pass']}")

    def _default(o):
        if isinstance(o, (np.bool_, np.integer)):
            return bool(o) if isinstance(o, np.bool_) else int(o)
        if isinstance(o, np.floating):
            return float(o)
        raise TypeError(f"not serializable: {type(o)}")

    with open("recovery_results.json", "w") as f:
        json.dump(results, f, indent=2, default=_default)

    overall_pass = all(r["all_under_10pct"] and r["ks_pass"] for r in results)
    print(f"\nOVERALL N2 DECISION RULE MET (all sets/seeds): {overall_pass}")


if __name__ == "__main__":
    main()
