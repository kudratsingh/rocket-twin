"""Bounded source-independent steady gas-conduction FEM verification fixtures."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

# Bound this standalone study before NumPy/SciPy load any threaded BLAS library.
for variable in (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "VECLIB_MAXIMUM_THREADS",
    "BLIS_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
):
    os.environ[variable] = "1"

import numpy as np
import scipy
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.gas_conduction import GasMesh, group_conductance, load_gas_mesh


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def create_fixture(name: str, size: float, cfg: dict[str, Any], output: Path) -> GasMesh:
    """Gmsh OCC shapes independent of all rocket CAD or physical face labels."""
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != cfg["versions"]["gmsh"]:
        raise ValueError("Pinned Gmsh version mismatch")
    d = cfg["fixture_dimensions_m"]
    length, width, height = d["length"], d["width"], d["height"]
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.option.setNumber("General.NumThreads", 1)
        for dim in (1, 2, 3):
            gmsh.option.setNumber(f"Mesh.MaxNumThreads{dim}D", 1)
        gmsh.model.add(name)
        occ = gmsh.model.occ
        if name == "concentric_cylinder":
            outer = occ.addCylinder(0, 0, 0, 0, 0, d["cylinder_length"], d["cylinder_outer_radius"])
            inner = occ.addCylinder(0, 0, 0, 0, 0, d["cylinder_length"], d["cylinder_inner_radius"])
            occ.cut([(3, outer)], [(3, inner)])
        elif name == "insulated_divider":
            half = (length - d["divider_thickness"]) / 2
            occ.addBox(0, 0, 0, half, width, height)
            occ.addBox(length - half, 0, 0, half, width, height)
        else:
            air = occ.addBox(0, 0, 0, length, width, height)
            if name == "longitudinal_obstruction":
                obstruction = occ.addBox(
                    -length / 10,
                    (width - d["obstruction_width"]) / 2,
                    (height - d["obstruction_height"]) / 2,
                    1.2 * length,
                    d["obstruction_width"],
                    d["obstruction_height"],
                )
                occ.cut([(3, air)], [(3, obstruction)])
            elif name != "slab":
                raise ValueError("Unknown independent fixture")
        occ.synchronize()
        faces: dict[str, list[int]] = {"hot": [], "cold": [], "insulated": []}
        for _, tag in gmsh.model.getEntities(2):
            box = gmsh.model.getBoundingBox(2, tag)
            if name == "concentric_cylinder":
                kind = gmsh.model.getType(2, tag)
                if kind == "Cylinder":
                    radius = occ.getMass(2, tag) / (2 * math.pi * d["cylinder_length"])
                    group = (
                        "hot"
                        if math.isclose(radius, d["cylinder_inner_radius"], rel_tol=1e-7)
                        else "cold"
                    )
                else:
                    group = "insulated"
            elif abs(box[0]) < 2e-7 and abs(box[3]) < 2e-7:
                group = "hot"
            elif abs(box[0] - length) < 2e-7 and abs(box[3] - length) < 2e-7:
                group = "cold"
            else:
                group = "insulated"
            faces[group].append(tag)
        if not all(faces.values()):
            raise ValueError("Fixture boundary classification incomplete")
        for group, tags in faces.items():
            gmsh.model.addPhysicalGroup(2, tags, name=group)
        gmsh.model.addPhysicalGroup(3, [tag for _, tag in gmsh.model.getEntities(3)], name="air")
        gmsh.option.setNumber("Mesh.ElementOrder", 1)
        gmsh.option.setNumber("Mesh.MeshSizeMin", size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size)
        gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 0)
        gmsh.option.setNumber("Mesh.MinimumCirclePoints", 12)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)
        gmsh.model.mesh.generate(3)
        node_tags, xyz_raw, _ = gmsh.model.mesh.getNodes()
        order = np.argsort(node_tags)
        sorted_tags = np.asarray(node_tags)[order]
        sorted_xyz = np.asarray(xyz_raw).reshape(-1, 3)[order]
        types, _, raw = gmsh.model.mesh.getElements(3)
        if list(types) != [4]:
            raise ValueError("Expected only first-order4-node tetrahedra")
        tag_tets = np.asarray(raw[0]).reshape(-1, 4)
        if len(tag_tets) > cfg["budget"]["max_tetrahedra"]:
            raise ValueError("Mesh exceeds150k tetrahedron budget")
        used_tags = np.unique(tag_tets)
        points = sorted_xyz[np.searchsorted(sorted_tags, used_tags)]
        tets = np.searchsorted(used_tags, tag_tets).astype(np.int64)
        groups = {}
        for group in ("hot", "cold"):
            tags = np.unique(
                np.concatenate(
                    [
                        gmsh.model.mesh.getNodes(2, face, includeBoundary=True)[0]
                        for face in faces[group]
                    ]
                )
            )
            indices = np.searchsorted(used_tags, tags)
            if np.any(indices >= len(used_tags)) or not np.array_equal(used_tags[indices], tags):
                raise ValueError("Boundary includes node not used by the air tetrahedra")
            groups[group] = indices.astype(np.int64)
        mesh_file = output / "mesh.msh"
        gmsh.write(str(mesh_file))
        metadata = {
            "source": "independent_analytic_fixture_not_rocket_CAD",
            "fixture": name,
            "gmsh_version": gmsh.__version__,
            "requested_mesh_size_m": size,
            "units": "m",
            "unlisted_exterior_faces": "insulated",
            "explicit_physical_surface_tags": faces,
            "insulated_divider_includes_solid_conduction": False,
            "boundary_edge_ownership": "Hot/cold faces are disjoint; their edges remain Dirichlet where adjacent to insulated faces.",
            "mesh_msh_sha256": sha(mesh_file),
        }
        return GasMesh(points, tets, groups, metadata)
    finally:
        gmsh.finalize()


def analytic_case(name: str, cfg: dict[str, Any], points: Any) -> tuple[float, Any, str]:
    """Independent Fourier-law exact fields for these restricted geometries."""
    d = cfg["fixture_dimensions_m"]
    k = cfg["conductivity_w_m_k_estimate"]
    hot, cold = cfg["boundary_temperature_k"]
    if name == "concentric_cylinder":
        ratio = d["cylinder_outer_radius"] / d["cylinder_inner_radius"]
        conductance = 2 * math.pi * k * d["cylinder_length"] / math.log(ratio)
        radius = np.linalg.norm(points[:, :2], axis=1)
        field = cold + (hot - cold) * np.log(d["cylinder_outer_radius"] / radius) / math.log(ratio)
        formula = "G=2*pi*k*L/ln(ro/ri); T=Tc+(Th-Tc)*ln(ro/r)/ln(ro/ri), insulated ends."
    elif name == "insulated_divider":
        conductance = 0.0
        field = np.where(points[:, 0] < d["length"] / 2, hot, cold)
        formula = "Two disconnected air volumes each with one isothermal reservoir and other faces insulated: G=0, each volume constant T. No barrier/solid conduction modeled."
    else:
        area = d["width"] * d["height"]
        if name == "longitudinal_obstruction":
            area -= d["obstruction_width"] * d["obstruction_height"]
        conductance = k * area / d["length"]
        field = hot + (cold - hot) * points[:, 0] / d["length"]
        formula = "G=k*A_open/L; T linear along x. All longitudinal exterior/obstruction faces insulated. The obstruction occupies the entire length; no short-aperture spreading approximation."
    return conductance, field, formula


def worker(config: Path, fixture: str, level: int, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config.read_text())
    if scipy.__version__ != cfg["versions"]["scipy"] or np.__version__ != cfg["versions"]["numpy"]:
        raise ValueError("Pinned NumPy/SciPy versions mismatch")
    output.mkdir(parents=True, exist_ok=True)
    mesh = create_fixture(fixture, cfg["mesh_sizes_m"][level], cfg, output)
    np.savez_compressed(output / "mesh.npz", points_m=mesh.points_m, tetrahedra=mesh.tetrahedra)
    (output / "groups.json").write_text(
        json.dumps(
            {
                "boundary_groups": {
                    name: nodes.tolist() for name, nodes in mesh.boundary_groups.items()
                },
                "metadata": mesh.metadata,
            },
            indent=2,
        )
        + "\n"
    )
    # Exercise the exact data interface expected from a later CAD exporter.
    reloaded = load_gas_mesh(output / "mesh.npz", output / "groups.json")
    result = group_conductance(
        reloaded,
        cfg["conductivity_w_m_k_estimate"],
        max_tetrahedra=cfg["budget"]["max_tetrahedra"],
        algebra_relative_tolerance=cfg["verification"]["algebra_relative_tolerance"],
    )
    rates = result.evaluate(cfg["boundary_temperature_k"])
    expected_g, exact_temperature, formula = analytic_case(fixture, cfg, mesh.points_m)
    calculated_g = float(result.matrix_w_k[0, 0])
    delta_t = cfg["boundary_temperature_k"][0] - cfg["boundary_temperature_k"][1]
    calculated_heat = float(rates["heat_into_gas_w"][0])
    expected_heat = expected_g * delta_t
    field_error = float(np.abs(rates["nodal_temperature_k"] - exact_temperature).max())
    if expected_g:
        raw_relative = (calculated_heat - expected_heat) / expected_heat
        heat_verified = abs(raw_relative) <= cfg["verification"]["known_case_relative_tolerance"]
    else:
        raw_relative = None
        heat_verified = bool(
            max(np.abs(rates["heat_into_gas_w"]))
            <= cfg["verification"]["zero_heat_absolute_tolerance_w"]
        )
    algebra_tol = result.diagnostics["algebra_check_tolerance_w_k"]
    energy_scale = max(abs(rates["element_dirichlet_form_w_times_k"]), 1e-12)
    energy_relative = abs(rates["dirichlet_form_difference_w_times_k"]) / energy_scale
    conservation = abs(rates["sum_heat_into_gas_w"]) <= max(1e-11, algebra_tol * abs(delta_t) * 10)
    energy_check = abs(rates["dirichlet_form_difference_w_times_k"]) <= max(
        1e-10, energy_scale * 1e-7
    )
    np.savez_compressed(
        output / "field.npz",
        points_m=mesh.points_m,
        nodal_temperature_k=rates.pop("nodal_temperature_k"),
        element_gradient_k_m=rates.pop("element_gradient_k_m"),
    )
    payload = {
        "fixture": fixture,
        "level": level,
        "mesh_size_m": cfg["mesh_sizes_m"][level],
        "elapsed_s": time.monotonic() - started,
        "group_ids": list(result.group_ids),
        "C_raw_w_k": result.matrix_w_k.tolist(),
        "net_inward_to_boundary_matrix_raw_w_k": result.net_inward_matrix_w_k.tolist(),
        "diagnostics": result.diagnostics,
        "rates": rates,
        "analytic_formula": formula,
        "expected_conductance_w_k": expected_g,
        "calculated_hot_self_conductance_w_k": calculated_g,
        "expected_heat_into_gas_from_hot_w": expected_heat,
        "calculated_heat_into_gas_from_hot_w": calculated_heat,
        "raw_heat_error_w": calculated_heat - expected_heat,
        "raw_heat_relative_error": raw_relative,
        "nodal_temperature_max_absolute_error_k": field_error,
        "energy_relative_difference": energy_relative,
        "energy_conservation_pass": conservation and energy_check,
        "heat_balance_pass": conservation,
        "dirichlet_quadratic_form_agreement_pass": energy_check,
        "analytic_heat_check_pass": heat_verified,
        "analytic_temperature_check_pass": field_error
        <= cfg["verification"]["interior_temperature_absolute_tolerance_k"],
        "method_algebra_pass": result.diagnostics["algebra_checks_pass"],
        "raw_matrix_altered": False,
        "actual_rocket_temperature_or_matrix_accepted": False,
        "artifacts": [
            {"path": str(output / name), "sha256": sha(output / name)}
            for name in ("mesh.msh", "mesh.npz", "groups.json", "field.npz")
        ],
    }
    (output / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def campaign(config: Path, output: Path) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(config.read_text())
    if (
        cfg["budget"]["threads"] != 1
        or cfg["budget"]["max_tetrahedra"] > 150000
        or cfg["budget"]["seconds_per_fixture_all_refinements"] > 180
    ):
        raise ValueError("OneCPU/150k-tet/180s fixture budget must be retained")
    if len(cfg["mesh_sizes_m"]) != 3 or not all(
        a > b > 0 for a, b in zip(cfg["mesh_sizes_m"], cfg["mesh_sizes_m"][1:])
    ):
        raise ValueError("Exactly three decreasing positive mesh sizes required")
    sources = [
        config,
        Path(__file__),
        Path("src/analysis/gas_conduction.py"),
        Path("pyproject.toml"),
        Path("requirements-wo03.txt"),
        Path("docs/ENVIRONMENT.md"),
    ]
    before = {str(path): sha(path) for path in sources}
    output.mkdir(parents=True, exist_ok=True)
    results = []
    stopped = None
    for fixture in cfg["fixtures"]:
        fixture_started = time.monotonic()
        levels = []
        for level in range(3):
            destination = output / fixture / f"level-{level}"
            remaining = cfg["budget"]["seconds_per_fixture_all_refinements"] - (
                time.monotonic() - fixture_started
            )
            try:
                process = subprocess.run(
                    [
                        sys.executable,
                        str(Path(__file__)),
                        "--config",
                        str(config),
                        "--worker",
                        fixture,
                        "--level",
                        str(level),
                        "--output",
                        str(destination),
                    ],
                    text=True,
                    capture_output=True,
                    timeout=max(0.01, remaining),
                    check=False,
                )
                if process.returncode:
                    stopped = {
                        "fixture": fixture,
                        "level": level,
                        "reason": "invalid_mesh_or_method_or_worker_error",
                        "stderr": process.stderr[-8000:],
                        "stdout": process.stdout[-2000:],
                    }
                    break
                record = json.loads((destination / "record.json").read_text())
                levels.append(record)
                print(
                    f"{fixture} level{level}: {record['diagnostics']['tetrahedra']} tets, heat_error={record['raw_heat_error_w']:.6g}W, algebra={record['method_algebra_pass']}",
                    flush=True,
                )
                if not record["method_algebra_pass"] or not record["energy_conservation_pass"]:
                    stopped = {
                        "fixture": fixture,
                        "level": level,
                        "reason": "decisive_algebra_or_conservation_failure",
                    }
                    break
            except subprocess.TimeoutExpired:
                stopped = {
                    "fixture": fixture,
                    "level": level,
                    "reason": "180s_total_fixture_budget_exceeded",
                }
                break
        if len(levels) == 3:
            old, new = (
                levels[-2]["calculated_hot_self_conductance_w_k"],
                levels[-1]["calculated_hot_self_conductance_w_k"],
            )
            if fixture == "insulated_divider":
                change = None
                converged = all(row["analytic_heat_check_pass"] for row in levels)
            else:
                change = abs(new - old) / abs(new)
                converged = (
                    change < cfg["verification"]["successive_conductance_relative_tolerance"]
                )
            verified = (
                converged
                and all(
                    row["method_algebra_pass"] and row["energy_conservation_pass"] for row in levels
                )
                and levels[-1]["analytic_heat_check_pass"]
                and levels[-1]["analytic_temperature_check_pass"]
            )
        else:
            change, converged, verified = None, False, False
        results.append(
            {
                "fixture": fixture,
                "levels": levels,
                "elapsed_s": time.monotonic() - fixture_started,
                "last_two_conductance_relative_change": change,
                "three_level_convergence_pass": converged,
                "fixture_verified": verified,
            }
        )
        if stopped:
            break
    after = {str(path): sha(path) for path in sources}
    payload = {
        "run_id": datetime.now(UTC).strftime("wo03-gas-conduction-%Y%m%dT%H%M%S%fZ"),
        "elapsed_s": time.monotonic() - started,
        "compute_cost_usd": 0,
        "threads": 1,
        "input_sha256_before": before,
        "input_sha256_after": after,
        "inputs_unchanged": before == after,
        "versions": cfg["versions"],
        "fixtures": results,
        "stopped": stopped,
        "source_independent_fixture_method_verified": not stopped
        and len(results) == 4
        and all(row["fixture_verified"] for row in results),
        "actual_CAD_fluid_boolean_and_face_mapping": None,
        "gas_advection_or_radiation_included": False,
        "actual_rocket_matrix_or_temperature_acceptance": False,
        "flight_ready": False,
    }
    (output / "record.json").write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n")
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-gas-conduction.yaml")
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument(
        "--worker",
        choices=["slab", "concentric_cylinder", "insulated_divider", "longitudinal_obstruction"],
    )
    parser.add_argument("--level", type=int, default=0)
    args = parser.parse_args()
    output = args.output or Path(yaml.safe_load(args.config.read_text())["default_output"])
    if args.worker:
        worker(args.config, args.worker, args.level, output)
    else:
        result = campaign(args.config, output)
        print(output / "record.json")
        return 0 if result["source_independent_fixture_method_verified"] else 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
