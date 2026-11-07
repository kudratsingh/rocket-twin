"""Source-derived display projection does not admit a vehicle or borrow archive CAD."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from urllib.parse import urlparse

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.rp1_inspection_view import build
from src.inspection.rp1_geometry import EVIDENCE, FOLDER, export, sources

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def generated_root(tmp_path_factory):
    root = tmp_path_factory.mktemp("projection-source")
    for relative in sources(ROOT):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    manifest = export(root)
    evidence = root / EVIDENCE
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(json.dumps(manifest, indent=2) + "\n")
    return root


@pytest.fixture
def projection_root(tmp_path, generated_root):
    shutil.copytree(generated_root, tmp_path, dirs_exist_ok=True)
    return tmp_path


def test_real_projection_keeps_55_records_and_no_canonical_inertia(projection_root):
    document = build(projection_root)
    assert len(document["parts"]) == 55
    assert sum("mesh_url" in p for p in document["parts"]) == 26
    assert document["identity"]["resolved_spec_sha256"] is None
    assert document["identity"]["cad_revision_sha256"] is None
    assert document["summary"]["physical_inertia"] is None
    assert document["summary"]["inspection_geometry"]["complete_installed_geometry"] is False
    for part in document["parts"]:
        if part["representation"]["role"] in ("mass_allowance", "missing_geometry"):
            assert "mesh_url" not in part


def test_exact_mesh_identity_api_and_missing_field_state(projection_root):
    client = TestClient(create_app(projection_root, catalog=()))
    doc = client.get("/api/vehicles/G80-F2-RP1-AD1-definition-v2").json()
    part = next(p for p in doc["parts"] if p["id"] == "fin_tabs")
    response = client.get(part["mesh_url"])
    assert response.status_code == 200
    assert response.headers["content-type"] == "model/gltf-binary"
    assert response.content[:4] == b"glTF"
    query = urlparse(part["mesh_url"]).query
    assert client.get(part["mesh_url"].replace("spec=811b", "spec=0000")).status_code == 409
    assert client.get(part["mesh_url"].replace("mesh=", "mesh=wrong")).status_code == 409
    assert client.get(part["mesh_url"].replace("geometry=", "geometry=wrong")).status_code == 409
    assert client.get(f"/api/design/foreign/inspection-mesh/fin_tabs?{query}").status_code == 404
    assert (
        client.get(f"/api/design/{doc['id']}/inspection-mesh/rail_buttons?{query}").status_code
        == 409
    )
    assert client.get(f"/api/vehicles/{doc['id']}/mass").status_code == 409
    assert client.get(f"/api/vehicles/{doc['id']}/analyses").json()["analyses"] == []
    metadata = client.get(f"/api/design/{doc['id']}/inspection-geometry").json()
    assert metadata["coverage"]["mesh_parts"] == 26


def test_unavailable_geometry_keeps_honest_source_view(projection_root):
    path = projection_root / FOLDER / "parts/body.glb"
    path.write_bytes(b"not a valid saved mesh")
    document = build(projection_root)
    assert len(document["parts"]) == 55
    assert all("mesh_url" not in p for p in document["parts"])
    assert document["summary"]["inspection_geometry"]["status"] == "unavailable"
    assert document["identity"]["cad_revision_sha256"] is None
    assert "inspection_geometry_sha256" not in document["identity"]
