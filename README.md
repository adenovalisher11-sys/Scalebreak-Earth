# Steppe to Mars (Scalebreak-Earth)

This project was made by a team from Astana for the NASA Space Apps Challenge 2026, in the challenge about terrestrial analogs. It asks whether places in Kazakhstan can serve as practice ground for missions to the Moon and Mars, and it answers the question with open data from NASA, ESA, JAXA and CSA rather than with photographs. The report with charts and maps is published at https://scalebreak-earth.vercel.app and the full description of every test is in [METHODOLOGY.md](METHODOLOGY.md).

## How the work was done

Places on Earth that are used for Moon and Mars training are usually chosen because they look similar to the target in pictures, and the team wanted to find out how similar they are when they are measured. One program was written that measures the same properties in the same way for four groups of places. The first group holds 9 real landing sites on Mars and 9 on the Moon, which show what landing ground on those bodies is like. The second group holds 16 places in Kazakhstan, including the two zones near Zhezkazgan and Arkalyk where Soyuz crews come down. The third group holds 10 places that are already used for training and rover tests, among them Meteor Crater, White Sands, the Atacama desert and the Qaidam basin. The fourth group holds between 40 and 200 random points (the number depends on the test) spread over eight dry regions of the world, from the Sahara and Arabia to the Gobi, Patagonia and Australia.

A place in Kazakhstan was counted as promising for a property only when it did better than the random points, because a property that any random desert also has says nothing special about Kazakhstan. Before each test was run, the team wrote down in [PLAN.md](PLAN.md) what result would count against the idea, and the tests that failed are reported in the same way as the tests that succeeded. The properties were kept apart and were not added into a single score, since one number would hide which properties are strong and which are weak.

## What was found

The clearest result came from the Soyuz landing zones. The team took the published coordinates of 95 crewed Soyuz landings and measured the slope of the ground around each of them with the NASA NASADEM elevation map, comparing points that are 480 m apart. The median slope at the landing points was 0.12 degrees, while random points in the Kazakh steppe gave 0.29 degrees, random deserts of the world gave 0.62 degrees, the Mars landing sites gave 0.84 degrees and the Moon landing sites gave 0.88 degrees. A Mann-Whitney test gave p = 2e-10 for the difference between the landing points and the random steppe, which means a gap of this size is very unlikely to appear by chance. Because NASADEM becomes unreliable on very flat ground at shorter distances, the same comparison was repeated with laser heights from the NASA ICESat-2 satellite at a distance of 40 m. The landing points again came out flatter, with a median slope of 0.16 degrees against 0.34 degrees in random steppe, and only 0.06 percent of the measured 40 m stretches were steeper than 5 degrees.

The temperature and brightness of the ground were measured next, with data from the NASA MODIS instrument. The ground temperature in Kazakhstan changes by about 72 K between summer and winter, while at the random points it changes by about 54 K, and the test gave p = 8e-6 for this difference. The median albedo of the Kazakh places was 0.19, which lies inside the range of 0.13 to 0.24 found at all ten Mars landing sites that were checked, while the established training sites were brighter, with a median of 0.31. The difference between day and night temperature was about 31 K, which is the same as at the random points and much smaller than on Mars, so this property did not separate Kazakhstan from other deserts.

The search for salt that has taken up water, which on Mars marks places where water once stood, was done with images from the ESA Sentinel-2 satellite. Two places scored higher than every random point, and these were the salt flat of Lake Inder and the dry bottom of the Aral Sea. The craters of Kazakhstan were compared with fresh craters of the same size on Mars after correcting for the difference in gravity, and they turned out to be old and worn down. Shunak, the only crater where the measurement can be trusted, has kept about a quarter of the depth that a fresh crater of its size would have.

Several tests did not show that Kazakhstan stands out. When the general shape of the terrain over 32 km was compared with the flat landing plains of Mars and the Moon, the Kazakh places as a group were not closer to the targets than the random points were. A few single places did match well, since Chiyli and Zhamanshin came closer to the Mars plains than 98 to 99 percent of the random points, and Balapan and Betpak-Dala came closer to the lunar plains than 99 percent of them. The established training sites did not beat the random points in this test either, which suggests that the overall shape of the terrain is not what makes a good analog. The rate at which the ground heats and cools placed the Kazakh places in the same range as the Mars landing sites, but this did not set them apart from other ground. Radar images from the ESA Sentinel-1 satellite showed no difference in roughness between Kazakhstan and the random points (p = 0.36). The search for crack patterns 20 to 150 m wide found nothing in Kazakhstan (p = 0.65), although the same method did find the known patterns at Dalangtan in China (p = 0.002), so the method itself was shown to work.

When the places were ranked 1,000 times with random weights for the properties, Balapan was among the top three in 99 percent of the runs, Chiyli in 92 percent and Betpak-Dala in 65 percent. The full tables are kept in the [`results/`](results/) folder, and the best file to begin with is [`results/property_table.md`](results/property_table.md).

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

Earth cannot copy the low gravity, the thin air or the radiation of the Moon and Mars, and this project does not try to deal with those differences. Everything was measured from satellites, so the strength of the soil, the number of boulders and any feature smaller than about 40 m were not measured, and no member of the team has visited the places yet.

The Soyuz landing zones were chosen for landings in the first place because the ground there is flat and open, so the landing test puts a number on that choice rather than discovering something new. The zones are also smoother than the real landing sites on the Moon and Mars, which means that they meet the same safety rules for landing but are not as rough as the places a spacecraft would actually land on.

The crater depth can be trusted only for Shunak, because for Zhamanshin, Bigach and Chiyli the program that searches for the crater centre moved far from the position given in the catalogue, and the numbers for these three craters give only a rough idea. The ranking with random weights shows which places stay near the top whatever the priorities are, and it should not be read as a score.

Balapan lies inside the former Semipalatinsk nuclear test site, and the team did not check the rules for entering it or how much contamination is left there. The coordinates of Bozzhyra and the Aktau hills were taken from tourism websites, and they are good enough for this work but are not of survey quality.

## Use of AI

The team used Claude, a model made by Anthropic, to help with planning, with reading the scientific literature and with writing the code and the text, and the team directed and checked this work at each step. Every number in this repository comes from running the code here on the data listed above, and no images or video made by AI were used.
