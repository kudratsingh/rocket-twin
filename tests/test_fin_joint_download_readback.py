"""Supplied file readback; generated source supply is optional, not fabricated."""

import pytest

from scripts import wo04_fin_joint_download_readback as verifier


def test_registered_source_readback_is_labelled_source_only():
    if not verifier.SOURCE_STEP.is_file():
        pytest.skip("Original registered STEP is optional generated source supply")
    pytest.importorskip("cadquery")
    result = verifier.verify(verifier.SOURCE_STEP)
    assert result["source_verification_only"] is True
    assert result["file"]["realpath"] == str(verifier.SOURCE_STEP.resolve())
    assert result["file"]["sha256"] == verifier.JOINT_SHA
    assert result["file"]["bytes"] == 339487
    assert result["units"] == "mm"
    assert result["readback"]["valid"] is True
    assert result["readback"]["solids"] == 18
    dimensions = result["readback"]["representative_dimensions"]
    assert dimensions["tab"]["thickness_mm"] == pytest.approx(6)
    assert dimensions["tab"]["axial_length_mm"] == pytest.approx(109.4)
    assert dimensions["tab"]["aft_station_mm"] == pytest.approx(1189.6)
    assert dimensions["aft_ring"]["front_station_mm"] == pytest.approx(1190)
    assert dimensions["nominal_aft_gap_mm"] == pytest.approx(0.4)
    slot = dimensions["body_slot"]
    assert slot["source_nominal_mm"] == 6.8
    if slot["status"] == "readback_planar_slot_faces":
        assert slot["measured_from_step_mm"] == pytest.approx(6.8)
    else:
        assert slot["measured_from_step_mm"] is None
    assert result["runtime"]["cpu_seconds"] < 60


def test_unknown_file_refused_before_cad_import(tmp_path, monkeypatch):
    path = tmp_path / "unknown.step"
    path.write_bytes(b"ISO-10303-21; unregistered")

    def forbidden(*args):
        raise AssertionError("No CAD import for unknown bytes")

    monkeypatch.setattr(verifier, "readback", forbidden)
    with pytest.raises(ValueError, match="SHA/size"):
        verifier.verify(path)


def test_foreign_provenance_refused_before_readback(tmp_path, monkeypatch):
    if not verifier.SOURCE_STEP.is_file():
        pytest.skip("Original registered STEP is optional generated source supply")
    provenance = tmp_path / "foreign.json"
    provenance.write_text('{"identity":"foreign"}')

    def forbidden(*args):
        raise AssertionError("No CAD import for foreign provenance")

    monkeypatch.setattr(verifier, "readback", forbidden)
    with pytest.raises(ValueError, match="provenance bytes mismatch"):
        verifier.verify(verifier.SOURCE_STEP, provenance)
