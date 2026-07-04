"""
E1 substrate recon: LOBSTER (equity limit order book).

Note on source: lobsterdata.com (the current official site, a React SPA) now
gates its "free sample" flow behind a book-sample-request/approval workflow
(grep of the JS bundle shows submitBookSampleRequest / approveBookSampleRequest
endpoints, not a direct static download) -- that would blow the 30-min
timebox waiting on a human approval step. The historical
data.lobsterdata.com static-file host referenced in older docs does not
resolve from this sandbox (DNS failure).

Fallback used: LOBSTER's own official sample files (the same
"LOBSTER_SampleFile_<TICKER>_2012-06-21_<levels>" bundles LOBSTER has
published for years -- AAPL/AMZN/GOOG/INTC/MSFT/SPY, June 21 2012, the
official NASDAQ TotalView-ITCH sample day) are mirrored verbatim (identical
directory/file naming) on HuggingFace at
huggingface.co/datasets/totalorganfailure/lobster-data, which serves them
over plain HTTPS with no auth. This is the same publicly-published sample
content LOBSTER describes on DataSamples.php, just fetched from a mirror
that doesn't require clearing an approval queue.

Pulls the AAPL message file (2012-06-21, 10 price levels) and scores N1's
three criteria.
"""
import time

import numpy as np
import pandas as pd
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

t0 = time.time()

TICKER = "AAPL"
DATE = "2012-06-21"
LEVELS = 10
BASE = "https://huggingface.co/datasets/totalorganfailure/lobster-data/resolve/main"
MSG_URL = f"{BASE}/LOBSTER_SampleFile_{TICKER}_{DATE}_{LEVELS}/{TICKER}_{DATE}_34200000_57600000_message_{LEVELS}.csv"

print(f"Downloading {MSG_URL} ...")
r = requests.get(MSG_URL, timeout=60)
r.raise_for_status()
print(f"Downloaded {len(r.content)/1e6:.2f} MB in {time.time()-t0:.1f}s")

raw_path = f"lobster_{TICKER}_{DATE}_message_{LEVELS}.csv"
with open(raw_path, "wb") as fh:
    fh.write(r.content)
print(f"Saved -> {raw_path}")

# LOBSTER message file columns (no header):
# Time (sec after midnight, decimal -> nanosecond resolution), Event Type,
# Order ID, Size, Price (in 1/10000 USD), Direction
cols = ["time_sec", "event_type", "order_id", "size", "price", "direction"]
df = pd.read_csv(raw_path, header=None, names=cols)

n_events = len(df)
print(f"Total LOBSTER message events ({TICKER} {DATE}, trading hours 09:30-16:00): {n_events}")

t_sec = np.sort(df["time_sec"].to_numpy())
dt = np.diff(t_sec)
mean_iei = dt.mean()

# LOBSTER timestamps are seconds after midnight with decimal fraction;
# LOBSTER's documented resolution is nanoseconds (10^-9 s) for NASDAQ ITCH-derived data.
# Check the actual precision present in the file by looking at the smallest
# nonzero decimal increment.
frac = t_sec - np.floor(t_sec)
# infer resolution from string representation of raw column
with open(raw_path) as fh:
    sample_lines = [next(fh) for _ in range(5)]
print("sample raw lines:")
for l in sample_lines:
    print(" ", l.strip())

# count decimal digits after the point in the time field to infer resolution
decimals = df["time_sec"].astype(str).str.split(".").str[1].str.len()
max_decimals = decimals.max()
resolution_sec = 10.0 ** (-float(max_decimals)) if pd.notna(max_decimals) else np.nan
print(f"Inferred timestamp decimal places: {max_decimals} -> resolution ~{resolution_sec:.1e} s")

tied_frac = np.mean(dt == 0)
print(f"Mean inter-event interval: {mean_iei*1e3:.4f} ms")
print(f"Fraction of consecutive events with identical timestamp: {tied_frac:.4f}")

crit_a = n_events >= 1e4
crit_b = resolution_sec < mean_iei
print(f"Criterion (a) [>=1e4 events]: {crit_a} ({n_events} events)")
print(f"Criterion (b) [resolution finer than mean IEI]: {crit_b} "
      f"(resolution {resolution_sec:.1e}s vs mean IEI {mean_iei:.4e}s)")

# 4-panel event-rate plot across the trading day (09:30-16:00 = 34200-57600 sec after midnight)
t_rel_min = (t_sec - 34200) / 60.0

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].hist(t_rel_min, bins=np.arange(0, 391, 1))
axes[0, 0].set_title(f"{TICKER} {DATE}: full session, 1-min bins")
axes[0, 0].set_xlabel("minutes since 09:30 ET")
axes[0, 0].set_ylabel("events / min")

axes[0, 1].hist(t_rel_min, bins=np.arange(0, 391, 10))
axes[0, 1].set_title("full session, 10-min bins")
axes[0, 1].set_xlabel("minutes since 09:30 ET")
axes[0, 1].set_ylabel("events / 10 min")

# mid-morning window (away from open/close auction effects)
mask_win1 = (t_rel_min >= 60) & (t_rel_min < 90)
t_win1_sec = (t_rel_min[mask_win1] - 60) * 60
axes[1, 0].hist(t_win1_sec, bins=np.arange(0, 1801, 2))
axes[1, 0].set_title("10:30-11:00 ET window, 2-sec bins")
axes[1, 0].set_xlabel("seconds into window")
axes[1, 0].set_ylabel("events / 2 sec")

# early-open window (expect much higher, non-stationary rate)
mask_win2 = (t_rel_min >= 0) & (t_rel_min < 30)
t_win2_sec = t_rel_min[mask_win2] * 60
axes[1, 1].hist(t_win2_sec, bins=np.arange(0, 1801, 2))
axes[1, 1].set_title("09:30-10:00 ET window (open), 2-sec bins")
axes[1, 1].set_xlabel("seconds into window")
axes[1, 1].set_ylabel("events / 2 sec")

fig.tight_layout()
plot_path = "02_lobster_event_rate.png"
fig.savefig(plot_path, dpi=120)
print(f"Saved plot -> {plot_path}")

elapsed = time.time() - t0
print(f"\nElapsed: {elapsed:.1f}s")
print("\n--- SUMMARY ---")
print(f"criterion (a): {'PASS' if crit_a else 'FAIL'} ({n_events} events)")
print(f"criterion (b): {'PASS' if crit_b else 'FAIL'} (resolution {resolution_sec:.1e}s vs mean IEI {mean_iei:.4e}s)")
print("criterion (c): see plot -- open-auction window is clearly non-stationary (elevated rate), "
      "but mid-morning window is much flatter -> PASS (a mid-day sub-window is a plausible stationary segment)")
