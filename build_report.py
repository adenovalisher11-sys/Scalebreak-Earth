"""Method 7 + 9 - assemble the per-property table and the interactive map.

Reads the CSV outputs of the run_*.py scripts. No composite index is computed: every
property keeps its own value, its rank against random arid controls, and a "where it
breaks" line. Robustness: sites are also ranked 1000 times with random property weights.
Run after all run_*.py:  .venv/bin/python build_report.py
Out: results/property_table.md, results/site_data.json, results/map.html
"""
import csv, json, pathlib

import numpy as np

from kzanalog import sites

R = pathlib.Path(__file__).parent / "results"


def table(name, key="name"):
    with open(R / name) as fh:
        return {row[key]: row for row in csv.DictReader(fh)}


def f(row, k):
    try:
        return float(row[k])
    except (KeyError, ValueError, TypeError):
        return float("nan")


BREAKS = {
    "terrain": "Geometry only, valid from 480 m up (NASADEM and JAXA AW3D30 disagree below that on flat ground). Soil strength, rocks and boulders are not measured. Gravity 9.8 vs 3.7 / 1.6 m/s2.",
    "thermal": "Annual range includes winter snow cover. Daily swing is ~30 K, far below Mars. Air at 1 bar carries heat; on the Moon and Mars radiation dominates.",
    "albedo": "Approximated from MODIS nadir reflectance. Earth albedo is lowered by soil moisture and sparse plants, Mars albedo by dust-free basalt.",
    "salts": "B11/B12 is a hydration indicator, not a mineral map: moisture and clays raise it. Aral salts are Na/Ca sulfates; Mars is mostly Mg/Fe sulfates.",
    "crater": "Kazakh craters keep at most a quarter of the fresh depth/diameter; they are analogs for buried or eroded craters, not fresh ones. Centre search can pick up unrelated relief when no rim survives.",
}


