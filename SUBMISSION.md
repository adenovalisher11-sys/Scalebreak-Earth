# Submission pack: Kazakhstan as a Moon / Mars analog

## Seven slides (English)

**1. The question.** Analog sites are chosen by eye ("looks like Mars"). We test a whole
country with numbers instead: Kazakhstan is absent from the analog literature (0 of 33
reviewed papers), yet NASA astronauts land there today (Soyuz MS-28, July 2026).

**2. Method: try to disprove it.** Same code for four groups: Moon / Mars targets,
16 Kazakh sites, 10 established analogs (Meteor Crater, Black Point, White Sands,
Atacama...), and ~200 random arid control points. A site is promising only if it beats
the random controls. Every property gets its own "where it breaks" line; no composite score.

**3. Landing ground (headline result).** 95 real Soyuz landing points (NASADEM):
median slope 0.12° at 480 m vs 0.29° random Kazakh steppe (p = 2e-10), 0.62° random
arid world, 0.84° Mars and 0.88° Moon landing sites. 95 / 95 landing boxes meet the 5°
landing rule. ICESat-2 laser profiles confirm it at 40 m: median 0.16° vs 0.34° random steppe
(p = 0.001); only 0.06 % of 40 m baselines exceed 5°. Breaks: geometry only; soil strength and boulders are not measured.

**4. Thermal regime.** MODIS 2023: annual surface-temperature range 72 K in Kazakhstan vs
54 K for random deserts (p = 8e-6). Albedo 0.19 sits inside the 0.13–0.24 range of all
10 Mars landing sites (TES); established analogs median 0.31. Breaks: daily swing ~30 K
(not Mars-like), winter snow. Thermal inertia by rank: 10 of 16 Kazakh sites sit in the same
part of Earth's range (MODIS ATI) as Mars landing sites sit in Mars's (TES, 44th-99th percentile).

**5. Terrain and craters.** The Semipalatinsk Balapan plain and Betpak-Dala match lunar mare
landing plains (LOLA) better than 99 % of random bare controls; Chiyli and Zhamanshin
match Martian landing plains better than 98–99 %. Kazakh craters keep 7–26 % of the
depth/diameter of fresh lunar / Martian craters of gravity-equivalent size: analogs for
eroded, buried craters, not fresh ones.

**6. Ice under a dry cover (Diviner).** Lunar south pole (Diviner PRP, 80,000 sampled
triangles): ice is stable in 38 % of the column, 34 % only under a dry layer, median
0.08 m deep. Tien Shan moraine (MODIS): the annual freeze line sits ~1.6 m down. Same
process, different physics: 93 K vs 264 K, sublimation vs melting.

**7. What to do with it.** Top candidates under 1,000 random weightings: Balapan plain
(top 3 in 99 % of runs), Chiyli crater (92 %), Betpak-Dala (65 %). Honest negatives: overall
terrain, radar roughness and 20-150 m polygons do not set Kazakhstan apart (the polygon test
does detect the Dalangtan polygons in Qaidam, so the method works). Use: rehearsal of
lander hazard maps and thermal cycling at 480 m+ scale. Code and data are open; the same
pipeline tests any region on Earth.

## Data used
| Data | Agency | Used for | Access |
|---|---|---|---|
| NASADEM 1 arc-second | NASA / JPL | Earth terrain, landing test, craters | Microsoft Planetary Computer mirror |
| MODIS MYD11A2 LST v6.1 | NASA | Thermal regime | Planetary Computer mirror |
| MODIS MCD43A4 NBAR v6.1 | NASA | Approximate albedo | Planetary Computer mirror |
| MODIS MOD13A1 NDVI v6.1 | NASA | Vegetation mask | Planetary Computer mirror |
| LRO LOLA global DEM 118 m | NASA | Moon terrain and craters | USGS Astrogeology |
| LRO Diviner Polar Resource Product v2 | NASA | Lunar polar temperature and ice depth | PDS Geosciences Node |
| MGS MOLA + Mars Express HRSC blend 200 m | NASA / ESA | Mars terrain and craters | USGS Astrogeology |
| MGS TES albedo | NASA | Mars albedo | USGS Astrogeology |
| MGS TES thermal inertia (Putzig & Mellon 2007) | NASA | Mars thermal inertia by rank | PDS Geosciences Node |
| OurAirports | open data | Accessibility | davidmegginson.github.io/ourairports-data |
| NASA GIBS Blue Marble | NASA | Map background | GIBS WMTS |
| Sentinel-2 L2A | ESA Copernicus | Hydrated-salt indicator, polygon-pattern test | Planetary Computer mirror |
| Sentinel-1 RTC | ESA Copernicus | Radar roughness (C-band, as RADARSAT) | Planetary Computer mirror |
| ICESat-2 ATL06 | NASA | Fine-scale slopes along track | NASA OpenAltimetry, CMR |
| ALOS World 3D 30 m | JAXA | Independent check of NASADEM | Planetary Computer mirror |
| Soyuz landing coordinates | spacefacts.de | Landing test | Mission pages |
| Site coordinates | Wikipedia | Craters and sites | API |

Not used although listed by the challenge: RADARSAT-1 (CSA open archive on AWS: none of 2,245 summer scenes from 1996-2013 covers Kazakhstan; Sentinel-1 used as the C-band equivalent) and EMIT minerals (needs a login).

## Tools
Python 3.12, numpy, scipy, rasterio (GDAL), matplotlib, requests, Leaflet 1.9.4.

## Use of AI
Planning, literature synthesis, code and text were produced with Claude (Anthropic) under
the team's direction. All numbers come from running the code on the data above. No
AI-generated images or video.
