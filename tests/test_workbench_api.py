"""Walkthrough availability is independent of detailed CAD and physical gates."""

from pathlib import Path

from fastapi.testclient import TestClient

from src.api.app import create_app


def test_workbench_route_serves_sourced_graphics_without_a_cad_catalog():
    root = Path(__file__).resolve().parents[1]
    with TestClient(create_app(root=root, catalog=())) as client:
        response = client.get("/api/engineering/workbench")
    assert response.status_code == 200
    record = response.json()
    assert record["identity"]["cad_revision"] is None
    assert len(record["load_paths"]) == 5
    assert len(record["cases"]) == 4
    assert record["launch"]["equipment_confirmed"] is False
    assert record["cases"][0]["growth_g"] == 50
