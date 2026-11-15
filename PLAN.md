# Research plan: Kazakhstan as a Mars and Moon analog — outcome

Status on 14 November 2026: every step has been run on data. Each step below states its result
separately: hypothesis confirmed, rejected, or a null result. The video was dropped by team decision on
14 November; 7 slides are submitted instead (SUBMISSION.md).
Project rule: every hypothesis has a failure criterion written down in advance, and the same code measures
the target (Mars, Moon), Kazakhstan, established analogs and random arid points.
The whole pipeline is rerun with the command in README.md; the last full run was on 14 November, after
the coordinates of all sites were checked (sources in `kzanalog/sites.py`).
The Russian original of this file is [PLAN.ru.md](PLAN.ru.md).

## Data roles (as used)

| Source | Used for | Script |
|---|---|---|
| NASA NASADEM 30 m | Kazakhstan terrain, landing test, craters | run_terrain, run_criteria, run_landing, run_craters |
| NASA ICESat-2 ATL06 (OpenAltimetry) | Slopes at 40–200 m | run_icesat |
| NASA MODIS LST, NBAR, NDVI | Thermal regime, albedo, vegetation mask | run_thermal, run_ti, run_terrain |
| NASA LRO LOLA, Diviner PRP | Moon terrain and craters; south-pole temperature and ice | run_terrain, run_craters, run_ice |
| NASA MGS MOLA+HRSC, TES albedo and thermal inertia | Mars terrain, craters, albedo, thermal inertia | run_terrain, run_craters, run_thermal, run_ti |
| NASA GIBS | Map background | build_report |
| ESA Sentinel-2 | Salt indicator, polygon search | run_salts, run_takyr |
| ESA Sentinel-1 | Radar roughness (C-band) | run_radar |
| CSA RADARSAT-1 (archive on AWS) | Check of coverage over Kazakhstan | rs1_index |
| JAXA AW3D30 | Independent check of NASADEM terrain | run_dem_check |

## Steps and results

**Step 0. Data access — done.** `kzanalog/dem.py` and `kzanalog/modis.py` read every layer over HTTP with no login.

**Step 1. Blind terrain ranking — done. Result: Kazakhstan as a group does not stand out.**
With "plains"-class targets and 163 bare control points: Mars p = 0.81, Moon p = 0.43.
Single sites are strong: Chiyli and Zhamanshin are closer to Martian landing plains than 98–99% of
controls; Balapan and Betpak-Dala are closer to lunar ones than 99%.

**Step 1b. Published slope thresholds — done. Result: the thresholds do not separate sites.**
The rule from paper 31 is passed by 18/18 real landing sites, 5/5 regions from papers 18, 21 and 30,
16/16 Kazakh sites and 40/40 random points. Slope at 480 m is a necessary condition, not a distinguishing one.

**Step 2. Target, coordinates, controls — done. Result: the criterion was NOT met.**
Original wording of the step: "Criterion: after this, established analogs must beat random points.
If they do not, we say so plainly." The work of the step (coordinates, target classes, 200 control points,
NDVI mask) was done in full; the criterion itself was not met, and that is recorded below.
The coordinates of all sites were checked against outside sources: Wikipedia (craters, Balapan, Charyn,
centre of the Aralkum, the American analogs), OpenStreetMap (Inder, Ryn sands, Ustyurt, Betpak-Dala,
Lenghu yardangs, Kyzylkum), USGS GNIS (Black Point, "Bench", Coconino County), tourism guides (Bozzhyra,
Aktau hills; not survey grade); the landing zones come from 95 published points (Arkalyk is the median of
the 41 northern landings). Every Kazakh point was reverse-geocoded to the expected district. Targets are
split into "plains" and "relief". There are 200 control points; 163 remain after the vegetation mask
(MODIS NDVI ≤ 0.3). The criterion "established analogs beat random points" was not met (Mars p = 0.95,
Moon p = 0.97): overall terrain does not identify an analog. This is a result of the test, not unfinished
work: it is the reason the project compares sites on several layers.

