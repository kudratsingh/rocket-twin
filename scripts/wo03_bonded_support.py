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
from src.analysis.bonded_support import bonded_bar_fixture, fragment_and_mesh
from src.cad.assembly import export_vehicle
from src.cad.parts import local_shape, shape_digest
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle, load_vehicle


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


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
    parser.add_argument("--physical", action="store_true")
    parser.add_argument("--case", help="Optional single physical case ID")
    parser.add_argument("--upper-doubler", action="store_true", help="Study-only upper G11 collar")
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
                ("upper_wrap_bond", 33.0, 33.5, 50.0, 868.0, 1200.0),
                ("upper_doubler", 33.5, 34.0, 50.0, 868.0, 1850.0),
            ]
            if args.upper_doubler
            else []
        )
        for name, inner, outer, length, z, density in [
            ("upper_segment", 32.5, 33.0, 100.0, 818.0, 700.0),
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
            if args.upper_doubler:
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
        }
    result = {
        "physical_input": physical,
        "trade": args.trade,
        "strip_taper": args.strip_taper,
        "shoulder": args.shoulder,
        "upper_doubler": args.upper_doubler,
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
