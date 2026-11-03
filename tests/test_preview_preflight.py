"""Read-only preview diagnostics distinguish source and route failure modes."""

import hashlib

from scripts.wo04_preview_preflight import response_status, source_status


def test_http_failures_do_not_conflate_missing_route_and_source():
    assert response_status(404, b'{"detail":"Not Found"}').startswith("missing-route")
    assert response_status(404, b'{"detail":"source unavailable"}').startswith(
        "source/resource missing"
    )
    assert response_status(409, b'{"detail":"source changed"}').startswith("source-error")
    assert response_status(503, b'{"detail":"unavailable"}').startswith("HTTP error 503")


def test_snapshot_source_matching_mismatch_and_missing(tmp_path):
    path = tmp_path / "source.yaml"
    path.write_text("actual")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    doc = {
        "identity": {
            "candidate_id": "G80-F2",
            "source_identity": "f2",
            "cad_revision": None,
            "specification_sha256": digest,
        },
        "generated_from": [{"id": "spec", "path": "source.yaml", "sha256": digest}],
    }
    assert any("matching current source" in line for line in source_status(doc, tmp_path))
    path.write_text("changed")
    assert any(line.startswith("mismatch:") for line in source_status(doc, tmp_path))
    path.unlink()
    assert any(line.startswith("source-error:") for line in source_status(doc, tmp_path))
    doc["identity"]["candidate_id"] = "G80-F1"
    assert source_status(doc, tmp_path)[0].startswith("identity mismatch")


def test_rejects_escaping_source_and_mismatched_identity(tmp_path):
    doc = {
        "identity": {
            "candidate_id": "G80-F2",
            "source_identity": "f2",
            "cad_revision": None,
            "specification_sha256": "a" * 64,
        },
        "generated_from": [{"id": "spec", "path": "../outside", "sha256": "b" * 64}],
    }
    lines = source_status(doc, tmp_path)
    assert any("specification hash" in line for line in lines)
    assert any("outside repository" in line for line in lines)
