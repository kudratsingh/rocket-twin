"""Build and verify the frozen candidate's actual opaque fluid-boundary tracer."""

from __future__ import annotations

import os

for name in [
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "MKL_NUM_THREADS",
]:
    os.environ[name] = "1"

import argparse
import hashlib
import inspect
import json
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cadquery as cq
import numpy as np
import yaml

from src.analysis.cad_radiation import (
    FirstHitLocator,
    boundary_topology,
    compare_ring_end_visibility,
    cut_fluid,
    cylindrical_boundary_coverage,
    load_placed_manifest,
    physical_surface_groups,
    resolve_material_owners,
    sample_first_hit,
    save_mesh,
    triangulate_fluid,
)
from src.cad.parts import local_shape, shape_digest
from src.vehicle.schema import load_vehicle


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def trace_record(result: dict[str, Any], path: Path) -> dict[str, Any]:
    """Keep full raw operators outside the small human-readable evidence record."""
    arrays = {key: value for key, value in result.items() if isinstance(value, np.ndarray)}
    np.savez_compressed(path, **arrays)  # type: ignore[arg-type]
    metadata = {key: value for key, value in result.items() if not isinstance(value, np.ndarray)}
    metadata.update(
        operator_path=str(path),
        operator_sha256=sha(path),
        minimum_source_rays=int(result["counts"].min()),
        maximum_source_rays=int(result["counts"].max()),
        maximum_binomial_standard_error=float(
            np.sqrt(
                result["raw_view_factors"]
                * (1 - result["raw_view_factors"])
                / result["counts"][:, None]
            ).max()
        ),
        maximum_zero_hit_probability_upper95=float(
            result["zero_hit_probability_upper95_by_source"].max()
        ),
    )
    return metadata


