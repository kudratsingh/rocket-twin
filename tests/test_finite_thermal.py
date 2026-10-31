"""Condensation algebra and explicit thermal-state/reservoir mapping checks."""

from __future__ import annotations

import numpy as np
import pytest

from src.analysis.finite_radiation import MaterialRadiationAdapter, condense_radiosity, radiosity


def test_condensed_arbitrary_temperature_groups_match_direct_radiosity() -> None:
    # A reciprocal stochastic fixture with two patches sharing one temperature.
    # This is an algebra fixture, not a claimed finite rocket geometry.
    view = np.array(
        [[0, 0.5, 0.25, 0.25], [0.5, 0, 0.25, 0.25], [0.25, 0.25, 0, 0.5], [0.25, 0.25, 0.5, 0]]
    )
    areas = np.ones(4)
    eps = np.array([0.2, 0.6, 0.9, 1.0])
    operator = condense_radiosity(
        view, areas, eps, ["material_a", "material_a", "material_b", "reservoir"]
    )
    for temperatures in ([550, 310, 290], [300, 650, 370], [350, 350, 350]):
        nodes = np.array(temperatures, dtype=float)
        direct = radiosity(view, areas, nodes[operator.patch_node_index], eps)
        expected = np.bincount(operator.patch_node_index, weights=-direct["net_outward_w"])
        actual = operator.heat_rates(nodes)
        assert actual == pytest.approx(expected, abs=1e-9)
        assert actual == pytest.approx(operator.inward_operator_w_k4 @ nodes**4, abs=1e-9)
        assert sum(actual) == pytest.approx(0, abs=1e-9)
    assert np.array_equal(operator.heat_rates([350, 350, 350]), np.zeros(3))
    assert np.max(abs(operator.inward_operator_w_k4.sum(axis=0))) < 1e-20


def test_adapter_declares_exclusions_and_rejects_missing_or_reordered_state() -> None:
    names = ["material", "motor_case_boundary", "fore_end_reservoir", "aft_end_reservoir"]
    operator = condense_radiosity(
        np.full((4, 4), 0.25), np.ones(4), np.array([0.9, 0.9, 1.0, 1.0]), names
    )
    adapter = MaterialRadiationAdapter(
        operator,
        ["material", "excluded_capacity"],
        {"fore_end_reservoir": "ambient", "aft_end_reservoir": "case"},
        {"scope": "fixture"},
    )
    q, external, links = adapter.rates(
        [350, 330], case_temperature_k=500, ambient_temperature_k=300
    )
    assert q[1] == 0
    assert external == pytest.approx(sum(q))
    assert len(links) > 0
    assert adapter.metadata()["radiation_excluded_thermal_nodes"] == ["excluded_capacity"]
    assert adapter.metadata()["transient_acceptance_available"] is False
    with pytest.raises(ValueError, match="identities/order"):
        adapter.validate_nodes(["excluded_capacity", "material"])
    with pytest.raises(ValueError, match="Missing/invalid"):
        adapter.rates([350, np.nan], case_temperature_k=500, ambient_temperature_k=300)
    with pytest.raises(ValueError, match="reciprocal"):
        condense_radiosity([[0, 1], [0.5, 0.5]], [1, 1], [0.9, 0.9], ["a", "b"])
