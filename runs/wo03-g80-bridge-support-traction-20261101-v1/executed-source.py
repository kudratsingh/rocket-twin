"""Read saved bridge nodal reactions and compute face-resultant lower bounds."""

from __future__ import annotations

import hashlib
import json
import math
import resource
import signal
import time
from pathlib import Path

resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
signal.alarm(30)
START = time.monotonic()

import numpy as np
import vtk
import yaml
from vtk.util.numpy_support import vtk_to_numpy

from scripts.wo03_elmer_bridge_diagnostic import CONFIG, ROOT, inputs, read_vtu

OUT = ROOT / "build/wo03-g80-bridge-support-traction-v1"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def arrays(path, nodes):
    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    pts = vtk_to_numpy(grid.GetPoints().GetData())
    pd = grid.GetPointData()
    names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]
    matches = [x for x in names if x and x.lower() == "displacement loads"]
    if len(matches) != 1:
        raise ValueError("Missing or ambiguous load field")
    r = vtk_to_numpy(pd.GetArray(matches[0]))
    if (
        pts.dtype != np.float64
        or r.dtype != np.float64
        or pts.shape != (len(nodes), 3)
        or r.shape != pts.shape
        or not np.isfinite(pts).all()
        or not np.isfinite(r).all()
    ):
        raise ValueError("Invalid coordinate or load vectors")
    lookup = {tuple(np.round(p, 12)): i for i, p in enumerate(pts)}
    if len(lookup) != len(nodes):
        raise ValueError("Duplicate coordinates")
    ids = sorted(nodes)
    order = [lookup[tuple(np.round(nodes[n], 12))] for n in ids]
    if np.max(np.abs(pts[order] - np.array([nodes[n] for n in ids]))) > 1e-12:
        raise ValueError("Node coordinate mismatch")
    return {n: r[order[i]] for i, n in enumerate(ids)}


