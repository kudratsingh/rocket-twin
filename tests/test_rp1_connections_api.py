"""Exercise AD1 connection endpoint provenance and allowlisted SVG delivery."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.api import rp1_connections as connections
from src.api.app import create_app

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = "/api/engineering/rp1-connections"


@pytest.fixture
def source_root(tmp_path):
    for relative, contents in connections._snapshot(ROOT).items():
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(contents)
    return tmp_path


@pytest.fixture
def client(source_root):
    with TestClient(create_app(root=source_root, catalog=())) as app_client:
        yield app_client


def drawing_request(client, drawing, *, spec=None, sha256=None):
    return client.get(
        f"{ENDPOINT}/drawings/{drawing['id']}",
        params={
            "spec": spec or connections.PINS[connections.SPEC],
            "sha256": sha256 or drawing["sha256"],
        },
    )


def test_payload_and_all_pinned_drawing_bytes(client, source_root):
    response = client.get(ENDPOINT)
    assert response.status_code == 200
    result = response.json()
    assert result == connections.build(source_root)
    assert result["configuration"]["sha256"] == connections.PINS[connections.SPEC]
    assert result["configuration"]["id"] == connections.rp1_inspection.ID
    assert len(result["part_ids"]) == 55
    assert [item["id"] for item in result["connections"]] == ["fin-root", "recovery"]
    for drawing in result["drawings"]:
        image = drawing_request(client, drawing)
        assert image.status_code == 200
        assert image.headers["content-type"].startswith("image/svg+xml")
        assert image.content == (source_root / drawing["path"]).read_bytes()
        assert hashlib.sha256(image.content).hexdigest() == drawing["sha256"]
        assert image.headers["etag"] == drawing["sha256"]


def test_wrong_spec_wrong_hash_unknown_id_and_missing_identity(client):
    drawing = client.get(ENDPOINT).json()["drawings"][0]
    assert drawing_request(client, drawing, spec="0" * 64).status_code == 409
    assert drawing_request(client, drawing, sha256="0" * 64).status_code == 409
    assert (
        client.get(
            f"{ENDPOINT}/drawings/unknown", params={"spec": "0" * 64, "sha256": "0" * 64}
        ).status_code
        == 404
    )
    assert client.get(f"{ENDPOINT}/drawings/{drawing['id']}").status_code == 422


@pytest.mark.parametrize(
    "alteration", ["missing-source", "tampered-source", "missing-drawing", "tampered-drawing"]
)
def test_missing_or_tampered_sources_fail_closed(client, source_root, alteration):
    drawing = client.get(ENDPOINT).json()["drawings"][0]
    path = source_root / (connections.SPEC if alteration.endswith("source") else drawing["path"])
    if alteration.startswith("missing"):
        path.unlink()
    else:
        path.write_bytes(path.read_bytes() + b"changed")
    assert client.get(ENDPOINT).status_code == 409
    assert drawing_request(client, drawing).status_code == 409
