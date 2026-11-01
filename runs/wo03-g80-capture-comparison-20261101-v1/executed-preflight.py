"""Source-pinned hand preflight; no CAD, solver, or candidate adoption."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-capture-comparison.yaml"
OUT = ROOT / "build/wo03-g80-capture-comparison-v1"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    assert not cfg["budgets"]["cad_execution_authorized"]
    base = yaml.safe_load((ROOT / cfg["source_asrun_73_spec"]).read_text())
    assert len(base["parts"]) == 73
    parts = {p["id"]: p for p in base["parts"]}
    files = [
        CONFIG,
        Path(__file__).resolve(),
        ROOT / cfg["source_asrun_73_spec"],
        ROOT / cfg["source_72_keeper_record"],
        ROOT / cfg["source_mount_geometry"],
        ROOT / cfg["source_materials"],
        ROOT / "build/wo03-g80-keeper-service-v1/bridge.step",
        ROOT / "build/wo03-g80-keeper-service-v1/keeper.step",
    ]
    before = {str(p): sha(p) for p in files}
    service = cfg["service_retention_N"] * cfg["design_factor"]
    recovery = cfg["recovery_already_factored_N"]
    b = cfg["option_B"]
    c = cfg["option_C"]
    width = b["rail_tangential_mm"]
    depth = b["rail_radial_mm"]
    pin = b["cross_pin_shaft_mm"]
    hole = b["cross_pin_hole_mm"]
    wooden = 10.0
    g11 = 25.0
    length = c["strip_station_end_mm"] - c["strip_station_start_mm"]
    striparea = c["strip_count"] * c["strip_radial_mm"] * c["strip_tangential_mm"]
    record = {
        "status": "preliminary_hand_screen_no_cad",
        "source_sha256_before": before,
        "source_sha256_after": {str(p): sha(p) for p in files},
        "72_identity": cfg["source_72_identity"],
        "73_corrected_identity": cfg["source_73_metadata_corrected_identity"],
        "73_asrun_yaml_not_corrected_identity": True,
        "73_source_parts": len(parts),
        "73_asrun_source_mass_kg": sum(float(p.get("mass_kg") or 0) for p in base["parts"]),
        "full_growth_kg_separate": 0.05,
        "B": {
            "single_pin_factored_N": service,
            "pin_bearing_MPa": service / (pin * width),
            "rail_net_section_MPa": service / ((depth - hole) * width),
            "optimistic_bearing_d_min_mm": service / (wooden * width),
            "optimistic_net_hole_d_max_mm": depth - service / (wooden * width),
            "screen_MPa": wooden,
            "screen_basis": "generic estimated weak direction; not bearing or net allowable",
            "cap_bore_shift_chord_mm": 25.5,
            "six_ideal_lug_blank_mass_g": 6 * 7 * 2 * 15 * 1850e-6,
            "engineering_status": "unslotted single unreinforced rail conditional screen fails; no CAD",
        },
        "C": {
            "already_factored_recovery_N": recovery,
            "strip_gross_area_mm2": striparea,
            "uniform_equal_share_axial_MPa": recovery / striparea,
            "one_strip_axial_MPa": recovery / (c["strip_radial_mm"] * c["strip_tangential_mm"]),
            "one_strip_450N_axial_MPa": service / (c["strip_radial_mm"] * c["strip_tangential_mm"]),
            "g11_screen_MPa": g11,
            "screen_basis": "generic estimated hot strength, not directional/joint allowable",
            "six_untrimmed_blank_volume_mm3": striparea * length,
            "six_untrimmed_blank_mass_g": striparea * length * c["g11_density_kg_m3"] * 1e-6,
            "ring_joint_pin_adhesive_mass_g": None,
            "installed_net_mass_change_g": None,
            "full_vehicle_cg_tensor": None,
            "force_transfer_and_clearance": "unresolved, no mechanical ground credit",
        },
        "source_items_kg": {
            k: parts[k].get("mass_kg")
            for k in (
                "parachute",
                "motor_mount",
                "service_keeper",
                "service_bridge",
                "adhesive_finish",
                "fin_bonds",
                "incremental_mount_gap_epoxy_upper_budget",
                "retention_locking_materials_reserve",
                "canopy_line_connector_sensitivity",
            )
        },
        "native_cad_invoked": False,
        "qualification": False,
    }
    OUT.mkdir(exist_ok=False)
    (OUT / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "B": record["B"],
                "C": record["C"],
                "source_mass_kg": record["73_asrun_source_mass_kg"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
