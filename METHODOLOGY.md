# Methodology

How each test in this repository works, what it measures, and where the measurement stops
being valid. Numbers quoted here come from the files in [`results/`](results/).

## 1. Design

**Question.** Are sites in Kazakhstan useful analogs for Moon and Mars landing and base
sites, when judged by measurements instead of appearance?

**Rule.** The same code measures four groups, and a Kazakh site counts as promising on a
property only if it beats random ground:

| Group | Defined in | Role |
|---|---|---|
| Targets | `kzanalog/sites.py` (`MARS`, `MOON`) | 9 Mars and 9 Moon landing sites: what landing-grade ground looks like |
| Kazakhstan | `KAZAKHSTAN` | 16 candidate sites |
| Reference | `REFERENCE` | 10 established analog or rover-test sites. If a method works, these should score well |
| Controls | `random_controls()` | Random points inside eight arid-region boxes (Sahara, Arabia, Gobi, Great Basin, Australia, Kalahari, Patagonia, Iran), fixed seed |

**No composite score.** Analogs are judged property by property. Each property keeps its
own value, its rank against the controls, and a "where it breaks" line
(`results/property_table.md`). A ranking under 1,000 random weightings of four rank-type
properties is reported only to show which sites stay near the top whatever the priorities.

**Failure criteria first.** Each step in `PLAN.md` states in advance what result would
count against the hypothesis, and null results are reported as results.

**Statistics.** Group comparisons use the Mann-Whitney U test, one-sided where the
hypothesis has a direction. Per-site results are given as the share of control points the
site beats.

**Sites and coordinates.** Sources are listed at the top of `kzanalog/sites.py`:
Wikipedia, OpenStreetMap, USGS GNIS, and for two sites tourism pages. Every Kazakh point
was reverse-geocoded to the expected district. The Zhezkazgan and Arkalyk zone points are
derived from the published Soyuz landing coordinates.

**Vegetation mask.** For the terrain test, control points with a yearly maximum MODIS
NDVI above 0.3 (31 points) or with unusable elevation data are dropped, leaving 163 bare
controls out of 200.

## 2. Terrain fingerprint (`run_terrain.py`, `kzanalog/fingerprint.py`)

**Data.** NASADEM 30 m (Earth), HRSC + MOLA blend 200 m (Mars), LOLA 118 m (Moon).
A 32 km window is read around each site.

**Measurement.** The elevation grid is block-averaged to cells of 240, 480, 960 and
1920 m. At each baseline:

- slope = median absolute slope between neighbouring cells, in degrees;
- roughness = median of |z_b − (z_a + z_c)/2| for three cells in a row, in metres.
  Removing the tilt this way means a uniformly sloping plain scores zero.

All values are in physical units, so the same code is valid on the three bodies.

**Target.** Landing sites differ a lot from each other, so the target is the "plains"
class only: sites with median slope under 1° at 480 m (6 on Mars, 5 on the Moon).
Relief-class sites such as Gale or Apollo 15 are listed but not used.

**Distance.** For each Earth site, distance = mean over baselines of |ln(site / target
median)|, averaged over slope and roughness. Zero means identical curves; 0.69 means a
factor of two. A leave-one-out distance among the real landing sites gives the scale:
0.85 on Mars and 0.18 on the Moon.

**Noise floor.** Salar de Uyuni, the flattest natural surface on Earth, measures what
NASADEM reports on ground with no relief: 0.12° at 240 m, 0.03° at 480 m.

**Result.** As a group, Kazakhstan is not closer to the targets than the controls
(Mars p = 0.81, Moon p = 0.43). The reference analogs are not either (p = 0.95 and 0.97),
which means overall terrain shape does not identify analogs. Single sites do match: Chiyli
and Zhamanshin beat 98 to 99% of controls against Mars plains, and Balapan and Betpak-Dala
beat 99% against lunar mare plains.

**Where it breaks.** Geometry only. NASADEM is noise-limited below 480 m on flat ground
(section 9). The four strong sites are four of 32 site-target comparisons and were chosen
as plains, so they should be read as "flat sites match flat targets".

## 3. Published slope rules (`run_criteria.py`)

**Measurement.** Slope as gradient magnitude after block-averaging to 480 m, then the
rules used in the site-selection literature: at most 5° (Moon base ideal, Mars landing),
under 8° over more than 30% of the area (lunar research station), at most 15° (settlement
and rover corridors).

**Result.** Every group passes: all 18 landing sites, all 16 Kazakh sites, all 10
reference sites and all 40 controls meet the 8° rule. At this scale the slope rules are a
necessary condition and do not separate sites.

## 4. Landing test (`run_landing.py`)

**Data.** 95 crewed Soyuz landing points (`data/soyuz_landings.json`, from spacefacts.de;
eight were cross-checked against Wikipedia and agree within a few kilometres). NASADEM in a
6 km box around each point.

