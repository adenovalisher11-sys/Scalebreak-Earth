"""Method 1 - blind terrain ranking.

Question: are Kazakhstan sites closer to real Mars / Moon landing terrain than
random arid ground, and how do they compare with established analog sites?

Run:  .venv/bin/python run_terrain.py
Out:  results/terrain.json, results/ranking_<body>.csv, results/*.png, results/summary.md
"""
import csv
import json
import pathlib
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker
import numpy as np
from scipy.stats import mannwhitneyu

from kzanalog import dem, sites
from kzanalog.fingerprint import BASELINES_M, fingerprint, log_distance

OUT = pathlib.Path(__file__).parent / "results"
HALF_KM = 16.0
METRICS = ("slope_deg", "rough_m")


def compute(job):
    group, body, name, (lat, lon) = job
    try:
        z, dx, dy = dem.window(body, lat, lon, HALF_KM)
        f = fingerprint(z, dx, dy)
    except Exception as e:  # network or coverage failure: record, do not hide
        return dict(group=group, body=body, name=name, lat=lat, lon=lon, error=repr(e))
    return dict(group=group, body=body, name=name, lat=lat, lon=lon, px_m=round(max(dx, dy), 1), **f)


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [("target", "mars", n, c) for n, c in sites.MARS.items()]
    jobs += [("target", "moon", n, c) for n, c in sites.MOON.items()]
    for grp, d in (("kazakhstan", sites.KAZAKHSTAN), ("reference", sites.REFERENCE),
                   ("noise", sites.NOISE_FLOOR), ("control", sites.random_controls(n_per_box=25))):
        jobs += [(grp, "earth", n, c) for n, c in d.items()]
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(compute, jobs))
    failed = [r for r in rows if "error" in r or r.get("valid_frac", 0) < 0.9]
    rows = [r for r in rows if r not in failed]
    (OUT / "terrain.json").write_text(json.dumps(dict(baselines_m=BASELINES_M, half_km=HALF_KM,
                                                      sites=rows, failed=failed), indent=1))

    noise = next(r for r in rows if r["group"] == "noise")
    earth = [r for r in rows if r["body"] == "earth" and r["group"] != "noise"]
    unusable = [r["name"] for r in earth if not (np.all(np.isfinite(r["slope_deg"])) and np.all(np.array(r["rough_m"]) > 0))]
    earth = [r for r in earth if r["name"] not in unusable]
    # Step 2: controls must be bare ground. Drop controls whose 2023 maximum NDVI exceeds 0.3.
    from kzanalog.modis import ndvi_max
    ctl = [r for r in earth if r["group"] == "control"]
    with ThreadPoolExecutor(8) as ex:
        nd = list(ex.map(lambda r: ndvi_max(r["lat"], r["lon"]), ctl))
    vegetated = [r["name"] for r, v in zip(ctl, nd) if not (v <= 0.3)]
    earth = [r for r in earth if r["name"] not in vegetated]
    veg_note = (f"Controls dropped as vegetated or no NDVI (max NDVI > 0.3, MODIS 2023): {len(vegetated)}; "
                f"bare controls kept: {len(ctl) - len(vegetated)}.\n")
    summary = ["# Terrain ranking (method 1)\n",
               f"Window {2*HALF_KM:g} km, baselines {BASELINES_M} m. "
               f"Sites computed: {len(rows)}, failed/insufficient data: {len(failed)}, "
               f"dropped as unusable (zero roughness, i.e. water or void-filled): {len(unusable)} {unusable}.\n", veg_note,
               "DEM noise floor (Salar de Uyuni): slope "
               + ", ".join(f"{s:.3f}° @{L} m" for s, L in zip(noise["slope_deg"], BASELINES_M)) + "\n"]

    for body in ("mars", "moon"):
        tg_all = [r for r in rows if r["group"] == "target" and r["body"] == body]
        # Step 2: landing sites differ from each other more than from Earth, so the target is
        # the "plains" class only (median slope < 1 deg at 480 m); relief-class sites
        # (crater floors with rims in view, mountain valleys) are listed but not used.
        tg = [r for r in tg_all if r["slope_deg"][1] < 1.0]
        summary.append(f"\nPlains-class targets used for {body}: {[t['name'] for t in tg]}; "
                       f"relief-class (not used): {[t['name'] for t in tg_all if t not in tg]}\n")
        env = {m: dict(med=np.nanmedian([t[m] for t in tg], axis=0),
                       lo=np.nanmin([t[m] for t in tg], axis=0),
                       hi=np.nanmax([t[m] for t in tg], axis=0)) for m in METRICS}
        # leave-one-out: how far is each real landing site from the median of the others?
        loo = []
        for t in tg:
            rest = [o for o in tg if o is not t]
            loo.append(np.mean([log_distance(t[m], np.nanmedian([o[m] for o in rest], axis=0)) for m in METRICS]))
        for r in earth:
            r[f"D_{body}"] = float(np.mean([log_distance(r[m], env[m]["med"]) for m in METRICS]))
            # signed: >0 means the Earth site is rougher than the target, <0 smoother
            r[f"bias_{body}"] = float(np.nanmean(np.log(np.array(r["slope_deg"]) / env["slope_deg"]["med"])))
            # scale break: walk from coarse to fine while slope stays inside target envelope
            inside = [bool(env["slope_deg"]["lo"][i] <= r["slope_deg"][i] <= env["slope_deg"]["hi"][i])
                      if np.isfinite(env["slope_deg"]["lo"][i]) else None for i in range(len(BASELINES_M))]
            brk = None
            for i in reversed(range(len(BASELINES_M))):
                if inside[i] is not True:
                    break
                brk = BASELINES_M[i]
            r[f"analog_down_to_m_{body}"] = brk
            r[f"at_noise_{body}"] = bool(r["slope_deg"][0] < 2 * noise["slope_deg"][0])
        ranked = sorted(earth, key=lambda r: r[f"D_{body}"])
        ctrl = np.array([r[f"D_{body}"] for r in earth if r["group"] == "control"])
        with open(OUT / f"ranking_{body}.csv", "w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["rank", "site", "group", "lat", "lon", "distance", "pct_of_controls_worse",
                        "analog_down_to_m", "slope_240m_near_noise_floor", "rougher_or_smoother"])
            for i, r in enumerate(ranked, 1):
                r[f"pct_{body}"] = float(100 * np.mean(ctrl > r[f"D_{body}"]))
                w.writerow([i, r["name"], r["group"], r["lat"], r["lon"], f"{r[f'D_{body}']:.3f}",
                            f"{r[f'pct_{body}']:.0f}", r[f"analog_down_to_m_{body}"], r[f"at_noise_{body}"],
                            "rougher" if r[f"bias_{body}"] > 0 else "smoother"])
        summary.append(f"\n## {body.capitalize()} ({len(tg)} landing sites as target)\n")
        summary.append(f"Landing sites vs each other (leave-one-out distance): median {np.median(loo):.2f}, "
                       f"max {np.max(loo):.2f}. An Earth site below ~{np.median(loo):.2f} is as close to the "
                       f"target as real landing sites are to one another.\n")
        for grp in ("kazakhstan", "reference"):
            d = np.array([r[f"D_{body}"] for r in earth if r["group"] == grp])
            u = mannwhitneyu(d, ctrl, alternative="less")
            summary.append(f"- {grp}: median distance {np.median(d):.2f} vs controls {np.median(ctrl):.2f}; "
                           f"Mann-Whitney one-sided p = {u.pvalue:.3f} (n={len(d)} vs {len(ctrl)})\n")
        summary.append("\n| rank | site | group | distance | vs target | beats % of controls | analog down to |\n|---|---|---|---|---|---|---|\n")
        for i, r in enumerate(ranked, 1):
            if r["group"] != "control":
                b = r[f"analog_down_to_m_{body}"]
                summary.append(f"| {i}/{len(ranked)} | {r['name']} | {r['group']} | {r[f'D_{body}']:.2f} | "
                               f"{'rougher' if r[f'bias_{body}'] > 0 else 'smoother'} x{np.exp(abs(r[f'bias_{body}'])):.1f} | "
                               f"{r[f'pct_{body}']:.0f} | {str(b)+' m' if b else 'not within envelope'} |\n")

        # figure: curves
        fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
        L = np.array(BASELINES_M)
        for ax, m, lab in zip(axes, METRICS, ("median slope (deg)", "detrended roughness (m)")):
            ax.fill_between(L, env[m]["lo"], env[m]["hi"], color="#d9534f", alpha=.18, label=f"{body} landing sites (range)")
            ax.plot(L, env[m]["med"], color="#d9534f", lw=2.5, label=f"{body} landing sites (median)")
            for r in earth:
                if r["group"] == "control":
                    ax.plot(L, r[m], color="0.75", lw=.6, zorder=0)
            for r in earth:
                if r["group"] == "reference":
                    ax.plot(L, r[m], color="#2b6cb0", lw=1, alpha=.7)
                if r["group"] == "kazakhstan":
                    ax.plot(L, r[m], color="#1a7f37", lw=1.4)
            ax.plot(L, noise[m], "k--", lw=1, label="DEM noise floor (Uyuni)")
            ax.set_xscale("log"); ax.set_yscale("log"); ax.set_xticks(L); ax.set_xticklabels(L); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
            ax.set_xlabel("baseline (m)"); ax.set_ylabel(lab); ax.grid(alpha=.3, which="both")
        axes[0].plot([], [], color="#1a7f37", label="Kazakhstan"); axes[0].plot([], [], color="#2b6cb0", label="established analogs")
        axes[0].plot([], [], color="0.75", label="random arid controls"); axes[0].legend(fontsize=7)
        fig.suptitle(f"Terrain fingerprint vs {body.capitalize()} landing sites (NASADEM / "
                     f"{'HRSC+MOLA' if body=='mars' else 'LOLA'})")
        fig.tight_layout(); fig.savefig(OUT / f"curves_{body}.png", dpi=150); plt.close(fig)

    (OUT / "terrain.json").write_text(json.dumps(dict(baselines_m=BASELINES_M, half_km=HALF_KM,
                                                      sites=rows, failed=failed), indent=1))
    (OUT / "summary.md").write_text("".join(summary))
    print("".join(summary))
    if failed:
        print("FAILED:", [(f["name"], f.get("error", f"valid={f.get('valid_frac')}")) for f in failed])


if __name__ == "__main__":
    main()
