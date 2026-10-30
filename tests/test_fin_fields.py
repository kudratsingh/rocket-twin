"""Synthetic field adapter fixture; this is not rocket validation evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from src.analysis.fin_fields import export_fin_fields
from src.vehicle.schema import load_vehicle


def test_synthetic_single_fin_export_and_consume(tmp_path: Path) -> None:
    """Exercise the raw FEA adapter, SI conversion, mesh IDs, and record consumer."""
    vehicle = load_vehicle("configs/vehicle/platform/performance.yaml")
    fin = next(part for part in vehicle.parts if part.type == "fin_set")
    fea = tmp_path / "synthetic-fea-fixture"
    fea.mkdir()
    mesh = {
        "frame": "FEM X=span from body tangent; Y=chord aft from fin front; Z=plate normal; mm",
        "part_id": fin.id,
        "coverage": "Synthetic test fixture only; not rocket validation.",
        "nodes": [
            {"id": 11, "xyz_mm": [0.0, 0.0, 0.0]},
            {"id": 12, "xyz_mm": [10.0, 0.0, 0.0]},
            {"id": 13, "xyz_mm": [0.0, 10.0, 0.0]},
            {"id": 14, "xyz_mm": [5.0, 0.0, 0.0]},
            {"id": 15, "xyz_mm": [5.0, 5.0, 0.0]},
            {"id": 16, "xyz_mm": [0.0, 5.0, 0.0]},
        ],
        "elements": [{"id": 42, "type": "S6", "nodes": [11, 12, 13, 14, 15, 16]}],
    }
    static_fields = {
        # Deliberately reversed to prove values are matched by the original node IDs.
        "displacements_node_mm": [
            [16, 0.0, 0.0, 0.0],
            [15, 0.0, 0.0, 0.0],
            [14, 0.0, 0.0, 0.0],
            [13, 0.0, 0.0, 0.0],
            [12, 0.3, 0.4, 0.0],
            [11, 0.0, 0.0, 0.0],
        ],
        "stress_integration_point_mpa": [
            [42, 1, 1.25, 0.0, 0.0, 0.0, 0.0, 0.0],
            [42, 2, -3.5, 0.0, 0.0, 0.0, 0.0, 0.0],
        ],
        "stress_components": ["xx", "yy", "zz", "xy", "xz", "yz"],
    }
    mesh_bytes = (json.dumps(mesh) + "\n").encode()
    deck_bytes = b"synthetic CalculiX deck fixture; not rocket validation\n"
    (fea / "case.inp").write_bytes(deck_bytes)
    (fea / "analysis-mesh.json").write_bytes(mesh_bytes)
    (fea / "static-fields.json").write_text(json.dumps(static_fields) + "\n")
    (fea / "mode-fields.json").write_text(json.dumps({"fixture": "synthetic only"}) + "\n")
    (fea / "report.json").write_text(
        json.dumps(
            {
                "solver_executed": True,
                "gmsh": "synthetic fixture",
                "part_id": fin.id,
                "part_shape_sha256": fin.cad_mass.shape_sha256,
                "mesh_sha256": hashlib.sha256(mesh_bytes).hexdigest(),
                "input_sha256": hashlib.sha256(deck_bytes).hexdigest(),
                "nodes": len(mesh["nodes"]),
                "elements": len(mesh["elements"]),
            }
        )
        + "\n"
    )

    record = export_fin_fields(
        vehicle,
        fea,
        tmp_path / "analysis-export",
        "synthetic-fin-fields-1",
        {"fixtures/synthetic-fin-fea": "a" * 64},
    )
    assert record.identity.configuration_id == vehicle.id
    assert all(field.evidence.validation == "unvalidated" for field in record.fields)
    assert all(field.evidence.known_case_verified is False for field in record.fields)
    assert all(field.evidence.mesh_converged is False for field in record.fields)
    assert all(field.part_ids == [fin.id] for field in record.fields)
    assert all(
        field.sample_count == (6 if field.association == "node" else 1) for field in record.fields
    )
    assert record.cases["single-fin-static"]["source_report"]["part_shape_sha256"] == (
        fin.cad_mass.shape_sha256
    )
    assert "fea/case.inp" in record.input_sha256
    assert "fea/analysis-mesh.json" in record.input_sha256

    displacement = next(field for field in record.fields if field.quantity == "displacement")
    stress = next(field for field in record.fields if field.quantity == "stress")
    displacement_data = json.loads(
        (tmp_path / "analysis-export" / displacement.artifact).read_text()
    )
    stress_data = json.loads((tmp_path / "analysis-export" / stress.artifact).read_text())
    assert displacement_data["analysis_mesh"]["nodes"][1]["id"] == 12
    assert displacement_data["values"][0][1] == 0.0005
    assert stress_data["analysis_mesh"]["elements"][0]["id"] == 42
    assert stress_data["values"][0] == [3_500_000.0]
    assert "not an orthotropic failure criterion" in stress.component
    assert "margin" not in stress.model_dump()
    assert len(displacement.mesh_sha256) == 64

    stale_report = json.loads((fea / "report.json").read_text())
    stale_report["part_shape_sha256"] = "0" * 64
    (fea / "report.json").write_text(json.dumps(stale_report) + "\n")
    with pytest.raises(ValueError, match="geometry identity"):
        export_fin_fields(
            vehicle,
            fea,
            tmp_path / "stale-analysis-export",
            "synthetic-fin-fields-1",
            {"fixtures/synthetic-fin-fea": "a" * 64},
        )
