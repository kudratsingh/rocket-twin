"""Small synthetic provenance/gate checks; no actual geometry or thermal solve."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from scripts import wo03_actual_transient as transient
from scripts import wo03_export_actual_debug as debug_export
from src.analysis.records import AnalysisRecord, load_compatible
from src.vehicle.cad_contract import digest
from src.vehicle.schema import Part, Vehicle


def _json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def guarded_factor(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Only the early guard inputs exist; reaching any backend is a test failure."""
    monkeypatch.setattr(transient, "ROOT", tmp_path)

    def forbidden_backend(*_args, **_kwargs):
        pytest.fail("A blocked source reached the cached-operator or thermal backend")

    monkeypatch.setattr(transient.RecordedGasResponse, "load", forbidden_backend)
    monkeypatch.setattr(transient, "run_thermal_topology", forbidden_backend)
    keys = [
        "factor_record",
        "gas_operator",
        "gas_metadata",
        "parent_map",
        "candidate",
        "candidate_record",
        "surface_groups",
        "acceptance_matrix",
        "engineering",
        "topology",
        "construction",
        "radiosity_record",
    ]
    cfg = {key: f"source/{key}.json" for key in keys}
    config = tmp_path / "transient.yaml"
    config.write_text(yaml.safe_dump(cfg))
    record = {
        "inputs_unchanged": True,
        "numerical_checks_pass": False,
        "native_successful_factor_available": True,
    }

    def invoke(*, debug=False):
        _json(tmp_path / cfg["factor_record"], record)
        return transient.worker(
            config, tmp_path / "no-output", SimpleNamespace(investigate_failed_operator=debug)
        )

    return record, cfg, invoke


def test_ordinary_transient_blocks_complete_but_failed_factor(guarded_factor):
    record, _, invoke = guarded_factor
    assert record["native_successful_factor_available"] is True
    with pytest.raises(ValueError, match="field checks failed; ordinary transient.*blocked"):
        invoke()


@pytest.mark.parametrize("numerical_pass", [False, True])
def test_debug_permission_never_accepts_incomplete_operator(guarded_factor, numerical_pass):
    record, _, invoke = guarded_factor
    record.update(native_successful_factor_available=False, numerical_checks_pass=numerical_pass)
    with pytest.raises(ValueError, match="complete actual response operator is unavailable"):
        invoke(debug=True)


def test_debug_permission_never_bypasses_source_identity_check(guarded_factor):
    record, _, invoke = guarded_factor
    record["inputs_unchanged"] = False
    with pytest.raises(ValueError, match="input-identity verification is not complete"):
        invoke(debug=True)


@pytest.mark.parametrize("changed", ["gas_operator", "gas_metadata"])
@pytest.mark.parametrize("debug", [False, True])
def test_changed_cache_cannot_borrow_a_complete_checked_record(
    guarded_factor, tmp_path: Path, changed: str, debug: bool
):
    record, cfg, invoke = guarded_factor
    record["numerical_checks_pass"] = not debug
    for key in ("gas_operator", "gas_metadata"):
        path = tmp_path / cfg[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"synthetic cache bytes; loading is forbidden in this guard test")
    record["artifacts"] = [
        {"path": cfg[key], "sha256": _sha(tmp_path / cfg[key])}
        for key in ("gas_operator", "gas_metadata")
    ]
    with (tmp_path / cfg[changed]).open("ab") as target:
        target.write(b" tampered after the source record was checked")
    with pytest.raises(ValueError, match="not the exact artifact in the checked source record"):
        invoke(debug=debug)


def _synthetic_vehicle() -> Vehicle:
    """Schema-valid toy records with supplied properties; no CAD generator call."""
    names = [
        "nose",
        "motor_mount",
        "aft_shell",
        "fitting_baffle_1_front",
        "fitting_baffle_1_front_foil_bond",
        "unmodeled_component",
    ]
    parts = []
    for i, name in enumerate(names):
        nose = i == 0
        part = Part.model_validate(
            {
                "id": name,
                "type": "nose_cone" if nose else "commercial",
                "parent": None if nose else "nose",
                "position_m": 0 if nose else 0.1 + i * 0.01,
                "geometry": (
                    {"length_m": 0.1, "radius_m": 0.01, "shape": "conical"}
                    if nose
                    else {"bbox_m": [0.01, 0.01, 0.01]}
                ),
                "mass_kg": 0.001,
                "cg_offset_m": 0.05 if nose else 0.005,
                "estimate": True,
                "learn": "Synthetic gate fixture only; no physical hardware or geometry is represented.",
                "cad": {
                    "generator": "synthetic_gate_fixture",
                    "mass_basis": "supplied_or_estimated",
                    "role": "purchased_envelope",
                    "notes": "Synthetic supplied properties; CAD is never generated.",
                },
            }
        )
        data = part.model_dump(by_alias=True)
        data["cad_mass"] = {
            "shape_sha256": digest(part.geometry, part.cad.model_dump()),
            "volume_m3": 1e-6,
            "cg_local_body_m": [-part.cg_offset_m, 0, 0],
            "inertia_per_kg_m2": [[1e-4, 0, 0], [0, 1e-4, 0], [0, 0, 1e-4]],
            "basis": "Synthetic gate fixture supplied mass properties, not CAD evidence",
        }
        parts.append(data)
    return Vehicle.model_validate(
        {
            "id": "synthetic-gate-vehicle",
            "name": "Synthetic gate vehicle",
            "class": "digital_only",
            "scale": "full",
            "axis": {"body_x": "nose", "body_z": "down", "world": "ECI"},
            "airframe": {
                "length_m": 0.5,
                "body_diameter_m": 0.02,
                "nose": {"length_m": 0.1, "shape": "conical"},
                "material_default": "commercial",
            },
            "aero": {
                "passive_stubs": {
                    "enabled": False,
                    "span_m": 0.01,
                    "count": 3,
                    "root_chord_m": 0.01,
                    "tip_chord_m": 0.01,
                    "sweep_m": 0,
                    "position_m": 0.2,
                },
                "cd_model": {
                    "estimate": True,
                    "type": "empirical_mach_table",
                    "reference": "Synthetic fixture",
                    "mach": [0, 0.8],
                    "cd": [0.4, 0.4],
                    "base_drag_cd": 0,
                },
            },
            "parts": parts,
        }
    )


