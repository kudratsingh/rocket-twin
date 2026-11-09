"""Derived, capped fin-attachment inspection sections of registered STEP bytes.

One explicit 120 wall/90 CPU-second worker. No source CAD reconstruction,
physical design, mass/inertia or engineering qualification. --prepare verifies
cached bytes, or reproduces only exact registered bytes from the same STEP inputs.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CATALOG = "docs/studies/frontend-fin-attachment-20261109/geometry.json"
MANIFEST = "docs/studies/frontend-desktop-detail-20261108/cad-export.json"
MANIFEST_SHA = "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731"
SCRIPT = "scripts/wo04_fin_attachment_export.py"
CACHE = ".cache/rp1-fin-attachment"
PUBLIC = "web/public/engineering-workbench/rp1-fin-attachment"
PREFIX = "/engineering-workbench/rp1-fin-attachment/"
IDS = (
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
CONFIGURATION = "G80-F2-RP1-AD1-definition-v2"
CORE = "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
JOINT_SHA = "2ea1796f0b506ce382e1f7f9d25280b21c2f30d2119bb3aa52f257c0e2cff119"
FRAME = {"units": "m", "cad_units": "mm", "viewer_mapping": "[cadX/1000,1.25-cadZ/1000,cadY/1000]"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def revision(value: Any) -> str:
    return sha(json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode())


def checked(root: Path, path: str, expected: str) -> Path:
    target = (root / path).resolve()
    if not target.is_relative_to(root.resolve()) or not target.is_file():
        raise ValueError(f"Required registered source unavailable: {path}")
    if sha(target.read_bytes()) != expected:
        raise ValueError(f"Registered source hash mismatch: {path}")
    return target


def source_packet(root: Path) -> dict[str, Any]:
    packet = json.loads(checked(root, MANIFEST, MANIFEST_SHA).read_bytes())
    if (
        packet["identity"]["configuration_id"] != CONFIGURATION
        or packet["identity"]["inspection_geometry_sha256"] != CORE
    ):
        raise ValueError("Foreign registered STEP source identity")
    for path, pin in packet["source_hashes"].items():
        checked(root, path, pin)
    checked(root, packet["script"]["path"], packet["script"]["sha256"])
    core = checked(
        root,
        "docs/studies/rp1-inspection-geometry-20261107/manifest.json",
        packet["core_manifest_sha256"],
    )
    if (root / "output/rp1-inspection-geometry/manifest.json").read_bytes() != core.read_bytes():
        raise ValueError("Frozen core manifest supply mismatch")
    rows = {r["id"]: r for r in packet["parts"]}
    for pid in IDS:
        row = rows[pid]
        checked(root, row["path"], row["sha256"])
        checked(root, row["core_glb"]["path"], row["core_glb"]["sha256"])
    joint = next(a for a in packet["assemblies"] if a["id"] == "critical_motor_fin_ring_joint")
    if joint["part_ids"] != list(IDS) or joint["sha256"] != JOINT_SHA:
        raise ValueError("Registered joint scope mismatch")
    checked(root, joint["path"], JOINT_SHA)
    return packet


def bounds(shape: Any) -> list[list[float]]:
    b = shape.BoundingBox()
    result = [[b.xmin, b.ymin, b.zmin], [b.xmax, b.ymax, b.zmax]]
    if not all(math.isfinite(v) for corner in result for v in corner):
        raise ValueError("Nonfinite BRep bounds")
    return result


def viewer(point: Any) -> list[float]:
    p = point.toTuple() if hasattr(point, "toTuple") else point
    return [float(p[0]) / 1000, 1.25 - float(p[2]) / 1000, float(p[1]) / 1000]


def viewer_bounds(shape: Any) -> list[list[float]]:
    b = bounds(shape)
    return [
        [b[0][0] / 1000, 1.25 - b[1][2] / 1000, b[0][1] / 1000],
        [b[1][0] / 1000, 1.25 - b[0][2] / 1000, b[1][1] / 1000],
    ]


def validate_solid(shape: Any) -> None:
    if (
        not shape.isValid()
        or not shape.Solids()
        or any(not shell.Closed() for shell in shape.Shells())
    ):
        raise ValueError("Invalid or unclosed retained BRep solid")


def half_sections(
    shape: Any, axis: int, offset: float
) -> tuple[Any | None, Any | None, list[Any], dict[str, Any]]:
    """Exact BRep intersections; complementary volumes partition the original."""
    import cadquery as cq

    original_bounds = bounds(shape)
    halves = []
    for positive in (True, False):
        lo, hi = ([v - 1 for v in original_bounds[0]], [v + 1 for v in original_bounds[1]])
        if positive:
            lo[axis] = offset
        else:
            hi[axis] = offset
        if hi[axis] <= original_bounds[0][axis] or lo[axis] >= original_bounds[1][axis]:
            halves.append(None)
            continue
        if lo[axis] <= original_bounds[0][axis] and hi[axis] >= original_bounds[1][axis]:
            result = shape
        else:
            box = cq.Solid.makeBox(*(hi[i] - lo[i] for i in range(3)), cq.Vector(*lo))
            result = shape.intersect(box)
        if not result.Solids() or result.Volume() < 1e-8:
            halves.append(None)
        else:
            validate_solid(result)
            halves.append(result)
    original = shape.Volume()
    values = [part.Volume() if part is not None else 0.0 for part in halves]
    error = abs(sum(values) - original)
    if error > max(1e-5, original * 1e-7):
        raise ValueError("Complementary section BRep volumes do not partition source")
    for half in halves:
        if half is not None:
            b = bounds(half)
            if any(
                b[0][i] < original_bounds[0][i] - 1e-5 or b[1][i] > original_bounds[1][i] + 1e-5
                for i in range(3)
            ):
                raise ValueError("Half-section exceeds source bounds")
    faces = []
    if halves[0] is not None and halves[1] is not None:
        for face in halves[0].Faces():
            b = bounds(face)
            if (
                face.geomType() == "PLANE"
                and abs(b[0][axis] - offset) < 1e-5
                and abs(b[1][axis] - offset) < 1e-5
            ):
                faces.append(face)
    # Disconnected source solids can lie wholly on either side without a cut.
    if (
        halves[0] is not None
        and halves[1] is not None
        and not faces
        and len(halves[0].Solids()) + len(halves[1].Solids()) != len(shape.Solids())
    ):
        raise ValueError("A crossing solid has no planar cut face")
    return (
        halves[0],
        halves[1],
        faces,
        {
            "source_volume_mm3": original,
            "positive_volume_mm3": values[0],
            "negative_volume_mm3": values[1],
            "partition_error_mm3": error,
            "source_bounds_mm": original_bounds,
        },
    )


def box_case() -> dict[str, Any]:
    import cadquery as cq

    box = cq.Solid.makeBox(10, 8, 6, cq.Vector(-5, -4, -3))
    records = []
    for axis in (1, 2):
        positive, negative, faces, record = half_sections(box, axis, 0)
        if (
            positive is None
            or negative is None
            or len(faces) != 1
            or abs(positive.Volume() - 240) > 1e-7
        ):
            raise ValueError("Known box half-section failed")
        expected_area = 60 if axis == 1 else 80
        if abs(faces[0].Area() - expected_area) > 1e-7:
            raise ValueError("Known box cap area failed")
        records.append({**record, "axis": axis, "cap_area_mm2": faces[0].Area()})
    return {"valid": True, "cases": records}


def mesh_bytes(shape: Any, color: str) -> tuple[bytes, list[list[float]]]:
    import numpy as np
    import trimesh

    vertices, triangles = shape.tessellate(0.15, 0.15)
    if not vertices or not triangles:
        raise ValueError("Nonempty BRep produced no triangles")
    mesh = trimesh.Trimesh(
        vertices=np.array([viewer(v) for v in vertices]), faces=np.asarray(triangles), process=False
    )
    mesh.visual.face_colors = trimesh.visual.color.hex_to_rgba(color)
    return trimesh.Scene(mesh).export(file_type="glb"), mesh.bounds.tolist()


def dimensions(root: Path) -> list[dict[str, Any]]:
    import yaml

    spec_path = "configs/vehicle/candidates/g80-f2-rp1-ad1-v2.yaml"
    definition_path = "configs/studies/rp1-attachment-definition-v2.yaml"
    spec = yaml.safe_load((root / spec_path).read_bytes())
    definition = yaml.safe_load((root / definition_path).read_bytes())
    parts = {p["id"]: p for p in spec["parts"]}
    fj = definition["fin_joints"]
    start = parts["fin_tabs"]["position_m"] * 1000
    station = (start + fj["aft_tab_end_mm"]) / 2
    if abs(station - 1134.9) > 1e-8:
        raise ValueError("Frozen tab midpoint changed")
    thickness = parts["fin_set"]["geometry"]["thickness_m"] * 1000
    tab_x = (fj["tab_inner_flat_radius_mm"] + parts["fin_set"]["geometry"]["radius_m"] * 1000) / 2
    slot_x = (
        parts["body"]["geometry"]["radius_m"] - parts["body"]["geometry"]["wall_m"] / 2
    ) * 1000
    values = [
        (
            "tab-thickness",
            "Nominal first-fin tab thickness",
            thickness,
            None,
            spec_path,
            "parts[id=fin_set].geometry.thickness_m",
            ["fin_tabs", "fin_set"],
            [[tab_x, -thickness / 2, station], [tab_x, thickness / 2, station]],
            "Source nominal6mm; not incoming thickness measurement",
        ),
        (
            "slot-width",
            "AD1 body slot width",
            fj["external_slot_width_mm"],
            fj["slot_cut_tolerance_mm"],
            definition_path,
            "fin_joints.external_slot_width_mm; fin_joints.slot_cut_tolerance_mm",
            ["body", "fin_tabs"],
            [
                [slot_x, -fj["external_slot_width_mm"] / 2, station],
                [slot_x, fj["external_slot_width_mm"] / 2, station],
            ],
            "Corrected source cut width; tolerance is proposed cut tolerance, not measured fit",
        ),
        (
            "aft-gap",
            "Nominal tab-end / aft-ring station gap",
            round(fj["aft_ring_front_mm"] - fj["aft_tab_end_mm"], 8),
            None,
            definition_path,
            "fin_joints.aft_ring_front_mm - fin_joints.aft_tab_end_mm",
            ["fin_tabs", "aft_ring"],
            [[25, 0, fj["aft_tab_end_mm"]], [25, 0, fj["aft_ring_front_mm"]]],
            "Computed difference of two source stations; no direct butt support or installed-clearance qualification",
        ),
    ]
    return [
        {
            "id": key,
            "label": label,
            "value_mm": value,
            "tolerance_mm": tolerance,
            "basis": basis,
            "source": {"path": path, "sha256": sha((root / path).read_bytes()), "locator": locator},
            "feature_ids": features,
            "points_m": [viewer(p) for p in points],
        }
        for key, label, value, tolerance, path, locator, features, points, basis in values
    ]


def generate(root: Path, destination: Path) -> dict[str, Any]:
    """One bounded worker's computation; output only into its staging directory."""
    import cadquery as cq
    import numpy as np
    import trimesh
    import yaml

    started_wall, started_cpu = time.monotonic(), time.process_time()
    source = source_packet(root)
    before = {path: sha((root / path).read_bytes()) for path in source["source_hashes"]}
    case = box_case()
    rows = {p["id"]: p for p in source["parts"]}
    spec = yaml.safe_load((root / source["identity"]["specification_path"]).read_bytes())
    originals = {p["id"]: p for p in spec["parts"]}
    destination.mkdir(parents=True)
    sections = [
        {
            "id": "longitudinal",
            "label": "Longitudinal half — CAD Y=0",
            "plane_cad_mm": {"normal": [0, 1, 0], "offset": 0.0},
            "axis": 1,
            "kept_side": "positive",
            "viewerplane": {"normal": [0, 0, 1], "constant": 0.0},
        },
        {
            "id": "transverse",
            "label": "Transverse aft half — tab midpoint1134.9mm",
            "plane_cad_mm": {"normal": [0, 0, 1], "offset": 1134.9},
            "axis": 2,
            "kept_side": "positive",
            "viewerplane": {"normal": [0, -1, 0], "constant": 0.1151},
        },
    ]
    packet: dict[str, Any] = {
        "schema_version": 1,
        "id": "rp1-fin-attachment-inspection-v1",
        "configuration_id": CONFIGURATION,
        "specification_sha256": source["identity"]["specification_sha256"],
        "definition_sha256": source["identity"]["definition_sha256"],
        "inspection_geometry_sha256": CORE,
        "frame": FRAME,
        "parts": [],
        "sections": sections,
        "dimensions": dimensions(root),
        "all55_part_ids": [r["id"] for r in source["source_records"]],
        "focus_bounds_m": [[-0.055, 0.045, -0.09], [0.1, 0.195, 0.09]],
        "sources": {**before, MANIFEST: MANIFEST_SHA, SCRIPT: sha((root / SCRIPT).read_bytes())},
        "validation": {
            "known_box": case,
            "tessellation_mm": 0.15,
            "angular_tessellation_radians": 0.15,
            "meaning": "BRep/readback representation checks, not engineering fit tolerances",
        },
        "callout_only_part_ids": [
            "fin_internal_bonds",
            "outer_fin_fillets",
            "ring_bonds",
            "ad1_slot_fill",
        ],
        "limits": [
            "Inspection sections of fixed registered source CAD, not a physical construction change",
            "Motor and retainer are nominal envelopes; threads/seats/nozzle contact remain undefined",
            "Forward ring is the registered single notched annulus, not optional three-layer display geometry",
            "No adhesive solid, equal load sharing, direct tab butt support or installed fit/strength claim",
            "No canonical mass/inertia, manufacturing or flight qualification",
        ],
        "engineering_accepted": False,
        "mass_or_inertia_generated": False,
        "canonical_vehicle_geometry_changed": False,
        "tools": {"cadquery": cq.__version__, "trimesh": trimesh.__version__},
    }
    shapes = []

    def guard() -> None:
        if time.monotonic() - started_wall > 108 or time.process_time() - started_cpu > 80:
            raise TimeoutError("Fin section cooperative reserve reached; no retry")

    def save(
        pid: str, variant: str, shape: Any, faces: list[Any], record: dict[str, Any]
    ) -> dict[str, Any]:
        guard()
        color = originals[pid]["cad"]["color"]
        data, bb = mesh_bytes(shape, color)
        name = f"{pid}--{variant}.glb"
        (destination / name).write_bytes(data)
        loaded = trimesh.load(destination / name, force="scene").to_geometry()
        if np.max(np.abs(loaded.bounds - bb)) > 2e-7:
            raise ValueError("GLB readback bounds mismatch")
        cap_url, cap_sha = None, None
        if faces:
            cap_data, _ = mesh_bytes(cq.Compound.makeCompound(faces), color)
            cap_name = f"{pid}--{variant}--cap.glb"
            (destination / cap_name).write_bytes(cap_data)
            cap_url, cap_sha = PREFIX + cap_name, sha(cap_data)
        edge_lines = []
        for face in faces:
            for edge in face.Edges():
                points, _ = edge.sample(0.15)
                line = [viewer(p) for p in points]
                if edge.IsClosed() and line:
                    line.append(line[0])
                edge_lines.append(line)
        return {
            "url": PREFIX + name,
            "sha256": sha(data),
            "bytes": len(data),
            "bounds_m": loaded.bounds.tolist(),
            "solid_count": len(shape.Solids()),
            "closed": True,
            "cut_faces": [
                {
                    "bounds_m": viewer_bounds(f),
                    "area_mm2": f.Area(),
                    "planar": True,
                }
                for f in faces
            ],
            "cut_edges_m": edge_lines,
            "cap_url": cap_url,
            "cap_sha256": cap_sha,
            "validation": record,
        }

    for pid in IDS:
        guard()
        row = rows[pid]
        shape = cq.Compound.makeCompound(
            cq.importers.importStep(str(root / row["path"]), unit="MM").vals()
        )
        validate_solid(shape)
        if (
            len(shape.Solids()) != row["readback"]["solids"]
            or np.max(np.abs(np.array(bounds(shape)) - row["cad_bounds_mm"])) > 1e-5
        ):
            raise ValueError("Registered part STEP readback changed")
        shapes.append(shape)
        assets = {
            "assembled": save(
                pid,
                "assembled",
                shape,
                [],
                {"source_bounds_mm": bounds(shape), "readback_valid": True},
            )
        }
        statuses = {"assembled": "complete registered source part"}
        for section in sections:
            guard()
            positive, _, faces, record = half_sections(
                shape, section["axis"], section["plane_cad_mm"]["offset"]
            )
            variant = section["id"]
            assets[variant] = (
                save(pid, variant, positive, faces, record) if positive is not None else None
            )
            statuses[variant] = (
                "retained CAD solid with true planar faces"
                if faces
                else (
                    "retained whole/disconnected solid; no crossing face"
                    if positive is not None
                    else "outside retained half-space; no solid or fake cap"
                )
            )
        packet["parts"].append(
            {
                "id": pid,
                "label": pid.replace("_", " "),
                "maturity": row["maturity"],
                "material": row["material"],
                "source": {
                    "path": row["path"],
                    "sha256": row["sha256"],
                    "specification": row["source"],
                    "definition": row["definition_source"],
                    "inspection_shape_sha256": row["inspection_shape_sha256"],
                },
                "assets": assets,
                "section_status": statuses,
            }
        )
    guard()
    joint = next(a for a in source["assemblies"] if a["id"] == "critical_motor_fin_ring_joint")
    loaded = cq.Compound.makeCompound(
        cq.importers.importStep(str(root / joint["path"]), unit="MM").vals()
    )
    validate_solid(loaded)
    if len(loaded.Solids()) != sum(len(s.Solids()) for s in shapes) or abs(
        loaded.Volume() - sum(s.Volume() for s in shapes)
    ) > max(1e-4, loaded.Volume() * 1e-7):
        raise ValueError("Whole joint readback/scope differs from nine registered source parts")
    if np.max(np.abs(np.array(bounds(loaded)) - joint["readback"]["bounds_mm"])) > 1e-5:
        raise ValueError("Whole joint readback bounds differ")
    packet["download"] = {
        "url": "/engineering-workbench/rp1-step/critical_motor_fin_ring_joint.step",
        "sha256": JOINT_SHA,
        "bytes": joint["bytes"],
        "provenance_url": "/engineering-workbench/rp1-step/provenance.json",
        "provenance_sha256": MANIFEST_SHA,
        "units": "mm",
        "included_part_ids": list(IDS),
    }
    packet["validation"]["joint_readback"] = {
        "solids": len(loaded.Solids()),
        "valid": True,
        "bounds_mm": bounds(loaded),
    }
    source_packet(root)
    if any(sha((root / p).read_bytes()) != pin for p, pin in packet["sources"].items()):
        raise ValueError("Fin section inputs changed during export")
    packet["runtime"] = {
        "wall_seconds": time.monotonic() - started_wall,
        "cpu_seconds": time.process_time() - started_cpu,
        "cost_usd": 0,
    }
    packet["revision_sha256"] = revision(packet)
    (destination / "catalog.json").write_text(json.dumps(packet, indent=2) + "\n")
    return packet