**Comparison groups.** 250 random points in the Kazakh steppe box (44.5 to 52° N, 50.5 to
78° E), 96 random arid points worldwide, and the Mars and Moon landing sites.

**Measurement.** Median slope after block-averaging to 120 m and 480 m, and the share of
the box under 5°.

**Result.** At 480 m the Soyuz points have a median slope of 0.12°, against 0.29° for
random Kazakh steppe (p = 2e-10), 0.62° for random arid ground, 0.84° for Mars and 0.88°
for Moon landing sites. In 95 of 95 boxes at least 90% of the area is under 5°.

**Where it breaks.** The landing zones were designated because they are flat and open, so
this test quantifies that choice. The zones are smoother than real Moon and Mars landing
sites, not equal to them. Soil strength and boulders are not measured.

## 5. Fine-scale slopes (`run_icesat.py`)

**Why.** NASADEM cannot be trusted below 480 m on flat ground. ICESat-2 ATL06 gives
heights every 20 m along track with centimetre to decimetre precision.

**Data.** ATL06 points from NASA OpenAltimetry for snow-free months of 2019 to 2023, in
boxes of ±0.15° around 25 Soyuz points, 25 random steppe points and 5 reference analogs.
Granule dates and track numbers come from NASA CMR.

**Measurement.** Slope over a baseline L = |Δz| / L between points L apart on the same
strong beam, for L = 40, 100 and 200 m. Reported: median, 99th percentile, and the share
of baselines steeper than 5° and 15°.

**Result.** Median slope at 40 m is 0.16° in the Soyuz boxes and 0.34° in random steppe
(p = 0.001). The 99th percentile is 1.7° against 3.7° (p = 1e-5). Baselines steeper than 5°
make up 0.06% in the Soyuz boxes and 4 to 25% at the reference analogs.

**Where it breaks.** Profiles, not maps: the ground between tracks is not sampled.

## 6. Thermal regime and albedo (`run_thermal.py`, `kzanalog/modis.py`)

**Data.** MODIS MYD11A2 land-surface temperature for 2023 (Aqua, about 13:30 and 01:30
local time), MCD43A4 reflectance, MOD13A1 NDVI. Each sample is the median of a 3 × 3 pixel
window. Mars albedo is the TES bolometric albedo at the landing sites.

**Measurement.**

- annual range = warmest monthly daytime temperature minus coldest monthly night-time
  temperature;
- daily swing = mean day minus night difference over the three warmest months;
- albedo = approximate shortwave albedo from nadir reflectance (Liang 2001 conversion),
  warmest month.

**Hypotheses, stated before the run.** H1: Kazakh sites have a larger annual range than
controls. H2: they pass the Mars "not dust-covered" albedo rule (under 0.25) at least as
often as controls.

**Result.** Annual range 72 K against 54 K for controls (p = 8e-6). Daily swing 31 K, not
different from controls (p = 0.21). Albedo median 0.19, with 11 of 16 sites under 0.25;
all Mars landing sites lie between 0.13 and 0.24.

**Where it breaks.** The annual range includes winter snow cover. The daily swing is far
below Mars. Air at 1 bar carries heat; on the Moon and Mars radiation dominates. Earth
albedo is lowered by soil moisture and sparse plants.

## 7. Thermal inertia by rank (`run_ti.py`)

**Problem.** Earth apparent thermal inertia, ATI = (1 − albedo) / (T_day − T_night), is
unitless and driven by moisture. Mars TES thermal inertia is in SI units and depends on
air pressure. Raw values cannot be compared.

**Measurement.** Each side is converted to a percentile within its own planet: an Earth
site among the arid controls, a Mars landing site among 5,000 random TES pixels within
±45° latitude.

**Result.** Mars landing sites sit between the 44th and 99th percentile of Mars. Ten of 16
Kazakh sites fall in the same band, and the two distributions do not differ (p = 0.73).
This is a null result: that band covers more than half of any distribution.

The Moon is left out because lunar regolith thermal inertia is nearly uniform.

## 8. Craters with a gravity correction (`run_craters.py`)

**Idea.** The diameter at which craters change from simple bowls to complex shapes scales
roughly with 1/g. A Kazakh crater is therefore compared with Moon or Mars craters of the
gravity-equivalent diameter, D_eq = D_earth × g_earth / g_body.

**Measurement.** An azimuthally averaged radial profile; the rim is the highest ring
between 0.6 and 1.4 catalogue radii; depth/diameter is reported. Because catalogue centres
are rounded, the centre is searched on a grid of offsets up to 0.75 radii and the deepest
result is kept. The same search is applied to every crater on every body.

**Result.** Kazakh craters keep 7 to 26% of the depth/diameter of fresh craters of
equivalent size. Shunak (2.8 km, 70 m deep, depth/D 0.025) is the reliable case: its
centre moved 0.15 radii in the search.

