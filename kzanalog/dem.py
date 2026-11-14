"""Read a square elevation window around a point on Earth, Mars or the Moon.

Data (all open, read by HTTP range requests, nothing downloaded whole):
  Earth: NASADEM 1 arc-second (NASA/JPL, SRTM reprocessing), COG mirror on
         Microsoft Planetary Computer. Covers 56S-60N.
  Mars : HRSC+MOLA blended DEM 200 m v2 (NASA MGS MOLA + ESA Mars Express HRSC), USGS.
  Moon : LRO LOLA global LDEM 118 m (NASA), USGS.
Returns (z_metres with NaN for no-data, dx_m, dy_m) where dx/dy are the true
ground size of one pixel at the site latitude.
"""
import math
import os
import time
import pathlib

import numpy as np
import rasterio
import requests
from rasterio.enums import Resampling
from rasterio.windows import Window

CACHE = pathlib.Path(__file__).resolve().parent.parent / "data" / "cache"
_USGS = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/"
MARS_URL = _USGS + "Mars/HRSC_MOLA_Blend/Mars_HRSC_MOLA_BlendDEM_Global_200mp_v2.tif"
MOON_URL = _USGS + "Lunar_LRO_LOLA_Global_LDEM_118m_Mar2014.tif"
R = {"earth": 6371008.8, "mars": 3396190.0, "moon": 1737400.0}
_ENV = dict(GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR", GTIFF_DIRECT_IO="YES",
            GDAL_HTTP_MAX_RETRY="4", GDAL_HTTP_RETRY_DELAY="2",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif")
_token = None


def _nasadem_token():
    global _token
    if _token is None:
        r = requests.get("https://planetarycomputer.microsoft.com/api/sas/v1/token/nasadem", timeout=30)
        r.raise_for_status()
        _token = r.json()["token"]
    return _token


def _read(url, col0, row0, w, h, step=1):
    """Read a window; step > 1 takes every step-th pixel (nearest) to keep big windows small."""
    last = None
    for attempt in range(4):
        try:
            with rasterio.Env(**_ENV), rasterio.open(url) as ds:
                fill = ds.nodata if ds.nodata is not None else -32768
                z = ds.read(1, window=Window(col0, row0, w, h), boundless=True, fill_value=fill,
                            out_shape=(max(1, h // step), max(1, w // step)),
                            resampling=Resampling.nearest).astype("float32")
                if ds.nodata is not None:
                    z[z == ds.nodata] = np.nan
                return z * (ds.scales[0] or 1.0) + (ds.offsets[0] or 0.0)
        except Exception as e:  # transient network errors on long range-request series
            last = e
            time.sleep(3 * (attempt + 1))
    raise last


def _earth(lat, lon, half_m):
    dlat = math.degrees(half_m / R["earth"])
    dlon = dlat / math.cos(math.radians(lat))
    px = 1 / 3600
    lat0, lat1, lon0, lon1 = lat - dlat, lat + dlat, lon - dlon, lon + dlon
    nrow, ncol = round((lat1 - lat0) / px), round((lon1 - lon0) / px)
    out = np.full((nrow, ncol), np.nan, "float32")
    for tlat in range(math.floor(lat0), math.floor(lat1) + 1):
        for tlon in range(math.floor(lon0), math.floor(lon1) + 1):
            name = f"{'n' if tlat >= 0 else 's'}{abs(tlat):02d}{'e' if tlon >= 0 else 'w'}{abs(tlon):03d}"
            url = (f"https://nasademeuwest.blob.core.windows.net/nasadem-cog/v001/"
                   f"NASADEM_HGT_{name}.tif?{_nasadem_token()}")
            # tile pixel (r, c) centre = (tlat + 1 - r*px, tlon + c*px)
            r0 = max(0, round((tlat + 1 - lat1) / px)); r1 = min(3601, round((tlat + 1 - lat0) / px))
            c0 = max(0, round((lon0 - tlon) / px)); c1 = min(3601, round((lon1 - tlon) / px))
            if r1 <= r0 or c1 <= c0:
                continue
            try:
                z = _read(url, c0, r0, c1 - c0, r1 - r0)
            except Exception:
                continue  # tile absent (ocean / outside coverage)
            orow = round((lat1 - (tlat + 1 - r0 * px)) / px); ocol = round(((tlon + c0 * px) - lon0) / px)
            hh = min(z.shape[0], nrow - orow); ww = min(z.shape[1], ncol - ocol)
            if hh > 0 and ww > 0:
                out[orow:orow + hh, ocol:ocol + ww] = z[:hh, :ww]
    dy = math.radians(px) * R["earth"]
    return out, dy * math.cos(math.radians(lat)), dy


def _planet(body, lat, lon, half_m):
    url = MARS_URL if body == "mars" else MOON_URL
    with rasterio.Env(**_ENV), rasterio.open(url) as ds:
        t, W, H = ds.transform, ds.width, ds.height
        geographic = ds.crs.is_geographic
    if geographic:  # degrees
        deg = math.degrees(half_m / R[body])
        x, y = lon, lat
        hx, hy = deg / math.cos(math.radians(lat)), deg
        dy = math.radians(abs(t.e)) * R[body]
    else:  # equirectangular metres, lat_ts = 0
        x, y = math.radians(lon) * R[body], math.radians(lat) * R[body]
        hx, hy = half_m / math.cos(math.radians(lat)), half_m
        dy = abs(t.e)
    col0 = round((x - hx - t.c) / t.a); col1 = round((x + hx - t.c) / t.a)
    row0 = round((t.f - (y + hy)) / abs(t.e)); row1 = round((t.f - (y - hy)) / abs(t.e))
    col0, col1, row0, row1 = max(0, col0), min(W, col1), max(0, row0), min(H, row1)
    step = max(1, math.ceil((row1 - row0) / 500))  # cap at ~500 rows; large craters do not need full resolution
    z = _read(url, col0, row0, col1 - col0, row1 - row0, step)
    return z, dy * math.cos(math.radians(lat)) * step, dy * step


def window(body, lat, lon, half_km=16.0):
    """Elevation window of +-half_km around (lat, lon). Cached on disk."""
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"{body}_{lat:+08.3f}_{lon:+09.3f}_{half_km:g}.npz"
    if f.exists():
        d = np.load(f)
        return d["z"], float(d["dx"]), float(d["dy"])
    z, dx, dy = (_earth(lat, lon, half_km * 1e3) if body == "earth"
                 else _planet(body, lat, lon, half_km * 1e3))
    tmp = f.with_suffix(f".{os.getpid()}.tmp.npz")
    np.savez_compressed(tmp, z=z, dx=dx, dy=dy)
    tmp.replace(f)
    return z, dx, dy
