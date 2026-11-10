"""Temporary copied reference sources/cache, GET metadata only and safe origins."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import reference_parts as api
from src.vehicle import reference_parts as references

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/reference-parts"


@pytest.fixture
def local(tmp_path):
    for relative in references.SOURCE_PINS:
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    # Ignored cache is optional on a clean checkout; never replace corrupt bytes.
    for relative in references.ASSET_PATHS:
        source = ROOT / relative
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert not source.is_symlink(), "Registered cache fixture must not follow a symlink"
        if source.exists():
            shutil.copyfile(source, destination)
    app = FastAPI(debug=True)
    app.include_router(api.create_router(tmp_path))
    return TestClient(app), tmp_path


def files(root):
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def detail(row, revision=None):
    return f"{BASE}/{row['id']}/{revision or row['revision_sha256']}"


def test_list_and_exact_details_preserve_unknowns_false_gates_and_file_bytes(local, monkeypatch):
    client, root = local
    before = files(root)

    def forbidden(*args, **kwargs):
        raise AssertionError("No CAD/kernel subprocess is authorized")

    monkeypatch.setattr(subprocess, "run", forbidden)
    response = client.get(BASE)
    assert response.status_code == 200 and response.headers["cache-control"] == "no-store"
    catalog = response.json()
    assert catalog == references.build(root)
    assert len(catalog["definitions"]) == 2
    for row in catalog["definitions"]:
        response = client.get(detail(row))
        assert response.status_code == 200
        selected = response.json()
        assert selected["definition"] == row
        assert selected["availability"] == catalog["availability"][row["id"]]
        missing = [
            ext
            for ext in ("step", "glb")
            if not (root / row["representation"]["assets"][ext]["path"]).exists()
        ]
        availability = catalog["availability"][row["id"]]
        assert availability["missing_formats"] == missing
        assert availability["geometry_available"] is (not missing)
        assert availability["status"] == (
            "unavailable" if missing else "verified_registered_local_cache"
        )
        assert availability["generation_attempted"] is False
        assert selected["catalog_revision_sha256"] == catalog["revision_sha256"]
        assert selected["catalog_id"] == "reference-local-v1"
        assert selected["scope"] == "geometry_only_planning"
        assert selected["action"] == "inspect_geometry_reference"
        assert selected["instance_created"] is False
        assert selected["engineering_accepted"] is False
        assert selected["simulation_eligible"] is False
        assert selected["flight_ready"] is False
        assert all(value is None for value in row["unknown_properties"].values())
        assert all(value is False for value in row["readiness"].values())
        assert row["interfaces"] is None and row["representation"]["installed_transform"] is None
        assert len(row["analytic_features"]) == 5
    assert files(root) == before
    assert client.post(BASE, json={}).status_code == 405
    assert client.get(detail(catalog["definitions"][0]) + "/glb").status_code == 404


def test_detail_selects_only_server_nominal_parameters(local, monkeypatch):
    client, _ = local
    row = client.get(BASE).json()["definitions"][0]
    original = references.select_reference
    calls = []

    def capture(root, reference_id, revision, parameters):
        calls.append((reference_id, revision, parameters))
        return original(root, reference_id, revision, parameters)

    monkeypatch.setattr(references, "select_reference", capture)
    assert client.get(detail(row)).status_code == 200
    assert calls == [(row["id"], row["revision_sha256"], row["parameters_mm"])]


def test_revision_mismatch_and_unknown_namespaced_id_are_recoverable(local):
    client, root = local
    row = client.get(BASE).json()["definitions"][0]
    before = files(root)
    response = client.get(detail(row, "0" * 64))
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "reference_revision_mismatch"
    assert response.json()["detail"]["current_revision"] == row["revision_sha256"]
    for reference_id in ["reference-local-v1:unknown", "foreign-namespace:item"]:
        response = client.get(f"{BASE}/{reference_id}/{row['revision_sha256']}")
        assert response.status_code == 404
        assert response.json()["detail"]["code"] == "reference_not_found"
    assert files(root) == before


@pytest.mark.parametrize(
    "suffix", ["?parameters_mm=1", "?format=glb", "?path=/Users/private", "?revision=x&revision=y"]
)
def test_no_queries_or_client_parameters_accepted(local, suffix):
    client, root = local
    row = client.get(BASE).json()["definitions"][0]
    before = files(root)
    for path in (BASE, detail(row)):
        response = client.get(path + suffix)
        assert response.status_code == 422
        assert "private" not in response.text
    assert files(root) == before


def test_body_paths_and_bad_revisions_rejected_without_source_access(local, monkeypatch):
    client, _ = local
    row = client.get(BASE).json()["definitions"][0]

    def forbidden(*args, **kwargs):
        raise AssertionError("Invalid/origin-forbidden requests must not read sources")

    monkeypatch.setattr(references, "build", forbidden)
    for path in (BASE, detail(row)):
        assert (
            client.request("GET", path, json={"parameters_mm": {"length_mm": 1}}).status_code == 422
        )
        assert (
            client.request(
                "OPTIONS",
                path,
                content=b"body",
                headers={"origin": "http://localhost:5173", "access-control-request-method": "GET"},
            ).status_code
            == 422
        )
    for reference_id in ["motor_tube", "..%2F..%2Fprivate", "http:%2F%2Fprivate"]:
        response = client.get(f"{BASE}/{reference_id}/{row['revision_sha256']}")
        assert response.status_code in (404, 422)
    assert client.get(detail(row, "not-a-revision")).status_code == 422
    assert client.get(detail(row, "A" * 64)).status_code == 422
    response = client.get(BASE + "?unknown=x")
    assert response.status_code == 422


def test_missing_cache_returns_unavailable_not_regeneration(local, monkeypatch):
    client, root = local
    before = client.get(BASE).json()
    for path in references.ASSET_PATHS:
        (root / path).unlink(missing_ok=True)
    remaining = files(root)

    def forbidden(*args, **kwargs):
        raise AssertionError("Cold cache must not regenerate or scan alternatives")

    monkeypatch.setattr(subprocess, "run", forbidden)
    response = client.get(BASE)
    assert response.status_code == 200
    cold = response.json()
    assert cold["definitions"] == before["definitions"]
    assert cold["revision_sha256"] == before["revision_sha256"]
    for row in cold["definitions"]:
        selected = client.get(detail(row)).json()
        assert selected["availability"]["status"] == "unavailable"
        assert selected["availability"]["geometry_available"] is False
        assert selected["availability"]["generation_attempted"] is False
        assert selected["availability"]["public_url_cache_verified"] is False
        assert selected["availability"]["missing_formats"] == ["step", "glb"]
    assert files(root) == remaining


@pytest.mark.parametrize("failure", ["corrupt_asset", "corrupt_manifest", "missing_source"])
def test_bad_or_missing_critical_evidence_fails_closed_without_raw_paths(local, failure):
    client, root = local
    row = client.get(BASE).json()["definitions"][0]
    if failure == "corrupt_asset":
        path = root / row["representation"]["assets"]["glb"]["path"]
        path.write_bytes(b"foreign bytes")
    elif failure == "corrupt_manifest":
        path = root / references.MANIFEST_PATH
        path.write_bytes(path.read_bytes() + b"\n")
    else:
        (root / references.CONFIG_PATH).unlink()
    before = files(root)
    for path in (BASE, detail(row)):
        response = client.get(path)
        assert response.status_code == 409
        assert response.json()["detail"]["code"] == "reference_source_unavailable"
        assert str(root) not in response.text and "Traceback" not in response.text
    assert files(root) == before


@pytest.mark.parametrize("origin", sorted(api.ORIGINS))
def test_exact_allowed_origins_success_error_and_get_only_preflight(local, origin):
    client, _ = local
    row = client.get(BASE).json()["definitions"][0]
    for path in (BASE, detail(row)):
        response = client.get(path, headers={"origin": origin})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["cache-control"] == "no-store"
        assert "access-control-allow-credentials" not in response.headers
        preflight = client.options(
            path,
            headers={
                "origin": origin,
                "access-control-request-method": "GET",
                "access-control-request-headers": "Content-Type",
            },
        )
        assert preflight.status_code == 204
        assert preflight.headers["access-control-allow-methods"] == "GET"
        assert preflight.headers["access-control-allow-origin"] == origin
        denied = client.options(
            path, headers={"origin": origin, "access-control-request-method": "POST"}
        )
        assert denied.status_code == 403
    error = client.get(detail(row, "0" * 64), headers={"origin": origin})
    assert error.status_code == 409
    assert error.headers["access-control-allow-origin"] == origin


@pytest.mark.parametrize(
    "origin",
    [
        "null",
        "https://evil.example",
        "http://localhost:8000",
        "http://localhost:5173/",
        "https://localhost:5173",
    ],
)
def test_foreign_origin_is_403_before_validation_or_source_access(local, monkeypatch, origin):
    client, _ = local

    def forbidden(*args, **kwargs):
        raise AssertionError("Origin rejection must happen before source reads")

    monkeypatch.setattr(references, "build", forbidden)
    for path in (BASE, BASE + "/invalid/invalid"):
        for method in ("get", "options"):
            response = getattr(client, method)(path, headers={"origin": origin})
            assert response.status_code == 403
            assert "access-control-allow-origin" not in response.headers


def test_repeated_origin_preflight_fields_and_unknown_options_queries_rejected(local):
    client, _ = local
    headers = {"origin": "http://localhost:5173", "access-control-request-method": "GET"}
    assert (
        client.get(
            BASE, headers=[("origin", "http://localhost:5173"), ("origin", "https://evil.example")]
        ).status_code
        == 403
    )
    assert (
        client.options(
            BASE, headers={**headers, "access-control-request-headers": "content-type,Content-Type"}
        ).status_code
        == 403
    )
    assert (
        client.options(
            BASE, headers={**headers, "access-control-request-headers": "authorization"}
        ).status_code
        == 403
    )
    assert client.options(BASE + "?path=/Users/private", headers=headers).status_code == 422
    assert client.options(BASE).status_code == 403


def test_factory_is_lazy_and_filesystem_failure_sanitized(local, monkeypatch):
    client, root = local

    def fail(*args, **kwargs):
        raise PermissionError("/Users/private/source")

    monkeypatch.setattr(references, "build", fail)
    api.create_router(root)  # no source read during construction
    response = client.get(BASE, headers={"origin": "http://localhost:4173"})
    assert response.status_code == 503
    assert "private" not in response.text and "Traceback" not in response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"
