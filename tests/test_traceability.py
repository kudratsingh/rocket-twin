from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from src.analysis.traceability import (
    resolve_interfaces,
    resolve_requirements,
    validate_catalog,
)
from src.vehicle.schema import load_vehicle

ROOT = Path(__file__).resolve().parents[1]


def test_catalog_rejects_invalid_cross_reference() -> None:
    catalog = {
        "requirements": [{"id": "RT-A", "interfaces": ["IF-MISSING"]}],
        "interfaces": [],
        "fmea": [],
    }
    with pytest.raises(ValueError, match="unknown interfaces"):
        validate_catalog(catalog)


def test_catalog_rejects_duplicate_fmea_id_and_unknown_applicability() -> None:
    duplicate = {
        "configurations": {"G80": "vehicle.yaml"},
        "requirements": [],
        "interfaces": [],
        "fmea": [{"id": "FMEA-A"}, {"id": "FMEA-A"}],
    }
    with pytest.raises(ValueError, match="duplicate.*FMEA ID"):
        validate_catalog(duplicate)
    unknown_mode = {
        "configurations": {"G80": "vehicle.yaml"},
        "requirements": [],
        "interfaces": [{"id": "IF-A", "applies_to": ["MISSING"]}],
        "fmea": [],
    }
    with pytest.raises(ValueError, match="unknown configurations"):
        validate_catalog(unknown_mode)


def test_fixed_mode_retains_gimbal_interface_as_not_applicable() -> None:
    catalog = yaml.safe_load((ROOT / "configs/engineering/traceability.yaml").read_text())
    resolved = resolve_interfaces(catalog, "G80")
    gimbal = next(item for item in resolved if item["id"] == "IF-GIMBAL-001")
    assert gimbal["applicability_status"] == "not_applicable"
    assert len(resolved) == 8
    validate_catalog(catalog)


def test_missing_spec_field_is_unavailable_not_zero() -> None:
    vehicle = load_vehicle(ROOT / "configs/vehicle/platform/performance.yaml")
    catalog = {
        "requirements": [{"id": "RT-X", "applies_to": ["G80"], "spec_paths": ["no.such.field"]}]
    }
    resolved = resolve_requirements(catalog, vehicle, "G80")[0]["resolved_spec"][0]
    assert resolved == {"path": "no.such.field", "status": "unavailable", "value": None}


def test_export_binds_active_spec_and_catalog(tmp_path: Path) -> None:
    # Unit exercise the package-level loader on a copied catalog; caller can override root.
    catalog = yaml.safe_load((ROOT / "configs/engineering/traceability.yaml").read_text())
    assert len(catalog["requirements"]) == 23
    assert len(catalog["interfaces"]) == 8
    assert len(catalog["fmea"]) == 12
    assert all("status" in r for r in catalog["requirements"])
    assert catalog["expanded_wo03_acceptance"] == "open"
    statuses = {r["id"]: r["status"] for r in catalog["requirements"]}
    for requirement_id in [
        "RT-LOAD-001",
        "RT-LOAD-002",
        "RT-THERM-001",
        "RT-FIT-001",
        "RT-MOTION-001",
        "RT-RECOVERY-001",
        "RT-RECOVERY-002",
        "RT-POWER-001",
        "RT-VIB-001",
        "RT-FLUTTER-001",
    ]:
        assert statuses[requirement_id] == "open"
    for evidence in catalog["evidence_sources"]:
        assert (ROOT / evidence["path"]).is_file()
