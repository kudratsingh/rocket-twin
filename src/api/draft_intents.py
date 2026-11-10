"""Stateless, read-only planning preview from server-owned saved source forks.

Clients send only opaque revisions and bounded occurrence IDs. No client source
or overlay JSON is accepted; no metadata, source, command or overlay is saved.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from src.api.design_drafts import ORIGINS, DraftId, Revision, _error, _LocalDraftRoute
from src.vehicle.design_drafts import DraftStore
from src.vehicle.draft_composition import CompositionError, apply_command, create_overlay

OccurrenceId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]{0,79}$")]
PATH = "/{draft_id}/intent-preview"
MAX_BODY_BYTES = 16 * 1024


class IntentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    base_draft_revision: Revision
    base_overlay_revision: Revision
    excluded_occurrence_ids: list[OccurrenceId] = Field(max_length=55)
    type: Literal["exclude-source-occurrence", "restore-source-occurrence"]
    occurrence_id: OccurrenceId


def _unique_fields(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Repeated JSON field")
        value[key] = item
    return value


async def _request_fields(request: Request) -> None:
    """Reject duplicate JSON names rather than silently accepting the last value."""
    body = await request.body()
    if len(body) > MAX_BODY_BYTES:
        raise _error(422, "invalid_request", "Intent preview request exceeds its size bound")
    try:
        json.loads(body, object_pairs_hook=_unique_fields)
    except (ValueError, UnicodeDecodeError):
        raise _error(
            422, "invalid_request", "Intent JSON is malformed or has repeated fields"
        ) from None


async def _empty_body(request: Request) -> None:
    if await request.body():
        raise _error(422, "invalid_request", "This intent preview method accepts no request body")


def _composition_error(error: CompositionError) -> HTTPException:
    messages = {
        "invalid_saved_revision": "The saved draft revision could not be verified",
        "source_unavailable": "The frozen saved source is unavailable or differs",
        "invalid_overlay": "The server planning overlay could not be verified",
        "invalid_command": "Only a valid exclude or restore intent command is supported",
        "unknown_occurrence": "Choose an exact original source occurrence ID",
        "duplicate_exclusion": "That occurrence already has an exclusion intent",
        "stale_overlay_revision": "Reload the preview before applying this intent",
    }
    code = error.code if error.code in messages else "intent_unavailable"
    status = 422 if code in ("invalid_command", "unknown_occurrence") else 409
    extra = {}
    if code == "stale_overlay_revision" and error.current_revision is not None:
        extra["current_overlay_revision"] = error.current_revision
    return _error(status, code, messages.get(code, "This intent preview is unavailable"), **extra)


def _reconstruct(current: dict[str, Any], excluded_ids: list[str]) -> dict[str, Any]:
    if len(set(excluded_ids)) != len(excluded_ids):
        raise _error(
            422, "duplicate_exclusions", "Submitted exclusion occurrence IDs must be unique"
        )
    overlay = create_overlay(current)
    source_order = [row["id"] for row in overlay["base"]["source"]["parts_bank"]["instances"]]
    if any(part_id not in source_order for part_id in excluded_ids):
        raise _error(
            422, "unknown_occurrence", "Exclusion intents must name original source occurrences"
        )
    for part_id in source_order:
        if part_id in excluded_ids:
            overlay = apply_command(
                overlay,
                {
                    "type": "exclude-source-occurrence",
                    "occurrence_id": part_id,
                    "base_overlay_revision": overlay["revision_sha256"],
                },
            )
    return overlay


def create_router(root: Path) -> APIRouter:
    """Read-only factory; primary owns mounting ahead of the existing draft router."""
    store = DraftStore(root)
    # Reuse exact-origin, no-query, safe-validation/error and no-store behavior.
    # These endpoint names intentionally differ from the metadata list/read names.
    router = APIRouter(prefix="/api/design-drafts", route_class=_LocalDraftRoute)

    @router.get(PATH, dependencies=[Depends(_empty_body)])
    def get_intent_preview(draft_id: DraftId) -> dict[str, Any]:
        try:
            return create_overlay(store.read(draft_id))
        except CompositionError as error:
            raise _composition_error(error) from None

    @router.post(PATH, dependencies=[Depends(_request_fields)])
    def apply_intent_preview(draft_id: DraftId, body: IntentRequest) -> dict[str, Any]:
        current = store.read(draft_id)
        if body.base_draft_revision != current["revision_sha256"]:
            raise _error(
                409,
                "stale_draft_revision",
                "Reload the current saved draft before previewing intents",
                current_draft_revision=current["revision_sha256"],
            )
        try:
            overlay = _reconstruct(current, body.excluded_occurrence_ids)
            return apply_command(
                overlay,
                {
                    "type": body.type,
                    "occurrence_id": body.occurrence_id,
                    "base_overlay_revision": body.base_overlay_revision,
                },
            )
        except CompositionError as error:
            raise _composition_error(error) from None

    @router.options(PATH, dependencies=[Depends(_empty_body)])
    def intent_preflight(draft_id: DraftId, request: Request) -> Response:
        if request.headers.get("origin") not in ORIGINS:
            raise _error(403, "origin_forbidden", "A local preview origin is required")
        requested = request.headers.get("access-control-request-headers", "")
        headers = [item.strip().lower() for item in requested.split(",") if item.strip()]
        if (
            request.headers.get("access-control-request-method") not in {"GET", "POST"}
            or len(request.headers.getlist("access-control-request-method")) != 1
            or len(request.headers.getlist("access-control-request-headers")) > 1
            or len(headers) != len(set(headers))
            or not set(headers) <= {"content-type"}
        ):
            raise _error(403, "preflight_forbidden", "Unsupported intent method or request header")
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Methods": "GET, POST",
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    return router