**Step 3. Landing test — done. Result: the main result.**
95 Soyuz landing points: median slope 0.12° (480 m) against 0.29° for random steppe (p = 2·10⁻¹⁰),
0.62° for random deserts, 0.84° for Mars landing sites and 0.88° for Moon ones; 95 of 95 windows pass the 5° rule.
ICESat-2 at 40 m: 0.16° against 0.34° (p = 0.001), 99th percentile 1.7° against 3.7° (p = 10⁻⁵),
slopes steeper than 5°: 0.06%; at established analogs 4–25%.

**Step 4. Craters with a gravity correction — done.**
Kazakh craters keep 7–26% of the depth-to-diameter ratio of fresh craters of the equivalent class.
Shunak is reliable (centre shift 0.15 R); for Zhamanshin, Bigach and Chiyli the centre search moved 0.67–0.81 R.

**Step 5. Thermal regime — done. Result: hypothesis confirmed.**
Annual range 72 K against 54 K for random deserts (p = 8·10⁻⁶). Albedo 0.19 (11 of 16 sites below 0.25),
inside the range of all 10 Mars sites (0.13–0.24). Daily swing about 31 K — no difference.
Thermal data exist for all 16 sites (MODIS tile selection was fixed: the tile number is computed from the projection).

**Step 5c. Thermal inertia by rank — done.**
TES (Mars): landing sites lie in the 44th–99th percentile of their planet. Kazakh apparent thermal inertia
(MODIS) falls in the same percentile range at 10 of 16 sites; the distributions do not differ
(p = 0.73). The Moon is not included: regolith thermal inertia is nearly the same everywhere.

**Step 5b. Ice under a dry cover (Diviner) — done.**
Lunar south pole: ice is stable in 38% of columns, in 34% only under a dry layer (median 0.08 m).
Tien Shan moraine: freezing boundary at about 1.6 m (estimate). The gap: 93 K against 264 K.

**Step 6. Salts and takyrs — done. Result: salts — a signal is present; polygons — null (the method works on the control).**
Salt indicator: the Lake Inder salt flat at 1.42 and the Aral seabed at 1.17 are above every control; the White Sands control is 1.20.
Search for 20–150 m polygons: the positive control works — a 5×5 grid over the Dalangtan area (bounds
from Kong et al.) stands out from the controls (p = 0.002), and its peaks at 50–116 m match the published
60–120 m. Kazakhstan, including the Daryalyk takyr, does not stand out (p = 0.65): there are no polygons of
this scale at the chosen points. Takyr cracks themselves (cm–m) are smaller than the 10 m pixel and are not measured.

**Step 7. Property table — done.** (results/property_table.md).
No overall index; a "where it breaks" line for every property; three scales (region 32 km,
landscape 480 m, profile 40 m); access (nearest airport 99–345 km; 5–9 frost-free months
by night surface temperature). Leaders under 1,000 random weightings: Balapan (in the top three in 99%
of runs), Chiyli (92%), Betpak-Dala (65%).

**Step 8. Partner data — done. Result: JAXA confirms the terrain from 480 m up; radar does not single out Kazakhstan; RADARSAT-1 does not cover Kazakhstan.**
JAXA AW3D30 and NASADEM agree within 10% from 480 m; below that, on flat steppe, they differ by up to a factor of 2 (noise).
Sentinel-1: Kazakhstan does not differ from the controls (p = 0.36); the roughest sites are Charyn, Bozzhyra and Aktau.
RADARSAT-1: of 2,245 summer scenes in the open archive (1996–2013), none covers Kazakhstan;
RCM data are not openly distributed.

**Step 9. Map and submission materials — done (no video, by team decision).**
results/map.html (click a site for all its properties and "where it breaks"), SUBMISSION.md (7 slides, data,
tools, AI disclosure). The video was dropped by team decision.

## Summary: where Kazakhstan stands out and where it does not

| Layer | Stands out? |
|---|---|
| Landing ground (480 m and 40 m) | Yes, on two independent data sets |
| Annual temperature range | Yes |
| Albedo in the Martian range | Yes |
| Thermal inertia by rank | Matches the Martian landing sites, but does not differ from them |
| Overall terrain | No (single sites do) |
| Radar roughness | No |
| 20–150 m polygons | No (method checked on Dalangtan) |
