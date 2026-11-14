"""Terrain fingerprint: how slope and roughness change with measurement baseline.

For each baseline L the DEM is block-averaged to cells of ~L metres, then:
  slope_deg(L) = median absolute slope between neighbouring cells (degrees)
  rough_m(L)   = median |z_b - (z_a + z_c)/2|  (metres; tilt removed, so a uniformly
                 sloping plain scores 0 - this is the detrended roughness)
  hurst        = log-log slope of RMS height difference vs L (0.5 = random walk,
                 ~1 = smooth self-affine terrain)
All are in physical units, so the same code is valid on Earth, Mars and the Moon.
"""
import warnings

import numpy as np

BASELINES_M = (240, 480, 960, 1920)


def _block_mean(z, fy, fx):
    h, w = (z.shape[0] // fy) * fy, (z.shape[1] // fx) * fx
    if h == 0 or w == 0:
        return np.empty((0, 0))
    b = z[:h, :w].reshape(h // fy, fy, w // fx, fx)
    ok = np.isfinite(b).mean(axis=(1, 3))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        m = np.nanmean(b, axis=(1, 3))
    m[ok < 0.5] = np.nan
    return m


def fingerprint(z, dx, dy, baselines=BASELINES_M):
    """Return dict with per-baseline arrays; baselines finer than 2 px are skipped (NaN)."""
    out = {"L": [], "slope_deg": [], "rough_m": [], "rms_dz": []}
    for L in baselines:
        fx, fy = max(1, round(L / dx)), max(1, round(L / dy))
        # require the native pixel to be no coarser than the baseline
        if dx > 1.25 * L or dy > 1.25 * L:
            for k in out: out[k].append(np.nan if k != "L" else L)
            continue
        m = _block_mean(z, fy, fx)
        if m.shape[0] < 6 or m.shape[1] < 6:
            for k in out: out[k].append(np.nan if k != "L" else L)
            continue
        lx, ly = fx * dx, fy * dy
        gx = np.diff(m, axis=1) / lx
        gy = np.diff(m, axis=0) / ly
        g = np.concatenate([gx[np.isfinite(gx)], gy[np.isfinite(gy)]])
        cx = m[:, 1:-1] - 0.5 * (m[:, :-2] + m[:, 2:])
        cy = m[1:-1, :] - 0.5 * (m[:-2, :] + m[2:, :])
        c = np.concatenate([cx[np.isfinite(cx)], cy[np.isfinite(cy)]])
        d = np.concatenate([(gx * lx)[np.isfinite(gx)], (gy * ly)[np.isfinite(gy)]])
        if g.size < 30:
            for k in out: out[k].append(np.nan if k != "L" else L)
            continue
        out["L"].append(L)
        out["slope_deg"].append(float(np.degrees(np.arctan(np.median(np.abs(g))))))
        out["rough_m"].append(float(np.median(np.abs(c))))
        out["rms_dz"].append(float(np.sqrt(np.mean(d ** 2))))
    Ls, r = np.array(out["L"], float), np.array(out["rms_dz"], float)
    ok = np.isfinite(r) & (r > 0)
    out["hurst"] = float(np.polyfit(np.log(Ls[ok]), np.log(r[ok]), 1)[0]) if ok.sum() >= 3 else float("nan")
    out["valid_frac"] = float(np.isfinite(z).mean())
    return out


def log_distance(a, b):
    """Mean |ln(a/b)| over baselines where both curves exist. 0 = identical; 0.69 = factor 2."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    ok = np.isfinite(a) & np.isfinite(b) & (a > 0) & (b > 0)
    return float(np.mean(np.abs(np.log(a[ok] / b[ok])))) if ok.any() else float("nan")
