"""Method 6 - hydrated-salt signal from ESA Sentinel-2 (small partner-data check).

EMIT mineral maps need an Earthdata login, so this uses open Sentinel-2 L2A instead.
Gypsum and other hydrated salts/clays absorb near 2.2 um, so reflectance in band 11
(1.61 um) exceeds band 12 (2.19 um). The ratio B11/B12 is a hydration indicator, NOT a
mineral identification: soil moisture, clays and vegetation raise it too. Vegetated pixels
(NDVI >= 0.15) are masked. Positive control: White Sands (gypsum dunes) must score high.
Takyr polygon sizes (planned) are not measurable: polygons are centimetres to metres,
below the 10 m pixel.
Run: .venv/bin/python run_salts.py   Out: results/salts.md, salts.csv
"""
import csv, json, pathlib, threading, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import rasterio
import requests
from rasterio.warp import transform
from rasterio.windows import Window

from kzanalog import sites

OUT = pathlib.Path(__file__).parent / "results"
CACHE = pathlib.Path(__file__).parent / "data" / "cache_s2"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
TOKEN = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel2l2a01/sentinel2-l2"
_tok = []
_lock = threading.Lock()
_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2")
EXTRA = {"Lake Inder salt flat (48.46N 51.93E, OSM lake centre)": (48.462, 51.929)}


def band(href, lat, lon, half_px):
    with _lock:
        while not _tok:  # one token for the whole run; the service rate-limits (HTTP 429)
            j = requests.get(TOKEN, timeout=60).json()
            if "token" in j:
                _tok.append(j["token"])
            else:
                time.sleep(20)
    signed = f"{href}?{_tok[0]}"
    with rasterio.Env(**_ENV), rasterio.open(signed) as ds:
        x, y = transform("EPSG:4326", ds.crs, [lon], [lat])
        r, c = ds.index(x[0], y[0])
        a = ds.read(1, window=Window(c - half_px, r - half_px, 2 * half_px, 2 * half_px), boundless=True, fill_value=0).astype("float64")
    a[a <= 0] = np.nan
    return a


def site(job):
    grp, name, (lat, lon) = job
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{lat:+08.3f}_{lon:+09.3f}.json"
    if f.exists():
        return dict(group=grp, name=name, **json.loads(f.read_text()))
    months = "2023-06-01/2023-08-31" if lat >= 0 else "2023-01-01/2023-02-28"
    try:
        r = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
                                      "datetime": months, "query": {"eo:cloud_cover": {"lt": 5}}, "limit": 20}, timeout=90).json()
        items = sorted(r.get("features", []), key=lambda i: i["properties"]["eo:cloud_cover"])
        if not items:
            return dict(group=grp, name=name, error="no cloud-free scene")
        it = items[0]
        b11, b12 = band(it["assets"]["B11"]["href"], lat, lon, 25), band(it["assets"]["B12"]["href"], lat, lon, 25)
        b8a, b04 = band(it["assets"]["B8A"]["href"], lat, lon, 25), band(it["assets"]["B04"]["href"], lat, lon, 50)
        b04 = np.nanmean(b04.reshape(50, 2, 50, 2), axis=(1, 3))
        ndvi = (b8a - b04) / (b8a + b04)
        bare = ndvi < 0.15
        if np.nansum(bare) < 100:
            out = dict(error="window mostly vegetated", date=it["properties"]["datetime"][:10])
        else:
            out = dict(ratio=float(np.nanmedian((b11 / b12)[bare])), b11=float(np.nanmedian(b11[bare]) / 1e4),
                       bare_frac=float(np.nanmean(bare)), ndvi=float(np.nanmedian(ndvi)), date=it["properties"]["datetime"][:10])
    except Exception as e:
        return dict(group=grp, name=name, error=repr(e)[:120])
    f.write_text(json.dumps(out))
    return dict(group=grp, name=name, **out)


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [("kazakhstan", n, c) for n, c in {**sites.KAZAKHSTAN, **EXTRA}.items()]
    jobs += [("reference", n, c) for n, c in sites.REFERENCE.items()] + [("control", n, c) for n, c in sites.random_controls().items()]
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(site, jobs))
    bad = [r for r in rows if "error" in r]; rows = [r for r in rows if "error" not in r]
    ctrl = np.array([r["ratio"] for r in rows if r["group"] == "control"])
    with open(OUT / "salts.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["group", "name", "ratio", "b11", "bare_frac", "ndvi", "date"]); w.writeheader(); w.writerows(rows)
    md = ["# Hydration indicator B11/B12 (Sentinel-2 L2A, summer 2023, bare pixels in a 1 km box)\n\n",
          f"Controls: n={len(ctrl)}, median {np.median(ctrl):.2f}, 90th pct {np.percentile(ctrl,90):.2f}. "
          f"No data: {[(b['name'], b['error']) for b in bad if b['group'] != 'control']}\n\n",
          "| site | group | B11/B12 | higher than % of controls | bare fraction | scene date |\n|---|---|---|---|---|---|\n"]
    for r in sorted(rows, key=lambda r: -r["ratio"]):
        if r["group"] != "control":
            md.append(f"| {r['name']} | {r['group']} | {r['ratio']:.2f} | {100*np.mean(ctrl < r['ratio']):.0f} | {r['bare_frac']:.0%} | {r['date']} |\n")
    (OUT / "salts.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
