"""Read-only local geometric embedding audit of the immutable coarse tet mesh.

For each shared canonical facet abc, compare orient3d(a,b,c,d0) and
orient3d(a,b,c,d1). Both must be nonzero and have opposite signs. Incidence2
alone is insufficient. A conservative floating orient3d filter is followed by
exact binary-rational arithmetic ONLY when near zero; no tolerance changes a
physical sign. Reference: Shewchuk, Adaptive Precision Floating-Point Arithmetic
and Fast Robust Geometric Predicates, Discrete & Computational Geometry,1997.
No Gmsh, mesh repair, PDE, factorization or temperature calculation is invoked.
"""

from __future__ import annotations

import os

for key in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "VECLIB_MAXIMUM_THREADS", "MKL_NUM_THREADS"]:
    os.environ[key] = "1"

import argparse
import hashlib
import json
import resource
import subprocess
import sys
import time
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_orientation(a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray) -> Fraction:
    xyz = [[Fraction.from_float(float(x)) for x in point] for point in [a, b, c, d]]
    u, v, w = [[xyz[row][i] - xyz[0][i] for i in range(3)] for row in [1, 2, 3]]
    return (
        u[0] * (v[1] * w[2] - v[2] * w[1])
        + u[1] * (v[2] * w[0] - v[0] * w[2])
        + u[2] * (v[0] * w[1] - v[1] * w[0])
    )


def signs(
    points: np.ndarray, vertices: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict[str, Any]]]:
    result = np.empty(len(vertices), dtype=np.int8)
    values = np.empty(len(vertices))
    scales = np.empty(len(vertices))
    exact_rows = []
    for begin in range(0, len(vertices), 100000):
        end = min(begin + 100000, len(vertices))
        p = points[vertices[begin:end]]
        u, v, w = p[:, 1] - p[:, 0], p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]
        v0w1, w0v1 = v[:, 0] * w[:, 1], w[:, 0] * v[:, 1]
        w0u1, u0w1 = w[:, 0] * u[:, 1], u[:, 0] * w[:, 1]
        u0v1, v0u1 = u[:, 0] * v[:, 1], v[:, 0] * u[:, 1]
        determinant = u[:, 2] * (v0w1 - w0v1) + v[:, 2] * (w0u1 - u0w1) + w[:, 2] * (u0v1 - v0u1)
        permanent = (
            abs(u[:, 2]) * (abs(v0w1) + abs(w0v1))
            + abs(v[:, 2]) * (abs(w0u1) + abs(u0w1))
            + abs(w[:, 2]) * (abs(u0v1) + abs(v0u1))
        )
        # 64*machine-epsilon is more conservative than the standard orient3d A filter.
        bound = 64 * np.finfo(float).eps * permanent
        uncertain = abs(determinant) <= bound
        filtered = np.sign(determinant).astype(np.int8)
        for local in np.flatnonzero(uncertain):
            exact = exact_orientation(*p[local])
            filtered[local] = (exact > 0) - (exact < 0)
            exact_rows.append(
                {
                    "row": begin + int(local),
                    "float_signed_sixvolume_m3": float(determinant[local]),
                    "roundoff_filter_bound_m3": float(bound[local]),
                    "exact_sign": int(filtered[local]),
                    "exact_numerator": str(exact.numerator),
                    "exact_denominator": str(exact.denominator),
                }
            )
        length = np.zeros(end - begin)
        for a, b in [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3], [2, 3]]:
            length = np.maximum(length, np.linalg.norm(p[:, a] - p[:, b], axis=1))
        result[begin:end], values[begin:end], scales[begin:end] = filtered, determinant, length**3
    return result, values, scales, exact_rows


