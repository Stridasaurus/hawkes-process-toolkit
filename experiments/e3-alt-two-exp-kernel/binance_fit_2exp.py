"""
N3-alt attempt 1: sum-of-2-exponentials fit on the same Binance window E3
used, to test whether a richer-but-still-parametric kernel resolves the
GOF failure before committing to full nonparametric estimation.
"""
import zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from hawkes_core_2exp import fit_mle_2exp, time_rescale_2exp, ks_test_exp1

ZIP_PATH = "../e1-substrate-recon/binance_BTCUSDT_aggTrades_2024-06-01.zip"
COLS = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
        "transact_time", "is_buyer_maker", "is_best_match"]
WINDOW_START_HR, WINDOW_END_HR = 1.0, 2.0

zf = zipfile.ZipFile(ZIP_PATH)
with zf.open(zf.namelist()[0]) as f:
    df = pd.read_csv(f, header=None, names=COLS)

t_sec_all = np.sort(df["transact_time"].to_numpy() / 1e3)
day_start = t_sec_all.min()
t_rel_hr = (t_sec_all - day_start) / 3600.0
mask = (t_rel_hr >= WINDOW_START_HR) & (t_rel_hr < WINDOW_END_HR)
window_times = t_sec_all[mask]
event_times = np.unique(window_times) - window_times.min()
n_events = len(event_times)
t_max = event_times.max()
print(f"n_events={n_events}, t_max={t_max:.1f}s")

rng = np.random.default_rng(0)
fit, nll = fit_mle_2exp(event_times, t_max, n_restarts=15, rng=rng)
mu, a1, b1, a2, b2 = fit
n_branch = a1 / b1 + a2 / b2
print(f"Fit: mu={mu:.5f} alpha1={a1:.5f} beta1={b1:.5f} (fast, ~{1000/b1:.2f}ms) "
      f"alpha2={a2:.5f} beta2={b2:.5f} (slow, ~{1000/b2:.2f}ms)")
print(f"Branching ratio n = {n_branch:.4f}  (need in (0,1))")

u = time_rescale_2exp(event_times, t_max, mu, a1, b1, a2, b2)
ks_stat, ks_p = ks_test_exp1(u)
print(f"KS D={ks_stat:.4f} p={ks_p:.6f}")
print(f"GOF pass (p>0.05): {ks_p > 0.05}")
print(f"Branching ratio valid: {0 < n_branch < 1}")

u_sorted = np.sort(u)
n = len(u_sorted)
theoretical = -np.log(1 - (np.arange(1, n + 1) - 0.5) / n)
fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(theoretical, u_sorted, ".", ms=2, alpha=0.5)
lims = [0, max(theoretical.max(), u_sorted.max())]
axes[0].plot(lims, lims, "r--", lw=1)
axes[0].set_xlabel("Exp(1) theoretical quantile")
axes[0].set_ylabel("Rescaled residual quantile")
axes[0].set_title("2-exp kernel: Binance 01:00-02:00 UTC residuals vs Exp(1)")
axes[1].hist(u, bins=50, density=True, alpha=0.6, label="rescaled residuals")
xs = np.linspace(0, u.max(), 200)
axes[1].plot(xs, np.exp(-xs), "r-", lw=2, label="Exp(1) pdf")
axes[1].legend()
plt.tight_layout()
plt.savefig("binance_2exp_residual_qq.png", dpi=120)
print("saved binance_2exp_residual_qq.png")

import json
with open("binance_2exp_fit_results.json", "w") as f:
    json.dump({
        "n_events": int(n_events), "t_max_sec": float(t_max),
        "fit": {"mu": float(mu), "alpha1": float(a1), "beta1": float(b1),
                "alpha2": float(a2), "beta2": float(b2)},
        "branching_ratio": float(n_branch),
        "ks_stat": float(ks_stat), "ks_p": float(ks_p),
        "gof_pass": bool(ks_p > 0.05),
    }, f, indent=2)
