"""Isolated real-source draft lifecycle and unsafe-storage rejection."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest
import yaml

from src.api import rp1_inspection
from src.vehicle import design_drafts as drafts

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def server(tmp_path):
    for relative in rp1_inspection.PINS:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    return drafts.DraftStore(tmp_path)


def folder(server, value):
    return server.root / "output" / "design-drafts" / value["draft_id"]


def test_fork_save_reload_history_preserves_source_and_group_accounting(server):
    before = {p: (server.root / p).read_bytes() for p in rp1_inspection.PINS}
    assert server.list_drafts() == {"drafts": [], "next_after": None}
    first = server.fork_rp1(label="RP1 study", notes="Investigate source conflicts")
    source = first["source"]
    assert source["configuration_id"] == rp1_inspection.ID
    assert source["specification"] == yaml.safe_load(before[rp1_inspection.SPEC])
    bank = source["parts_bank"]
    assert len(bank["instances"]) == len(bank["definitions"]) == 55
    fin = next(i for i in bank["instances"] if i["id"] == "fin_set")
    assert fin["quantity"] == 1 and fin["group_count"] == 3
    rows = {d["source_part_id"]: d for d in bank["definitions"]}
    assert rows["motor_retainer"]["reuse_status"] == "identity_unresolved"
    assert rows["independent_recovery"]["reuse_status"] == "identity_unresolved"
    assert rows["rp1_kevlar_wrap"]["geometry"]["maturity"] == "missing_geometry"
    assert source["inspection"]["summary"]["inertia_status"] == "unavailable"
    assert source["inspection"]["evidence"]["fin"]
    assert first["readiness"] == drafts.READINESS
    assert first["readiness"]["flight_ready"] is False
    assert first["readiness"]["simulation_eligible"] is False
    assert server.read(first["draft_id"]) == first
    old_bytes = (
        folder(server, first) / "revisions" / (first["revision_sha256"] + ".json")
    ).read_bytes()
    second = server.save_metadata(
        first["draft_id"],
        base_revision=first["revision_sha256"],
        label="Renamed study",
        notes="Only notes changed",
    )
    assert second["source"] == source
    assert second["source_sha256"] == first["source_sha256"]
    assert second["sequence"] == 2
    assert second["parent_revision_sha256"] == first["revision_sha256"]
    assert second["revision_sha256"] != first["revision_sha256"]
    assert server.read(first["draft_id"]) == second
    assert server.read(first["draft_id"], revision=first["revision_sha256"]) == first
    assert (
        folder(server, first) / "revisions" / (first["revision_sha256"] + ".json")
    ).read_bytes() == old_bytes
    assert before == {p: (server.root / p).read_bytes() for p in before}
    assert (
        server.save_metadata(
            first["draft_id"],
            base_revision=second["revision_sha256"],
            label=second["label"],
            notes=second["notes"],
        )
        == second
    )
    with pytest.raises(drafts.RevisionConflict) as conflict:
        server.save_metadata(
            first["draft_id"], base_revision=first["revision_sha256"], label="stale", notes=""
        )
    assert conflict.value.current_revision == second["revision_sha256"]
    # Reload/history use their saved content even after the live frozen source drifts.
    (server.root / rp1_inspection.SPEC).write_text("changed")
    assert server.read(first["draft_id"]) == second
    with pytest.raises(drafts.DraftError, match="hash mismatch"):
        server.fork_rp1(label="Drift rejected")


def test_simultaneous_saves_have_one_winner_and_one_recoverable_conflict(server):
    first = server.fork_rp1(label="Concurrent source")
    barrier = Barrier(2)

    def save(label):
        barrier.wait(timeout=5)
        try:
            return server.save_metadata(
                first["draft_id"], base_revision=first["revision_sha256"], label=label, notes=""
            )
        except drafts.RevisionConflict as error:
            return error

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(save, ["Writer A", "Writer B"]))
    assert sum(isinstance(r, drafts.RevisionConflict) for r in results) == 1
    winner = next(r for r in results if isinstance(r, dict))
    assert server.read(first["draft_id"]) == winner
    assert winner["sequence"] == 2


def test_interrupted_head_publication_preserves_last_complete_revision(server, monkeypatch):
    first = server.fork_rp1(label="Before interruption")
    original = drafts._write

    def fail_head(directory, name, value, *, immutable):
        if name == "head.json":
            raise OSError("simulated interrupted publication")
        return original(directory, name, value, immutable=immutable)

    monkeypatch.setattr(drafts, "_write", fail_head)
    with pytest.raises(OSError, match="interrupted"):
        server.save_metadata(
            first["draft_id"], base_revision=first["revision_sha256"], label="Interrupted", notes=""
        )
    assert server.read(first["draft_id"]) == first
    monkeypatch.setattr(drafts, "_write", original)
    recovered = server.save_metadata(
        first["draft_id"], base_revision=first["revision_sha256"], label="Recovered", notes=""
    )
    assert recovered["sequence"] == 2
    assert not list(folder(server, first).rglob(".tmp-*"))


@pytest.mark.parametrize(
    "bad_id", ["../configs", "/tmp", "", "../" + str(uuid4()), str(uuid4()).upper(), "1" * 36]
)
def test_request_paths_are_not_storage_paths(server, bad_id):
    with pytest.raises(drafts.DraftError, match="UUID4"):
        server.read(bad_id)
    with pytest.raises(drafts.DraftError):
        server.list_drafts(after=bad_id)
    assert not (server.root / "output").exists()


def test_unsupported_fields_invalid_input_and_unknown_ids_fail_before_writes(server):
    with pytest.raises(TypeError):
        server.fork_rp1(label="Bad", asset_path="../../configs")
    for label in ["", " " * 2, "x" * 161, "nul\0"]:
        with pytest.raises(drafts.DraftError):
            server.fork_rp1(label=label)
    with pytest.raises(drafts.DraftError):
        server.fork_rp1(label="Good", notes="x" * 8001)
    with pytest.raises(drafts.DraftNotFound):
        server.read(str(uuid4()))
    with pytest.raises(drafts.DraftError, match="SHA-256"):
        server.read(str(uuid4()), revision="../../source")
    for limit in [True, 0, 101, 1.2]:
        with pytest.raises(drafts.DraftError):
            server.list_drafts(limit=limit)
    assert not (server.root / "output").exists()


def test_list_is_bounded_cursor_paged_and_source_copy_cannot_mutate_storage(server):
    created = [server.fork_rp1(label=f"Study {i}") for i in range(3)]
    first = server.list_drafts(limit=2)
    second = server.list_drafts(limit=2, after=first["next_after"])
    ids = [r["draft_id"] for page in [first, second] for r in page["drafts"]]
    assert ids == sorted(c["draft_id"] for c in created)
    assert second["next_after"] is None
    assert "source" not in first["drafts"][0]
    current = created[0]
    current["source"]["parts_bank"]["instances"].clear()
    assert len(server.read(current["draft_id"])["source"]["parts_bank"]["instances"]) == 55


@pytest.mark.parametrize("component", ["output", "design-drafts"])
def test_storage_symlink_cannot_reach_frozen_source(server, component):
    target = server.root / "configs"
    before = (server.root / rp1_inspection.SPEC).read_bytes()
    if component == "output":
        link = server.root / "output"
    else:
        (server.root / "output").mkdir()
        link = server.root / "output" / "design-drafts"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(drafts.DraftError, match="symlink"):
        server.fork_rp1(label="Unsafe storage")
    with pytest.raises(drafts.DraftError):
        server.list_drafts()
    assert (server.root / rp1_inspection.SPEC).read_bytes() == before
    assert sorted(p.name for p in target.iterdir()) == ["studies", "vehicle"]


def test_source_symlink_and_draft_directory_symlink_are_rejected(server):
    source = server.root / rp1_inspection.SPEC
    saved = source.with_name("saved.yaml")
    source.rename(saved)
    source.symlink_to(saved)
    with pytest.raises(OSError):
        server.fork_rp1(label="Linked source")
    source.unlink()
    saved.rename(source)
    first = server.fork_rp1(label="Real source")
    directory = folder(server, first)
    moved = directory.with_name("outside")
    directory.rename(moved)
    directory.symlink_to(moved, target_is_directory=True)
    with pytest.raises(drafts.DraftError):
        server.read(first["draft_id"])


@pytest.mark.parametrize("component", ["head.json", "source.json", "revisions", ".lock"])
def test_snapshot_and_lock_symlinks_cannot_mutate_foreign_files(server, component):
    first = server.fork_rp1(label="Symlink check")
    directory = folder(server, first)
    foreign = server.root / "foreign"
    foreign.write_text("owner data")
    path = directory / component
    if path.exists():
        if path.is_dir():
            path.rename(directory / "saved-revisions")
        else:
            path.unlink()
    path.symlink_to(foreign)
    with pytest.raises((drafts.DraftError, OSError)):
        server.save_metadata(
            first["draft_id"], base_revision=first["revision_sha256"], label="Rejected", notes=""
        )
    assert foreign.read_text() == "owner data"


def test_corruption_oversized_files_hardlinks_and_fifo_fail_closed(server):
    first = server.fork_rp1(label="Damage checks")
    directory = folder(server, first)
    source = directory / "source.json"
    original = source.read_bytes()
    value = json.loads(original)
    value["configuration_id"] = "foreign"
    source.write_text(json.dumps(value))
    with pytest.raises(drafts.DraftError, match="hash mismatch"):
        server.read(first["draft_id"])
    source.write_bytes(original)
    with source.open("wb") as stream:
        stream.truncate(drafts.MAX_JSON_BYTES + 1)
    with pytest.raises(drafts.DraftError, match="bounded"):
        server.read(first["draft_id"])
    source.write_bytes(original)
    os.link(source, directory / "hardlink")
    with pytest.raises(drafts.DraftError, match="regular files"):
        server.read(first["draft_id"])
    (directory / "hardlink").unlink()
    source.unlink()
    os.mkfifo(source)
    with pytest.raises(drafts.DraftError, match="regular files"):
        server.read(first["draft_id"])
    assert (
        hashlib.sha256((server.root / rp1_inspection.SPEC).read_bytes()).hexdigest()
        == rp1_inspection.PINS[rp1_inspection.SPEC]
    )


def test_frozen_web_fixture_matches_current_source_and_revision_generator(server):
    """Node consumes frozen real-store bytes; generator contract is checked here."""
    fixture_path = ROOT / "web/tests/fixtures/rp1-draft-library.json"
    data = fixture_path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == (
        "b2339838a42a6426d535a533df7c021211362e3dd4e643a933e5c4562d0cded0"
    )
    fixture = json.loads(data)
    assert fixture["schema_version"] == 1
    assert fixture["generation"]["inputs"] == rp1_inspection.PINS
    assert (
        fixture["generation"]["store_module_sha256"]
        == hashlib.sha256((ROOT / "src/vehicle/design_drafts.py").read_bytes()).hexdigest()
    )
    assert fixture["source"] == server._source()
    source_sha = drafts._digest(fixture["source"])
    latest = {}
    for revision in fixture["revisions"].values():
        metadata = revision["metadata"]
        assert metadata["source_sha256"] == source_sha
        assert drafts._digest(metadata) == revision["revision_sha256"]
        drafts._id(metadata["draft_id"])
        generated = server._revision(
            metadata["draft_id"],
            source_sha,
            metadata["label"],
            metadata["notes"],
            metadata["parent_revision_sha256"],
            metadata["sequence"],
        )
        generated.pop("revision_sha256")
        # Timestamp/UUID are preserved observations from actual fixture generation;
        # compare every other generated field without freezing the live clock.
        generated["created_at"] = metadata["created_at"]
        assert generated == metadata
        current = latest.get(metadata["draft_id"])
        if current is None or current["metadata"]["sequence"] < metadata["sequence"]:
            latest[metadata["draft_id"]] = revision
    initial, saved = (fixture["revisions"][key] for key in ("initial", "saved"))
    assert saved["metadata"]["parent_revision_sha256"] == initial["revision_sha256"]
    summary_keys = ("draft_id", "revision_sha256", "label", "sequence", "created_at", "readiness")
    expected = []
    for draft_id in sorted(latest):
        revision = latest[draft_id]
        full = {**revision["metadata"], "revision_sha256": revision["revision_sha256"]}
        expected.append({key: full[key] for key in summary_keys})
    assert fixture["page"] == {"drafts": expected, "next_after": None}
    assert not (server.root / "output").exists()
