"""Two serial, guarded mesh-only bridge pilots; never launches a solver."""

import argparse
import hashlib
import json
import os
import resource
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo03_g80_bridge_adapter import build_case, source_hashes
from scripts.wo03_g80_bridge_boundary_case import inspect_and_apply, validate_budget_spec
from scripts.wo03_g80_bridge_fea import validate_adapter_loads
from scripts.wo03_g80_washer_boundary import verify_source_hashes
from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

OUT = ROOT / "build/wo03-g80-bridge-mesh-pilots-v1"
CONFIG = ROOT / "configs/studies/wo03-g80-bridge-mesh-pilots.yaml"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def metrics(meta):
    import numpy as np

    coords = {int(k): np.asarray(v) for k, v in meta["coordinates_mm"].items()}
    centers = np.array([[12.75, 22.083647796503], [-25.5, 0], [12.75, -22.0836477965]])
    buckets = {"G11_all": [], "G11_washer_zone": [], **{f"EPOXY_{i}": [] for i in range(6)}}
    ownership = {x["epoxy_material"]: x for x in meta["film_surface_ownership"]}
    for key, con in meta["all_c3d10_connectivity"].items():
        pts = np.array([coords[int(n)] for n in con[:4]])
        edges = [np.linalg.norm(pts[i] - pts[j]) for i in range(4) for j in range(i)]
        owner = meta["tetrahedron_material"][key]
        c = np.asarray(meta["tetrahedron_centroids_mm"][key])
        row = [max(edges), min(edges), float(meta["tetrahedron_volumes_mm3"][key])]
        if owner == "G11":
            buckets["G11_all"].append(row)
            if c[2] >= 168.1 and min(np.linalg.norm(centers - c[:2], axis=1)) <= 6:
                buckets["G11_washer_zone"].append(row)
        else:
            film = ownership[owner]
            theta = np.deg2rad(film["film_angle_deg"])
            tangent = np.array([-np.sin(theta), np.cos(theta)])
            row.append(float(np.ptp(pts[:, :2] @ tangent)))
            buckets[owner].append(row)
    report = {}
    for name, rows in buckets.items():
        a = np.asarray(rows)
        if not len(a):
            raise ValueError("Empty physical region: " + name)
        report[name] = {
            "tetrahedra": len(a),
            "max_corner_edge_mm_p10_p50_p90": np.quantile(a[:, 0], [0.1, 0.5, 0.9]).tolist(),
            "min_corner_edge_mm_p10_p50_p90": np.quantile(a[:, 1], [0.1, 0.5, 0.9]).tolist(),
            "volume_mm3_p10_p50_p90": np.quantile(a[:, 2], [0.1, 0.5, 0.9]).tolist(),
        }
        if name.startswith("EPOXY"):
            report[name]["thickness_normal_span_mm_p10_p50_p90"] = np.quantile(
                a[:, 3], [0.1, 0.5, 0.9]
            ).tolist()
    return report


