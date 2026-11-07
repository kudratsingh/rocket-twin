"""Current AD1 is inspectable without substituting archived CAD, inertia or flight."""

from fastapi.testclient import TestClient

from src.api.app import ROOT, create_app
from src.api.rp1_inspection import ID, PINS, SPEC


def test_current_ad1_endpoints_preserve_source_and_withhold_missing_models(monkeypatch):
    client = TestClient(create_app(ROOT))

    def no_mass(*args, **kwargs):
        raise AssertionError("Current AD1 inspection must not compute a new mass model")

    monkeypatch.setattr("src.api.app.mass_properties", no_mass)
    catalog = client.get("/api/vehicles").json()
    assert catalog["default_design_id"] == ID
    assert next(row for row in catalog["candidates"] if row["id"] == ID)["available"]
    document = client.get(f"/api/vehicles/{ID}").json()
    assert document["identity"]["specification_sha256"] == PINS[SPEC]
    assert document["identity"]["resolved_spec_sha256"] is None
    assert document["identity"]["cad_revision_sha256"] is None
    assert len(document["parts"]) == 55
    assert not any(row.get("mesh_url") for row in document["parts"])
    assert len(document["summary"]["mass_cases"]) == 4
    assert document["summary"]["physical_inertia"] is None
    assert document["summary"]["flight_ready"] is False
    assert client.get(f"/api/vehicles/{ID}/mass").status_code == 409
    assert client.get(f"/api/vehicles/{ID}/analyses").json()["analyses"] == []
