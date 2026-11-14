"""Method 3b - fine-scale landing test with NASA ICESat-2 laser altimetry (ATL06).

NASADEM is noise-limited below ~480 m on flat ground (see run_dem_check.py). ICESat-2
ATL06 gives land-ice/land heights every 20 m along track with ~cm-dm precision, so it
reaches 40-200 m baselines. No login: granule dates and reference-ground-track numbers
come from NASA CMR, the points from NASA OpenAltimetry (openaltimetry.earthdatacloud.nasa.gov).
Per box: all strong-beam points within +-0.15 deg; slope over baseline L = |dz| / L between
points L apart along the same beam; reports median and 99th percentile slope and the share
of baselines above 5 deg (landing rule) and above 15 deg.
Run: .venv/bin/python run_icesat.py   Out: results/icesat.md, icesat.csv
"""
import csv, json, math, pathlib, random, re, time
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import requests
from scipy.stats import mannwhitneyu

OUT = pathlib.Path(__file__).parent / "results"
CACHE = pathlib.Path(__file__).parent / "data" / "cache_icesat"
OA = "https://openaltimetry.earthdatacloud.nasa.gov/data/api/icesat2/atl06"
CMR = "https://cmr.earthdata.nasa.gov/search/granules.json"
H = 0.15
BASE = (40, 100, 200)


def granules(lat, lon, n=4):
    r = requests.get(CMR, params=dict(short_name="ATL06", bounding_box=f"{lon-H},{lat-H},{lon+H},{lat+H}",
                                      temporal="2019-05-01T00:00:00Z,2023-09-30T00:00:00Z", page_size=60), timeout=60).json()
    out = []
    for e in r["feed"]["entry"]:
        m = re.match(r"ATL06_(\d{8})\d{6}_(\d{4})\d{4}_", e["title"])
        mon = int(m.group(1)[4:6])
        if m and 5 <= mon <= 9:  # snow-free months
            out.append((f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}", int(m.group(2))))
    return list(dict.fromkeys(out))[:n]


def points(lat, lon, date, track):
    f = CACHE / f"{lat:+.3f}_{lon:+.3f}_{date}_{track}.json"
    if f.exists():
        return json.loads(f.read_text())
    for attempt in range(4):
        try:
            r = requests.get(OA, params=dict(date=date, minx=lon - H, miny=lat - H, maxx=lon + H, maxy=lat + H, trackId=track,
                                             outputFormat="json"), timeout=90)
            if r.ok:
                ser = [dict(beam=s["beam"], strong=s["isStrongBeam"], p=s["lat_lon_elev"]) for s in r.json().get("series", [])]
                CACHE.mkdir(parents=True, exist_ok=True); f.write_text(json.dumps(ser))
                return ser
        except Exception:
            pass
        time.sleep(5 * (attempt + 1))
    return []


def box(job):
    grp, name, lat, lon = job
    try:
        slopes = {L: [] for L in BASE}
        n = 0
        for date, track in granules(lat, lon):
            for s in points(lat, lon, date, track):
                if not s["strong"] or len(s["p"]) < 20:
                    continue
                p = np.array(s["p"], float)
                d = np.cumsum(np.r_[0, np.hypot(np.diff(p[:, 0]) * 111320, np.diff(p[:, 1]) * 111320 * math.cos(math.radians(lat)))])
                z = p[:, 2]
                n += len(p)
                for L in BASE:
                    j = np.searchsorted(d, d + L)
                    ok = j < len(d)
                    gap = d[j[ok]] - d[ok]
                    good = np.abs(gap - L) < 0.25 * L  # no data gaps
                    dz = np.abs(z[j[ok]][good] - z[ok][good])
                    slopes[L] += list(np.degrees(np.arctan(dz / gap[good])))
        if n < 200:
            return dict(group=grp, name=name, error=f"only {n} points")
        row = dict(group=grp, name=name, lat=lat, lon=lon, n_points=n)
        for L in BASE:
            s = np.array(slopes[L])
            row[f"med{L}"], row[f"p99_{L}"] = float(np.median(s)), float(np.percentile(s, 99))
            row[f"gt5_{L}"], row[f"gt15_{L}"] = float(np.mean(s > 5)), float(np.mean(s > 15))
        return row
    except Exception as e:
        return dict(group=grp, name=name, error=repr(e)[:100])


def main():
    OUT.mkdir(exist_ok=True)
    land = json.loads((pathlib.Path(__file__).parent / "data" / "soyuz_landings.json").read_text())["sites"]
    pts = sorted(land.items())
    rng = random.Random(5)
    jobs = [("soyuz landing", k, v["lat"], v["lon"]) for k, v in rng.sample(pts, 25)]
    jobs += [("random Kazakhstan", f"kz{i}", rng.uniform(44.5, 52), rng.uniform(50.5, 78)) for i in range(25)]
    jobs += [("reference analog", n, la, lo) for n, (la, lo) in {"Meteor Crater, AZ": (35.028, -111.023), "Black Point, AZ": (35.688, -111.360),
             "White Sands, NM": (32.779, -106.172), "MDRS Hanksville, UT": (38.406, -110.792), "Mojave (Pisgah)": (34.746, -116.375)}.items()]
    with ThreadPoolExecutor(4) as ex:
        rows = list(ex.map(box, jobs))
    bad = [r for r in rows if "error" in r]; rows = [r for r in rows if "error" not in r]
    with open(OUT / "icesat.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    g = lambda grp, k: np.array([r[k] for r in rows if r["group"] == grp])
    md = ["# Fine-scale slopes from ICESat-2 ATL06 (NASA), snow-free months 2019-2023\n\n",
          f"Boxes +-{H} deg. Failed or too few points: {len(bad)} ({sorted(set(b['error'][:20] for b in bad))})\n\n",
          "| group | boxes | median slope @40 m | 99th pct @40 m | share of 40 m baselines > 5 deg | median @200 m |\n|---|---|---|---|---|---|\n"]
    for grp in ("soyuz landing", "random Kazakhstan", "reference analog"):
        if len(g(grp, "med40")):
            md.append(f"| {grp} | {len(g(grp,'med40'))} | {np.median(g(grp,'med40')):.2f} | {np.median(g(grp,'p99_40')):.2f} | "
                      f"{np.median(g(grp,'gt5_40')):.2%} | {np.median(g(grp,'med200')):.2f} |\n")
    for k in ("med40", "p99_40"):
        u = mannwhitneyu(g("soyuz landing", k), g("random Kazakhstan", k), alternative="less")
        md.append(f"\nSoyuz boxes flatter than random Kazakh steppe ({k}): one-sided p = {u.pvalue:.2g}")
    md.append("\n\n| site | group | points | median @40 m | 99th pct @40 m | > 5 deg @40 m |\n|---|---|---|---|---|---|\n")
    for r in rows:
        if r["group"] == "reference analog":
            md.append(f"| {r['name']} | {r['group']} | {r['n_points']} | {r['med40']:.2f} | {r['p99_40']:.2f} | {r['gt5_40']:.1%} |\n")
    md.append("\nWhere it breaks: one profile line per beam, not an area; 40 m is still far above boulder scale (0.5-2 m), "
              "which Mars landers must avoid. No Moon/Mars counterpart computed at 40 m (LOLA / MOLA shot spacing is coarser).\n")
    (OUT / "icesat.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
