"""Strict D native classification does not treat uncertain print as pass."""

import pytest

from scripts.wo03_ccx_poisson_native import classify


def test_classification_preserves_unavailable_and_rejects_bad_output():
    def step(n, force="pass", support="pass", disp=True):
        return {
            "step": n,
            "total_reaction_plus_applied_from_all_RF": {"force_balance_status": force},
            "bottom_support_rf_z_status": support,
            "bars": [{"displacement_pass": disp}],
        }

    assert classify({"steps": [step(1), step(2)]}) == "diagnostic_complete_strict_force_pass"
    assert (
        classify({"steps": [step(1, "unavailable_print_precision"), step(2)]})
        == "diagnostic_complete_strict_force_unavailable"
    )
    with pytest.raises(ValueError, match="imbalance"):
        classify({"steps": [step(1, "fail"), step(2)]})
    with pytest.raises(ValueError, match="Displacement"):
        classify({"steps": [step(1), step(2, disp=False)]})
