"""Export existing frozen RP1 inspection shapes to separately identified STEP files.

One worker, at most120 wall/60 CPU seconds, no dependency installation or retry.
This reconstructs existing nominal inspection shapes; it adds no hardware detail,
mass/inertia, physical-fit qualification or manufacturing release.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/rp1-inspection-step"
REPORT = ROOT / "docs/studies/frontend-desktop-detail-20261108/cad-export.json"
SCRIPT = "scripts/wo04_rp1_inspection_step.py"
CORE = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
CRITICAL = (
    "motor_tube",
    "forward_ring",
    "aft_ring",
    "fin_set",
    "fin_tabs",
    "root_gussets",
    "body",
    "motor",
    "motor_retainer",
)
WALL_SECONDS = 120
CPU_SECONDS = 60
COMPARISON_MM = 0.2
READBACK_MM = 1e-5


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_manifest(packet: dict[str, Any]) -> None:
    temporary = OUTPUT / "manifest.tmp"
    temporary.write_text(json.dumps(packet, indent=2) + "\n")
    temporary.replace(OUTPUT / "manifest.json")


def worker() -> int:
    import resource

    started_wall, started_cpu = time.monotonic(), time.process_time()
    resource.setrlimit(resource.RLIMIT_CPU, (CPU_SECONDS - 1, CPU_SECONDS))
    signal.signal(signal.SIGXCPU, lambda *_: sys.exit("CPU limit reached; no retry"))
    packet: dict[str, Any] = {
        "schema_version": 1,
        "id": "rp1-ad1-v2-inspection-step-20261108",
        "status": "started",
        "script": {"path": SCRIPT, "sha256": sha(ROOT / SCRIPT)},
        "budget": {"wall_seconds": WALL_SECONDS, "cpu_seconds": CPU_SECONDS},
        "cost_usd": 0,
        "units": {"step": "mm", "source": "m except named mm fields", "core_glb": "m"},
        "cad_frame": "X=body+y, Y=body-z, Z=station aft from nose tip; origin at nose",
        "viewer_mapping": "viewer[X,Y,Z]=[cadX/1000,length_m-cadZ/1000,cadY/1000]",
        "placements": "cad=[lateral_offset_m[0],-lateral_offset_m[1],position_m]*1000",
        "validation_limits": {
            "step_readback_bounds_absolute_mm": READBACK_MM,
            "core_glb_bounds_absolute_mm_strictly_less_than": COMPARISON_MM,
            "meaning": "Representation/readback comparison only; not an engineering fit tolerance",
        },
        "parts": [],
        "assemblies": [],
        "engineering_accepted": False,
        "manufacturing_clearance": False,
        "flight_ready": False,
        "mass_or_inertia_generated": False,
        "limitations": [
            "Inspection CAD reconstruction from fixed nominal definition, not manufacturing-ready geometry",
            "Source-dimensioned shapes retain estimates; simplified envelopes retain undefined supplier internals",
            "No new roundovers, threads, hardware, cord/knot topology, bonds or installed contact definition",
            "25 allowances and4 missing-geometry records remain meshless; no inferred placeholder solid",
            "No canonical CAD/inertia/physical vehicle adoption or installed joint pass",
            "Historical G80/G54/G12 CAD and unadopted FP1/FR1 remain separate",
        ],
    }
    write_manifest(packet)

    def guard() -> None:
        if time.process_time() - started_cpu > 50 or time.monotonic() - started_wall > 105:
            raise TimeoutError("Cooperative reserve reached; stop without another attempt")

    try:
        sys.path.insert(0, str(ROOT))
        import cadquery as cq
        import trimesh
        import yaml

        from src.api import rp1_geometry, rp1_inspection
        from src.inspection.rp1_geometry import _local, sources

        core = rp1_geometry.build(ROOT)
        if core["identity"]["inspection_geometry_sha256"] != CORE:
            raise ValueError("Frozen core inspection identity mismatch")
        source = rp1_inspection.build(ROOT)
        definition = yaml.safe_load((ROOT / rp1_inspection.DEFINITION).read_bytes())
        originals = {row["id"]: row["raw"] for row in source["parts"]}
        rows = {row["id"]: row for row in core["parts"]}
        frozen = sources(ROOT)
        packet.update(
            identity=core["identity"],
            source_hashes=frozen,
            core_manifest_sha256=sha(
                ROOT / "docs/studies/rp1-inspection-geometry-20261107/manifest.json"
            ),
            source_coverage=core["coverage"],
            tools={
                "python": sys.version.split()[0],
                "cadquery": cq.__version__,
                "trimesh": trimesh.__version__,
            },
            source_records=[
                {
                    "id": row["id"],
                    "maturity": row["maturity"],
                    "material": originals[row["id"]]["material"],
                    "source_dimensions": row["source_dimensions"],
                    "source": row["source"],
                    "inspection_shape_sha256": row["inspection_shape_sha256"],
                    "exportable": row["mesh"] is not None,
                    "description": row["description"],
                }
                for row in core["parts"]
            ],
        )
        if len(rows) != 55 or sum(row["mesh"] is not None for row in rows.values()) != 26:
            raise ValueError("Expected55 source records/26 existing mesh-bearing shapes")

        def bounds(shape: Any) -> list[list[float]]:
            box = shape.BoundingBox()
            result = [[box.xmin, box.ymin, box.zmin], [box.xmax, box.ymax, box.zmax]]
            if not all(math.isfinite(v) for corner in result for v in corner):
                raise ValueError("Nonfinite CAD bounds")
            return result

        def max_error(a: list[list[float]], b: list[list[float]]) -> float:
            return max(
                abs(v - w) for c, d in zip(a, b, strict=True) for v, w in zip(c, d, strict=True)
            )

        def check_readback(path: Path, original: Any) -> dict[str, Any]:
            guard()
            loaded = cq.Compound.makeCompound(cq.importers.importStep(str(path), unit="MM").vals())
            count = len(original.Solids())
            if not loaded.isValid() or len(loaded.Solids()) != count or count <= 0:
                raise ValueError(f"Invalid STEP readback/solid coverage: {path.name}")
            expected, actual = bounds(original), bounds(loaded)
            error = max_error(expected, actual)
            if error > READBACK_MM:
                raise ValueError(f"STEP readback bounds differ: {path.name}: {error}mm")
            return {
                "valid": True,
                "solids": count,
                "bounds_mm": actual,
                "max_bounds_error_mm": error,
            }

        shapes: dict[str, Any] = {}
        paths = OUTPUT / "parts"
        paths.mkdir()

        def save_assembly(ids: list[str], name: str) -> None:
            guard()
            assembly = cq.Assembly(name=name)
            for pid in ids:
                assembly.add(shapes[pid], name=pid, color=cq.Color(originals[pid]["cad"]["color"]))
            path = OUTPUT / f"{name}.step"
            assembly.save(str(path), exportType="STEP", mode="default")
            expected = cq.Compound.makeCompound([shapes[pid] for pid in ids])
            checked = check_readback(path, expected)
            packet["assemblies"].append(
                {
                    "id": name,
                    "part_ids": ids,
                    "path": str(path.relative_to(ROOT)),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                    "readback": checked,
                    "maturity": "mixed; see per-part records",
                }
            )
            write_manifest(packet)

        order = list(CRITICAL) + [
            pid for pid, row in rows.items() if row["mesh"] and pid not in CRITICAL
        ]
        for pid in order:
            guard()
            raw, row = originals[pid], rows[pid]
            shape = _local(raw, definition, originals).translate(
                (
                    raw["lateral_offset_m"][0] * 1000,
                    -raw["lateral_offset_m"][1] * 1000,
                    raw["position_m"] * 1000,
                )
            )
            if not shape.isValid() or not shape.Solids():
                raise ValueError(f"Invalid fixed-source shape: {pid}")
            cad_bounds = bounds(shape)
            display_bounds = [
                [
                    cad_bounds[0][0],
                    source["geometry"]["length_m"] * 1000 - cad_bounds[1][2],
                    cad_bounds[0][1],
                ],
                [
                    cad_bounds[1][0],
                    source["geometry"]["length_m"] * 1000 - cad_bounds[0][2],
                    cad_bounds[1][1],
                ],
            ]
            mesh_path = ROOT / row["mesh"]["path"]
            if sha(mesh_path) != row["mesh"]["sha256"]:
                raise ValueError("Core GLB changed before comparison")
            mesh = trimesh.load(mesh_path, force="scene").to_geometry()
            glb_bounds_mm = [[float(v) * 1000 for v in corner] for corner in mesh.bounds]
            representation_error = max_error(display_bounds, glb_bounds_mm)
            if representation_error >= COMPARISON_MM:
                raise ValueError(f"Core GLB/CAD bounds differ: {pid}: {representation_error}mm")
            path = paths / f"{pid}.step"
            assembly = cq.Assembly(name=f"{pid}_inspection")
            assembly.add(shape, name=pid, color=cq.Color(raw["cad"]["color"]))
            assembly.save(str(path), exportType="STEP", mode="default")
            readback = check_readback(path, shape)
            shapes[pid] = shape
            packet["parts"].append(
                {
                    "id": pid,
                    "maturity": row["maturity"],
                    "material": raw["material"],
                    "path": str(path.relative_to(ROOT)),
                    "sha256": sha(path),
                    "bytes": path.stat().st_size,
                    "source": row["source"],
                    "definition_source": row["definition_source"],
                    "inspection_shape_sha256": row["inspection_shape_sha256"],
                    "core_glb": row["mesh"],
                    "cad_bounds_mm": cad_bounds,
                    "dimensions_mm": [
                        hi - lo for lo, hi in zip(cad_bounds[0], cad_bounds[1], strict=True)
                    ],
                    "core_glb_bounds_mm": glb_bounds_mm,
                    "max_core_glb_bounds_error_mm": representation_error,
                    "readback": readback,
                    "physical_verification": "open",
                }
            )
            write_manifest(packet)
            if pid == CRITICAL[-1]:
                save_assembly(list(CRITICAL), "critical_motor_fin_ring_joint")
        save_assembly(order, "rp1_ad1_v2_inspection_26_records")
        if sources(ROOT) != frozen or sha(ROOT / SCRIPT) != packet["script"]["sha256"]:
            raise ValueError("Source/code changed during export")
        rp1_geometry.build(ROOT)
        packet["status"] = "complete_inspection_reconstruction"
        return_code = 0
    except (Exception, SystemExit) as error:  # noqa: BLE001 - Preserve the first stopped packet.
        packet["status"] = "stopped_no_retry"
        packet["error"] = {"type": type(error).__name__, "message": str(error)}
        return_code = 1
    packet["runtime"] = {
        "worker_wall_seconds": time.monotonic() - started_wall,
        "worker_cpu_seconds": time.process_time() - started_cpu,
    }
    packet["exported_part_records"] = len(packet["parts"])
    write_manifest(packet)
    return return_code


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute one bounded packet; existing output prevents a repeat",
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        return worker()
    if not args.execute:
        parser.error("Use --execute for the one bounded export")
    if OUTPUT.exists():
        raise SystemExit("Output already exists; no overwrite or automatic new attempt")
    OUTPUT.mkdir(parents=True)
    os.environ.setdefault("XDG_CACHE_HOME", str(ROOT / ".cache"))
    started = time.monotonic()
    timed_out = False
    with (OUTPUT / "execution.log").open("w") as log:
        try:
            result = subprocess.run(
                [sys.executable, str(ROOT / SCRIPT), "--worker"],
                cwd=ROOT,
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=WALL_SECONDS,
                check=False,
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            code, timed_out = 1, True
    manifest = OUTPUT / "manifest.json"
    packet = (
        json.loads(manifest.read_text())
        if manifest.exists()
        else {
            "status": "stopped_no_retry",
            "parts": [],
            "error": "Worker did not produce a manifest",
        }
    )
    if code != 0:
        packet["status"] = "stopped_no_retry"
        packet["worker_exit_code"] = code
        packet["wall_timeout"] = timed_out
    packet["parent_wall_seconds"] = time.monotonic() - started
    packet["output_manifest_path"] = str(manifest.relative_to(ROOT))
    write_manifest(packet)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_bytes(manifest.read_bytes())
    print(
        json.dumps(
            {
                "status": packet["status"],
                "parts": len(packet["parts"]),
                "assemblies": len(packet.get("assemblies", [])),
                "runtime": packet.get("runtime"),
                "parent_wall_seconds": packet["parent_wall_seconds"],
                "report": str(REPORT.relative_to(ROOT)),
            }
        )
    )
    return code


if __name__ == "__main__":
    raise SystemExit(main())
