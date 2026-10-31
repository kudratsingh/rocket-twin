"""Read ONLY completed failed gas fields/maps; no factor, mesher or heat solve.

Local tet coefficient audit: K_e=k*V*grad(N)*grad(N). Cylinder reference:
q/(2piL)=(Th-Tb)/(log(b/a)/k_air+log(r_cell/b)/k_liner),
T(r)=Th-q/(2piL*k_air)*log(r/a). Fourier cylinder resistance: DOE-HDBK-
1012/2-92 HT-02. This is a long-cylinder fixture comparison with finite-end
limits, not a replacement model. P1 triangle mean(T^4)=sum15monomials/15.
No coefficient, eigenvalue, temperature or response is clipped/retuned.
"""

from __future__ import annotations

import os
from pathlib import Path

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"]:
    os.environ[key] = "1"

import argparse
import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_medium_mesh_diagnostic import sha, write


def local_node(
    node: int,
    T: Any,
    mesh: Any,
    wall: Any,
    correspondence: Any,
    faces: Any,
    airk: float,
    cold: float,
) -> dict[str, Any]:
    points, tets = mesh["points_m"], mesh["tetrahedra"]
    incident = np.flatnonzero(np.any(tets == node, axis=1))
    rows = defaultdict(float)
    details = []
    for tet_id in incident:
        ids = tets[tet_id]
        xyz = points[ids]
        J = np.stack([xyz[i] - xyz[0] for i in [1, 2, 3]], axis=1)
        det = float(np.linalg.det(J))
        inv = np.linalg.inv(J)
        grad = np.vstack((-inv.sum(axis=0), inv))
        K = airk * det / 6 * (grad @ grad.T)
        local = int(np.flatnonzero(ids == node)[0])
        for j, value in zip(ids, K[local], strict=True):
            rows[int(j)] += float(value)
        maxedge = float(np.linalg.norm(xyz[:, None] - xyz[None, :], axis=2).max())
        details.append(
            {
                "tet_index": int(tet_id),
                "node_ids": ids.tolist(),
                "volume_m3": det / 6,
                "scaled_determinant": det / maxedge**3,
                "maximum_edge_mm": maxedge * 1000,
                "edge_J_condition_number": float(np.linalg.cond(J)),
                "local_positive_offdiagonals": int(np.sum(np.delete(K[local], local) > 0)),
            }
        )
    boundary = np.flatnonzero(np.any(mesh["boundary_triangles"] == node, axis=1))
    wrows = defaultdict(float)
    rhs = 0.0
    wdetails = []
    source_to_row = {int(s): i for i, s in enumerate(wall["original_triangle_indices"])}
    liner_lookup = {int(i): j for j, i in enumerate(wall["liner_Robin_local_indices"])}
    for triangle_id in boundary:
        source_id = int(correspondence["boundary_source_triangle_ids"][triangle_id])
        if source_id not in source_to_row:
            continue
        wi = source_to_row[source_id]
        perm = correspondence["boundary_source_vertex_permutation"][triangle_id]
        M = wall["wall_matrix_w_k"][wi][np.ix_(perm, perm)]
        ids = mesh["boundary_triangles"][triangle_id]
        local = int(np.flatnonzero(ids == node)[0])
        for j, value in zip(ids, M[local], strict=True):
            wrows[int(j)] += float(value)
        if wall["bulk_index"][wi] >= 0:
            B = wall["bulk_load_vector_w_k"][wi][perm]
            D = float(wall["bulk_diagonal_w_k"][wi])
        else:
            li = liner_lookup[wi]
            B = wall["liner_bulk_load_vectors_w_k"][li].sum(axis=0)[perm]
            D = float(wall["liner_bulk_diagonals_w_k"][li].sum())
        rhs += float(B[local] * cold)
        face_id = int(mesh["boundary_face_ids"][triangle_id])
        f = faces[face_id]
        wdetails.append(
            {
                "triangle_id": int(triangle_id),
                "source_triangle_id": source_id,
                "face_id": face_id,
                "group_id": int(mesh["boundary_group_ids"][triangle_id]),
                "part_id": f["part_id"],
                "material": f["material"],
                "halfwall_scope": f["halfwall"],
                "area_m2": float(mesh["boundary_area_m2"][triangle_id]),
                "integrated_h_area_mean_w_m2_k": D / mesh["boundary_area_m2"][triangle_id],
                "row_positive_offdiagonals": int(np.sum(np.delete(M[local], local) > 0)),
            }
        )
    combined = dict(rows)
    for j, v in wrows.items():
        combined[j] = combined.get(j, 0) + v

    def signs(data: Any) -> Any:
        off = [v for j, v in data.items() if j != node]
        return {
            "diagonal_w_k": data.get(node, 0.0),
            "offdiagonal_positive_count": sum(v > 0 for v in off),
            "offdiagonal_positive_sum_w_k": sum(v for v in off if v > 0),
            "offdiagonal_negative_sum_w_k": sum(v for v in off if v < 0),
            "row_sum_w_k": sum(data.values()),
        }

    group_ids = sorted(set(map(int, mesh["boundary_group_ids"][boundary])))
    return {
        "node_index_zero_based": node,
        "temperature_k": float(T[node]),
        "CAD_coordinates_mm": (points[node] * 1000).tolist(),
        "boundary": bool(len(boundary)),
        "physical_face_ids": sorted(set(map(int, mesh["boundary_face_ids"][boundary]))),
        "radiation_group_ids": group_ids,
        "incident_tetrahedra": details,
        "incident_Robin_triangles": wdetails,
        "gas_row": signs(rows),
        "wall_row": signs(wrows),
        "combined_row": signs(combined),
        "local_equation_residual_recomputed_w": sum(v * T[j] for j, v in combined.items()) - rhs,
        "local_shifted_equation_residual_w": sum(v * (T[j] - cold) for j, v in combined.items()),
        "gradient_inverse_scope": "geometric3x3inverse only; no PDE factor/solve",
        "stencil": [
            {
                "node_id": j,
                "T_k": float(T[j]),
                "gas_w_k": rows.get(j, 0.0),
                "Robin_w_k": wrows.get(j, 0.0),
            }
            for j in sorted(combined)
        ],
    }


