"""
Reconsidering the N3 GOF bar (Strider-approved, 2026-07-04): KS test power
scales with n, and real substrates hand us n~1e4+ while published Hawkes/
microstructure fits typically report KS at n~1e3-3e3. Rather than pick an
arbitrary fixed-D threshold, subsample the rescaled residuals down to a
reference n and ask whether the fit would be judged adequate at a scale
comparable to the literature. This changes how GOF is *evaluated*, not the
fitted model or the underlying time-rescaling math.
"""
import json
import sys
import zipfile
import numpy as np
import pandas as pd

sys.path.insert(0, "../e2-synthetic-recovery")
from hawkes_core import time_rescale as time_rescale_1exp, ks_test_exp1
from hawkes_core_2exp import time_rescale_2exp

REFERENCE_N = 2000
N_BOOTSTRAP = 2000

zf = zipfile.ZipFile("../e1-substrate-recon/binance_BTCUSDT_aggTrades_2024-06-01.zip")
cols = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
        "transact_time", "is_buyer_maker", "is_best_match"]
with zf.open(zf.namelist()[0]) as f:
    df = pd.read_csv(f, header=None, names=cols)
t_sec_all = np.sort(df["transact_time"].to_numpy() / 1e3)
day_start = t_sec_all.min()
t_rel_hr = (t_sec_all - day_start) / 3600.0
mask = (t_rel_hr >= 1.0) & (t_rel_hr < 2.0)
window_times = t_sec_all[mask]
event_times = np.unique(window_times) - window_times.min()
t_max = event_times.max()


def subsampled_ks(u, reference_n, n_bootstrap, rng):
    """Random contiguous-index subsamples of size reference_n from the
    residual sequence (contiguous, not random scatter, to preserve any
    local structure), KS-tested against Exp(1) each time."""
    n = len(u)
    ps = []
    for _ in range(n_bootstrap):
        start = rng.integers(0, n - reference_n)
        sub = u[start:start + reference_n]
        _, p = ks_test_exp1(sub)
        ps.append(p)
    return np.array(ps)


rng = np.random.default_rng(0)
results = {}

with open("../e3-real-data-gof/binance_fit_results.json") as f:
    fit1 = json.load(f)["fit"]
u1 = time_rescale_1exp(event_times, t_max, fit1["mu"], fit1["alpha"], fit1["beta"])
ps1 = subsampled_ks(u1, REFERENCE_N, N_BOOTSTRAP, rng)
results["1exp"] = {
    "full_n": len(u1), "full_ks_p": float(ks_test_exp1(u1)[1]),
    "reference_n": REFERENCE_N,
    "subsampled_median_p": float(np.median(ps1)),
    "subsampled_pass_fraction": float(np.mean(ps1 > 0.05)),
}

with open("binance_2exp_fit_results.json") as f:
    fit2 = json.load(f)["fit"]
u2 = time_rescale_2exp(event_times, t_max, fit2["mu"], fit2["alpha1"], fit2["beta1"],
                        fit2["alpha2"], fit2["beta2"])
ps2 = subsampled_ks(u2, REFERENCE_N, N_BOOTSTRAP, rng)
results["2exp"] = {
    "full_n": len(u2), "full_ks_p": float(ks_test_exp1(u2)[1]),
    "reference_n": REFERENCE_N,
    "subsampled_median_p": float(np.median(ps2)),
    "subsampled_pass_fraction": float(np.mean(ps2 > 0.05)),
}

for name, r in results.items():
    print(f"{name}: full_n={r['full_n']} full_p={r['full_ks_p']:.2e} | "
          f"at n={REFERENCE_N}: median_p={r['subsampled_median_p']:.4f}, "
          f"pass_fraction={r['subsampled_pass_fraction']:.3f}")

with open("gof_bar_reconsidered_results.json", "w") as f:
    json.dump(results, f, indent=2)
