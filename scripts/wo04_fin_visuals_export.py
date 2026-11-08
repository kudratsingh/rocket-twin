"""Export recorded fin dimensions for an unadopted schematic preview, never CAD/physics."""

import hashlib
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
SPEC = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
FP = "configs/studies/rp1-fin-precedent-replacement.yaml"
FR = "configs/studies/rp1-fin-root-replacement.yaml"


def build() -> dict:
    paths = [SOURCE, FP, FR]
    pins = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}
    if pins[SOURCE] != SPEC:
        raise ValueError("Frozen AD1 source changed")
    source, fp, fr = [yaml.safe_load((ROOT / p).read_text()) for p in paths]
    parts = {p["id"]: p for p in source["parts"]}
    if fr.get("adopted") is not False or fp["admission"]["active_vehicle_change"] is not False:
        raise ValueError("This preview is restricted to the recorded unadopted studies")
    if fp["source_sha256"] != SPEC or fr["source_sha256"] != SPEC:
        raise ValueError("Unmatched alternative source")
    common = {
        "root_m": 0.13,
        "tip_m": 0.065,
        "span_m": 0.06,
        "sweep_m": 0.045,
        "tab_depth_m": 0.017451,
        "tab_offset_m": 0.0052,
        "tab_chord_m": 0.1094,
    }
    if any(
        abs(fp["geometry"][k] - common[k]) > 1e-9
        for k in ["root_m", "tip_m", "span_m", "sweep_m", "tab_depth_m", "tab_chord_m"]
    ):
        raise ValueError("Recorded alternative planform changed; revise preview definition")
    if any(
        fr["construction"]["planform_mm"][k] / 1000 != common[k + "_m"]
        for k in ["root", "tip", "span", "sweep"]
    ):
        raise ValueError("FR1 planform mismatch")
    return {
        "id": "rp1-recorded-fin-visuals-v1",
        "configuration_id": "G80-F2-RP1-AD1-definition-v2",
        "specification_sha256": SPEC,
        "units": "m",
        "source_pins": pins,
        "scope": "One source-dimensioned conceptual fin blank; not finished CAD, a complete replacement assembly, installed strength or an adopted vehicle.",
        "profile": common,
        "studies": [
            {
                "id": "AD1",
                "record_id": "G80-F2-RP1-AD1-definition-v2",
                "label": "Current AD1: plywood",
                "core_m": parts["fin_set"]["geometry"]["thickness_m"],
                "skin_each_m": 0,
                "bond_each_m": 0,
                "skin_span_m": 0,
                "status": "Recorded panel screen fails; installed joint evidence missing.",
            },
            {
                "id": "FP1",
                "record_id": fp["id"],
                "label": "FP1: carbon-faced plywood",
                "core_m": 0.005,
                "skin_each_m": 0.0005,
                "bond_each_m": 0.00004,
                "skin_span_m": fp["geometry"]["skin_span_m"],
                "status": "Nominal component screen conditional; material sensitivities fail. Extra attachment movement unverified.",
            },
            {
                "id": "FR1",
                "record_id": fr["id"],
                "label": "FR1: solid carbon",
                "core_m": fr["stock"]["nominal_thickness_mm"] / 1000,
                "skin_each_m": 0,
                "bond_each_m": 0,
                "skin_span_m": 0,
                "status": "Stopped: finite-support movement and body-bond screens fail.",
            },
        ],
        "missing": [
            "Finished notch/edge profiles and manufacturing details",
            "Qualified skin/bond properties and final adhesive selection",
            "Complete installed attachment geometry, mass, balance, thermal and flutter acceptance",
        ],
        "nominal_basis": "Nominal dimensions from recorded studies; FP1 bond film0.04mm is midpoint of its proposed0.03–0.05mm range, not measured stock.",
    }


if __name__ == "__main__":
    target = ROOT / "web/src/data/rp1FinVisuals.json"
    target.write_text(json.dumps(build(), indent=2) + "\n")
    print(target)
