# Kazakhstan sites: property-by-property table

All values are measured by this project's code from open NASA / ESA / JAXA data unless marked. Percentages are the share of random arid control points the site beats on that property.

| site | terrain vs Mars plains | terrain vs lunar mare plains | area with slope <=5 deg | annual T range K (beats) | daily swing K | albedo (<0.25 = Mars-like) | max NDVI (>0.3 = seasonal plants) | hydration B11/B12 (beats) | thermal inertia rank (in Mars landing band) | nearest airport km | in top 3 under random weights |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Semipalatinsk (Balapan) | 81% (smoother) | 99% (smoother) | 100% | 74 (90%) | 31 | 0.13 | 0.24 | 1.11 (87%) | 97% (yes) | 99 | 99% |
| Chiyli crater | 99% (smoother) | 91% (rougher) | 100% | 72 (90%) | 31 | 0.16 | 0.41 | 1.10 (76%) | 95% (yes) | 128 | 92% |
| Betpak-Dala | 78% (smoother) | 99% (smoother) | 100% | 71 (90%) | 31 | 0.26 | 0.21 | 1.11 (82%) | 54% (yes) | 264 | 65% |
| Zhamanshin crater | 98% (rougher) | 75% (rougher) | 100% | 71 (90%) | 30 | 0.19 | 0.30 | 1.10 (71%) | 92% (yes) | 341 | 29% |
| Bigach crater | 39% (rougher) | 31% (rougher) | 100% | 76 (97%) | 30 | 0.15 | 0.35 | 1.14 (95%) | 97% (yes) | 164 | 8% |
| Shunak crater | 31% (rougher) | 26% (rougher) | 92% | 67 (82%) | 30 | 0.17 | 0.35 | 1.17 (100%) | 97% (yes) | 174 | 4% |
| Mangystau (Bozzhyra) | 55% (rougher) | 40% (rougher) | 91% | 65 (79%) | 29 | 0.36 | 0.10 | 1.14 (95%) | 46% (yes) | 245 | 2% |
| Aralkum (dry Aral bed) | 6% (smoother) | 17% (smoother) | 100% | 64 (77%) | 34 | 0.32 | 0.09 | 1.17 (100%) | 23% (no) | 223 | 1% |
| Inder salt dome | 24% (smoother) | 53% (smoother) | 100% | 63 (77%) | 25 | 0.19 | 0.36 | 1.13 (95%) | 100% (no) | 159 | 0% |
| Soyuz zone (Zhezkazgan) | 21% (smoother) | 49% (smoother) | 100% | 76 (95%) | 34 | 0.18 | 0.27 | 1.10 (68%) | 69% (yes) | 145 | 0% |
| Soyuz zone (Arkalyk) | 36% (smoother) | 72% (smoother) | 100% | 75 (92%) | 34 | 0.16 | 0.38 | 1.05 (34%) | 69% (yes) | 292 | 0% |
| Ustyurt plateau | 15% (smoother) | 36% (smoother) | 100% | 70 (87%) | 37 | 0.33 | 0.11 | 1.05 (32%) | 5% (no) | 345 | 0% |
| Altyn-Emel (Aktau) | 37% (rougher) | 30% (rougher) | 94% | 74 (90%) | 32 | 0.32 | 0.07 | 1.07 (50%) | 36% (no) | 138 | 0% |
| Charyn canyon | 36% (rougher) | 29% (rougher) | 92% | 72 (90%) | 27 | 0.17 | 0.16 | 1.09 (63%) | 100% (no) | 110 | 0% |
| Kyzylkum (Kazakh part) | 34% (smoother) | 58% (smoother) | 100% | 73 (90%) | 38 | 0.20 | 0.15 | 1.07 (50%) | 31% (no) | 110 | 0% |
| Caspian lowland (Ryn) | 4% (smoother) | 17% (smoother) | 100% | 69 (85%) | 28 | 0.19 | 0.31 | 1.10 (66%) | 97% (yes) | 180 | 0% |

## Craters (depth / diameter against fresh craters of gravity-equivalent size)

| crater | depth m | depth/D | centre shift in search (R) |
|---|---|---|---|
| Zhamanshin crater | 66 | 0.006 | 0.67 |
| Bigach crater | 52 | 0.006 | 0.75 |
| Shunak crater | 70 | 0.025 | 0.15 |
| Chiyli crater | 29 | 0.007 | 0.81 |

## Three scales (paper 14)

- Region, 32 km windows: terrain fingerprint vs Moon/Mars landing plains (run_terrain.py).
- Landscape, 480 m cells: slope rules and Soyuz landing test (run_criteria.py, run_landing.py).
- Outcrop-near, 40 m along track: ICESat-2 laser profiles (run_icesat.py); below that nothing is measured.

## Where each property breaks

- **terrain**: Geometry only, valid from 480 m up (NASADEM and JAXA AW3D30 disagree below that on flat ground). Soil strength, rocks and boulders are not measured. Gravity 9.8 vs 3.7 / 1.6 m/s2.
- **thermal**: Annual range includes winter snow cover. Daily swing is ~30 K, far below Mars. Air at 1 bar carries heat; on the Moon and Mars radiation dominates.
- **albedo**: Approximated from MODIS nadir reflectance. Earth albedo is lowered by soil moisture and sparse plants, Mars albedo by dust-free basalt.
- **salts**: B11/B12 is a hydration indicator, not a mineral map: moisture and clays raise it. Aral salts are Na/Ca sulfates; Mars is mostly Mg/Fe sulfates.
- **crater**: Kazakh craters keep at most a quarter of the fresh depth/diameter; they are analogs for buried or eroded craters, not fresh ones. Centre search can pick up unrelated relief when no rim survives.
