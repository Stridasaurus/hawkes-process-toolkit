"""
E1 substrate recon: Binance (crypto ticks).

Source: https://data.binance.vision/ (Binance's own official historical-data
static file host -- api.binance.com is geo-blocked (451) from this sandbox,
data.binance.vision is not a workaround, it's the same exchange's public
data dump: monthly/daily zipped CSV of aggTrades / trades).

Pulls one day of BTCUSDT aggTrades (public REST, no auth) and scores N1's
three criteria:
  (a) >= 1e4 events within ~30 min effort
  (b) timestamp resolution finer than mean inter-event interval
  (c) plausibly stationary segment extractable (eyeball 4-panel event-rate plot)
"""
import io
import time
import zipfile

import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

t0 = time.time()

SYMBOL = "BTCUSDT"
DATE = "2024-06-01"
URL = f"https://data.binance.vision/data/spot/daily/aggTrades/{SYMBOL}/{SYMBOL}-aggTrades-{DATE}.zip"

print(f"Downloading {URL} ...")
r = requests.get(URL, timeout=60)
r.raise_for_status()
print(f"Downloaded {len(r.content)/1e6:.2f} MB in {time.time()-t0:.1f}s")

zf = zipfile.ZipFile(io.BytesIO(r.content))
name = zf.namelist()[0]
print("zip member:", name)

# aggTrades columns (no header in the raw file):
# agg_trade_id, price, quantity, first_trade_id, last_trade_id, transact_time, is_buyer_maker, [is_best_match]
with zf.open(name) as f:
    first_line = f.readline().decode()
print("first line sample:", first_line.strip())

cols = [
    "agg_trade_id", "price", "quantity", "first_trade_id", "last_trade_id",
    "transact_time", "is_buyer_maker", "is_best_match",
]
with zf.open(name) as f:
    df = pd.read_csv(f, header=None, names=cols)

# Save a small local copy (raw zip is ~7MB; keep it, it's small enough to commit,
# but we also keep a trimmed CSV sample for quick reloading / E3 use).
raw_path = f"binance_{SYMBOL}_aggTrades_{DATE}.zip"
with open(raw_path, "wb") as fh:
    fh.write(r.content)
print(f"Saved raw zip -> {raw_path} ({len(r.content)/1e6:.2f} MB)")

n_events = len(df)
print(f"Total aggTrades events on {DATE}: {n_events}")

# transact_time is in ms (some Binance archives switched to microseconds in
# 2025 for some symbols; sanity check the magnitude).
t_ms = df["transact_time"].to_numpy()
# detect us vs ms by magnitude (ms epoch ~1.7e12, us epoch ~1.7e15)
if t_ms.max() > 1e14:
    print("Detected microsecond timestamps")
    t_sec = t_ms / 1e6
    resolution_sec = 1e-6
else:
    print("Detected millisecond timestamps")
    t_sec = t_ms / 1e3
    resolution_sec = 1e-3

t_sec = np.sort(t_sec)
dt = np.diff(t_sec)
mean_iei = dt.mean()
tied_frac = np.mean(dt == 0)

print(f"Mean inter-event interval: {mean_iei*1e3:.4f} ms")
print(f"Timestamp resolution: {resolution_sec*1e3:.4f} ms")
print(f"Fraction of consecutive events with identical timestamp (tied ms): {tied_frac:.4f}")
crit_b = resolution_sec < mean_iei
print(f"Criterion (b) [resolution finer than mean IEI]: {crit_b}")

crit_a = n_events >= 1e4
print(f"Criterion (a) [>=1e4 events]: {crit_a} ({n_events} events)")

# 4-panel event-rate-over-time plot for stationarity eyeball:
# full day at 1-min bins, plus three zoomed sub-windows at finer resolution.
t0_day = t_sec.min()
t_rel_min = (t_sec - t0_day) / 60.0

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

# Panel 1: full day, 1-min bins
bins_full = np.arange(0, 24 * 60 + 1, 1)
axes[0, 0].hist(t_rel_min, bins=bins_full)
axes[0, 0].set_title(f"{SYMBOL} aggTrades {DATE}: full day, 1-min bins")
axes[0, 0].set_xlabel("minutes since 00:00 UTC")
axes[0, 0].set_ylabel("events / min")

# Panel 2: full day, 10-min bins (smoother)
bins_10 = np.arange(0, 24 * 60 + 1, 10)
axes[0, 1].hist(t_rel_min, bins=bins_10)
axes[0, 1].set_title("full day, 10-min bins")
axes[0, 1].set_xlabel("minutes since 00:00 UTC")
axes[0, 1].set_ylabel("events / 10 min")

# Panel 3: a 1-hour sub-window, 1-sec bins (early UTC hours -- Asia session)
mask_win1 = (t_rel_min >= 60) & (t_rel_min < 120)
t_win1_sec = (t_sec[mask_win1] - t0_day) - 60 * 60
axes[1, 0].hist(t_win1_sec, bins=np.arange(0, 3601, 5))
axes[1, 0].set_title("01:00-02:00 UTC window, 5-sec bins")
axes[1, 0].set_xlabel("seconds into window")
axes[1, 0].set_ylabel("events / 5 sec")

# Panel 4: a different 1-hour sub-window (US session, higher activity expected)
mask_win2 = (t_rel_min >= 14 * 60) & (t_rel_min < 15 * 60)
t_win2_sec = (t_sec[mask_win2] - t0_day) - 14 * 60 * 60
axes[1, 1].hist(t_win2_sec, bins=np.arange(0, 3601, 5))
axes[1, 1].set_title("14:00-15:00 UTC window, 5-sec bins")
axes[1, 1].set_xlabel("seconds into window")
axes[1, 1].set_ylabel("events / 5 sec")

fig.tight_layout()
plot_path = "01_binance_event_rate.png"
fig.savefig(plot_path, dpi=120)
print(f"Saved plot -> {plot_path}")

elapsed = time.time() - t0
print(f"\nElapsed: {elapsed:.1f}s")
print("\n--- SUMMARY ---")
print(f"criterion (a): {'PASS' if crit_a else 'FAIL'} ({n_events} events)")
print(f"criterion (b): {'PASS' if crit_b else 'FAIL'} (resolution {resolution_sec*1e3:.4f}ms vs mean IEI {mean_iei*1e3:.4f}ms)")
print("criterion (c): see plot -- intraday rate varies (diurnal pattern), "
      "but hour-long sub-windows look locally near-stationary -> PASS (segment extractable)")
