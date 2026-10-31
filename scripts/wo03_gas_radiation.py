"""Execute independent gas/radiation/halfwall and opening-boundary fixtures."""

from __future__ import annotations

import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.optimize import brentq

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.gas_conduction import assemble_tetra_conductivity
from src.analysis.gas_radiation import GasRadiationNetwork
from src.analysis.robin_gas import RobinGasMesh, factor_robin_gas

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-gas-radiation.yaml"


def slab_factor(divisions: int, cfg: dict[str, Any], *, prescribed_cold: bool = False) -> Any:
    """Conforming six-tet cubical cells: independent of rocket CAD/Gmsh."""
    if not 1 <= divisions <= 8:
        raise ValueError("Bounded fixture divisions must be1..8")
    dims = np.array(cfg["slab_dimensions_m"])
    indices = np.indices((divisions + 1,) * 3).reshape(3, -1).T
    points = indices / divisions * dims
    index = {tuple(p): i for i, p in enumerate(indices)}
    local = np.array(
        [[0, 1, 2, 6], [0, 2, 3, 6], [0, 3, 7, 6], [0, 7, 4, 6], [0, 4, 5, 6], [0, 5, 1, 6]]
    )
    offsets = np.array(
        [[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0], [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1]]
    )
    cells = []
    for origin in np.indices((divisions,) * 3).reshape(3, -1).T:
        vertices = np.array([index[tuple(p)] for p in offsets + origin])
        cells.extend(vertices[local].tolist())
    tets = np.array(cells)
    conductivity = cfg["air_conductivity_w_m_k"]
    assembly = assemble_tetra_conductivity(points, tets, conductivity)
    triangles = assembly.exterior_triangles.copy()
    normal = np.cross(
        points[triangles[:, 1]] - points[triangles[:, 0]],
        points[triangles[:, 2]] - points[triangles[:, 0]],
    )
    toward_interior = points[assembly.exterior_opposite_nodes] - points[triangles[:, 0]]
    inward = np.sum(normal * toward_interior, axis=1) > 0
    triangles[inward] = triangles[inward][:, [0, 2, 1]]
    x = points[triangles, 0]
    groups = np.where(np.all(x == 0, axis=1), 0, np.where(np.all(x == dims[0], axis=1), 1, 2))
    cold = (
        {"kind": "dirichlet", "temperature_id": "outside_gas"}
        if prescribed_cold
        else {"kind": "robin", "bulk_id": "cold", "h_w_m2_k": cfg["cold_halfwall_h_w_m2_k"]}
    )
    return factor_robin_gas(
        RobinGasMesh(points, tets, triangles, groups, {"fixture": "affine slab"}),
        {
            0: {"kind": "robin", "bulk_id": "hot", "h_w_m2_k": cfg["hot_halfwall_h_w_m2_k"]},
            1: cold,
            2: {"kind": "insulated"},
        },
        conductivity,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=CONFIG)
    parser.add_argument("--preset", choices=("tiny", "sim", "rl", "real"), default="tiny")
    args = parser.parse_args()
    start = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_text())
    inputs = [
        args.config,
        Path(__file__),
        ROOT / "src/analysis/gas_radiation.py",
        ROOT / "src/analysis/robin_gas.py",
        ROOT / "src/analysis/gas_conduction.py",
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    run_id = "wo03-gas-radiation-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir()
    for path in hashes:
        target = folder / "source-snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    length, width, height = cfg["slab_dimensions_m"]
    area = width * height
    hot, cold = cfg["bulk_temperatures_k"]
    eh, ec = cfg["plate_emissivities"]
    radiation = cfg["sigma_w_m2_k4"] * area / (1 / eh + 1 / ec - 1)
    matrix = radiation * np.array([[-1.0, 1.0], [1.0, -1.0]])
    rh = 1 / (area * cfg["hot_halfwall_h_w_m2_k"])
    rc = 1 / (area * cfg["cold_halfwall_h_w_m2_k"])

    def balance(q: float) -> float:
        th, tc = hot - rh * q, cold + rc * q
        return (
            cfg["air_conductivity_w_m_k"] * area / length * (th - tc)
            + radiation * (th**4 - tc**4)
            - q
        )

    expected = brentq(balance, 0, (hot - cold) / (rh + rc), xtol=1e-14)
    rows = []
    for divisions in cfg["divisions"]:
        factor = slab_factor(divisions, cfg)
        network = GasRadiationNetwork(
            factor,
            matrix,
            (0, 1),
            (-1, -1),
            (),
            "Isothermal parallel plates with insulated lateral gas boundaries",
        )
        by_id = {"hot": hot, "cold": cold}
        theta = np.array([by_id[name] for name in factor.bulk_ids])
        result = network.solve(
            theta, np.array([]), np.array([]), absolute_tolerance_k=1e-10, reconstruct=True
        )
        rates = result.heat_into_material_and_gas_reservoir_w
        expected_rates = np.array(
            [-expected if name == "hot" else expected for name in factor.bulk_ids]
        )
        assert result.reconstruction is not None
        rows.append(
            {
                "divisions_per_axis": divisions,
                "nodes": len(factor.mesh.points_m),
                "tetrahedra": len(factor.mesh.tetrahedra),
                "expected_heat_w": expected,
                "actual_heat_into_reservoirs_w": dict(
                    zip(factor.bulk_ids, rates.tolist(), strict=True)
                ),
                "maximum_expected_heat_error_w": float(np.max(np.abs(rates - expected_rates))),
                "surface_residual_k": result.surface_residual_k,
                "energy_residual_w": result.enclosure_energy_residual_w,
                "newton_iterations": result.iterations,
                "mean_reconstruction_difference_k": result.reconstruction[
                    "nonlinear_mean_reconstruction_difference_k"
                ],
                "P1_minimum_k": result.reconstruction["P1_nodal_minimum_k"],
                "P1_maximum_k": result.reconstruction["P1_nodal_maximum_k"],
                "FEM_algebra_checks_pass": factor.diagnostics["algebra_checks_pass"],
            }
        )
    # The opening's gas state remains300K; its independent brightness becomes500K.
    factor = slab_factor(2, cfg, prescribed_cold=True)
    black = cfg["sigma_w_m2_k4"] * area * np.array([[-1.0, 1.0], [1.0, -1.0]])
    network = GasRadiationNetwork(
        factor,
        black,
        (0, -1),
        (-1, 0),
        ("outside_radiation",),
        "Black opening brightness separate from physical gas temperature",
    )
    result = network.solve(
        np.array([350.0]),
        np.array([300.0]),
        np.array([500.0]),
        absolute_tolerance_k=1e-10,
        reconstruct=True,
    )
    assert result.reconstruction is not None
    field = result.reconstruction["nodal_temperature_k"]
    opening_error = float(np.max(np.abs(field[factor.mesh.points_m[:, 0] == length] - 300)))
    opening = {
        "physical_gas_temperature_k": 300,
        "radiative_brightness_temperature_k": 500,
        "maximum_opening_node_temperature_error_k": opening_error,
        "heat_into_bulk_and_gas_reservoirs_w": result.heat_into_material_and_gas_reservoir_w.tolist(),
        "heat_into_brightness_reservoir_w": result.heat_into_radiative_brightness_reservoir_w.tolist(),
        "energy_residual_w": result.enclosure_energy_residual_w,
    }
    passed = (
        all(
            row["FEM_algebra_checks_pass"]
            and row["maximum_expected_heat_error_w"] < 1e-10
            and abs(row["energy_residual_w"]) < 1e-10
            for row in rows
        )
        and opening_error < 1e-10
    )
    record = {
        "run_id": run_id,
        "preset": args.preset,
        "input_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "expected_method": "Independent scalar energy balance: q=k_air*A/L*(Ts_hot-Ts_cold)+sigma*A/(1/eps_hot+1/eps_cold-1)*(Ts_hot^4-Ts_cold^4); Ts_hot=Tbulk_hot-q/(h_hot*A), Ts_cold=Tbulk_cold+q/(h_cold*A).",
        "slab_refinement": rows,
        "independent_opening_inputs": opening,
        "known_case_checks_pass": passed,
        "scope": {
            "radiation_projection": "group mean temperature to fourth power; groupwise uniform integrated flux",
            "actual_rocket_temperature": "unavailable",
            "physical_hot_spots": "unavailable",
            "thermal_acceptance": False,
            "flight_ready": False,
        },
        "elapsed_s": time.perf_counter() - start,
        "cost_usd": 0,
    }
    path = folder / "record.json"
    path.write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str(path.relative_to(ROOT)),
                "checks_pass": passed,
                "maximum_heat_error_w": max(row["maximum_expected_heat_error_w"] for row in rows),
                "elapsed_s": record["elapsed_s"],
            }
        )
    )
    return 0 if passed and record["inputs_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
