"""Bounded, source-nominal local CAD for two RP1 part-bank recipes.

Explicit CLI only. This never modifies a vehicle, physics model, installed CAD,
part registry, or mass accounting. Run --build once, then --prepare for the
fixed public cache; --check is read-only. No browser-triggered execution.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SCRIPT = "scripts/wo04_part_template_geometry.py"
PREPARED = ROOT / "web/public/engineering-workbench/rp1-part-templates.json"
OUTPUT = ROOT / "output/rp1-template-geometry-v1"
PUBLIC = ROOT / "web/public/engineering-workbench/rp1-part-templates-geometry"
DOCUMENT = ROOT / "docs/studies/frontend-template-bank-20261109/geometry.json"
REGISTRY_REVISION = "cb43e923df940ba0a1f9ec80216a194bd1cbc85e92b1eac5c77f3e18b55fd9be"
PREPARED_SHA256 = "f2b1c4ab801f3ba8b1b8f95659bca3d116bf169246e394f42aef0987763b28f8"
CASES = ("motor-tube-cut", "aft-annular-ring")
CASE_WALL_SECONDS = 120
CASE_CPU_SECONDS = 90
PACKET_WALL_SECONDS = 270
PACKET_CPU_SECONDS = 180
STEP_BOUNDS_TOLERANCE_MM = 1e-5
GLB_BOUNDS_TOLERANCE_M = 0.00025


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_record(path: Path, *, url: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.relative_to(ROOT)),
        "sha256": sha(path.read_bytes()),
        "bytes": path.stat().st_size,
    }
    if url is not None:
        record["url"] = url
    return record


def source_catalog(root: Path = ROOT) -> dict[str, Any]:
    from src.vehicle import part_templates

    if root != ROOT or PREPARED.is_symlink() or sha(PREPARED.read_bytes()) != PREPARED_SHA256:
        raise ValueError("Frozen prepared source bytes differ")
    prepared = json.loads(PREPARED.read_bytes())
    catalog = part_templates.validate_catalog(root, prepared)
    if catalog["revision_sha256"] != REGISTRY_REVISION:
        raise ValueError("Frozen registry revision differs")
    return catalog


def nominal_requests(catalog: dict[str, Any]) -> list[dict[str, Any]]:
    from src.vehicle.part_templates import prepare_local_geometry_request

    requests = []
    for slug in CASES:
        row = next(
            (item for item in catalog["templates"] if item["id"] == f"rp1-template:{slug}"), None
        )
        if row is None:
            raise ValueError(f"Missing admitted nominal template: {slug}")
        parameters = {param["key"]: param["value"] for param in row["parameters"]}
        request = prepare_local_geometry_request(
            ROOT, catalog, row["id"], row["revision_sha256"], parameters
        )
        if (
            request["generator"] != "src.cad.parts.tube"
            or request["cad_execution"] is not False
            or request["draft_admission"] is not False
            or request["mass_kg"] is not None
        ):
            raise ValueError("Nominal request no longer has the admitted boundary")
        requests.append(request)
    return requests


def _bounds(shape: Any) -> list[list[float]]:
    box = shape.BoundingBox()
    bounds = [[box.xmin, box.ymin, box.zmin], [box.xmax, box.ymax, box.zmax]]
    if not all(math.isfinite(v) for row in bounds for v in row):
        raise ValueError("Nonfinite CAD bounds")
    return bounds


def _max_difference(a: list[list[float]], b: list[list[float]]) -> float:
    return max(abs(x - y) for aa, bb in zip(a, b, strict=True) for x, y in zip(aa, bb, strict=True))


def validate_step(shape: Any, *, outer: float, inner: float, length: float) -> dict[str, Any]:
    """Readback checks nominal annular B-rep, including a real empty central bore."""
    import cadquery as cq

    solids = shape.Solids()
    shells = shape.Shells()
    expected_bounds = [[-outer, -outer, 0.0], [outer, outer, length]]
    bounds = _bounds(shape)
    if (
        not shape.isValid()
        or len(solids) != 1
        or len(shells) != 1
        or not shells[0].Closed()
        or _max_difference(bounds, expected_bounds) > STEP_BOUNDS_TOLERANCE_MM
    ):
        raise ValueError("STEP is not one valid closed nominal annular solid")
    expected_volume = math.pi * (outer**2 - inner**2) * length
    if abs(shape.Volume() - expected_volume) > max(1e-5, expected_volume * 1e-7):
        raise ValueError("STEP annular volume differs from nominal radii/length")
    cylinder_radii = sorted(
        face.Area() / (2 * math.pi * length)
        for face in shape.Faces()
        if face.geomType() == "CYLINDER"
    )
    if (
        len(cylinder_radii) != 2
        or max(abs(cylinder_radii[0] - inner), abs(cylinder_radii[1] - outer)) > 1e-5
    ):
        raise ValueError("STEP inner/outer cylindrical faces differ from nominal diameters")
    probe = cq.Solid.makeCylinder(inner * 0.5, length * 0.8, cq.Vector(0, 0, length * 0.1))
    if shape.intersect(probe).Volume() > 1e-6:
        raise ValueError("STEP central bore is occupied")
    return {
        "valid": True,
        "closed": True,
        "solid_count": 1,
        "annular_bore": True,
        "outer_diameter_mm": 2 * cylinder_radii[1],
        "inner_diameter_mm": 2 * cylinder_radii[0],
        "length_mm": bounds[1][2] - bounds[0][2],
        "bounds_mm": bounds,
        "volume_mm3_geometry_only": shape.Volume(),
    }


def worker(slug: str) -> None:
    """Only the parent CLI invokes this fixed-path subprocess after source preflight."""
    import cadquery as cq
    import trimesh

    from src.cad.assembly import mesh
    from src.cad.parts import tube

    if slug not in CASES:
        raise ValueError("Unsupported recipe")
    catalog = source_catalog()
    request = next(
        row for row in nominal_requests(catalog) if row["template_id"] == f"rp1-template:{slug}"
    )
    params = request["parameters_mm"]
    outer, inner, length = (
        params[key] for key in ("outer_radius_mm", "inner_radius_mm", "length_mm")
    )
    staging = OUTPUT / "staging" / slug
    if staging.exists():
        raise ValueError("Prior case staging exists; no automatic retry")
    staging.mkdir(parents=True)
    shape = tube(outer, inner, length)
    validate_step(shape, outer=outer, inner=inner, length=length)
    step = staging / f"{slug}.step"
    glb = staging / f"{slug}.glb"
    cq.exporters.export(shape, str(step), exportType="STEP")
    loaded = cq.Compound.makeCompound(
        [
            value
            for value in cq.importers.importStep(str(step), unit="MM").vals()
            if isinstance(value, cq.Shape)
        ]
    )
    readback = validate_step(loaded, outer=outer, inner=inner, length=length)
    display = mesh(shape, 0.0, "#8bb9c4")
    glb.write_bytes(trimesh.Scene(display).export(file_type="glb"))  # type: ignore[no-untyped-call]
    loaded_mesh = trimesh.load(glb, force="scene").to_geometry()  # type: ignore[attr-defined]
    expected_display = [
        [-outer / 1000, -length / 1000, -outer / 1000],
        [outer / 1000, 0.0, outer / 1000],
    ]
    actual_display = [[float(value) for value in row] for row in loaded_mesh.bounds]
    display_error = _max_difference(actual_display, expected_display)
    if display_error > GLB_BOUNDS_TOLERANCE_M:
        raise ValueError("GLB metre bounds differ from local CAD mapping")
    outcome = {
        "template_id": request["template_id"],
        "template_revision_sha256": request["template_revision_sha256"],
        "parameters_mm": params,
        "readback": readback,
        "bounds_m": {"min": actual_display[0], "max": actual_display[1]},
        "glb_bounds_error_m": display_error,
        "step": file_record(step),
        "glb": file_record(glb),
        "tools": {
            "python": sys.version.split()[0],
            "cadquery": cq.__version__,
            "trimesh": trimesh.__version__,
        },
        "child_cpu_seconds": resource.getrusage(resource.RUSAGE_SELF).ru_utime
        + resource.getrusage(resource.RUSAGE_SELF).ru_stime,
    }
    (staging / "readback.json").write_text(json.dumps(outcome, indent=2, allow_nan=False) + "\n")


def _write_once(path: Path, data: bytes) -> None:
    if path.is_symlink():
        raise ValueError(f"Refusing symlink output: {path}")
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Refusing to overwrite existing output: {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(data)


def _attempt(packet: dict[str, Any]) -> None:
    path = OUTPUT / "attempt.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, indent=2, allow_nan=False) + "\n")


def build() -> dict[str, Any]:
    if DOCUMENT.exists() or (OUTPUT.exists() and any(OUTPUT.iterdir())):
        raise ValueError("Prior geometry packet exists; use --check, never blind rerun")
    catalog = source_catalog()
    requests = nominal_requests(catalog)
    started = time.monotonic()
    cpu_before = resource.getrusage(resource.RUSAGE_CHILDREN)
    packet: dict[str, Any] = {
        "status": "started",
        "budget": {
            "case_wall_seconds": CASE_WALL_SECONDS,
            "case_cpu_seconds": CASE_CPU_SECONDS,
            "packet_wall_seconds": PACKET_WALL_SECONDS,
            "packet_cpu_seconds": PACKET_CPU_SECONDS,
        },
        "cases": [],
    }
    _attempt(packet)
    try:
        for request in requests:
            elapsed = time.monotonic() - started
            used = resource.getrusage(resource.RUSAGE_CHILDREN)
            cpu_used = used.ru_utime + used.ru_stime - cpu_before.ru_utime - cpu_before.ru_stime
            if elapsed >= PACKET_WALL_SECONDS or cpu_used >= PACKET_CPU_SECONDS:
                raise TimeoutError("Whole packet resource cap reached; no next case")
            slug = request["template_id"].split(":", 1)[1]
            case_started = time.monotonic()
            result = subprocess.run(
                [sys.executable, str(ROOT / SCRIPT), "--worker", slug],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=min(CASE_WALL_SECONDS, PACKET_WALL_SECONDS - elapsed),
                check=False,
                preexec_fn=lambda: resource.setrlimit(
                    resource.RLIMIT_CPU, (CASE_CPU_SECONDS - 1, CASE_CPU_SECONDS)
                ),
            )
            case_record = {
                "template_id": request["template_id"],
                "wall_seconds": time.monotonic() - case_started,
                "returncode": result.returncode,
                "stderr_tail": result.stderr[-2000:],
            }
            packet["cases"].append(case_record)
            _attempt(packet)
            if result.returncode != 0:
                raise RuntimeError(f"CAD case stopped: {slug}: {result.stderr[-500:]}")
        used = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_used = used.ru_utime + used.ru_stime - cpu_before.ru_utime - cpu_before.ru_stime
        elapsed = time.monotonic() - started
        if elapsed > PACKET_WALL_SECONDS or cpu_used > PACKET_CPU_SECONDS:
            raise TimeoutError("Whole packet resource cap exceeded; do not publish")
        representations = []
        for request in requests:
            slug = request["template_id"].split(":", 1)[1]
            staging = OUTPUT / "staging" / slug
            result = json.loads((staging / "readback.json").read_bytes())
            if (
                result["template_revision_sha256"] != request["template_revision_sha256"]
                or result["parameters_mm"] != request["parameters_mm"]
            ):
                raise ValueError("Worker result differs from admitted nominal request")
            assets = {}
            for extension in ("step", "glb"):
                source = staging / f"{slug}.{extension}"
                target = OUTPUT / f"{slug}.{extension}"
                _write_once(target, source.read_bytes())
                assets[extension] = file_record(
                    target,
                    url=f"/engineering-workbench/rp1-part-templates-geometry/{slug}.{extension}",
                )
            representations.append(
                {
                    "template_id": request["template_id"],
                    "template_revision_sha256": request["template_revision_sha256"],
                    "representation_status": "source_nominal_local_only",
                    "parameters_mm": request["parameters_mm"],
                    "bounds_m": result["bounds_m"],
                    "readback": result["readback"],
                    "glb_bounds_error_m": result["glb_bounds_error_m"],
                    **assets,
                }
            )
        manifest = {
            "schema_version": 1,
            "id": "rp1-template-geometry-v1",
            "configuration_id": catalog["configuration_id"],
            "specification_sha256": catalog["identity"]["specification"]["sha256"],
            "registry": {
                "id": catalog["id"],
                "revision_sha256": REGISTRY_REVISION,
                "prepared_sha256": PREPARED_SHA256,
            },
            "source": catalog["identity"],
            "script": {"path": SCRIPT, "sha256": sha((ROOT / SCRIPT).read_bytes())},
            "cad_generator": {
                "path": "src/cad/parts.py",
                "sha256": sha((ROOT / "src/cad/parts.py").read_bytes()),
                "call": "src.cad.parts.tube",
            },
            "local_cad_frame_mm": "front center; X=body+y, Y=body-z, Z=aft along part",
            "viewer_mapping": "viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]",
            "viewer_units": "m",
            "step_units": "mm",
            "representations": representations,
            "resources": {
                "elapsed_wall_seconds": elapsed,
                "child_cpu_seconds": cpu_used,
                "limits": packet["budget"],
                "cases": packet["cases"],
            },
            "mass_or_inertia_generated": False,
            "draft_admission": False,
            "vehicle_adoption": False,
            "engineering_accepted": False,
            "physical_verification": "open",
            "flight_ready": False,
            "limitations": [
                "Nominal local inspection recipes only; not installed CAD or qualified fit",
                "No motor/liner/retainer mating, bond strength, tolerance stack or manufactured part acceptance",
                "No mass, inertia, thermal, structural or flight result",
            ],
        }
        data = (json.dumps(manifest, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
        _write_once(DOCUMENT, data)
        _write_once(OUTPUT / "manifest.json", data)
        packet["status"] = "complete"
        packet["elapsed_wall_seconds"] = elapsed
        packet["child_cpu_seconds"] = cpu_used
        _attempt(packet)
        return manifest
    except BaseException as error:
        packet["status"] = "stopped"
        packet["error"] = f"{type(error).__name__}: {error}"
        packet["elapsed_wall_seconds"] = time.monotonic() - started
        _attempt(packet)
        raise


def validate_manifest() -> dict[str, Any]:
    catalog = source_catalog()
    data = DOCUMENT.read_bytes()
    if (OUTPUT / "manifest.json").read_bytes() != data:
        raise ValueError("Output and tracked manifest bytes differ")
    manifest: dict[str, Any] = json.loads(data)
    if (
        manifest["id"] != "rp1-template-geometry-v1"
        or manifest["registry"]
        != {
            "id": catalog["id"],
            "revision_sha256": REGISTRY_REVISION,
            "prepared_sha256": PREPARED_SHA256,
        }
        or manifest["script"] != {"path": SCRIPT, "sha256": sha((ROOT / SCRIPT).read_bytes())}
        or len(manifest["representations"]) != 2
        or manifest["mass_or_inertia_generated"] is not False
        or manifest["vehicle_adoption"] is not False
    ):
        raise ValueError("Template geometry manifest source or status mismatch")
    requests = nominal_requests(catalog)
    for row, request in zip(manifest["representations"], requests, strict=True):
        if (
            row["template_id"] != request["template_id"]
            or row["template_revision_sha256"] != request["template_revision_sha256"]
            or row["parameters_mm"] != request["parameters_mm"]
            or row["representation_status"] != "source_nominal_local_only"
            or row["readback"]["valid"] is not True
            or row["readback"]["closed"] is not True
            or row["readback"]["annular_bore"] is not True
            or row["readback"]["solid_count"] != 1
        ):
            raise ValueError("Template geometry representation differs")
        for extension in ("step", "glb"):
            asset = row[extension]
            slug = request["template_id"].split(":", 1)[1]
            expected_path = OUTPUT / f"{slug}.{extension}"
            expected_url = f"/engineering-workbench/rp1-part-templates-geometry/{slug}.{extension}"
            if asset != file_record(expected_path, url=expected_url):
                raise ValueError("Template geometry asset path/hash/size differs")
    return manifest


def prepare() -> dict[str, Any]:
    manifest = validate_manifest()
    if PUBLIC.is_symlink():
        raise ValueError("Refusing symlink public cache")
    for row in manifest["representations"]:
        for extension in ("step", "glb"):
            source = ROOT / row[extension]["path"]
            target = PUBLIC / source.name
            _write_once(target, source.read_bytes())
    _write_once(PUBLIC / "provenance.json", DOCUMENT.read_bytes())
    return manifest


def check(*, public: bool = False) -> dict[str, Any]:
    manifest = validate_manifest()
    if public:
        for row in manifest["representations"]:
            for extension in ("step", "glb"):
                source = ROOT / row[extension]["path"]
                if (PUBLIC / source.name).read_bytes() != source.read_bytes():
                    raise ValueError("Public cache differs from validated local CAD")
        if (PUBLIC / "provenance.json").read_bytes() != DOCUMENT.read_bytes():
            raise ValueError("Public provenance differs")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--build", action="store_true")
    action.add_argument("--prepare", action="store_true")
    action.add_argument("--check", action="store_true")
    action.add_argument("--worker", choices=CASES)
    parser.add_argument(
        "--public", action="store_true", help="With --check, verify public cache too"
    )
    args = parser.parse_args()
    try:
        if args.worker:
            worker(args.worker)
            return
        if args.build:
            result = build()
        elif args.prepare:
            result = prepare()
        else:
            result = check(public=args.public)
    except (OSError, ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired) as error:
        parser.error(str(error))
    print(f"{result['id']}: {len(result['representations'])} source-nominal local representations")


if __name__ == "__main__":
    main()