def worker(cfg: Any, folder: Path) -> None:
    start = time.monotonic()
    record = json.loads(Path(cfg["observed"]).read_text())
    meta = json.loads(Path(cfg["response_metadata"]).read_text())
    with np.load(cfg["fields"], allow_pickle=False) as z:
        fields = {k: z[k] for k in z.files}
    with np.load(cfg["mesh"], allow_pickle=False) as z:
        mesh = {k: z[k] for k in z.files}
    with np.load(cfg["response"], allow_pickle=False) as z:
        response = {k: z[k] for k in z.files}
    with np.load(cfg["wall"], allow_pickle=False) as z:
        wall = {k: z[k] for k in z.files}
    with np.load(cfg["correspondence"], allow_pickle=False) as z:
        correspondence = {k: z[k] for k in z.files}
    groups = json.loads(Path(cfg["groups"]).read_text())
    faces = {r["fluid_face_id"]: r for r in json.loads(Path(cfg["material_faces"]).read_text())}
    case = int(np.flatnonzero(fields["case_ids"] == cfg["probe"])[0])
    T = fields["nodal_temperature_k"][case]
    means = fields["area_mean_temperature_k"][case]
    check = next(c for c in record["field_checks"] if c["id"] == cfg["probe"])
    cold, hot = check["state_minimum_k"], check["state_maximum_k"]
    local = [
        local_node(
            int(i), T, mesh, wall, correspondence, faces, cfg["air_conductivity_w_m_k"], cold
        )
        for i in [T.argmin(), T.argmax()]
    ]
    for node in local:
        hot_neighbors = []
        for entry in node["stencil"]:
            if abs(entry["T_k"] - hot) <= 1e-7 and entry["Robin_w_k"] > 0:
                incident = np.any(mesh["boundary_triangles"] == entry["node_id"], axis=1)
                hot_neighbors.append(
                    {
                        **entry,
                        "physical_group_ids": np.unique(
                            mesh["boundary_group_ids"][incident]
                        ).tolist(),
                    }
                )
        node["hot_Robin_neighbors"] = hot_neighbors
        node["positive_Robin_hot_neighbor_term_in_shifted_row_w"] = sum(
            e["Robin_w_k"] * (e["T_k"] - cold) for e in hot_neighbors
        )
    write(folder / "extreme-node-local-stencils.json", local)
    tris = mesh["boundary_triangles"]
    gids = mesh["boundary_group_ids"]
    areas = mesh["boundary_area_m2"]
    points = mesh["points_m"]
    group_rows = []
    for g in groups:
        gid = g["group_id"]
        ids = np.unique(tris[gids == gid])
        p = points[ids] * 1000
        group_rows.append(
            {
                **g,
                "probe_mean_temperature_k": float(means[gid]),
                "node_temperature_min_k": float(T[ids].min()),
                "node_temperature_max_k": float(T[ids].max()),
                "below_ambient_nodes": int(np.sum(T[ids] < cold - cfg["interval_tolerance_k"])),
                "CAD_coordinate_bounds_mm": [p.min(axis=0).tolist(), p.max(axis=0).tolist()],
                "actual_face_interior_points_mm": [
                    faces[i]["ownership_interior_point_mm"] for i in g["fluid_face_ids"][:3]
                ],
            }
        )
    write(folder / "all-group-field-locations.json", group_rows)

    def top_entries(matrix: Any, kind: str) -> Any:
        n = cfg["caps"]["top_responses"]
        idx = np.argpartition(matrix.ravel(), n)[:n]
        idx = idx[np.argsort(matrix.ravel()[idx])]
        values = []
        for flat in idx:
            i, j = np.unravel_index(flat, matrix.shape)
            source = (
                (meta["bulk_ids"] + meta["prescribed_ids"])[j]
                if kind == "reservoir"
                else group_rows[j]
            )
            values.append(
                {
                    "target_group": group_rows[i],
                    "source": source,
                    "source_column": int(j),
                    "value": float(matrix[i, j]),
                    "units": "K/K" if kind == "reservoir" else "K/W",
                }
            )
        return values

    write(
        folder / "most-negative-mean-reservoir-responses.json",
        top_entries(response["mean_by_reservoir_temperature"], "reservoir"),
    )
    write(
        folder / "most-negative-mean-positive-load-responses.json",
        top_entries(response["mean_by_group_neumann_k_w"], "load"),
    )
    inner = next(
        f
        for f in faces.values()
        if f["part_id"] == "motor_liner"
        and f["halfwall"].get("bulk_state_override") == "motor_liner.cell_0"
    )
    cyl = cfg["cylinder"]
    a, b = cyl["motor_radius_m"], cyl["liner_inner_radius_m"]
    rb = inner["halfwall"]["bulk_radius_m"]
    q2pi = (hot - cold) / (
        np.log(b / a) / cfg["air_conductivity_w_m_k"]
        + np.log(rb / b) / cyl["liner_conductivity_w_m_k"]
    )
    radius = np.linalg.norm(points[:, :2], axis=1)
    mid = (cyl["start_m"] + cyl["end_m"]) / 2
    length = cyl["end_m"] - cyl["start_m"]
    selected = np.flatnonzero(
        (radius >= a - 1e-10)
        & (radius <= b + 1e-10)
        & (np.abs(points[:, 2] - mid) <= length * cyl["central_length_fraction"] / 2)
    )
    analytic = hot - q2pi / cfg["air_conductivity_w_m_k"] * np.log(radius[selected] / a)
    error = T[selected] - analytic
    np.savez(
        folder / "midspan-cylinder-comparison.npz",
        node_indices=selected,
        coordinates_m=points[selected],
        saved_field_k=T[selected],
        long_cylinder_reference_k=analytic,
        difference_k=error,
    )
    cylinder = {
        "nodes": len(selected),
        "motor_radius_m": a,
        "liner_radius_m": b,
        "cell_center_radius_m": rb,
        "halfwall_h_w_m2_k": inner["h_nominal_w_m2_k"],
        "reference_liner_surface_k": float(
            hot - q2pi / cfg["air_conductivity_w_m_k"] * np.log(b / a)
        ),
        "reference_heat_per_axial_length_w_m": float(2 * np.pi * q2pi),
        "selected_axial_range_m": [
            mid - length * cyl["central_length_fraction"] / 2,
            mid + length * cyl["central_length_fraction"] / 2,
        ],
        "minimum_distance_from_end_in_gap_widths": float(
            (1 - cyl["central_length_fraction"]) * length / 2 / (b - a)
        ),
        "saved_T_range_k": [float(T[selected].min()), float(T[selected].max())],
        "error_min_max_k": [float(error.min()), float(error.max())],
        "RMS_error_k": float(np.sqrt(np.mean(error**2))),
        "finite_end_error_bound_available": False,
        "scope": "steady coaxial long-cylinder reference; finiteend/numericaltracecomparison only, no new heat solution",
    }
    traces = []
    for gid, expected in [(495, hot), (523, cylinder["reference_liner_surface_k"])]:
        xyz = points[tris[gids == gid]]
        axial_spans = np.ptp(xyz[:, :, 2], axis=1)
        values_surface = T[tris[gids == gid]]
        segments = []
        for coordinates, temperatures in zip(xyz, values_surface, strict=True):
            endpoints = []
            for i, j in [(0, 1), (1, 2), (2, 0)]:
                if (coordinates[i, 2] - mid) * (coordinates[j, 2] - mid) < 0:
                    fraction = (mid - coordinates[i, 2]) / (coordinates[j, 2] - coordinates[i, 2])
                    endpoints.append(
                        (
                            coordinates[i] + fraction * (coordinates[j] - coordinates[i]),
                            temperatures[i] + fraction * (temperatures[j] - temperatures[i]),
                        )
                    )
            if len(endpoints) == 2:
                segment_length = float(np.linalg.norm(endpoints[1][0] - endpoints[0][0]))
                errors = [float(e[1] - expected) for e in endpoints]
                segments.append((segment_length, errors, [float(e[1]) for e in endpoints]))
        total_length = sum(s[0] for s in segments)
        traces.append(
            {
                "group_id": gid,
                "part_id": groups[gid]["part_id"],
                "surface_triangle_count": len(xyz),
                "maximum_axial_facet_span_mm": float(axial_spans.max() * 1000),
                "maximum_axial_span_over_gap_width": float(axial_spans.max() / (b - a)),
                "midplane_segments": len(segments),
                "midplane_trace_temperature_min_max_k": [
                    min(t for s in segments for t in s[2]),
                    max(t for s in segments for t in s[2]),
                ],
                "length_weighted_RMS_error_against_reference_k": float(
                    np.sqrt(
                        sum(
                            s[0] * (s[1][0] ** 2 + s[1][0] * s[1][1] + s[1][1] ** 2) / 3
                            for s in segments
                        )
                        / total_length
                    )
                ),
                "reference_physical_surface_temperature_k": expected,
                "scope": "evaluation of saved P1 boundary trace, no new field solve",
            }
        )
    cylinder["midplane_boundary_trace_and_axial_resolution"] = traces
    values = T[tris]
    fourth = np.zeros(len(tris))
    for aa in range(5):
        for bb in range(5 - aa):
            fourth += values[:, 0] ** aa * values[:, 1] ** bb * values[:, 2] ** (4 - aa - bb) / 15
    ag = np.bincount(gids, weights=areas, minlength=len(groups))
    mean4 = np.bincount(gids, weights=areas * fourth, minlength=len(groups)) / ag
    delta4 = mean4 - means**4
    fixed = {r["radiation_group_id"] for r in record["physical_boundary_alias_table"]}
    material_delta = delta4.copy()
    for gid in fixed:
        material_delta[gid] = 0.0  # DIFFERENCE held fixed, never assign0Kbrightness.
    with np.load(cfg["radiosity_C"]) as z:
        C = z["inward_w_k4"]
        Cids = z["group_ids"]
        Carea = z["group_area_m2"]
    if not np.array_equal(Cids, np.arange(len(groups))):
        raise ValueError("Radiation group order mismatch")
    dq = C @ material_delta
    order = np.argsort(np.abs(dq))[::-1][:20]
    radiation = {
        "existing_C_only_no_radiosity_factor": True,
        "meanT4_minus_meanT4power_max_k4": float(delta4.max()),
        "maximum_abs_projected_delta_w": float(np.abs(dq).max()),
        "sum_projected_delta_w": float(dq.sum()),
        "half_L1_exchange_change_w": float(np.abs(dq).sum() / 2),
        "fixed_gas_motor_or_opening_brightness_difference_held_zero": sorted(fixed),
        "unknown_radiative_brightness_temperatures_not_assigned": True,
        "maximum_group_area_relative_difference": float(np.max(np.abs(ag / Carea - 1))),
        "top_changes": [
            {
                "group_id": int(i),
                "part_id": groups[i]["part_id"],
                "delta_net_inward_w": float(dq[i]),
                "mean_k": float(means[i]),
                "mean4_minus_mean_to_fourth_k4": float(delta4[i]),
            }
            for i in order
        ],
        "scope": "THISfaileduncoupledstaticprobe only; no coupledtemperature prediction",
    }
    np.savez(
        folder / "radiation-projection-difference.npz",
        group_ids=Cids,
        area_mean_fourth_k4=mean4,
        fourth_power_of_mean_k4=means**4,
        material_delta_fourth_k4=material_delta,
        delta_net_inward_w=dq,
    )
    boundary_nodes = np.unique(tris)
    boundary_mask = np.zeros(len(T), dtype=bool)
    boundary_mask[boundary_nodes] = True
    below = T < cold - cfg["interval_tolerance_k"]
    hotcolumn = len(meta["bulk_ids"]) + meta["prescribed_ids"].index(
        "screening_shared_required_hot_case_history_k"
    )
    G = response["mean_by_reservoir_temperature"]
    reconstructed = cold * G.sum(axis=1) + (hot - cold) * G[:, hotcolumn]
    stats = {
        "status": "READ_ONLY_DIAGNOSTIC_OF_NUMERICALLY_FAILED_OPERATOR",
        "source_numerical_checks_pass": record["numerical_checks_pass"],
        "probe": cfg["probe"],
        "global_T_min_max_k": [float(T.min()), float(T.max())],
        "below_ambient_total_nodes": int(below.sum()),
        "below_boundary_nodes": int((below & boundary_mask).sum()),
        "below_interior_nodes": int((below & ~boundary_mask).sum()),
        "group_means_below_ambient": int(np.sum(means < cold - cfg["interval_tolerance_k"])),
        "group505": group_rows[505],
        "hotcolumn_group505_coefficient": float(G[505, hotcolumn]),
        "mean_reconstruction_maximum_error_k": float(np.abs(reconstructed - means).max()),
        "cylinder_reference": cylinder,
        "radiation_projection": radiation,
        "original_probe_energy_balance_residual_w": check["energy_balance_residual_w"],
        "original_probe_free_residual_max_w": check["free_residual_max_w"],
        "original_uniform_error_k": record["field_checks"][0]["max_uniform_error_k"],
        "field_undershoot_k": float(cold - T.min()),
        "root_cause_proven": False,
        "new_factor_mesher_heat_or_ray_solve": False,
        "temperature_acceptance": False,
        "cpu_workers": 1,
        "cost_usd": 0,
        "elapsed_s": time.monotonic() - start,
    }
    write(folder / "diagnostic.json", stats)
    print(
        json.dumps(
            {
                "output": str(folder.relative_to(ROOT)),
                "elapsed_s": stats["elapsed_s"],
                "midspan": cylinder,
                "radiation_max_delta_W": radiation["maximum_abs_projected_delta_w"],
            },
            indent=2,
        ),
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/studies/wo03-gas-field-diagnostic.yaml")
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    os.chdir(ROOT)
    cfg = yaml.safe_load(Path(args.config).read_text())
    for key, expected in cfg["expected_sha256"].items():
        if sha(Path(cfg[key])) != expected:
            raise ValueError(f"Pinned completed artifact changed:{key}")
    folder = (
        ROOT / args.output
        if args.output
        else ROOT
        / "runs"
        / ("wo03-gas-field-diagnostic-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"))
    )
    if args.worker:
        worker(cfg, folder)
        return
    folder.mkdir(parents=True)
    before = {
        str(p): sha(p)
        for p in [
            Path(args.config),
            Path(__file__).relative_to(ROOT),
            *[Path(cfg[k]) for k in cfg["expected_sha256"]],
        ]
    }
    cmd = [
        sys.executable,
        "-u",
        str(Path(__file__)),
        "--config",
        args.config,
        "--worker",
        "--output",
        str(folder.relative_to(ROOT)),
    ]
    start = time.monotonic()
    with (folder / "worker.log").open("w") as log:
        child = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
        try:
            code = child.wait(timeout=cfg["caps"]["seconds"])
            capped = False
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait()
            code = None
            capped = True
    result = {
        "status": (
            "COMPLETE_READ_ONLY_FAILED_FIELD_DIAGNOSTIC"
            if code == 0
            else "INCOMPLETE_DATA_ANALYSIS"
        ),
        "child_exitcode": code,
        "time_cap_reached": capped,
        "elapsed_s": time.monotonic() - start,
        "input_sha256": before,
        "inputs_unchanged": all(sha(Path(p)) == v for p, v in before.items()),
        "new_factor_mesher_heat_or_ray_solve": False,
        "temperature_acceptance": False,
    }
    write(folder / "record.json", result)
    print(
        json.dumps(
            {
                "output": str(folder.relative_to(ROOT)),
                **{k: result[k] for k in ["status", "elapsed_s", "inputs_unchanged"]},
            },
            indent=2,
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