@pytest.fixture
def debug_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(debug_export, "ROOT", tmp_path)
    vehicle = _synthetic_vehicle()
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    folder = tmp_path / "synthetic-debug-run"
    key = "fixtures/resolved-candidate.json"
    candidate = folder / "source-snapshot" / key
    candidate.parent.mkdir(parents=True)
    candidate.write_text(vehicle.model_dump_json(by_alias=True))
    ids = ["motor_mount", "aft_shell", "fitting_baffle_1_front", "fitting_baffle_1_front_foil_bond"]
    result = {
        "part_ids": ids,
        "times_s": [0.0, 1.0],
        "temperature_k": [[300.0] * 4, [301.0, 302.0, 303.0, 304.0]],
        "peaks": [
            {"part_id": name, "peak_c": 27.85 + i, "peak_time_s": 1.0} for i, name in enumerate(ids)
        ],
        "prescribed_case_peak_c": 137.0,
        "ambient_c": 22.0,
    }
    output = folder / "thermal-results.json"
    _json(output, result)
    record = {
        "run_id": "synthetic-debug-run",
        "mode": "INVESTIGATION_OF_FAILED_GAS_OPERATOR",
        "inputs_unchanged": True,
        "candidate_identity": identity,
        "cad_revision_sha256": "b" * 64,
        "input_sha256": {key: _sha(candidate)},
        "output": output.name,
        "output_sha256": _sha(output),
        "case": {"id": "synthetic-source-case", "outer_foil_emissivity": 0.41},
        "material_corner": "nominal",
        "opening_radiative_brightness": "case",
        # Adversarial promotion claims must never override explicit debug evidence.
        "temperature_prediction_credible": True,
        "temperature_acceptance": "passed",
        "source_gas_numerical_checks_pass": True,
    }
    path = folder / "record.json"

    def invoke():
        _json(path, record)
        monkeypatch.setattr(sys, "argv", [str(debug_export.__file__), str(path)])
        return debug_export.main()

    return record, result, path, candidate, output, invoke


def test_debug_export_preserves_failed_validation_and_recorded_provenance(debug_record):
    run, result, path, _, _, invoke = debug_record
    assert invoke() == 0
    manifest = path.parent / "analysis-debug/manifest.json"
    record = AnalysisRecord.model_validate_json(manifest.read_bytes())
    assert load_compatible(manifest, record.identity) == record
    assert record.identity.resolved_spec_sha256 == run["candidate_identity"]
    assert set(record.cases) == {"synthetic-source-case"}
    case = record.cases["synthetic-source-case"]
    assert case["credible_prediction"] is False
    assert case["gas_source_field_checks_pass"] is False
    assert case["temperature_acceptance"] == "unavailable_due_to_failed_source_numerics"
    available = [f for f in record.fields if f.artifact]
    assert len(available) == 1 and available[0].evidence.validation == "failed"
    assert available[0].evidence.mesh_converged is False
    assumptions = " ".join(available[0].evidence.assumptions)
    assert run["candidate_identity"] in assumptions
    for text in ("synthetic-source-case", "137.0", "22.0", "0.41", "brightness: case"):
        assert text in assumptions
    data = json.loads((manifest.parent / available[0].artifact).read_text())
    assert data["values"] == result["temperature_k"]
    unavailable = [f for f in record.fields if not f.artifact]
    assert len(unavailable) == 1
    assert unavailable[0].evidence.validation == "unavailable"
    assert set(unavailable[0].part_ids) == {"nose", "unmodeled_component"}
    assert unavailable[0].sample_count == 0
    exported = json.loads((path.parent / "debug-export-record.json").read_text())
    assert exported["validation"] == "failed"
    for flag in (
        "temperature_prediction_credible",
        "thermal_acceptance",
        "flight_ready",
        "registration_on_active_vehicle",
    ):
        assert exported[flag] is False


@pytest.mark.parametrize("tamper", ["output", "snapshot", "identity"])
def test_debug_export_rejects_tampered_output_or_vehicle(debug_record, tamper):
    record, _, path, candidate, output, invoke = debug_record
    if tamper == "identity":
        record["candidate_identity"] = "a" * 64
        message = "Candidate identity mismatch"
    else:
        target = output if tamper == "output" else candidate
        with target.open("ab") as stream:
            stream.write(b" ")
        message = "transient output changed" if tamper == "output" else "vehicle snapshot changed"
    with pytest.raises(ValueError, match=message):
        invoke()
    assert not (path.parent / "analysis-debug").exists()


@pytest.mark.parametrize("claim", ["wrong_mode", "changed_inputs"])
def test_export_requires_explicit_unchanged_failed_investigation(debug_record, claim):
    record, _, _, _, _, invoke = debug_record
    if claim == "wrong_mode":
        record["mode"] = "PROVISIONAL_COARSE_DIAGNOSTIC"
    else:
        record["inputs_unchanged"] = False
    with pytest.raises(ValueError, match="unchanged, explicitly failed-operator investigation"):
        invoke()
