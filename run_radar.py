"""Method 8b - radar roughness below DEM resolution (ESA Sentinel-1, C-band 5.6 cm).

On dry, bare ground C-band backscatter rises with surface roughness at the centimetre-
decimetre scale (rocks, crust, ripples) that no DEM resolves. Sentinel-1 RTC (radiometric
terrain corrected gamma0, Planetary Computer) for a dry-season scene, VV and VH, median
over a 1 km box. Moisture also raises backscatter, so only July-August scenes are used.
Bare-ground references: Salar de Uyuni (smoothest), Black Point lava (rough).
The lunar counterpart is LRO Mini-RF (S-band, 12.6 cm), a different wavelength and
geometry, so the comparison is by rank only and is not computed here.
Run: .venv/bin/python run_radar.py    Out: results/radar.md, radar.csv
"""
import csv, json, pathlib, threading, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio
import requests
from rasterio.warp import transform
from rasterio.windows import Window
from scipy.stats import mannwhitneyu

from kzanalog import sites

OUT = pathlib.Path(__file__).parent / "results"
CACHE = pathlib.Path(__file__).parent / "data" / "cache_s1"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
TOKEN = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel-1-rtc"
_tok, _lock = [], threading.Lock()
EXTRA = {"Salar de Uyuni (smooth reference)": (-20.20, -67.60)}


def token():
    with _lock:
        while not _tok:
            j = requests.get(TOKEN, timeout=60).json()
            if "token" in j:
                _tok.append(j["token"])
            else:
                time.sleep(20)
    return _tok[0]


def sample(href, lat, lon):
    with rasterio.open(f"{href}?{token()}") as ds:
        x, y = transform("EPSG:4326", ds.crs, [lon], [lat])
        r, c = ds.index(x[0], y[0])
        a = ds.read(1, window=Window(c - 50, r - 50, 100, 100), boundless=True, fill_value=0).astype("float64")
    a = a[a > 0]
    return float(10 * np.log10(np.median(a))) if a.size > 1000 else float("nan")


def site(job):
    grp, name, (lat, lon) = job
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{lat:+08.3f}_{lon:+09.3f}.json"
    if f.exists():
        return dict(group=grp, name=name, **json.loads(f.read_text()))
    # Sentinel-1B failed in Dec 2021, so parts of Kazakhstan have no summer 2022-2023 scenes:
    # fall back to the same dry months of 2021 (the year is reported per site).
    it = []
    try:
        for yr in (2023, 2021):
            months = f"{yr}-07-01/{yr}-08-31" if lat >= 0 else f"{yr}-08-01/{yr}-09-30"
            it = requests.post(STAC, json={"collections": ["sentinel-1-rtc"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
                                           "datetime": months, "limit": 8}, timeout=90).json()["features"]
            if it:
                break
        out = None
        for i in it:  # first scene where the 1 km box is fully inside the swath
            vv = sample(i["assets"]["vv"]["href"], lat, lon)
            if np.isfinite(vv):
                out = dict(vv=vv, vh=sample(i["assets"]["vh"]["href"], lat, lon), date=i["properties"]["datetime"][:10])
                break
        if out is None:
            return dict(group=grp, name=name, error="no scene covering the box")
    except Exception as e:
        return dict(group=grp, name=name, error=repr(e)[:100])
    f.write_text(json.dumps(out))
    return dict(group=grp, name=name, **out)


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [("kazakhstan", n, c) for n, c in sites.KAZAKHSTAN.items()] + [("reference", n, c) for n, c in {**sites.REFERENCE, **EXTRA}.items()]
    jobs += [("control", n, c) for n, c in sites.random_controls().items()]
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(site, jobs))
    bad = [r for r in rows if "error" in r or not np.isfinite(r.get("vv", np.nan))]
    rows = [r for r in rows if r not in bad]
    with open(OUT / "radar.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["group", "name", "vv", "vh", "date"]); w.writeheader(); w.writerows(rows)
    ctrl = np.array([r["vv"] for r in rows if r["group"] == "control"])
    kz = np.array([r["vv"] for r in rows if r["group"] == "kazakhstan"])
    u = mannwhitneyu(kz, ctrl, alternative="two-sided")
    md = ["# Radar roughness: Sentinel-1 RTC gamma0 VV, dry season 2023 (2021 where no 2023 scene), 1 km box\n\n",
          f"Kazakhstan median {np.median(kz):.1f} dB vs controls {np.median(ctrl):.1f} dB (two-sided p = {u.pvalue:.2g}); "
          f"no data: {[b['name'] for b in bad if b['group'] != 'control']}\n\n",
          "| site | group | VV dB | VH dB | rougher than % of controls | scene |\n|---|---|---|---|---|---|\n"]
    for r in sorted(rows, key=lambda r: -r["vv"]):
        if r["group"] != "control":
            md.append(f"| {r['name']} | {r['group']} | {r['vv']:.1f} | {r['vh']:.1f} | {100*np.mean(ctrl < r['vv']):.0f} | {r['date']} |\n")
    md.append("\nWhere it breaks: backscatter also rises with soil moisture and sparse shrubs; C-band (5.6 cm) on Earth vs "
              "S-band Mini-RF (12.6 cm) on the Moon, so only ranks can be compared.\n")
    (OUT / "radar.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