def worker(size):
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))

    spec = yaml.safe_load(
        (ROOT / "configs/studies/wo03-g80-washer-boundary-area-budget.yaml").read_text()
    )
    cfg = yaml.safe_load((ROOT / "configs/studies/wo03-g80-bridge-fea.yaml").read_text())
    out = OUT / ("mesh_" + str(size).replace(".", "p"))
    out.mkdir(exist_ok=False)
    try:
        meta = build_case(
            out / "mesh",
            size,
            50000,
            75000,
            boundary_callback=lambda g, p: inspect_and_apply(
                g, p, spec, out / "boundary-inventory.json"
            ),
        )
        # Persist raw metadata and patch diagnostics before strict independent checks.
        (out / "regional-metrics.json").write_text(json.dumps(metrics(meta), indent=2) + "\n")
        result = validate_adapter_loads(meta, cfg)
        deck = (out / "mesh/case.inp").read_text().upper()
        if deck.count("*STEP") != 2 or deck.count("*CLOAD,OP=NEW") != 2:
            raise ValueError("Two-step deck invalid")
        (out / "input-check.json").write_text(json.dumps(result, indent=2) + "\n")
    finally:
        u = resource.getrusage(resource.RUSAGE_SELF)
        (out / "worker-resource.json").write_text(
            json.dumps({"cpu_s": u.ru_utime + u.ru_stime, "peak_rss_bytes": u.ru_maxrss}, indent=2)
            + "\n"
        )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--worker", type=float)
    args = parser.parse_args()
    if args.worker is not None:
        if args.worker not in (3.0, 2.0):
            raise ValueError("Unadmitted mesh size")
        worker(args.worker)
        return
    cfg = yaml.safe_load(CONFIG.read_text())
    assert cfg["bulk_mm"] == [3.0, 2.0] and not cfg["native_solver_authorized"]
    spec = yaml.safe_load((ROOT / cfg["fixed_boundary_config"]).read_text())
    original = yaml.safe_load((ROOT / "configs/studies/wo03-g80-washer-boundary.yaml").read_text())
    known = json.loads((ROOT / "build/wo03-g80-washer-area-budget-v1/result.json").read_text())
    validate_budget_spec(spec, original, known)
    verify_source_hashes(ROOT, spec)
    old = json.loads((ROOT / "build/wo03-g80-bridge-area-budget-coarse-v1/record.json").read_text())
    assert source_hashes() == old["physical_source_sha256"]
    files = [
        Path(__file__).resolve(),
        CONFIG,
        ROOT / cfg["fixed_boundary_config"],
        ROOT / "configs/studies/wo03-g80-bridge-fea.yaml",
        ROOT / "scripts/wo03_g80_bridge_adapter.py",
        ROOT / "scripts/wo03_g80_bridge_boundary_case.py",
        ROOT / "scripts/wo03_g80_washer_boundary.py",
        ROOT / "scripts/wo03_g80_bridge_fea.py",
        ROOT / "scripts/wo03_owned_process.py",
        ROOT / "build/wo03-g80-washer-area-budget-v1/result.json",
    ]
    # Prior as-run source pins remain unchanged except the separately reviewed process helper.
    for p in files:
        if (
            str(p) in old["source_before"]
            and p.name != "wo03_owned_process.py"
            and sha(p) != old["source_before"][str(p)]
        ):
            raise ValueError("Changed source " + str(p))
    if (
        sha(ROOT / "scripts/wo03_owned_process.py")
        != "18cced6ac2d54bcb6aa4ca593ccb5a9ceb2c596aefd6a02c227f0f7983d1d9d0"
    ):
        raise ValueError("Supervisor pin differs")
    OUT.mkdir(exist_ok=False)
    before = {str(p): sha(p) for p in files}
    rec = {
        "status": "started",
        "admitted_sizes_mm": [3.0, 2.0],
        "solver_invoked": False,
        "sources_before": before,
        "physical_source_sha256": source_hashes(),
        "pilots": [],
        "cpu_reservation_s": 150,
    }

    def save():
        (OUT / "record.json").write_text(json.dumps(rec, indent=2) + "\n")

    save()
    rss, desc = darwin_process_callbacks()
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    try:
        for size in (3.0, 2.0):
            label = str(size).replace(".", "p")
            st = run_owned(
                [sys.executable, str(Path(__file__).resolve()), "--worker", str(size)],
                log_path=OUT / ("mesh_" + label + ".log"),
                status_path=OUT / ("mesh_" + label + "-status.json"),
                wall_limit_s=60,
                rss_callback=rss,
                descendants_callback=desc,
                rss_limit_bytes=2147483648,
                cwd=ROOT,
                env=env,
            )
            check = json.loads((OUT / ("mesh_" + label) / "input-check.json").read_text())
            rec["pilots"].append(
                {
                    "size_mm": size,
                    "input_check": check,
                    "child_status": {
                        k: v
                        for k, v in st.items()
                        if k
                        not in (
                            "cpu_samples",
                            "rss_samples_bytes",
                            "descendant_samples",
                            "sample_times_s",
                        )
                    },
                }
            )
            save()
            if (
                before != {str(p): sha(p) for p in files}
                or source_hashes() != rec["physical_source_sha256"]
            ):
                raise ValueError("Source changed")
        rec["status"] = "two_mesh_inputs_passed_no_solver"
    except Exception as exc:  # noqa: BLE001
        rec.update(status="stopped", error=repr(exc))
    finally:
        rec["sources_after"] = {str(p): sha(p) for p in files}
        rec["source_unchanged"] = before == rec["sources_after"]
        rec["physical_source_unchanged"] = source_hashes() == rec["physical_source_sha256"]
        save()
    print(
        json.dumps(
            {
                "status": rec["status"],
                "error": rec.get("error"),
                "sizes_passed": [p["size_mm"] for p in rec["pilots"]],
            }
        )
    )


if __name__ == "__main__":
    main()
