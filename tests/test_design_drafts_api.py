"""In-process HTTP lifecycle on isolated temporary storage, without a server."""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import design_drafts as api
from src.api import rp1_inspection
from src.vehicle.design_drafts import DraftStore

ROOT = Path(__file__).resolve().parents[1]
BODY = {
    "source_configuration_id": rp1_inspection.ID,
    "source_specification_sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
    "label": "Isolated RP1 fork",
    "notes": "Original source remains frozen",
}
BASE = "/api/design-drafts"


@pytest.fixture
def local(tmp_path):
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    app = FastAPI(debug=True)
    app.include_router(api.create_router(tmp_path))
    return TestClient(app), tmp_path


def test_fork_partial_metadata_save_reload_exact_history_and_original_preservation(local):
    client, root = local
    before = {p: (root / p).read_bytes() for p in rp1_inspection.PINS}
    assert client.get(BASE).json() == {"drafts": [], "next_after": None}
    response = client.post(BASE, json=BODY)
    assert response.status_code == 201
    first = response.json()
    location = f"{BASE}/{first['draft_id']}"
    assert first["base_configuration_id"] == rp1_inspection.ID
    assert len(first["source"]["parts_bank"]["instances"]) == 55
    assert first["readiness"]["flight_ready"] is False
    assert first["readiness"]["simulation_eligible"] is False
    assert client.get(location).json() == first
    changed = client.patch(
        location, json={"base_revision": first["revision_sha256"], "notes": "Updated notes"}
    )
    assert changed.status_code == 200
    second = changed.json()
    assert second["label"] == first["label"]
    assert second["notes"] == "Updated notes"
    assert second["source"] == first["source"]
    assert second["parent_revision_sha256"] == first["revision_sha256"]
    assert client.get(location, params={"revision": first["revision_sha256"]}).json() == first
    third = client.patch(
        location, json={"base_revision": second["revision_sha256"], "label": "Renamed"}
    ).json()
    assert third["notes"] == second["notes"]
    assert client.get(location).json() == third
    summary = client.get(BASE).json()["drafts"][0]
    assert summary["revision_sha256"] == third["revision_sha256"]
    assert "source" not in summary
    assert before == {p: (root / p).read_bytes() for p in before}
    assert response.headers["cache-control"] == "no-store"


def test_stale_save_returns_recoverable_current_revision_without_changing_head(local):
    client, _ = local
    first = client.post(BASE, json=BODY).json()
    location = f"{BASE}/{first['draft_id']}"
    second = client.patch(
        location, json={"base_revision": first["revision_sha256"], "label": "Winner"}
    ).json()
    response = client.patch(
        location, json={"base_revision": first["revision_sha256"], "notes": "Stale intent"}
    )
    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "stale_revision"
    assert response.json()["detail"]["current_revision"] == second["revision_sha256"]
    assert client.get(location).json() == second


@pytest.mark.parametrize(
    "changes",
    [
        {"source_configuration_id": "modular-performance-v1"},
        {"source_configuration_id": "../../configs/private.yaml"},
        {"source_specification_sha256": "0" * 64},
        {"source_specification_sha256": None},
        {"label": 42},
        {"label": " "},
        {"label": "x" * 161},
        {"notes": "x" * 8001},
        {"asset_path": "/Users/private/secret"},
        {"draft_id": str(uuid4())},
    ],
)
def test_invalid_fork_fields_sources_and_paths_fail_before_writes(local, changes):
    client, root = local
    response = client.post(BASE, json={**BODY, **changes})
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "invalid_request"
    assert "/Users/private" not in response.text
    assert "../../configs" not in response.text
    assert not (root / "output").exists()


def test_required_source_fields_and_unknown_payload_are_rejected(local):
    client, root = local
    for missing in ["source_configuration_id", "source_specification_sha256", "label"]:
        response = client.post(BASE, json={k: v for k, v in BODY.items() if k != missing})
        assert response.status_code == 422
    malformed = client.post(
        BASE,
        content=b'{"label": /Users/private/secret}',
        headers={"content-type": "application/json"},
    )
    assert malformed.status_code == 422
    assert "private/secret" not in malformed.text
    assert not (root / "output").exists()


@pytest.mark.parametrize(
    "payload",
    [
        {"notes": "Missing revision"},
        {"base_revision": "../../private", "notes": "Bad"},
        {"base_revision": "0" * 64},
        {"base_revision": "0" * 64, "label": None},
        {"base_revision": "0" * 64, "notes": None},
        {"base_revision": "0" * 64, "label": " ", "notes": ""},
        {"base_revision": "0" * 64, "notes": "nul\0"},
        {"base_revision": "0" * 64, "flight_ready": True},
        {"base_revision": "0" * 64, "source": {"path": "/Users/private"}},
    ],
)
def test_metadata_schema_rejects_unsupported_edits(local, payload):
    client, root = local
    response = client.patch(f"{BASE}/{uuid4()}", json=payload)
    assert response.status_code == 422
    assert "private" not in response.text
    assert not (root / "output").exists()


