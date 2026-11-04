"""D1 read-only reconciliation: no flight, guide, vehicle, CAD or solver campaign."""

from __future__ import annotations

import argparse
import copy
import hashlib
import itertools
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

for key in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[key] = "1"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml

from scripts.wo03_rp1_fin_precedent_replacement import component_screen, section

SOURCE = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
SOURCE_SHA = "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660"
STUDY = "configs/studies/rp1-fin-precedent-replacement.yaml"
FP = "docs/studies/rp1-fin-precedent-replacement/screen-record.json"
FR = "runs/wo03-rp1-fin-root-20261104-v1/record.json"
AD = "runs/wo03-rp1-attachment-definition-20261103-v2/record.json"
HIST = "build/wo03-g80-fin-loads-v3/results.json"


def sha(path: str) -> str:
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load_case(span: float, root: float, tip: float) -> dict:
    """Historical finite-aspect-ratio small-angle formula, DF3 once."""
    area = span * (root + tip) / 2
    ar = 2 * span**2 / area
    slope = 2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))
    arm = span * (root + 2 * tip) / (3 * (root + tip))
    force = 40000 * area * slope * math.radians(5) * 3
    return {
        "span_m": span,
        "root_m": root,
        "tip_m": tip,
        "area_m2": area,
        "centroid_m": arm,
        "CNa_per_rad": slope,
        "q_Pa": 40000,
        "alpha_deg": 5,
        "design_factor": 3,
        "force_N": force,
        "moment_Nm": force * arm,
    }


def tab_compliance(study: dict) -> dict:
    """Reciprocal cantilever at fixed motor-side cut: diagnostic, not installed."""
    g, p = study["geometry"], study["screening_inputs"]
    h, width = g["tab_depth_m"], g["tab_chord_m"]
    ei = section(study)["D_Nm"] * width
    kga = p["shear_correction_factor"] * p["plywood_G_Pa"] * width * g["plywood_thickness_min_m"]
    ff, fm, mm = h**3 / (3 * ei) + h / kga, h**2 / (2 * ei), h / ei
    f, m = (
        study["loads"]["factored_tip_force_equivalent_N"],
        study["loads"]["factored_root_moment_Nm"],
    )
    y, theta = ff * f + fm * m, fm * f + mm * m
    return {
        "matrix_SI": [[ff, fm], [fm, mm]],
        "EI_Nm2": ei,
        "kGA_N": kga,
        "translation_m": y,
        "rotation_rad": theta,
        "contribution_at_tip_mm": (y + g["span_m"] * theta) * 1000,
        "support": "Fixed motor-side cut only, not a validated installed support",
    }


def historical() -> dict:
    if not (ROOT / HIST).exists():
        return {
            "available": False,
            "compatible_with_RP1": False,
            "reason": "Ignored local historic artifacts unavailable; no recreated run.",
        }
    d = json.loads((ROOT / HIST).read_text())
    pins = d["identity_and_source_validation"]["input_sha256_before"]
    verified = {p: (ROOT / p).exists() and sha(p) == s for p, s in pins.items()}
    rows = []
    for name, case in d["cases"].items():
        phase = next(p for p in case["phase_loads"] if p["phase"] == "powered_predeployment")
        rows.append(
            {
                "case": name,
                "wind_north_mps": case["flight_case"]["wind_north_mps"],
                "wind_east_mps": case["flight_case"]["wind_east_mps"],
                "q_max_time_and_coincident_alpha": phase["max_dynamic_pressure"],
                "peak_coincident_load": phase["peak_estimated_load"],
            }
        )
    return {
        "available": True,
        "source": {"path": HIST, "sha256": sha(HIST)},
        "source_hashes_match": all(verified.values()),
        "input_verification": verified,
        "identity": d["candidate_identity"],
        "part_count": d["candidate_part_count"],
        "span_m": d["geometry"]["span_m"],
        "source_design_factor": d["design_factor"],
        "compatible_with_RP1": False,
        "cases": rows,
        "reason": "52-part 70 mm rectangular-fin modular vehicle, not 60 mm tapered RP1. Calm only; no current physical inertia/full flight. No transferred loads.",
    }