def adjacency(points: np.ndarray, tet: np.ndarray) -> tuple[dict[str, Any], dict[str, Any]]:
    element_sign, element_value, element_scale, element_exact = signs(points, tet)
    faces = np.concatenate([tet[:, c] for c in [[1, 2, 3], [0, 2, 3], [0, 1, 3], [0, 1, 2]]])
    opposite = np.concatenate([tet[:, i] for i in range(4)])
    owner = np.tile(np.arange(len(tet)), 4)
    canonical = np.sort(faces, axis=1)
    order = np.lexsort(canonical.T[::-1])
    sorted_keys = canonical[order]
    start = np.r_[0, np.flatnonzero((sorted_keys[1:] != sorted_keys[:-1]).any(axis=1)) + 1]
    count = np.diff(np.r_[start, len(order)])
    paired_start = start[count == 2]
    first, second = order[paired_start], order[paired_start + 1]
    common = canonical[first]
    opp = np.stack([opposite[first], opposite[second]], axis=1)
    owners = np.stack([owner[first], owner[second]], axis=1)
    left, left_value, left_scale, left_exact = signs(points, np.column_stack([common, opp[:, 0]]))
    right, right_value, right_scale, right_exact = signs(
        points, np.column_stack([common, opp[:, 1]])
    )
    zero = (left == 0) | (right == 0)
    same = (left == right) & ~zero
    bad = zero | same
    signed = np.stack([left_value, right_value], axis=1)
    scale = np.stack([left_scale, right_scale], axis=1)
    arrays = {
        "face_node_ids": common[bad],
        "opposite_node_ids": opp[bad],
        "incident_tet_rows": owners[bad],
        "face_points_m": points[common[bad]],
        "opposite_points_m": points[opp[bad]],
        "filtered_or_exact_signs": np.stack([left, right], axis=1)[bad],
        "floating_signed_sixvolumes_m3": signed[bad],
        "tet_length_cubed_scale_m3": scale[bad],
        "zero_face": zero[bad],
        "same_side_face": same[bad],
    }
    examples = []
    for row in np.flatnonzero(bad)[:32]:
        examples.append(
            {
                "internal_face_row": int(row),
                "kind": "zero" if zero[row] else "same_side",
                "face_node_ids": common[row].tolist(),
                "opposite_node_ids": opp[row].tolist(),
                "incident_tet_rows": owners[row].tolist(),
                "face_points_m": points[common[row]].tolist(),
                "opposite_points_m": points[opp[row]].tolist(),
                "signed_sixvolumes_m3": signed[row].tolist(),
                "length_cubed_scale_m3": scale[row].tolist(),
            }
        )
    histogram_values, histogram_counts = np.unique(count, return_counts=True)
    report = {
        "node_count": len(points),
        "tetrahedra": len(tet),
        "all_elements_strict_positive_exact_or_filtered": bool((element_sign > 0).all()),
        "negative_elements": int((element_sign < 0).sum()),
        "zero_elements": int((element_sign == 0).sum()),
        "minimum_positive_floating_sixvolume_m3": (
            float(element_value[element_sign > 0].min()) if (element_sign > 0).any() else None
        ),
        "minimum_abs_scaled_element_sixvolume": float((abs(element_value) / element_scale).min()),
        "face_incidence_histogram": {
            str(int(a)): int(b) for a, b in zip(histogram_values, histogram_counts, strict=True)
        },
        "nonmanifold_incidence_faces": int((count > 2).sum()),
        "all_incidence2_faces_tested": len(common),
        "opposite_side_faces": int((~bad).sum()),
        "same_side_faces": int(same.sum()),
        "zero_side_faces": int(zero.sum()),
        "all_incidence2_faces_geometrically_opposite": bool(not bad.any()),
        "bad_face_examples": examples,
        "nearzero_exact_binary_checks": {
            "elements": element_exact,
            "first_opposite": left_exact,
            "second_opposite": right_exact,
        },
        "predicate": "strict sign; conservative64epsilon orient3d filter, exact binary Fraction only for uncertain signs",
        "global_embedding_or_nonintersection_proven": False,
        "limits": "Checks all shared incidence2 facets and every element orientation. Does not test distant/nonadjacent cell intersections, CAD approximation, PDE consistency, conditioning, discrete maximum principle or thermal accuracy.",
        "PDE_or_factorization_invoked": False,
        "mesh_modified": False,
    }
    return report, arrays


