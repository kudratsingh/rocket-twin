"""Read-only exact-connectivity quotient diagnostic; no Gmsh/PDE/factor call.

Only cells with the SAME four original node IDs form an equivalence class.
The representative is an existing oriented row with lowest element tag, then
lowest row index. No coordinates, distinct cells, zero cells or boundary rows
are changed. The derived proposal is not accepted mesh cleanup or adoption.
"""

from __future__ import annotations

import os

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"

import argparse
import json
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import yaml

from src.analysis.cad_gas_mesh import load_source, sha, verify_volume_mesh


def exact_quotient(
    node_ids: np.ndarray, element_tags: np.ndarray
) -> tuple[np.ndarray, list[dict[str, Any]]]:
    canonical = np.sort(node_ids, axis=1)
    _, inverse, counts = np.unique(canonical, axis=0, return_inverse=True, return_counts=True)
    row_ids = np.arange(len(node_ids))
    priority = np.lexsort((row_ids, element_tags, inverse))
    first = np.r_[True, np.diff(inverse[priority]) != 0]
    representatives = priority[first]
    keep = np.sort(representatives)
    duplicates = []
    for group in np.flatnonzero(counts > 1):
        members = np.flatnonzero(inverse == group)
        representative = members[np.lexsort((members, element_tags[members]))[0]]
        duplicates.append(
            {
                "exact_four_node_ids": canonical[representative].tolist(),
                "member_rows_zero_based": members.tolist(),
                "element_tags": element_tags[members].tolist(),
                "oriented_node_ids": node_ids[members].tolist(),
                "retained_original_row": int(representative),
                "retained_element_tag": int(element_tags[representative]),
            }
        )
    return keep, duplicates


def face_incidence(tet: np.ndarray) -> tuple[np.ndarray, dict[str, Any]]:
    all_faces = np.concatenate([tet[:, c] for c in [[0, 1, 2], [0, 1, 3], [0, 2, 3], [1, 2, 3]]])
    unique, counts = np.unique(np.sort(all_faces, axis=1), axis=0, return_counts=True)
    values, bins = np.unique(counts, return_counts=True)
    return unique[counts == 1], {
        "histogram": {str(int(k)): int(v) for k, v in zip(values, bins, strict=True)},
        "nonmanifold_faces": int((counts > 2).sum()),
        "maximum_incidence": int(counts.max()),
        "first_nonmanifold_faces": unique[counts > 2][:12].tolist(),
    }


def sorted_triangles(triangles: np.ndarray) -> np.ndarray:
    keys = np.sort(triangles, axis=1)
    return keys[np.lexsort(keys.T[::-1])]


def boundary_checks(
    mesh: dict[str, Any], source: dict[str, Any], exterior: np.ndarray, caps: dict[str, Any]
) -> dict[str, Any]:
    def different(a: np.ndarray, b: np.ndarray) -> dict[str, Any]:
        aa = np.unique(np.sort(a, axis=1), axis=0)
        bb = np.unique(np.sort(b, axis=1), axis=0)
        dtype = np.dtype((np.void, aa.dtype.itemsize * 3))
        delta = (
            np.setdiff1d(
                np.ascontiguousarray(aa).view(dtype).ravel(),
                np.ascontiguousarray(bb).view(dtype).ravel(),
            )
            .view(aa.dtype)
            .reshape(-1, 3)
        )
        return {"unique_count": len(delta), "first_node_index_triplets": delta[:8].tolist()}

    result: dict[str, Any] = {
        "exterior_not_in_fixed": different(exterior, mesh["fixed_boundary_triangles"]),
        "fixed_not_in_exterior": different(mesh["fixed_boundary_triangles"], exterior),
        "Gmsh_not_in_fixed": different(
            mesh["gmsh_boundary_triangles"], mesh["fixed_boundary_triangles"]
        ),
        "fixed_not_in_Gmsh": different(
            mesh["fixed_boundary_triangles"], mesh["gmsh_boundary_triangles"]
        ),
    }
    cad = np.array([row["cad_area_mm2"] for row in source["faces"]])
    fixed_map = {
        tuple(key): int(face)
        for key, face in zip(
            np.sort(mesh["fixed_boundary_triangles"], axis=1),
            source["boundary"]["triangle_face_index"] + 1,
            strict=True,
        )
    }
    for name, triangles, face_ids in [
        ("fixed", mesh["fixed_boundary_triangles"], source["boundary"]["triangle_face_index"] + 1),
        ("unchanged_Gmsh", mesh["gmsh_boundary_triangles"], mesh["gmsh_boundary_face_ids"]),
    ]:
        p = mesh["points_m"][triangles]
        area = np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1) / 2 * 1e6
        if not ((face_ids >= 1) & (face_ids <= len(cad))).all():
            result[name] = {"valid_face_ids": False}
            continue
        face_area = np.bincount(face_ids - 1, weights=area, minlength=len(cad))
        error = face_area / cad - 1
        group_area = np.bincount(source["face_to_group"], weights=face_area)
        group_cad = np.bincount(source["face_to_group"], weights=cad)
        group_error = group_area / group_cad - 1
        known = [fixed_map.get(tuple(key)) for key in np.sort(triangles, axis=1)]
        mismatches = int(
            sum(old is not None and old != face for old, face in zip(known, face_ids, strict=True))
        )
        result[name] = {
            "valid_face_ids": True,
            "all_original_faces_present": bool((face_area > 0).all()),
            "zero_area_boundary_elements": int((area == 0).sum()),
            "maximum_abs_face_area_error": float(abs(error).max()),
            "face_area_guard_violations": int(
                (abs(error) > caps["max_face_area_relative_error"]).sum()
            ),
            "maximum_abs_group_area_error": float(abs(group_error).max()),
            "group_area_guard_violations": int(
                (abs(group_error) > caps["max_group_area_relative_error"]).sum()
            ),
            "fixed_facet_label_mismatches": mismatches,
            "boundary_elements_without_exact_fixed_facet_key": sum(old is None for old in known),
        }
    return result


