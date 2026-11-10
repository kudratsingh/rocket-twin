"""Standalone read-only metadata API for two geometry-only reference definitions.

No asset bytes, parameters, instances, connections, source edits or generation
are served. Primary owns mounting this router into the loopback workbench.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Request, Response
from pydantic import Field

from src.api.design_drafts import ORIGINS, Revision, _error, _LocalDraftRoute
from src.vehicle import reference_parts as references

ReferenceId = Annotated[str, Field(pattern=r"^[a-z0-9-]{1,60}:[a-z0-9-]{1,80}$")]
DETAIL = "/{reference_id}/{revision}"


async def _empty_body(request: Request) -> None:
    if await request.body():
        raise _error(422, "invalid_request", "Reference inspection accepts no request body")


def _catalog(root: Path) -> dict[str, Any]:
    try:
        return references.build(root)
    except (references.ReferencePartsError, FileNotFoundError):
        raise _error(
            409,
            "reference_source_unavailable",
            "Pinned reference source, frame or registered cache could not be verified; no regeneration attempted",
        ) from None


def _preflight(request: Request) -> Response:
    if request.headers.get("origin") not in ORIGINS:
        raise _error(403, "origin_forbidden", "A local preview origin is required")
    requested = request.headers.get("access-control-request-headers", "")
    headers = [item.strip().lower() for item in requested.split(",") if item.strip()]
    if (
        request.headers.get("access-control-request-method") != "GET"
        or len(request.headers.getlist("access-control-request-method")) != 1
        or len(request.headers.getlist("access-control-request-headers")) > 1
        or len(headers) != len(set(headers))
        or not set(headers) <= {"content-type"}
    ):
        raise _error(
            403,
            "preflight_forbidden",
            "Only GET reference inspection and Content-Type are supported",
        )
    return Response(
        status_code=204,
        headers={
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        },
    )


def create_router(root: Path) -> APIRouter:
    """Create route declarations without reading/writing source or cache files."""
    router = APIRouter(prefix="/api/reference-parts", route_class=_LocalDraftRoute)

    @router.get("", dependencies=[Depends(_empty_body)])
    def reference_catalog() -> dict[str, Any]:
        return _catalog(root)

    @router.get(DETAIL, dependencies=[Depends(_empty_body)])
    def reference_detail(reference_id: ReferenceId, revision: Revision) -> dict[str, Any]:
        catalog = _catalog(root)
        row = next((item for item in catalog["definitions"] if item["id"] == reference_id), None)
        if row is None:
            raise _error(404, "reference_not_found", "Unknown registered geometry reference ID")
        if revision != row["revision_sha256"]:
            raise _error(
                409,
                "reference_revision_mismatch",
                "Reload the reference catalog before inspecting this revision",
                current_revision=row["revision_sha256"],
            )
        # Exact server nominal values only; the request owns no parameter data.
        try:
            selected = references.select_reference(
                root, reference_id, revision, row["parameters_mm"]
            )
        except (references.ReferencePartsError, FileNotFoundError):
            raise _error(
                409,
                "reference_source_unavailable",
                "Reference source or cache changed during inspection; reload the catalog",
            ) from None
        return {
            **selected,
            "catalog_id": catalog["id"],
            "catalog_revision_sha256": catalog["revision_sha256"],
            "scope": catalog["scope"],
        }

    @router.options("", dependencies=[Depends(_empty_body)])
    def catalog_preflight(request: Request) -> Response:
        return _preflight(request)

    @router.options(DETAIL, dependencies=[Depends(_empty_body)])
    def detail_preflight(
        reference_id: ReferenceId, revision: Revision, request: Request
    ) -> Response:
        return _preflight(request)

    return router
