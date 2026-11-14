"""Method 5c - thermal inertia by rank: Earth ATI (MODIS) vs Mars TI (TES).

Earth apparent thermal inertia (paper 11) is unitless and moisture-driven; Mars TES thermal
inertia is in SI units and depends on air pressure. Raw values cannot be compared, so each
side is converted to a percentile WITHIN its own planet's distribution:
  Earth: ATI percentile of a site among the random arid control points (results/thermal.csv)
  Mars : TI percentile of a landing site among 5,000 random TES pixels within +-45 deg
Question: do the Kazakh sites sit in the same part of their planet's distribution as the
Mars landing sites sit in theirs? Also reports the published firm-ground rules (papers 19, 21)
for the Mars sites: TI > 100 load-bearing, 350-600 firm ground for heavy landers.
Data: NASA PDS Geosciences MGS-M-TES-5-TIMAP-V1.0 GLOBAL_TI_NIGHT_2007 (Putzig & Mellon 2007),
20 px/deg, MSB int16, downloaded to data/tes/ (52 MB) on first run.
The Moon is not included: lunar regolith TI is nearly uniform (~55 SI, Hayne 2017), so a
percentile there says nothing about the surface.
Run: .venv/bin/python run_ti.py   Out: results/ti.md
"""
import csv, pathlib

import numpy as np
import requests
from scipy.stats import mannwhitneyu

from kzanalog import sites

ROOT = pathlib.Path(__file__).parent
IMG = ROOT / "data" / "tes" / "global_ti_night_2007.img"
URL = "https://pds-geosciences.wustl.edu/mgs/mgs-m-tes-5-timap-v1/mgst_9001/data/global_ti_night_2007.img"


def tes():
    if not IMG.exists():
        IMG.parent.mkdir(parents=True, exist_ok=True)
        IMG.write_bytes(requests.get(URL, timeout=600).content)
    a = np.fromfile(IMG, dtype=">i2").reshape(3600, 7200).astype("float32")
    a[a <= 0] = np.nan
    return a


def ti_at(a, lat, lon):
    r = int((90 - lat) * 20); c = int((lon + 180) * 20) % 7200
    w = a[max(0, r - 1):r + 2, max(0, c - 1):c + 2]
    return float(np.nanmedian(w))


def main():
    a = tes()
    rng = np.random.default_rng(1)
    lats = np.degrees(np.arcsin(rng.uniform(np.sin(np.radians(-45)), np.sin(np.radians(45)), 20000)))
    pool = np.array([ti_at(a, la, lo) for la, lo in zip(lats, rng.uniform(-180, 180, 20000))])
    pool = pool[np.isfinite(pool)][:5000]
    mars = {n: ti_at(a, la, lo) for n, (la, lo) in {**sites.MARS, "Top settlement site (paper 21)": (1.40, -7.4)}.items()}
    with open(ROOT / "results" / "thermal.csv") as fh:
        rows = [r for r in csv.DictReader(fh)]
    ati = lambda grp: np.array([float(r["ati"]) for r in rows if r["group"] == grp and r["ati"] not in ("", "nan")])
    ctrl = ati("control")
    kz = {r["name"]: float(r["ati"]) for r in rows if r["group"] == "kazakhstan" and r["ati"] not in ("", "nan")}
    mars_pct = {n: 100 * np.mean(pool < v) for n, v in mars.items() if np.isfinite(v)}
    kz_pct = {n: 100 * np.mean(ctrl < v) for n, v in kz.items()}
    lo, hi = np.min(list(mars_pct.values())), np.max(list(mars_pct.values()))
    md = ["# Thermal inertia by rank: Mars TES vs Earth MODIS ATI\n\n",
          f"Mars random pool: {len(pool)} TES pixels, median TI {np.median(pool):.0f} SI.\n\n",
          "| Mars landing site | TES TI (SI) | > 100 load-bearing | 350-600 heavy-lander | percentile on Mars |\n|---|---|---|---|---|\n"]
    for n, v in mars.items():
        md.append(f"| {n} | {v:.0f} | {'yes' if v > 100 else 'no'} | {'yes' if 350 <= v <= 600 else 'no'} | {mars_pct.get(n, float('nan')):.0f} |\n")
    md.append(f"\nMars landing sites span percentiles {lo:.0f}-{hi:.0f} of their planet (median {np.median(list(mars_pct.values())):.0f}).\n\n"
              "| Kazakh site | ATI | percentile among Earth arid controls | inside the Mars landing-site band |\n|---|---|---|---|\n")
    inside = 0
    for n, p in sorted(kz_pct.items(), key=lambda x: -x[1]):
        ok = lo <= p <= hi; inside += ok
        md.append(f"| {n} | {kz[n]:.3f} | {p:.0f} | {'yes' if ok else 'no'} |\n")
    u = mannwhitneyu(list(kz_pct.values()), list(mars_pct.values()), alternative="two-sided")
    md.append(f"\n{inside} of {len(kz_pct)} Kazakh sites fall inside the percentile band of Mars landing sites. "
              f"Percentile distributions Kazakhstan vs Mars landing sites: two-sided p = {u.pvalue:.2g} "
              f"(high p = no evidence they differ).\n\n"
              "Where it breaks: ATI is driven by soil moisture and vegetation (paper 11); Mars TI by grain size and "
              "atmospheric pressure. Matching percentiles means 'same position in the planet's range', not the same physics.\n")
    (ROOT / "results" / "ti.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