def known_cases(cfg: dict[str, Any], output: Path) -> dict[str, Any]:
    """Independent diffuse integral fixtures and actual Boolean opaque barriers."""
    case_rows = []
    total = 0
    nodes, weights = np.polynomial.legendre.leggauss(64)
    x = (nodes + 1) / 2
    w = weights / 2
    # Equal unit squares, separation one: integrate relative displacements.
    cube_opposite = float(
        4
        / np.pi
        * np.sum(
            w[:, None]
            * w[None, :]
            * (1 - x[:, None])
            * (1 - x[None, :])
            / (1 + x[:, None] ** 2 + x[None, :] ** 2) ** 2
        )
    )

    def sphere(radius: float) -> Any:
        return cq.Solid.makeSphere(radius, angleDegrees1=-90, angleDegrees2=90)

    primitives: list[tuple[str, Callable[[], tuple[Any, dict[str, Any]]]]] = [
        ("cube", lambda: (cq.Solid.makeBox(20, 20, 20), {})),
        ("equal_parallel_disks", lambda: (cq.Solid.makeCylinder(10, 10), {})),
        ("concentric_spheres", lambda: (sphere(10), {"inner_sphere": sphere(5)})),
    ]
    for name, build in primitives:
        enclosure, opaque = build()
        fluid, faces, geometry = cut_fluid(enclosure, opaque, 1e-7)
        faces, owners = resolve_material_owners(fluid, faces, opaque, 1e-4)
        if not owners["all_material_owners_verified"]:
            raise RuntimeError(f"Known-case material ownership failed: {name}")
        groups, mapping = physical_surface_groups(fluid, faces)
        previous: np.ndarray | None = None
        levels = []
        for i, level in enumerate(cfg["numerics"]["known_levels"]):
            mesh = triangulate_fluid(
                fluid,
                faces,
                level["deflection_mm"],
                level["angular_tolerance_rad"],
                1e-7,
                150000,
                1e-4,
            )
            result = sample_first_hit(
                mesh,
                mapping,
                level["rays"],
                100,
                cfg["numerics"]["seed"] + i,
                1e-5,
                cfg["numerics"]["max_ray_seconds"],
            )
            total += result["rays"]
            view = result["raw_view_factors"]
            inner_check = None
            if name == "cube":
                normals = np.array([g["physical_surface_family"]["normal"] for g in groups])
                opposite = normals @ normals.T < -0.9
                observed = float(view[opposite].mean())
                expected = cube_opposite
                trials = int(result["counts"].sum())
            elif name == "equal_parallel_disks":
                caps = [
                    g["group_id"] for g in groups if g["physical_surface_family"]["kind"] == "PLANE"
                ]
                observed = float(
                    (
                        view[caps[0], caps[1]] * result["counts"][caps[0]]
                        + view[caps[1], caps[0]] * result["counts"][caps[1]]
                    )
                    / result["counts"][caps].sum()
                )
                expected = (3 - np.sqrt(5)) / 2
                trials = int(result["counts"][caps].sum())
            else:
                inner = next(g["group_id"] for g in groups if g["part_id"] == "inner_sphere")
                outer = next(g["group_id"] for g in groups if g["part_id"] != "inner_sphere")
                inner_check = {
                    "expected_inner_to_outer": 1.0,
                    "observed_inner_to_outer": float(view[inner, outer]),
                    "spurious_faceted_inner_self_hits": int(result["hits"][inner, inner]),
                    "inner_source_rays": int(result["counts"][inner]),
                    "maximum_allowed_faceting_probability": 0.002,
                }
                observed = float(view[outer, inner])
                expected = 0.25
                trials = int(result["counts"][outer])
            sigma = float(np.sqrt(expected * (1 - expected) / trials))
            delta: float | None = None if previous is None else float(np.abs(view - previous).max())
            previous = view
            row = {
                "id": level["id"],
                "mesh": {k: v for k, v in mesh["checks"].items() if k != "face_checks"},
                **trace_record(result, output / f"known-{name}-{level['id']}.npz"),
                "expected": expected,
                "observed": observed,
                "absolute_error": abs(observed - expected),
                "binomial_standard_error": sigma,
                "max_raw_F_change_from_previous_level": delta,
                "convex_inner_sphere_check": inner_check,
                "passed": abs(observed - expected) < 5 * sigma + 0.002
                and result["escaped_rays"] == 0
                and result["near_origin_hits"] == 0
                and abs(mesh["checks"]["relative_volume_error"]) < 0.005
                and (inner_check is None or inner_check["observed_inner_to_outer"] >= 0.998),
            }
            levels.append(row)
        case_rows.append(
            {
                "id": name,
                "geometry": geometry,
                "groups": groups,
                "levels": levels,
                "passed": all(row["passed"] for row in levels),
            }
        )
        print(
            f"Known case {name}: {levels[-1]['observed']:.6f} versus {levels[-1]['expected']:.6f}",
            flush=True,
        )
    barrier_rows = []
    for name in ["fully_open", "fully_glued", "partly_glued", "opaque_nearest_barrier"]:
        opaque = {}
        if name in ["fully_glued", "partly_glued"]:
            opaque["glue"] = cq.Solid.makeBox(
                0.4, 20 if name == "fully_glued" else 10, 20, cq.Vector(9.8, 0, 0)
            )
        if name == "opaque_nearest_barrier":
            opaque = {
                "near_barrier": cq.Solid.makeBox(0.4, 20, 20, cq.Vector(8, 0, 0)),
                "far_barrier": cq.Solid.makeBox(0.4, 20, 20, cq.Vector(12, 0, 0)),
            }
        fluid, faces, _ = cut_fluid(cq.Solid.makeBox(20, 20, 20), opaque, 1e-7)
        faces, owners = resolve_material_owners(fluid, faces, opaque, 1e-4)
        if not owners["all_material_owners_verified"]:
            raise RuntimeError(f"Barrier ownership failed: {name}")
        mesh = triangulate_fluid(fluid, faces, 0.05, 0.2, 1e-7, 150000, 1e-4)
        locator = FirstHitLocator(mesh["vertices_mm"], mesh["triangles"])
        hit_counts: dict[str, int] = {}
        errors = []
        for y in (np.arange(16) + 0.5) * 20 / 16:
            for z in (np.arange(16) + 0.5) * 20 / 16:
                cell, distance = locator.hit(np.array([1.0, y, z]), np.array([1.0, 0, 0]))
                owner = (
                    "escaped" if cell < 0 else faces[mesh["triangle_face_index"][cell]]["part_id"]
                )
                expected_owner = (
                    "near_barrier"
                    if name == "opaque_nearest_barrier"
                    else (
                        "glue"
                        if name == "fully_glued" or (name == "partly_glued" and y < 10)
                        else "radial_reservoir"
                    )
                )
                expected_distance = (
                    7
                    if name == "opaque_nearest_barrier"
                    else 8.8 if expected_owner == "glue" else 19
                )
                hit_counts[owner] = hit_counts.get(owner, 0) + 1
                if owner != expected_owner or abs(distance - expected_distance) > 1e-7:
                    errors.append({"y": y, "z": z, "owner": owner, "distance": distance})
        total += 256
        barrier_rows.append(
            {
                "id": name,
                "rays": 256,
                "first_hit_counts": hit_counts,
                "errors": errors,
                "passed": not errors,
                "fluid_solid_count": len(fluid.Solids()),
            }
        )
    return {
        "diffuse_cases": case_rows,
        "barrier_cases": barrier_rows,
        "total_rays": total,
        "passed": all(c["passed"] for c in case_rows + barrier_rows),
        "independent_expected_values": "cube cosine integral via 64x64 Gauss quadrature; equal disks analytic view factor; concentric spheres area ratio; deterministic actual slab visibility",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-cad-radiation.yaml")
    )
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--stage", choices=["known", "geometry", "mesh", "rays"], default="geometry"
    )
    parser.add_argument("--geometry-cache", type=Path)
    parser.add_argument("--known-cache", type=Path)
    parser.add_argument("--level", choices=["coarse", "medium", "fine"], action="append")
    parser.add_argument("--previous-level-operator", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text())
    paths = [
        args.config,
        Path(__file__),
        Path("src/analysis/cad_radiation.py"),
        Path(cfg["source_record"]),
        Path(cfg["source_resolved"]),
        *sorted(Path("src/cad").glob("*.py")),
        *sorted(Path("src/vehicle").glob("*.py")),
    ]
    if cfg.get("source_geometry_manifest"):
        manifest_path = Path(cfg["source_geometry_manifest"])
        paths.append(manifest_path)
        for row in json.loads(manifest_path.read_text()):
            paths.extend(manifest_path.parent / row[kind] for kind in ["step", "stl"])
    if cfg.get("comparison"):
        paths.extend(
            Path(cfg["comparison"][name])
            for name in ["before_record", "before_groups", "before_operator"]
        )
    before = {str(p): sha(p) for p in paths}
    if args.geometry_cache:
        for name in ["report.json", "face-inventory.json", "fluid-void.step"]:
            path = args.geometry_cache / name
            paths.append(path)
            before[str(path)] = sha(path)
    if args.known_cache:
        paths.append(args.known_cache / "report.json")
        before[str(paths[-1])] = sha(paths[-1])
        kernel_path = args.known_cache / "known-kernel-hashes.json"
        if kernel_path.exists():
            paths.append(kernel_path)
            before[str(kernel_path)] = sha(kernel_path)
    if args.previous_level_operator:
        paths.append(args.previous_level_operator)
        before[str(paths[-1])] = sha(paths[-1])
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "study-config.yaml").write_text(args.config.read_text())
    report: dict[str, Any] = {
        "study_id": cfg["id"],
        "source_sha256": before,
        "source_record": cfg["source_record"],
        "stage_requested": args.stage,
        "engineering_acceptance_passed": False,
        "flight_ready": False,
        "resolved_study_configuration": cfg,
    }
    start = time.monotonic()
    try:
        if args.stage == "known":
            report["known_cases"] = known_cases(cfg, args.output)
            if not report["known_cases"]["passed"]:
                raise RuntimeError("Known first-hit fixtures failed")
            report["status"] = "known_cases_passed"
            return
        source = json.loads(Path(cfg["source_record"]).read_text())
        vehicle = load_vehicle(cfg["source_resolved"])
        identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        if (
            identity != cfg["expected_candidate_identity"]
            or source["candidate_identity"] != identity
        ):
            raise ValueError("Frozen candidate identity mismatch")
        if source["cad_revision_sha256"] != cfg["expected_source_cad_revision"]:
            raise ValueError("Source CAD revision mismatch")
        e = cfg["enclosure"]
        fore = e["fore_station_m"] * 1000
        aft = e["aft_station_m"] * 1000
        radius = e["outer_radius_m"] * 1000
        enclosure = cq.Solid.makeCylinder(radius, aft - fore, cq.Vector(0, 0, fore))
        opaque: dict[str, Any] = {}
        part_inventory: list[dict[str, Any]] = []
        excluded: list[dict[str, Any]] = []
        if cfg.get("source_geometry_manifest"):
            if sha(Path(cfg["source_resolved"])) != cfg["expected_resolved_file_sha256"]:
                raise ValueError("Resolved placed candidate file hash mismatch")
            opaque, part_inventory, excluded, verified_assets = load_placed_manifest(
                Path(cfg["source_geometry_manifest"]),
                cfg["expected_manifest_sha256"],
                {p.id: p.model_dump(by_alias=True) for p in vehicle.parts if p.cad},
                cfg["geometry"]["opaque_roles"],
                fore,
                aft,
                radius,
            )
            report["placed_source"] = {
                "manifest": cfg["source_geometry_manifest"],
                "verified_asset_count": len(verified_assets),
                "actual_geometry_only": True,
                "study_postprocessor_sha256": source["study_postprocessor_sha256"],
            }
        else:
            for part in vehicle.parts:
                if shape_digest(part) != source["part_shape_sha256"][part.id]:
                    raise ValueError(
                        f"Actual current geometry no longer matches recorded source: {part.id}"
                    )
                if part.cad is None or part.cad.role not in cfg["geometry"]["opaque_roles"]:
                    excluded.append(
                        {
                            "id": part.id,
                            "reason": "No source-owned rigid opaque geometry; budget/flexible proxy is not an invented solid",
                        }
                    )
                    continue
                shape = local_shape(part).translate(
                    (
                        part.lateral_offset_m[0] * 1000,
                        -part.lateral_offset_m[1] * 1000,
                        part.position_m * 1000,
                    )
                )
                box = shape.BoundingBox()
                if (
                    box.zmax < fore
                    or box.zmin > aft
                    or box.xmin > radius
                    or box.xmax < -radius
                    or box.ymin > radius
                    or box.ymax < -radius
                ):
                    excluded.append(
                        {"id": part.id, "reason": "Actual BRep bounds outside selected enclosure"}
                    )
                    continue
                if not shape.isValid() or shape.Volume() <= 0:
                    raise ValueError(f"Invalid actual opaque solid: {part.id}")
                opaque[part.id] = shape
                part_inventory.append(
                    {
                        "id": part.id,
                        "source_shape_sha256": shape_digest(part),
                        "cad_role": part.cad.role,
                        "volume_mm3": shape.Volume(),
                        "solid_count": len(shape.Solids()),
                        "estimated_purchased_envelope": part.cad.role == "purchased_envelope",
                        "native_fin_slot_parameters": {
                            k: v
                            for k, v in part.cad.parameters.items()
                            if "slot" in k or "sector" in k
                        },
                    }
                )
        report.update(
            candidate_identity=identity,
            source_cad_revision=source["cad_revision_sha256"],
            included_parts=part_inventory,
            excluded_parts=excluded,
            reservoirs=e,
            missing_nozzle=cfg["geometry"]["missing_nozzle"],
        )
        print(f"Building actual Boolean void from {len(opaque)} source parts", flush=True)
        fluid: Any
        if args.geometry_cache:
            cached = json.loads((args.geometry_cache / "report.json").read_text())
            if (
                cached["candidate_identity"] != identity
                or cached["reservoirs"] != e
                or sha(args.geometry_cache / "fluid-void.step") != cached["fluid_step_sha256"]
            ):
                raise ValueError("Cached actual Boolean identity mismatch")
            for path, value in cached["source_sha256"].items():
                if (
                    path.startswith(("src/cad/", "src/vehicle/", "runs/"))
                    and sha(Path(path)) != value
                ):
                    raise ValueError("Cached Boolean physical source has changed")
            fluid = cq.importers.importStep(str(args.geometry_cache / "fluid-void.step")).val()
            faces = json.loads((args.geometry_cache / "face-inventory.json").read_text())
            if len(fluid.Faces()) != len(faces):
                raise ValueError("STEP face count changed")
            for face, row in zip(fluid.Faces(), faces, strict=True):
                if abs(face.Area() - row["cad_area_mm2"]) > max(1e-5, 0.001 * row["cad_area_mm2"]):
                    raise ValueError("STEP face inventory order/area incompatible")
            geometry = dict(cached["geometry"])
            geometry["cached_actual_boolean_step"] = str(args.geometry_cache / "fluid-void.step")
        else:
            fluid, faces, geometry = cut_fluid(
                enclosure, opaque, cfg["geometry"]["boolean_tolerance_mm"]
            )
        faces, material_owners = resolve_material_owners(
            fluid, faces, opaque, cfg["geometry"]["interior_offset_mm"]
        )
        report["material_ownership"] = material_owners
        report["geometry"] = geometry
        (args.output / "face-inventory.json").write_text(json.dumps(faces, indent=2) + "\n")
        cq.exporters.export(fluid, str(args.output / "fluid-void.step"))
        report["fluid_step_sha256"] = sha(args.output / "fluid-void.step")
        print(
            f'Void: {geometry["fluid_face_count"]} faces; ownership errors {len(geometry["ownership_errors"])}',
            flush=True,
        )
        if not material_owners["all_material_owners_verified"]:
            raise RuntimeError(
                "Actual fluid boundary has unowned or ambiguous material faces; rays not permitted"
            )
        report["geometry_preflight_passed"] = True
        groups, mapping = physical_surface_groups(fluid, faces)
        for group in groups:
            group["cad_area_mm2"] = sum(
                faces[i - 1]["cad_area_mm2"] for i in group["fluid_face_ids"]
            )
        (args.output / "surface-groups.json").write_text(json.dumps(groups, indent=2) + "\n")
        report["grouping"] = {
            "groups": len(groups),
            "preserved_fluid_faces": len(faces),
            "policy": "part plus physical surface family; all triangles/face IDs retained; no assigned temperatures",
            "surface_groups_sha256": sha(args.output / "surface-groups.json"),
        }
        report["boundary_topology"] = boundary_topology(fluid)
        if not report["boundary_topology"]["all_finite_edges_have_two_face_incidences"]:
            report["geometry_preflight_passed"] = False
            raise RuntimeError(
                "Actual CAD fluid has non-manifold finite contact edges; no candidate mesh/rays permitted"
            )
        if e.get("coverage_audit", False):
            report["control_boundary_coverage"] = cylindrical_boundary_coverage(
                fluid, faces, opaque, radius, fore, aft
            )
            if not report["control_boundary_coverage"]["coverage_balance_passed"]:
                report["geometry_preflight_passed"] = False
                raise RuntimeError("Independent radial control-boundary coverage failed")
        prior_ray_bound = cfg["numerics"].get("prior_executed_rays_upper_bound", 0)
        ray_total = prior_ray_bound
        report["prior_executed_rays_budget_upper_bound"] = prior_ray_bound
        if args.stage == "rays":
            if args.known_cache:
                known_record = json.loads((args.known_cache / "report.json").read_text())
                if known_record["source_sha256"]["src/analysis/cad_radiation.py"] != sha(
                    Path("src/analysis/cad_radiation.py")
                ):
                    import src.analysis.cad_radiation as kernel

                    anchor = json.loads((args.known_cache / "known-kernel-hashes.json").read_text())
                    if (
                        anchor["source_record_sha256"] != sha(args.known_cache / "report.json")
                        or anchor["source_module_sha256"]
                        != known_record["source_sha256"]["src/analysis/cad_radiation.py"]
                    ):
                        raise ValueError("Known-kernel anchor is not bound to cached record")
                    for name, value in anchor["function_source_sha256"].items():
                        if (
                            hashlib.sha256(
                                inspect.getsource(getattr(kernel, name)).encode()
                            ).hexdigest()
                            != value
                        ):
                            raise ValueError(f"Known tracer kernel changed: {name}")
                    if (
                        hashlib.sha256(inspect.getsource(known_cases).encode()).hexdigest()
                        != anchor["known_cases_wrapper_sha256"]
                    ):
                        raise ValueError("Known analytic fixture construction changed")
                    report["verified_known_kernel_anchor_sha256"] = sha(
                        args.known_cache / "known-kernel-hashes.json"
                    )
                for case in known_record["known_cases"]["diffuse_cases"]:
                    for known_level in case["levels"]:
                        if (
                            sha(Path(known_level["operator_path"]))
                            != known_level["operator_sha256"]
                        ):
                            raise ValueError("Known-case cached raw operator hash mismatch")
                report["known_cases"] = known_record["known_cases"]
                report["known_cases_reused_from"] = str(args.known_cache / "report.json")
                report["known_cache_compatibility"] = (
                    "unchanged tested kernel and analytic fixture function hashes; placed-STEP loader and execution plumbing separately recorded"
                )
            else:
                report["known_cases"] = known_cases(cfg, args.output)
            if not report["known_cases"]["passed"]:
                raise RuntimeError("Known first-hit fixtures failed; no candidate rays")
            if not args.known_cache:
                ray_total += report["known_cases"]["total_rays"]
        if args.stage != "geometry":
            levels = []
            previous_view = None
            if args.previous_level_operator:
                previous_view = np.load(args.previous_level_operator)["raw_view_factors"]
                report["previous_level_operator"] = str(args.previous_level_operator)
            requested_levels = [
                level
                for level in cfg["numerics"]["levels"]
                if args.level is None or level["id"] in args.level
            ]
            report["selected_levels"] = [level["id"] for level in requested_levels]
            for level in requested_levels:
                mesh = triangulate_fluid(
                    fluid,
                    faces,
                    level["deflection_mm"],
                    level["angular_tolerance_rad"],
                    cfg["geometry"]["weld_tolerance_mm"],
                    cfg["geometry"]["max_triangles"],
                    cfg["geometry"]["interior_offset_mm"],
                )
                checks = mesh["checks"]
                mesh_path = args.output / (level["id"] + "-boundary.npz")
                mesh_hash = save_mesh(mesh, mesh_path)
                levels.append(
                    {
                        "id": level["id"],
                        "requested_numerics": level,
                        "mesh_sha256": mesh_hash,
                        **checks,
                    }
                )
                report["mesh_levels"] = levels
                if (
                    abs(checks["relative_volume_error"])
                    > cfg["geometry"]["mesh_relative_volume_limit"]
                ):
                    raise RuntimeError(
                        "CAD versus boundary-mesh volume error exceeds configured limit"
                    )
                print(
                    f'{level["id"]}: {checks["triangle_count"]} triangles; volume error {checks["relative_volume_error"]:.6g}',
                    flush=True,
                )
                if args.stage == "rays":
                    if ray_total + level["rays"] > cfg["numerics"]["max_total_rays"]:
                        raise RuntimeError("Total first-hit ray budget exceeded")
                    result = sample_first_hit(
                        mesh,
                        mapping,
                        level["rays"],
                        cfg["numerics"]["min_rays_per_group"],
                        cfg["numerics"]["seed"],
                        cfg["numerics"]["ray_origin_offset_mm"],
                        cfg["numerics"]["max_ray_seconds"],
                    )
                    ray_total += result["rays"]
                    view = result["raw_view_factors"]
                    row = trace_record(result, args.output / (level["id"] + "-operator.npz"))
                    if previous_view is not None:
                        difference = view - previous_view
                        area = result["group_area_m2"]
                        row["max_raw_F_change_from_previous_level"] = float(abs(difference).max())
                        row["area_weighted_raw_F_l1_change"] = float(
                            (area[:, None] * abs(difference)).sum() / area.sum()
                        )
                    previous_view = view
                    levels[-1]["ray_trace"] = row
                    report["total_rays_this_execution"] = ray_total - prior_ray_bound
                    report["total_budgeted_rays_including_prior_upper_bound"] = ray_total
                    if result["escaped_rays"] or result["near_origin_hits"]:
                        raise RuntimeError(
                            "Candidate escaped or near-origin rays require investigation"
                        )
                    if cfg.get("comparison"):
                        comparison_cfg = cfg["comparison"]
                        baseline = json.loads(Path(comparison_cfg["before_record"]).read_text())
                        if (
                            baseline["candidate_identity"]
                            != comparison_cfg["before_candidate_identity"]
                            or sha(Path(comparison_cfg["before_groups"]))
                            != baseline["grouping"]["surface_groups_sha256"]
                        ):
                            raise ValueError(
                                "Before/after comparison base identity/group map mismatch"
                            )
                        expected_operator = baseline["mesh_levels"][-1]["ray_trace"][
                            "operator_sha256"
                        ]
                        if sha(Path(comparison_cfg["before_operator"])) != expected_operator:
                            raise ValueError("Comparison base raw operator hash mismatch")
                        visibility = compare_ring_end_visibility(
                            Path(comparison_cfg["before_operator"]),
                            Path(comparison_cfg["before_groups"]),
                            args.output / (level["id"] + "-operator.npz"),
                            args.output / "surface-groups.json",
                            source["contact_ledger"],
                        )
                        visibility.update(
                            before_candidate_identity=baseline["candidate_identity"],
                            after_candidate_identity=identity,
                            after_requested_numerics=level,
                            after_mesh_relative_volume_error=checks["relative_volume_error"],
                            before_requested_numerics=baseline["mesh_levels"][-1][
                                "requested_numerics"
                            ],
                            source_changed_part_ids=source["changed_source_part_ids"],
                        )
                        visibility_path = args.output / (level["id"] + "-ring-end-visibility.json")
                        visibility_path.write_text(json.dumps(visibility, indent=2) + "\n")
                        levels[-1]["ring_end_visibility"] = {
                            "path": str(visibility_path),
                            "sha256": sha(visibility_path),
                        }
            report["mesh_preflight_passed"] = True
        report["status"] = {
            "geometry": "geometry_ready",
            "mesh": "mesh_ready",
            "rays": "raw_first_hit_operator_ready_not_thermal_acceptance",
        }[args.stage]
    except Exception as exc:  # noqa: BLE001 - preserve blocked/failed geometric evidence
        report.update(status="failed", error=repr(exc))
        print(f"Preflight failed: {exc}", flush=True)
    finally:
        report["inputs_unchanged"] = before == {str(p): sha(p) for p in paths}
        report["elapsed_s"] = time.monotonic() - start
        (args.output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "status": report.get("status"),
                    "inputs_unchanged": report["inputs_unchanged"],
                    "elapsed_s": report["elapsed_s"],
                },
                indent=2,
            )
        )
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