def old_validation(
    mesh: dict[str, Any], source: dict[str, Any], caps: dict[str, Any]
) -> dict[str, Any]:
    # The validator may reverse negative tet indices. Never mutate the proposal.
    copy = {
        key: value.copy() if isinstance(value, np.ndarray) else value for key, value in mesh.items()
    }
    try:
        _, diagnostic = verify_volume_mesh(
            copy,
            source["boundary"],
            source["faces"],
            source["groups"],
            source["face_to_group"],
            caps,
        )
        return {
            "passed": True,
            "diagnostics": {
                k: v for k, v in diagnostic.items() if k not in ["face_area_mm2", "group_area_mm2"]
            },
        }
    except Exception as exc:  # noqa: BLE001 - unchanged validator failure is evidence
        return {"passed": False, "error": repr(exc)}


def fixture(caps: dict[str, Any]) -> dict[str, Any]:
    points = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]]
    )
    distinct = np.array([[0, 1, 2, 3], [0, 2, 1, 4]], dtype=np.int64)
    raw = np.array([[0, 1, 2, 3], [0, 2, 3, 1], [0, 2, 1, 4]], dtype=np.int64)
    tags = np.array([100, 50, 200], dtype=np.int64)
    exterior, _ = face_incidence(distinct)
    oriented = []
    for face in exterior:
        parent = next(cell for cell in distinct if np.isin(cell, face).sum() == 3)
        p = points[face]
        if (
            np.dot(np.cross(p[1] - p[0], p[2] - p[0]), p.mean(axis=0) - points[parent].mean(axis=0))
            < 0
        ):
            face = face[[0, 2, 1]]
        oriented.append(face)
    boundary_triangles = np.array(oriented)
    area = (
        np.linalg.norm(
            np.cross(
                points[boundary_triangles[:, 1]] - points[boundary_triangles[:, 0]],
                points[boundary_triangles[:, 2]] - points[boundary_triangles[:, 0]],
            ),
            axis=1,
        )
        / 2
    )
    source = {
        "boundary": {
            "vertices_mm": points,
            "triangles": boundary_triangles,
            "triangle_face_index": np.arange(len(exterior)),
        },
        "faces": [{"cad_area_mm2": x} for x in area],
        "groups": [{"group_id": 0}],
        "face_to_group": np.zeros(len(exterior), dtype=np.int32),
    }
    mesh = {
        "points_m": points * 0.001,
        "tetrahedra": raw,
        "gmsh_boundary_triangles": boundary_triangles,
        "gmsh_boundary_face_ids": np.arange(1, len(exterior) + 1),
        "gmsh_boundary_entity_tags": np.arange(1, len(exterior) + 1),
        "fixed_boundary_triangles": boundary_triangles,
    }
    keep, classes = exact_quotient(raw, tags)
    assert keep.tolist() == [1, 2] and np.array_equal(raw[keep][0], raw[1])
    before = old_validation(mesh, source, caps)
    after = old_validation({**mesh, "tetrahedra": raw[keep]}, source, caps)
    no_change, no_classes = exact_quotient(distinct, np.array([5, 3]))
    assert np.array_equal(no_change, [0, 1]) and not no_classes
    if before["passed"] or not after["passed"]:
        raise ValueError("Exact duplicate/simple-tet fixture did not meet independent expectation")
    return {
        "passed": True,
        "duplicate_fixture_before": before,
        "duplicate_fixture_after": after,
        "lowest_tag_oriented_representative_preserved": True,
        "distinct_simple_tets_unchanged": True,
        "classes": classes,
    }