def fixtures() -> dict[str, Any]:
    points = np.array(
        [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, -1.0]]
    )
    valid, _ = adjacency(points, np.array([[0, 1, 2, 3], [0, 2, 1, 4]]))
    folded_points = points.copy()
    folded_points[4] = [0.2, 0.2, 0.6]
    folded, _ = adjacency(folded_points, np.array([[0, 1, 2, 3], [0, 1, 2, 4]]))
    zero_points = points.copy()
    zero_points[4] = [0.2, 0.2, 0]
    zero, _ = adjacency(zero_points, np.array([[0, 1, 2, 3], [0, 1, 2, 4]]))
    assert (
        valid["all_incidence2_faces_geometrically_opposite"]
        and valid["all_elements_strict_positive_exact_or_filtered"]
    )
    assert (
        folded["same_side_faces"] == 1 and folded["all_elements_strict_positive_exact_or_filtered"]
    )
    assert zero["zero_side_faces"] == 1 and zero["nearzero_exact_binary_checks"]["elements"]
    return {
        "passed": True,
        "valid_opposite_pair": valid,
        "deliberately_folded_pair": folded,
        "exact_zero_pair": zero,
    }


def worker(args: Any) -> None:
    start = time.monotonic()
    known = fixtures()
    before = sha(args.mesh)
    if before != args.expected_sha256:
        raise ValueError("Immutable coarse input hash mismatch")
    with np.load(args.mesh, allow_pickle=False) as archive:
        points, tet = archive["points_m"], archive["tetrahedra"]
    if len(points) > 150000 or len(tet) > 750000 or not np.isfinite(points).all():
        raise ValueError("Existing memory/count/finite-coordinate limits violated")
    report, bad = adjacency(points, tet)
    bad_path = args.output / "bad-internal-faces.npz"
    np.savez_compressed(bad_path, **bad)
    report.update(
        fixtures=known,
        source_mesh=str(args.mesh),
        source_sha256=before,
        source_unchanged=before == sha(args.mesh),
        diagnostic_complete=True,
        bad_faces_path=str(bad_path),
        bad_faces_sha256=sha(bad_path),
        elapsed_s=time.monotonic() - start,
    )
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_RSS_bytes"] = int(rss if sys.platform == "darwin" else rss * 1024)
    (args.output / "diagnostic.json").write_text(json.dumps(report, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mesh", type=Path, default=Path("build/wo03-cad-gas-actual-v1/coarse/mesh.npz")
    )
    parser.add_argument(
        "--expected-sha256",
        default="aefc71e318393ae781fefb5e5d2195eb6383dc32214f292eb4445f1de86b4351",
    )
    parser.add_argument("--config", type=Path)
    parser.add_argument("--preset", choices=["tiny", "sim", "rl", "real"], default="tiny")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    if args.worker:
        worker(args)
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
                    f"Read-only adjacency audit exited{completed.returncode}; inspect worker.log"
                )
        except subprocess.TimeoutExpired:
            (args.output / "incomplete.json").write_text(
                json.dumps({"status": "incomplete120s_cap", "source_untouched": True}) + "\n"
            )
            raise SystemExit(1) from None
    report = json.loads((args.output / "diagnostic.json").read_text())
    print(
        json.dumps(
            {
                key: report[key]
                for key in [
                    "all_elements_strict_positive_exact_or_filtered",
                    "all_incidence2_faces_tested",
                    "opposite_side_faces",
                    "same_side_faces",
                    "zero_side_faces",
                    "source_unchanged",
                    "elapsed_s",
                    "peak_RSS_bytes",
                ]
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
