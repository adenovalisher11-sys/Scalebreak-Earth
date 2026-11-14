# Steppe to Mars (Scalebreak-Earth)

Testing sites in Kazakhstan as Moon and Mars analogs with open NASA, ESA, JAXA and CSA data.
A NASA Space Apps Challenge 2026 project (terrestrial analogs challenge).

**Live report:** https://scalebreak-earth.vercel.app

## What this is

Analog sites are usually chosen because they look like the Moon or Mars. This project
measures instead. One pipeline computes the same properties for four groups of places:

| Group | What | Count |
|---|---|---|
| Targets | Real landing sites on Mars and the Moon | 9 + 9 |
| Kazakhstan | Candidate sites, including the two Soyuz landing zones | 16 |
| Reference | Established analog and rover-test sites (Meteor Crater, White Sands, Atacama, Qaidam...) | 10 |
| Controls | Random points in eight arid regions of the world | 40 to 200, depending on the test |

A Kazakh site counts as promising on a property only if it beats the random controls.
Every property is reported separately, with a line saying where the analogy breaks.
There is no single analog score.

## Results at a glance

| Layer | Does Kazakhstan stand out? | Numbers |
|---|---|---|
| Landing ground, 480 m (NASADEM) | Yes | 95 Soyuz landing points: median slope 0.12° against 0.29° for random Kazakh steppe (p = 2e-10), 0.62° random arid world, 0.84° Mars and 0.88° Moon landing sites |
| Landing ground, 40 m (ICESat-2) | Yes | Median 0.16° against 0.34° for random steppe (p = 0.001); 0.06% of 40 m baselines steeper than 5° |
| Annual temperature range (MODIS) | Yes | 72 K against 54 K for controls (p = 8e-6) |
| Albedo in the Mars landing-site range | Yes | Median 0.19; Mars landing sites 0.13 to 0.24; reference analogs 0.31 |
| Hydrated-salt signal (Sentinel-2) | Two sites | Lake Inder salt flat and the dry Aral seabed score above every control |
| Craters | As eroded craters only | Shunak keeps about a quarter of the depth/diameter of a fresh crater of equivalent size |
| Thermal inertia by rank | No | Kazakh sites and Mars landing sites do not differ (p = 0.73) |
| Overall terrain shape | No, as a group | Against controls: Mars p = 0.81, Moon p = 0.43. Single sites do match: Chiyli and Zhamanshin (Mars plains), Balapan and Betpak-Dala (lunar mare plains) |
| Daily temperature swing | No | About 31 K, same as controls and far below Mars |
| Radar roughness (Sentinel-1) | No | p = 0.36 |
| 20 to 150 m polygon patterns | No | p = 0.65; the same test does detect the Dalangtan polygons in Qaidam (p = 0.002) |

Full tables are in [`results/`](results/). Start with
[`results/property_table.md`](results/property_table.md).

## Repository layout

```
kzanalog/          shared code
  sites.py         site catalogue, coordinate sources, random control points
  dem.py           elevation windows for Earth, Mars and the Moon
  fingerprint.py   slope and roughness as a function of baseline
  modis.py         MODIS temperature, reflectance and NDVI samples
run_*.py           one script per test (see METHODOLOGY.md)
build_report.py    per-property table and interactive map
make_figures.py    images and chart data for the report page
rs1_index.py       RADARSAT-1 coverage check (optional)
data/              small inputs kept in git (Soyuz landing points, Diviner sample...)
results/           outputs of every script: tables, CSVs, figures, map.html
report/            the published report page (index.html) and its assets
PLAN.md            research plan and outcome of every step (in Russian)
SUBMISSION.md      slide text, data list, AI disclosure
METHODOLOGY.md     how each test works
```

## How to recreate the results

**Requirements:** Python 3.12, an internet connection and free disk space for the data caches.
No account or login is needed for any data source. `ffmpeg` is needed only for the
3D crater video made by `make_figures.py`.

**1. Install**

```bash
git clone https://github.com/adenovalisher11-sys/Scalebreak-Earth.git
cd Scalebreak-Earth
python3.12 -m venv .venv
.venv/bin/pip install numpy scipy rasterio matplotlib requests pillow
```

With `uv`: `uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python numpy scipy rasterio matplotlib requests pillow`

**2. Run the tests, in this order**

```bash
for s in run_terrain run_criteria run_landing run_thermal run_ti run_craters run_ice \
         run_salts run_takyr run_radar run_dem_check run_icesat run_access build_report; do
  .venv/bin/python $s.py
done
```

Order matters in two places: `run_ti.py` reads `results/thermal.csv` from `run_thermal.py`,
and `build_report.py` reads the CSVs of all the others, so it goes last.

Optional: `.venv/bin/python rs1_index.py` scans the RADARSAT-1 open archive for scenes
over Kazakhstan (about 6 minutes).

**3. Rebuild the report page**

