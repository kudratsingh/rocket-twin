"""Historical provenance remains strict even when current code evolves."""

import hashlib
from pathlib import Path

import pytest

from src.analysis.source_archive import ARCHIVES, verified_source


def test_current_matching_source_is_used_and_unknown_drift_fails(tmp_path):
    p = tmp_path / "source.py"
    p.write_bytes(b"original")
    expected = hashlib.sha256(p.read_bytes()).hexdigest()
    assert verified_source(tmp_path, "source.py", expected) == p
    p.write_bytes(b"changed")
    with pytest.raises(ValueError, match="without an exact archive"):
        verified_source(tmp_path, "source.py", expected)
    with pytest.raises(ValueError, match="escapes repository"):
        verified_source(tmp_path, "../source.py", expected)


def test_explicit_archive_requires_original_bytes_and_exact_path_hash(tmp_path):
    root = Path(__file__).resolve().parents[1]
    (source, expected), archive = next(iter(ARCHIVES.items()))
    original = (root / archive).read_bytes()
    assert hashlib.sha256(original).hexdigest() == expected
    p = tmp_path / source
    p.parent.mkdir(parents=True)
    p.write_bytes(b"current schema")
    a = tmp_path / archive
    a.parent.mkdir(parents=True)
    a.write_bytes(original)
    assert verified_source(tmp_path, source, expected) == a
    a.write_bytes(b"tampered")
    with pytest.raises(ValueError):
        verified_source(tmp_path, source, expected)
    with pytest.raises(ValueError):
        verified_source(tmp_path, "other.py", expected)
