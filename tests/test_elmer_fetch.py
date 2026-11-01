"""Offline acquisition integrity; no network, extraction or tool execution."""

import hashlib
import io
import json

import pytest

from scripts import wo03_fetch_elmer_eval as fetch


def test_checksum_failure_preserves_partial_and_cannot_mark_download_verified(
    tmp_path, monkeypatch
):
    payload = b"\x1f\x8btest bytes; never extracted"

    def response(_url, timeout):
        assert timeout == 15
        stream = io.BytesIO(payload)
        stream.url = "https://example.invalid/fixture"
        return stream

    monkeypatch.setattr(fetch, "urlopen", response)
    monkeypatch.setattr(fetch, "DEST", tmp_path)
    monkeypatch.setattr(fetch, "FILES", (("test.tar.gz", "https://example.invalid", "0" * 64),))
    with pytest.raises(ValueError, match="checksum mismatch"):
        fetch.main()
    assert not (tmp_path / "test.tar.gz").exists()
    assert (tmp_path / "test.tar.gz.partial").read_bytes() == payload
    record = json.loads((tmp_path / "acquisition.json").read_text())
    assert record["status"] == "failed_preserved"
    assert record["files"][0]["sha256"] == hashlib.sha256(payload).hexdigest()
    with pytest.raises(SystemExit, match="No automatic retry"):
        fetch.main()