```bash
.venv/bin/python make_figures.py
.venv/bin/python -c "import pathlib; r = pathlib.Path('report'); (r/'index.html').write_text((r/'template.html').read_text(encoding='utf-8').replace('__DATA__', (r/'data.json').read_text(encoding='utf-8')), encoding='utf-8')"
```

`report/index.html` is `report/template.html` with `__DATA__` replaced by `report/data.json`.
Open it in a browser, or deploy the `report/` folder as a static site.

**4. Check against the committed results**

Each script overwrites its files in `results/`. `git diff --stat results/` shows what changed
compared with the run used for the report.

**What to expect**

- Data are read over HTTP as small windows and cached under `data/cache*/` and `data/tes/`
  (ignored by git). The first run is the slow one. `run_ti.py` downloads one 52 MB file.
- Random control points use fixed seeds, so the same points are drawn every time.
- The Soyuz landing points and the Diviner sample are stored in `data/`, so those tests
  use exactly the same inputs.
- Small differences are possible where a script picks a satellite scene by search
  (Sentinel-1, Sentinel-2, ICESat-2), if the archive has changed. Scene dates are printed
  in the result tables.

## Data sources

| Data | Agency | Used for | Read from |
|---|---|---|---|
| [NASADEM 1 arc-second](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001) | NASA / JPL | Earth terrain, landing test, craters | Microsoft Planetary Computer mirror |
| [ICESat-2 ATL06](https://nsidc.org/data/atl06) | NASA | Slopes at 40 to 200 m | NASA OpenAltimetry and CMR |
| [MODIS MYD11A2 v6.1](https://doi.org/10.5067/MODIS/MYD11A2.061) land-surface temperature | NASA | Thermal regime, ice estimate | Planetary Computer mirror |
| MODIS MCD43A4 v6.1 reflectance, MOD13A1 v6.1 NDVI | NASA | Approximate albedo, vegetation mask | Planetary Computer mirror |
| [LRO LOLA DEM 118 m](https://astrogeology.usgs.gov/search/map/moon_lro_lola_dem_118m) | NASA | Moon terrain and craters | USGS Astrogeology |
| [LRO Diviner Polar Resource Product](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | NASA | Lunar polar temperature and ice depth | PDS Geosciences Node |
| [MOLA + HRSC blended DEM 200 m](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m) | NASA / ESA | Mars terrain and craters | USGS Astrogeology |
| [MGS TES bolometric albedo](https://astrogeology.usgs.gov/search/map/mars_mgs_tes_global_bolometric_albedo_map_7410m) | NASA | Mars albedo | USGS Astrogeology |
| [MGS TES thermal inertia](https://pds-geosciences.wustl.edu/missions/mgs/tes-timap.html) (Putzig & Mellon 2007) | NASA | Mars thermal inertia by rank | PDS Geosciences Node |
| NASA GIBS Blue Marble | NASA | Map background | GIBS WMTS |
| Sentinel-2 L2A | ESA Copernicus | Hydration indicator, polygon test | Planetary Computer mirror |
| Sentinel-1 RTC | ESA Copernicus | Radar roughness | Planetary Computer mirror |
| ALOS World 3D 30 m | JAXA | Independent check of NASADEM | Planetary Computer mirror |
| RADARSAT-1 open archive | CSA | Coverage check only: no summer scene covers Kazakhstan | AWS open data |
| Soyuz landing coordinates | spacefacts.de | Landing test | Mission pages, stored in `data/soyuz_landings.json` |
| OurAirports | open data | Accessibility | ourairports-data |
| Site coordinates | Wikipedia, OpenStreetMap, USGS GNIS | Site catalogue | Listed in `kzanalog/sites.py` |

Not used although listed by the challenge: EMIT mineral maps (they need an Earthdata login,
and this pipeline runs without one).

## Methodology

See [METHODOLOGY.md](METHODOLOGY.md) for how each test works, the statistics used and the
limits of each measurement.

## Limitations

- Earth cannot reproduce lunar or Martian gravity, air pressure or radiation.
- Everything is measured from orbit. Soil strength, boulders and anything smaller than
  about 40 m are not measured. No site was visited.
- The Soyuz landing zones were chosen for flat, open ground. The landing test puts a number
  on that choice; it does not discover it. The zones are also smoother than real Moon and
  Mars landing sites, so they match the landing rules but not the roughness of the targets.
- Crater depth is reliable for Shunak only. For Zhamanshin, Bigach and Chiyli the centre
  search moved far from the catalogue position, so those numbers are indicative.
- The site ranking under random weights is a robustness check, not a score.
- Balapan lies inside the former Semipalatinsk nuclear test site. Access rules and residual
  contamination were not assessed.
- Coordinates of two sites (Bozzhyra, Aktau hills) come from tourism pages and are not
  survey grade.

## Use of AI

Planning, literature synthesis, code and text were produced with Claude (Anthropic) under
the team's direction. All numbers come from running the code in this repository on the data
listed above. No AI-generated images or video are used.
