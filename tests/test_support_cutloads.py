"""Known answers for the station/first-moment free-body accounting."""

import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.wo03_support_cutloads import fraction_bounds, run


def test_extremal_mass_fractions() -> None:
    # A unit mass on [0, 10] has mean 2; at cut 5, at least 3/5 must
    # be forward. An all-forward distribution centered at 2 is attainable.
    assert fraction_bounds(0, 10, 2, 5) == pytest.approx((0.6, 1.0))
    # Mirror case: all aft is possible; at most 2/5 can be forward.
    assert fraction_bounds(0, 10, 8, 5) == pytest.approx((0.0, 0.4))
    assert fraction_bounds(0, 10, 5, -1) == (0.0, 0.0)
    assert fraction_bounds(0, 10, 5, 11) == (1.0, 1.0)
    with pytest.raises(ValueError):
        fraction_bounds(0, 10, 11, 5)


def test_synthetic_ledger_balances_and_preserves_cut_inertia(tmp_path: Path) -> None:
    def write(path: Path, value: dict) -> None:
        path.write_text(json.dumps(value))

    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    curve = tmp_path / "curve.eng"
    curve.write_text("synthetic input identity only\n")
    source = tmp_path / "candidate.json"
    write(
        source,
        {
            "motor": {"curve": str(curve)},
            "parts": [
                {"id": "motor", "mass_kg": 2.0},
                {
                    "id": "front",
                    "mass_kg": 1.0,
                    "position_m": 0.0,
                    "geometry": {"length_m": 0.2},
                    "cg_offset_m": 0.1,
                },
                {
                    "id": "rear",
                    "mass_kg": 1.0,
                    "position_m": 2.0,
                    "geometry": {"length_m": 0.2},
                    "cg_offset_m": 0.1,
                },
            ],
        },
    )
    record = tmp_path / "record.json"
    write(record, {"candidate_identity": "synthetic"})
    audit = tmp_path / "audit.json"
    write(
        audit,
        {
            "input_sha256_before": {str(source): sha(source), str(curve): sha(curve)},
            "peak_motor_flank": {
                "time_s": 0.135,
                "thrust_n": 40.0,
                "motor_mass_kg": 1.0,
                "mass_with_full_growth_kg": 4.0,
                "motor_flank_n": 30.0,
            },
        },
    )
    config = tmp_path / "config.yaml"
    config.write_text(
        yaml.safe_dump(
            {
                "candidate": str(source),
                "candidate_sha256": sha(source),
                "candidate_record": str(record),
                "candidate_identity": "synthetic",
                "support_audit": str(audit),
                "design_factor": 3,
                "contact_station_m_assumed": 1.0,
                "cuts_m": [0.5, 1.5],
                "growth_kg": 1.0,
                "paper_strength_mpa": 2.0,
                "shell_section_mm2": 100.0,
            }
        )
    )
    result = run(config)
    assert abs(result["motor_balance_residual_n"]) < 1e-10
    assert abs(result["whole_nonmotor_balance_residual_n"]) < 1e-10
    assert result["effective_axial_specific_force_m_s2"] == pytest.approx(10.0)
    assert result["vertical_no_drag_kinematic_acceleration_m_s2"] == pytest.approx(0.19335)
    assert result["assumed_contact_n"] == pytest.approx(30.0)
    before, after = result["rows"]
    assert before["assumed_motor_contact_forward_n"] == 0
    assert after["assumed_motor_contact_forward_n"] == pytest.approx(30.0)
    assert before["combined_cut_force_n_bounds_noseward_positive"] == pytest.approx([10.0, 20.0])
    assert after["combined_cut_force_n_bounds_noseward_positive"] == pytest.approx([-20.0, -10.0])
    assert before["df3_force_n_bounds"] == pytest.approx([30.0, 60.0])
    assert all(row["shell_share_n"] is None for row in result["rows"])
    assert all(row["rail_share_n"] is None for row in result["rows"])
    step_result = run(config, {"front": (0.0, 0.2, 0.1), "rear": (2.0, 2.2, 2.1)})
    assert step_result["rows"][0]["combined_cut_force_n_bounds_noseward_positive"] == pytest.approx(
        [10.0, 20.0]
    )
