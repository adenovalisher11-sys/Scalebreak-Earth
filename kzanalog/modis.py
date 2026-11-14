"""Point samples of NASA MODIS land products (Collection 6.1), read as COGs from the
Microsoft Planetary Computer mirror (no login). Products:
  MYD11A2  8-day land-surface temperature, 1 km, Aqua (~13:30 day / ~01:30 night)
  MCD43A4  daily nadir BRDF-adjusted reflectance, 500 m (-> approximate shortwave albedo)
  MOD13A1 / MYD13A1  16-day NDVI, 500 m
Each sample is the median of a 3x3 pixel window at the site.
"""
import json
import pathlib
import time

import numpy as np
import rasterio
import requests
from rasterio.warp import transform
from rasterio.windows import Window

CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "cache_modis"
STAC = "https://planetarycomputer.microsoft.com/api/stac/v1/search"
_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2")
_tokens = {}


def _token(collection):
    collection = "modis"  # all MODIS 6.1 COGs live in one storage container
    if collection not in _tokens:
        r = requests.get(f"https://planetarycomputer.microsoft.com/api/sas/v1/token/modiseuwest/modis-061-cogs", timeout=30)
        r.raise_for_status()
        _tokens[collection] = r.json()["token"]
    return _tokens[collection]


def _tile(lat, lon):
    """MODIS sinusoidal tile (h, v) that contains the point (R = 6371007.181 m, 10x10 deg tiles)."""
    import math
    R, T = 6371007.181, 1111950.5197665233
    x = R * math.radians(lon) * math.cos(math.radians(lat)); y = R * math.radians(lat)
    return int((x + 18 * T) // T), int((9 * T - y) // T)


def _search(collection, lat, lon, datetime, platform=None):
    # Query by tile number, not by geometry: the catalogue's tile footprints are loose near
    # tile edges and can return only the wrong neighbouring tile.
    h, v = _tile(lat, lon)
    q = {"modis:horizontal-tile": {"eq": h}, "modis:vertical-tile": {"eq": v}}
    if platform:
        q["platform"] = {"eq": platform}
    body = {"collections": [collection], "datetime": datetime, "query": q, "limit": 250}
    for attempt in range(4):
        r = requests.post(STAC, json=body, timeout=60)
        if r.ok:
            return sorted(r.json()["features"], key=lambda f: f["properties"]["start_datetime"])
        time.sleep(5 * (attempt + 1))
    r.raise_for_status()


def _sample(href, collection, lat, lon, fill, scale):
    with rasterio.Env(**_ENV), rasterio.open(f"{href}?{_token(collection)}") as ds:
        x, y = transform("EPSG:4326", ds.crs, [lon], [lat])
        row, col = ds.index(x[0], y[0])
        if not (1 <= row < ds.height - 1 and 1 <= col < ds.width - 1):
            return float("nan")  # point lies in a neighbouring tile
        a = ds.read(1, window=Window(col - 1, row - 1, 3, 3), boundless=True, fill_value=fill).astype("float64")
    a[np.isin(a, fill)] = np.nan
    a = a[np.isfinite(a)]
    return float(np.median(a) * scale) if a.size else float("nan")


def year_profile(lat, lon, year=2023):
    """Monthly day/night LST (K), dry-month albedo and yearly max NDVI for one point."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{lat:+08.3f}_{lon:+09.3f}_{year}.json"
    if f.exists():
        return json.loads(f.read_text())
    items = _search("modis-11A2-061", lat, lon, f"{year}-01-01/{year}-12-31", "aqua")
    day, night = [[] for _ in range(12)], [[] for _ in range(12)]
    # composites grouped by month, closest to the 12th first; several MODIS tiles can be
    # returned for a point near a tile edge, so try each until the point is inside one
    by_month = {}
    for it in items:
        d = it["properties"]["start_datetime"]
        by_month.setdefault(int(d[5:7]) - 1, []).append(it)
    for m, its in by_month.items():
        for it in sorted(its, key=lambda i: abs(int(i["properties"]["start_datetime"][8:10]) - 12)):
            vd = _sample(it["assets"]["LST_Day_1km"]["href"], "modis-11A2-061", lat, lon, 0, 0.02)
            vn = _sample(it["assets"]["LST_Night_1km"]["href"], "modis-11A2-061", lat, lon, 0, 0.02)
            if np.isfinite(vd) or np.isfinite(vn):
                day[m].append(vd); night[m].append(vn)
                break
    tday = [float(np.nanmean(v)) if v else float("nan") for v in day]
    tnight = [float(np.nanmean(v)) if v else float("nan") for v in night]
    warm = int(np.nanargmax(tday)) if np.isfinite(tday).any() else 6
    # MCD43A3 is not on the mirror, so shortwave albedo is approximated from MCD43A4
    # nadir BRDF-adjusted reflectance with the Liang (2001) MODIS narrow-to-broadband
    # weights. NBAR is not true albedo: treat as approximate (a few 0.01).
    w = {1: 0.160, 2: 0.291, 3: 0.243, 4: 0.116, 5: 0.112, 7: 0.081}
    alb = float("nan")
    for it in _search("modis-43A4-061", lat, lon, f"{year}-{warm+1:02d}-10/{year}-{warm+1:02d}-20")[:12]:
        b = {k: _sample(it["assets"][f"Nadir_Reflectance_Band{k}"]["href"], "modis", lat, lon, 32767, 1e-4) for k in w}
        if all(np.isfinite(v) for v in b.values()):
            alb = float(sum(w[k] * b[k] for k in w) - 0.0015)
            break
    ndvi = []
    for it in _search("modis-13A1-061", lat, lon, f"{year}-01-01/{year}-12-31")[::8]:
        ndvi.append(_sample(it["assets"]["500m_16_days_NDVI"]["href"], "modis-13A1-061", lat, lon, -3000, 1e-4))
    out = dict(tday=tday, tnight=tnight, warm_month=warm + 1, albedo=alb,
               ndvi_max=float(np.nanmax(ndvi)) if np.isfinite(ndvi).any() else float("nan"))
    f.write_text(json.dumps(out))
    return out


def ndvi_max(lat, lon, year=2023):
    """Yearly maximum NDVI (MOD13A1, one composite every ~2 months). Cached."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"ndvi_{lat:+08.3f}_{lon:+09.3f}_{year}.json"
    if f.exists():
        return json.loads(f.read_text())["ndvi_max"]
    v = [_sample(it["assets"]["500m_16_days_NDVI"]["href"], "modis", lat, lon, -3000, 1e-4)
         for it in _search("modis-13A1-061", lat, lon, f"{year}-01-01/{year}-12-31")[::4]]
    m = float(np.nanmax(v)) if np.isfinite(v).any() else float("nan")
    f.write_text(json.dumps({"ndvi_max": m}))
    return m
