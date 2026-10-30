"""Generate an isolated WO-03 motor-mount load-path proposal study."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cad.assembly import export_vehicle, rigid_intersections
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Vehicle, load_vehicle, vehicle_input_paths


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _proposal_copy(vehicle: Vehicle, study: dict[str, Any]) -> tuple[Vehicle, set[str]]:
    data = vehicle.model_dump(by_alias=True)
    parts = {part["id"]: part for part in data["parts"]}
    liner = parts["motor_liner"]
    retention = parts["retention"]
    if vehicle.tvc:
        front = retention["position_m"] - float(study["tvc_retention_clearance_m"])
        aft = float(study["tvc_liner_aft_station_m"])
    else:
        front = parts["motor_mount"]["position_m"]
        aft = float(study["fixed_liner_aft_station_m"])
    if front >= aft:
        raise ValueError(f"{vehicle.id}: proposed liner has non-positive length")
    liner["position_m"] = front
    liner["geometry"]["length_m"] = aft - front
    liner["cad_mass"] = None
    retention["geometry"]["radius_m"] = liner["geometry"]["inner_radius_m"]
    retention["geometry"].pop("od_m", None)
    retention["geometry"].pop("diameter_m", None)
    retention["cad_mass"] = None
    changed = {"motor_liner", "retention"}
    return Vehicle.model_validate(data), changed


def _reconcile_copy(vehicle: Vehicle, changed: set[str], manifest: dict[str, Any]) -> Vehicle:
    rows = {row["id"]: row for row in manifest["parts"]}
    data = vehicle.model_dump(by_alias=True)
    for item in data["parts"]:
        if item["id"] not in changed:
            continue
        row = rows[item["id"]]
        density = DENSITY_KG_M3[item["material"]]
        item["mass_kg"] = row["properties"]["volume_m3"] * density
        item["density_kg_m3"] = None
        item["cad_mass"] = {
            "shape_sha256": row["shape_sha256"],
            "volume_m3": row["properties"]["volume_m3"],
            "cg_local_body_m": row["properties"]["cg_local_body_m"],
            "inertia_per_kg_m2": row["properties"]["inertia_per_kg_m2"],
            "basis": row["properties"]["basis"],
        }
        item["cg_offset_m"] = -row["properties"]["cg_local_body_m"][0]
    return Vehicle.model_validate(data)


def _tube_properties(liner: Any) -> dict[str, float]:
    ro = float(liner.geometry["radius_m"])
    ri = float(liner.geometry["inner_radius_m"])
    area = math.pi * (ro**2 - ri**2)
    second_moment = math.pi / 4 * (ro**4 - ri**4)
    return {
        "outer_radius_m": ro,
        "inner_radius_m": ri,
        "area_m2": area,
        "second_moment_m4": second_moment,
    }


def _bond_screen(
    force_n: float, radius_m: float, length_m: float, allowable_pa: float, df: float
) -> dict[str, float | str]:
    area = 2 * math.pi * radius_m * length_m
    stress = force_n / area
    allowable_after_df = allowable_pa / df
    return {
        "radius_m": radius_m,
        "effective_length_m": length_m,
        "cylindrical_shear_area_m2": area,
        "load_n": force_n,
        "average_shear_stress_pa": stress,
        "provisional_allowable_pa": allowable_pa,
        "design_factor": df,
        "allowable_after_design_factor_pa": allowable_after_df,
        "screen_margin": allowable_after_df / stress - 1,
        "status": "screen-pass" if stress <= allowable_after_df else "screen-fail",
    }


def _analyze(
    baseline: Vehicle,
    proposal: Vehicle,
    structural: dict[str, Any],
    engineering: dict[str, Any],
    study: dict[str, Any],
    cad_manifest: dict[str, Any],
    solids: dict[str, Any],
) -> dict[str, Any]:
    parts = {part.id: part for part in proposal.parts}
    liner, mount, retention = parts["motor_liner"], parts["motor_mount"], parts["retention"]
    force = float(structural["peak_scaled_thrust_n"])
    df = float(study["design_factor"])
    props = _tube_properties(liner)
    area = props["area_m2"]
    stress = force / area
    phenolic = engineering["materials"]["phenolic"]
    allowable = float(phenolic["strength_pa"])
    compression_allowable = allowable / df
    buckling_length = float(liner.geometry["length_m"])
    euler_load = (
        math.pi**2
        * float(phenolic["youngs_pa"])
        * props["second_moment_m4"]
        / (float(study["buckling_effective_length_factor"]) * buckling_length) ** 2
    )
    buckling_bound = euler_load * float(study["buckling_imperfection_factor"])
    buckling_after_df = buckling_bound / df
    ret_length = float(study["retention_stop_effective_bond_length_mm"]) / 1000
    bondline_gap = float(study["nominal_annular_bondline_radial_clearance_mm"]) / 1000
    retention_bond = _bond_screen(
        force,
        float(liner.geometry["inner_radius_m"]),
        ret_length,
        float(study["bond_shear_allowable_pa"]),
        df,
    )
    mount_length = (
        float(study["tvc_cradle_effective_bond_length_mm"])
        if proposal.tvc
        else float(study["fixed_mount_effective_bond_length_mm"])
    ) / 1000
    liner_mount = _bond_screen(
        force,
        (float(liner.geometry["radius_m"]) + float(mount.geometry["inner_radius_m"])) / 2,
        mount_length,
        float(study["bond_shear_allowable_pa"]),
        df,
    )
    additional_bonds = []
    if proposal.tvc:
        inner_gimbal = parts["gimbal_inner"]
        cradle_gimbal = _bond_screen(
            force,
            (float(mount.geometry["radius_m"]) + float(inner_gimbal.geometry["inner_radius_m"]))
            / 2,
            float(study["tvc_inner_gimbal_effective_bond_length_mm"]) / 1000,
            float(study["bond_shear_allowable_pa"]),
            df,
        )
        additional_bonds.append(
            {"interface": "motor_mount_cradle_to_gimbal_inner", **cradle_gimbal}
        )

    before = mass_properties(baseline)
    after = mass_properties(proposal)
    delta_i = after.inertia_kg_m2 - before.inertia_kg_m2
    rows = {row["id"]: row for row in cad_manifest["parts"]}
    identities = {part.id: rows[part.id]["shape_sha256"] for part in proposal.parts}
    collisions = rigid_intersections(proposal, solids)
    return {
        "configuration_id": proposal.id,
        "vehicle_id": proposal.id,
        "proposal_only": True,
        "changed_parts": ["motor_liner", "retention"],
        "geometry": {
            "liner_front_station_m": liner.position_m,
            "liner_aft_station_m": liner.position_m + float(liner.geometry["length_m"]),
            "liner_length_m": float(liner.geometry["length_m"]),
            "retention_outer_radius_m": float(retention.geometry["radius_m"]),
            "liner_inner_radius_m": float(liner.geometry["inner_radius_m"]),
            "nominal_liner_outer_to_mount_bore_radial_gap_mm": (
                float(mount.geometry["inner_radius_m"]) - float(liner.geometry["radius_m"])
            )
            * 1000,
            "assumed_annular_bondline_radial_clearance_mm": bondline_gap * 1000,
        },
        "structural_design_load": {
            "peak_scaled_thrust_n": force,
            "source_record": "WO-03 engineering structural peak_scaled_thrust_n (configured 1.15 thrust multiplier already applied)",
            "design_factor": df,
        },
        "liner_hand_screen": {
            **props,
            "axial_compression_stress_pa": stress,
            "phenolic_strength_bound_pa": allowable,
            "allowable_after_design_factor_pa": compression_allowable,
            "compression_screen_margin": compression_allowable / stress - 1,
            "compression_status": (
                "screen-pass" if stress <= compression_allowable else "screen-fail"
            ),
            "euler_pinned_load_n": euler_load,
            "imperfection_factor": float(study["buckling_imperfection_factor"]),
            "buckling_load_after_imperfection_n": buckling_bound,
            "buckling_allowable_after_design_factor_n": buckling_after_df,
            "buckling_screen_margin": buckling_after_df / force - 1,
            "buckling_status": "screen-pass" if buckling_after_df >= force else "screen-fail",
            "assumptions": "Deliberately conservative full-clear-liner-length pin-ended Euler sensitivity for a thin circular tube, homogeneous linear-elastic phenolic E at provisional 3 GPa, K=1.0 and 0.1 imperfection knockdown before DF=3. Actual tube segments ahead of and behind the internal stop have different axial loads and support spans; fixed-mode centering rings may share load. This model represents neither, so a failed bound does not establish that the actual G54 tube buckles. Local shell buckling, end crushing, thermal degradation, ovality, joint support, case contact and material anisotropy are omitted; this is not a qualified strength result.",
        },
        "bond_shear_screens": {
            "retention_stop_to_liner_id": retention_bond,
            "liner_od_to_mount_bond_annuli": liner_mount,
            "additional_tvc_interfaces": additional_bonds,
            "caveat": "Uniform average cylindrical shear only. 0.2 mm bond line, adhesive wet-out, eccentric peel, edge effects, thermal cycling and substrate failure are unverified; apply load throughout each listed interface as an intentionally simple bound.",
        },
        "load_path_before": (
            "The axial retention disk has 18 mm radius (36 mm OD) at the fixed-mode forward station and is spatially separated from the 28.5 mm-radius three-rail mount; the liner starts at the motor front. No continuous load-transfer interface is established from the disk into the mount."
            if not proposal.tvc
            else "The retention stop is separated from the liner start, and no verified load-transfer path is established from stop into the motor cradle, inner gimbal, pivots and frame."
        ),
        "load_path_proposal": (
            "Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> two fixed centering-ring annular bonds (3 mm each) -> motor-mount rails/rings -> aft-shell joints. The mount-to-shell joints remain unqualified."
            if not proposal.tvc
            else "Motor front stop -> 4 mm cylindrical bond at liner ID -> extended phenolic liner -> 18 mm cradle annular bond -> 6 mm motor-cradle/inner-gimbal bond -> pivot pins -> outer frame. Retention, all bonds, pin bearing/shear and frame closure remain unqualified."
        ),
        "neutral_rigid_intersections": {
            "count": len(collisions),
            "pairs": collisions,
            "checked": True,
            "interpretation": "Geometric BRep overlap diagnostic on proposed copy only; touching/bonded surfaces and thin bond layers are not qualified by this check.",
        },
        "mass_properties_reconciled_copy": {
            "basis": "Changed liner and retention masses and local CAD CG/inertia refreshed from generated proposal CAD volumes/properties using configured material densities; unchanged parts retain resolved source properties.",
            "baseline": {
                "mass_kg": before.mass_kg,
                "cg_m": before.cg_m,
                "inertia_kg_m2": before.inertia_kg_m2.tolist(),
            },
            "proposal": {
                "mass_kg": after.mass_kg,
                "cg_m": after.cg_m,
                "inertia_kg_m2": after.inertia_kg_m2.tolist(),
            },
            "delta": {
                "mass_kg": after.mass_kg - before.mass_kg,
                "cg_m": after.cg_m - before.cg_m,
                "inertia_kg_m2": delta_i.tolist(),
            },
        },
        "cad_identity": identities,
        "acceptance": "open",
        "acceptance_passed": False,
        "active_adoption": False,
        "flight_ready": False,
        "physical_fit_verified": False,
        "open_items": [
            "Annular geometry and 0.2 mm bondline require detailed CAD, tolerance, material and adhesive verification.",
            "Purchased motor case/closure capture and bidirectional retention remain unresolved.",
            "Fixed mount-to-aft-shell joints, TVC pivot pins/bearings and outer-frame load path remain unqualified.",
            "Local ring bending, peel, crushing, thermal properties and FEA/coupon/proof tests remain open.",
            "This simplified load screen does not claim continuous TVC motion clearance or wiring proof.",
        ],
    }


def generate(config_path: Path = Path("configs/studies/wo03-mount-loadpath.yaml")) -> Path:
    root = Path.cwd()
    config_path = config_path if config_path.is_absolute() else root / config_path
    study_bytes = config_path.read_bytes()
    study = yaml.safe_load(study_bytes)
    engineering_path = root / study["engineering_inputs"]
    engineering_bytes = engineering_path.read_bytes()
    engineering = yaml.safe_load(engineering_bytes)
    evidence_path = root / study["engineering_evidence"]
    evidence = json.loads(evidence_path.read_text())
    structural_by_vehicle = {item["vehicle"]: item["structural"] for item in evidence["vehicles"]}
    source_paths = {
        config_path,
        engineering_path,
        evidence_path,
        root / "scripts/wo03_mount_loadpath_study.py",
        root / "src/cad/assembly.py",
        root / "src/cad/parts.py",
        root / "src/vehicle/schema.py",
        root / "src/vehicle/geometry.py",
        root / "src/vehicle/mass.py",
        root / "src/vehicle/materials.py",
    }
    vehicles = []
    for config_id, relpath in study["configurations"].items():
        spec_path = root / relpath
        vehicle = load_vehicle(spec_path)
        source_paths.update(vehicle_input_paths(spec_path))
        vehicles.append((config_id, vehicle))
    hashes_before = {
        str(path.relative_to(root)): _sha256(path) for path in sorted(source_paths) if path.exists()
    }
    outdir = root / "build/wo03-mount-loadpath"
    outdir.mkdir(parents=True, exist_ok=True)
    reports = []
    for config_id, baseline in vehicles:
        proposal, changed = _proposal_copy(baseline, study)
        cad_folder = outdir / proposal.id / "cad"
        manifest, solids = export_vehicle(proposal, cad_folder, export=False)
        reconciled = _reconcile_copy(proposal, changed, manifest)
        report = _analyze(
            baseline,
            reconciled,
            structural_by_vehicle[baseline.id],
            engineering,
            study,
            manifest,
            solids,
        )
        report["configuration_id"] = config_id
        report["resolved_spec_sha256"] = hashlib.sha256(
            baseline.model_dump_json(by_alias=True).encode()
        ).hexdigest()
        report["proposal_spec_sha256"] = hashlib.sha256(
            reconciled.model_dump_json(by_alias=True).encode()
        ).hexdigest()
        report["structural_source_record"] = study["engineering_evidence"]
        report["structural_source_run_id"] = evidence.get("run_id")
        report_path = outdir / f"{config_id}.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        reports.append(
            {
                "configuration_id": config_id,
                "vehicle_id": baseline.id,
                "report": str(report_path.relative_to(root)),
            }
        )
    hashes_after = {
        str(path.relative_to(root)): _sha256(path) for path in sorted(source_paths) if path.exists()
    }
    run_id = "wo03-mount-loadpath-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    record = {
        "run_id": run_id,
        "work_order": "03",
        "study_config_sha256": hashlib.sha256(study_bytes).hexdigest(),
        "engineering_inputs_sha256": hashlib.sha256(engineering_bytes).hexdigest(),
        "engineering_evidence_sha256": _sha256(evidence_path),
        "input_sha256_before": hashes_before,
        "input_sha256_after": hashes_after,
        "inputs_unchanged": hashes_before == hashes_after,
        "vehicles": reports,
        "acceptance": "open",
        "acceptance_passed": False,
        "active_adoption": False,
        "flight_ready": False,
        "physical_fit_verified": False,
        "cost_usd": 0,
    }
    record_path = root / "runs" / run_id / "record.json"
    record_path.parent.mkdir(parents=True, exist_ok=False)
    record_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    _write_doc(root / "docs/wo03-mount-loadpath.md", record, reports, outdir)
    return record_path


def _write_doc(
    path: Path, record: dict[str, Any], reports: list[dict[str, str]], outdir: Path
) -> None:
    def fmt(value: Any) -> str:
        return "n/a" if value is None else f"{value:.3f}"

    lines = [
        "# WO-03 motor-mount load-path proposal",
        "",
        "This is an isolated geometry and hand-screen proposal. It changes resolved vehicle copies only. No active vehicle or CAD source is modified; no hardware adoption, physical-fit, strength qualification, or flight-readiness claim is made.",
        "",
        f"Run: `{record['run_id']}`; inputs unchanged: `{record['inputs_unchanged']}`; acceptance: **open / false**; active adoption: **false**; flight ready: **false**; cost: $0.",
        "",
        "## Proposal",
        "",
        "Fixed configurations extend the existing phenolic liner from the actual motor-mount front to 800 mm, retaining the two 3 mm centering-ring annuli. TVC configurations extend it from 4 mm ahead of the existing retention stop to 800 mm, into the 18 mm-long cradle annulus. The existing retention radius is 18 mm (36 mm OD); in the copy, its outer radius is set to the liner inner radius (14.7 mm, 29.4 mm OD in current resolved specs). A nominal 0.2 mm radial annular gap is treated as a bondline assumption, not a measured or detailed adhesive layer.",
        "",
        "Before, the 36 mm OD (18 mm radius) forward stop at the fixed-mode station is spatially disconnected from the three-rail mount, while the liner starts at the motor front. In TVC modes, no verified stop-to-liner-to-cradle-to-gimbal-to-pin load path is established. Proposed paths are shown per mode below; mount-to-shell retention, pin/frame transfer and actual motor case capture remain open.",
        "",
        "## Quantitative pilot",
        "",
        "The axial tube screen uses `A = π(ro²−ri²)`, `I = π(ro⁴−ri⁴)/4`, `σ = F/A`, and pinned Euler `Pcr = π²EI/(KL)²`. Peak thrust comes from the linked executed WO-03 structural report, whose `peak_scaled_thrust_n` already applies its configured 1.15 multiplier. Strength/bond screens use design factor 3. Phenolic E=3 GPa and strength=20 MPa, epoxy shear=2 MPa are provisional engineering-input bounds. Euler uses full clear liner length with K=1 and a stated 0.1 imperfection reduction before DF as a deliberately conservative load-path sensitivity only: segments ahead of/behind the internal stop have different axial loads and support spans, and the fixed centering rings may share load. Thus a failed G54 full-length bound does not establish that the actual tube buckles. No calibrated imperfection or support restraint is available. Cylindrical bond area is `2πrL` under uniform average shear. Local bending, peel, crushing, thermal property degradation, tolerance, adhesive process and joint failure are not represented.",
        "",
        "| Mode | Peak scaled thrust (N) | Proposed liner (mm) | Compression screen margin | Buckling screen margin | Stop bond margin | Liner/mount bond margin | TVC cradle/inner bond margin | Δmass (g) | ΔCG (mm) | Acceptance |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for item in reports:
        report = json.loads((outdir / f"{item['configuration_id']}.json").read_text())
        tube = report["liner_hand_screen"]
        bonds = report["bond_shear_screens"]
        inner = bonds["additional_tvc_interfaces"]
        lines.append(
            f"| {item['configuration_id']} | {report['structural_design_load']['peak_scaled_thrust_n']:.2f} | {report['geometry']['liner_front_station_m']*1000:.1f}–{report['geometry']['liner_aft_station_m']*1000:.1f} | {fmt(tube['compression_screen_margin'])} | {fmt(tube['buckling_screen_margin'])} | {fmt(bonds['retention_stop_to_liner_id']['screen_margin'])} | {fmt(bonds['liner_od_to_mount_bond_annuli']['screen_margin'])} | {fmt(inner[0]['screen_margin'] if inner else None)} | {report['mass_properties_reconciled_copy']['delta']['mass_kg']*1000:.2f} | {report['mass_properties_reconciled_copy']['delta']['cg_m']*1000:.2f} | open |"
        )
    lines += [
        "",
        "All computed margins are preliminary average-stress/buckling screens, not acceptance evidence. A screen-pass does not establish real load transfer. TVC final bond margin represents only cradle-to-inner-gimbal annular shear; pin and outer-frame capacity are unavailable.",
        "",
        "## Per-mode load paths and limitations",
        "",
    ]
    for item in reports:
        report = json.loads((outdir / f"{item['configuration_id']}.json").read_text())
        lines += [
            f"### {item['configuration_id']}",
            "",
            f"Before: {report['load_path_before']}",
            "",
            f"Proposal: {report['load_path_proposal']}",
            "",
            f"Neutral BRep overlap pairs in proposed copy: {report['neutral_rigid_intersections']['count']}; touching surfaces and bond layers are not resolved by this diagnostic. Full mass/CG/inertia change is in `{item['report']}`.",
            "",
        ]
    lines += [
        "## Open closure work",
        "",
        "- The stop-ring capture geometry must match the exact purchased motor case and closure and sustain bidirectional axial load.",
        "- Resolve annular bond preparation, adhesive, thickness, cure, thermal cycle, voiding and load sharing; test representative coupons and assembled proof articles.",
        "- Verify local retainer and centering-ring bending, liner-end bearing/crush, shell attachment, gimbal pins/bearings, outer frame and combined TVC loads with targeted FEA and physical tests.",
        "- The report checks neither continuous motion nor wiring access, hot fit, vibration, or stability/flight effects. All WO-03 acceptance remains open.",
        "",
        "Source hashes and resolved/proposal identities are stored in the run record and per-configuration JSON. No original spec/CAD inputs are edited.",
        "",
    ]
    path.write_text("\n".join(lines))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-mount-loadpath.yaml")
    )
    args = parser.parse_args()
    path = generate(args.config)
    print(path)
    record = json.loads(path.read_text())
    if not record["inputs_unchanged"]:
        print("Source provenance check failed: inputs changed during the run.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