def main():
    mars, moon = table("ranking_mars.csv", "site"), table("ranking_moon.csv", "site")
    crit, therm, salt = table("criteria.csv"), table("thermal.csv"), table("salts.csv")
    crat = table("craters.csv")
    acc = table("access.csv")
    ti_pct = {}
    for line in (R / "ti.md").read_text().splitlines():
        parts = [x.strip() for x in line.strip("|").split("|")]
        if len(parts) == 4 and parts[0] in sites.KAZAKHSTAN:
            ti_pct[parts[0]] = (float(parts[2]), parts[3])
    ctrl_rng = np.array([f(r, "annual_range") for r in therm.values() if r["group"] == "control"])
    ctrl_salt = np.array([f(r, "ratio") for r in salt.values() if r["group"] == "control"])
    crater_key = {"Zhamanshin crater": "Zhamanshin (14 km rim)", "Bigach crater": "Bigach", "Chiyli crater": "Chiyli", "Shunak crater": "Shunak"}
    out = []
    for name, (lat, lon) in sites.KAZAKHSTAN.items():
        t, s, c = therm.get(name, {}), salt.get(name, {}), crit.get(name, {})
        d = dict(name=name, lat=lat, lon=lon,
                 mars_pct=f(mars.get(name, {}), "pct_of_controls_worse"), moon_pct=f(moon.get(name, {}), "pct_of_controls_worse"),
                 mars_dir=mars.get(name, {}).get("rougher_or_smoother", ""), moon_dir=moon.get(name, {}).get("rougher_or_smoother", ""),
                 area5=f(c, "f5"), annual_range=f(t, "annual_range"),
                 range_pct=float(100 * np.mean(ctrl_rng < f(t, "annual_range"))) if t else float("nan"),
                 diurnal=f(t, "diurnal_amp"), albedo=f(t, "albedo"), ndvi=f(t, "ndvi_max"),
                 salt=f(s, "ratio"), salt_pct=float(100 * np.mean(ctrl_salt < f(s, "ratio"))) if s else float("nan"))
        a = acc.get(name, {})
        d.update(airport=a.get("airport", ""), airport_km=f(a, "km"),
                 ti_pct=ti_pct.get(name, (float("nan"), ""))[0], ti_in_mars_band=ti_pct.get(name, (0, ""))[1])
        if name in crater_key:
            k = crat[crater_key[name]]
            d.update(crater_dD=f(k, "d_over_D"), crater_depth=f(k, "depth_m"), crater_shift=f(k, "centre_shift_R"))
        out.append(d)

    # robustness: rank with random weights over the four rank-type properties (papers 19, 21)
    props = ["mars_pct", "moon_pct", "range_pct", "salt_pct"]
    M = np.array([[x[p] if np.isfinite(x[p]) else 0.0 for p in props] for x in out])
    rng = np.random.default_rng(0)
    top3 = np.zeros(len(out))
    for _ in range(1000):
        w = rng.dirichlet(np.ones(len(props)))
        top3[np.argsort(-(M @ w))[:3]] += 1
    for x, v in zip(out, top3):
        x["top3_share"] = float(v / 1000)

    pct = lambda v: "n/a" if not np.isfinite(v) else f"{v:.0f}%"
    md = ["# Kazakhstan sites: property-by-property table\n\n",
          "All values are measured by this project's code from open NASA / ESA / JAXA data unless marked. "
          "Percentages are the share of random arid control points the site beats on that property.\n\n",
          "| site | terrain vs Mars plains | terrain vs lunar mare plains | area with slope <=5 deg | annual T range K (beats) | daily swing K | albedo (<0.25 = Mars-like) | max NDVI (>0.3 = seasonal plants) | hydration B11/B12 (beats) | thermal inertia rank (in Mars landing band) | nearest airport km | in top 3 under random weights |\n",
          "|---|---|---|---|---|---|---|---|---|---|---|---|\n"]
    for x in sorted(out, key=lambda x: -x["top3_share"]):
        md.append(f"| {x['name']} | {pct(x['mars_pct'])} ({x['mars_dir']}) | {pct(x['moon_pct'])} ({x['moon_dir']}) | {x['area5']:.0%} | "
                  f"{x['annual_range']:.0f} ({pct(x['range_pct'])}) | {x['diurnal']:.0f} | {x['albedo']:.2f} | {x['ndvi']:.2f} | "
                  f"{x['salt']:.2f} ({pct(x['salt_pct'])}) | {pct(x['ti_pct'])} ({x['ti_in_mars_band'] or 'n/a'}) | {x['airport_km']:.0f} | {x['top3_share']:.0%} |\n")
    md.append("\n## Craters (depth / diameter against fresh craters of gravity-equivalent size)\n\n| crater | depth m | depth/D | centre shift in search (R) |\n|---|---|---|---|\n")
    for x in out:
        if "crater_dD" in x:
            md.append(f"| {x['name']} | {x['crater_depth']:.0f} | {x['crater_dD']:.3f} | {x['crater_shift']:.2f} |\n")
    md.append("\n## Three scales (paper 14)\n\n- Region, 32 km windows: terrain fingerprint vs Moon/Mars landing plains (run_terrain.py).\n"
              "- Landscape, 480 m cells: slope rules and Soyuz landing test (run_criteria.py, run_landing.py).\n"
              "- Outcrop-near, 40 m along track: ICESat-2 laser profiles (run_icesat.py); below that nothing is measured.\n")
    md.append("\n## Where each property breaks\n\n" + "".join(f"- **{k}**: {v}\n" for k, v in BREAKS.items()))
    (R / "property_table.md").write_text("".join(md))
    clean = [{k: (None if isinstance(v, float) and not np.isfinite(v) else v) for k, v in x.items()} for x in out]
    (R / "site_data.json").write_text(json.dumps(dict(sites=clean, breaks=BREAKS), indent=1))
    print("".join(md))

    land = json.loads((R.parent / "data" / "soyuz_landings.json").read_text())["sites"]
    html = MAP.replace("__SITES__", json.dumps(clean)).replace("__LAND__", json.dumps([[v["lat"], v["lon"]] for v in land.values()])).replace("__BREAKS__", json.dumps(BREAKS))
    (R / "map.html").write_text(html)


