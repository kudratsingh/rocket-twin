"""Inspection boundary smoke: exact backend numbers, recorded identity and safe files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.api.app import CATALOG, ROOT, _analysis_notice, create_app, sha256, vehicle_identity
from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import load_vehicle


@pytest.fixture
def recorded_root(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "configs", tmp_path / "configs")
    shutil.copytree(ROOT / "src/cad", tmp_path / "src/cad")
    for entry in CATALOG:
        vehicle = load_vehicle(tmp_path / entry.path)
        folder = tmp_path / "build" / vehicle.id
        (folder / "parts").mkdir(parents=True)
        rows = []
        for part in vehicle.parts:
            # Tiny fixture bytes test serving only, not geometry correctness.
            (folder / "parts" / f"{part.id}.glb").write_bytes(b"glTF-test-fixture")
            rows.append(
                {
                    "id": part.id,
                    "shape_sha256": vehicle_identity(vehicle, tmp_path).part_shape_sha256[part.id],
                    "mesh": f"parts/{part.id}.glb",
                    "cad_mass_kg": part.resolved_mass_kg,
                }
            )
        (folder / "manifest.json").write_text(
            json.dumps(
                {
                    "identity": vehicle_identity(vehicle, tmp_path).model_dump(),
                    "parts": rows,
                    "viewer_frame": "X=body+y, Y=length-station, Z=body-z",
                }
            )
        )
    return tmp_path


def test_readonly_inspection_uses_backend_mass_and_recorded_mesh(
    recorded_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_solver(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Read-only inspection must not launch external solvers")

    monkeypatch.setattr("subprocess.run", no_solver)
    client = TestClient(create_app(recorded_root))
    catalog = client.get("/api/vehicles").json()
    assert len(catalog["vehicles"]) == 4
    assert all(row["available"] for row in catalog["vehicles"])
    assert catalog["candidates"][0]["available"] is False
    assert catalog["candidates"][0]["id"] == "experimental-g80-retention-72"
    assert catalog["vehicles"][1]["role"] == "conditional_upgrade"
    assert catalog["vehicles"][3]["role"] == "eventual_concept"
    for entry in CATALOG:
        vehicle = load_vehicle(recorded_root / entry.path)
        detail = client.get(f"/api/vehicles/{vehicle.id}")
        assert detail.status_code == 200
        payload = detail.json()
        props = mass_properties(vehicle)
        assert payload["identity"] == vehicle_identity(vehicle, recorded_root).model_dump()
        assert payload["summary"]["nominal_mass_kg"] == pytest.approx(props.mass_kg)
        assert payload["summary"]["cp_m"] == pytest.approx(center_of_pressure(vehicle))
        assert sum(row["mass_kg"] for row in payload["summary"]["mass_budget"]) == pytest.approx(
            props.mass_kg
        )
        assert sum(
            row["percent_total"] for row in payload["summary"]["mass_budget"]
        ) == pytest.approx(100)
        assert payload["summary"]["engineering_acceptance"] == "open"
        assert payload["summary"]["flight_ready"] is False
        assert all(
            p["learn"]
            and p["manufacturing"]
            and p["evidence_status"]["validation"] == "unvalidated"
            for p in payload["parts"]
        )
        for fraction in (0, 0.5, 1):
            backend = mass_properties(vehicle, fraction)
            actual = client.get(
                f"/api/vehicles/{vehicle.id}/mass", params={"burn_fraction": fraction}
            ).json()
            assert actual["mass_kg"] == pytest.approx(backend.mass_kg)
            assert actual["cg_m"] == pytest.approx(backend.cg_m)
            assert actual["inertia_kg_m2"] == backend.inertia_kg_m2.tolist()
        if vehicle.design and vehicle.design.mode == "tvc_finless":
            assert payload["summary"]["stability_margin_cal"] < 0
        mesh_url = payload["parts"][0]["mesh_url"]
        mesh = client.get(mesh_url)
        assert mesh.status_code == 200 and mesh.content == b"glTF-test-fixture"
        assert mesh.headers["x-artifact-sha256"] == sha256(mesh.content)
        assert (
            client.get(mesh_url, headers={"If-None-Match": mesh.headers["etag"]}).status_code == 304
        )
        assert client.get(f"/api/vehicles/{vehicle.id}/mass?burn_fraction=-1").status_code == 422
        assert client.get(f"/api/vehicles/{vehicle.id}/mass?burn_fraction=nan").status_code == 422
        motor = payload["summary"]["motor"]["id"]
        assert client.get(f"/api/motors/{motor}/curve").json()["samples"]
    assert client.get("/api/vehicles/not-allowlisted").status_code == 404
    assert client.get("/api/motors/not-allowlisted/curve").status_code == 404
    assert client.post("/api/vehicles", json={"path": "/etc/passwd"}).status_code == 405
    assert (
        client.get("/api/vehicles/modular-performance-v1/meshes/not_a_part.glb").status_code == 404
    )
    assert (
        client.get(
            "/api/vehicles/modular-performance-v1/meshes/%2e%2e%2fmanifest.json.glb"
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    "mismatch",
    [
        "resolved_spec_sha256",
        "cad_revision_sha256",
        "part_shape_sha256",
        "mesh_path",
        "missing_mesh",
    ],
)
def test_stale_or_missing_geometry_is_unavailable(recorded_root: Path, mismatch: str) -> None:
    folder = recorded_root / "build/modular-performance-v1"
    manifest = json.loads((folder / "manifest.json").read_text())
    if mismatch == "part_shape_sha256":
        manifest["identity"][mismatch]["nose_cone"] = "0" * 64
    elif mismatch == "mesh_path":
        manifest["parts"][0]["mesh"] = "../../configs/platform.yaml"
    elif mismatch == "missing_mesh":
        (folder / "parts/nose_cone.glb").unlink()
    else:
        manifest["identity"][mismatch] = "0" * 64
    (folder / "manifest.json").write_text(json.dumps(manifest))
    client = TestClient(create_app(recorded_root))
    assert client.get("/api/vehicles").json()["vehicles"][0]["available"] is False
    assert client.get("/api/vehicles/modular-performance-v1").status_code == 503
    assert (
        client.get("/api/vehicles/modular-performance-v1/meshes/nose_cone.glb").status_code == 503
    )
    # The source-only mass model remains explicit and usable without invented geometry.
    assert client.get("/api/vehicles/modular-performance-v1/mass").status_code == 200


def test_runtime_changes_and_symlinks_fail_closed(recorded_root: Path, tmp_path: Path) -> None:
    client = TestClient(create_app(recorded_root))
    url = "/api/vehicles/modular-performance-v1/meshes/nose_cone.glb"
    mesh = recorded_root / "build/modular-performance-v1/parts/nose_cone.glb"
    mesh.write_bytes(b"corrupted")
    assert client.get(url).status_code == 503
    outside = tmp_path / "outside.glb"
    outside.write_bytes(b"glTF-test-fixture")
    mesh.unlink()
    mesh.symlink_to(outside)
    assert client.get(url).status_code == 503
    spec = recorded_root / CATALOG[0].path
    spec.write_text(spec.read_text() + "\n# runtime edit\n")
    assert client.get("/api/vehicles/modular-performance-v1/mass").status_code == 503


def test_recorded_analysis_is_allowlisted_and_incompatible_fields_are_rejected(
    recorded_root: Path,
) -> None:
    vehicle = load_vehicle(recorded_root / CATALOG[0].path)
    client = TestClient(create_app(recorded_root))
    assert client.get(f"/api/vehicles/{vehicle.id}/analyses").json()["analyses"] == []
    assert (
        client.get(f"/api/vehicles/{vehicle.id}").json()["analysis_status"]["compatible_runs"] == 0
    )
    identity = vehicle_identity(vehicle, recorded_root).model_dump()
    folder = recorded_root / "build" / vehicle.id / "analysis/fixture"
    (folder / "fields").mkdir(parents=True)
    artifact = json.dumps({"values": [[300.0], [310.0]]}, sort_keys=True).encode() + b"\n"
    (folder / "fields/temperature.json").write_bytes(artifact)
    record = {
        "run_id": "fixture",
        "tools": {"fixture": "test-only"},
        "input_sha256": {},
        "identity": identity,
        "cases": {"soak": {"description": "fixture"}},
        "fields": [
            {
                "id": "temperature",
                "case_id": "soak",
                "quantity": "temperature",
                "component": "part temperature",
                "units": "K",
                "association": "part",
                "part_ids": ["nose_cone"],
                "evidence": {
                    "provenance": "calculated",
                    "validation": "unvalidated",
                    "assumptions": ["fixture"],
                    "limits": [],
                    "sources": [],
                    "uncertainty": "fixture",
                    "required_physical_tests": ["Measure temperature"],
                },
                "times_s": [0, 1],
                "artifact": "fields/temperature.json",
                "artifact_sha256": sha256(artifact),
                "sample_count": 1,
                "coverage_notes": "Uniform part-level fixture",
            }
        ],
    }
    (folder / "manifest.json").write_text(json.dumps(record))
    # Registration happens after app creation, as it does for a running preview.
    # Discovery only reads records; no server restart or solver invocation is needed.
    listing = client.get(f"/api/vehicles/{vehicle.id}/analyses").json()["analyses"]
    assert len(listing) == 1 and listing[0]["compatible"]
    assert (
        client.get(f"/api/vehicles/{vehicle.id}").json()["analysis_status"]["compatible_runs"] == 1
    )
    manifest = client.get(listing[0]["manifest_url"]).json()
    assert manifest["fields"][0]["times_s"] == [0, 1]
    url = manifest["artifacts"]["fields/temperature.json"]
    assert client.get(url).content == artifact
    assert client.get(url.replace("temperature.json", "not-allowlisted.json")).status_code == 404
    (folder / "fields/temperature.json").write_bytes(b"{}")
    assert client.get(url).status_code == 503
    (folder / "fields/temperature.json").write_bytes(artifact)
    record["identity"]["resolved_spec_sha256"] = "0" * 64
    (folder / "manifest.json").write_text(json.dumps(record))
    listing = client.get(f"/api/vehicles/{vehicle.id}/analyses").json()["analyses"]
    assert listing[0]["compatible"] is False
    assert client.get(url).status_code == 409
    assert (
        client.get(f"/api/vehicles/{vehicle.id}").json()["analysis_status"]["compatible_runs"] == 0
    )
    (folder / "manifest.json").unlink()
    assert client.get(f"/api/vehicles/{vehicle.id}/analyses").json()["analyses"] == []
    assert client.get(url).status_code == 404


def test_analysis_registry_rejects_escaping_manifests(recorded_root: Path, tmp_path: Path) -> None:
    client = TestClient(create_app(recorded_root))
    outside = tmp_path / "outside-analysis"
    outside.mkdir()
    (outside / "manifest.json").write_text("{}")
    registry = recorded_root / "build/modular-performance-v1/analysis"
    registry.mkdir()
    (registry / "outside").symlink_to(outside, target_is_directory=True)
    listing = client.get("/api/vehicles/modular-performance-v1/analyses")
    assert listing.status_code == 200 and listing.json()["analyses"] == []


def test_superseded_band_model_notice_is_not_a_cad_compatibility_claim() -> None:
    historical = SimpleNamespace(
        run_id="wo03-thermal-20261031T004856773221Z-modular-performance-v1"
    )
    assert "SUPERSEDED" in _analysis_notice(historical)
    assert _analysis_notice(SimpleNamespace(run_id="other-analysis")) is None


def test_frozen_candidate_is_separate_and_fails_closed(
    recorded_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Synthetic fixture checks routing/provenance, not candidate CAD geometry."""
    from src.api import candidate_snapshot

    folder = recorded_root / candidate_snapshot.FOLDER
    (folder / "parts").mkdir(parents=True)
    ids = [f"test_part_{i}" for i in range(72)]
    identity = {
        "resolved_spec_sha256": candidate_snapshot.IDENTITY,
        "cad_revision_sha256": candidate_snapshot.CAD,
    }
    data = {
        "id": candidate_snapshot.ALIAS,
        "identity": identity,
        "parts": [{"id": part_id} for part_id in ids],
        "snapshot_only": True,
    }
    projection = {"data": data, "mass": [{"mass_kg": 0.7}] * 21}
    projection_bytes = json.dumps(projection).encode()
    (folder / "projection.json").write_bytes(projection_bytes)
    mesh_bytes = b"test-only-glb"
    for part_id in ids:
        (folder / "parts" / f"{part_id}.glb").write_bytes(mesh_bytes)
    index = {
        "candidate_identity": candidate_snapshot.IDENTITY,
        "cad_revision_sha256": candidate_snapshot.CAD,
        "projection_sha256": sha256(projection_bytes),
        "mesh_sha256": dict.fromkeys(ids, sha256(mesh_bytes)),
    }
    index_bytes = json.dumps(index).encode()
    (folder / "index.json").write_bytes(index_bytes)
    monkeypatch.setattr(candidate_snapshot, "INDEX_SHA256", sha256(index_bytes))
    client = TestClient(create_app(recorded_root))
    catalog = client.get("/api/vehicles").json()
    assert len(catalog["vehicles"]) == 4
    assert catalog["candidates"][0]["id"] == candidate_snapshot.ALIAS
    assert catalog["candidates"][0]["available"] is True
    base = "/api/vehicles/" + candidate_snapshot.ALIAS
    assert client.get(base).json()["snapshot_only"] is True
    assert client.get(base + "/mass?burn_fraction=0.05").json()["mass_kg"] == 0.7
    assert client.get(base + "/mass?burn_fraction=0.03").status_code == 422
    assert len(client.get(base + "/meshes").json()["parts"]) == 72
    assert client.get(base + "/meshes/test_part_0.glb").content == mesh_bytes
    assert client.get(base + "/meshes/not_a_part.glb").status_code == 404
    assert client.get(base + "/meshes/%2e%2e%2fprojection.json.glb").status_code == 404
    assert (
        client.post(
            "/api/experiments", json={"configuration": candidate_snapshot.ALIAS}
        ).status_code
        == 422
    )
    (folder / "parts/test_part_0.glb").write_bytes(b"tampered")
    assert client.get(base + "/meshes/test_part_0.glb").status_code == 503
    (folder / "projection.json").write_bytes(b"tampered")
    assert client.get(base).status_code == 503
    assert client.get("/api/vehicles/modular-performance-v1").status_code == 200
