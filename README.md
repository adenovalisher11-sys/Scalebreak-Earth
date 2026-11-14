# kz-analog

Tests Kazakhstan sites as Moon/Mars analogs with open NASA data.

    uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python numpy scipy rasterio matplotlib requests
    for s in run_terrain run_criteria run_landing run_thermal run_ti run_craters run_ice run_salts run_takyr \
             run_radar run_dem_check run_icesat run_access build_report; do .venv/bin/python $s.py; done
    .venv/bin/python rs1_index.py        # optional, ~6 min: RADARSAT-1 coverage check

Data read by `kzanalog/dem.py` (no login needed):
- Earth: NASADEM 30 m (NASA/JPL), COG mirror on Microsoft Planetary Computer
- Moon: LRO LOLA global DEM 118 m (NASA), USGS Astrogeology
- Mars: HRSC+MOLA blended DEM 200 m (NASA MGS MOLA + ESA Mars Express), USGS Astrogeology

Outputs in `results/`: `summary.md`, `ranking_mars.csv`, `ranking_moon.csv`, `curves_*.png`, `terrain.json`.
Site coordinates in `kzanalog/sites.py` are approximate and must be checked before publishing.
See `PLAN.md` for the research plan.
