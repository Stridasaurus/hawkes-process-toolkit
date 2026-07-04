"""
E1 substrate recon: Allen Institute (neural spike trains).

Path taken (and why):
1. api.brain-map.org is reachable and serves RMA-query JSON directly with
   `requests` -- no allensdk needed for metadata. `pip install allensdk`
   was attempted and FAILS outright in this env (python 3.13 / numpy 2.x:
   allensdk's build chain pulls an old setuptools/pkg_resources that breaks
   under 3.13 -- "AttributeError: module 'pkgutil' has no attribute
   'ImpImporter'"). Abandoned immediately per the task's own guidance
   (check requests first; don't force a heavy install).
2. The "pre-extracted spike times" hope (Visual Coding Neuropixels units)
   requires downloading a full session NWB via AllenSDK's EcephysProjectCache,
   which pulls the whole multi-GB session file (LFP + running wheel + video
   sync + all units) even if you only want spike_times. That is exactly the
   "multi-GB NWB" the task says to avoid -- not attempted.
3. Fallback: the Allen Cell Types Database (single-neuron patch-clamp,
   whole-cell current clamp) publishes a flattened, directly-queryable API
   view (`ApiCellTypesSpecimenDetail`) whose rows include `erwkf__id`, the
   well_known_file id for that cell's ephys NWB -- fetchable at
   /api/v2/well_known_file_download/<id> with plain `requests`, no auth.
   The one pulled here is ~91.5 MB (not heavy). But: Cell Types NWB stores
   RAW VOLTAGE SWEEPS, not spike times -- there is no shortcut around
   spike-detecting them ourselves.

Spike detection used here: per-sweep 0V threshold crossing (data is already
baseline-subtracted membrane potential in Volts) with a 2ms refractory
period, applied only to sweeps with suprathreshold current stimuli (Long
Square, Square - 2s Suprathreshold, Noise 1/2) -- subthreshold sweeps
contribute no spikes by construction and are skipped.

Result: this one cell's ENTIRE recording (65 sweeps, every stimulus type,
~a couple hours of wall-clock experiment time) yields on the order of a
few hundred to ~1000 spikes total (single-neuron firing rates are just not
high enough, and stimuli are short pulses, not sustained drive). This is
nowhere near 1e4 -- and pooling spikes across many *different* cells to
hit 1e4 would not be one coherent point process (unrelated neurons), so
that's not a real fix. Getting 1e4+ *real, single-stream* neural events
within the 30-min budget would require the Neuropixels session route,
which is blocked by kill criterion 2 above (multi-GB download).

Conclusion drafted BEFORE writing this file (kill-criterion discipline):
criterion (a) = FAIL for the Cell Types path; recon stops here and moves
on rather than rabbit-holing on a bigger download.
"""
import time
from collections import Counter

import h5py
import numpy as np
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

t0 = time.time()

# --- 1. find a specimen with ephys data via the flattened Cell Types view ---
url = "http://api.brain-map.org/api/v2/data/query.json"
params = {"criteria": "model::ApiCellTypesSpecimenDetail,rma::options[num_rows$eq1]"}
r = requests.get(url, params=params, timeout=30)
r.raise_for_status()
row = r.json()["msg"][0]
specimen_id = row["specimen__id"]
nwb_file_id = row["erwkf__id"]
print(f"Specimen {specimen_id}, ephys NWB well_known_file id {nwb_file_id}, "
      f"avg_firing_rate={row.get('ef__avg_firing_rate')} Hz, avg_isi={row.get('ef__avg_isi')} ms")

# --- 2. download the NWB (patch-clamp raw sweeps; ~90 MB, not multi-GB) ---
nwb_path = f"allen_specimen_{specimen_id}_ephys.nwb"
dl_url = f"http://api.brain-map.org/api/v2/well_known_file_download/{nwb_file_id}"
resp = requests.get(dl_url, timeout=120, stream=True)
resp.raise_for_status()
with open(nwb_path, "wb") as fh:
    for chunk in resp.iter_content(chunk_size=1 << 20):
        fh.write(chunk)
print(f"Downloaded NWB -> {nwb_path} ({time.time()-t0:.1f}s elapsed)")

# --- 3. spike-detect on suprathreshold sweeps ---
SUPRATHRESHOLD_STIMS = {b"Long Square", b"Noise 1", b"Noise 2", b"Square - 2s Suprathreshold"}

f = h5py.File(nwb_path, "r")
sweeps = list(f["acquisition/timeseries"].keys())
stim_counts = Counter(f["acquisition/timeseries"][s]["aibs_stimulus_name"][()] for s in sweeps)
print("Stimulus types in this cell's recording:", dict(stim_counts))

all_spike_times = []   # absolute session time (seconds), using each sweep's starting_time
per_sweep_summary = []
for s in sweeps:
    grp = f["acquisition/timeseries"][s]
    name = grp["aibs_stimulus_name"][()]
    if name not in SUPRATHRESHOLD_STIMS:
        continue
    conv = grp["data"].attrs["conversion"]
    rate = grp["starting_time"].attrs["rate"]        # Hz, sampling rate
    t_start = grp["starting_time"][()]               # seconds, session clock
    data = grp["data"][()] * conv                     # Volts

    above = data > 0.0
    crossings = np.where(np.diff(above.astype(int)) == 1)[0]
    refr = int(0.002 * rate)  # 2 ms refractory
    keep = []
    last = -refr
    for c in crossings:
        if c - last >= refr:
            keep.append(c)
            last = c
    spike_t = t_start + np.array(keep) / rate
    all_spike_times.extend(spike_t.tolist())
    per_sweep_summary.append((name, t_start, len(data) / rate, len(keep)))

