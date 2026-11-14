"""Method 1b - published site-selection rules applied to every site.

The literature picks landing / base sites by slope thresholds, not by similarity
to an average site. Rules used (source paper numbers from the team's review):
  slope <= 5 deg  : Moon-base "ideal" (18, at a 560 m baseline), Mars landing (20)
  slope <  8 deg over > 30 % of the area : lunar research station, ILRS (31)
  slope <= 15 deg : Mars settlement / rover corridor (21, 6); > 15 deg unsuitable (18)
Validation pattern from papers 20 and 21: known good sites must pass. So the real
landing sites and the regions those papers selected are run through the same code.

Slope here = gradient magnitude after block-averaging the DEM to ~480 m cells.
Run:  .venv/bin/python run_criteria.py     Out: results/criteria.csv, results/criteria.md
"""
import csv
import pathlib
from concurrent.futures import ThreadPoolExecutor

import numpy as np

from kzanalog import dem, sites
from kzanalog.fingerprint import _block_mean

OUT = pathlib.Path(__file__).parent / "results"
L = 480.0

# Regions that the reviewed site-selection papers themselves ended up choosing.
SELECTED = {
    ("moon", "Pytheas cluster (base, paper 18)"): (16.4, -18.25),
    ("moon", "Gambart cluster (base, paper 18)"): (1.65, -14.15),
    ("moon", "Parry cluster (base, paper 18)"): (-8.7, -12.3),
    ("moon", "Nobile Rim 2 (Artemis III, paper 30)"): (-84.20, 60.70),
    ("mars", "Top settlement site (paper 21)"): (1.40, -7.4),
}


def slopes_deg(z, dx, dy):
    fx, fy = max(1, round(L / dx)), max(1, round(L / dy))
    m = _block_mean(z, fy, fx)
    gy, gx = np.gradient(m, fy * dy, fx * dx)
    s = np.degrees(np.arctan(np.hypot(gx, gy)))
    return s[np.isfinite(s)]


def compute(job):
    group, body, name, (lat, lon) = job
    try:
        s = slopes_deg(*dem.window(body, lat, lon, 16.0))
    except Exception as e:
        return dict(group=group, body=body, name=name, error=repr(e))
    return dict(group=group, body=body, name=name, median=float(np.median(s)), p95=float(np.percentile(s, 95)),
                f5=float(np.mean(s <= 5)), f8=float(np.mean(s < 8)), f15=float(np.mean(s <= 15)))


def main():
    OUT.mkdir(exist_ok=True)
    jobs = [("landing site", "mars", n, c) for n, c in sites.MARS.items()]
    jobs += [("landing site", "moon", n, c) for n, c in sites.MOON.items()]
    jobs += [("paper-selected", b, n, c) for (b, n), c in SELECTED.items()]
    for grp, d in (("kazakhstan", sites.KAZAKHSTAN), ("reference analog", sites.REFERENCE),
                   ("control", sites.random_controls())):
        jobs += [(grp, "earth", n, c) for n, c in d.items()]
    with ThreadPoolExecutor(8) as ex:
        rows = list(ex.map(compute, jobs))
    bad = [r for r in rows if "error" in r]
    rows = [r for r in rows if "error" not in r]
    for r in rows:
        r["ilrs_pass"] = r["f8"] > 0.30          # paper 31
        r["landing_grade"] = r["f5"] >= 0.90     # our strict reading: 90 % of cells <= 5 deg
    with open(OUT / "criteria.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)

    md = [f"# Published slope rules at a {L:g} m baseline\n\n"]
    for grp in ("landing site", "paper-selected", "kazakhstan", "reference analog", "control"):
        g = [r for r in rows if r["group"] == grp]
        md.append(f"**{grp}** (n={len(g)}): median share of area <=5 deg = {np.median([r['f5'] for r in g]):.0%}; "
                  f"pass ILRS rule (>30 % <8 deg): {sum(r['ilrs_pass'] for r in g)}/{len(g)}; "
                  f">=90 % of area <=5 deg: {sum(r['landing_grade'] for r in g)}/{len(g)}\n\n")
    md.append("| site | body | group | median slope | 95th pct | area <=5 deg | area <=15 deg |\n|---|---|---|---|---|---|---|\n")
    for r in rows:
        if r["group"] != "control":
            md.append(f"| {r['name']} | {r['body']} | {r['group']} | {r['median']:.2f} | {r['p95']:.1f} | "
                      f"{r['f5']:.0%} | {r['f15']:.0%} |\n")
    (OUT / "criteria.md").write_text("".join(md))
    print("".join(md))
    if bad:
        print("FAILED:", [(b["name"], b["error"]) for b in bad])


if __name__ == "__main__":
    main()
