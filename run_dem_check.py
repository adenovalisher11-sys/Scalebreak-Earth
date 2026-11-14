"""Method 8 - independent DEM check with JAXA ALOS World 3D 30 m (AW3D30).

NASADEM (radar, 2000) and AW3D30 (optical stereo, 2006-2011) have independent errors.
If both give the same slope at a baseline, the value is terrain; where they disagree,
it is sensor noise. Same block-average slope as the other methods, 16 km box.
Caveat: AW3D30 fills its own voids (water, featureless salt) with SRTM-based data, so on
Salar de Uyuni the two are not independent.
Run: .venv/bin/python run_dem_check.py    Out: results/dem_check.md
"""
import math, pathlib, time

import numpy as np
import rasterio
import requests
from rasterio.windows import from_bounds

from kzanalog import dem
from kzanalog.fingerprint import fingerprint

OUT = pathlib.Path(__file__).parent / "results"
SITES = {"Zhamanshin crater": (48.40, 60.967), "Soyuz zone (Zhezkazgan)": (47.35, 69.60),
         "Altyn-Emel (Aktau)": (44.03, 79.35), "Shunak crater": (47.208, 72.760),
         "Salar de Uyuni (flat reference)": (-20.20, -67.60)}
BASE = (120, 240, 480, 960)


def aw3d(lat, lon, half_km=8.0):
    r = requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search",
                      json={"collections": ["alos-dem"], "intersects": {"type": "Point", "coordinates": [lon, lat]}, "limit": 1}, timeout=60).json()
    href = r["features"][0]["assets"]["data"]["href"]
    while True:
        j = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/alos-dem", timeout=60).json()
        if "token" in j:
            break
        time.sleep(20)
    dlat = math.degrees(half_km * 1e3 / dem.R["earth"]); dlon = dlat / math.cos(math.radians(lat))
    with rasterio.open(f"{href}?{j['token']}") as ds:
        z = ds.read(1, window=from_bounds(lon - dlon, lat - dlat, lon + dlon, lat + dlat, ds.transform), boundless=True, fill_value=-9999).astype("float32")
        z[z <= -9999] = np.nan
        dy = math.radians(abs(ds.transform.e)) * dem.R["earth"]; dx = math.radians(ds.transform.a) * dem.R["earth"] * math.cos(math.radians(lat))
    return z, dx, dy


def main():
    md = ["# NASADEM (NASA) vs AW3D30 (JAXA): median slope in degrees by baseline, 16 km box\n\n",
          "| site | baseline m | NASADEM | AW3D30 | ratio | verdict |\n|---|---|---|---|---|---|\n"]
    for name, (lat, lon) in SITES.items():
        # AW3D30 is read from a single 1-degree tile, so slide the box to lie fully inside it
        # (both DEMs then cover exactly the same ground).
        dlat = math.degrees(8.5e3 / dem.R["earth"]); dlon = dlat / math.cos(math.radians(lat))
        lat = min(max(lat, math.floor(lat) + dlat), math.floor(lat) + 1 - dlat)
        lon = min(max(lon, math.floor(lon) + dlon), math.floor(lon) + 1 - dlon)
        a = fingerprint(*dem.window("earth", lat, lon, 8.0), baselines=BASE)
        try:
            b = fingerprint(*aw3d(lat, lon), baselines=BASE)
        except Exception as e:
            md.append(f"| {name} | - | - | failed: {repr(e)[:60]} | - | - |\n"); continue
        for L, sa, sb in zip(BASE, a["slope_deg"], b["slope_deg"]):
            ratio = sa / sb if sb else float("nan")
            md.append(f"| {name} | {L} | {sa:.3f} | {sb:.3f} | {ratio:.2f} | {'agree (terrain)' if 0.8 <= ratio <= 1.25 else 'disagree (noise-limited)'} |\n")
    (OUT / "dem_check.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