all_spike_times = np.sort(np.array(all_spike_times))
n_events = len(all_spike_times)
print(f"Total spikes across all suprathreshold sweeps: {n_events}")

resolution_sec = 1.0 / 200000.0  # 200 kHz sampling, from starting_time.rate
dt = np.diff(all_spike_times)
mean_iei = dt.mean() if len(dt) else float("nan")
print(f"Timestamp resolution: {resolution_sec*1e6:.1f} microseconds")
print(f"Mean inter-event interval (across sweep boundaries, includes inter-sweep gaps): {mean_iei:.4f} s")

crit_a = n_events >= 1e4
crit_b = resolution_sec < mean_iei
print(f"Criterion (a) [>=1e4 events]: {crit_a} ({n_events} events)")
print(f"Criterion (b) [resolution finer than mean IEI]: {crit_b}")

# --- 4. 4-panel event-rate plot across the session, for the stationarity eyeball ---
t_rel_min = (all_spike_times - all_spike_times.min()) / 60.0
span_min = t_rel_min.max() if n_events else 1.0

fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].hist(t_rel_min, bins=60)
axes[0, 0].set_title(f"Specimen {specimen_id}: all suprathreshold sweeps, session timeline")
axes[0, 0].set_xlabel("minutes since first spike")
axes[0, 0].set_ylabel("events / bin")

# per-sweep spike counts in sweep order (shows sweep-to-sweep structure directly)
sweep_names = [str(x[0]) for x in per_sweep_summary]
sweep_counts = [x[3] for x in per_sweep_summary]
axes[0, 1].bar(range(len(sweep_counts)), sweep_counts)
axes[0, 1].set_title("spikes per sweep (sweep order)")
axes[0, 1].set_xlabel("sweep index (suprathreshold sweeps only)")
axes[0, 1].set_ylabel("spike count")

# zoom into a single Noise sweep (closest thing to a sustained, irregular drive)
noise_sweeps = [s for s in sweeps if f["acquisition/timeseries"][s]["aibs_stimulus_name"][()] in (b"Noise 1", b"Noise 2")]
if noise_sweeps:
    grp = f["acquisition/timeseries"][noise_sweeps[0]]
    conv = grp["data"].attrs["conversion"]
    rate = grp["starting_time"].attrs["rate"]
    data = grp["data"][()] * conv
    above = data > 0.0
    crossings = np.where(np.diff(above.astype(int)) == 1)[0]
    refr = int(0.002 * rate)
    keep = []
    last = -refr
    for c in crossings:
        if c - last >= refr:
            keep.append(c)
            last = c
    spike_t_sec = np.array(keep) / rate
    axes[1, 0].hist(spike_t_sec, bins=np.arange(0, data.shape[0] / rate + 0.5, 0.5))
    axes[1, 0].set_title(f"single Noise sweep ({noise_sweeps[0]}), 0.5-sec bins")
    axes[1, 0].set_xlabel("seconds into sweep")
    axes[1, 0].set_ylabel("events / 0.5 sec")
else:
    axes[1, 0].set_title("no Noise sweep found")

# inter-sweep gap structure (shows this is NOT a continuous point process)
starting_times = np.array([x[1] for x in per_sweep_summary])
axes[1, 1].plot(np.sort(starting_times), np.arange(len(starting_times)), "o-")
axes[1, 1].set_title("cumulative sweep count vs session clock (gaps = idle time)")
axes[1, 1].set_xlabel("session time (s)")
axes[1, 1].set_ylabel("cumulative sweep #")

fig.tight_layout()
plot_path = "03_allen_event_rate.png"
fig.savefig(plot_path, dpi=120)
print(f"Saved plot -> {plot_path}")

elapsed = time.time() - t0
print(f"\nElapsed: {elapsed:.1f}s (this excludes earlier exploration: allensdk install attempt, "
      f"RMA query-syntax trial and error, ~25-30 min total wall-clock for this substrate)")
print("\n--- SUMMARY ---")
print(f"criterion (a): {'PASS' if crit_a else 'FAIL'} ({n_events} events from one cell's full recording "
      f"-- pooling across cells would not be one coherent point process)")
print(f"criterion (b): {'PASS' if crit_b else 'FAIL'} (resolution {resolution_sec*1e6:.1f}us vs mean IEI {mean_iei:.3f}s)")
print("criterion (c): FAIL/not applicable -- this is trial-based evoked-response data (short current-pulse "
      "sweeps separated by idle gaps), not an ongoing spontaneous process; no natural stationary segment to extract. "
      "(A Neuropixels spontaneous-activity session would be the right neural substrate for this, but requires "
      "a multi-GB NWB pull that exceeds this experiment's timebox -- kill criterion invoked.)")
