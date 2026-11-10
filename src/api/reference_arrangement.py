"""Stateless geometry-reference arrangement; no owner library or CAD execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, NoReturn

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from src.api.design_drafts import ORIGINS, _error, _LocalDraftRoute
from src.api.reference_parts import _catalog
from src.vehicle import reference_arrangement as arrangements


class PreviewRequest(BaseModel):
    """Only tiny instance identifiers/placements and one explicit command."""

    model_config = ConfigDict(extra="forbid", strict=True)
    instances: list[dict[str, Any]] = Field(max_length=2)
    command: dict[str, Any]


async def _bounded_body(request: Request) -> None:
    if len(await request.body()) > 4096:
        raise _error(413, "request_too_large", "Arrangement requests are limited to 4096 bytes")


async def _empty_body(request: Request) -> None:
    if await request.body():
        raise _error(422, "invalid_request", "This arrangement request accepts no body")


def _reply(catalog: dict[str, Any], plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "catalog": catalog,
        "plan": plan,
        "action": "preview_uninstalled_reference_arrangement",
        "persisted": False,
        "source_vehicle_changed": False,
    }


def _arrangement_error(error: arrangements.ArrangementError) -> NoReturn:
    extra = {}
    if error.current_revision is not None:
        extra["current_plan_revision"] = error.current_revision
    if error.field is not None:
        extra["field"] = error.field
    raise _error(
        409 if error.code in ("stale_plan_revision", "invalid_catalog") else 422,
        error.code,
        str(error),
        **extra,
    )


def create_router(root: Path) -> APIRouter:
    """Read trusted reference metadata and reconstruct tiny state, never save it."""
    router = APIRouter(prefix="/api/reference-arrangement", route_class=_LocalDraftRoute)

    @router.get("", dependencies=[Depends(_empty_body)])
    def empty_arrangement() -> dict[str, Any]:
        catalog = _catalog(root)
        try:
            return _reply(catalog, arrangements.create_plan(catalog))
        except arrangements.ArrangementError as error:
            _arrangement_error(error)

    @router.post("", dependencies=[Depends(_bounded_body)])
    def arrangement_preview(body: PreviewRequest) -> dict[str, Any]:
        catalog = _catalog(root)
        try:
            base = arrangements.reconstruct_plan(catalog, body.instances)
            return _reply(catalog, arrangements.apply_command(catalog, base, body.command))
        except arrangements.ArrangementError as error:
            _arrangement_error(error)

    @router.options("", dependencies=[Depends(_empty_body)])
    def arrangement_preflight(request: Request) -> Response:
        requested = request.headers.get("access-control-request-method")
        raw_headers = request.headers.get("access-control-request-headers", "")
        headers = [value.strip().lower() for value in raw_headers.split(",") if value.strip()]
        if (
            request.headers.get("origin") not in ORIGINS
            or requested not in ("GET", "POST")
            or len(request.headers.getlist("access-control-request-method")) != 1
            or len(request.headers.getlist("access-control-request-headers")) > 1
            or len(headers) != len(set(headers))
            or not set(headers) <= {"content-type"}
        ):
            raise _error(403, "preflight_forbidden", "Only local arrangement GET/POST is supported")
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Methods": "GET, POST",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    return router
