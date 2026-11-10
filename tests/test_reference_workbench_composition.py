"""Actual mounted wrapper metadata and unchanged archived API source boundary."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from scripts.wo04_prepare_archived_cad_preview import (
    CATALOG_EQUIVALENCE,
    CATALOG_EQUIVALENCE_SHA256,
    REGISTRY,
    REGISTRY_SHA256,
    verify_catalog_equivalence,
)
from src.api import app as inspection
from src.api import workbench_app
from src.vehicle import reference_parts as references

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/reference-parts"


@pytest.fixture
def source_root(tmp_path: Path) -> Path:
    # Only known project-source/cache inputs, copied into isolated storage.
    for relative in references.SOURCE_PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    # Ignored cache is optional on a clean checkout; never replace corrupt bytes.
    for relative in references.ASSET_PATHS:
        source = ROOT / relative
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        assert not source.is_symlink(), "Registered cache fixture must not follow a symlink"
        if source.exists():
            shutil.copyfile(source, target)
    return tmp_path


def files(root: Path) -> dict[str, bytes]:
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def test_actual_wrapper_routes_catalog_and_exact_details_before_inspection_mount(
    source_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    before = files(source_root)

    def no_execution(*args, **kwargs):
        raise AssertionError("Composition checks must not start a solver, CAD kernel or listener")

    monkeypatch.setattr(subprocess, "run", no_execution)
    app = workbench_app.create_app(source_root, catalog=())
    # No synthetic test mount: these requests must pass through the actual factory.
    with TestClient(app) as client:
        response = client.get(BASE)
        assert response.status_code == 200, "Primary must mount the actual reference router"
        catalog = response.json()
        assert catalog == references.build(source_root)
        assert catalog["id"] == "reference-local-v1"
        assert catalog["scope"] == "geometry_only_planning"
        assert len(catalog["definitions"]) == 2
        assert response.headers["cache-control"] == "no-store"
        for definition in catalog["definitions"]:
            path = f"{BASE}/{definition['id']}/{definition['revision_sha256']}"
            detail = client.get(path)
            assert detail.status_code == 200
            data = detail.json()
            assert data["definition"] == definition
            assert data["catalog_revision_sha256"] == catalog["revision_sha256"]
            assert data["availability"] == catalog["availability"][definition["id"]]
            missing = [
                ext
                for ext in ("step", "glb")
                if not (source_root / definition["representation"]["assets"][ext]["path"]).exists()
            ]
            availability = catalog["availability"][definition["id"]]
            assert availability["missing_formats"] == missing
            assert availability["geometry_available"] is (not missing)
            assert availability["status"] == (
                "unavailable" if missing else "verified_registered_local_cache"
            )
            assert availability["generation_attempted"] is False
            assert data["instance_created"] is False
            assert data["engineering_accepted"] is False
            assert data["simulation_eligible"] is False
            assert data["flight_ready"] is False
            assert all(value is None for value in definition["unknown_properties"].values())
            assert all(value is False for value in definition["readiness"].values())
            assert definition["interfaces"] is None
            assert definition["representation"]["installed_transform"] is None
    assert files(source_root) == before
    assert not (source_root / "output/design-drafts").exists()


def test_wrapper_preserves_base_api_docs_source_catalog_and_cors_behavior(
    source_root: Path,
) -> None:
    base_app = inspection.create_app(source_root, catalog=())
    wrapper = workbench_app.create_app(source_root, catalog=())
    assert base_app.state.snapshots == {}  # No archive geometry/model resolution in this fixture.
    assert workbench_app.CATALOG is inspection.CATALOG
    assert len(inspection.CATALOG) == 4
    before = files(source_root)
    with TestClient(base_app) as base, TestClient(wrapper) as composed:
        for path in (
            "/api/health",
            "/api/vehicles",
            "/api/parts-bank",
            "/api/vehicles/not-registered",
            "/docs",
            "/openapi.json",
        ):
            original = base.get(path)
            actual = composed.get(path)
            assert actual.status_code == original.status_code, path
            assert actual.content == original.content, path
            assert actual.headers.get("content-type") == original.headers.get("content-type"), path
        assert composed.get("/api/vehicles").json()["vehicles"] == []
        assert composed.get("/api/parts-bank").json()["summary"]["source_records"] == 55
        # Existing docs still belong to the unchanged base app, not a replacement schema.
        assert "/api/reference-parts" not in composed.get("/openapi.json").json()["paths"]
        for origin in ("http://127.0.0.1:5173", "http://127.0.0.1:4173"):
            original = base.get("/api/vehicles", headers={"Origin": origin})
            actual = composed.get("/api/vehicles", headers={"Origin": origin})
            assert actual.content == original.content
            assert actual.headers.get("access-control-allow-origin") == original.headers.get(
                "access-control-allow-origin"
            )
        request = {"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "PATCH"}
        assert (
            composed.options("/api/vehicles", headers=request).status_code
            == base.options("/api/vehicles", headers=request).status_code
            == 400
        )
    assert files(source_root) == before
    assert not (source_root / "output/design-drafts").exists()


def test_reference_preflight_and_errors_are_not_intercepted_by_base_cors(source_root: Path) -> None:
    with TestClient(workbench_app.create_app(source_root, catalog=())) as client:
        origin = "http://127.0.0.1:4173"
        catalog = client.get(BASE, headers={"Origin": origin})
        assert catalog.status_code == 200
        assert catalog.headers["access-control-allow-origin"] == origin
        row = catalog.json()["definitions"][0]
        for path in (BASE, f"{BASE}/{row['id']}/{row['revision_sha256']}"):
            preflight = client.options(
                path,
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "GET",
                    "Access-Control-Request-Headers": "content-type",
                },
            )
            assert preflight.status_code == 204
            assert preflight.headers["access-control-allow-methods"] == "GET"
            assert preflight.headers["access-control-allow-origin"] == origin
            assert "access-control-allow-credentials" not in preflight.headers
            assert (
                client.get(path, headers={"Origin": "https://foreign.invalid"}).status_code == 403
            )
        stale = client.get(f"{BASE}/{row['id']}/{'0' * 64}", headers={"Origin": origin})
        assert stale.status_code == 409
        assert stale.json()["detail"]["code"] == "reference_revision_mismatch"
        assert stale.json()["detail"]["current_revision"] == row["revision_sha256"]
        assert stale.headers["access-control-allow-origin"] == origin


def test_missing_reference_cache_does_not_change_legacy_api_or_generate_files(
    source_root: Path,
) -> None:
    with TestClient(workbench_app.create_app(source_root, catalog=())) as client:
        before_catalog = client.get(BASE).json()
        legacy = client.get("/api/parts-bank").content
        for path in references.ASSET_PATHS:
            (source_root / path).unlink(missing_ok=True)
        before = files(source_root)
        cold = client.get(BASE)
        assert cold.status_code == 200
        assert cold.json()["definitions"] == before_catalog["definitions"]
        assert cold.json()["revision_sha256"] == before_catalog["revision_sha256"]
        assert all(
            state["status"] == "unavailable"
            and state["missing_formats"] == ["step", "glb"]
            and state["geometry_available"] is False
            and state["generation_attempted"] is False
            for state in cold.json()["availability"].values()
        )
        assert client.get("/api/parts-bank").content == legacy
        assert client.get("/api/health").json()["flight_ready"] is False
        assert files(source_root) == before


def test_frozen_archived_registry_and_api_body_keep_existing_equivalence_record() -> None:
    # Static archived-source equivalence, not a new archived CAD/runtime campaign.
    proof_bytes = CATALOG_EQUIVALENCE.read_bytes()
    assert hashlib.sha256(proof_bytes).hexdigest() == CATALOG_EQUIVALENCE_SHA256
    assert hashlib.sha256(REGISTRY.read_bytes()).hexdigest() == REGISTRY_SHA256
    proof = json.loads(proof_bytes)
    verify_catalog_equivalence(
        (ROOT / "src/api/app.py").read_bytes(), proof, proof["original"]["sha256"]
    )
    assert proof["geometry_or_asset_changed"] is False