**Where it breaks.** For Zhamanshin, Bigach and Chiyli the centre search moved 0.67 to
0.81 radii, so it may have locked onto unrelated relief; treat those values as indicative.
Diameters of the comparison craters are approximate catalogue values. These are analogs
for eroded or buried craters, not fresh ones.

## 9. DEM cross-check (`run_dem_check.py`)

NASADEM (radar, 2000) and JAXA AW3D30 (optical stereo, 2006 to 2011) have independent
errors. Where both give the same slope, the value is terrain; where they disagree, it is
sensor noise. From 480 m upward they agree within about 10%. Below that, on flat steppe,
they differ by up to a factor of two. This is why terrain results are quoted from 480 m
and the finer scale comes from ICESat-2.

## 10. Ice under a dry cover (`run_ice.py`)

**Moon.** LRO Diviner Polar Resource Product, south pole: for each surface triangle, the
annual mean and maximum temperature and the modelled depth at which water ice is stable.
A random sample of 80,000 of 2.88 million triangles is stored in
`data/diviner_prp_south_sample.json`.

**Earth.** MODIS 2023 surface temperature at a Tien Shan glacier and moraine pixel and two
steppe sites. The depth at which the annual temperature wave no longer reaches 273 K is
estimated by pure conduction: z = δ ln(A / (273.15 − T_mean)), δ = √(κP/π), with
κ = 5e-7 m²/s **assumed** for dry debris.

**Result.** On the Moon, ice is stable somewhere in the column at 38% of sampled
locations; at 34% only under a dry layer, at a median depth of 0.08 m. In the Tien Shan
the estimated depth is about 1.6 m. The steppe sites have no permafrost by this estimate.

**Where it breaks.** This compares a geometry (ice protected beneath a dry layer), not a
temperature or a process: 93 K and sublimation on the Moon, 264 K and melting on Earth.
The Earth depth is a model estimate with an assumed diffusivity, not a measurement.

## 11. Hydration indicator (`run_salts.py`)

**Measurement.** Sentinel-2 L2A, summer 2023, bare pixels (NDVI under 0.15) in a 1 km box.
Hydrated salts and clays absorb near 2.2 µm, so the ratio of band 11 (1.61 µm) to band 12
(2.19 µm) rises. White Sands (gypsum) is the positive control.

**Result.** Controls have a median of 1.07. The Lake Inder salt flat (1.42) and the dry
Aral seabed (1.17) score above every control; White Sands scores 1.20.

**Where it breaks.** The ratio indicates hydration; it does not identify a mineral. Soil
moisture and clays raise it too. Aral salts are sodium and calcium sulfates, while Mars
deposits are mostly magnesium and iron sulfates.

## 12. Polygon patterns (`run_takyr.py`)

**Measurement.** For 2.56 km windows of Sentinel-2 band 8 (10 m): detrend, Hann window,
2-D FFT, radially averaged power, power-law fit over 15 to 640 m. Periodicity = the largest
ratio of power to the fit between 20 and 150 m. Each site is scanned with a 3 × 3 grid of
windows. Positive control: a 5 × 5 grid over the Dalangtan playa in Qaidam, where polygons
of 60 to 120 m are published.

**Result.** The control works: Dalangtan stands out from random points (p = 0.002), with
peaks at 50 to 116 m. Kazakhstan, including a takyr site, does not (p = 0.65).

**Where it breaks.** Takyr cracks are centimetres to metres wide, below the 10 m pixel.

## 13. Radar roughness (`run_radar.py`)

Sentinel-1 RTC gamma0 (C-band, 5.6 cm), July to August scenes only to limit moisture
effects, median over a 1 km box. Kazakh sites do not differ from controls (−14.6 dB
against −13.0 dB, p = 0.36). The roughest Kazakh sites are Charyn, Bozzhyra and Aktau.
RADARSAT-1 was checked (`rs1_index.py`): none of 2,245 summer scenes in the open archive
covers Kazakhstan.

## 14. Access (`run_access.py`)

Great-circle distance to the nearest airport with scheduled service (OurAirports), and the
number of months in 2023 with night surface temperature above 0 °C. Sites are 99 to 345 km
from an airport and have 5 to 9 such months.

## 15. Report and map (`build_report.py`, `make_figures.py`)

`build_report.py` joins the CSV outputs into `results/property_table.md`,
`results/site_data.json` and the interactive `results/map.html`. `make_figures.py` writes
the images and `report/data.json` used by the report page.

## 16. What Earth cannot reproduce

Gravity (9.8 against 3.7 and 1.6 m/s²), the lunar vacuum and thin Martian atmosphere,
radiation, and the lunar day-night cycle. Every result above is about one measurable
property; none of them makes a Kazakh site equivalent to the Moon or Mars.
