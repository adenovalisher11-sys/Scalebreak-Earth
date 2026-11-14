"""Method 5 - thermal regime of Earth sites (MODIS) and albedo against Mars (TES).

Pre-declared hypotheses:
  H1  Kazakhstan sites have a larger annual surface-temperature range than random
      arid controls (one-sided).
  H2  Kazakhstan sites pass the Mars "not dust-covered" albedo rule (< 0.25, paper 21)
      at least as often as controls.
Measured per Earth site (year 2023, Aqua MYD11A2 at ~13:30 / ~01:30 local):
  diurnal_amp  mean (T_day - T_night) over the 3 warmest months, K
  annual_range max monthly T_day - min monthly T_night, K
  albedo       approximate shortwave albedo, warmest month (MCD43A4 + Liang 2001)
  ati          apparent thermal inertia (1 - albedo) / (T_day - T_night), paper 11;
               unitless, moisture-sensitive: compare by rank only
  ndvi_max     yearly maximum NDVI; > 0.3 flags seasonal vegetation
Mars side: TES bolometric albedo (USGS global mosaic) at the landing sites.
Run:  .venv/bin/python run_thermal.py    Out: results/thermal.csv, thermal.md, thermal.png
"""
import csv
import pathlib
import warnings
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rasterio
from scipy.stats import mannwhitneyu

from kzanalog import modis, sites

OUT = pathlib.Path(__file__).parent / "results"
TES_ALBEDO = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars_MGS_TES_Albedo_mosaic_global_7410m.tif"
warnings.simplefilter("ignore", RuntimeWarning)


def earth(job):
    group, name, (lat, lon) = job
    try:
        p = modis.year_profile(lat, lon)
    except Exception as e:
        return dict(group=group, name=name, error=repr(e))
    td, tn = np.array(p["tday"]), np.array(p["tnight"])
    if np.isfinite(td).sum() < 8 or np.isfinite(tn).sum() < 8:
        return dict(group=group, name=name, error="fewer than 8 months of valid LST")
    amp = td - tn
    warm3 = np.argsort(np.where(np.isfinite(td), td, -1))[-3:]
    d = float(np.nanmean(amp[warm3]))
    a = p["albedo"]
    return dict(group=group, name=name, lat=lat, lon=lon, diurnal_amp=d,
                annual_range=float(np.nanmax(td) - np.nanmin(tn)),
                tday_max=float(np.nanmax(td)), tnight_min=float(np.nanmin(tn)), albedo=a,
                ati=float((1 - a) / d) if np.isfinite(a) and d > 0 else float("nan"),
                ndvi_max=p["ndvi_max"], months=int(np.isfinite(amp).sum()))


def mars_albedo():
    out = {}
    with rasterio.open(TES_ALBEDO) as ds:
        R = 3396190.0
        for name, (lat, lon) in {**sites.MARS, "Top settlement site (paper 21)": (1.40, -7.4)}.items():
            x, y = (np.radians(lon) * R, np.radians(lat) * R) if not ds.crs.is_geographic else (lon, lat)
            v = float(next(ds.sample([(x, y)]))[0])
            out[name] = v * (ds.scales[0] or 1) + (ds.offsets[0] or 0)
        meta = f"dtype {ds.dtypes[0]}, nodata {ds.nodata}, scale {ds.scales[0]}"
    return out, meta


def main():
    OUT.mkdir(exist_ok=True)
    jobs = []
    for grp, d in (("kazakhstan", sites.KAZAKHSTAN), ("reference", sites.REFERENCE), ("control", sites.random_controls())):
        jobs += [(grp, n, c) for n, c in d.items()]
    with ThreadPoolExecutor(12) as ex:
        rows = list(ex.map(earth, jobs))
    bad = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    with open(OUT / "thermal.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    mars, meta = mars_albedo()

    def col(grp, k):
        return np.array([r[k] for r in rows if r["group"] == grp and np.isfinite(r[k])])

    md = ["# Thermal regime (MODIS 2023) and albedo\n\n",
          f"Earth sites with data: {len(rows)}; failed: {len(bad)} {[b['name'] for b in bad]}\n\n",
          "| group | n | annual range, K (median) | diurnal amplitude, K | albedo | albedo < 0.25 | NDVI max > 0.3 |\n|---|---|---|---|---|---|---|\n"]
    for grp in ("kazakhstan", "reference", "control"):
        g = [r for r in rows if r["group"] == grp]
        al = col(grp, "albedo")
        md.append(f"| {grp} | {len(g)} | {np.median(col(grp,'annual_range')):.0f} | {np.median(col(grp,'diurnal_amp')):.0f} | "
                  f"{np.median(al):.2f} | {int((al < 0.25).sum())}/{len(al)} | {sum(r['ndvi_max'] > 0.3 for r in g)}/{len(g)} |\n")
    h1 = mannwhitneyu(col("kazakhstan", "annual_range"), col("control", "annual_range"), alternative="greater")
    h1b = mannwhitneyu(col("kazakhstan", "diurnal_amp"), col("control", "diurnal_amp"), alternative="two-sided")
    md.append(f"\nH1 annual range Kazakhstan > controls: Mann-Whitney one-sided p = {h1.pvalue:.2g}\n\n"
              f"Diurnal amplitude Kazakhstan vs controls (two-sided): p = {h1b.pvalue:.2g}\n\n")
    ctrl_rng = col("control", "annual_range")
    md.append("| site | group | annual range K | beats % of controls | diurnal amp K | T_day max K | T_night min K | albedo | ATI | NDVI max |\n|---|---|---|---|---|---|---|---|---|---|\n")
    for r in sorted(rows, key=lambda r: -r["annual_range"]):
        if r["group"] != "control":
            md.append(f"| {r['name']} | {r['group']} | {r['annual_range']:.0f} | {100*np.mean(ctrl_rng < r['annual_range']):.0f} | "
                      f"{r['diurnal_amp']:.0f} | {r['tday_max']:.0f} | {r['tnight_min']:.0f} | {r['albedo']:.2f} | {r['ati']:.3f} | {r['ndvi_max']:.2f} |\n")
    md.append(f"\n## Mars: TES albedo at landing sites ({meta})\n\n| site | albedo | < 0.25 |\n|---|---|---|\n")
    for n, v in mars.items():
        md.append(f"| {n} | {v:.3f} | {'yes' if v < 0.25 else 'no'} |\n")
    (OUT / "thermal.md").write_text("".join(md)); print("".join(md))

    fig, ax = plt.subplots(figsize=(7.5, 5))
    for grp, c, s in (("control", "0.7", 18), ("reference", "#2b6cb0", 40), ("kazakhstan", "#1a7f37", 55)):
        g = [r for r in rows if r["group"] == grp]
        ax.scatter([r["diurnal_amp"] for r in g], [r["annual_range"] for r in g], c=c, s=s, label=grp, zorder=3 if grp != "control" else 1)
        if grp == "kazakhstan":
            for r in g:
                ax.annotate(r["name"].split(" (")[0], (r["diurnal_amp"], r["annual_range"]), fontsize=6, xytext=(3, 2), textcoords="offset points")
    ax.set_xlabel("diurnal surface-temperature amplitude, warm season (K)")
    ax.set_ylabel("annual surface-temperature range (K)")
    ax.set_title("Thermal regime of analog candidates (NASA MODIS MYD11A2, 2023)")
    ax.grid(alpha=.3); ax.legend()
    fig.tight_layout(); fig.savefig(OUT / "thermal.png", dpi=150)


if __name__ == "__main__":
    main()
