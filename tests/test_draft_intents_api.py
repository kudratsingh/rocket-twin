"""Real isolated server records, stateless intent replay and exact local origins."""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api import draft_intents as api
from src.api import rp1_inspection
from src.vehicle import draft_composition
from src.vehicle.design_drafts import DraftStore
from src.vehicle.draft_composition import apply_command, create_overlay

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def local(tmp_path):
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    store = DraftStore(tmp_path)
    saved = store.fork_rp1(label="Isolated API source fork", notes="Temporary data only")
    app = FastAPI(debug=True)
    app.include_router(api.create_router(tmp_path))
    return TestClient(app), store, saved


def url(saved):
    return f"/api/design-drafts/{saved['draft_id']}/intent-preview"


def body(saved, overlay, kind="exclude-source-occurrence", occurrence="fin_set"):
    return {
        "base_draft_revision": saved["revision_sha256"],
        "base_overlay_revision": overlay["revision_sha256"],
        "excluded_occurrence_ids": overlay["excluded_occurrence_ids"],
        "type": kind,
        "occurrence_id": occurrence,
    }


def files(root):
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def assert_unresolved(value):
    assert len(value["base"]["source"]["parts_bank"]["instances"]) == 55
    assert value["preview"]["source_occurrences"] == 55
    assert value["preview"]["effective_inventory"] is None
    assert value["checks"]["total_mass_kg"] is None
    assert value["checks"]["mass_removal_credit_kg"] is None
    assert value["checks"]["cg_m"] is None
    assert value["checks"]["inertia_kg_m2"] is None
    assert all(
        value["readiness"][key] is False
        for key in (
            "resolve_available",
            "resolved_candidate",
            "simulation_eligible",
            "engineering_accepted",
            "flight_ready",
        )
    )


def test_get_exclude_restore_are_stateless_and_do_not_add_or_change_files(local):
    client, store, saved = local
    before = files(store.root)
    initial = client.get(url(saved))
    assert initial.status_code == 200
    assert initial.headers["cache-control"] == "no-store"
    initial = initial.json()
    assert initial == create_overlay(saved)
    excluded = client.post(url(saved), json=body(saved, initial))
    assert excluded.status_code == 200
    excluded = excluded.json()
    assert excluded["excluded_occurrence_ids"] == ["fin_set"]
    assert excluded["base"] == saved
    assert excluded["preview"]["removed_functions"][0]["function"]
    assert excluded["preview"]["removed_functions"][0]["source_occurrence"]["group_count"] == 3
    restored = client.post(url(saved), json=body(saved, excluded, "restore-source-occurrence"))
    assert restored.status_code == 200
    assert restored.json() == initial
    # GET always returns the current saved fork with no persistent intents.
    assert client.get(url(saved)).json() == initial
    assert store.read(saved["draft_id"]) == saved
    assert files(store.root) == before
    assert_unresolved(excluded)
    assert_unresolved(restored.json())


def test_replay_is_source_ordered_and_opaque_overlay_revision_is_not_client_source_json(local):
    client, _, saved = local
    initial = create_overlay(saved)
    first = client.post(url(saved), json=body(saved, initial, occurrence="motor_retainer")).json()
    second = client.post(url(saved), json=body(saved, first)).json()
    assert second["excluded_occurrence_ids"] == ["fin_set", "motor_retainer"]
    request = body(saved, second, "restore-source-occurrence", "motor_retainer")
    request["excluded_occurrence_ids"].reverse()
    response = client.post(url(saved), json=request)
    assert response.status_code == 200
    assert response.json()["excluded_occurrence_ids"] == ["fin_set"]
    expected = apply_command(
        initial,
        {
            "type": "exclude-source-occurrence",
            "occurrence_id": "fin_set",
            "base_overlay_revision": initial["revision_sha256"],
        },
    )
    assert response.json()["revision_sha256"] == expected["revision_sha256"]
    assert_unresolved(response.json())


