"""Define one supplier-stock F2 candidate, keeping frozen F1 untouched."""

from __future__ import annotations

import copy
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from src.vehicle.schema import load_vehicle


def define(output):
    d = yaml.safe_load(Path("configs/vehicle/candidates/g80-f1.yaml").read_text())
    d["id"] = "G80-F2-fixed-stock-v1"
    d["name"] = "G80-F2 supplier-stock fixed conventional candidate"
    d["airframe"]["body_diameter_m"] = 0.066802
    by = {p["id"]: p for p in d["parts"]}
    areal = 0.92 * 0.45359237 / 0.09290304
    density = areal / 0.006

    def box(id, z, size, mass, fn, parent="nose", offset=(0, 0)):
        p = copy.deepcopy(by["service_allowance"])
        p.update(
            id=id,
            parent=parent,
            position_m=z,
            geometry={"bbox_m": size},
            mass_kg=mass,
            learn=fn,
            lateral_offset_m=list(offset),
        )
        p["engineering"]["function"] = fn
        p["build"]["notes"] = fn
        p["cad"]["notes"] = fn
        return p

    for p in d["parts"]:
        if p["id"] == "nose":
            p["geometry"]["radius_m"] = 0.033401
        if p["id"] == "body":
            p["position_m"] = 0.458
            p["geometry"].update(
                length_m=0.762, radius_m=0.033401, inner_radius_m=0.032512, wall_m=0.000889
            )
            p["mass_kg"] = math.pi * (0.033401**2 - 0.032512**2) * 0.762 * 700
            p["cad"]["parameters"]["fin_slot_start_mm"] = 622
            p["cad"]["parameters"]["fin_slot_width_mm"] = 6.5
            p["build"]["cost_usd"] = 20.54
            p["cite"] = "https://locprecision.com/products/cardboard-airframes"
            p["learn"] = (
                "LOC BT-2.56 lower762mm body. Two full blanks charged here; upper section, sleeve and patch are cut from second blank. Fixed splice, no removable aft."
            )
        if p["id"] == "motor_tube":
            p["geometry"].update(radius_m=0.0156845, inner_radius_m=0.0145845, wall_m=0.0011)
            p["mass_kg"] = 0.024
            p["build"]["cost_usd"] = 7.49
            p["learn"] = (
                "AeroTech12912 cut165mm from305mm stock;1.235in OD retainer family,1.1mm wall nominal.24g installed budget covers unweighed tube. Bore tolerances unknown."
            )
            p["cite"] = "docs/wo03-g80-f2-suppliers.md"
        if p["id"] == "motor_retainer":
            p["mass_kg"] = 0.030
            p["build"]["cost_usd"] = 23.99
            p["learn"] = (
                "AeroTech19002 retainer,30g unweighed installed hardware budget. Current78010 shoulder/cap/nozzle mating drawing absent; envelope is not accepted contact geometry."
            )
            p["cite"] = "docs/wo03-g80-f2-suppliers.md"
        if p["id"] == "motor":
            p["build"]["cost_usd"] = 43.99
        if p["id"] == "fin_set":
            p["geometry"].update(thickness_m=0.006, radius_m=0.033401)
            p["mass_kg"] = 3 * 0.060 * (0.130 + 0.065) / 2 * areal
            p["cad"]["parameters"].update(
                tab_depth_mm=17.7165,
                tab_length_mm=109.8,
                root_gusset_span_mm=15,
                root_gusset_base_mm=6,
            )
            p["build"]["cost_usd"] = 69.75
            p["learn"] = (
                "Aircraft Spruce02-20850 nominal6mm twelve-ply Finnish birch; one24x48in sheet charged here for all plywood parts. Spanwise face grain. Incoming thickness5.8--6.2mm is a proposed inspection window, not supplier tolerance."
            )
            p["cite"] = "docs/wo03-g80-f2-suppliers.md"
        if p["id"] == "fin_tabs":
            p["mass_kg"] = 3 * 0.1098 * 0.0177165 * areal
            p["geometry"] = {"bbox_m": [0.1098, 0.0177165, 0.006]}
            p["build"][
                "notes"
            ] = "Integral material already charged in fullfinstock purchase; distinct mass from external panel, not free inventory."
        if p["id"] in ["forward_ring", "aft_ring"]:
            g = p["geometry"]
            g.update(
                radius_m=0.0323,
                inner_radius_m=0.0158845,
                length_m=0.0122 if p["id"] == "forward_ring" else 0.006,
            )
            vol = (
                math.pi
                * (0.0323**2 - 0.0158845**2)
                * (0.012 if p["id"] == "forward_ring" else 0.006)
            )
            if p["id"] == "forward_ring":
                vol -= 3 * 0.0065 * (0.0323 - 0.0158845) * 0.0074
            p["mass_kg"] = vol * density
            p["build"]["cost_usd"] = 0
            p["build"][
                "notes"
            ] = "Material included in one Spruce sheet. Forward ring two6mm plies+.2mm epoxy; blindnotches7.4mmdeep fromaftface,6.5mmwide;4.8mmfrontweb."
        if p["id"] == "nose_anchor_plate":
            p["geometry"].update(inner_radius_m=0.0225, length_m=0.0122)
            p["mass_kg"] = math.pi * (0.0306**2 - 0.0225**2) * 0.012 * density
            p["build"]["cost_usd"] = 0
            p["learn"] = (
                "Two-ply12mm plywood nose annulus with45mm service opening; source sheet charged with fins. Perimeter12mm adhesive lap to shoulder. Small eye washers intrude into opening; service path must be checked."
            )
        if p["id"] == "body_recovery_eye":
            p["mass_kg"] = 0.018
            p["learn"] = (
                "Two opposed provisional closed M4 eyes/nuts/washers at30/210deg, R23mm; each full-demand sensitivity. Finished part capacity/source remains held."
            )
        if p["id"] == "ring_bonds":
            p["mass_kg"] = 0.010
            p["learn"] = (
                "Ring/body and mount joints plus forward/nose ring laminate and nose perimeter adhesive. No free adhesive credit."
            )
        if p["id"] == "mount_external_shield":
            p["mass_kg"] = 0.010
            p["learn"] = (
                "10g bounded sector shielding/retention reserve. Fullannulus is not adopted; gaps around fin contacts and shield ends require thermal revalidation."
            )
        if p["id"] == "independent_recovery":
            p.update(
                position_m=0.170,
                geometry={"bbox_m": [0.04445, 0.02286, 0.008]},
                mass_kg=0.005,
                parent="nose",
                lateral_offset_m=[0, 0.005],
            )
            p["build"]["cost_usd"] = 15
            p["learn"] = (
                "Eggtimer Apogee singleapogee kit,44.45x22.86mm/about5g plusheightbudget8mm. Builtin screw power switch;1S only. Kit assembly and supply confirmation pending; no external switch assumed owned."
            )
            p["cite"] = "docs/wo03-g80-f2-suppliers.md"
        if p["id"] == "recovery_battery":
            p.update(
                position_m=0.193,
                geometry={"bbox_m": [0.030, 0.015, 0.005]},
                mass_kg=0.005,
                parent="nose",
                lateral_offset_m=[0.020, -0.010],
            )
            p["build"]["cost_usd"] = 19
            p["learn"] = (
                "Matching1S110mAh starterpack cell,5g envelopebudget.19USD allocated incremental bundlecost includes offvehicle charger; combinedcontroller+bundle34USD. Polarity/envelope/pulse verification pending, not owner inventory."
            )
        if p["id"] in ["recovery_carrier", "recovery_harness_wiring", "recovery_output_mount"]:
            p["parent"] = "nose"
            p["position_m"] = {
                "recovery_carrier": 0.165,
                "recovery_harness_wiring": 0.190,
                "recovery_output_mount": 0.225,
            }[p["id"]]
        if p["id"] == "electrical_harness":
            p["position_m"] = 0.110
            p["mass_kg"] = 0.011
            p["parent"] = "nose"
            p["learn"] = (
                "Nose logger wiring/connectors and retention;11g includes2g relocation increment. Separate from5g independent recovery harness."
            )
        if p["id"] == "parachute":
            p["position_m"] = 0.620
            p["geometry"] = {"length_m": 0.080, "radius_m": 0.025}
            p["learn"] = (
                "Purchased750mm canopy35g hypothesis,50mm diameter x80mm packed cylinder157mL, unmeasured. Combined packing allowance and extraction through splice checked separately."
            )
        if p["id"] == "shock_cord":
            p["position_m"] = 0.710
        if p["id"] == "recovery_connectors":
            p["position_m"] = 0.700
        if p["id"] == "recovery_protection":
            p["position_m"] = 0.700
    # Existing logger moves as a compact removable nose carrier; axial and lateral boxes stay explicit.
    loc = {
        "flight_computer": (0.085, [0, -0.011]),
        "battery": (0.085, [0, 0.008]),
        "high_g_accel": (0.085, [0, -0.020]),
        "imu": (0.113, [0, -0.020]),
        "baro": (0.137, [0, -0.020]),
        "micro_sd": (0.145, [0, 0.008]),
        "logger_regulator": (0.148, [-0.015, -0.010]),
        "logger_power_switch": (0.150, [0.025, 0]),
        "avionics_sled": (0.082, [0, 0]),
    }
    for id, (z, off) in loc.items():
        p = by[id]
        p.update(position_m=z, lateral_offset_m=off, parent="nose")
        if id == "logger_regulator":
            p["geometry"] = {"bbox_m": [0.025, 0.018, 0.008]}
        if id == "logger_power_switch":
            p["geometry"] = {"bbox_m": [0.012, 0.008, 0.010]}
        if id == "avionics_sled":
            p["geometry"] = {"bbox_m": [0.090, 0.030, 0.002]}
            p["learn"] = (
                "11g removable two-rail nose carrier, fasteners and battery straps; actual rails are not the solid envelope. Slides through45mm nose opening after eye/connector service."
            )
    # No independent external recovery switch: Apogee integrated screw switch included in board5g.
    d["parts"] = [p for p in d["parts"] if p["id"] != "recovery_power_switch"]
    upper = copy.deepcopy(by["body"])
    upper.update(
        id="upper_body",
        position_m=0.160,
        mass_kg=math.pi * (0.033401**2 - 0.032512**2) * 0.298 * 700,
    )
    upper["geometry"]["length_m"] = 0.298
    upper["cad"]["parameters"] = {}
    upper["build"]["cost_usd"] = 0
    upper["learn"] = (
        "298mm uppercut from second LOC762mm blank; fullblank cost already charged onbody. Permanent50mm overlap splice."
    )
    d["parts"].append(upper)
    sleeve = copy.deepcopy(upper)
    sleeve.update(
        id="body_splice",
        position_m=0.408,
        mass_kg=math.pi * (0.032225**2 - 0.031336**2) * 0.100 * 700,
    )
    sleeve["geometry"].update(
        length_m=0.100, radius_m=0.032225, inner_radius_m=0.031336, wall_m=0.000889
    )
    sleeve["learn"] = (
        "100mm split sleeve formed from same LOCoffcut to fitted64.45mm OD;50mm overlap each side of458mm splice. Seam patched inside. Finalconditionedfit required, not supplierdiameter."
    )
    d["parts"].append(sleeve)
    additions = [
        box(
            "splice_seam_patch",
            0.408,
            [0.100, 0.015, 0.000889],
            0.100 * 0.015 * 0.000889 * 700,
            "15mmwide internal paperseam patch fromoffcut; jointfixed, no extraction latch.",
            parent="body",
        ),
        box(
            "splice_adhesive",
            0.408,
            [0.100, 0.004, 0.004],
            0.005,
            "5g metered overlap/seam adhesive and tapered edges, counted separately.",
            parent="body",
        ),
        box(
            "root_gussets",
            1.075,
            [0.130, 0.015, 0.006],
            6 * 0.5 * 0.015 * 0.006 * 0.130 * density,
            "Six triangular6mm-stock root wedges,15mm radial x6mm base x130mm axial. Massseparate frompanels/tabs. Bevel/process/adhesive supported by localjointcheck.",
            parent="body",
        ),
        box(
            "root_extra_bond_finish",
            1.075,
            [0.130, 0.004, 0.004],
            0.004,
            "4g extra gusset adhesive/sealing increment beyond F1 internal/outer fillets.",
            parent="body",
        ),
        box(
            "recovery_bridle",
            1.055,
            [0.030, 0.020, 0.005],
            0.003,
            "3g opposed-eye bridle/termination increment; finished strength and unequalloading required.",
            parent="body",
        ),
        box(
            "nose_service_hardware",
            0.174,
            [0.020, 0.015, 0.008],
            0.003,
            "3g nosecarrier captive screws/retention/battery strainrelief increment; no loose ballast.",
            parent="nose",
        ),
    ]
    for p in additions:
        p["build"]["cost_usd"] = 0 if p["id"] in ["splice_seam_patch", "root_gussets"] else 2
    d["parts"] += additions
    for net in d["netlist"]:
        if net["net"] == "RECOVERY_INDEPENDENT":
            net["to"] = [i for i in net["to"] if i != "recovery_power_switch"]
        net["to"] = [i for i in net["to"] if i != "recovery_power_switch"]
    d["design"][
        "provenance"
    ] = "G80-F2 fixedstock followup. Conservative historicalG80curve hypothesis, full50g all aft; additional20g/motorCGprobe separate. No automatic motor/retainer fit, controller supply or physical acceptance."
    p = Path(output)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump(d, sort_keys=False))
    load_vehicle(p)
    return p


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Historical F2 starting-layout generator; never overwrite an existing specification."
    )
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; preserve frozen specifications")
    print(define(args.output))
