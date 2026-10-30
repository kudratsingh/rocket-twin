"""Adapt executed single-fin CalculiX screen files to the Analysis field contract.

This module exports solver results only. It does not calculate structural physics,
failure criteria, design margins, or a hardware pass/fail decision.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
from typing import Any

from src.analysis.records import AnalysisRecord, Identity, export_record, load_compatible
from src.vehicle.schema import Vehicle

RAW_FILES = (
    "case.inp",
    "analysis-mesh.json",
    "static-fields.json",
    "mode-fields.json",
    "report.json",
)


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, allow_nan=False, sort_keys=True).encode() + b"\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _read_json(folder: Path, filename: str) -> dict[str, Any]:
    path = folder / filename
    if not path.is_file():
        raise FileNotFoundError(f"Required fin FEA source file missing: {filename}")
    if not path.resolve().is_relative_to(folder.resolve()):
        raise ValueError(f"Fin FEA source path escapes its input folder: {filename}")
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"Expected JSON object in {filename}")
    return value


def _validate_input_hashes(input_sha256: dict[str, str]) -> dict[str, str]:
    checked: dict[str, str] = {}
    for name, digest in input_sha256.items():
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or not path.parts:
            raise ValueError("input hash paths must be relative and traversal-free")
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"input hash is not lowercase SHA-256: {name}")
        checked[name] = digest
    return checked


def _cad_revision_sha256() -> str:
    cad_root = Path(__file__).resolve().parents[1] / "cad"
    return _sha256_bytes(b"".join(path.read_bytes() for path in sorted(cad_root.glob("*.py"))))


def _vehicle_identity(vehicle: Vehicle) -> Identity:
    fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    if fin is None or fin.cad_mass is None:
        raise ValueError("Vehicle requires a fin_set with CAD mass identity")
    return Identity(
        configuration_id=vehicle.id,
        resolved_spec_sha256=_sha256_bytes(vehicle.model_dump_json(by_alias=True).encode()),
        cad_revision_sha256=_cad_revision_sha256(),
        part_shape_sha256={
            part.id: part.cad_mass.shape_sha256
            for part in vehicle.parts
            if part.cad_mass is not None
        },
    )


def _registration(vehicle: Vehicle, fin: Any) -> dict[str, Any]:
    return {
        "type": "affine_4x4",
        "source_frame": "FEM X=span from body tangent; Y=chord aft from fin front; Z=plate normal; mm",
        "target_frame": "CAD_mm_registered_to_viewer_m",
        "matrix": [
            [0.001, 0.0, 0.0, fin.geometry["radius_m"]],
            [0.0, -0.001, 0.0, vehicle.airframe["length_m"] - fin.position_m],
            [0.0, 0.0, -0.001, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ],
    }


def _node_values(mesh: dict[str, Any], static_fields: dict[str, Any]) -> list[float]:
    nodes = mesh.get("nodes")
    rows = static_fields.get("displacements_node_mm")
    if not isinstance(nodes, list) or not isinstance(rows, list):
        raise TypeError("Mesh nodes or nodal displacement rows are missing")
    magnitudes: dict[int, float] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError("Nodal displacement rows must be [node_id, ux, uy, uz]")
        node_id = int(row[0])
        if node_id in magnitudes:
            raise ValueError(f"Duplicate displacement row for node {node_id}")
        ux, uy, uz = (float(value) for value in row[1:])
        magnitudes[node_id] = math.sqrt(ux * ux + uy * uy + uz * uz) * 1e-3
    ordered: list[float] = []
    for node in nodes:
        node_id = int(node["id"])
        if node_id not in magnitudes:
            raise ValueError(f"Missing displacement for mesh node {node_id}")
        ordered.append(magnitudes[node_id])
    if len(ordered) != len(magnitudes):
        raise ValueError("Displacement data includes node IDs absent from analysis mesh")
    return ordered


def _element_xx_values(mesh: dict[str, Any], static_fields: dict[str, Any]) -> list[float]:
    elements = mesh.get("elements")
    rows = static_fields.get("stress_integration_point_mpa")
    if not isinstance(elements, list) or not isinstance(rows, list):
        raise TypeError("Mesh elements or integration-point stress rows are missing")
    maxima: dict[int, float] = {}
    for row in rows:
        if not isinstance(row, list) or len(row) != 8:
            raise ValueError("Stress rows must be [element_id, ip, xx, yy, zz, xy, xz, yz]")
        element_id = int(row[0])
        xx_pa = abs(float(row[2])) * 1e6
        maxima[element_id] = max(maxima.get(element_id, 0.0), xx_pa)
    ordered: list[float] = []
    for element in elements:
        element_id = int(element["id"])
        if element_id not in maxima:
            raise ValueError(f"Missing integration-point stress for mesh element {element_id}")
        ordered.append(maxima[element_id])
    if len(ordered) != len(maxima):
        raise ValueError("Stress data includes element IDs absent from analysis mesh")
    return ordered


def export_fin_fields(
    vehicle: Vehicle,
    fea_folder: Path,
    output_folder: Path,
    run_id: str,
    input_sha256: dict[str, str],
    *,
    known_case_verified: bool = False,
    mesh_converged: bool = False,
) -> AnalysisRecord:
    """Export one-fin displacement/stress diagnostics and consume by exact identity.

    Only the four named raw files are read or hashed from ``fea_folder``. Field
    assets embed the original S6 analysis mesh and preserve its solver node/element
    IDs. The returned record has passed the existing backend identity/hash check.
    """
    fea_folder = fea_folder.resolve()
    output_folder = output_folder.resolve()
    for filename in RAW_FILES:
        source = fea_folder / filename
        if not source.is_file():
            raise FileNotFoundError(f"Required fin FEA source file missing: {filename}")
        if not source.resolve().is_relative_to(fea_folder):
            raise ValueError(f"Fin FEA source path escapes its input folder: {filename}")
    mesh = _read_json(fea_folder, "analysis-mesh.json")
    static_fields = _read_json(fea_folder, "static-fields.json")
    _read_json(fea_folder, "mode-fields.json")
    report = _read_json(fea_folder, "report.json")
    if report.get("solver_executed") is not True:
        raise ValueError("Fin FEA export requires an executed CalculiX result")
    fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    if fin is None or fin.cad_mass is None:
        raise ValueError("Vehicle requires a fin_set with CAD mass identity")
    if mesh.get("part_id") != fin.id:
        raise ValueError("Analysis mesh part ID does not match the resolved vehicle fin_set")
    if report.get("part_id") != fin.id:
        raise ValueError("Fin FEA report part ID does not match the resolved vehicle fin_set")
    if report.get("part_shape_sha256") != fin.cad_mass.shape_sha256:
        raise ValueError("Fin FEA geometry identity does not match the current CAD fin_set")
    raw_mesh_sha256 = _sha256_bytes((fea_folder / "analysis-mesh.json").read_bytes())
    if report.get("mesh_sha256") != raw_mesh_sha256:
        raise ValueError("Fin FEA report mesh hash does not match its raw analysis mesh")
    deck_sha256 = _sha256_bytes((fea_folder / "case.inp").read_bytes())
    if report.get("input_sha256") != deck_sha256:
        raise ValueError("Fin FEA report input hash does not match its CalculiX input deck")
    nodes = mesh.get("nodes")
    elements = mesh.get("elements")
    if not isinstance(nodes, list) or not nodes or not isinstance(elements, list) or not elements:
        raise ValueError("Analysis mesh requires nonempty node and element arrays")
    if any(element.get("type") != "S6" for element in elements):
        raise ValueError("Expected original CalculiX S6 shell elements")
    if report.get("nodes") != len(nodes) or report.get("elements") != len(elements):
        raise ValueError("Fin FEA report node/element counts do not match its analysis mesh")
    stress_components = static_fields.get("stress_components")
    if stress_components != ["xx", "yy", "zz", "xy", "xz", "yz"]:
        raise ValueError("Stress component ordering is missing or incompatible with CalculiX rows")

    node_values = _node_values(mesh, static_fields)
    stress_values = _element_xx_values(mesh, static_fields)
    mesh_sha256 = _sha256_bytes(_canonical_bytes(mesh))
    registration = _registration(vehicle, fin)
    fields: list[dict[str, Any]] = []
    assets: dict[str, Any] = {}
    field_specs = [
        (
            "fin-displacement-magnitude",
            "displacement",
            "displacement magnitude at S6 mesh nodes",
            "m",
            "node",
            node_values,
            "Node displacement magnitude is a solver result on the explicit shell midsurface mesh.",
        ),
        (
            "fin-spanwise-normal-stress-xx",
            "stress",
            "maximum absolute spanwise normal stress xx over each element's integration points; component diagnostic, not an orthotropic failure criterion",
            "Pa",
            "element",
            stress_values,
            "One scalar per S6 element: maximum absolute xx component across that element's integration points.",
        ),
    ]
    for field_id, quantity, component, units, association, values, coverage in field_specs:
        artifact = f"fields/{field_id}.json"
        payload = {"analysis_mesh": mesh, "values": [values]}
        encoded = _canonical_bytes(payload)
        assets[artifact] = payload
        fields.append(
            {
                "id": field_id,
                "case_id": "single-fin-static",
                "quantity": quantity,
                "component": component,
                "units": units,
                "association": association,
                "part_ids": [fin.id],
                "evidence": {
                    "provenance": "calculated",
                    "validation": (
                        "numerically_verified"
                        if known_case_verified and mesh_converged
                        else "unvalidated"
                    ),
                    "assumptions": [
                        "Ideal root clamp and tab restraint are model boundary conditions, not a qualified bond or joint.",
                        "Estimated material properties use an isotropic weak-direction surrogate for this screen.",
                        "Mesh refinement is a separate numerical convergence check and does not establish physical validation.",
                        "Numerical verification flags do not establish physical material, joint, or hardware validation.",
                    ],
                    "limits": [
                        "One fin instance only; no copying of the result to the other fins.",
                        "S6 shell midsurface values; shell normals and physical faces are not direct CAD vertices.",
                        "Stress xx is a component diagnostic only; no orthotropic failure criterion, margin, or safety pass is calculated.",
                    ],
                    "sources": ["CalculiX fin screen", "Resolved vehicle fin_set specification"],
                    "uncertainty": "Estimated material and idealized root boundary; mesh convergence status is recorded separately from physical validity.",
                    "required_physical_tests": [
                        "Hot material and root-joint coupons",
                        "Root attachment proof test",
                        "Assembled modal and vibration tests",
                    ],
                    "known_case_verified": known_case_verified,
                    "mesh_converged": mesh_converged,
                    "report": "embedded in single-fin-static case metadata",
                },
                "artifact": artifact,
                "artifact_sha256": _sha256_bytes(encoded),
                "sample_count": len(values),
                "mesh_sha256": mesh_sha256,
                "registration": registration,
                "reported_extrema": {"maximum": max(values), "minimum": min(values)},
                "coverage_notes": coverage,
            }
        )

    raw_hashes = {
        f"fea/{filename}": _sha256_bytes((fea_folder / filename).read_bytes())
        for filename in RAW_FILES
    }
    merged_hashes = {**_validate_input_hashes(input_sha256), **raw_hashes}
    identity = _vehicle_identity(vehicle)
    record = AnalysisRecord.model_validate(
        {
            "run_id": run_id,
            "identity": identity.model_dump(),
            "cases": {
                "single-fin-static": {
                    "kind": "static_structural_shell",
                    "solver": "CalculiX",
                    "boundary": "Ideal clamp at the fin root/tab; one S6 shell midsurface instance.",
                    "field_resolution": "node displacement and element integration-point component maximum",
                    "source_report": report,
                }
            },
            "fields": fields,
            "tools": {
                "mesh_format": "Gmsh S6",
                "mesh_tool_version": str(report.get("gmsh", "recorded in report.json")),
                "solver": "CalculiX executed; version not inferred if absent from report",
            },
            "input_sha256": merged_hashes,
        }
    )
    manifest = export_record(output_folder, record, assets)
    return load_compatible(manifest, identity)