def run() -> dict:
    start, cpu = time.monotonic(), time.process_time()
    paths = [
        SOURCE,
        STUDY,
        FP,
        FR,
        AD,
        "scripts/wo03_rp1_fin_precedent_replacement.py",
        "configs/studies/rp1-integrated-ledger-audit.json",
        "configs/studies/rp1-joint-material-evidence.yaml",
        "scripts/wo03_rp1_load_attachment_decision.py",
    ]
    before = {p: sha(p) for p in paths}
    if before[SOURCE] != SOURCE_SHA:
        raise ValueError("Frozen AD1 identity changed")
    fp, fr, ad = [json.loads((ROOT / p).read_text()) for p in (FP, FR, AD)]
    if fp["adopted"] or fr["adopted"] or ad["adopted"]:
        raise ValueError("D1 reconciles unadopted sources only")
    if (
        before[STUDY] != fp["study_sha256"]
        or before["scripts/wo03_rp1_fin_precedent_replacement.py"] != fp["producer_sha256"]
    ):
        raise ValueError("Frozen FP1 method/input drift")
    study = yaml.safe_load((ROOT / STUDY).read_text())
    corners = []
    for ew, ec, gw, film in itertools.product(
        (1e9, 8e9), (30e9, 60e9), (100e6, 200e6), (30e-6, 50e-6)
    ):
        case = copy.deepcopy(study)
        case["screening_inputs"].update(plywood_E_Pa=ew, carbon_E_Pa=ec, plywood_G_Pa=gw)
        case["geometry"]["bond_each_face_min_m"] = film
        result = component_screen(case, 6400)
        corners.append(
            {"Ewood_Pa": ew, "Ecarbon_Pa": ec, "Gwood_Pa": gw, "film_m": film, "result": result}
        )
    current, old = load_case(0.06, 0.13, 0.065), load_case(0.09, 0.12, 0.06)
    ratio = current["moment_Nm"] / 8.83
    ordinary = []
    for label, item in [
        ("AD1 ideal bonded wedges", ad["fin"]["ideal_composite_strip_lower_deflection_only"][-1]),
        ("AD1 bare panel", ad["fin"]["bare_panel"]),
    ]:
        ordinary.append(
            {
                "label": label,
                "retained_moment_Nm": 8.83,
                "retained_panel_movement_mm": item["deflection_m"] * 1000,
                "retained_panel_stress_MPa": item["maximum_bending_Pa"] / 1e6,
                "unadopted_2_905_panel_movement_mm": item["deflection_m"] * 1000 * ratio,
                "unadopted_2_905_panel_stress_MPa": item["maximum_bending_Pa"] / 1e6 * ratio,
                "installed_pass": None,
                "scope": "Linear source-component scaling only; no new construction or adopted load.",
            }
        )
    nominal = fp["component_screens"][-1]
    panel = nominal["panel_bending_mm"] + nominal["panel_shear_mm"]
    result = {
        "id": "RP1-D1-load-attachment-decision-v1",
        "adopted_construction": False,
        "required_case": {
            "id": "RP1-FIN-LEGACY-883",
            "moment_Nm": 8.83,
            "force_N": 331.125,
            "design_factor_already_applied": 3,
            "origin": "Retained older-planform admission envelope, not measured operating maximum",
        },
        "unadopted_current_formula": current,
        "original_formula": old,
        "lower_load_adopted": False,
        "legacy_ratio": 8.83 / current["moment_Nm"],
        "historical_flight": historical(),
        "nominal_FP1_tab": tab_compliance(study),
        "FP1_panel_only_mm": panel,
        "nominal_complete_root_ceiling_mm": 1 - panel,
        "root_ceiling_is_evidence": False,
        "root_model": "Replace tab plus arbitrary allowance with complete validated root response; never add full root twice.",
        "material_corners": corners,
        "all_diagnostic_corners_pass": all(
            x["result"]["conditional_numeric_pass"] for x in corners
        ),
        "corners_are_verified_bounds": False,
        "ordinary_plywood": ordinary,
        "installed_tip_movement": None,
        "installed_strength": None,
        "physical_inertia": None,
        "mass_changes_g": 0,
        "new_construction_admitted": False,
        "decision": "Retain 8.83 Nm and 331.125 N once-factored; no fin correction admitted until compatible load/material/whole-root evidence.",
        "sources": before,
    }
    if {p: sha(p) for p in paths} != before:
        raise ValueError("Input changed during reconciliation")
    result["resources"] = {
        "cpu_s": time.process_time() - cpu,
        "wall_s": time.monotonic() - start,
        "packet_CPU_limit_s": 10,
        "packet_wall_stop_s": 20,
        "threads": 1,
        "material_cases": 16,
        "new_flight_guide_CAD_FEA_runs": 0,
    }
    if result["resources"]["wall_s"] > 20:
        raise RuntimeError("Wall budget exhausted: preserve as failed, no retry")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "runs/wo03-rp1-d1-20261104-v1/record.json"
    )
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve completed/stopped D1 record; no blind repeat")
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    value = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {k: value[k] for k in ("id", "decision", "all_diagnostic_corners_pass", "resources")}
        )
    )


if __name__ == "__main__":
    main()
