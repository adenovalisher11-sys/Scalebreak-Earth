# Steppe to Mars (Scalebreak-Earth)

This project was made by the team [HopeMaxxxing](https://www.spaceappschallenge.org/2026/find-a-team/hopemaxxxing/) from Astana for the NASA Space Apps Challenge 2026, in the challenge about terrestrial analogs. It asks whether places in Kazakhstan can serve as practice ground for missions to the Moon and Mars, and it answers the question with open data from NASA, ESA, JAXA and CSA rather than with photographs. The report with charts and maps is published at https://scalebreak-earth.vercel.app and the full description of every test is in [METHODOLOGY.md](METHODOLOGY.md).

## How the work was done

Places on Earth that are used for Moon and Mars training are usually chosen because they look similar to the target in pictures, and the team wanted to find out how similar they are when they are measured. One program measures the same properties in the same way for four groups of places.

| Group | What it contains | How many |
|---|---|---|
| Targets | Real landing sites on Mars and on the Moon | 9 on Mars and 9 on the Moon |
| Kazakhstan | Proposed places, including the Soyuz landing zones near Zhezkazgan and Arkalyk | 16 |
| Reference | Places already used for training and rover tests, such as Meteor Crater, White Sands, Atacama and Qaidam | 10 |
| Controls | Random points in eight dry regions of the world, from the Sahara to Patagonia | Between 40 and 250, depending on the test |

A place in Kazakhstan was counted as promising for a property only when it did better than the random points. Before each test the team wrote down in [PLAN.md](PLAN.md) what result would count against the idea, and failed tests are reported in the same way as successful ones. The properties are kept apart and are not added into one score.

## What was found

| What was measured | Data | Kazakhstan | Comparison | Does it stand out |
|---|---|---|---|---|
| Slope at the 95 Soyuz landing points, over 480 m | NASA NASADEM | 0.12° | 0.29° random steppe, 0.62° random deserts, 0.84° Mars sites, 0.88° Moon sites (p = 2e-10) | Yes |
| Slope at the landing points, over 40 m | NASA ICESat-2 | 0.16° | 0.34° random steppe (p = 0.001) | Yes |
| Share of 40 m stretches steeper than 5° | NASA ICESat-2 | 0.06% | 4 to 25% at US training sites | Yes |
| Change of ground temperature over the year | NASA MODIS | 72 K | 54 K random deserts, 63 K training sites (p = 8e-6) | Yes |
| Albedo | NASA MODIS | 0.19 | 0.13 to 0.24 at Mars landing sites, 0.31 at training sites | Yes, it is in the Mars range |
| Salt that has taken up water | ESA Sentinel-2 | Lake Inder salt flat and the dry Aral Sea bottom | Both score above every random point | Yes, at two places |
| Depth of craters | NASA NASADEM | Shunak keeps about a quarter of a fresh crater's depth | Fresh craters of the same gravity class on Mars | Only as old craters |
| How fast the ground heats and cools | NASA MODIS and MGS TES | Same range as Mars landing sites | No difference from other ground (p = 0.73) | No |
| General shape of the terrain over 32 km | NASADEM, MOLA and LOLA | Not closer than random points as a group (Mars p = 0.81, Moon p = 0.43) | Training sites also fail this test | No, except single places |
| Difference between day and night temperature | NASA MODIS | About 31 K | Same at random points, about 90 K on Mars | No |
| Radar roughness | ESA Sentinel-1 | No difference (p = 0.36) | Random points | No |
| Crack patterns 20 to 150 m wide | ESA Sentinel-2 | None found (p = 0.65) | The same test finds them at Dalangtan in China (p = 0.002) | No |

Some single places match the targets well even though the group as a whole does not.

| Place | Close to | Better than this share of random points |
|---|---|---|
| Chiyli crater | Flat landing plains of Mars | 99% |
| Zhamanshin crater | Flat landing plains of Mars | 98% |
| Balapan | Flat plains of the Moon | 99% |
| Betpak-Dala | Flat plains of the Moon | 99% |

When the places were ranked 1,000 times with random weights for the properties, these three stayed near the top most often.

| Place | Runs in the top three |
|---|---|
| Balapan | 99% |
| Chiyli | 92% |
| Betpak-Dala | 65% |

The full tables are in the [`results/`](results/) folder, and the best file to begin with is [`results/property_table.md`](results/property_table.md).

## What is in the repository

```
kzanalog/          code that all tests share
  sites.py         list of places, where each coordinate came from, and the random points
  dem.py           reads elevation for Earth, Mars and the Moon
  fingerprint.py   measures slope and roughness at different distances
  modis.py         reads MODIS temperature, brightness and vegetation
run_*.py           one script for each test, described in METHODOLOGY.md
build_report.py    makes the table of properties and the clickable map
make_figures.py    makes the pictures and the chart data for the report
rs1_index.py       checks whether the RADARSAT-1 archive covers Kazakhstan (optional)
data/              small input files kept in git, such as the Soyuz landing points
results/           everything the scripts produce, including tables, CSV files and map.html
report/            the report page (index.html) with its pictures and video
PLAN.md            the research plan and the result of every step, written in Russian
SUBMISSION.md      slide text, the list of data and the note about AI use
METHODOLOGY.md     a detailed description of how each test works
```

## How to get the same results

You need Python 3.12, an internet connection and some free disk space for downloaded data. None of the data sources ask for an account or a login. The program `ffmpeg` is needed only if you want to make the 3D crater video again.

### 1. Install

```bash
git clone https://github.com/adenovalisher11-sys/Scalebreak-Earth.git
```

```bash
cd Scalebreak-Earth
```

```bash
python3.12 -m venv .venv
```

```bash
.venv/bin/pip install numpy scipy rasterio matplotlib requests pillow
```

If you use `uv`, you can install the same packages with the next command.

```bash
uv venv --python 3.12 .venv && uv pip install --python .venv/bin/python numpy scipy rasterio matplotlib requests pillow
```

### 2. Run the tests

Run the scripts in the order shown below. The order matters in two places. The script `run_ti.py` reads the file `results/thermal.csv`, which is made by `run_thermal.py`, so `run_thermal.py` has to run first. The script `build_report.py` reads the results of all the other scripts, so it has to run last.

```bash
for s in run_terrain run_criteria run_landing run_thermal run_ti run_craters run_ice run_salts run_takyr run_radar run_dem_check run_icesat run_access build_report; do .venv/bin/python $s.py; done
```

There is also an optional script that searches the RADARSAT-1 archive for pictures of Kazakhstan. It takes about six minutes.

```bash
.venv/bin/python rs1_index.py
```

### 3. Build the report page

First make the pictures and the chart data.

```bash
.venv/bin/python make_figures.py
```

Then put the chart data into the page. The file `report/index.html` is the same as `report/template.html`, except that the word `__DATA__` is replaced with the contents of `report/data.json`.

```bash
.venv/bin/python -c "import pathlib; r = pathlib.Path('report'); (r/'index.html').write_text((r/'template.html').read_text(encoding='utf-8').replace('__DATA__', (r/'data.json').read_text(encoding='utf-8')), encoding='utf-8')"
```

You can open `report/index.html` in a browser, or put the whole `report/` folder on any static website host.

### 4. Compare with our results

Every script writes its files into `results/` and replaces the old ones. After a run, the command below shows which result files are now different from the ones we used for the report.

```bash
git diff --stat results/
```

### What to expect during a run

The scripts download only small pieces of each data set and keep them in the folders `data/cache*/` and `data/tes/`, which git ignores, so the first run takes a long time and the later runs are much faster. The script `run_ti.py` is the only one that downloads a whole file, of about 52 MB.

The random points are drawn with a fixed seed, so every run uses the same points, and the Soyuz landing points and the Diviner sample are saved in `data/`, so those tests always start from the same input. The Sentinel-1, Sentinel-2 and ICESat-2 scripts search a satellite archive and pick an image by date, and if the archive has changed since our run, a different image may be chosen and the numbers may shift a little. The date of every image is written in the result tables, so such a change can be traced.

## Data sources

| Data | Agency | What we used it for | Where we read it from |
|---|---|---|---|
| [NASADEM 1 arc-second](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001) | NASA and JPL | Terrain of Earth, the landing test and the craters | Microsoft Planetary Computer |
| [ICESat-2 ATL06](https://nsidc.org/data/atl06) | NASA | Slopes over 40 to 200 m | NASA OpenAltimetry and NASA CMR |
| [MODIS MYD11A2 v6.1](https://doi.org/10.5067/MODIS/MYD11A2.061) ground temperature | NASA | Temperature over the year and the ice estimate | Microsoft Planetary Computer |
| MODIS MCD43A4 v6.1 reflectance and MOD13A1 v6.1 NDVI | NASA | Approximate albedo and removing points covered by plants | Microsoft Planetary Computer |
| [LRO LOLA elevation 118 m](https://astrogeology.usgs.gov/search/map/moon_lro_lola_dem_118m) | NASA | Terrain and craters of the Moon | USGS Astrogeology |
| [LRO Diviner Polar Resource Product](https://pds-geosciences.wustl.edu/missions/lro/diviner.htm) | NASA | Temperature and ice depth near the lunar south pole | PDS Geosciences Node |
| [MOLA and HRSC blended elevation 200 m](https://astrogeology.usgs.gov/search/map/mars_mgs_mola_mex_hrsc_blended_dem_global_200m) | NASA and ESA | Terrain and craters of Mars | USGS Astrogeology |
| [MGS TES bolometric albedo](https://astrogeology.usgs.gov/search/map/mars_mgs_tes_global_bolometric_albedo_map_7410m) | NASA | Albedo of Mars | USGS Astrogeology |
| [MGS TES thermal inertia](https://pds-geosciences.wustl.edu/missions/mgs/tes-timap.html) by Putzig and Mellon (2007) | NASA | How fast the ground of Mars heats and cools | PDS Geosciences Node |
| NASA GIBS Blue Marble | NASA | Background of the map | GIBS |
| Sentinel-2 L2A | ESA Copernicus | Salt signal and the crack pattern test | Microsoft Planetary Computer |
| Sentinel-1 RTC | ESA Copernicus | Radar roughness | Microsoft Planetary Computer |
| ALOS World 3D 30 m | JAXA | A second, independent check of NASADEM | Microsoft Planetary Computer |
| RADARSAT-1 open archive | CSA | Only a check of coverage. No summer picture in the archive covers Kazakhstan. | AWS open data |
| Soyuz landing coordinates | spacefacts.de | The landing test | Saved in `data/soyuz_landings.json` |
| OurAirports | Open data | Distance to the nearest airport | ourairports-data |
| Coordinates of the places | Wikipedia, OpenStreetMap and USGS GNIS | The list of places | Written in `kzanalog/sites.py` |

The challenge also lists the EMIT mineral maps. We did not use them, because they need an Earthdata login and we wanted every step to work without an account.

## Limitations

| Limitation | What it means for the results |
|---|---|
| Earth has different gravity, air and radiation | The project does not try to copy these conditions |
| Everything was measured from satellites | Soil strength, boulders and anything smaller than about 40 m were not measured, and nobody from the team has visited the places yet |
| The Soyuz zones were picked for landings because they are flat | The landing test puts a number on that choice but does not discover it, and the zones are smoother than the real landing sites on the Moon and Mars |
| The crater centre search moved far from the catalogue position for Zhamanshin, Bigach and Chiyli | Only the Shunak crater depth can be trusted, and the other three give a rough idea |
| The ranking with random weights | It shows which places stay near the top and should not be read as a score |
| Balapan is inside the former Semipalatinsk nuclear test site | Access rules and remaining contamination were not checked |
| Coordinates of Bozzhyra and the Aktau hills come from tourism websites | They are good enough for this work but are not of survey quality |

## Use of AI

The team used Claude, a model made by Anthropic, to help with planning, with reading the scientific literature and with writing the code and the text, and the team directed and checked this work at each step. Every number in this repository comes from running the code here on the data listed above, and no images or video made by AI were used.