def test_safe_id_revision_and_bounded_query_validation(local):
    client, root = local
    for path in ["not-a-uuid", "source.json", str(uuid4()).upper()]:
        response = client.get(f"{BASE}/{path}")
        assert response.status_code == 422
    for query in [
        {"limit": 0},
        {"limit": 101},
        {"limit": "true"},
        {"after": "../configs"},
        {"path": "/Users/private"},
    ]:
        response = client.get(BASE, params=query)
        assert response.status_code == 422
        assert "private" not in response.text
    assert client.get(BASE + "?limit=1&limit=2").status_code == 422
    assert client.get(f"{BASE}/{uuid4()}", params={"revision": "../source.json"}).status_code == 422
    assert client.get(f"{BASE}/{uuid4()}").status_code == 404
    assert not (root / "output").exists()


def test_http_list_pagination_and_unknown_historical_revision(local):
    client, _ = local
    created = [client.post(BASE, json={**BODY, "label": f"Study {i}"}).json() for i in range(3)]
    first = client.get(BASE, params={"limit": 2}).json()
    second = client.get(BASE, params={"limit": 2, "after": first["next_after"]}).json()
    ids = [r["draft_id"] for page in [first, second] for r in page["drafts"]]
    assert ids == sorted(c["draft_id"] for c in created)
    assert second["next_after"] is None
    assert (
        client.get(f"{BASE}/{created[0]['draft_id']}", params={"revision": "0" * 64}).status_code
        == 404
    )


@pytest.mark.parametrize("origin", sorted(api.ORIGINS))
def test_exact_local_preview_origins_and_scoped_preflight(local, origin):
    client, root = local
    headers = {"origin": origin}
    get = client.get(BASE, headers=headers)
    assert get.status_code == 200
    assert get.headers["access-control-allow-origin"] == origin
    assert "access-control-allow-credentials" not in get.headers
    preflight = client.options(
        BASE,
        headers={
            **headers,
            "access-control-request-method": "POST",
            "access-control-request-headers": "Content-Type",
        },
    )
    assert preflight.status_code == 204
    assert preflight.headers["access-control-allow-origin"] == origin
    assert preflight.headers["access-control-allow-methods"] == "GET, POST"
    assert preflight.headers["access-control-allow-headers"] == "Content-Type"
    invalid = client.post(BASE, json={}, headers=headers)
    assert invalid.status_code == 422
    assert invalid.headers["access-control-allow-origin"] == origin
    assert not (root / "output").exists()


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example",
        "null",
        "http://localhost:8080",
        "http://localhost:5173.evil.example",
        "http://localhost:5173/",
        "https://localhost:5173",
    ],
)
def test_other_browser_origins_are_403_without_reads_or_writes(local, origin):
    client, root = local
    for method in ["get", "post", "options"]:
        response = getattr(client, method)(BASE, headers={"origin": origin})
        assert response.status_code == 403
        assert response.json()["detail"]["code"] == "origin_forbidden"
        assert "access-control-allow-origin" not in response.headers
    assert not (root / "output").exists()


def test_unsupported_preflight_and_duplicate_origins_fail(local):
    client, root = local
    origin = "http://127.0.0.1:5173"
    for method, header in [("DELETE", "content-type"), ("POST", "authorization")]:
        response = client.options(
            BASE,
            headers={
                "origin": origin,
                "access-control-request-method": method,
                "access-control-request-headers": header,
            },
        )
        assert response.status_code == 403
    assert client.options(BASE).status_code == 403
    duplicate = client.get(BASE, headers=[("origin", origin), ("origin", "https://evil.example")])
    assert duplicate.status_code == 403
    assert not (root / "output").exists()


@pytest.mark.parametrize(
    "failure, status, code",
    [
        (PermissionError("/Users/private/secret"), 503, "storage_unavailable"),
        (ValueError("bad source /Users/private/secret"), 409, "source_unavailable"),
        (RuntimeError("internal /Users/private/secret"), 500, "draft_error"),
    ],
)
def test_internal_errors_never_expose_filesystem_details(local, monkeypatch, failure, status, code):
    client, root = local

    def fail(self, **kwargs):
        raise failure

    monkeypatch.setattr(DraftStore, "fork_rp1", fail)
    response = client.post(BASE, json=BODY, headers={"origin": "http://127.0.0.1:4173"})
    assert response.status_code == status
    assert response.json()["detail"]["code"] == code
    assert "private" not in response.text
    assert "Traceback" not in response.text
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:4173"
    assert not (root / "output").exists()


def test_source_drift_and_saved_snapshot_damage_are_visible_without_raw_paths(local):
    client, root = local
    first = client.post(BASE, json=BODY).json()
    source = root / rp1_inspection.SPEC
    before = source.read_bytes()
    source.write_bytes(before + b"\n# drift\n")
    blocked = client.post(BASE, json=BODY)
    assert blocked.status_code == 409
    assert "configs/" not in blocked.text
    assert client.get(f"{BASE}/{first['draft_id']}").status_code == 200
    snapshot = root / "output" / "design-drafts" / first["draft_id"] / "source.json"
    snapshot.write_text("broken JSON /Users/private")
    damaged = client.get(f"{BASE}/{first['draft_id']}")
    assert damaged.status_code == 409
    assert damaged.json()["detail"]["code"] == "draft_unavailable"
    assert "private" not in damaged.text
    assert hashlib.sha256(before).hexdigest() == rp1_inspection.PINS[rp1_inspection.SPEC]