def main():
    OUT.mkdir(exist_ok=False)
    cfg = yaml.safe_load(CONFIG.read_text())
    assert not cfg["native_execution_authorized"] and not cfg["required_ci_confirmed"]
    meta = ROOT / cfg["source_metadata"]
    deck = ROOT / cfg["source_deck"]
    mapping = ROOT / cfg["input_root"] / "node-map.json"
    equal = ROOT / "build/wo03-elmer-bridge-diagnostic-v1/native/equal/field_t0001.vtu"
    single = ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single/field_t0001.vtu"
    paths = [
        Path(__file__).resolve(),
        CONFIG,
        meta,
        deck,
        mapping,
        equal,
        single,
        ROOT / "scripts/wo03_elmer_bridge_diagnostic.py",
        ROOT / cfg["input_review"],
        ROOT / "build/wo03-elmer-bridge-diagnostic-v1/equal-readonly-recovery.json",
        ROOT / "build/wo03-elmer-bridge-single-continuation-v1/single-readonly-recovery.json",
    ]
    before = {str(p): sha(p) for p in paths}
    record = {
        "status": "started",
        "solver_invoked": False,
        "before": before,
        "qualification": False,
        "service_force_N": 150,
        "design_factor": 3,
        "screen_MPa_estimated": 1.0,
    }
    try:
        d = inputs(cfg)
        metadata = json.loads(meta.read_text())
        mp = {int(k): int(v) for k, v in json.loads(mapping.read_text()).items()}
        faces = metadata["film_surface_ownership"]
        face_sets = [set(map(int, f["rail_back"]["node_ids"])) for f in faces]
        support = set(map(int, metadata["support_node_ids"]))
        if (
            len(faces) != 6
            or sum(map(len, face_sets)) != len(set.union(*face_sets))
            or set.union(*face_sets) != support
            or len(support) != 1574
        ):
            raise ValueError("Face support partition not disjoint and complete")
        geoms = []
        for f, ids in zip(faces, face_sets, strict=True):
            pts = np.asarray([d["nodes"][mp[n]] * 1000 for n in sorted(ids)])
            ctr = pts.mean(axis=0)
            _, _, v = np.linalg.svd(pts - ctr, full_matrices=False)
            normal = v[-1]
            normal *= 1 if normal[np.argmax(np.abs(normal))] >= 0 else -1
            deviation = float(np.max(np.abs((pts - ctr) @ normal)))
            area = float(f["rail_back"]["area_mm2"])
            if area <= 0 or deviation > 2e-6:
                raise ValueError("Face not planar or invalid source area")
            geoms.append(
                {
                    "material": f["epoxy_material"],
                    "film_angle_deg": f["film_angle_deg"],
                    "side": f["side"],
                    "node_count": len(ids),
                    "source_cad_area_mm2": area,
                    "plane_normal_sign_convention": "largest absolute component positive, not an outward-orientation claim",
                    "plane_normal": normal.tolist(),
                    "planarity_residual_mm": deviation,
                }
            )
        record["partition"] = {
            "face_count": 6,
            "support_count": len(support),
            "disjoint_complete": True,
        }
        record["cases"] = {}
        for i, (name, path) in enumerate((("equal", equal), ("single", single))):
            prior = json.loads((paths[-2] if i == 0 else paths[-1]).read_text())
            assert (
                prior["status"] == "read_only_evaluation_complete"
                if i == 0
                else prior["status"] == "read_only_numerical_evidence_recovered"
            )
            baseline, _ = read_vtu(path, d["nodes"], d["support"], d["loads"][i])
            r = arrays(path, d["nodes"])
            face_results = []
            total = np.zeros(3)
            moment = np.zeros(3)
            for g, source_ids in zip(geoms, face_sets, strict=True):
                ids = [mp[n] for n in sorted(source_ids)]
                F = np.array([math.fsum(float(r[n][j]) for n in ids) for j in range(3)])
                M = np.array(
                    [
                        math.fsum(float(np.cross(d["nodes"][n], r[n])[j]) for n in ids)
                        for j in range(3)
                    ]
                )
                total += F
                moment += M
                normal = np.array(g["plane_normal"])
                fn = float(F @ normal)
                tangent = F - fn * normal
                A = g["source_cad_area_mm2"]
                row = {
                    **g,
                    "reaction_N": F.tolist(),
                    "reaction_moment_Nm": M.tolist(),
                    "mean_traction_norm_lower_bound_MPa": float(np.linalg.norm(F) / A),
                    "mean_normal_traction_signed_MPa": fn / A,
                    "mean_tangential_traction_norm_MPa": float(np.linalg.norm(tangent) / A),
                    "mean_axial_shear_signed_MPa": float(F[2] / A),
                    "df3_traction_norm_lower_bound_MPa": float(3 * np.linalg.norm(F) / A),
                    "df3_tangential_lower_bound_MPa": float(3 * np.linalg.norm(tangent) / A),
                    "df3_axial_shear_MPa": float(3 * F[2] / A),
                }
                face_results.append(row)
            ref = np.asarray(baseline["support_reaction_N"])
            diff = total - ref
            if np.linalg.norm(diff) > 1e-9:
                raise ValueError("Partition sum mismatch")
            record["cases"][name] = {
                "faces": face_results,
                "summed_reaction_N": total.tolist(),
                "global_reaction_crosscheck_difference_N": diff.tolist(),
                "summed_support_moment_Nm": moment.tolist(),
                "original_reader_force_residual_N": baseline["force_residual_N"],
                "original_reader_moment_residual_Nm": baseline["moment_residual_Nm"],
                "strict_force_status": baseline["strict_force_status"],
            }
        record["status"] = "read_only_support_traction_bounds_complete"
    except Exception as exc:  # noqa: BLE001
        record.update(status="stopped", error=repr(exc))
    finally:
        record["after"] = {str(p): sha(p) for p in paths}
        record["sources_unchanged"] = before == record["after"]
        try:
            post = inputs(cfg)
            record["prefix_unchanged"] = post["prefix_hash"] == d["prefix_hash"]
            record["runtime_unchanged"] = post["runtime_hash"] == d["runtime_hash"]
        except Exception as exc:  # noqa: BLE001
            record.update(status="stopped", postcheck_error=repr(exc))
        u = resource.getrusage(resource.RUSAGE_SELF)
        record.update(
            cpu_s=u.ru_utime + u.ru_stime,
            wall_s=time.monotonic() - START,
            peak_rss_bytes=u.ru_maxrss,
        )
        (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
        print(
            json.dumps(
                {
                    k: record.get(k)
                    for k in (
                        "status",
                        "error",
                        "sources_unchanged",
                        "prefix_unchanged",
                        "runtime_unchanged",
                        "cpu_s",
                        "wall_s",
                    )
                },
                indent=2,
            )
        )
        signal.alarm(0)


if __name__ == "__main__":
    main()
