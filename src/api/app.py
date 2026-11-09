"""Read-only inspection of resolved specifications and recorded engineering artifacts.

Mass/CG/inertia and Barrowman CP use the existing backend models. Vehicle snapshots
are assembled when the app starts. Registered analysis manifests are indexed on
demand so completed offline exports appear without a restart. GET requests never
run CAD, flight or engineering solvers. Identity/file checks fail closed.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from itertools import islice
from pathlib import Path
from typing import Annotated, Any, cast

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from src.analysis.records import AnalysisRecord, Identity, asset_path, load_compatible
from src.api import (
    candidate_snapshot,
    rp1_connections,
    rp1_geometry,
    rp1_inspection,
    rp1_inspection_view,
)
from src.vehicle.aero import center_of_pressure
from src.vehicle.cad_contract import digest
from src.vehicle.mass import mass_properties
from src.vehicle.motors import load_rasp
from src.vehicle.schema import Vehicle, load_vehicle, vehicle_input_paths

ROOT = Path(__file__).resolve().parents[2]
STATUS = "Preliminary design — engineering acceptance remains open"


@dataclass(frozen=True)
class CatalogEntry:
    path: str
    label: str
    role: str
    design_status: str
    group: str
    description: str


CATALOG = (
    CatalogEntry(
        "configs/vehicle/platform/performance.yaml",
        "Archived G80 reference · 3D/replay fixture",
        "reference",
        "Preliminary reference; engineering acceptance open",
        "reference",
        "Historical modular fixed-motor reference; matching CAD/run fixture, separate from current RP1 AD1 source definition.",
    ),
    CatalogEntry(
        "configs/vehicle/wo02/performance-g54.yaml",
        "G54 conditional upgrade",
        "conditional_upgrade",
        "Conditional; thermal and motor-CG sensitivities remain open",
        "conditional",
        "Near-160 N s performance hypothesis; no motor or hardware choice is frozen.",
    ),
    CatalogEntry(
        "configs/vehicle/platform/tvc-finned.yaml",
        "G12 finned TVC trainer",
        "trainer",
        "Preliminary trainer; recovery and guide budget unresolved",
        "trainer",
        "Physical finned TVC configuration for the future PID-to-RL progression.",
    ),
    CatalogEntry(
        "configs/vehicle/platform/tvc-finless.yaml",
        "G12 eventual finless TVC",
        "eventual_concept",
        "Concept; negative passive stability and control gates remain open",
        "concept",
        "Eventual finless configuration; active control and burnout transition are unqualified.",
    ),
)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cad_revision(root: Path) -> str:
    return sha256(b"".join(p.read_bytes() for p in sorted((root / "src/cad").glob("*.py"))))


def vehicle_identity(vehicle: Vehicle, root: Path) -> Identity:
    return Identity(
        configuration_id=vehicle.id,
        resolved_spec_sha256=sha256(vehicle.model_dump_json(by_alias=True).encode()),
        cad_revision_sha256=cad_revision(root),
        part_shape_sha256={
            part.id: digest(part.geometry, part.cad.model_dump() if part.cad else None)
            for part in vehicle.parts
        },
    )


def safe_file(folder: Path, name: str) -> Path:
    path = folder.joinpath(*asset_path(name).parts).resolve()
    if not path.is_relative_to(folder.resolve()) or not path.is_file():
        raise ValueError("Artifact is missing or escapes its allowlisted directory")
    return path


@dataclass
class Snapshot:
    entry: CatalogEntry
    vehicle: Vehicle
    identity: Identity
    inputs: dict[str, str]
    folder: Path
    manifest: dict[str, Any] | None
    manifest_sha256: str | None
    mesh_hashes: dict[str, str]
    unavailable_reason: str | None
    traceability: dict[str, Any] | None
    data: dict[str, Any]


def _traceability(folder: Path, identity: Identity) -> dict[str, Any] | None:
    path = folder / "traceability.json"
    if not path.is_file():
        return None
    try:
        record: dict[str, Any] = json.loads(path.read_bytes())
    except (ValueError, OSError):
        return None
    if not isinstance(record, dict):
        return None
    root = folder.parents[1]
    try:
        if sha256(
            safe_file(root, "configs/engineering/traceability.yaml").read_bytes()
        ) != record.get("catalog_sha256"):
            return None
        for source, expected in record.get("source_sha256", {}).items():
            # Resolved-source provenance can name wo02/../platform/common-upper.yaml.
            # Normalize it within the repository; artifact URLs remain traversal-free.
            source_path = (root / source).resolve()
            if (
                not source_path.is_relative_to(root.resolve())
                or sha256(source_path.read_bytes()) != expected
            ):
                return None
    except (ValueError, OSError, TypeError):
        return None
    cad = record.get("cad_identity", {})
    if (
        record.get("vehicle_id") != identity.configuration_id
        or record.get("resolved_spec_sha256") != identity.resolved_spec_sha256
        or cad.get("cad_generator_sha256") != identity.cad_revision_sha256
        or cad.get("part_shape_sha256") != identity.part_shape_sha256
    ):
        return None
    return record


def _checks(vehicle: Vehicle, nominal_mass: float, cp: float) -> list[dict[str, Any]]:
    allowance = vehicle.design.mass_allowance_kg if vehicle.design else 0.0
    motor = vehicle.motor
    qualification = motor.qualification if motor else None
    rows = [
        ("resolved_spec", "Resolved specification schema", True, "Validated backend schema"),
        (
            "loaded_mass",
            "Loaded mass including growth allowance < 1.5 kg",
            nominal_mass + allowance < 1.5,
            f"{nominal_mass + allowance:.6f} kg including {allowance:.3f} kg allowance",
        ),
        (
            "propellant",
            "Propellant mass ≤ 125 g",
            bool(motor and motor.propellant_mass_kg <= 0.125),
            f"{motor.propellant_mass_kg:.6f} kg" if motor else "No motor",
        ),
        (
            "motor_scope",
            "Declared certified motor impulse ≤ 160 N s and average thrust ≤ 80 N",
            bool(qualification),
            "Declared source evidence; exact offered hardware/lot and club eligibility remain open",
        ),
    ]
    result = [
        {
            "id": key,
            "label": label,
            "status": "pass" if passed else "fail",
            "detail": detail,
            "scope": "preliminary numerical check",
        }
        for key, label, passed, detail in rows
    ]
    if vehicle.design and vehicle.design.minimum_static_margin_cal is not None:
        margins = []
        for fraction in (0.0, 1.0):
            props = mass_properties(vehicle, fraction)
            cg = (props.mass_kg * props.cg_m + allowance * vehicle.airframe["length_m"]) / (
                props.mass_kg + allowance
            )
            margins.append((cp - cg) / vehicle.airframe["body_diameter_m"])
        required = vehicle.design.minimum_static_margin_cal
        result.append(
            {
                "id": "static_margin",
                "label": "Liftoff/burnout static margin with aft growth",
                "status": "pass" if min(margins) >= required else "fail",
                "detail": f"Minimum endpoint {min(margins):.6f} cal; required {required:g} cal. Full-growth/depletion and motor-CG sensitivities require their recorded report.",
                "scope": "preliminary endpoint model",
            }
        )
    else:
        result.append(
            {
                "id": "static_margin",
                "label": "Passive stability",
                "status": "open",
                "detail": "Finless configuration requires qualified active control and burnout transition; passive stability is not an acceptance gate waiver.",
                "scope": "engineering acceptance open",
            }
        )
    result.append(
        {
            "id": "flight_release",
            "label": "Physical / flight release",
            "status": "open",
            "detail": "WO-03 expanded acceptance, owner physical qualification, exact motor/site/club checks, controls and HIL remain open.",
            "scope": "not authorized by numerical checks",
        }
    )
    return result


def _analysis_notice(record: AnalysisRecord) -> str | None:
    # This exact older band-model export is historical even if its CAD identity matches.
    if record.run_id.startswith("wo03-thermal-20261031T004856773221Z-"):
        return (
            "SUPERSEDED for thermal acceptance: this historical coaxial band model "
            "omits finite end heating and actual slot gas/radiation. Its part-mean "
            "values are exploratory, not accepted design temperatures. See "
            "docs/wo03-thermal-model-corrections.md."
        )
    return None


def _findings(trace: dict[str, Any] | None, vehicle: Vehicle) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = [
        {
            "id": "WO03-ACCEPTANCE",
            "status": "open",
            "severity": "open",
            "title": "Engineering acceptance remains open",
            "detail": "Minimum fits, recovery/guide budget, installed-root and flutter, thermal sensitivities, service/arming/routing and recovery-anchor capacity retain unresolved evidence.",
            "source": "docs/wo03-package-closure-progress.md",
            "part_ids": [],
        },
        {
            "id": "WO03-BAFFLE-FAILED-NUMERICS",
            "status": "failed",
            "severity": "failed",
            "title": "Replacement-baffle transient numerical validation failed",
            "detail": "The candidate calculation produced nonphysical local temperatures; its debug values are not accepted temperatures and cannot qualify or overlay the active design. The separate G12 shield case also failed its 45 °C screen.",
            "source": "docs/wo03-actual-debug-transient.md",
            "part_ids": [],
        },
    ]
    for item in (trace or {}).get("fmea", []):
        findings.append(
            {
                "id": item["id"],
                "status": item.get("status", "open"),
                "severity": item.get("severity", "unknown"),
                "title": item["failure_mode"],
                "detail": item.get("residual_risk", ""),
                "source": "configs/engineering/traceability.yaml",
                "part_ids": item.get("related_parts", []),
                "fmea": item,
            }
        )
    if vehicle.design and vehicle.design.mode == "tvc_finless":
        findings.append(
            {
                "id": "FINLESS-CONTROL",
                "status": "open",
                "severity": "open",
                "title": "Finless control and burnout transition unqualified",
                "detail": "Negative passive stability is explicit. A rendered vehicle does not establish control authority or safe deployment.",
                "source": "docs/STATUS.md",
                "part_ids": ["motor"],
            }
        )
    return findings


def build_snapshot(entry: CatalogEntry, root: Path) -> Snapshot:
    spec_path = root / entry.path
    vehicle = load_vehicle(spec_path)
    identity = vehicle_identity(vehicle, root)
    paths = vehicle_input_paths(spec_path)
    if vehicle.motor and vehicle.motor.curve:
        paths.extend(
            [root / vehicle.motor.curve, (root / vehicle.motor.curve).with_suffix(".yaml")]
        )
    paths.extend(
        root / name
        for name in (
            "src/vehicle/mass.py",
            "src/vehicle/aero.py",
            "src/vehicle/geometry.py",
            "src/vehicle/cad_contract.py",
        )
        if (root / name).is_file()
    )
    inputs = {str(p.relative_to(root)): sha256(p.read_bytes()) for p in paths}
    folder = root / "build" / vehicle.id
    manifest = None
    manifest_hash = None
    mesh_hashes: dict[str, str] = {}
    unavailable = None
    try:
        manifest_path = safe_file(folder, "manifest.json")
        manifest_bytes = manifest_path.read_bytes()
        manifest = json.loads(manifest_bytes)
        if Identity.model_validate(manifest["identity"]) != identity:
            raise ValueError(
                "Recorded mesh configuration/spec/CAD/part identity does not match current source"
            )
        rows = manifest["parts"]
        if {row["id"] for row in rows} != set(identity.part_shape_sha256):
            raise ValueError(
                "Recorded mesh part coverage does not match the complete resolved specification"
            )
        for row in rows:
            if row["shape_sha256"] != identity.part_shape_sha256[row["id"]]:
                raise ValueError("Recorded mesh part shape identity mismatch")
            if row["mesh"] != f"parts/{row['id']}.glb":
                raise ValueError("Recorded mesh path is outside the explicit part allowlist")
            mesh_hashes[row["id"]] = sha256(safe_file(folder, row["mesh"]).read_bytes())
        manifest_hash = sha256(manifest_bytes)
    except (OSError, ValueError, KeyError, TypeError) as error:
        unavailable = str(error)
        manifest = None
        mesh_hashes = {}
    trace = _traceability(folder, identity)
    launch, burnout = mass_properties(vehicle), mass_properties(vehicle, 1.0)
    cp = center_of_pressure(vehicle)
    diameter = vehicle.airframe["body_diameter_m"]
    allowance = vehicle.design.mass_allowance_kg if vehicle.design else 0.0
    cad_parts = {row["id"]: row for row in manifest["parts"]} if manifest else {}
    parts = []

    def subtree_mass(part_id: str) -> float:
        return launch.budget_kg[part_id] + sum(
            subtree_mass(p.id) for p in vehicle.parts if p.parent == part_id
        )

    for part in vehicle.parts:
        cad = cad_parts.get(part.id, {})
        engineering = part.engineering.model_dump() if part.engineering else {}
        related_requirements = [
            r
            for r in (trace or {}).get("requirements", [])
            if part.id in r.get("related_parts", [])
        ]
        connections = [
            i for i in (trace or {}).get("interfaces", []) if part.id in i.get("spec_parts", [])
        ]
        req_ids = {r["id"] for r in related_requirements}
        interface_ids = {i["id"] for i in connections}
        failures = [
            f
            for f in (trace or {}).get("fmea", [])
            if req_ids.intersection(f.get("requirements", []))
            or interface_ids.intersection(f.get("interfaces", []))
        ]
        parts.append(
            {
                "id": part.id,
                "name": part.id.replace("_", " ").capitalize(),
                "type": part.type,
                "parent": part.parent,
                "learn": part.learn,
                "cite": part.cite,
                "function": engineering.get("function", part.learn),
                "location": {
                    "position_m": part.position_m,
                    "cg_station_m": part.cg_station_m,
                    "lateral_offset_m": part.lateral_offset_m,
                    "explode_offset": part.explode_offset,
                },
                "dimensions": part.geometry,
                "material": part.material,
                "mass_kg": part.resolved_mass_kg,
                "subtree_mass_kg": subtree_mass(part.id),
                "cad_mass_kg": cad.get("cad_mass_kg"),
                "mass_basis": part.cad.mass_basis if part.cad else "specification estimate",
                "manufacturing": part.build.model_dump() if part.build else {},
                "engineering": engineering,
                "evidence_status": {
                    "provenance": "estimated" if part.estimate else "calculated",
                    "validation": "unvalidated",
                    "physical_verification": "required",
                    "required_physical_tests": engineering.get(
                        "required_physical_verification", []
                    ),
                },
                "connections": connections,
                "requirements": related_requirements,
                "mesh_url": (
                    f"/api/vehicles/{vehicle.id}/meshes/{part.id}.glb"
                    if part.id in mesh_hashes
                    else None
                ),
                "color": part.cad.color if part.cad else "#7aa2b6",
                "representation": {
                    "role": part.cad.role if part.cad else "unavailable",
                    "description": part.cad.notes if part.cad else "No CAD representation declared",
                    "outer_body": part.type == "nose_cone"
                    or part.id in ("body_upper", "aft_shell"),
                },
                "failure_modes": [
                    f"{f['id']}: {f['failure_mode']}. Cause: {f.get('cause', 'unavailable')}. Effect: {f.get('local_system_effect', 'unavailable')}. Mitigation: {f.get('mitigation_design_change', 'unavailable')}. Residual risk: {f.get('residual_risk', 'unavailable')}. Verification: {f.get('verification_test', 'unavailable')}. Status: {f.get('status', 'open')}."
                    for f in failures
                ],
                "fmea_records": failures,
                "source": {
                    "spec_path": entry.path,
                    "spec_inputs": [{"path": p, "sha256": h} for p, h in inputs.items()],
                    "cad_generator": part.cad.generator if part.cad else None,
                    "shape_sha256": identity.part_shape_sha256[part.id],
                },
                "raw": part.model_dump(by_alias=True),
            }
        )
    motor = vehicle.motor.model_dump() if vehicle.motor else None
    summary = {
        "length_m": vehicle.airframe["length_m"],
        "overall_length_m": max(
            vehicle.airframe["length_m"],
            *(
                p.position_m + float(p.geometry.get("length_m", p.geometry.get("bbox_m", [0])[0]))
                for p in vehicle.parts
            ),
        ),
        "diameter_m": diameter,
        "nominal_mass_kg": launch.mass_kg,
        "loaded_mass_with_allowance_kg": launch.mass_kg + allowance,
        "growth_allowance_kg": allowance,
        "cg_m": launch.cg_m,
        "cp_m": cp,
        "stability_margin_cal": (cp - launch.cg_m) / diameter,
        "burnout_cg_m": burnout.cg_m,
        "burnout_stability_margin_cal": (cp - burnout.cg_m) / diameter,
        "burnout_mass_kg": burnout.mass_kg,
        "motor": motor,
        "inertia_kg_m2": launch.inertia_kg_m2.tolist(),
        "engineering_acceptance": "open",
        "flight_ready": False,
        "coordinate_frame": "Stations in m aft from nose; meshes X=body+y, Y=length-station, Z=body-z",
        "model_scope": "Existing backend mass moments and subsonic Barrowman CP; estimated inputs, not physical qualification",
        "mass_budget": [
            {
                "part_id": part.id,
                "mass_kg": launch.budget_kg[part.id],
                "percent_total": 100 * launch.budget_kg[part.id] / launch.mass_kg,
            }
            for part in vehicle.parts
        ],
    }
    data = {
        "id": vehicle.id,
        "label": entry.label,
        "role": entry.role,
        "group": entry.group,
        "design_status": entry.design_status,
        "description": entry.description,
        "identity": identity.model_dump(),
        "calculation_sources_sha256": {
            name: value for name, value in inputs.items() if name.startswith("src/")
        },
        "summary": summary,
        "parts": parts,
        "checks": _checks(vehicle, launch.mass_kg, cp),
        "findings": _findings(trace, vehicle),
        "analysis_status": {
            "status": "engineering acceptance open",
            "compatible_runs": 0,
            "detail": "Recorded data only; calculated fields do not imply physical validation",
        },
        "mesh_status": {"available": manifest is not None, "reason": unavailable},
        "traceability_status": "identity verified" if trace else "unavailable or incompatible",
        "traceability": trace,
        "spec": vehicle.model_dump(by_alias=True),
    }
    return Snapshot(
        entry,
        vehicle,
        identity,
        inputs,
        folder,
        manifest,
        manifest_hash,
        mesh_hashes,
        unavailable,
        trace,
        data,
    )


def _ensure_current(snapshot: Snapshot, root: Path, *, meshes: bool = True) -> None:
    try:
        changed = (
            any(
                sha256((root / p).read_bytes()) != expected
                for p, expected in snapshot.inputs.items()
            )
            or cad_revision(root) != snapshot.identity.cad_revision_sha256
        )
    except OSError as error:
        raise HTTPException(503, f"Snapshot input unavailable: {error}") from error
    if changed:
        raise HTTPException(
            503,
            "Source specification/CAD changed after snapshot; restart API with matching recorded artifacts",
        )
    if meshes:
        if snapshot.manifest is None:
            raise HTTPException(
                503, {"status": "unavailable", "reason": snapshot.unavailable_reason}
            )
        try:
            current = sha256(safe_file(snapshot.folder, "manifest.json").read_bytes())
        except (ValueError, OSError) as error:
            raise HTTPException(503, f"Recorded mesh manifest unavailable: {error}") from error
        if current != snapshot.manifest_sha256:
            raise HTTPException(
                503, "Recorded mesh manifest changed; restart API and verify matching identity"
            )


def _asset_response(path: Path, expected_hash: str, request: Request, media_type: str) -> Response:
    try:
        content = path.read_bytes()
    except OSError as error:
        raise HTTPException(503, f"Recorded artifact unavailable: {error}") from error
    if sha256(content) != expected_hash:
        raise HTTPException(503, "Recorded artifact checksum changed; artifact unavailable")
    headers = {
        "ETag": f'"{expected_hash}"',
        "Cache-Control": "public, max-age=0, must-revalidate",
        "X-Content-Type-Options": "nosniff",
        "X-Artifact-SHA256": expected_hash,
    }
    if request.headers.get("if-none-match") == headers["ETag"]:
        return Response(status_code=304, headers=headers)
    return Response(content=content, media_type=media_type, headers=headers)


def _recorded_analyses(
    snapshot: Snapshot,
) -> dict[str, tuple[Path, AnalysisRecord, Snapshot, str | None]]:
    """Re-index a bounded, fixed-depth registry; never execute an analysis.

    The offline registrar publishes each run under analysis/<run>/manifest.json.
    Re-reading avoids stale availability/identity labels when exports are added,
    removed or replaced while the local preview is open. No symlink may attach
    artifacts outside this configuration's recorded geometry folder.
    """
    paths = list(islice(snapshot.folder.glob("analysis/*/manifest.json"), 257))
    if len(paths) > 256:
        raise HTTPException(503, "Analysis registry exceeds the 256-run inspection limit")
    analyses: dict[str, tuple[Path, AnalysisRecord, Snapshot, str | None]] = {}
    for candidate in sorted(paths):
        try:
            path = safe_file(snapshot.folder, candidate.relative_to(snapshot.folder).as_posix())
            record = AnalysisRecord.model_validate_json(path.read_bytes())
            public_id = f"{snapshot.vehicle.id}--{record.run_id}"
            reason = None
            try:
                load_compatible(path, snapshot.identity)
            except (ValueError, OSError, TypeError) as error:
                reason = str(error)
            if public_id in analyses:
                reason = "Duplicate run identity; artifact attachment unavailable"
            analyses[public_id] = (path, record, snapshot, reason)
        except (ValueError, OSError, TypeError):
            # A partial/malformed offline export is unavailable until registration
            # finishes; it must never become a fabricated zero or passing field.
            continue
    return analyses


def create_app(root: Path = ROOT, catalog: tuple[CatalogEntry, ...] = CATALOG) -> FastAPI:
    root = root.resolve()
    app = FastAPI(title="Rocket Twin inspection and bounded experiments", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )
    snapshots: dict[str, Snapshot] = {}
    for entry in catalog:
        snapshot = build_snapshot(entry, root)
        snapshots[snapshot.vehicle.id] = snapshot
    app.state.snapshots = snapshots

    def get_snapshot(vehicle_id: str, meshes: bool = True) -> Snapshot:
        if vehicle_id not in snapshots:
            raise HTTPException(
                404, "Unknown vehicle; only explicit catalog configurations are available"
            )
        snapshot = snapshots[vehicle_id]
        _ensure_current(snapshot, root, meshes=meshes)
        return snapshot

    @app.get("/api/health")
    def health() -> dict[str, Any]:
        return {"status": "ok", "mode": "read-only recorded inspection", "flight_ready": False}

    @app.get("/api/engineering/rp1-connections")
    def rp1_connection_data() -> dict[str, Any]:
        try:
            return rp1_connections.build(root)
        except (OSError, ValueError, KeyError) as exc:
            raise HTTPException(409, "RP1 connection sources unavailable or incompatible") from exc

    @app.get("/api/engineering/rp1-connections/drawings/{drawing_id}")
    def rp1_connection_drawing(drawing_id: str, spec: str, sha256: str) -> Response:
        if drawing_id not in rp1_connections.DRAWING_IDS:
            raise HTTPException(404, "Unknown RP1 drawing")
        if spec != rp1_connections.PINS[rp1_connections.SPEC]:
            raise HTTPException(409, "Incompatible RP1 design revision")
        try:
            path, expected = rp1_connections.asset(root, drawing_id)
            data = path.read_bytes()
            if expected != sha256 or hashlib.sha256(data).hexdigest() != expected:
                raise ValueError("Drawing bytes mismatch")
        except (OSError, ValueError, KeyError) as exc:
            raise HTTPException(409, "RP1 drawing unavailable or incompatible") from exc
        return Response(data, media_type="image/svg+xml", headers={"ETag": expected})

    @app.get("/api/engineering/workbench")
    def engineering_workbench() -> dict[str, Any]:
        from src.api.workbench import build_workbench

        try:
            return build_workbench(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(
                409, f"Engineering walkthrough source unavailable: {error}"
            ) from error

    @app.get("/api/engineering/workbench-extended")
    def engineering_workbench_extended() -> dict[str, Any]:
        from src.api.workbench_extended import build_workbench_extended

        try:
            return build_workbench_extended(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(
                409, f"Engineering extension source unavailable: {error}"
            ) from error

    @app.get("/api/engineering/workbench-a1")
    def engineering_workbench_a1() -> dict[str, Any]:
        from src.api.workbench_a1 import build_workbench_a1

        try:
            return build_workbench_a1(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"A1 connection snapshot unavailable: {error}") from error

    @app.get("/api/engineering/workbench-g80-fixed")
    def engineering_workbench_g80_fixed() -> dict[str, Any]:
        from src.api.workbench_g80_fixed import build_conventional_g80

        try:
            return build_conventional_g80(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"G80-F1 snapshot unavailable: {error}") from error

    @app.get("/api/engineering/workbench-g80-f2")
    def engineering_workbench_g80_f2() -> dict[str, Any]:
        from src.api.workbench_f2 import build_f2

        try:
            return build_f2(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"G80-F2 snapshot unavailable: {error}") from error

    @app.get("/api/engineering/workbench-g80-f2-c1")
    def engineering_workbench_g80_f2_c1() -> dict[str, Any]:
        from src.api.workbench_f2_c1 import build_f2_c1

        try:
            return build_f2_c1(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"F2-C1 study source unavailable: {error}") from error

    @app.get("/api/parts-bank")
    def source_parts_bank() -> dict[str, Any]:
        from src.api import parts_bank

        try:
            return parts_bank.build(root)
        except (OSError, ValueError, KeyError, TypeError) as error:
            raise HTTPException(409, f"Parts-bank source unavailable: {error}") from error

    @app.get("/api/parts-bank/{definition_id}")
    def source_part_definition(definition_id: str) -> dict[str, Any]:
        bank = source_parts_bank()
        item = next((row for row in bank["definitions"] if row["id"] == definition_id), None)
        if item is None:
            raise HTTPException(404, "Unknown source-owned part definition")
        return {
            "identity": bank["identity"],
            "revision_sha256": bank["revision_sha256"],
            "definition": item,
            "instances": [
                row for row in bank["instances"] if row["definition_id"] == definition_id
            ],
        }

    @app.get("/api/vehicles")
    def vehicles() -> dict[str, Any]:
        rows = []
        for snapshot in snapshots.values():
            reason = snapshot.unavailable_reason
            try:
                _ensure_current(snapshot, root)
            except (HTTPException, OSError) as error:
                reason = str(error.detail) if isinstance(error, HTTPException) else str(error)
            rows.append(
                {
                    "id": snapshot.vehicle.id,
                    "label": snapshot.entry.label,
                    "role": snapshot.entry.role,
                    "design_status": snapshot.entry.design_status,
                    "group": snapshot.entry.group,
                    "description": snapshot.entry.description,
                    "available": reason is None,
                    "unavailable_reason": reason,
                    "identity": snapshot.identity.model_dump(),
                }
            )
        try:
            candidate_snapshot.load(root)
            candidate_available = True
            reason = None
        except HTTPException as error:
            candidate_available = False
            reason = error.detail
        try:
            current_definition = rp1_inspection.catalog_entry(root)
        except (OSError, ValueError, KeyError) as error:
            current_definition = {
                "id": rp1_inspection.ID,
                "label": "G80 RP1 / AD1 v2 — source unavailable",
                "available": False,
                "unavailable_reason": str(error),
            }
        return {
            "vehicles": rows,
            "status": STATUS,
            "default_design_id": rp1_inspection.ID,
            "candidates": [
                {
                    "id": candidate_snapshot.ALIAS,
                    "label": "Experimental G80 retention candidate · 72 parts",
                    "role": "candidate",
                    "group": "candidate",
                    "design_status": "Experimental/unadopted — engineering acceptance open",
                    "description": "Archived retention candidate; snapshot inspection only. Active baseline unchanged.",
                    "available": candidate_available,
                    "unavailable_reason": reason,
                },
                current_definition,
            ],
            "candidate_message": "Experimental candidate is separate and unadopted; snapshot inspection only.",
        }

    @app.get("/api/vehicles/{vehicle_id}")
    def vehicle_detail(vehicle_id: str) -> dict[str, Any]:
        if vehicle_id == rp1_inspection.ID:
            try:
                return rp1_inspection_view.build(root)
            except (OSError, ValueError, KeyError) as error:
                raise HTTPException(409, f"Current AD1 source unavailable: {error}") from error
        if vehicle_id == candidate_snapshot.ALIAS:
            _, projection = candidate_snapshot.load(root)
            return cast(dict[str, Any], projection["data"])
        snapshot = get_snapshot(vehicle_id)
        return {
            **snapshot.data,
            "analysis_status": {
                **snapshot.data["analysis_status"],
                "compatible_runs": sum(
                    reason is None for _, _, _, reason in _recorded_analyses(snapshot).values()
                ),
            },
        }

    @app.get("/api/design/{vehicle_id}/inspection-geometry")
    def inspection_geometry_manifest(vehicle_id: str) -> dict[str, Any]:
        if vehicle_id != rp1_inspection.ID:
            raise HTTPException(404, "Unknown source-derived inspection design")
        try:
            return rp1_geometry.build(root)
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"Inspection geometry unavailable: {error}") from error

    @app.get("/api/design/{vehicle_id}/inspection-mesh/{part_id}")
    def source_inspection_mesh(
        vehicle_id: str, part_id: str, spec: str, geometry: str, mesh: str, request: Request
    ) -> Response:
        if vehicle_id != rp1_inspection.ID:
            raise HTTPException(404, "Unknown source-derived inspection design")
        try:
            manifest = rp1_geometry.build(root)
            if (
                spec != manifest["identity"]["specification_sha256"]
                or geometry != manifest["identity"]["inspection_geometry_sha256"]
            ):
                raise ValueError("Inspection source/geometry revision mismatch")
            path, expected = rp1_geometry.asset(root, part_id)
            if mesh != expected:
                raise ValueError("Inspection part mesh revision mismatch")
        except (OSError, ValueError, KeyError) as error:
            raise HTTPException(409, f"Inspection mesh unavailable: {error}") from error
        return _asset_response(path, expected, request, "model/gltf-binary")

    @app.get("/api/vehicles/{vehicle_id}/mass")
    def vehicle_mass(
        vehicle_id: str, burn_fraction: Annotated[float, Query(ge=0, le=1)] = 0
    ) -> dict[str, Any]:
        if vehicle_id == rp1_inspection.ID:
            raise HTTPException(
                409,
                "AD1 has saved estimated mass cases, not a compatible burn-state model. Inspect its recorded cases; no inertia or flight result is substituted.",
            )
        if vehicle_id == candidate_snapshot.ALIAS:
            _, projection = candidate_snapshot.load(root)
            index = round(burn_fraction * 20)
            if abs(index / 20 - burn_fraction) > 1e-8:
                raise HTTPException(422, "Snapshot provides recorded 5% burn increments only")
            return cast(dict[str, Any], projection["mass"][index])
        snapshot = get_snapshot(vehicle_id, meshes=False)
        props = mass_properties(snapshot.vehicle, burn_fraction)
        cp = snapshot.data["summary"]["cp_m"]
        return {
            "vehicle_id": vehicle_id,
            "burn_fraction": burn_fraction,
            "mass_kg": props.mass_kg,
            "cg_m": props.cg_m,
            "cp_m": cp,
            "stability_margin_cal": (cp - props.cg_m)
            / snapshot.vehicle.airframe["body_diameter_m"],
            "inertia_kg_m2": props.inertia_kg_m2.tolist(),
            "budget_kg": props.budget_kg,
            "cg_lateral_m": props.cg_lateral_m,
            "identity": snapshot.identity.model_dump(),
            "growth_allowance_included": False,
            "flight_ready": False,
        }

    @app.get("/api/vehicles/{vehicle_id}/meshes")
    def vehicle_meshes(vehicle_id: str) -> dict[str, Any]:
        if vehicle_id == candidate_snapshot.ALIAS:
            index, projection = candidate_snapshot.load(root)
            return {
                "identity": projection["data"]["identity"],
                "units": "m",
                "viewer_frame": "X=body+y, Y=length-station, Z=body-z",
                "world_placed": True,
                "parts": [
                    {
                        "id": part["id"],
                        "mesh_url": f"/api/vehicles/{candidate_snapshot.ALIAS}/meshes/{part['id']}.glb",
                        "sha256": index["mesh_sha256"][part["id"]],
                    }
                    for part in projection["data"]["parts"]
                ],
            }
        snapshot = get_snapshot(vehicle_id)
        return {
            "identity": snapshot.identity.model_dump(),
            "units": "m",
            "viewer_frame": snapshot.manifest["viewer_frame"] if snapshot.manifest else None,
            "world_placed": True,
            "parts": [
                {
                    "id": part["id"],
                    "mesh_url": part["mesh_url"],
                    "sha256": snapshot.mesh_hashes[part["id"]],
                }
                for part in snapshot.data["parts"]
            ],
        }

    @app.get("/api/vehicles/{vehicle_id}/meshes/{part_id}.glb")
    def vehicle_mesh(vehicle_id: str, part_id: str, request: Request) -> Response:
        if vehicle_id == candidate_snapshot.ALIAS:
            path, expected = candidate_snapshot.mesh(root, part_id)
            return _asset_response(path, expected, request, "model/gltf-binary")
        snapshot = get_snapshot(vehicle_id)
        if part_id not in snapshot.mesh_hashes:
            raise HTTPException(404, "Unknown part mesh")
        try:
            path = safe_file(snapshot.folder, f"parts/{part_id}.glb")
        except (ValueError, OSError) as error:
            raise HTTPException(503, f"Recorded mesh unavailable: {error}") from error
        return _asset_response(path, snapshot.mesh_hashes[part_id], request, "model/gltf-binary")

    @app.get("/api/motors")
    def motors() -> dict[str, Any]:
        rows = {
            s.vehicle.motor.id: s.vehicle.motor.model_dump()
            for s in snapshots.values()
            if s.vehicle.motor
        }
        return {
            "motors": list(rows.values()),
            "status": "Preliminary numerical hypotheses; exact hardware/source/lot approval remains open",
        }

    @app.get("/api/motors/{motor_id}/curve")
    def motor_curve(motor_id: str) -> dict[str, Any]:
        matching = [
            s for s in snapshots.values() if s.vehicle.motor and s.vehicle.motor.id == motor_id
        ]
        if not matching:
            raise HTTPException(404, "Unknown catalog motor")
        snapshot = matching[0]
        _ensure_current(snapshot, root, meshes=False)
        assert snapshot.vehicle.motor and snapshot.vehicle.motor.curve
        path = safe_file(root, snapshot.vehicle.motor.curve)
        curve = load_rasp(path)
        return {
            "id": motor_id,
            "samples": curve.samples.tolist(),
            "columns": ["time_s", "thrust_n"],
            "burn_time_s": curve.burn_time_s,
            "total_impulse_ns": curve.total_impulse_ns,
            "source": snapshot.vehicle.motor.curve,
            "sha256": sha256(path.read_bytes()),
            "provenance": "source curve; preliminary numerical hypothesis",
            "flight_ready": False,
        }

    @app.get("/api/vehicles/{vehicle_id}/analyses")
    def vehicle_analyses(vehicle_id: str) -> dict[str, Any]:
        if vehicle_id == rp1_inspection.ID:
            return {
                "vehicle_id": vehicle_id,
                "analyses": [],
                "status": "No registered field matches AD1 geometry; source calculations remain separate.",
            }
        snapshot = get_snapshot(vehicle_id, meshes=False)
        entries = []
        for public_id, (_, record, owner, reason) in _recorded_analyses(snapshot).items():
            if owner is snapshot:
                entries.append(
                    {
                        "id": public_id,
                        "run_id": record.run_id,
                        "engineering_notice": _analysis_notice(record),
                        "compatible": reason is None,
                        "incompatible_reason": reason,
                        "identity": record.identity.model_dump(),
                        "cases": record.cases,
                        "quantities": sorted({field.quantity for field in record.fields}),
                        "manifest_url": f"/api/analyses/{public_id}",
                    }
                )
        return {
            "vehicle_id": vehicle_id,
            "analyses": entries,
            "status": "Recorded evidence only; engineering acceptance remains open",
        }

    def get_analysis(public_id: str) -> tuple[Path, AnalysisRecord, Snapshot, str | None]:
        vehicle_id, separator, _ = public_id.partition("--")
        if not separator:
            raise HTTPException(404, "Unknown recorded analysis")
        snapshot = get_snapshot(vehicle_id, meshes=False)
        analyses = _recorded_analyses(snapshot)
        if public_id not in analyses:
            raise HTTPException(404, "Unknown recorded analysis")
        return analyses[public_id]

    @app.get("/api/analyses/{run_id}")
    def analysis_manifest(run_id: str) -> dict[str, Any]:
        _, record, _, reason = get_analysis(run_id)
        return {
            **record.model_dump(),
            "api_id": run_id,
            "engineering_notice": _analysis_notice(record),
            "compatible": reason is None,
            "incompatible_reason": reason,
            "artifacts": {
                f.artifact: f"/api/analyses/{run_id}/artifacts/{f.artifact}"
                for f in record.fields
                if f.artifact
            },
        }

    @app.get("/api/analyses/{run_id}/artifacts/{asset:path}")
    def analysis_artifact(run_id: str, asset: str, request: Request) -> Response:
        path, record, snapshot, reason = get_analysis(run_id)
        if reason:
            if record.identity != snapshot.identity or reason.startswith("Duplicate run identity"):
                raise HTTPException(409, f"Incompatible recorded analysis: {reason}")
            raise HTTPException(503, f"Recorded analysis unavailable: {reason}")
        try:
            load_compatible(path, snapshot.identity)
            fields = {field.artifact: field for field in record.fields if field.artifact}
            if asset not in fields:
                raise HTTPException(404, "Unknown allowlisted analysis artifact")
            field = fields[asset]
            artifact = safe_file(path.parent, asset)
            assert field.artifact_sha256 is not None
        except (ValueError, OSError, TypeError) as error:
            raise HTTPException(503, f"Recorded analysis unavailable: {error}") from error
        return _asset_response(artifact, field.artifact_sha256, request, "application/json")

    from src.api.experiments import router

    app.include_router(router)
    return app