def test_stale_metadata_and_stale_overlay_return_distinct_recoverable_hashes(local):
    client, store, saved = local
    initial = client.get(url(saved)).json()
    stale = client.post(
        url(saved), json={**body(saved, initial), "base_overlay_revision": "0" * 64}
    )
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_overlay_revision"
    assert stale.json()["detail"]["current_overlay_revision"] == initial["revision_sha256"]
    updated = store.save_metadata(
        saved["draft_id"],
        base_revision=saved["revision_sha256"],
        label="Changed metadata",
        notes="New actual saved revision",
    )
    before = files(store.root)
    stale = client.post(url(saved), json=body(saved, initial))
    assert stale.status_code == 409
    assert stale.json()["detail"]["code"] == "stale_draft_revision"
    assert stale.json()["detail"]["current_draft_revision"] == updated["revision_sha256"]
    assert client.get(url(saved)).json()["base"] == updated
    assert files(store.root) == before


@pytest.mark.parametrize(
    "changes",
    [
        {"base_draft_revision": "bad"},
        {"base_overlay_revision": None},
        {"excluded_occurrence_ids": ["fin_set", "fin_set"]},
        {"excluded_occurrence_ids": ["unknown"]},
        {"excluded_occurrence_ids": ["fin_set"] * 56},
        {"excluded_occurrence_ids": "fin_set"},
        {"excluded_occurrence_ids": [42]},
        {"type": "add"},
        {"type": "connect"},
        {"type": "fly"},
        {"occurrence_id": "../../configs/private"},
        {"occurrence_id": "unknown"},
        {"source": {"path": "/Users/private"}},
        {"overlay": {}},
        {"label": "Cannot save"},
    ],
)
def test_invalid_commands_paths_fields_types_and_exclusion_ids_rejected(local, changes):
    client, store, saved = local
    overlay = create_overlay(saved)
    before = files(store.root)
    response = client.post(url(saved), json={**body(saved, overlay), **changes})
    assert response.status_code == 422
    assert "private" not in response.text
    assert files(store.root) == before


def test_duplicate_exclusion_restore_noop_unknown_queries_and_repeated_json_fields(local):
    client, store, saved = local
    initial = create_overlay(saved)
    noop = client.post(url(saved), json=body(saved, initial, "restore-source-occurrence", "body"))
    assert noop.status_code == 200 and noop.json() == initial
    excluded = client.post(url(saved), json=body(saved, initial)).json()
    duplicate = client.post(url(saved), json=body(saved, excluded))
    assert duplicate.status_code == 409
    assert duplicate.json()["detail"]["code"] == "duplicate_exclusion"
    for suffix in [
        "?revision=" + saved["revision_sha256"],
        "?limit=1&limit=2",
        "?path=/Users/private",
    ]:
        response = client.get(url(saved) + suffix)
        assert response.status_code == 422 and "private" not in response.text
    request = json.dumps(body(saved, initial))
    duplicate_json = request[:-1] + ',"occurrence_id":"motor"}'
    repeated = client.post(
        url(saved), content=duplicate_json, headers={"content-type": "application/json"}
    )
    assert repeated.status_code == 422
    assert repeated.json()["detail"]["code"] == "invalid_request"
    assert (
        client.post(
            url(saved),
            content='{"source":/Users/private}',
            headers={"content-type": "application/json"},
        ).status_code
        == 422
    )
    assert store.read(saved["draft_id"]) == saved


def test_invalid_unknown_uuid_and_source_drift_are_sanitized(local):
    client, store, saved = local
    for draft_id in ["not-a-uuid", str(uuid4()).upper()]:
        assert client.get(f"/api/design-drafts/{draft_id}/intent-preview").status_code == 422
        assert (
            client.options(
                f"/api/design-drafts/{draft_id}/intent-preview",
                headers={
                    "origin": "http://localhost:5173",
                    "access-control-request-method": "GET",
                },
            ).status_code
            == 422
        )
    assert client.request("GET", url(saved), json={"source": "not accepted"}).status_code == 422
    unknown = client.get(f"/api/design-drafts/{uuid4()}/intent-preview")
    assert unknown.status_code == 404 and unknown.json()["detail"]["code"] == "draft_not_found"
    source = store.root / "output" / "design-drafts" / saved["draft_id"] / "source.json"
    data = json.loads(source.read_text())
    data["configuration_id"] = "foreign"
    source.write_text(json.dumps(data))
    response = client.get(url(saved))
    assert response.status_code == 409 and response.json()["detail"]["code"] == "draft_unavailable"
    assert str(store.root) not in response.text