def run(args: Any) -> dict[str, Any]:
    started = time.monotonic()
    cfg = yaml.safe_load(args.frozen_config.read_text())
    caps = cfg["caps"]
    report: dict[str, Any] = {
        "fixture": fixture(caps),
        "accepted_mesh": False,
        "official_cleanup": False,
        "adoption": False,
        "Gmsh_invoked": False,
        "PDE_or_factorization_invoked": False,
    }
    if sha(args.postraw) != args.postraw_sha256 or sha(args.returned) != args.returned_sha256:
        raise ValueError("Immutable postraw source hash mismatch")
    paths = [
        args.postraw,
        args.returned,
        args.frozen_config,
        Path(__file__),
        Path("src/analysis/cad_gas_mesh.py"),
    ]
    before_hashes = {str(path): sha(path) for path in paths}
    with np.load(args.postraw, allow_pickle=False) as archive:
        raw = {name: archive[name] for name in archive.files}
    with np.load(args.returned, allow_pickle=False) as archive:
        original = {name: archive[name] for name in archive.files}
    if (
        len(original["points_m"]) > caps["max_nodes"]
        or len(original["tetrahedra"]) > caps["max_tetrahedra"]
    ):
        raise RuntimeError("Read-only diagnostic input exceeds existing node/tet memory cap")
    order = np.argsort(raw["node_tags"])
    node_tags = raw["node_tags"][order]
    assert np.array_equal(raw["points_mm"][order] * 0.001, original["points_m"])
    assert np.array_equal(np.searchsorted(node_tags, raw["tet_node_tags"]), original["tetrahedra"])
    keep, classes = exact_quotient(raw["tet_node_tags"], raw["tet_element_tags"])
    proposal = {**original, "tetrahedra": original["tetrahedra"][keep].copy()}
    proposal["retained_original_tet_rows"] = keep
    proposal["retained_original_element_tags"] = raw["tet_element_tags"][keep]
    # These assertions forbid perturbation, boundary edits or orientation canonicalization.
    unchanged = {
        key: np.array_equal(value, proposal[key])
        for key, value in original.items()
        if key != "tetrahedra"
    }
    assert all(unchanged.values())
    assert np.array_equal(proposal["tetrahedra"], original["tetrahedra"][keep])
    assert np.array_equal(
        np.unique(np.sort(raw["tet_node_tags"], axis=1), axis=0),
        np.unique(np.sort(raw["tet_node_tags"][keep], axis=1), axis=0),
    )
    source = load_source(cfg["source"])
    exterior, incidence = face_incidence(proposal["tetrahedra"])
    fixed = sorted_triangles(proposal["fixed_boundary_triangles"])
    gmsh_boundary = sorted_triangles(proposal["gmsh_boundary_triangles"])
    p = proposal["points_m"][proposal["tetrahedra"]]
    determinant = np.einsum(
        "ij,ij->i", p[:, 1] - p[:, 0], np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0])
    )
    edge = np.zeros(len(p))
    for a, b in [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]:
        edge = np.maximum(edge, np.linalg.norm(p[:, a] - p[:, b], axis=1))
    scaled = abs(determinant) / edge**3
    residual_cells = []
    for face in incidence["first_nonmanifold_faces"]:
        ids = np.flatnonzero(np.isin(proposal["tetrahedra"], face).sum(axis=1) == 3)
        original_ids = keep[ids]
        residual_cells.append(
            {
                "face_node_indices_zero_based": face,
                "face_original_node_tags": node_tags[face].tolist(),
                "incident_proposal_rows": ids.tolist(),
                "incident_original_rows": original_ids.tolist(),
                "incident_element_tags": raw["tet_element_tags"][original_ids].tolist(),
                "incident_oriented_original_node_tags": raw["tet_node_tags"][original_ids].tolist(),
                "distinct_four_node_classes": len(
                    np.unique(np.sort(raw["tet_node_tags"][original_ids], axis=1), axis=0)
                ),
            }
        )
    plc_points = source["boundary"]["vertices_mm"][source["boundary"]["triangles"]]
    plc_volume = float(
        np.einsum("ij,ij->i", plc_points[:, 0], np.cross(plc_points[:, 1], plc_points[:, 2])).sum()
        / 6
    )
    signed_volume = float(determinant.sum() / 6 * 1e9)
    original_boundary_bits = np.array_equal(
        proposal["points_m"][proposal["fixed_boundary_triangles"]],
        source["boundary"]["vertices_mm"][source["boundary"]["triangles"]] * 0.001,
    )
    validation = old_validation(proposal, source, caps)
    output = args.output / "DIAGNOSTIC-PROPOSAL-exact-connectivity-quotient.npz"
    np.savez_compressed(output, **proposal)
    report.update(
        source_sha256=before_hashes,
        source_geometry_sha256=source["source_sha256"],
        exact_duplicate_classes=classes,
        original_tets=len(original["tetrahedra"]),
        retained_tets=len(keep),
        removed_duplicate_occurrences=len(original["tetrahedra"]) - len(keep),
        remaining_exact_duplicate_occurrences=len(keep)
        - len(np.unique(np.sort(proposal["tetrahedra"], axis=1), axis=0)),
        geometric_cell_union_preserved_by_exact_ID_equivalence=True,
        oriented_representatives_preserved=True,
        coordinates_and_all_boundary_arrays_bitwise_unchanged=unchanged,
        original_optical_boundary_coordinates_bitwise_exact=original_boundary_bits,
        post_quotient_face_incidence=incidence,
        post_quotient_exterior_triangles=len(exterior),
        source_fixed_triangles=len(fixed),
        unchanged_Gmsh_boundary_elements=len(gmsh_boundary),
        exterior_matches_fixed_source_exact_multiset=np.array_equal(exterior, fixed),
        unchanged_Gmsh_boundary_matches_fixed_multiset=np.array_equal(gmsh_boundary, fixed),
        zero_tets_not_dropped=int((determinant == 0).sum()),
        negative_oriented_tets_preserved=int((determinant < 0).sum()),
        minimum_scaled_determinant=float(scaled.min()),
        scaled_determinant_guard_violations=int(
            (scaled <= caps["minimum_scaled_determinant"]).sum()
        ),
        raw_signed_tet_volume_mm3=float(determinant.sum() / 6 * 1e9),
        old_whole_validator=validation,
        diagnostic_proposal_path=str(output),
        diagnostic_proposal_sha256=sha(output),
        guards=caps,
        scope="Exact node-ID cell equivalence only; no boundary quotient, distinct-cell removal, coordinate perturbation, zero-cell removal or clipping.",
    )
    report["inputs_unchanged"] = before_hashes == {str(path): sha(path) for path in paths}
    report["independent_boundary_area_label_checks"] = boundary_checks(
        proposal, source, exterior, caps
    )
    report["remaining_nonmanifold_incident_distinct_cells"] = residual_cells
    report["source_PLC_volume_mm3"] = plc_volume
    report["relative_signed_tet_volume_error_vs_PLC"] = signed_volume / plc_volume - 1
    report["PLC_volume_guard_passed"] = (
        abs(signed_volume / plc_volume - 1) <= caps["relative_PLC_volume_tolerance"]
    )
    report["positive_and_scaled_det_guards_passed"] = bool(
        (determinant > 0).all() and (scaled > caps["minimum_scaled_determinant"]).all()
    )
    report["elapsed_s"] = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_RSS_bytes"] = int(rss if sys.platform == "darwin" else rss * 1024)
    return report


