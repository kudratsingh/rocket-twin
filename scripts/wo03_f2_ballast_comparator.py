"""One declared retained-washer comparator; no architecture search."""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse

import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Vehicle, load_vehicle

parser = argparse.ArgumentParser(
    description="Historical initial F2 ballast comparator; write only a new study output."
)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error("output already exists; frozen specifications are not overwritten")
v = load_vehicle("configs/vehicle/candidates/g80-f2.yaml")
d = v.model_dump(by_alias=True, exclude_none=True)
d["id"] = "G80-F2-fixed-stock-ballast-v1"
d["parts"][0]["parent"] = None
for p in d["parts"]:
    if p["id"] == "fin_set":
        p["geometry"]["span_m"] = 0.060
        p["mass_kg"] *= 60 / 65
cap = copy.deepcopy(next(p for p in d["parts"] if p["id"] == "nose_service_hardware"))
cap.update(
    id="ballast_capsule",
    position_m=0.040,
    geometry={"bbox_m": [0.035, 0.017, 0.017]},
    mass_kg=0.007,
    learn="7g captive ASA capsule, M5 throughbolt/nut and nosecarrier attachment. Steel washers retained through central bolt; no loose ballast. Required receiving dimensions and proof remain open.",
)
cap["build"]["cost_usd"] = 3
d["parts"].append(cap)
vb = Vehicle.model_validate(d)
p = mass_properties(vb)
target = center_of_pressure(vb) - 1.1 * vb.airframe["body_diameter_m"]
m = p.mass_kg + 0.07
moment = p.mass_kg * p.cg_m + 0.07 * 1.25 + 0.1282 * 0.0128
w = math.pi * (0.0075**2 - 0.00265**2) * 0.0012 * 8000
a = w * 0.0006
b = w * (0.045 - target)
c = moment - target * m
root = (-b - math.sqrt(b * b - 4 * a * c)) / (2 * a)
n = math.ceil(root)
ballast = copy.deepcopy(cap)
ballast.update(
    id="nose_ballast",
    position_m=0.045,
    geometry={"length_m": n * 0.0012, "radius_m": 0.0075, "inner_radius_m": 0.00265},
    mass_kg=n * w,
    learn=f"{n} BelMetric WFE5X15SS/DIN9021 M5 stainlesswashers:15OD/5.3ID/1.2mm source nominal.8000kg/m3 density estimate, actual stack mass required; no loose washers.",
)
ballast["cite"] = "https://belmetric.com/content/A-PDF_Drawings/WFE5X15SS.pdf"
ballast["build"]["cost_usd"] = round(n * 0.25, 2)
ballast["cad"]["generator"] = "tube"
ballast["cad"]["role"] = "purchased_envelope"
d["parts"].append(ballast)
path = args.output
path.parent.mkdir(parents=True, exist_ok=True)
path.write_text(yaml.safe_dump(d, sort_keys=False))
load_vehicle(path)
print(
    "washers",
    n,
    "steel_g",
    n * w * 1000,
    "capture_g",
    7,
    "algebraic_target_cal",
    1.1,
    "output",
    path,
)
