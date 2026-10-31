"""Regenerate exact candidate solids and attempt conformal bonded mesh."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cadquery as cq
import yaml

from scripts.wo03_fit_correction_study import _reconcile_copy
from src.analysis.bonded_support import (
    annular_brace_sensitivity,
    bonded_bar_fixture,
    bonded_path_hand_budget,
    fragment_and_mesh,
    overlap_beam_spring,
    overlap_known_case,
    peel_foundation_known_case,
)
from src.cad.assembly import export_vehicle
from src.cad.parts import local_shape, shape_digest
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle, load_vehicle


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reduced_study(candidate: Path, output: Path) -> dict:
    """Bounded finite-overlap decision screen; no active spec or CAD mutation."""
    from src.analysis.motor_support import _rail_section_mm

    study_path = Path("configs/studies/wo03-bonded-support.yaml")
    study = yaml.safe_load(study_path.read_text())
    cfg = study["bounded_load_transfer"]
    paper_e = study["materials"]["cardboard"]["young_hot_mpa"]
    plywood_e = study["materials"]["plywood"]["young_hot_mpa"]
    vehicle = load_vehicle(candidate)
    assert vehicle.motor and vehicle.motor.curve
    paths = [
        candidate,
        study_path,
        Path(__file__),
        Path("src/analysis/bonded_support.py"),
        Path("src/analysis/motor_support.py"),
        Path(vehicle.motor.curve),
        *sorted(Path("src/cad").glob("*.py")),
        Path("src/vehicle/schema.py"),
    ]
    hashes = {str(p): sha(p) for p in paths}
    output.mkdir(parents=True, exist_ok=False)
    critical = [
        p
        for p in vehicle.parts
        if p.id in ("body_upper", "aft_shell", "motor_mount")
        or p.id.startswith("mount_shell_bond_")
    ]
    cad_identities = {
        p.id: {
            "current_shape_sha256": shape_digest(p),
            "cached_shape_sha256": p.cad_mass.shape_sha256 if p.cad_mass else None,
            "cache_matches_current_generator": p.cad_mass is not None
            and p.cad_mass.shape_sha256 == shape_digest(p),
            "mass_kg": p.resolved_mass_kg,
        }
        for p in critical
    }
    if not all(p["cache_matches_current_generator"] for p in cad_identities.values()):
        raise ValueError("Critical candidate CAD identity stale; reconcile before bounded study")
    curve = load_rasp(vehicle.motor.curve)
    masses = {p.id: p.resolved_mass_kg for p in vehicle.parts}
    samples = []
    for time, value in curve.samples:
        motor_mass = vehicle.motor.casing_mass_kg + vehicle.motor.propellant_mass_kg * (
            1 - curve.burned_fraction(float(time))
        )
        thrust = float(value) * 1.15
        total = sum(masses.values()) - masses["motor"] + motor_mass + 0.05
        specific = thrust / total
        forward = sum(p.resolved_mass_kg for p in vehicle.parts if p.position_m < 0.922)
        samples.append(
            {
                "time_s": float(time),
                "thrust_n": thrust,
                "motor_mass_kg": motor_mass,
                "mass_with_growth_kg": total,
                "specific_acceleration_m_s2": specific,
                "motor_flank_n": thrust - motor_mass * specific,
                "joint_n_forward_growth": (forward + 0.05) * specific,
                "joint_n_aft_growth": forward * specific,
            }
        )
    peak_joint = max(samples, key=lambda x: x["joint_n_forward_growth"])
    peak_flank = max(samples, key=lambda x: x["motor_flank_n"])
    # The reduced overlap represents the upper joint only. It does not use the
    # larger flank force as if every force went through the upstream body.
    load = peak_joint["joint_n_forward_growth"]
    fixtures = [overlap_known_case(n) for n in cfg["divisions"]]
    normal_fixtures = [peel_foundation_known_case(n) for n in cfg["divisions"]]
    annulus_r = cfg["overlap"]["base_outer_radius_mm"]
    overlap = cfg["overlap"]
    width = 2 * math.pi * annulus_r
    counts = cfg["divisions"]
    groups = {}
    for adhesive_e in cfg["adhesive_young_mpa"]:
        for hoop_fraction in cfg["hoop_modulus_fraction"]:
            for load_fraction in cfg["outer_load_fraction"]:
                label = f"E{adhesive_e:g}_hoop{hoop_fraction:g}_outer{load_fraction:g}"
                levels = []
                for divisions in counts:
                    row = overlap_beam_spring(
                        divisions=divisions,
                        length_mm=overlap["upper_length_mm"],
                        overlap_mm=overlap["length_mm"],
                        width_mm=width,
                        thickness_mm=(overlap["base_wall_mm"], overlap["paper_wall_mm"]),
                        young_mpa=(paper_e, paper_e),
                        adhesive_thickness_mm=overlap["film_mm"],
                        adhesive_young_mpa=adhesive_e,
                        adhesive_poisson=0.3,
                        force_n=load,
                        outer_load_fraction=load_fraction,
                        radius_mm=annulus_r,
                        hoop_young_mpa=(paper_e * hoop_fraction, paper_e * hoop_fraction),
                        retain_fields=True,
                    )
                    fields = row.pop("gauss_fields")
                    (output / f"{label}_{divisions}_fields.json").write_text(
                        json.dumps(fields, indent=2) + "\n"
                    )
                    levels.append(row)
                metrics = [
                    "max_axial_displacement_mm",
                    "base_peak_abs_surface_axial_mpa",
                    "outer_peak_abs_surface_axial_mpa",
                    "peak_abs_adhesive_shear_mpa",
                    "peak_tensile_peel_mpa",
                ]
                changes = {
                    k: abs(levels[-1][k] - levels[-2][k]) / max(abs(levels[-1][k]), 1e-15)
                    for k in metrics
                }
                fine = levels[-1]
                df = cfg["design_factor"]
                groups[label] = {
                    "levels": levels,
                    "final_relative_changes": changes,
                    "converged": changes[metrics[0]] < 0.05
                    and all(changes[k] < 0.1 for k in metrics[1:]),
                    "required_hot_base_axial_strength_mpa": df * fine[metrics[1]],
                    "required_hot_outer_axial_strength_mpa": df * fine[metrics[2]],
                    "required_hot_adhesive_shear_strength_mpa": df * fine[metrics[3]],
                    "required_hot_adhesive_normal_tensile_strength_mpa": df * fine[metrics[4]],
                    "paper_2mpa_screen_passed": df * max(fine[metrics[1]], fine[metrics[2]]) <= 2.0,
                    "adhesive_mixed_mode_acceptance": "unavailable; no interaction/fracture envelope",
                    "numerical_assembly_acceptance": False,
                }
    bonds = [p for p in critical if p.id.startswith("mount_shell_bond_")]
    actual_gaps = [
        (float(p.geometry["radius_m"]) - float(p.geometry["inner_radius_m"])) * 1000 for p in bonds
    ]
    if max(actual_gaps) - min(actual_gaps) > 1e-8:
        raise ValueError("Different ring bond gaps need separate serial connection properties")
    actual_gap = actual_gaps[0]
    areas = [
        p.cad_mass.volume_m3 * 1e9 / gap
        for p, gap in zip(bonds, actual_gaps, strict=True)
        if p.cad_mass
    ]
    mount = next(p for p in critical if p.id == "motor_mount")
    assert mount.cad
    params = mount.cad.parameters
    rail_a, rail_ix, rail_iy = _rail_section_mm(
        params["rail_radius_mm"],
        params["rail_depth_mm"],
        params["rail_width_mm"],
        params["fin_channel_radius_mm"],
        params["fin_channel_depth_mm"],
        params["fin_slot_width_mm"],
        float(mount.geometry["radius_m"]) * 1000,
    )
    budgets = []
    density = cfg["paper_density_kg_m3"]
    upper_part = next(p for p in critical if p.id == "body_upper")
    shell_part = next(p for p in critical if p.id == "aft_shell")
    base_bore = float(shell_part.geometry["inner_radius_m"]) * 1000
    original_outer = float(shell_part.geometry["radius_m"]) * 1000
    upper_length = float(upper_part.geometry["length_m"]) * 1000
    aft_length = float(shell_part.geometry["length_m"]) * 1000
    original_area = math.pi * (original_outer**2 - base_bore**2)
    slot_ratio = (
        masses["aft_shell"]
        / density
        * 1e9
        / (
            original_area
            * next(p.geometry["length_m"] * 1000 for p in critical if p.id == "aft_shell")
        )
    )
    for upper_wall, aft_wall in cfg["whole_tube_wall_pairs_mm"]:
        upper_delta = (
            math.pi
            * ((base_bore + upper_wall) ** 2 - original_outer**2)
            * upper_length
            * density
            * 1e-9
        )
        aft_delta = (
            math.pi
            * ((base_bore + aft_wall) ** 2 - original_outer**2)
            * aft_length
            * slot_ratio
            * density
            * 1e-9
        )
        for joint_k in cfg["joint_stiffness_n_mm"]:
            budget = bonded_path_hand_budget(
                force_n=peak_joint["joint_n_forward_growth"],
                rail_force_n=peak_flank["motor_flank_n"],
                ring_bond_areas_mm2=areas,
                ring_stations_mm=params["ring_stations_mm"],
                rail_area_mm2=rail_a,
                rail_weak_i_mm4=min(rail_ix, rail_iy),
                paper_hot_mpa=paper_e,
                plywood_hot_mpa=plywood_e,
                adhesive_hot_mpa=cfg["hand_budget_adhesive_young_mpa"],
                bond_gap_mm=actual_gap,
                upper_path_length_mm=upper_length,
                aft_path_length_mm=max(p.position_m for p in bonds) * 1000
                - shell_part.position_m * 1000,
                ring_width_mm=params["rail_width_mm"],
                ring_arm_mm=float(mount.geometry["radius_m"]) * 1000 - params["rail_radius_mm"],
                ring_thickness_mm=params["ring_thickness_mm"],
                upper_wall_mm=upper_wall,
                aft_wall_mm=aft_wall,
                joint_stiffness_n_mm=joint_k,
                design_factor=cfg["design_factor"],
            )
            budget.update(
                upper_wall_mm=upper_wall,
                aft_wall_mm=aft_wall,
                added_upper_mass_kg=upper_delta,
                added_aft_mass_kg=aft_delta,
                mass_basis="monolithic custom-wound wall candidate; aft slot loss ratio held constant",
            )
            budgets.append(budget)
    paper_inner = annulus_r + overlap["film_mm"]
    paper_volume = (
        math.pi
        * ((paper_inner + overlap["paper_wall_mm"]) ** 2 - paper_inner**2)
        * overlap["length_mm"]
    )
    film_volume = math.pi * (paper_inner**2 - annulus_r**2) * overlap["length_mm"]
    contacts = {
        "paper_doubler_mass_kg": paper_volume * density * 1e-9,
        "film_mass_kg": film_volume * study["trade_only"]["adhesive"]["density_kg_m3"] * 1e-9,
        "film_conduction_w_k": [
            k
            * (2 * math.pi * (annulus_r + overlap["film_mm"] / 2) * overlap["length_mm"])
            / overlap["film_mm"]
            * 0.001
            for k in study["thermal_conductivity_w_m_k"]
        ],
        "five_ring_conduction_w_k_nominal": [
            k * sum(areas) / actual_gap * 0.001 for k in study["thermal_conductivity_w_m_k"]
        ],
        "five_ring_estimated_heat_capacity_j_k": sum(masses[p.id] for p in bonds)
        * study["trade_only"]["adhesive"]["thermal_cp_j_kg_k_estimate"],
        "thermal_assumptions": "Perfect nominal area only; k and cp are estimates. Cure, voids, gap bounds and actual contact reduce/restructure conduction.",
    }
    result = {
        "schema_version": 1,
        "candidate": str(candidate),
        "source_sha256": hashes,
        "critical_cad_identities": cad_identities,
        "actual_ring_bond_gaps_mm": actual_gaps,
        "circumferential_ring_sensitivities": [
            annular_brace_sensitivity(
                float(mount.geometry["radius_m"]) * 1000,
                inner,
                params["ring_thickness_mm"],
                plywood_e,
                (
                    params["fin_channel_radius_mm"] - params["fin_channel_depth_mm"] / 2
                    if station >= params["tab_slot_start_mm"]
                    else None
                ),
            )
            for station, inner in zip(
                params["ring_stations_mm"],
                params.get(
                    "ring_inner_radii_mm",
                    [float(mount.geometry["inner_radius_m"]) * 1000]
                    * len(params["ring_stations_mm"]),
                ),
                strict=True,
            )
        ],
        "load_samples": samples,
        "peak_joint_sample": peak_joint,
        "peak_motor_flank_sample": peak_flank,
        "known_case": fixtures,
        "normal_foundation_known_case": normal_fixtures,
        "known_case_verified": all(r["verified"] for r in fixtures + normal_fixtures),
        "finite_overlap_sensitivities": groups,
        "serial_path_hand_budgets": budgets,
        "thermal_contacts": contacts,
        "method_limits": [
            "Numerically verified reduced upper-overlap model, not the complete 3D rail/ring/body/contact assembly.",
            "Upper overlap normal springs retain peel; full-cylinder hoop stiffness and end-load partition are explicit sensitivities.",
            "End bearing is represented by specified independent compressive forces; no end tie or friction/contact capacity is credited.",
            "Estimated elastic properties are inputs; no physical measured data or hot material allowable is inferred.",
            "Whole-tube mass trades are new manufacturing candidates; a bonded wrap cannot be relabeled a thicker monolithic tube.",
            "Missing local crushing, bond peel/mixed-mode envelope, actual ring lateral support, joint bearing contact and positive retention block assembly acceptance.",
        ],
        "expanded_wo03_passed": False,
        "active_geometry_adopted": False,
        "flight_ready": False,
    }
    result["inputs_unchanged"] = hashes == {str(p): sha(p) for p in paths}
    (output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--candidate",
        type=Path,
        default=Path("build/wo03-correction-package/latest/G54-0.075/resolved-candidate.yaml"),
    )
    parser.add_argument(
        "--shoulder", action="store_true", help="Study-only finite shoulder and upper-shell segment"
    )
    parser.add_argument("--carbon-modulus", type=float, choices=[5000.0, 10000.0], default=5000.0)
    parser.add_argument("--size", type=float, default=5.0)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument(
        "--reduced",
        action="store_true",
        help="Bounded verified overlap/spring and load-path hand study",
    )
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--case", help="Optional single physical case ID")
    parser.add_argument("--upper-doubler", action="store_true", help="Study-only upper G11 collar")
    parser.add_argument(
        "--paper-doubler", action="store_true", help="Study-only 100 mm paper doubler"
    )
    parser.add_argument("--collar-length", type=float, choices=[50.0, 70.0], default=50.0)
    parser.add_argument("--g11-stop", action="store_true", help="Study-only G11 stop")
    parser.add_argument("--strip-width", type=float, choices=[3.0, 10.0], default=3.0)
    parser.add_argument("--strip-taper", action="store_true", help="Study-only 30 mm front taper")
    parser.add_argument("--trade", choices=["pu", "pu_strips"])
    parser.add_argument("--pu-modulus", type=float, choices=[2.0, 20.0], default=20.0)
    parser.add_argument(
        "--joint",
        choices=["ideal_strip_projection", "shell_only"],
        default="ideal_strip_projection",
    )
    args = parser.parse_args()
    if args.reduced:
        report = reduced_study(args.candidate, args.output)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "known_case_verified": report["known_case_verified"],
                    "inputs_unchanged": report["inputs_unchanged"],
                    "expanded_wo03_passed": False,
                },
                indent=2,
            )
        )
        return
    if args.paper_doubler and (
        not args.shoulder or args.upper_doubler or args.trade != "pu_strips"
    ):
        parser.error(
            "--paper-doubler requires --shoulder --trade pu_strips and excludes --upper-doubler"
        )
    if args.fixture:
        print(json.dumps(bonded_bar_fixture(args.output), indent=2))
        return
    candidate = args.candidate
    source = [
        candidate,
        *sorted(Path("src/cad").glob("*.py")),
        Path("src/analysis/bonded_support.py"),
        Path("src/vehicle/motors.py"),
        Path("configs/studies/wo02/motors/CTI_G54_RSE_hypothesis.eng"),
        Path("configs/studies/wo03-bonded-support.yaml"),
        Path(__file__),
    ]
    before = {str(p): sha(p) for p in source}
    args.output.mkdir(parents=True, exist_ok=False)
    if args.trade:
        # The historical resolved copy contains stale cached CAD mass data.
        # Clear all caches before regenerating and reconciling every part with
        # current generator sources; never reuse the old identity.
        raw = yaml.safe_load(candidate.read_text())
        for item in raw["parts"]:
            item["cad_mass"] = None
            if args.shoulder and item["id"] == "aft_shell":
                item["position_m"] = 0.923
                item["geometry"]["length_m"] = 0.277
                item["cad"]["parameters"]["fin_slot_start_mm"] = 167
            if args.shoulder and item["id"] == "interface_coupler":
                item["geometry"]["length_m"] = 0.105
        uncached = Vehicle.model_validate(raw)
        manifest, _ = export_vehicle(uncached, args.output / "reconciled-cad", export=False)
        v = _reconcile_copy(uncached, {p.id for p in uncached.parts}, manifest)
        (args.output / "regenerated-candidate.json").write_text(
            v.model_dump_json(by_alias=True, indent=2) + "\n"
        )
        (args.output / "regenerated-cad-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
    else:
        v = load_vehicle(candidate)
    paths = {}
    metadata = {}
    for p in v.parts:
        if p.id not in ("motor_mount", "aft_shell") and not p.id.startswith("mount_shell_bond_"):
            continue
        shape = local_shape(p)
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError(f"{p.id} invalid solid")
        shape = shape.translate(
            (p.lateral_offset_m[0] * 1000, -p.lateral_offset_m[1] * 1000, p.position_m * 1000)
        )
        path = args.output / f"{p.id}.step"
        cq.exporters.export(shape, str(path))
        paths[p.id] = path
        metadata[p.id] = {
            "shape_sha256": shape_digest(p),
            "step_sha256": sha(path),
            "cad_volume_mm3": shape.Volume(),
            "position_m": p.position_m,
            "material": p.material,
        }
    if args.shoulder:
        # Shoulder/spreader and a 100 mm upper-shell segment are new finite
        # solids. The keyed stop/coupler are NOT represented in this surrogate.
        additional = (
            [
                (
                    "upper_wrap_bond",
                    33.0,
                    33.5,
                    args.collar_length,
                    918.0 - args.collar_length,
                    1200.0,
                ),
                (
                    "upper_doubler",
                    33.5,
                    34.0,
                    args.collar_length,
                    918.0 - args.collar_length,
                    1850.0,
                ),
            ]
            if args.upper_doubler
            else []
        )
        if args.paper_doubler:
            additional = [
                ("upper_wrap_bond", 33.0, 33.1, 100.0, 818.0, 1200.0),
                ("upper_doubler", 33.1, 33.3, 100.0, 818.0, 700.0),
            ]
        for name, inner, outer, length, z, density in [
            (
                "upper_segment",
                32.5,
                33.0,
                150.0 if args.paper_doubler else 100.0,
                768.0 if args.paper_doubler else 818.0,
                700.0,
            ),
            ("joint_flange", 32.05, 34.2, 4.0, 918.0, 1850.0 if args.g11_stop else 1070.0),
            ("face_spreader", 32.3, 34.2, 1.0, 922.0, 1850.0),
            *additional,
        ]:
            shape = (
                cq.Workplane("XY")
                .circle(outer)
                .circle(inner)
                .extrude(length)
                .val()
                .translate((0, 0, z))
            )
            path = args.output / f"{name}.step"
            cq.exporters.export(shape, str(path))
            paths[name] = path
            metadata[name] = {
                "shape_basis": "study-only finite annulus; interfaces perfectly bonded",
                "step_sha256": sha(path),
                "cad_volume_mm3": shape.Volume(),
                "position_m": z / 1000,
                "material": name,
                "mass_kg": shape.Volume() * 1e-9 * density,
            }
    if args.trade == "pu_strips":
        # Curved, conforming annular sectors: contact arc at R33 is exactly
        # 3 mm. Each 0.5 mm PU film and 0.5 mm strip spans 922..1200 mm.
        half = args.strip_width / 33.0 / 2.0
        strip_start = 923.0 if args.shoulder else 922.0
        strip_length = 1200.0 - strip_start
        for i, angle in enumerate((60.0, 180.0, 300.0)):
            theta = math.radians(angle)

            def sector(inner: float, outer: float, theta: float = theta) -> cq.Shape:
                def xy(radius: float, alpha: float) -> tuple[float, float]:
                    return (radius * math.cos(alpha), radius * math.sin(alpha))

                return (
                    cq.Workplane("XY")
                    .moveTo(*xy(inner, theta - half))
                    .lineTo(*xy(outer, theta - half))
                    .threePointArc(xy(outer, theta), xy(outer, theta + half))
                    .lineTo(*xy(inner, theta + half))
                    .threePointArc(xy(inner, theta), xy(inner, theta - half))
                    .close()
                    .extrude(strip_length)
                    .val()
                    .translate((0, 0, strip_start))
                )

            for kind, inner, outer, density in (
                ("strip_bond", 33.0, 33.5, 1200.0),
                ("strip", 33.5, 34.0, 1400.0),
            ):
                name = f"{kind}_{i}"
                shape = sector(inner, outer)
                if kind == "strip" and args.strip_taper:
                    cone = cq.Solid.makeCone(33.52, 34.0, 30.0, cq.Vector(0, 0, 922))
                    aft = cq.Solid.makeCylinder(34.0, 248.0, cq.Vector(0, 0, 952))
                    bore = cq.Solid.makeCylinder(33.5, 278.0, cq.Vector(0, 0, 922))
                    shape = shape.intersect(cone.fuse(aft).cut(bore))
                    if not shape.isValid() or shape.Volume() <= 0:
                        raise ValueError("Invalid tapered strip solid")
                path = args.output / f"{name}.step"
                cq.exporters.export(shape, str(path))
                paths[name] = path
                metadata[name] = {
                    "shape_basis": f"study-only concentric sector, {args.strip_width:g} mm contact arc"
                    + (
                        "; 30 mm front taper from 0.02 to 0.5 mm"
                        if kind == "strip" and args.strip_taper
                        else ""
                    ),
                    "step_sha256": sha(path),
                    "cad_volume_mm3": shape.Volume(),
                    "position_m": strip_start / 1000,
                    "material": "PU" if kind == "strip_bond" else "carbon",
                    "mass_kg": shape.Volume() * 1e-9 * density,
                }
    physical = None
    if args.physical or args.trade:
        assert v.motor and v.motor.curve
        curve = load_rasp(v.motor.curve)
        index = int(curve.samples[:, 1].argmax())
        time = float(curve.samples[index, 0])
        thrust = float(curve.samples[index, 1]) * 1.15
        motor_mass = v.motor.casing_mass_kg + v.motor.propellant_mass_kg * (
            1 - curve.burned_fraction(time)
        )
        masses = {p.id: p.resolved_mass_kg for p in v.parts}
        if args.trade == "pu_strips":
            masses.update(
                {
                    name: data["mass_kg"]
                    for name, data in metadata.items()
                    if name.startswith("strip")
                }
            )
        if args.shoulder:
            segment_mass = metadata["upper_segment"]["mass_kg"]
            original_stop = masses.pop("joint_stop")
            masses["body_upper"] -= segment_mass
            old_flange_mass = math.pi * (33.2**2 - 32.05**2) * 4 * 1e-9 * 1070
            key_allowance = max(original_stop - old_flange_mass, 0.0)
            masses["joint_keys_allowance"] = key_allowance
            modeled_shoulder = ("upper_segment", "joint_flange", "face_spreader")
            if args.upper_doubler or args.paper_doubler:
                modeled_shoulder += ("upper_wrap_bond", "upper_doubler")
            masses.update({name: metadata[name]["mass_kg"] for name in modeled_shoulder})
        modeled = set(paths)
        forward = sum(p.resolved_mass_kg for p in v.parts if p.position_m < 0.922)
        if args.shoulder:
            forward -= segment_mass + original_stop
        mount_attach = {
            "motor_liner",
            "retention",
            "motor_radiant_shield",
            "thrust_pads",
            "aft_retainer",
            "retention_hardware",
            "aft_thrust_pads",
            "mount_bond_fillets",
        }
        attachments = []
        for part in v.parts:
            if part.position_m < 0.922 or part.id == "motor" or part.id in modeled:
                continue
            substrate = "motor_mount" if part.id in mount_attach else "aft_shell"
            station = min(1199.0, max(923.0, (part.position_m + part.cg_offset_m) * 1000))
            attachments.append(
                {
                    "id": part.id,
                    "mass_kg": part.resolved_mass_kg,
                    "substrate": substrate,
                    "station_mm": station,
                }
            )
        if args.shoulder and key_allowance:
            attachments.append(
                {
                    "id": "joint_keys_allowance",
                    "mass_kg": key_allowance,
                    "substrate": "joint_flange",
                    "station_mm": 920.0,
                }
            )
        total = sum(masses.values()) - masses["motor"] + motor_mass + 0.05
        cases = []
        for growth in ("forward", "aft"):
            for state, ply, paper, epoxy in [
                ("cold", 2000, 500, 2000),
                ("hot_nominal", 1000, 250, 2000),
                ("hot_soft", 1000, 250, 100),
            ]:
                cases.append(
                    {
                        "id": growth + "_" + state,
                        "growth_location": growth,
                        "ply_mpa": ply,
                        "paper_mpa": paper,
                        "epoxy_mpa": epoxy,
                    }
                )
        if args.trade:
            cases = [
                {
                    "id": "forward_hot_pu",
                    "growth_location": "forward",
                    "ply_mpa": 1000,
                    "paper_mpa": 250,
                    "epoxy_mpa": args.pu_modulus,
                    "carbon_mpa": args.carbon_modulus if args.shoulder else 14000,
                }
            ]
        if args.case:
            cases = [case for case in cases if case["id"] == args.case]
            if not cases:
                raise ValueError(f"Unknown case {args.case}")
        physical = {
            "curve": v.motor.curve,
            "peak_time_s": time,
            "thrust_n": thrust,
            "motor_mass_kg": motor_mass,
            "total_mass_with_growth_kg": total,
            "forward_mass_kg": forward,
            "specific_acceleration_m_s2": thrust / total,
            "mass_kg": masses,
            "attachments": attachments,
            "cases": cases,
            "joint_model": "finite_shoulder_bonded" if args.shoulder else args.joint,
            "g11_stop": args.g11_stop,
            "paper_doubler": args.paper_doubler,
            "support_station_mm": 768.0 if args.paper_doubler else 818.0,
        }
    result = {
        "physical_input": physical,
        "trade": args.trade,
        "strip_taper": args.strip_taper,
        "shoulder": args.shoulder,
        "upper_doubler": args.upper_doubler,
        "paper_doubler": args.paper_doubler,
        "collar_length_mm": args.collar_length if args.upper_doubler else None,
        "g11_stop": args.g11_stop,
        "strip_width_mm": args.strip_width,
        "candidate": str(candidate),
        "source_sha256": before,
        "parts": metadata,
        "mesh_size_mm": args.size,
        "expanded_wo03_passed": False,
        "flight_ready": False,
    }
    try:
        result["mesh"] = fragment_and_mesh(paths, args.size, args.output, physical)
        result["status"] = (
            "physical inertia cases executed; validation and convergence pending"
            if physical
            else "exploratory static solve executed; physical inertia and convergence pending"
        )
    except Exception as e:  # noqa: BLE001 - preserve failed-run evidence
        result["status"] = "failed"
        result["error"] = repr(e)
    result["inputs_unchanged"] = before == {str(p): sha(p) for p in source}
    (args.output / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    if result["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
