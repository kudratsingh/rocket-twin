"""Study two declared cord envelopes against pinned saved individual STEP solids."""

import hashlib
import json
import math
import os
import resource
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/wo03-g80-backbone-route-v1"
CONFIG = ROOT / "configs/studies/wo03-g80-backbone-route.yaml"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def worker():
    import cadquery as cq
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    OSD_Parallel.SetUseOcctThreads_s(True)
    OSD_ThreadPool.DefaultPool_s().Init(1)
    cfg = yaml.safe_load(CONFIG.read_text())
    before = {p: sha(ROOT / p) for p in cfg["source_hashes"]}
    assert before == cfg["source_hashes"]
    sourcehash = sha(__file__)
    confighash = sha(CONFIG)
    spec = yaml.safe_load(
        (
            ROOT
            / "build/wo03-g80-integration-staging/stage1-result-metadata-final-v2/resolved-candidate.yaml"
        ).read_text()
    )
    parts = spec["parts"]
    assert len(parts) == 72
    routes = []
    for a in cfg["azimuth_deg"]:
        rad = math.radians(a)
        x = cfg["radius_mm"] * math.cos(rad)
        y = cfg["radius_mm"] * math.sin(rad)
        z = cfg["station_start_mm"]
        h = cfg["station_end_mm"] - z
        routes.append(
            {
                "angle_deg": a,
                "x_mm": x,
                "y_mm": y,
                "nominal": cq.Solid.makeCylinder(
                    cfg["nominal_diameter_mm"] / 2, h, cq.Vector(x, y, z)
                ),
                "inflated": cq.Solid.makeCylinder(
                    cfg["nominal_diameter_mm"] / 2 + cfg["allowance_per_side_mm"],
                    h,
                    cq.Vector(x, y, z),
                ),
                "checks": [],
            }
        )
    result = {
        "status": "started",
        "source_identity": cfg["source_identity"],
        "source_hashes_before": before,
        "source_script_sha256": sourcehash,
        "config_sha256": confighash,
        "routes": [],
    }
    start = time.monotonic()

    def save():
        result["routes"] = [
            {k: v for k, v in r.items() if k not in ("nominal", "inflated")} for r in routes
        ]
        (OUT / "record.json").write_text(json.dumps(result, indent=2) + "\n")

    save()
    for part in parts:
        p = (
            ROOT
            / "build/wo03-g80-integration-staging/stage1-result-metadata-final-v2/parts"
            / f"{part['id']}.step"
        )
        s = cq.importers.importStep(str(p)).val()
        assert s.isValid() and s.Volume() > 0, part["id"]
        s = s.translate(
            (
                1000 * part["lateral_offset_m"][0],
                -1000 * part["lateral_offset_m"][1],
                1000 * part["position_m"],
            )
        )
        b = s.BoundingBox()
        for r in routes:
            rb = r["inflated"].BoundingBox()
            gap = math.sqrt(
                sum(
                    max(a0 - b1, b0 - a1, 0.0) ** 2
                    for a0, a1, b0, b1 in [
                        (rb.xmin, rb.xmax, b.xmin, b.xmax),
                        (rb.ymin, rb.ymax, b.ymin, b.ymax),
                        (rb.zmin, rb.zmax, b.zmin, b.zmax),
                    ]
                )
            )
            row = {
                "part": part["id"],
                "role": part["cad"]["role"],
                "source_sha256": before[str(p.relative_to(ROOT))],
                "bbox_gap_lower_bound_mm": gap,
                "exact_computed": gap <= cfg["broadphase_clearance_mm"],
            }
            if row["exact_computed"]:
                row["nominal_intersection_mm3"] = r["nominal"].intersect(s).Volume()
                row["inflated_intersection_mm3"] = r["inflated"].intersect(s).Volume()
                row["nominal_distance_mm"] = r["nominal"].distance(s)
                row["inflated_distance_mm"] = r["inflated"].distance(s)
            r["checks"].append(row)
        save()
    result["status"] = "completed_geometry_only"
    result["source_hashes_after"] = {p: sha(ROOT / p) for p in cfg["source_hashes"]}
    assert (
        result["source_hashes_after"] == before
        and sha(__file__) == sourcehash
        and sha(CONFIG) == confighash
    )
    usage = resource.getrusage(resource.RUSAGE_SELF)
    result["resources"] = {
        "cpu_s": usage.ru_utime + usage.ru_stime,
        "wall_s": time.monotonic() - start,
        "peak_rss_bytes": usage.ru_maxrss,
        "threading": "one worker requested; OCCT pool set to 1; OS affinity not established",
    }
    save()


def main():
    if "--worker" in sys.argv:
        worker()
        return
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    cfg = yaml.safe_load(CONFIG.read_text())
    out = OUT
    assert not (out / "status.json").exists()
    out.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    for x in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[x] = "1"
    launch = f'import os,resource,sys;resource.setrlimit(resource.RLIMIT_CPU,({cfg["cpu_s"]},{cfg["cpu_s"]}));os.execv(sys.executable,[sys.executable,{str(Path(__file__).resolve())!r},"--worker"])'
    rss, desc = darwin_process_callbacks()
    run_owned(
        [sys.executable, "-c", launch],
        log_path=out / "worker.log",
        status_path=out / "status.json",
        wall_limit_s=cfg["wall_s"],
        rss_callback=rss,
        descendants_callback=desc,
        rss_limit_bytes=cfg["rss_bytes"],
        cwd=ROOT,
        env=env,
    )


if __name__ == "__main__":
    main()
