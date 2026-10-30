from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts import wo03_tolerances
from src.analysis.tolerances import _domain_temperature, _thermal_gap_bounds, interval_stack


def test_interval_stack_combines_dimension_and_thermal_bounds() -> None:
    result = interval_stack(
        host_mm=20.0,
        insert_mm=18.0,
        host_tolerance_mm=0.1,
        insert_tolerance_mm=0.2,
        required_minimum_mm=1.5,
        thermal_gap_shift_mm=(0.01, 0.02),
    )
    assert result["nominal_mm"] == 2.0
    assert result["minimum_mm"] == pytest.approx(1.71)
    assert result["maximum_mm"] == pytest.approx(2.32)
    assert result["status"] == "pass"


def test_interval_stack_reports_failed_minimum_without_waiver() -> None:
    result = interval_stack(10.0, 9.8, 0.15, 0.15, 0.1)
    assert result["minimum_mm"] == pytest.approx(-0.1)
    assert result["status"] == "fail"


def test_independent_hot_insert_cold_host_closes_clearance() -> None:
    shift = _thermal_gap_bounds(
        host_nominal_mm=40.0,
        insert_nominal_mm=39.0,
        host_cte_per_k=1e-5,
        insert_cte_per_k=2e-5,
        host_delta_t_k=[0.0, 10.0],
        insert_delta_t_k=[0.0, 10.0],
    )
    assert shift is not None
    assert shift[0] == pytest.approx(-0.0078)
    assert shift[1] == pytest.approx(0.004)
    closed = interval_stack(40.0, 39.0, 0.0, 0.0, 0.995, shift)
    assert closed["minimum_mm"] == pytest.approx(0.9922)
    assert closed["status"] == "fail"


def test_key_flank_uses_half_width_gap_and_fails_at_point075() -> None:
    result = interval_stack(5.75, 5.6, 0.0, 0.0, 0.1, clearance_factor=2.0)
    assert result["nominal_mm"] == pytest.approx(0.075)
    assert result["minimum_mm"] == pytest.approx(0.075)
    assert result["status"] == "fail"


def test_interval_stack_preserves_unknown_tolerance_as_unavailable() -> None:
    result = interval_stack(10.0, 9.8, None, 0.1, 0.1)
    assert result["nominal_mm"] == pytest.approx(0.2)
    assert result["minimum_mm"] is None
    assert result["maximum_mm"] is None
    assert result["status"] == "unavailable"


@pytest.mark.parametrize(
    ("material", "limit_c", "expected_delta"),
    [("cardboard", 45.0, 30.0), ("phenolic", 120.0, 105.0), ("asa", 60.0, 45.0)],
)
def test_fit_domain_is_capped_by_material_limit(
    material: str, limit_c: float, expected_delta: float
) -> None:
    part = SimpleNamespace(
        engineering=SimpleNamespace(material_profile=material), material="unknown"
    )
    domain = _domain_temperature(
        part,
        {"materials": {material: {"limit_c": limit_c}}},
        {"ambient_reference_c": 15.0, "maximum_external_case_sensitivity_c": 250.0},
    )
    assert domain is not None
    assert domain["minimum_c"] == 15.0
    assert domain["maximum_c"] == limit_c
    assert domain["delta_t_k_maximum"] == expected_delta


def test_missing_material_limit_keeps_fit_domain_unavailable() -> None:
    part = SimpleNamespace(
        engineering=SimpleNamespace(material_profile="unknown"), material="unknown"
    )
    assert (
        _domain_temperature(
            part,
            {"materials": {}},
            {"ambient_reference_c": 15.0, "maximum_external_case_sensitivity_c": 250.0},
        )
        is None
    )


def test_cli_returns_nonzero_only_for_failed_source_provenance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record = tmp_path / "record.json"
    record.write_text('{"acceptance_passed": false, "inputs_unchanged": true}')
    monkeypatch.setattr(wo03_tolerances, "generate", lambda _config: record)
    monkeypatch.setattr("sys.argv", ["wo03_tolerances.py", "--preset", "tiny"])
    assert wo03_tolerances.main() == 0
    record.write_text('{"acceptance_passed": false, "inputs_unchanged": false}')
    assert wo03_tolerances.main() == 2
