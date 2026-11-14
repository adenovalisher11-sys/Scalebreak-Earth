"""Step 7 - accessibility line (paper 24): distance to the nearest airport with scheduled
service, plus the snow-free season length from MODIS (months with night LST above 0 C).
Airports: OurAirports open data (public domain), types medium/large with scheduled_service=yes.
Run: .venv/bin/python run_access.py   Out: results/access.csv, access.md
"""
import csv, io, json, math, pathlib

import numpy as np
import requests

from kzanalog import sites

ROOT = pathlib.Path(__file__).parent
URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
CACHE = ROOT / "data" / "airports.csv"


def main():
    if not CACHE.exists():
        CACHE.write_text(requests.get(URL, timeout=120).text)
    ap = [r for r in csv.DictReader(io.StringIO(CACHE.read_text()))
          if r["type"] in ("medium_airport", "large_airport") and r["scheduled_service"] == "yes"]
    la = np.radians([float(r["latitude_deg"]) for r in ap]); lo = np.radians([float(r["longitude_deg"]) for r in ap])
    therm = {r["name"]: r for r in csv.DictReader(open(ROOT / "results" / "thermal.csv"))}
    cache = ROOT / "data" / "cache_modis"
    rows = []
    for grp, d in (("kazakhstan", sites.KAZAKHSTAN), ("reference", sites.REFERENCE)):
        for name, (lat, lon) in d.items():
            p1, l1 = math.radians(lat), math.radians(lon)
            dist = 6371 * 2 * np.arcsin(np.sqrt(np.sin((la - p1) / 2) ** 2 + np.cos(p1) * np.cos(la) * np.sin((lo - l1) / 2) ** 2))
            i = int(np.argmin(dist))
            f = cache / f"{lat:+08.3f}_{lon:+09.3f}_2023.json"
            warm = None
            if f.exists():
                tn = np.array(json.loads(f.read_text())["tnight"], float)
                warm = int(np.sum(tn > 273.15)) if np.isfinite(tn).sum() >= 8 else None
            rows.append(dict(group=grp, name=name, airport=ap[i]["name"], iata=ap[i]["iata_code"], km=round(float(dist[i])),
                             months_night_above_0C=warm))
    with open(ROOT / "results" / "access.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    md = ["# Accessibility\n\n| site | group | nearest airport with scheduled flights | km (great circle) | months with night surface T > 0 C (2023) |\n|---|---|---|---|---|\n"]
    for r in rows:
        md.append(f"| {r['name']} | {r['group']} | {r['airport']} ({r['iata']}) | {r['km']} | {r['months_night_above_0C'] if r['months_night_above_0C'] is not None else 'n/a'} |\n")
    (ROOT / "results" / "access.md").write_text("".join(md)); print("".join(md))


if __name__ == "__main__":
    main()
