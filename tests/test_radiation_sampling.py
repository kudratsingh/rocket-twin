"""Fixed-area likelihood versus an independent scalar constrained optimum."""

import numpy as np
import pytest
from scipy.optimize import brentq

from src.analysis.radiation_sampling import reciprocal_counts


def test_unequal_area_two_surface_likelihood_and_support() -> None:
    counts = np.array([[100, 900], [80, 920]])
    area = np.array([1.0, 10.0])
    # Only one free exchange-area scalar x under reciprocal closure.
    optimum = brentq(lambda x: 980 / x - 100 / (1 - x) - 920 / (10 - x), 1e-8, 1 - 1e-8, xtol=1e-14)
    result, diagnostics = reciprocal_counts(counts, area)
    assert result[0, 1] == pytest.approx(optimum, abs=2e-11)
    assert result[1, 0] == pytest.approx(optimum / 10, abs=2e-12)
    assert result.sum(axis=1) == pytest.approx(1, abs=1e-11)
    assert diagnostics["likelihood_deviance_vs_unconstrained"] >= 0
    # Increasing all counts leaves the point estimate unchanged.
    larger, _ = reciprocal_counts(counts * 100, area)
    assert larger == pytest.approx(result, abs=1e-12)
    support = np.array([[50, 40, 0], [20, 50, 30], [0, 20, 50]])
    f, _ = reciprocal_counts(support, [1, 2, 3])
    assert f[0, 2] == f[2, 0] == 0
    with pytest.raises(ValueError, match="counts"):
        reciprocal_counts(np.zeros((2, 2), dtype=int), area)
    with pytest.raises(RuntimeError, match="closure"):
        reciprocal_counts(counts, area, max_iterations=1)
