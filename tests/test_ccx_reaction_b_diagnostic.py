"""B diagnostic classifies print precision without changing strict tolerance."""

import pytest

from scripts.wo03_ccx_reaction_b_diagnostic import classify


def test_unavailable_print_precision_is_not_a_pass():
    step = lambda n, s: {
        "step": n,
        "support_balance": {"force_balance_status": s},
        "free_end": [{"passed": True}],
    }
    assert (
        classify({"steps": [step(1, "unavailable_print_precision"), step(2, "pass")]})
        == "diagnostic_complete_strict_force_unavailable"
    )
    assert (
        classify({"steps": [step(1, "pass"), step(2, "pass")]})
        == "diagnostic_complete_strict_force_pass"
    )
    with pytest.raises(ValueError, match="imbalance"):
        classify({"steps": [step(1, "fail"), step(2, "pass")]})
    with pytest.raises(ValueError, match="displacement"):
        classify(
            {
                "steps": [
                    step(1, "pass"),
                    {
                        "step": 2,
                        "support_balance": {"force_balance_status": "pass"},
                        "free_end": [{"passed": False}],
                    },
                ]
            }
        )
