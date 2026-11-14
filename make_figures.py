"""Figures and chart data for the HTML report (report/).

Uses only cached project data plus three small fetches: a Sentinel-2 true-colour chip of
Shunak crater, a NASA GIBS Blue Marble map of Kazakhstan, and the Mars window if missing.
Run after all run_*.py:  .venv/bin/python make_figures.py   Out: report/img/*, report/data.json
"""
import csv, io, json, math, pathlib, subprocess

import numpy as np
import requests
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LightSource
from PIL import Image
from scipy.ndimage import zoom

from kzanalog import dem, sites

ROOT = pathlib.Path(__file__).parent
RES, OUT = ROOT / "results", ROOT / "report"
IMG = OUT / "img"
IMG.mkdir(parents=True, exist_ok=True)


def shade(z, dx, dy, size=900, exag=3.0, cmap="cividis"):
    z = np.where(np.isfinite(z), z, np.nanmedian(z))
    ls = LightSource(azdeg=315, altdeg=35)
    rgb = ls.shade(z, cmap=plt.get_cmap(cmap), vert_exag=exag, dx=dx, dy=dy, blend_mode="soft")
    im = Image.fromarray((rgb[..., :3] * 255).astype("uint8"))
    return im.resize((size, round(size * z.shape[0] / z.shape[1])), Image.LANCZOS)


