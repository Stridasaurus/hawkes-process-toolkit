"""
E3: real-data fit + GOF on the N1 substrate (Binance BTCUSDT aggTrades).

Reuses hawkes_core.py from E2 UNCHANGED (fit_mle, time_rescale, ks_test_exp1) --
per ROADMAP.md, the fitting engine must not vary between synthetic and real
fits; only the adapter (this script's data-loading section) is substrate-specific.

Univariate, unmarked: trade price/quantity/side are dropped, only arrival
times are used. Window: 01:00-02:00 UTC on 2024-06-01 (E1's flagged
near-stationary segment). Simultaneous same-millisecond aggTrades prints are
collapsed to one event time (39% of consecutive Binance events tie at the
same ms per E1 -- a timestamp-resolution artifact of the exchange's aggTrades
export, not real coincident arrivals; standard practice for tick-level Hawkes
fits, not a marks/multivariate extension).
"""
import sys
import zipfile
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, "../e2-synthetic-recovery")
from hawkes_core import fit_mle, time_rescale, ks_test_exp1

ZIP_PATH = "../e1-substrate-recon/binance_BTCUSDT_aggTrades_2024-06-01.zip"
COLS = ["agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
        "transact_time", "is_buyer_maker", "is_best_match"]
WINDOW_START_HR, WINDOW_END_HR = 1.0, 2.0

zf = zipfile.ZipFile(ZIP_PATH)
name = zf.namelist()[0]
with zf.open(name) as f:
    df = pd.read_csv(f, header=None, names=COLS)

t_ms = df["transact_time"].to_numpy()
t_sec_all = np.sort(t_ms / 1e3)
day_start = t_sec_all.min()
t_rel_hr = (t_sec_all - day_start) / 3600.0

mask = (t_rel_hr >= WINDOW_START_HR) & (t_rel_hr < WINDOW_END_HR)
window_times_sec = t_sec_all[mask]
window_start_sec = window_times_sec.min() if len(window_times_sec) else 0.0

# Collapse same-millisecond ties to one event (unique timestamps).
event_times = np.unique(window_times_sec) - window_times_sec.min()
n_events = len(event_times)
t_max = event_times.max()

print(f"Window {WINDOW_START_HR}-{WINDOW_END_HR}h UTC: "
      f"{mask.sum()} raw prints -> {n_events} unique-ms events over {t_max:.1f}s")

rng = np.random.default_rng(0)
fit, nll = fit_mle(event_times, t_max, n_restarts=8, rng=rng)
mu_hat, alpha_hat, beta_hat = fit
n_branch = alpha_hat / beta_hat

print(f"Fit: mu={mu_hat:.5f}, alpha={alpha_hat:.5f}, beta={beta_hat:.5f}")
print(f"Branching ratio n = alpha/beta = {n_branch:.4f}  (need in (0,1) for stationarity)")

u = time_rescale(event_times, t_max, mu_hat, alpha_hat, beta_hat)
ks_stat, ks_p = ks_test_exp1(u)
print(f"KS test on time-rescaled residuals vs Exp(1): D={ks_stat:.4f}, p={ks_p:.4f}")
print(f"GOF pass (p > 0.05): {ks_p > 0.05}")
print(f"Branching ratio in (0,1): {0 < n_branch < 1}")

# QQ plot + residual histogram, same diagnostic as E2.
u_sorted = np.sort(u)
n = len(u_sorted)
theoretical = -np.log(1 - (np.arange(1, n + 1) - 0.5) / n)

fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
axes[0].plot(theoretical, u_sorted, ".", ms=2, alpha=0.5)
lims = [0, max(theoretical.max(), u_sorted.max())]
axes[0].plot(lims, lims, "r--", lw=1)
axes[0].set_xlabel("Exp(1) theoretical quantile")
axes[0].set_ylabel("Rescaled residual quantile")
axes[0].set_title("QQ plot: Binance 01:00-02:00 UTC residuals vs Exp(1)")

axes[1].hist(u, bins=50, density=True, alpha=0.6, label="rescaled residuals")
xs = np.linspace(0, u.max(), 200)
axes[1].plot(xs, np.exp(-xs), "r-", lw=2, label="Exp(1) pdf")
axes[1].set_title("Residual histogram vs Exp(1)")
axes[1].legend()
plt.tight_layout()
plt.savefig("binance_residual_qq.png", dpi=120)
print("saved binance_residual_qq.png")

import json
with open("binance_fit_results.json", "w") as f:
    json.dump({
        "window": f"{WINDOW_START_HR}-{WINDOW_END_HR}h UTC 2024-06-01",
        "n_events": int(n_events),
        "t_max_sec": float(t_max),
        "fit": {"mu": float(mu_hat), "alpha": float(alpha_hat), "beta": float(beta_hat)},
        "branching_ratio": float(n_branch),
        "ks_stat": float(ks_stat),
        "ks_p": float(ks_p),
        "gof_pass": bool(ks_p > 0.05),
        "branching_ratio_valid": bool(0 < n_branch < 1),
    }, f, indent=2)
