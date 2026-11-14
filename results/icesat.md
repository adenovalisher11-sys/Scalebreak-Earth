# Fine-scale slopes from ICESat-2 ATL06 (NASA), snow-free months 2019-2023

Boxes +-0.15 deg. Failed or too few points: 0 ([])

| group | boxes | median slope @40 m | 99th pct @40 m | share of 40 m baselines > 5 deg | median @200 m |
|---|---|---|---|---|---|
| soyuz landing | 25 | 0.16 | 1.66 | 0.06% | 0.14 |
| random Kazakhstan | 25 | 0.34 | 3.71 | 0.44% | 0.28 |
| reference analog | 5 | 0.91 | 19.40 | 9.42% | 0.71 |

Soyuz boxes flatter than random Kazakh steppe (med40): one-sided p = 0.0011
Soyuz boxes flatter than random Kazakh steppe (p99_40): one-sided p = 1.2e-05

| site | group | points | median @40 m | 99th pct @40 m | > 5 deg @40 m |
|---|---|---|---|---|---|
| Meteor Crater, AZ | reference analog | 16285 | 0.68 | 14.26 | 4.3% |
| Black Point, AZ | reference analog | 8153 | 0.91 | 19.40 | 9.4% |
| White Sands, NM | reference analog | 3238 | 0.38 | 7.71 | 4.2% |
| MDRS Hanksville, UT | reference analog | 11543 | 1.52 | 29.82 | 21.1% |
| Mojave (Pisgah) | reference analog | 12720 | 2.01 | 26.05 | 24.5% |

Where it breaks: one profile line per beam, not an area; 40 m is still far above boulder scale (0.5-2 m), which Mars landers must avoid. No Moon/Mars counterpart computed at 40 m (LOLA / MOLA shot spacing is coarser).
