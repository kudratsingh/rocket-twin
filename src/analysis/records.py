"""Versioned engineering-field export and identity-checked backend consumption.

A field's provenance is independent of validation. Part-level results remain
part-level; measured points never become an entire measured surface. Scalar fields
are stored in SI on an explicit analysis mesh or on named parts. Display mappings
must be generated offline and recorded; this module never fabricates spatial data.
References: ADR-0007 and docs/UI.md Analysis contract. No engineering solver here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path, PurePosixPath
from typing import Annotated, Any, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Identifier = Annotated[str, Field(pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$")]
Provenance = Literal["calculated", "estimated", "measured", "unavailable"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Identity(Record):
    configuration_id: Identifier
    resolved_spec_sha256: Sha256
    cad_revision_sha256: Sha256
    part_shape_sha256: dict[Identifier, Sha256]


class Evidence(Record):
    provenance: Provenance
    validation: Literal[
        "unvalidated", "numerically_verified", "physically_validated", "failed", "unavailable"
    ]
    assumptions: list[str]
    limits: list[str]
    sources: list[str]
    uncertainty: str
    required_physical_tests: list[str]
    known_case_verified: bool = False
    mesh_converged: bool = False
    report: str | None = None


class FieldRecord(Record):
    id: Identifier
    case_id: Identifier
    quantity: Literal["stress", "displacement", "temperature", "design_margin"]
    component: str
    units: Literal["Pa", "m", "K", "1"]
    association: Literal["part", "node", "element", "integration_point", "measured_point"]
    part_ids: list[Identifier] = Field(min_length=1)
    evidence: Evidence
    # Static fields have no time axis; transient samples are exact solver times.
    times_s: list[float] | None = None
    artifact: str | None = None
    artifact_sha256: Sha256 | None = None
    sample_count: int = Field(ge=0)
    unavailable_reason: str | None = None
    mesh_sha256: Sha256 | None = None
    registration: dict[str, Any] | None = None
    reported_extrema: dict[str, Any] = Field(default_factory=dict)
    margin_definition: str | None = None
    coverage_notes: str

    @model_validator(mode="after")
    def consistency(self) -> Self:
        expected = {"stress": "Pa", "displacement": "m", "temperature": "K", "design_margin": "1"}
        if self.units != expected[self.quantity]:
            raise ValueError("field units must be SI and agree with quantity")
        if self.times_s is not None and (
            not self.times_s or any(a >= b for a, b in zip(self.times_s, self.times_s[1:]))
        ):
            raise ValueError("transient times must be nonempty and strictly increasing")
        if self.evidence.provenance == "unavailable":
            if self.evidence.validation != "unavailable":
                raise ValueError("unavailable data cannot have a validated result")
            if not self.unavailable_reason or self.artifact or self.sample_count:
                raise ValueError("unavailable fields require a reason and no fabricated samples")
        else:
            if not self.artifact or not self.artifact_sha256 or self.sample_count == 0:
                raise ValueError("available fields require a hashed data artifact and samples")
            asset_path(self.artifact)
            if self.association != "part" and (not self.mesh_sha256 or not self.registration):
                raise ValueError("spatial fields require analysis mesh identity and registration")
        if self.association == "part" and self.sample_count not in (0, len(self.part_ids)):
            raise ValueError("part field must have one sample per declared part")
        if self.quantity == "design_margin" and not self.margin_definition:
            raise ValueError("design margin requires its criterion/formula and threshold")
        if self.evidence.provenance == "measured" and self.association != "measured_point":
            raise ValueError("measured fields require located point coverage")
        return self


class AnalysisRecord(Record):
    schema_version: Literal["rocket-twin.analysis.v1"] = "rocket-twin.analysis.v1"
    run_id: Identifier
    identity: Identity
    coordinate_frame: Literal["CAD_mm_registered_to_viewer_m"] = "CAD_mm_registered_to_viewer_m"
    cases: dict[Identifier, dict[str, Any]]
    fields: list[FieldRecord]
    tools: dict[str, str]
    input_sha256: dict[str, Sha256]
    flight_ready: Literal[False] = False

    @model_validator(mode="after")
    def references(self) -> Self:
        if len({f.id for f in self.fields}) != len(self.fields):
            raise ValueError("duplicate field IDs")
        for f in self.fields:
            if (
                f.case_id not in self.cases
                or not set(f.part_ids) <= self.identity.part_shape_sha256.keys()
            ):
                raise ValueError("field refers to unknown case or part geometry")
        return self


def asset_path(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "\\" in value or not path.parts:
        raise ValueError("analysis assets must be relative allowlisted paths")
    return path


def check_field_payload(field: FieldRecord, payload: Any) -> None:
    """Check scalar sample shape and bind spatial data to its embedded mesh."""
    if not isinstance(payload, dict) or not isinstance(payload.get("values"), list):
        raise TypeError("field payload requires frame/sample values")
    frames = payload["values"]
    if len(frames) != (len(field.times_s) if field.times_s is not None else 1) or any(
        not isinstance(frame, list) or len(frame) != field.sample_count for frame in frames
    ):
        raise ValueError("field frame/sample shape disagrees with metadata")
    for frame in frames:
        for value in frame:
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, (int, float))
            ):
                raise ValueError("scalar field samples must be numeric or null coverage")
    if field.association != "part":
        if "analysis_mesh" not in payload:
            raise ValueError("spatial field requires its embedded analysis mesh")
        mesh = (
            json.dumps(payload["analysis_mesh"], allow_nan=False, sort_keys=True).encode() + b"\n"
        )
        if hashlib.sha256(mesh).hexdigest() != field.mesh_sha256:
            raise ValueError("analysis mesh checksum mismatch")
    # Reject nonfinite samples and coordinates, including permissive JSON readers.
    json.dumps(payload, allow_nan=False)


def export_record(folder: Path, record: AnalysisRecord, assets: dict[str, Any]) -> Path:
    """Write exact offline samples; arrays are frames x samples, with null coverage."""
    folder.mkdir(parents=True, exist_ok=True)
    for field in record.fields:
        if field.artifact is None:
            continue
        if field.artifact not in assets:
            raise ValueError("missing analysis asset")
        payload = assets[field.artifact]
        check_field_payload(field, payload)
        encoded = json.dumps(payload, allow_nan=False, sort_keys=True).encode() + b"\n"
        if hashlib.sha256(encoded).hexdigest() != field.artifact_sha256:
            raise ValueError("field artifact hash disagrees with metadata")
        path = folder.joinpath(*asset_path(field.artifact).parts)
        if not path.resolve().is_relative_to(folder.resolve()):
            raise ValueError("analysis artifact escapes run directory")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(encoded)
    manifest = folder / "manifest.json"
    manifest.write_text(record.model_dump_json(indent=2) + "\n")
    return manifest


def load_compatible(manifest: Path, expected: Identity) -> AnalysisRecord:
    """Backend boundary: stale identity, path escape and corrupt assets fail closed."""
    record = AnalysisRecord.model_validate_json(manifest.read_bytes())
    if record.identity != expected:
        raise ValueError("analysis configuration/CAD identity mismatch")
    for field in record.fields:
        if field.artifact:
            path = manifest.parent.joinpath(*asset_path(field.artifact).parts).resolve()
            if not path.is_relative_to(manifest.parent.resolve()):
                raise ValueError("analysis artifact escapes run directory")
            if hashlib.sha256(path.read_bytes()).hexdigest() != field.artifact_sha256:
                raise ValueError("analysis artifact checksum mismatch")
            check_field_payload(field, json.loads(path.read_bytes()))
    return record
