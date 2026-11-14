"""Method 5b - ice under a dry cover: the lunar-pole comparison the challenge resources suggest.

Moon : NASA LRO Diviner Polar Resource Product (PRP v2, PDS Geosciences), south pole:
       per surface triangle the annual average and maximum temperature and the modelled
       depth at which water ice is stable (-999 = not stable in the top metre of the model).
       The 605 MB table is sampled with HTTP range requests (random blocks of fixed-width rows).
Earth: NASA MODIS MYD11A2 surface temperature (2023) at a Tien Shan glacier / moraine pixel
       and two steppe sites. Depth at which the annual temperature wave no longer reaches
       273 K is estimated by pure conduction:  z = delta * ln(A / (273.15 - T_mean)),
       delta = sqrt(kappa * P / pi), with kappa = 5e-7 m2/s ASSUMED for dry debris.
This is a process comparison (a dry layer damps the temperature wave so ice survives
below it). It is NOT a temperature analog, and the script prints the gap.
Run: .venv/bin/python run_ice.py    Out: results/ice.md, ice.png
"""
import json, pathlib, random
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import requests

from kzanalog import modis

OUT = pathlib.Path(__file__).parent / "results"
CACHE = pathlib.Path(__file__).parent / "data" / "diviner_prp_south_sample.json"
PRP = "https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_prp/dlre_prp_south.tab"
ROW, NROWS, BLOCK, NBLOCKS = 210, 2880000, 200, 400
EARTH = {"Tuyuksu glacier area, Tien Shan (3.4 km a.s.l.)": (43.048, 77.081),
         "Soyuz zone, Zhezkazgan steppe": (47.35, 69.60),
         "Arkalyk steppe": (50.20, 66.90)}
KAPPA, YEAR = 5e-7, 365.25 * 86400


def prp_sample():
    if CACHE.exists():
        return json.loads(CACHE.read_text())
    rng = random.Random(3)
    starts = sorted(rng.sample(range(1, NROWS - BLOCK), NBLOCKS))
    def get(s):
        for _ in range(4):
            try:
                r = requests.get(PRP, headers={"Range": f"bytes={s*ROW}-{(s+BLOCK)*ROW-1}"}, timeout=60)
                if r.status_code == 206:
                    return r.text
            except Exception:
                pass
        return ""
    with ThreadPoolExecutor(6) as ex:
        chunks = list(ex.map(get, starts))
    rows = []
    for c in chunks:
        for line in c.splitlines():
            p = line.split(",")
            if len(p) == 15:
                try:
                    rows.append([float(p[10]), float(p[12]), float(p[13]), float(p[14])])  # lat, Tavg, Tmax, ice depth
                except ValueError:
                    pass
    CACHE.write_text(json.dumps(rows))
    return rows


def main():
    OUT.mkdir(exist_ok=True)
    d = np.array(prp_sample())
    lat, tavg, tmax, ice = d.T
    stable = ice > -900
    surf = stable & (ice <= 0.0)
    buried = stable & (ice > 0)
    md = ["# Ice under a dry cover: lunar south pole (Diviner) vs Kazakhstan (MODIS)\n\n",
          f"## Moon: Diviner PRP south, random sample of {len(d):,} of 2,880,000 surface triangles "
          f"(latitudes {lat.min():.1f} to {lat.max():.1f})\n\n",
          f"- annual maximum temperature: median {np.median(tmax):.0f} K, 5th pct {np.percentile(tmax,5):.0f} K\n",
          f"- triangles with maximum temperature below 110 K: {np.mean(tmax < 110):.1%}\n",
          f"- model says ice stable somewhere in the column: {stable.mean():.1%}; at the surface (depth 0): {surf.mean():.1%}; "
          f"only under a dry layer: {buried.mean():.1%}\n"]
    if buried.any():
        md.append(f"- where ice is buried: depth median {np.median(ice[buried]):.2f} m (10th-90th pct "
                  f"{np.percentile(ice[buried],10):.2f}-{np.percentile(ice[buried],90):.2f} m); "
                  f"surface there averages {np.median(tavg[buried]):.0f} K and peaks at {np.median(tmax[buried]):.0f} K\n")
    delta = float(np.sqrt(KAPPA * YEAR / np.pi))
    md.append(f"\n## Earth: MODIS 2023 surface temperature, conduction estimate (annual skin depth {delta:.2f} m, kappa assumed)\n\n"
              "| site | mean surface T, K | annual half-range A, K | warmest month day T, K | depth where annual max stays below 273 K |\n|---|---|---|---|---|\n")
    earth = {}
    for name, (la, lo) in EARTH.items():
        p = modis.year_profile(la, lo)
        td, tn = np.array(p["tday"]), np.array(p["tnight"])
        mid = (td + tn) / 2
        tm, A = float(np.nanmean(mid)), float((np.nanmax(mid) - np.nanmin(mid)) / 2)
        z = delta * np.log(A / (273.15 - tm)) if tm < 273.15 and A > 273.15 - tm else None
        earth[name] = (tm, A, z)
        md.append(f"| {name} | {tm:.0f} | {A:.0f} | {np.nanmax(td):.0f} | "
                  f"{f'{z:.1f} m' if z else ('at the surface all year' if tm < 273.15 else 'none: mean above freezing, no permafrost by this estimate')} |\n")
    tm_ts = earth[list(EARTH)[0]][0]
    md.append(f"\n## Where the analogy breaks (measured)\n\n"
              f"- Temperature gap: the coldest Kazakh site averages {tm_ts:.0f} K; lunar ground with buried ice averages "
              f"{np.median(tavg[buried]) if buried.any() else float('nan'):.0f} K. Ice is lost by melting on Earth and by sublimation into vacuum on the Moon.\n"
              f"- Cover scale: metres of rock debris on Earth against a modelled {np.median(ice[buried]) if buried.any() else float('nan'):.2f} m of regolith on the Moon.\n"
              f"- The Earth depth uses an assumed diffusivity and ignores latent heat, snow and water flow.\n"
              f"- What does match: in both places ice is absent at the surface and survives below a dry layer that damps the temperature wave.\n")
    (OUT / "ice.md").write_text("".join(md)); print("".join(md))
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 4.2))
    ax[0].hist(tmax, bins=60, color="#6b7280"); ax[0].axvline(110, color="r", ls="--"); ax[0].set_xlabel("annual max surface temperature (K)")
    ax[0].set_title("Lunar south pole, Diviner PRP"); ax[0].set_ylabel("sampled triangles")
    for name, (tm, A, z) in earth.items():
        ax[0].axvline(tm, color="#1a7f37", lw=1)
    ax[0].text(0.98, 0.9, "green: Kazakh sites, annual mean\nred: 110 K ice limit", transform=ax[0].transAxes, ha="right", fontsize=7)
    if buried.any():
        ax[1].hist(ice[buried], bins=40, color="#2b6cb0"); ax[1].set_xlabel("modelled depth to stable ice (m)")
    ax[1].set_title("Moon: ice only under a dry layer")
    fig.tight_layout(); fig.savefig(OUT / "ice.png", dpi=150)


if __name__ == "__main__":
    main()
