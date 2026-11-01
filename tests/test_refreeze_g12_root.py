"""Checks comparison bookkeeping without CAD or archived build artifacts."""

import pytest

from scripts.wo03_refreeze_g12_root import difference


def test_maximum_absolute_component_difference():
    assert difference([[1.0, 2.0], [3.0, 4.0]], [[1.0, 2.5], [2.0, 4.0]]) == 1.0
    assert difference(None, 2.0) is None
    with pytest.raises(ValueError):
        difference([1.0], [1.0, 2.0])
