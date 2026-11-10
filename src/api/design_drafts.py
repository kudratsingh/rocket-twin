"""Standalone local draft router; never imported into the frozen base app here.

Construct with a trusted server root. Requests can supply only exact source IDs,
opaque draft IDs/revisions and metadata. No request owns a filesystem/asset path.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from pathlib import Path
from typing import Annotated, Any, Self

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from starlette.responses import JSONResponse

from src.api import rp1_inspection
from src.vehicle.design_drafts import DraftError, DraftNotFound, DraftStore, RevisionConflict

ORIGINS = frozenset(
    f"http://{host}:{port}" for host in ("localhost", "127.0.0.1") for port in (5173, 4173)
)
UUID4_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
HASH_PATTERN = r"^[0-9a-f]{64}$"
DraftId = Annotated[str, Field(pattern=UUID4_PATTERN)]
Revision = Annotated[str, Field(pattern=HASH_PATTERN)]
KNOWN_FIELDS = frozenset(
    (
        "body",
        "query",
        "path",
        "label",
        "notes",
        "draft_id",
        "revision",
        "base_revision",
        "source_configuration_id",
        "source_specification_sha256",
        "limit",
        "after",
    )
)


def _error(status: int, code: str, message: str, **extra: Any) -> HTTPException:
    return HTTPException(status, {"code": code, "message": message, **extra})


def _text(value: str, *, label: bool = False) -> str:
    if label and not value.strip():
        raise ValueError("Label cannot be blank")
    if any(ord(c) < 32 and c not in ("\n", "\t") for c in value):
        raise ValueError("Unsupported control character")
    return value


class ForkRequest(BaseModel):
    """Explicit confirmation of the exact current source, not a selectable path."""

    model_config = ConfigDict(extra="forbid", strict=True)
    source_configuration_id: str
    source_specification_sha256: str
    label: str = Field(min_length=1, max_length=160)
    notes: str = Field(default="", max_length=8000)

    @field_validator("source_configuration_id")
    @classmethod
    def exact_source(cls, value: str) -> str:
        if value != rp1_inspection.ID:
            raise ValueError("Only the current frozen RP1 source is supported")
        return value

    @field_validator("source_specification_sha256")
    @classmethod
    def exact_specification(cls, value: str) -> str:
        if value != rp1_inspection.PINS[rp1_inspection.SPEC]:
            raise ValueError("The exact frozen RP1 specification hash is required")
        return value

    @field_validator("label", "notes")
    @classmethod
    def safe_text(cls, value: str, info: Any) -> str:
        return _text(value, label=info.field_name == "label")


class MetadataRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    base_revision: Revision
    label: str | None = Field(default=None, min_length=1, max_length=160)
    notes: str | None = Field(default=None, max_length=8000)

    @model_validator(mode="after")
    def supplied_metadata(self) -> Self:
        supplied = self.model_fields_set & {"label", "notes"}
        if not supplied:
            raise ValueError("Supply label or notes")
        for field in supplied:
            value = getattr(self, field)
            if value is None:
                raise ValueError("Metadata cannot be null")
            _text(value, label=field == "label")
        return self


class _LocalDraftRoute(APIRoute):
    """Origin and safe-error boundary scoped to these routes, including OPTIONS."""

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        original = super().get_route_handler()
        allowed_queries = {"limit", "after"} if self.name == "list_drafts" else {"revision"}
        if self.name not in ("list_drafts", "read_draft"):
            allowed_queries = set()

        async def process(request: Request) -> Response:
            origins = request.headers.getlist("origin")
            if origins and (len(origins) != 1 or origins[0] not in ORIGINS):
                raise _error(
                    403, "origin_forbidden", "This browser origin cannot access local drafts"
                )
            keys = list(request.query_params.keys())
            if any(
                k not in allowed_queries or len(request.query_params.getlist(k)) != 1 for k in keys
            ):
                raise _error(
                    422, "invalid_request", "Unsupported or repeated query field", fields=["query"]
                )
            try:
                response = await original(request)
            except RequestValidationError as exc:
                # Never echo input values, filesystem exception text or unknown
                # caller-chosen field names into error responses.
                fields = sorted(
                    {
                        str(part)
                        for issue in exc.errors()
                        for part in issue["loc"]
                        if part in KNOWN_FIELDS
                    }
                )
                raise _error(
                    422,
                    "invalid_request",
                    "Request fields are invalid or unsupported",
                    fields=fields,
                ) from None
            except RevisionConflict as exc:
                raise _error(
                    409,
                    "stale_revision",
                    "Reload the current draft before saving",
                    current_revision=exc.current_revision,
                ) from None
            except DraftNotFound:
                raise _error(404, "draft_not_found", "Draft or revision not found") from None
            except DraftError:
                raise _error(
                    409,
                    "draft_unavailable",
                    "Draft storage or saved content is unsafe, damaged or exceeds its limits",
                ) from None
            except (ValueError, TypeError):
                raise _error(
                    409, "source_unavailable", "The pinned draft source could not be verified"
                ) from None
            except OSError:
                raise _error(
                    503,
                    "storage_unavailable",
                    "Local draft storage is unavailable; no save is confirmed",
                ) from None
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001 -- API boundary must not leak debug tracebacks.
                raise _error(
                    500, "draft_error", "The draft operation could not be completed"
                ) from None
            return response

        async def handler(request: Request) -> Response:
            try:
                response = await process(request)
            except HTTPException as exc:
                response = JSONResponse(
                    {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
                )
            # Exact route-scoped preview origins only; no app CORS middleware or
            # persistent permission changes, wildcard or credentials are added.
            origins = request.headers.getlist("origin")
            if len(origins) == 1 and origins[0] in ORIGINS:
                response.headers["Access-Control-Allow-Origin"] = origins[0]
                response.headers["Vary"] = "Origin"
            response.headers["Cache-Control"] = "no-store"
            return response

        return handler


def create_router(root: Path) -> APIRouter:
    """Create a router over a trusted root; construction does not write storage."""
    store = DraftStore(root)
    router = APIRouter(prefix="/api/design-drafts", route_class=_LocalDraftRoute)

    @router.post("", status_code=201)
    def fork_draft(body: ForkRequest) -> dict[str, Any]:
        return store.fork_rp1(label=body.label, notes=body.notes)

    @router.get("")
    def list_drafts(
        limit: Annotated[int, Query(ge=1, le=100)] = 25,
        after: Annotated[str | None, Query(pattern=UUID4_PATTERN)] = None,
    ) -> dict[str, Any]:
        return store.list_drafts(limit=limit, after=after)

    @router.get("/{draft_id}")
    def read_draft(
        draft_id: DraftId,
        revision: Annotated[str | None, Query(pattern=HASH_PATTERN)] = None,
    ) -> dict[str, Any]:
        return store.read(draft_id, revision=revision)

    @router.patch("/{draft_id}")
    def save_metadata(draft_id: DraftId, body: MetadataRequest) -> dict[str, Any]:
        current = store.read(draft_id)
        # The store compares this explicit base against its locked current head;
        # the read above never converts stale intent into a successful write.
        return store.save_metadata(
            draft_id,
            base_revision=body.base_revision,
            label=current["label"] if body.label is None else body.label,
            notes=current["notes"] if body.notes is None else body.notes,
        )

    @router.options("")
    @router.options("/{draft_id}")
    def preflight(request: Request) -> Response:
        if request.headers.get("origin") not in ORIGINS:
            raise _error(403, "origin_forbidden", "A local preview origin is required")
        method = request.headers.get("access-control-request-method", "")
        supported = {"GET", "PATCH"} if request.path_params else {"GET", "POST"}
        requested = request.headers.get("access-control-request-headers", "")
        headers = {h.strip().lower() for h in requested.split(",") if h.strip()}
        if method not in supported or not headers <= {"content-type"}:
            raise _error(403, "preflight_forbidden", "Unsupported draft method or request header")
        return Response(
            status_code=204,
            headers={
                "Access-Control-Allow-Methods": ", ".join(sorted(supported)),
                "Access-Control-Allow-Headers": "Content-Type",
            },
        )

    return router