def main() -> None:
    root = Path("runs/wo03-optimized-plc-mesh-20261031T055336322017Z/actual/actual_medium")
    parser = argparse.ArgumentParser()
    parser.add_argument("--postraw", type=Path, default=root / "post-optimization-raw.npz")
    parser.add_argument(
        "--postraw-sha256",
        default="7d3fb6b74982e295b209d753dfe9138e78aa3b9c8ff7db69affab30a423f688d",
    )
    parser.add_argument(
        "--returned", type=Path, default=root / "returned-post-mesh-BEFORE-validation.npz"
    )
    parser.add_argument(
        "--returned-sha256",
        default="d106f16a8e178296b0a9811c250e5ff391a5418013912dceb7852a0a103351db",
    )
    parser.add_argument(
        "--frozen-config",
        "--config",
        dest="frozen_config",
        type=Path,
        default=Path("configs/studies/wo03-cad-gas-mesh.yaml"),
    )
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        result = run(args)
        (args.output / "diagnostic.json").write_text(json.dumps(result, indent=2) + "\n")
        return
    args.output.mkdir(parents=True, exist_ok=False)
    with (args.output / "worker.log").open("w") as log:
        try:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__)), *sys.argv[1:], "--worker"],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=120,
                check=False,
            )
            if completed.returncode:
                raise RuntimeError(
                    f"Read-only diagnostic exited{completed.returncode}; inspect worker.log"
                )
        except subprocess.TimeoutExpired:
            (args.output / "incomplete.json").write_text(
                json.dumps({"status": "incomplete120s_cap", "no_Gmsh_or_PDE": True}) + "\n"
            )
            raise SystemExit(1) from None
    result = json.loads((args.output / "diagnostic.json").read_text())
    print(
        json.dumps(
            {
                "output": str(args.output),
                "removed_exact_duplicate_occurrences": result["removed_duplicate_occurrences"],
                "old_validator": result["old_whole_validator"],
                "remaining_nonmanifold_faces": result["post_quotient_face_incidence"][
                    "nonmanifold_faces"
                ],
                "inputs_unchanged": result["inputs_unchanged"],
                "elapsed_s": result["elapsed_s"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