def registered_files(packet: dict[str, Any]) -> dict[str, str]:
    files = {}
    for part in packet["parts"]:
        for asset in part["assets"].values():
            if asset:
                files[asset["url"]] = asset["sha256"]
                if asset["cap_url"]:
                    files[asset["cap_url"]] = asset["cap_sha256"]
    download = packet["download"]
    if (
        download["url"] != "/engineering-workbench/rp1-step/critical_motor_fin_ring_joint.step"
        or download["sha256"] != JOINT_SHA
        or download["provenance_url"] != "/engineering-workbench/rp1-step/provenance.json"
        or download["provenance_sha256"] != MANIFEST_SHA
        or download["included_part_ids"] != list(IDS)
    ):
        raise ValueError("Unregistered joint STEP/provenance reference")
    for url in files:
        if not url.startswith(PREFIX) or "/" in url[len(PREFIX) :] or ".." in url:
            raise ValueError("Unregistered fin-attachment asset URL")
    return files


def prepare(root: Path = ROOT, destination: Path | None = None) -> dict[str, Any]:
    """Only this recorded packet; no catalog/STEP/core modification or pin relaxation."""
    packet = json.loads((root / CATALOG).read_bytes())
    expected_revision = packet["revision_sha256"]
    if revision({k: v for k, v in packet.items() if k != "revision_sha256"}) != expected_revision:
        raise ValueError("Fin attachment catalog content revision mismatch")
    source_packet(root)
    for path, pin in packet["sources"].items():
        checked(root, path, pin)
    files = registered_files(packet)
    target = (destination or root / PUBLIC).resolve()
    if target != (root / PUBLIC).resolve() and not target.is_relative_to(
        Path(tempfile.gettempdir()).resolve()
    ):
        raise ValueError("Only fixed public or temporary test destination allowed")

    def valid(folder: Path) -> bool:
        if folder.exists() and any(
            p.name not in {u[len(PREFIX) :] for u in files} for p in folder.iterdir()
        ):
            raise ValueError("Unregistered destination files preserved")
        return all(
            (folder / u[len(PREFIX) :]).is_file()
            and sha((folder / u[len(PREFIX) :]).read_bytes()) == pin
            for u, pin in files.items()
        )

    if valid(target):
        return {
            "status": "verified_existing",
            "files": len(files),
            "revision_sha256": expected_revision,
        }
    cache = root / CACHE
    if not all((cache / u[len(PREFIX) :]).is_file() for u in files):
        with tempfile.TemporaryDirectory(prefix="fin-attachment-reconstruct-") as temporary:
            staging = Path(temporary) / "assets"
            run_worker(root, staging)
            reproduced = json.loads((staging / "catalog.json").read_bytes())
            if registered_files(reproduced) != files or reproduced["parts"] != packet["parts"]:
                raise ValueError(
                    "Recorded section byte/geometry reproduction mismatch; no replacement"
                )
            cache.mkdir(parents=True, exist_ok=True)
            for url, pin in files.items():
                name = url[len(PREFIX) :]
                checked(staging, name, pin)
                shutil.copyfile(staging / name, cache / name)
    for url, pin in files.items():
        checked(cache, url[len(PREFIX) :], pin)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".fin-attachment-stage-", dir=target.parent
    ) as temporary:
        staging = Path(temporary)
        for url, pin in files.items():
            name = url[len(PREFIX) :]
            shutil.copyfile(cache / name, staging / name)
            checked(staging, name, pin)
        source_packet(root)
        if target.exists():
            # Existing registered files can only be replaced after all new bytes validate.
            for p in target.iterdir():
                if p.name not in {u[len(PREFIX) :] for u in files}:
                    raise ValueError("Unregistered destination files preserved")
            for p in staging.iterdir():
                os.replace(p, target / p.name)
        else:
            staging.rename(target)
    return {"status": "prepared", "files": len(files), "revision_sha256": expected_revision}


def run_worker(root: Path, destination: Path) -> None:
    command = [sys.executable, str(root / SCRIPT), "--worker", str(destination)]
    subprocess.run(command, cwd=root, timeout=120, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--export", action="store_true")
    mode.add_argument("--prepare", action="store_true")
    mode.add_argument("--worker", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        import resource
        import signal

        resource.setrlimit(resource.RLIMIT_CPU, (89, 90))
        signal.signal(signal.SIGALRM, lambda *_: sys.exit("Fin attachment120s wall cap; stop"))
        signal.alarm(120)
        packet = generate(ROOT, args.worker)
        print(json.dumps({"status": "derived", "parts": 9, "runtime": packet["runtime"]}))
    elif args.export:
        target = ROOT / CATALOG
        if target.exists() or (ROOT / CACHE).exists():
            raise ValueError("Initial fin-attachment export is already recorded; no rerun")
        run_worker(ROOT, ROOT / CACHE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / CACHE / "catalog.json", target)
        print(json.dumps({"status": "recorded", "catalog": CATALOG}))
    else:
        print(json.dumps(prepare()))


if __name__ == "__main__":
    main()
