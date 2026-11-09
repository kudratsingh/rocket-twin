"""Production reconstruction from existing mesh bytes; never rerun CAD/export campaign."""

import json
import shutil

import pytest

from scripts.wo04_prepare_component_detail import (
    CACHE_PATH,
    CATALOG_PATH,
    CATALOG_SHA256,
    EXPORTER_PATH,
    ROOT,
    UnavailableError,
    catalog,
    digest,
    filename,
    prepare,
)


def source_packet():
    packet = json.loads((ROOT / CATALOG_PATH).read_text())
    if any(not (ROOT / path).exists() for path in packet["sources"]):
        pytest.skip("Matching core/optional parent files are generated local supply")
    return packet


def test_default_verification_is_read_only_and_fast_existing_cache_copy_is_repeatable(tmp_path):
    packet = source_packet()
    if any(not (ROOT / CACHE_PATH / filename(c)).exists() for c in packet["children"]):
        pytest.skip("Original optional child cache absent")
    target = tmp_path / "public"
    result = prepare(destination=target)
    assert result["status"] == "verified_cache_copy_required" and not target.exists()
    result = prepare(destination=target, publish=True)
    assert result["status"] == "prepared" and result["reconstructed"] == 0
    for child in packet["children"]:
        assert digest((target / filename(child)).read_bytes()) == child["sha256"]
    again = prepare(destination=target, publish=True)
    assert again["status"] == "verified_existing_public"
    assert again["public_writes"] == 0 and again["reconstructed"] == 0


def test_empty_child_cache_reconstructs_exact_recorded_bytes_only_in_temporary_staging(tmp_path):
    packet = source_packet()
    target = tmp_path / "fresh-public"
    result = prepare(destination=target, cache=tmp_path / "missing-cache", publish=True)
    assert result["reconstructed"] == 18
    assert result["catalog_sha256"] == CATALOG_SHA256
    assert len(list(target.iterdir())) == 18
    for child in packet["children"]:
        assert digest((target / filename(child)).read_bytes()) == child["sha256"]
    assert digest((ROOT / CATALOG_PATH).read_bytes()) == CATALOG_SHA256
    assert not list(tmp_path.glob(".component-detail-stage-*"))


def test_missing_parent_source_is_explicitly_unavailable_even_when_child_cache_exists(tmp_path):
    packet = source_packet()
    root = tmp_path / "source"
    for relative in [CATALOG_PATH, EXPORTER_PATH, *packet["sources"]]:
        dest = root / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, dest)
    (root / "output/rp1-inspection-geometry/parts/body.glb").unlink()
    target = tmp_path / "public"
    with pytest.raises(UnavailableError, match="Required source unavailable.*body.glb"):
        prepare(root, destination=target, cache=ROOT / CACHE_PATH, publish=True)
    assert not target.exists()


def test_changed_catalog_corrupt_child_and_unregistered_target_fail_without_overwrite(tmp_path):
    packet = source_packet()
    root = tmp_path / "bad-source"
    path = root / CATALOG_PATH
    path.parent.mkdir(parents=True)
    path.write_bytes((ROOT / CATALOG_PATH).read_bytes() + b"\n")
    with pytest.raises(UnavailableError, match="Source hash mismatch"):
        catalog(root)
    cache = tmp_path / "cache"
    cache.mkdir()
    child = cache / filename(packet["children"][0])
    child.write_bytes(b"not registered")
    with pytest.raises(UnavailableError, match="Recorded child bytes differ"):
        prepare(destination=tmp_path / "public", cache=cache, publish=True)
    assert child.read_bytes() == b"not registered"
    target = tmp_path / "owner"
    target.mkdir()
    (target / "owner.txt").write_text("preserve")
    with pytest.raises(UnavailableError, match="unregistered files"):
        prepare(destination=target, publish=True)
    assert (target / "owner.txt").read_text() == "preserve"