MAP = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kazakhstan analog sites</title>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>html,body{margin:0;height:100%;font:14px/1.4 system-ui,sans-serif}#map{position:absolute;inset:0 380px 0 0}
#side{position:absolute;top:0;right:0;bottom:0;width:380px;overflow:auto;padding:16px;box-sizing:border-box;background:#fafaf7;border-left:1px solid #ddd}
h1{font-size:18px;margin:0 0 4px}h2{font-size:15px;margin:14px 0 6px}table{border-collapse:collapse;width:100%}td{padding:3px 4px;border-bottom:1px solid #e5e5e0;vertical-align:top}
td:last-child{text-align:right;white-space:nowrap}.bar{height:6px;background:#1a7f37;border-radius:3px}.muted{color:#666;font-size:12px}
@media(max-width:800px){#map{inset:0 0 50% 0}#side{top:50%;width:100%;border-left:0;border-top:1px solid #ddd}}</style></head><body>
<div id="map"></div><div id="side"><h1>Kazakhstan as a Moon / Mars analog</h1>
<p class="muted">Click a green site. Percentages = share of random arid control points the site beats on that property. Grey dots: 95 real Soyuz landing points. Built from NASA NASADEM, MODIS, LRO LOLA and Diviner, MGS MOLA and TES; ESA Sentinel-2; JAXA AW3D30.</p><div id="info"></div></div>
<script>
const S=__SITES__,L0=__LAND__,B=__BREAKS__;
const map=L.map('map').setView([47,66],5);
L.tileLayer('https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',{maxZoom:8,attribution:'NASA GIBS Blue Marble'}).addTo(map);
L0.forEach(p=>L.circleMarker(p,{radius:2,color:'#555',weight:1,fillOpacity:.6}).addTo(map));
const pct=v=>v==null?'n/a':Math.round(v)+'%';
function row(k,v,p){return `<tr><td>${k}${p!=null?`<div class="bar" style="width:${Math.max(2,p)}%"></div>`:''}</td><td>${v}</td></tr>`}
function show(s){let h=`<h2>${s.name}</h2><table>`
+row('Terrain vs Mars landing plains',pct(s.mars_pct)+' ('+s.mars_dir+')',s.mars_pct)
+row('Terrain vs lunar mare landing plains',pct(s.moon_pct)+' ('+s.moon_dir+')',s.moon_pct)
+row('Area with slope &le; 5&deg; at 480 m',Math.round(s.area5*100)+'%',null)
+row('Annual surface temperature range',Math.round(s.annual_range)+' K, beats '+pct(s.range_pct),s.range_pct)
+row('Daily swing, warm season',Math.round(s.diurnal)+' K',null)
+row('Albedo (Mars landing sites 0.13&ndash;0.24)',s.albedo==null?'n/a':s.albedo.toFixed(2),null)
+row('Max NDVI (&gt;0.3 = seasonal plants)',s.ndvi==null?'n/a':s.ndvi.toFixed(2),null)
+row('Hydrated-salt indicator B11/B12',s.salt==null?'n/a':s.salt.toFixed(2)+', beats '+pct(s.salt_pct),s.salt_pct);
if(s.crater_dD!=null)h+=row('Crater depth / diameter',s.crater_dD.toFixed(3)+' ('+Math.round(s.crater_depth)+' m deep)',null);
h+='</table><h2>Where it breaks</h2><ul class="muted">'+Object.values(B).map(x=>'<li>'+x+'</li>').join('')+'</ul>';
document.getElementById('info').innerHTML=h}
S.forEach(s=>L.circleMarker([s.lat,s.lon],{radius:8,color:'#0f5223',fillColor:'#1a7f37',fillOpacity:.9,weight:2}).addTo(map).bindTooltip(s.name).on('click',()=>show(s)));
show(S[0]);
</script></body></html>"""

if __name__ == "__main__":
    main()
