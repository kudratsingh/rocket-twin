"""New draft composition preserves existing API routes and their CORS behavior."""

from pathlib import Path

from fastapi.testclient import TestClient

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
