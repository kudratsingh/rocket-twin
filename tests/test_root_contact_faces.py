"""Known contact-area fixtures include a real positive gap and curved overlap."""

from scripts.wo03_root_contact_faces import box_can_touch, fixtures


def test_known_face_common_areas():
    cfg = {"positive_patch_area_mm2": 1e-6, "fixture_area_abs_tolerance_mm2": 1e-6}
    result = fixtures(cfg)
    assert result["passed"]
    assert result["actual"]["physical_gap_mm2"] == 0
    assert not box_can_touch([0, 1, 0, 1, 0, 1], [2, 3, 0, 1, 0, 1])