def to_res(z, dx, dy, res):
    """Block-average a DEM to a target pixel size (metres)."""
    fy, fx = max(1, round(res / dy)), max(1, round(res / dx))
    h, w = z.shape[0] // fy * fy, z.shape[1] // fx * fx
    return z[:h, :w].reshape(h // fy, fy, w // fx, fx).mean(axis=(1, 3)), dx * fx, dy * fy


def square(im):
    s = min(im.size); return im.crop(((im.width - s) // 2, (im.height - s) // 2, (im.width + s) // 2, (im.height + s) // 2))


# 1. Hero slider: Chiyli crater (Kazakhstan) vs Meridiani (Opportunity), both 32 km, both at 200 m
zk, dxk, dyk = dem.window("earth", *sites.KAZAKHSTAN["Chiyli crater"], 16)
zm, dxm, dym = dem.window("mars", *sites.MARS["Meridiani (Opportunity)"], 16)
zk2, dxk2, dyk2 = to_res(zk, dxk, dyk, 200)
square(shade(zk2, dxk2, dyk2, 1000, exag=8)).save(IMG / "hero_kz.jpg", quality=85)
square(shade(zm, dxm, dym, 1000, exag=8)).save(IMG / "hero_mars.jpg", quality=85)

# 2. Shunak: Sentinel-2 true colour vs NASADEM hillshade, same 6 km box
lat, lon = sites.KAZAKHSTAN["Shunak crater"]
zs, dxs, dys = dem.window("earth", lat, lon, 3.08)
square(shade(zs, dxs, dys, 1000, exag=4, cmap="gist_earth")).save(IMG / "shunak_dem.jpg", quality=85)
if not (IMG / "shunak_s2.jpg").exists():
    import rasterio
    from rasterio.warp import transform
    from rasterio.windows import Window
    it = requests.post("https://planetarycomputer.microsoft.com/api/stac/v1/search", json={
        "collections": ["sentinel-2-l2a"], "intersects": {"type": "Point", "coordinates": [lon, lat]},
        "datetime": "2023-06-01/2023-09-30", "query": {"eo:cloud_cover": {"lt": 1}}, "limit": 20}, timeout=90).json()["features"]
    it = sorted(it, key=lambda i: i["properties"]["eo:cloud_cover"])[0]
    tok = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/sentinel2l2a01/sentinel2-l2", timeout=60).json()["token"]
    with rasterio.open(f"{it['assets']['visual']['href']}?{tok}") as ds:
        x, y = transform("EPSG:4326", ds.crs, [lon], [lat]); r, c = ds.index(x[0], y[0])
        n = round(2 * 3080 / 10)
        a = ds.read(window=Window(c - n // 2, r - n // 2, n, n))
    Image.fromarray(np.moveaxis(a, 0, -1)).resize((1000, 1000), Image.LANCZOS).save(IMG / "shunak_s2.jpg", quality=85)

# 3. Crater pair: Shunak (2.8 km, Earth) vs Zunil (10.4 km, Mars), each framed at 2.2 D
zz, dxz, dyz = dem.window("mars", 7.7, 166.2, 11.44)
square(shade(zs, dxs, dys, 700, exag=6)).save(IMG / "crater_shunak.jpg", quality=85)
square(shade(zz, dxz, dyz, 700, exag=2)).save(IMG / "crater_zunil.jpg", quality=85)

# 4. 3D fly-around of Shunak (NASADEM), mp4
vid = OUT / "shunak_3d.mp4"
if not vid.exists():
    frames = IMG / "frames"; frames.mkdir(exist_ok=True)
    z = zs[::3, ::3]; z = np.where(np.isfinite(z), z, np.nanmedian(z))
    ny, nx = z.shape
    X, Y = np.meshgrid(np.arange(nx) * dxs * 3 / 1000, np.arange(ny) * dys * 3 / 1000)
    ls = LightSource(azdeg=315, altdeg=40)
    col = ls.shade(z, cmap=plt.get_cmap("gist_earth"), vert_exag=4, blend_mode="soft")
    for i in range(72):
        fig = plt.figure(figsize=(8, 4.5), dpi=120); ax = fig.add_subplot(projection="3d")
        ax.plot_surface(X, Y, (z - z.min()) / 1000, facecolors=col, rstride=1, cstride=1, linewidth=0, antialiased=False, shade=False)
        ax.set_box_aspect((1, 1, 0.16), zoom=1.75); ax.view_init(30, 225 + i * 5); ax.set_axis_off()
        fig.patch.set_facecolor("#fdfdfd"); fig.subplots_adjust(0, 0, 1, 1)
        fig.savefig(frames / f"f{i:03d}.png", facecolor="#fdfdfd"); plt.close(fig)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", "18", "-i", str(frames / "f%03d.png"),
                    "-vf", "crop=iw:ih*0.84:0:ih*0.08,scale=880:-2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-crf", "26", "-movflags", "+faststart", str(vid)], check=True)

# 5. Map background: NASA GIBS Blue Marble, equirectangular 40-56 N, 45-88 E
BBOX = (45, 40, 88, 56)
if not (IMG / "map_kz.jpg").exists():
    r = requests.get("https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi", params=dict(
        SERVICE="WMS", REQUEST="GetMap", VERSION="1.1.1", LAYERS="BlueMarble_ShadedRelief", SRS="EPSG:4326",
        BBOX=",".join(map(str, BBOX)), WIDTH=1376, HEIGHT=512, FORMAT="image/jpeg"), timeout=120)
    Image.open(io.BytesIO(r.content)).convert("RGB").save(IMG / "map_kz.jpg", quality=82)

# 6. Chart data
def rows(name):
    with open(RES / name) as fh:
        return list(csv.DictReader(fh))

land = rows("landing.csv")
data = {"bbox": BBOX}
data["landing"] = {g: sorted(round(float(r["med480"]), 3) for r in land if r["group"] == g and r["med480"] not in ("", "nan"))
                   for g in ("soyuz landing", "random Kazakhstan", "random arid world", "mars landing", "moon landing")}
ice = rows("icesat.csv")
data["icesat"] = {g: [dict(n=r["name"], m=round(float(r["med40"]), 3), p=round(float(r["p99_40"]), 2)) for r in ice if r["group"] == g]
                  for g in ("soyuz landing", "random Kazakhstan", "reference analog")}
th = rows("thermal.csv")
data["thermal"] = [dict(n=r["name"], g=r["group"], rng=round(float(r["annual_range"]), 1), alb=None if r["albedo"] in ("", "nan") else round(float(r["albedo"]), 3))
                   for r in th if r["annual_range"] not in ("", "nan")]
cache = ROOT / "data" / "cache_modis"
def prof(la, lo):
    f = cache / f"{la:+08.3f}_{lo:+09.3f}_2023.json"
    return json.loads(f.read_text()) if f.exists() else None
monthly = {}
for grp, pts in (("kazakhstan", [(float(r["lat"]), float(r["lon"])) for r in th if r["group"] == "kazakhstan"]),
                 ("control", [(float(r["lat"]), float(r["lon"])) for r in th if r["group"] == "control"])):
    ps = [p for p in (prof(*x) for x in pts) if p]
    td = np.array([p["tday"] for p in ps], float); tn = np.array([p["tnight"] for p in ps], float)
    monthly[grp] = dict(n=len(ps), day=[round(float(v), 1) for v in np.nanmedian(td, 0)], night=[round(float(v), 1) for v in np.nanmedian(tn, 0)])
data["monthly"] = monthly
data["sites"] = json.loads((RES / "site_data.json").read_text())["sites"]
data["soyuz"] = [[v["lat"], v["lon"]] for v in json.loads((ROOT / "data" / "soyuz_landings.json").read_text())["sites"].values()]
(OUT / "data.json").write_text(json.dumps(data, separators=(",", ":")))
print({k: (len(v) if hasattr(v, "__len__") else v) for k, v in data.items()}, monthly["kazakhstan"]["n"], monthly["control"]["n"])
