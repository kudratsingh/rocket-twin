"""Local RP1 fork/history foundation; no composition, resolution, CAD or physics.

Only a trusted server supplies ``root``. Request data consists of opaque IDs,
revision hashes, labels and notes, never filesystem or asset paths. All writes
stay below root/output/design-drafts using no-follow directory descriptors.
"""

from __future__ import annotations

import copy
import fcntl
import hashlib
import json
import os
import re
import stat
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import yaml

from src.api import parts_bank, rp1_inspection

STORAGE = ("output", "design-drafts")
MAX_JSON_BYTES = 8 * 1024 * 1024
MAX_DRAFTS = 1000
MAX_HISTORY = 1000
HASH = re.compile(r"[0-9a-f]{64}\Z")
READINESS = {
    "status": "unresolved_source_fork",
    "resolved_candidate": False,
    "simulation_eligible": False,
    "engineering_accepted": False,
    "flight_ready": False,
    "blockers": [
        "Source fork only; no candidate resolver or simulation admission is implemented",
        "Whole-body physical inertia and complete installed geometry are unavailable",
        "Source product conflicts, estimates and missing geometry remain unresolved",
        "Installed fin, recovery, thermal, physical, WO-10 and flight gates remain open",
    ],
}


class DraftError(ValueError):
    """Invalid request, unsafe storage or damaged snapshot; map to a useful API error."""


class DraftNotFound(DraftError):
    """An exact, valid server ID or revision does not exist."""


class RevisionConflict(DraftError):
    """The caller must reload and reconcile against ``current_revision``."""

    def __init__(self, current_revision: str):
        self.current_revision = current_revision
        super().__init__("Stale draft revision; reload before saving")


def _bytes(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_bytes(value)).hexdigest()


def _id(value: str) -> str:
    try:
        valid = isinstance(value, str) and str(UUID(value, version=4)) == value
        valid = valid and UUID(value).version == 4
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise DraftError("Expected an exact server-generated UUID4 draft ID")
    return value


def _hash(value: object) -> str:
    if not isinstance(value, str) or HASH.fullmatch(value) is None:
        raise DraftError("Expected a lowercase SHA-256 revision")
    return value


def _text(value: str, field: str, maximum: int, *, required: bool = False) -> str:
    if not isinstance(value, str) or len(value) > maximum:
        raise DraftError(f"{field} must be text of at most {maximum} characters")
    if any(ord(c) < 32 and c not in ("\n", "\t") for c in value):
        raise DraftError(f"{field} contains unsupported control characters")
    if required and not value.strip():
        raise DraftError(f"{field} cannot be blank")
    return value


def _now() -> str:
    return datetime.now(UTC).isoformat()


@contextmanager
def _directory(parent: int, name: str, *, create: bool = False) -> Iterator[int]:
    if create:
        try:
            os.mkdir(name, mode=0o700, dir_fd=parent)
        except FileExistsError:
            pass
    try:
        fd = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    except FileNotFoundError as exc:
        raise DraftNotFound("Draft storage or ID not found") from exc
    except OSError as exc:
        raise DraftError("Draft directory must be a real directory, never a symlink") from exc
    try:
        yield fd
    finally:
        os.close(fd)


def _regular(fd: int) -> None:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise DraftError("Draft files must be ordinary unlinked-to-other-files regular files")


def _read(directory: int, name: str) -> dict[str, Any]:
    try:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    except FileNotFoundError as exc:
        raise DraftNotFound("Draft snapshot or revision not found") from exc
    except OSError as exc:
        raise DraftError("Unsafe draft file") from exc
    try:
        _regular(fd)
        if os.fstat(fd).st_size > MAX_JSON_BYTES:
            raise DraftError("Draft snapshot exceeds bounded read size")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(MAX_JSON_BYTES + 1)
        if len(data) > MAX_JSON_BYTES:
            raise DraftError("Draft snapshot exceeds bounded read size")
        value = json.loads(data)
        if not isinstance(value, dict):
            raise DraftError("Draft snapshot must be an object")
        return value
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DraftError("Damaged draft JSON") from exc
    finally:
        os.close(fd)


