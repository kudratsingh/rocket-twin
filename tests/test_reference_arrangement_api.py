"""Read-only source metadata plus stateless bounded display placement commands."""

import copy
import json
import shutil
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.reference_arrangement import create_router
from src.vehicle import reference_parts

ROOT = Path(__file__).resolve().parents[1]
BASE = "/api/reference-arrangement"


@pytest.fixture
def setup(tmp_path):
    # Deliberately cold: the source-only API must work without ignored CAD assets.
    for path in reference_parts.SOURCE_PINS:
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / path, target)
    app = FastAPI()
    app.include_router(create_router(tmp_path))
    with TestClient(app) as client:
        yield client, tmp_path


def tiny(plan):
    return [
        {key: row[key] for key in ("reference_id", "definition_revision_sha256", "translation_mm")}
        for row in plan["instances"]
    ]


def add(client, state, index):
    definition = state["catalog"]["definitions"][index]
    return client.post(
        BASE,
        json={
            "instances": tiny(state["plan"]),
            "command": {
                "type": "add-reference",
                "reference_id": definition["id"],
                "definition_revision_sha256": definition["revision_sha256"],
                "base_plan_revision": state["plan"]["revision_sha256"],
            },
        },
    )


def test_empty_add_two_translate_and_fresh_clear_are_unsaved_and_read_only(setup):
    client, root = setup
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    empty = client.get(BASE)
    assert empty.status_code == 200
    initial = empty.json()
    assert initial["plan"]["instances"] == []
    first = add(client, initial, 0)
    assert first.status_code == 200
    second = add(client, first.json(), 1)
    assert second.status_code == 200
    state = second.json()
    instance = state["plan"]["instances"][1]
    moved = client.post(
        BASE,
        json={
            "instances": tiny(state["plan"]),
            "command": {
                "type": "translate-reference",
                "instance_id": instance["id"],
                "translation_mm": [12.125, -20, 100],
                "base_plan_revision": state["plan"]["revision_sha256"],
            },
        },
    )
    assert moved.status_code == 200
    data = moved.json()
    assert data["plan"]["instances"][1]["translation_mm"] == [12.125, -20, 100]
    assert data["persisted"] is False and data["source_vehicle_changed"] is False
    assert data["plan"]["physical_inventory"] is None
    assert all(value is False for value in data["plan"]["readiness"].values())
    assert data["plan"]["checks"]["total_mass_kg"] is None
    assert all(not row["geometry_available"] for row in data["catalog"]["availability"].values())
    assert client.get(BASE).json() == initial  # No server head, history or stored arrangement.
    assert {
        str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()
    } == before
    assert not (root / "output").exists()


def test_stale_guard_duplicate_and_foreign_fields_do_not_mutate_base(setup):
    client, _ = setup
    empty = client.get(BASE).json()
    state = add(client, empty, 0).json()
    old = copy.deepcopy(state)
    response = add(client, state, 0)
    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "duplicate_reference"
    body = {
        "instances": tiny(state["plan"]),
        "command": {
            "type": "translate-reference",
            "instance_id": state["plan"]["instances"][0]["id"],
            "translation_mm": [0, 0, 10],
            "base_plan_revision": empty["plan"]["revision_sha256"],
        },
    }
    stale = client.post(BASE, json=body)
    assert stale.status_code == 409
    assert stale.json()["detail"]["current_plan_revision"] == state["plan"]["revision_sha256"]
    body["command"]["base_plan_revision"] = state["plan"]["revision_sha256"]
    for payload in (
        {**body, "draft_id": "caller-owned-path"},
        {**body, "source": {}},
        {**body, "command": {**body["command"], "scale": [2, 2, 2]}},
        {**body, "command": {**body["command"], "type": "connect"}},
        {**body, "instances": body["instances"] * 3},
    ):
        rejected = client.post(BASE, json=payload)
        assert rejected.status_code == 422
        assert "caller-owned-path" not in rejected.text
    assert state == old
    assert client.get(BASE).json() == empty


@pytest.mark.parametrize("position", [[True, 0, 0], [501, 0, 0], [0.0001, 0, 0], ["NaN", 0, 0]])
def test_invalid_numeric_positions_remain_unapplied(setup, position):
    client, _ = setup
    state = add(client, client.get(BASE).json(), 0).json()
    response = client.post(
        BASE,
        json={
            "instances": tiny(state["plan"]),
            "command": {
                "type": "translate-reference",
                "instance_id": state["plan"]["instances"][0]["id"],
                "translation_mm": position,
                "base_plan_revision": state["plan"]["revision_sha256"],
            },
        },
    )
    assert response.status_code == 422


def test_nonfinite_json_request_is_rejected_without_source_echo(setup):
    client, _ = setup
    state = add(client, client.get(BASE).json(), 0).json()
    payload = {
        "instances": tiny(state["plan"]),
        "command": {
            "type": "translate-reference",
            "instance_id": state["plan"]["instances"][0]["id"],
            "translation_mm": [float("nan"), 0, 0],
            "base_plan_revision": state["plan"]["revision_sha256"],
        },
    }
    response = client.post(
        BASE, content=json.dumps(payload), headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422


def test_origin_body_query_size_and_get_post_preflight_boundaries(setup):
    client, _ = setup
    origin = "http://127.0.0.1:5173"
    assert client.get(BASE, headers={"Origin": "https://foreign.invalid"}).status_code == 403
    assert client.get(BASE + "?source=caller").status_code == 422
    assert client.request("GET", BASE, content="{}").status_code == 422
    for method in ("GET", "POST"):
        response = client.options(
            BASE,
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": method,
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 204
        assert response.headers["access-control-allow-origin"] == origin
        assert response.headers["cache-control"] == "no-store"
    assert (
        client.options(
            BASE, headers={"Origin": origin, "Access-Control-Request-Method": "PATCH"}
        ).status_code
        == 403
    )
    oversized = {"instances": [], "command": {"type": "x" * 4096}}
    assert client.post(BASE, json=oversized).status_code == 413


def test_actual_workbench_mount_preserves_legacy_source_and_has_no_saved_head(setup):
    from src.api.workbench_app import create_app

    _, root = setup
    with TestClient(create_app(root, catalog=())) as client:
        before = client.get("/api/parts-bank").content
        empty = client.get(BASE)
        assert empty.status_code == 200
        assert add(client, empty.json(), 0).status_code == 200
        assert client.get(BASE).json() == empty.json()
        assert client.get("/api/parts-bank").content == before
        assert client.get("/api/vehicles").json()["vehicles"] == []
        assert client.get("/api/design-drafts").json() == {"drafts": [], "next_after": None}
        assert client.get("/docs").status_code == 200
        assert BASE not in client.get("/openapi.json").json()["paths"]
        assert not (root / "output").exists()
