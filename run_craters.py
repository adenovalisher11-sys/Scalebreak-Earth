"""Method 4 - crater profiles with a gravity correction.

A crater's shape class depends on gravity: the simple-to-complex transition diameter
scales roughly as 1/g. So a Kazakh crater is compared with Moon / Mars craters of the
gravity-equivalent diameter D_eq = D_earth * g_earth / g_body, not the same diameter.
For every crater the same code builds an azimuthally averaged radial profile, finds the
rim (highest ring between 0.6 and 1.4 catalogue radii) and reports depth / diameter.
Self-check: if the detected rim is more than 30 % away from the catalogue radius the
crater is reported as "rim not detected" (for old craters that is itself a result).
Catalogue diameters are from memory except where noted; centres from Wikipedia.
Run: .venv/bin/python run_craters.py   Out: results/craters.md, craters.png, craters.csv
"""
import csv
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from kzanalog import dem

OUT = pathlib.Path(__file__).parent / "results"
G = {"earth": 9.81, "mars": 3.71, "moon": 1.62}
# name: (body, lat, lon_east, catalogue diameter km, group)
CRATERS = {
    "Zhamanshin (14 km rim)": ("earth", 48.40, 60.967, 14.0, "kazakhstan"),
    "Bigach": ("earth", 48.60, 82.00, 8.0, "kazakhstan"),
    "Chiyli": ("earth", 49.175, 57.835, 5.5, "kazakhstan"),
    "Shunak": ("earth", 47.208, 72.760, 2.8, "kazakhstan"),
    "Meteor Crater (fresh, Earth)": ("earth", 35.028, -111.023, 1.2, "earth fresh"),
    "Linne": ("moon", 27.7, 11.8, 2.2, "moon fresh"),
    "Diophantus": ("moon", 27.6, -34.3, 17.6, "moon fresh"),
    "Giordano Bruno": ("moon", 35.97, 102.89, 22.0, "moon fresh"),
    "Triesnecker": ("moon", 4.18, 3.6, 25.0, "moon fresh"),
    "Euler": ("moon", 23.3, -29.2, 27.0, "moon fresh"),
    "Kepler": ("moon", 8.1, -38.0, 29.5, "moon fresh"),
    "Lambert": ("moon", 25.8, -21.0, 30.0, "moon fresh"),
    "Timocharis": ("moon", 26.7, -13.1, 34.0, "moon fresh"),
    "Aristarchus": ("moon", 23.7, -47.4, 40.0, "moon fresh"),
    "Tycho": ("moon", -43.31, -11.36, 85.0, "moon fresh"),
    "Copernicus": ("moon", 9.62, -20.08, 93.0, "moon fresh"),
    "Zunil": ("mars", 7.7, 166.2, 10.4, "mars fresh"),
    "Tooting": ("mars", 23.2, -152.2, 27.2, "mars fresh"),
    "Mojave": ("mars", 7.5, -33.0, 58.0, "mars fresh"),
}


def _profile(z, dx, dy, cx, cy, R):
    yy, xx = np.indices(z.shape)
    r = np.hypot((xx - cx) * dx, (yy - cy) * dy)
    dr = max(dx, dy, R / 40)
    edges = np.arange(0, 2.2 * R, dr)
    idx = np.digitize(r.ravel(), edges) - 1
    zz = z.ravel()
    ok = np.isfinite(zz) & (idx < len(edges) - 1)
    order = np.argsort(idx[ok]); ii, vv = idx[ok][order], zz[ok][order]
    cuts = np.searchsorted(ii, np.arange(len(edges)))
    prof = np.array([np.median(vv[cuts[i]:cuts[i + 1]]) if cuts[i + 1] > cuts[i] else np.nan for i in range(len(edges) - 1)])
    return (edges[:-1] + edges[1:]) / 2, prof


def _measure_at(z, dx, dy, cx, cy, R):
    rc, prof = _profile(z, dx, dy, cx, cy, R)
    band = (rc > 0.6 * R) & (rc < 1.4 * R)
    i_rim = np.where(band)[0][np.nanargmax(prof[band])]
    r_rim, z_rim = rc[i_rim], prof[i_rim]
    floor = np.nanmin(prof[rc < 0.8 * r_rim])
    outside = np.nanmedian(prof[(rc > 1.7 * R) & (rc < 2.2 * R)])
    return rc, prof, r_rim, z_rim - floor, z_rim - outside, outside


