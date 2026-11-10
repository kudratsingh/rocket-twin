"""New draft composition preserves existing API routes and their CORS behavior."""

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from src.api import rp1_inspection
from src.api.workbench_app import create_app


def test_existing_api_and_docs_remain_mounted_without_creating_storage(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path, catalog=())) as client:
        response = client.get("/api/vehicles")
        assert response.status_code == 200
        assert response.json()["vehicles"] == []
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        assert not (tmp_path / "output/design-drafts").exists()
        assert client.get("/api/design-drafts").json() == {"drafts": [], "next_after": None}
        assert not (tmp_path / "output/design-drafts").exists()


def test_draft_cors_is_not_intercepted_by_the_base_get_post_boundary(tmp_path: Path) -> None:
    with TestClient(create_app(tmp_path, catalog=())) as client:
        response = client.options(
            "/api/design-drafts/013e3333-1234-4abc-8def-123456789abc",
            headers={
                "Origin": "http://127.0.0.1:5173",
                "Access-Control-Request-Method": "PATCH",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 204
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
        assert "PATCH" in response.headers["access-control-allow-methods"]
        assert (
            client.get(
                "/api/design-drafts", headers={"Origin": "https://foreign.invalid"}
            ).status_code
            == 403
        )
        base = client.options(
            "/api/vehicles",
            headers={"Origin": "http://127.0.0.1:5173", "Access-Control-Request-Method": "PATCH"},
        )
        assert base.status_code == 400
        assert (
            client.get("/api/vehicles", headers={"Origin": "http://127.0.0.1:5173"}).headers[
                "access-control-allow-origin"
            ]
            == "http://127.0.0.1:5173"
        )


def test_stateless_intents_route_before_base_app_and_preserve_saved_bytes(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(repo / relative, target)
    origin = {"Origin": "http://127.0.0.1:5173"}
    with TestClient(create_app(tmp_path, catalog=())) as client:
        response = client.post(
            "/api/design-drafts",
            headers=origin,
            json={
                "source_configuration_id": rp1_inspection.ID,
                "source_specification_sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
                "label": "Isolated integrated intent validation",
            },
        )
        assert response.status_code == 201
        saved = response.json()
        folder = tmp_path / "output/design-drafts" / saved["draft_id"]
        before = {
            str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob("*") if p.is_file()
        }
        path = f"/api/design-drafts/{saved['draft_id']}/intent-preview"
        initial = client.get(path, headers=origin)
        assert initial.status_code == 200
        base = initial.json()
        result = client.post(
            path,
            headers=origin,
            json={
                "base_draft_revision": saved["revision_sha256"],
                "base_overlay_revision": base["revision_sha256"],
                "excluded_occurrence_ids": [],
                "type": "exclude-source-occurrence",
                "occurrence_id": "fin_set",
            },
        )
        assert result.status_code == 200
        assert result.json()["excluded_occurrence_ids"] == ["fin_set"]
        assert result.json()["checks"]["mass_removal_credit_kg"] is None
        assert result.json()["readiness"]["simulation_eligible"] is False
        assert len(result.json()["base"]["source"]["parts_bank"]["instances"]) == 55
        assert result.headers["access-control-allow-origin"] == origin["Origin"]
        assert (
            client.options(
                path,
                headers={
                    **origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                },
            ).status_code
            == 204
        )
        assert client.get("/api/vehicles").status_code == 200
        assert before == {
            str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob("*") if p.is_file()
        }
