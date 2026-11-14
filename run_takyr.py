"""Method 6b - polygon patterns on takyrs and playas (ESA Sentinel-2, 10 m).

Takyr desiccation cracks are centimetres to metres (below the pixel), but salt and
desiccation polygons on playas reach 20-150 m (Dalangtan, Qaidam: 20-150 m, Mars crater
floors ~120 m; review paper 5). This test asks whether a surface has a repeating pattern
in that band. For each 2.56 km window of band B08 (NIR, 10 m): detrend, Hann window, 2-D
FFT, radially averaged power; fit a power law over 15-640 m wavelengths; periodicity =
max ratio of power to the fit inside 20-150 m, plus the wavelength of that peak.
Each site is scanned with a 3x3 grid of windows (offsets 3 km) and the strongest kept.
Positive control: Dalangtan playa (centre approximate). Negative: random arid points.
Run: .venv/bin/python run_takyr.py   Out: results/takyr.md, takyr.csv
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
CACHE = pathlib.Path(__file__).parent / "data" / "cache_takyr"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
TOKEN = "https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel2l2a01/sentinel2-l2"
_tok, _lock = [], threading.Lock()
N = 256
SITES = {
    ("kazakhstan", "Daryalyk takyr"): (45.417, 65.333),
    ("kazakhstan", "Aralkum (dry Aral bed)"): (45.0, 60.5),
    ("kazakhstan", "Betpak-Dala"): (46.033, 70.200),
    ("kazakhstan", "Lake Inder shore"): (48.45, 51.92),
    ("kazakhstan", "Kyzylkum (Kazakh part)"): (43.90, 66.40),
    ("kazakhstan", "Soyuz zone (Zhezkazgan)"): (47.35, 69.60),
        ("reference", "Makgadikgadi pans"): (-20.75, 25.50),
    ("reference", "White Sands, NM"): (32.779, -106.172),
}


def token():
    with _lock:
        while not _tok:
            j = requests.get(TOKEN, timeout=60).json()
            if "token" in j:
                _tok.append(j["token"])
            else:
                time.sleep(20)
    return _tok[0]


def spectrum_score(a):
    a = a - np.polyval(np.polyfit(np.arange(a.size), a.ravel(), 1), np.arange(a.size)).reshape(a.shape)
    a = a - a.mean()
    w = np.outer(np.hanning(N), np.hanning(N))
    P = np.abs(np.fft.fftshift(np.fft.fft2(a * w))) ** 2
    ky, kx = np.indices(P.shape) - N // 2
    k = np.hypot(kx, ky).astype(int)
    rad = np.bincount(k.ravel(), P.ravel()) / np.maximum(np.bincount(k.ravel()), 1)
    kk = np.arange(rad.size)
    lam = np.where(kk > 0, N * 10.0 / np.maximum(kk, 1), np.inf)  # metres
    fit = (lam >= 15) & (lam <= 640) & (rad > 0)
    c = np.polyfit(np.log(kk[fit]), np.log(rad[fit]), 1)
    ratio = rad / np.exp(np.polyval(c, np.log(np.maximum(kk, 1))))
    band = (lam >= 20) & (lam <= 150)
    i = np.where(band)[0][np.argmax(ratio[band])]
    return float(ratio[i]), float(lam[i])


def site(job):
    (grp, name), (lat, lon) = job
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{lat:+08.3f}_{lon:+09.3f}.json"
    if f.exists():
        return dict(group=grp, name=name, **json.loads(f.read_text()))
    months = "2023-06-01/2023-09-30" if lat >= 0 else "2023-06-01/2023-10-31"
    try:
        it = requests.post(STAC, json={"collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
                                       "datetime": months, "query": {"eo:cloud_cover": {"lt": 2}}, "limit": 10}, timeout=90).json()["features"]
        if not it:
            return dict(group=grp, name=name, error="no clear scene")
        it = sorted(it, key=lambda i: i["properties"]["eo:cloud_cover"])[0]
        best = (0, 0)
        with rasterio.open(f"{it['assets']['B08']['href']}?{token()}") as ds:
            x, y = transform("EPSG:4326", ds.crs, [lon], [lat])
            r0, c0 = ds.index(x[0], y[0])
            for dr in (-300, 0, 300):
                for dc in (-300, 0, 300):
                    a = ds.read(1, window=Window(c0 + dc - N // 2, r0 + dr - N // 2, N, N), boundless=True, fill_value=0).astype("float64")
                    if (a <= 0).mean() > 0.01:
                        continue
                    best = max(best, spectrum_score(a))
        out = dict(periodicity=best[0], wavelength_m=best[1], date=it["properties"]["datetime"][:10])
    except Exception as e:
        return dict(group=grp, name=name, error=repr(e)[:100])
    f.write_text(json.dumps(out))
    return dict(group=grp, name=name, **out)


def main():
    OUT.mkdir(exist_ok=True)
    jobs = list(SITES.items()) + [(("control", n), c) for n, c in sites.random_controls().items()]
    # Positive control: Dalangtan (DLT) area, 38.0-38.67 N, 91.17-92.17 E (Kong et al., PMC6205091).
    # The exact polygon field is not published, so a 5x5 grid over the area is scanned and every
    # grid point is reported; the method passes only if some of them stand out from the controls.
    jobs += [(("positive control", f"Dalangtan grid {la:.2f}N {lo:.2f}E"), (round(la, 3), round(lo, 3)))
             for la in np.linspace(38.05, 38.62, 5) for lo in np.linspace(91.25, 92.10, 5)]
    with ThreadPoolExecutor(6) as ex:
        rows = list(ex.map(site, jobs))
    bad = [r for r in rows if "error" in r or not r.get("periodicity")]
    rows = [r for r in rows if r not in bad]
    with open(OUT / "takyr.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["group", "name", "periodicity", "wavelength_m", "date"]); w.writeheader(); w.writerows(rows)
    ctrl = np.array([r["periodicity"] for r in rows if r["group"] == "control"])
    kz = np.array([r["periodicity"] for r in rows if r["group"] == "kazakhstan"])
    pos = np.array([r["periodicity"] for r in rows if r["group"] == "positive control"])
    u = mannwhitneyu(kz, ctrl, alternative="greater")
    md = ["# Polygon-scale pattern (20-150 m) in Sentinel-2 B08\n\n",
          f"Periodicity = peak power over the red-noise fit. Controls n={len(ctrl)}: median {np.median(ctrl):.2f}, "
          f"95th pct {np.percentile(ctrl,95):.2f}. Kazakhstan vs controls one-sided p = {u.pvalue:.2g}. "
          f"Positive control (Dalangtan grid, n={len(pos)}): max {pos.max():.2f}, {int((pos > np.percentile(ctrl,95)).sum())} grid points above the "
          f"controls' 95th percentile; Dalangtan vs controls one-sided p = {mannwhitneyu(pos, ctrl, alternative='greater').pvalue:.2g}. "
          f"No data: {[b['name'] for b in bad if b['group'] != 'control']}\n\n",
          "| site | group | periodicity | above % of controls | peak wavelength m | scene |\n|---|---|---|---|---|---|\n"]
    for r in sorted(rows, key=lambda r: -r["periodicity"]):
        if r["group"] != "control":
            md.append(f"| {r['name']} | {r['group']} | {r['periodicity']:.2f} | {100*np.mean(ctrl < r['periodicity']):.0f} | {r['wavelength_m']:.0f} | {r['date']} |\n")
    md.append("\nWhere it breaks: a 10 m pixel cannot see takyr cracks themselves (cm to m); only patterns of 20 m and more "
              "are testable. Dunes, field boundaries and drainage also make spectral peaks, so a peak is a candidate, not a detection.\n")
    (OUT / "takyr.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
