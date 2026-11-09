"""Read-only source bank routing and fail-closed current-source identity."""

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import rp1_inspection
from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]


def source_client(tmp_path):
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return TestClient(create_app(tmp_path, catalog=()))


def test_catalog_and_detail_preserve_source_group_and_installed_instance(tmp_path):
    client = source_client(tmp_path)
    response = client.get("/api/parts-bank")
    assert response.status_code == 200
    bank = response.json()
    assert len(bank["definitions"]) == len(bank["instances"]) == 55
    assert bank["identity"]["specification_sha256"] == rp1_inspection.PINS[rp1_inspection.SPEC]
    assert bank["identity"]["inspection_geometry_sha256"] is None
    detail = client.get("/api/parts-bank/rp1:fin_set")
    assert detail.status_code == 200
    item = detail.json()
    assert item["definition"]["source_part_id"] == "fin_set"
    assert item["instances"][0]["quantity"] == 1
    assert item["instances"][0]["group_count"] == 3
    assert item["revision_sha256"] == bank["revision_sha256"]
    assert client.get("/api/parts-bank/rp1:unavailable").status_code == 404
    assert client.post("/api/parts-bank", json={"add": "motor"}).status_code == 405


def test_changed_source_rejects_both_catalog_and_detail_instead_of_serving_stale_data(tmp_path):
    client = source_client(tmp_path)
    assert client.get("/api/parts-bank").status_code == 200
    spec = tmp_path / rp1_inspection.SPEC
    spec.write_bytes(spec.read_bytes() + b"\n")
    for url in ("/api/parts-bank", "/api/parts-bank/rp1:fin_set"):
        response = client.get(url)
        assert response.status_code == 409
        assert "source hash mismatch" in response.json()["detail"]