@pytest.mark.parametrize("origin", sorted(api.ORIGINS))
def test_allowed_origin_success_error_and_scoped_preflight(local, origin):
    client, _, saved = local
    headers = {"origin": origin}
    get = client.get(url(saved), headers=headers)
    assert get.status_code == 200 and get.headers["access-control-allow-origin"] == origin
    invalid = client.post(url(saved), json={}, headers=headers)
    assert invalid.status_code == 422 and invalid.headers["access-control-allow-origin"] == origin
    for method in ("GET", "POST"):
        preflight = client.options(
            url(saved),
            headers={
                **headers,
                "access-control-request-method": method,
                "access-control-request-headers": "Content-Type",
            },
        )
        assert preflight.status_code == 204
        assert preflight.headers["access-control-allow-methods"] == "GET, POST"
        assert preflight.headers["access-control-allow-origin"] == origin
        assert "access-control-allow-credentials" not in preflight.headers
    denied = client.options(
        url(saved), headers={**headers, "access-control-request-method": "PATCH"}
    )
    assert denied.status_code == 403
    denied = client.options(
        url(saved),
        headers={
            **headers,
            "access-control-request-method": "POST",
            "access-control-request-headers": "authorization",
        },
    )
    assert denied.status_code == 403


@pytest.mark.parametrize(
    "origin",
    [
        "https://evil.example",
        "null",
        "http://localhost:8080",
        "http://localhost:5173/",
        "http://127.0.0.1:4173.evil",
    ],
)
def test_forbidden_origins_cannot_read_or_post_preview(local, origin):
    client, store, saved = local
    before = files(store.root)
    for method in ("get", "post", "options"):
        response = getattr(client, method)(url(saved), headers={"origin": origin})
        assert response.status_code == 403
        assert "access-control-allow-origin" not in response.headers
    assert files(store.root) == before


def test_duplicate_origins_and_raw_filesystem_errors_do_not_escape(local, monkeypatch):
    client, _, saved = local
    response = client.get(
        url(saved),
        headers=[("origin", "http://localhost:5173"), ("origin", "https://evil.example")],
    )
    assert response.status_code == 403

    def fail(*args, **kwargs):
        raise PermissionError("/Users/private/storage")

    monkeypatch.setattr(DraftStore, "read", fail)
    response = client.get(url(saved), headers={"origin": "http://localhost:4173"})
    assert response.status_code == 503
    assert "private" not in response.text and "Traceback" not in response.text
    assert response.headers["access-control-allow-origin"] == "http://localhost:4173"


@pytest.mark.skipif(
    os.environ.get("RUN_DRAFT_INTENT_REPLAY_PROBE") != "1",
    reason="One explicitly bounded source-JSON timing probe, run separately",
)
def test_55_replay_timing_probe(local):
    client, store, saved = local
    # All55 intentions reconstructed; one restore then leaves54. No physics/CAD.
    ids = [row["id"] for row in saved["source"]["parts_bank"]["instances"]]
    # Prepare the expected server identity directly, without a second55-replay.
    # This test-only Python value is never submitted; the request carries tiny IDs.
    expected = draft_composition._assemble(saved, ids)
    request = {
        "base_draft_revision": saved["revision_sha256"],
        "base_overlay_revision": expected["revision_sha256"],
        "excluded_occurrence_ids": ids,
        "type": "restore-source-occurrence",
        "occurrence_id": ids[0],
    }
    before = files(store.root)
    start_wall, start_cpu = time.monotonic(), time.process_time()
    response = client.post(url(saved), json=request)
    wall, cpu = time.monotonic() - start_wall, time.process_time() - start_cpu
    print(
        f"55-intent source-JSON replay: wall={wall:.6f}s CPU={cpu:.6f}s status={response.status_code}"
    )
    assert (
        wall < 20 and cpu < 10
    ), "Declared replay bound exceeded; stop and report, no automatic optimization"
    assert response.status_code == 200
    assert len(response.json()["excluded_occurrence_ids"]) == 54
    assert_unresolved(response.json())
    assert files(store.root) == before
