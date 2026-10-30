"""Backend consumes recorded fields honestly and refuses stale/corrupt overlays."""

import hashlib
import json
from pathlib import Path

import pytest

from src.analysis.records import AnalysisRecord, export_record, load_compatible


def test_transient_export_identity_and_missing_coverage(tmp_path: Path) -> None:
    payload = {
        "values": [[293.15, None], [315.0, None]],
        "notes": "Uniform part model; second part unmodeled.",
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode() + b"\n").hexdigest()
    evidence = {
        "provenance": "calculated",
        "validation": "unvalidated",
        "assumptions": ["Synthetic exporter fixture, not rocket thermal evidence."],
        "limits": ["Fixture only."],
        "sources": ["test fixture"],
        "uncertainty": "Not an engineering result.",
        "required_physical_tests": [],
    }
    record = AnalysisRecord.model_validate(
        {
            "run_id": "fixture-1",
            "identity": {
                "configuration_id": "fixture-rocket",
                "resolved_spec_sha256": "a" * 64,
                "cad_revision_sha256": "b" * 64,
                "part_shape_sha256": {"liner": "c" * 64, "servo": "d" * 64},
            },
            "cases": {"heat": {"boundary": "synthetic"}},
            "fields": [
                {
                    "id": "temperature",
                    "case_id": "heat",
                    "quantity": "temperature",
                    "component": "part mean",
                    "units": "K",
                    "association": "part",
                    "part_ids": ["liner", "servo"],
                    "evidence": evidence,
                    "times_s": [0, 10],
                    "artifact": "fields/temperature.json",
                    "artifact_sha256": digest,
                    "sample_count": 2,
                    "coverage_notes": "Null is unavailable, not zero.",
                }
            ],
            "tools": {"fixture": "1"},
            "input_sha256": {},
        }
    )
    manifest = export_record(tmp_path, record, {"fields/temperature.json": payload})
    assert load_compatible(manifest, record.identity) == record
    other = record.identity.model_copy(update={"cad_revision_sha256": "e" * 64})
    with pytest.raises(ValueError, match="identity mismatch"):
        load_compatible(manifest, other)
    (tmp_path / "fields/temperature.json").write_text("{}")
    with pytest.raises(ValueError, match="checksum"):
        load_compatible(manifest, record.identity)


def test_unavailable_cannot_become_a_green_zero_or_path_escape(tmp_path: Path) -> None:
    from pydantic import ValidationError

    from src.analysis.records import FieldRecord, asset_path

    evidence = {
        "provenance": "unavailable",
        "validation": "unavailable",
        "assumptions": [],
        "limits": [],
        "sources": [],
        "uncertainty": "No solver result.",
        "required_physical_tests": [],
    }
    base = {
        "id": "stress",
        "case_id": "thrust",
        "quantity": "stress",
        "component": "axial",
        "units": "Pa",
        "association": "part",
        "part_ids": ["cradle"],
        "evidence": evidence,
        "sample_count": 0,
        "coverage_notes": "Not analyzed.",
        "unavailable_reason": "Solver not run.",
    }
    assert FieldRecord.model_validate(base).artifact is None
    with pytest.raises(ValidationError):
        FieldRecord.model_validate({**base, "sample_count": 1})
    with pytest.raises(ValueError, match="relative"):
        asset_path("../secrets")
