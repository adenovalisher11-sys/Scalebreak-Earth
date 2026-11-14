"""Method 3 - landing test.

Question: is the ground where 95 crewed Soyuz capsules actually landed different from
random Kazakh steppe, and does it meet the slope rule used for Mars / Moon landing?
Landing points: data/soyuz_landings.json (spacefacts.de mission pages; 8 cross-checked
against Wikipedia agree within a few km).
Slope = gradient magnitude after block-averaging NASADEM to 120 m and to 480 m cells,
inside a 6 km box around each point.
Run: .venv/bin/python run_landing.py   Out: results/landing.md, landing.png, landing.csv
"""
import csv, json, pathlib, random
from concurrent.futures import ThreadPoolExecutor

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import mannwhitneyu

from kzanalog import dem, sites
from kzanalog.fingerprint import _block_mean

OUT = pathlib.Path(__file__).parent / "results"
HALF_KM = 3.0


def slope_stats(body, lat, lon, half_km=HALF_KM):
    z, dx, dy = dem.window(body, lat, lon, half_km)
    if np.isfinite(z).mean() < 0.9:
        return None
    out = {}
    for L in (120, 480):
        if max(dx, dy) > 1.25 * L:
            out[f"med{L}"] = out[f"p95_{L}"] = out[f"f5_{L}"] = float("nan"); continue
        m = _block_mean(z, max(1, round(L / dy)), max(1, round(L / dx)))
        gy, gx = np.gradient(m, max(1, round(L / dy)) * dy, max(1, round(L / dx)) * dx)
        s = np.degrees(np.arctan(np.hypot(gx, gy))); s = s[np.isfinite(s)]
        out[f"med{L}"], out[f"p95_{L}"], out[f"f5_{L}"] = float(np.median(s)), float(np.percentile(s, 95)), float(np.mean(s <= 5))
    out["relief"] = float(np.nanmax(z) - np.nanmin(z))
    return out


def job(j):
    grp, body, name, lat, lon = j
    try:
        s = slope_stats(body, lat, lon)
    except Exception as e:
        return None
    return None if s is None else dict(group=grp, name=name, lat=lat, lon=lon, **s)


def main():
    OUT.mkdir(exist_ok=True)
    land = json.loads((pathlib.Path(__file__).parent / "data" / "soyuz_landings.json").read_text())["sites"]
    rng = random.Random(7)
    jobs = [("soyuz landing", "earth", k, v["lat"], v["lon"]) for k, v in land.items()]
    # random Kazakhstan: box 44-52N, 50-80E (mostly steppe and desert; mountains in the SE corner excluded by lon/lat cut)
    jobs += [("random Kazakhstan", "earth", f"kz{i}", rng.uniform(44.5, 52), rng.uniform(50.5, 78)) for i in range(250)]
    jobs += [("random arid world", "earth", n, la, lo) for n, (la, lo) in sites.random_controls(n_per_box=12, seed=11).items()]
    jobs += [("mars landing", "mars", n, la, lo) for n, (la, lo) in sites.MARS.items()]
    jobs += [("moon landing", "moon", n, la, lo) for n, (la, lo) in sites.MOON.items()]
    with ThreadPoolExecutor(12) as ex:
        rows = [r for r in ex.map(job, jobs) if r]
    # drop flat-filled water (zero relief) from the random samples
    rows = [r for r in rows if r["relief"] > 1 or r["group"].endswith("landing")]
    with open(OUT / "landing.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    g = lambda grp, k: np.array([r[k] for r in rows if r["group"] == grp and np.isfinite(r[k])])
    md = ["# Landing test\n\n| group | n | median slope @120 m | median slope @480 m | 95th pct @480 m | sites with >=90 % area <=5 deg @480 m |\n|---|---|---|---|---|---|\n"]
    for grp in ("soyuz landing", "random Kazakhstan", "random arid world", "mars landing", "moon landing"):
        n = len(g(grp, "med480")); m120 = g(grp, "med120")
        md.append(f"| {grp} | {n} | {np.median(m120):.2f} | {np.median(g(grp,'med480')):.2f} | {np.median(g(grp,'p95_480')):.2f} | "
                  f"{int((g(grp,'f5_480') >= 0.9).sum())}/{n} |\n" if m120.size else
                  f"| {grp} | {n} | not resolved | {np.median(g(grp,'med480')):.2f} | {np.median(g(grp,'p95_480')):.2f} | {int((g(grp,'f5_480') >= 0.9).sum())}/{n} |\n")
    for other in ("random Kazakhstan", "random arid world"):
        for k in ("med120", "med480"):
            u = mannwhitneyu(g("soyuz landing", k), g(other, k), alternative="less")
            md.append(f"\nSoyuz points flatter than {other} ({k}): one-sided p = {u.pvalue:.2g}")
    for other in ("mars landing", "moon landing"):
        u = mannwhitneyu(g("soyuz landing", "med480"), g(other, "med480"), alternative="less")
        md.append(f"\nSoyuz points flatter than {other} (med480): one-sided p = {u.pvalue:.2g}")
    md.append(f"\n\nSteepest Soyuz landing box: median {g('soyuz landing','med480').max():.2f} deg @480 m. "
              f"Worst 95th percentile: {g('soyuz landing','p95_480').max():.2f} deg.\n")
    (OUT / "landing.md").write_text("".join(md)); print("".join(md))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    groups = ["soyuz landing", "random Kazakhstan", "random arid world", "mars landing", "moon landing"]
    ax.boxplot([g(x, "med480") for x in groups], tick_labels=[x.replace(" ", "\n") for x in groups], showfliers=True)
    ax.set_yscale("log"); ax.axhline(5, color="r", ls="--", lw=1); ax.text(0.55, 5.3, "5 deg landing rule", color="r", fontsize=8)
    ax.set_ylabel("median slope at 480 m baseline (deg)")
    ax.set_title("Where spacecraft actually landed: Kazakh steppe vs Mars and Moon")
    ax.grid(alpha=.3, axis="y"); fig.tight_layout(); fig.savefig(OUT / "landing.png", dpi=150)


if __name__ == "__main__":
    main()