def _write(directory: int, name: str, value: dict[str, Any], *, immutable: bool) -> None:
    """Publish complete bytes atomically; immutable targets can never be replaced."""
    data = _bytes(value)
    if len(data) > MAX_JSON_BYTES:
        raise DraftError("Draft snapshot exceeds bounded write size")
    temporary = f".tmp-{uuid4()}"
    fd = os.open(
        temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory
    )
    try:
        with os.fdopen(fd, "wb", closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(fd)
        if immutable:
            os.link(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        else:
            # Replacing a symlink itself is safe, but reject it rather than silently repair it.
            existing = os.stat(name, dir_fd=directory, follow_symlinks=False)
            if not stat.S_ISREG(existing.st_mode) or existing.st_nlink != 1:
                raise DraftError("Unsafe draft head")
            os.replace(temporary, name, src_dir_fd=directory, dst_dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(fd)
        try:
            os.unlink(temporary, dir_fd=directory)
            os.fsync(directory)
        except FileNotFoundError:
            pass


@contextmanager
def _locked(directory: int) -> Iterator[None]:
    # Created before first publication, so concurrent saves never race lock creation.
    fd = os.open(".lock", os.O_RDWR | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        _regular(fd)
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


class DraftStore:
    """Trusted local server seam. No caller-selected storage location or source ID.

    ``fork_rp1`` is the only constructor; blank drafts and builder commands are
    deliberately absent. ``save_metadata`` accepts only label/notes and compare-
    and-swap revision intent. Returned objects are independent deserialized data.
    """

    def __init__(self, root: Path):
        if root.is_symlink():
            raise DraftError("Server root cannot be a symlink")
        self.root = root.resolve(strict=True)

    @contextmanager
    def _storage(self, *, create: bool = False) -> Iterator[int]:
        root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            with (
                _directory(root_fd, STORAGE[0], create=create) as output,
                _directory(output, STORAGE[1], create=create) as storage,
            ):
                yield storage
        finally:
            os.close(root_fd)

    def _source(self) -> dict[str, Any]:
        # Pin verification occurs before and after the projection. Source files
        # are read through no-follow descriptors too; no generated assets run.
        source_bytes: dict[str, bytes] = {}
        root_fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for path, pin in rp1_inspection.PINS.items():
                source_bytes[path] = self._source_bytes(root_fd, path)
                if hashlib.sha256(source_bytes[path]).hexdigest() != pin:
                    raise DraftError("Frozen RP1 source hash mismatch")
            bank = parts_bank.build(self.root)
            inspection = rp1_inspection.build(self.root)
            if any(self._source_bytes(root_fd, p) != b for p, b in source_bytes.items()):
                raise DraftError("Frozen RP1 source changed during fork")
        finally:
            os.close(root_fd)
        return {
            "configuration_id": rp1_inspection.ID,
            "source_refs": [{"path": p, "sha256": h} for p, h in rp1_inspection.PINS.items()],
            "parts_bank_revision_sha256": bank["revision_sha256"],
            "parts_bank": bank,
            "specification": yaml.safe_load(source_bytes[rp1_inspection.SPEC]),
            "inspection": inspection,
            "accounting_policy": (
                "Preserved source groups: 55 occurrences, quantity 1 per source record; "
                "geometry group_count never multiplies source group mass or budget. "
                "Source estimates and separate 50g, 20g and 55/68g cases are unchanged. "
                "No new mass, cost, inertia or engineering calculation."
            ),
        }

    def _source_bytes(self, directory: int, path: str) -> bytes:
        parts = Path(path).parts
        if len(parts) > 1:
            with _directory(directory, parts[0]) as child:
                return self._source_bytes(child, str(Path(*parts[1:])))
        fd = os.open(parts[0], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        try:
            _regular(fd)
            if os.fstat(fd).st_size > MAX_JSON_BYTES:
                raise DraftError("Frozen source exceeds bounded read size")
            with os.fdopen(fd, "rb", closefd=False) as stream:
                return stream.read(MAX_JSON_BYTES + 1)
        finally:
            os.close(fd)

    def fork_rp1(self, *, label: str, notes: str = "") -> dict[str, Any]:
        label = _text(label, "label", 160, required=True)
        notes = _text(notes, "notes", 8000)
        source = self._source()
        source_sha = _digest(source)
        draft_id = str(uuid4())
        revision = self._revision(draft_id, source_sha, label, notes, None, 1)
        with self._storage(create=True) as storage:
            # UUID collisions never reuse an existing directory.
            os.mkdir(draft_id, mode=0o700, dir_fd=storage)
            with _directory(storage, draft_id) as directory:
                os.mkdir("revisions", mode=0o700, dir_fd=directory)
                _write(directory, "source.json", source, immutable=True)
                _write(directory, ".lock", {}, immutable=True)
                with _directory(directory, "revisions") as revisions:
                    _write(
                        revisions, revision["revision_sha256"] + ".json", revision, immutable=True
                    )
                _write(
                    directory,
                    "head.json",
                    {"revision_sha256": revision["revision_sha256"]},
                    immutable=True,
                )
            os.fsync(storage)
        return {**revision, "source": source}

    @staticmethod
    def _revision(
        draft_id: str, source_sha: str, label: str, notes: str, parent: str | None, sequence: int
    ) -> dict[str, Any]:
        value = {
            "schema_version": 1,
            "draft_id": draft_id,
            "source_sha256": source_sha,
            "base_configuration_id": rp1_inspection.ID,
            "parent_revision_sha256": parent,
            "sequence": sequence,
            "created_at": _now(),
            "label": label,
            "notes": notes,
            "operation": "fork_rp1" if parent is None else "save_metadata",
            "readiness": copy.deepcopy(READINESS),
            "capabilities": {"save_metadata": True, "compose": False, "resolve": False},
        }
        value["revision_sha256"] = _digest(value)
        return value

    def _load(self, directory: int, draft_id: str, revision: str | None) -> dict[str, Any]:
        if revision is None:
            head = _read(directory, "head.json")
            revision = _hash(head.get("revision_sha256"))
        with _directory(directory, "revisions") as revisions:
            value = _read(revisions, _hash(revision) + ".json")
        unsigned = {k: v for k, v in value.items() if k != "revision_sha256"}
        if (
            value.get("draft_id") != draft_id
            or value.get("revision_sha256") != revision
            or _digest(unsigned) != revision
            or value.get("readiness") != READINESS
            or value.get("base_configuration_id") != rp1_inspection.ID
        ):
            raise DraftError("Draft revision identity, readiness or content hash mismatch")
        source = _read(directory, "source.json")
        if _digest(source) != value.get("source_sha256"):
            raise DraftError("Draft source content hash mismatch")
        return {**value, "source": source}

    def read(self, draft_id: str, *, revision: str | None = None) -> dict[str, Any]:
        """Read current or exact immutable history without reopening frozen source."""
        _id(draft_id)
        if revision is not None:
            _hash(revision)
        with self._storage() as storage, _directory(storage, draft_id) as directory:
            return self._load(directory, draft_id, revision)

    def save_metadata(
        self, draft_id: str, *, base_revision: str, label: str, notes: str
    ) -> dict[str, Any]:
        _id(draft_id)
        _hash(base_revision)
        label = _text(label, "label", 160, required=True)
        notes = _text(notes, "notes", 8000)
        with (
            self._storage() as storage,
            _directory(storage, draft_id) as directory,
            _locked(directory),
        ):
            current = self._load(directory, draft_id, None)
            if current["revision_sha256"] != base_revision:
                raise RevisionConflict(current["revision_sha256"])
            if current["sequence"] >= MAX_HISTORY:
                raise DraftError("Draft revision limit reached")
            if current["label"] == label and current["notes"] == notes:
                return current
            value = self._revision(
                draft_id,
                current["source_sha256"],
                label,
                notes,
                base_revision,
                current["sequence"] + 1,
            )
            with _directory(directory, "revisions") as revisions:
                _write(revisions, value["revision_sha256"] + ".json", value, immutable=True)
            _write(
                directory,
                "head.json",
                {"revision_sha256": value["revision_sha256"]},
                immutable=False,
            )
            return {**value, "source": current["source"]}

    def list_drafts(self, *, limit: int = 25, after: str | None = None) -> dict[str, Any]:
        """Bounded summaries in UUID order; cursor is an ID, never a path."""
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise DraftError("Draft list limit must be an integer between 1 and 100")
        if after is not None:
            _id(after)
        try:
            with self._storage() as storage:
                names: list[str] = []
                with os.scandir(storage) as entries:
                    for entry in entries:
                        if len(names) >= MAX_DRAFTS:
                            raise DraftError("Draft inventory limit exceeded")
                        _id(entry.name)
                        if entry.is_symlink() or not entry.is_dir(follow_symlinks=False):
                            raise DraftError("Unsafe draft inventory entry")
                        names.append(entry.name)
                selected = sorted(n for n in names if after is None or n > after)[: limit + 1]
                rows = []
                for name in selected[:limit]:
                    with _directory(storage, name) as directory:
                        value = self._load(directory, name, None)
                    rows.append(
                        {
                            k: value[k]
                            for k in (
                                "draft_id",
                                "revision_sha256",
                                "label",
                                "sequence",
                                "created_at",
                                "readiness",
                            )
                        }
                    )
                return {
                    "drafts": rows,
                    "next_after": selected[limit - 1] if len(selected) > limit else None,
                }
        except DraftNotFound:
            # A pristine server has no output/design-drafts yet. Missing snapshots
            # inside an existing draft remain errors rather than disappearing rows.
            output = self.root / STORAGE[0]
            storage_path = output / STORAGE[1]
            if (
                not output.is_symlink()
                and not storage_path.is_symlink()
                and not storage_path.exists()
            ):
                return {"drafts": [], "next_after": None}
            raise