def measure(name, body, lat, lon, d_km, group):
    """Catalogue centres are rounded (0.1 deg = several km), so the centre is searched on a
    grid of offsets up to 0.75 R and the offset giving the deepest rim-to-floor is kept.
    The same search is applied to every crater on every body."""
    R = d_km * 500.0
    z, dx, dy = dem.window(body, lat, lon, 3.0 * R / 1e3)
    k = max(1, int(min(z.shape) / 400))  # thin very large arrays for speed
    z, dx, dy = z[::k, ::k], dx * k, dy * k
    best = None
    for oy in np.arange(-0.75, 0.76, 0.15):
        for ox in np.arange(-0.75, 0.76, 0.15):
            cx, cy = z.shape[1] / 2 + ox * R / dx, z.shape[0] / 2 + oy * R / dy
            m = _measure_at(z, dx, dy, cx, cy, R)
            if best is None or m[3] > best[0][3]:
                best = (m, ox, oy)
    (rc, prof, r_rim, depth, rim_h, outside), ox, oy = best
    # a real rim stands above BOTH the floor and the surroundings and sits near the catalogue radius
    ok = abs(r_rim / R - 1) <= 0.30 and rim_h > 0 and depth > 0
    return dict(name=name, body=body, group=group, D_cat_km=d_km, D_rim_km=2 * r_rim / 1e3, depth_m=float(depth),
                rim_height_m=float(rim_h), d_over_D=float(depth / (2 * r_rim)), rim_detected=bool(ok),
                centre_shift_R=float(np.hypot(ox, oy)), px_per_D=float(d_km * 1e3 / max(dx, dy)),
                rc=rc / R, prof=(prof - outside) / (2 * R))


def main():
    OUT.mkdir(exist_ok=True)
    rows = [measure(n, *v) for n, v in CRATERS.items()]
    fresh = {b: [r for r in rows if r["body"] == b and "fresh" in r["group"] and r["rim_detected"]] for b in ("moon", "mars")}
    md = ["# Crater profiles with gravity correction\n\n",
          "| crater | body | D catalogue km | D rim detected km | depth m | rim height m | depth/D | rim detected | centre shift (R) | pixels per D |\n|---|---|---|---|---|---|---|---|---|---|\n"]
    for r in rows:
        md.append(f"| {r['name']} | {r['body']} | {r['D_cat_km']:g} | {r['D_rim_km']:.1f} | {r['depth_m']:.0f} | {r['rim_height_m']:.0f} | "
                  f"{r['d_over_D']:.3f} | {'yes' if r['rim_detected'] else 'NO'} | {r['centre_shift_R']:.2f} | {r['px_per_D']:.0f} |\n")
    md.append("\n## Kazakh craters vs fresh craters of gravity-equivalent size\n\n"
              "| Kazakh crater | depth/D | body | equivalent D km | nearest fresh crater measured | its depth/D | preserved fraction |\n|---|---|---|---|---|---|---|\n")
    for r in rows:
        if r["group"] != "kazakhstan":
            continue
        for b in ("moon", "mars"):
            deq = r["D_cat_km"] * G["earth"] / G[b]
            c = min(fresh[b], key=lambda f: abs(np.log(f["D_cat_km"] / deq)))
            md.append(f"| {r['name']} | {r['d_over_D']:.3f}{'' if r['rim_detected'] else ' (rim not detected)'} | {b} | {deq:.0f} | "
                      f"{c['name']} ({c['D_cat_km']:g} km) | {c['d_over_D']:.3f} | {r['d_over_D']/c['d_over_D']:.0%} |\n")
    (OUT / "craters.md").write_text("".join(md)); print("".join(md))
    with open(OUT / "craters.csv", "w", newline="") as fh:
        keys = [k for k in rows[0] if k not in ("rc", "prof")]
        w = csv.DictWriter(fh, fieldnames=keys); w.writeheader(); w.writerows([{k: r[k] for k in keys} for r in rows])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
    for ax, grp_ref, title in ((axes[0], "moon fresh", "vs fresh lunar craters (LOLA)"), (axes[1], "mars fresh", "vs fresh Martian craters (HRSC+MOLA)")):
        for r in rows:
            if r["group"] == grp_ref:
                ax.plot(r["rc"], r["prof"], color="0.6", lw=1)
            if r["group"] == "kazakhstan":
                ax.plot(r["rc"], r["prof"], lw=2, label=r["name"])
            if r["group"] == "earth fresh":
                ax.plot(r["rc"], r["prof"], "k--", lw=1.2, label=r["name"])
        ax.plot([], [], color="0.6", label=grp_ref)
        ax.set_xlabel("radius / catalogue radius"); ax.set_title(title, fontsize=10); ax.grid(alpha=.3); ax.axvline(1, color="r", lw=.6, ls=":")
    axes[0].set_ylabel("(elevation - surroundings) / diameter"); axes[0].legend(fontsize=7)
    fig.suptitle("Radial crater profiles, normalised by diameter (NASADEM, LOLA, HRSC+MOLA)")
    fig.tight_layout(); fig.savefig(OUT / "craters.png", dpi=150)


if __name__ == "__main__":
    main()
