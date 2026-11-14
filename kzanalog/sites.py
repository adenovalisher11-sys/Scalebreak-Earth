"""Site catalogue. Coordinates are (lat, lon_east) in degrees.

Sources (checked 2026-11-14):
- Wikipedia coordinates: the four impact craters, Chagan (Balapan), Charyn, Meteor Crater,
  White Sands, MDRS, Pisgah, and all Moon/Mars craters in run_craters.py.
- OpenStreetMap features: Lake Inder (lake centre 48.462, 51.929; the site point sits on the
  salt-dome highland ~12 km NW), Ryn sands (natural=sand), Ustyurt (natural=plateau),
  Betpak-Dala (locality), Eboliang yardang field at Lenghu, Kyzylkum south of the Syr Darya
  (reverse-geocoded to Shieli district).
- Tourism / tour-operator pages (not survey grade): Bozzhyra tract centre, Aktau hills of
  Altyn-Emel.
- Published landing points: Zhezkazgan zone = centre of the southern cluster; Arkalyk zone =
  median of the 41 landings north of 49.5 N (spacefacts.de).
- Every Kazakhstan point was reverse-geocoded (OpenStreetMap) to the expected district.
- USGS GNIS (carto.nationalmap.gov geonames service): Black Point, feature class Bench,
  Coconino County, 35.6878 N, 111.3599 W (6 km from the NASA ISS020-E-33530 image centre).
- Wikipedia "Aralkum Desert" centre (45.0, 60.5) for the dry Aral bed.
"""
import random

# --- Targets: real landing sites (what "landing-grade terrain" looks like) ---
MARS = {
    "Jezero (Perseverance)": (18.445, 77.451),
    "Gale (Curiosity)": (-4.589, 137.441),
    "Meridiani (Opportunity)": (-1.946, -5.527),
    "Gusev (Spirit)": (-14.568, 175.473),
    "Elysium (InSight)": (4.502, 135.623),
    "Chryse (Viking 1)": (22.27, -47.95),
    "Utopia (Viking 2)": (47.64, 134.29),
    "Ares Vallis (Pathfinder)": (19.13, -33.22),
    "Utopia (Zhurong)": (25.07, 109.93),
}
MOON = {
    "Apollo 11": (0.674, 23.473),
    "Apollo 12": (-3.012, -23.422),
    "Apollo 14": (-3.645, -17.471),
    "Apollo 15": (26.132, 3.634),
    "Apollo 16": (-8.973, 15.500),
    "Apollo 17": (20.191, 30.772),
    "Chang'e-3": (44.12, -19.51),
    "Chang'e-5": (43.06, -51.92),
    "Luna 17": (38.24, -35.00),
}

# --- Kazakhstan candidates ---
KAZAKHSTAN = {
    "Soyuz zone (Zhezkazgan)": (47.35, 69.60),
    "Soyuz zone (Arkalyk)": (50.956, 67.293),
    "Zhamanshin crater": (48.40, 60.967),
    "Bigach crater": (48.60, 82.00),
    "Shunak crater": (47.208, 72.760),
    "Chiyli crater": (49.175, 57.835),
    "Aralkum (dry Aral bed)": (45.00, 60.50),
    "Betpak-Dala": (46.033, 70.200),
    "Ustyurt plateau": (44.00, 55.90),
    "Mangystau (Bozzhyra)": (43.453, 54.087),
    "Inder salt dome": (48.55, 51.80),
    "Semipalatinsk (Balapan)": (49.935, 79.008),
    "Altyn-Emel (Aktau)": (44.040, 79.291),
    "Charyn canyon": (43.358, 79.093),
    "Kyzylkum (Kazakh part)": (43.90, 66.40),
    "Caspian lowland (Ryn)": (47.828, 49.666),
}

# --- Established analog / rover-test sites (must rank high if the method works) ---
REFERENCE = {
    "Black Point (D-RATS), AZ": (35.688, -111.360),
    "White Sands, NM": (32.779, -106.172),
    "Atacama (Yungay)": (-24.08, -69.92),
    "Mojave (Pisgah)": (34.746, -116.375),
    "Meteor Crater, AZ": (35.028, -111.023),
    "Qaidam (Lenghu)": (38.337, 92.906),
    "Makgadikgadi pans": (-20.75, 25.50),
    "Kilauea (Kau desert)": (19.33, -155.33),
    "MDRS Hanksville, UT": (38.406, -110.792),
    "Wadi Rum": (29.57, 35.42),
}

# Flattest natural surface on Earth: used to measure the DEM noise floor.
NOISE_FLOOR = {"Salar de Uyuni (noise floor)": (-20.20, -67.60)}

# --- Negative control: random points inside arid-region boxes ---
_ARID_BOXES = {  # name: (lat_min, lat_max, lon_min, lon_max)
    "Sahara": (18, 30, -10, 30),
    "Arabia": (18, 28, 42, 55),
    "Gobi": (40, 45, 95, 110),
    "GreatBasin": (36, 42, -119, -113),
    "Australia": (-30, -22, 122, 138),
    "Kalahari": (-27, -20, 15, 24),
    "Patagonia": (-48, -40, -70, -66),
    "Iran": (30, 35, 52, 60),
}


def random_controls(n_per_box=5, seed=2026):
    rng = random.Random(seed)
    out = {}
    for name, (a, b, c, d) in _ARID_BOXES.items():
        for i in range(n_per_box):
            out[f"ctrl {name} {i+1}"] = (round(rng.uniform(a, b), 3), round(rng.uniform(c, d), 3))
    return out
