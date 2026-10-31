"""Published audit imports and independent contact/foundation known cases."""

from scripts.wo03_installed_fin_closure_audit import fixtures


def test_published_contact_audit_runs_known_cases_without_local_study_driver() -> None:
    result = fixtures(young=2.0e9, shear=0.77e9)
    assert result["passed"]
    assert result["finite_planar_patch_matrix_relative_error"] < 1e-12
    assert result["independent_series_parallel_rotation_relative_error"] < 1e-12
