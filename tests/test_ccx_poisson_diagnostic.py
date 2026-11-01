"""Independent substitution and all-node reaction-accounting checks."""

import numpy as np
import pytest

from scripts.wo03_ccx_poisson_diagnostic import (
    assess_saved_output,
    modified_deck,
    reference_displacement,
    reference_tensor,
)


def test_uniaxial_strain_hooke_substitution():
    for young in (100.0, 10000.0):
        tensor = reference_tensor(50.0, 16.0, young, 0.3)
        sigma = 50 / 16
        np.testing.assert_allclose(
            tensor["stress_components_MPa"],
            [sigma * 0.3 / 0.7, sigma * 0.3 / 0.7, sigma, 0, 0, 0],
            atol=1e-12,
        )
        assert tensor["effective_axial_modulus_MPa"] == pytest.approx(young * 1.346153846153846)
    assert reference_displacement(50.0, 20.0, 16.0, 0.3) == pytest.approx(0.2344642857142857)
    assert reference_displacement(150.0, 20.0, 16.0, 0.3) == pytest.approx(0.7033928571428571)
    assert reference_displacement(50.0, 10.0, 16.0, 0.3) == pytest.approx(
        reference_displacement(50.0, 10.0 - 1e-12, 16.0, 0.3), abs=1e-12
    )


def test_only_three_deck_edits_and_reject_duplicate():
    src = b"*ELASTIC\n100,0\n*ELASTIC\n10000,0\n*BOUNDARY\nSUPPORT,1,3,0\n"
    result = modified_deck(src)
    assert b"*ELASTIC\n100,0.3\n" in result
    assert b"*ELASTIC\n10000,0.3\n" in result
    assert b"SUPPORT,1,3,0\nALL,1,2,0\n" in result
    with pytest.raises(ValueError, match="unique"):
        modified_deck(src + b"*ELASTIC\n100,0\n")


def test_all_rf_subtracts_applied_before_reaction_balance(tmp_path, monkeypatch):
    coords = {
        1: [-10, 0, 0],
        2: [-10, 0, 20],
        3: [0, 0, 0],
        4: [0, 0, 20],
        5: [10, 0, 0],
        6: [10, 0, 20],
    }
    lines = ["*NODE"] + [f"{n},{v[0]},{v[1]},{v[2]}" for n, v in coords.items()]
    lines += ["*CLOAD", "2,3,50", "4,3,50", "6,3,50", "*CLOAD", "2,3,150"]
    path = tmp_path / "case.inp"
    path.write_text("\n".join(lines) + "\n")
    meta = {"support_node_ids": [1, 3, 5], "bar_node_ids_by_bar": [[1, 2], [3, 4], [5, 6]]}

    def row(n, z):
        return {"id": n, "values": [0.0, 0.0, z], "rounding_half_width": [1e-12] * 3}

    data = {}
    for step in (1, 2):
        force = [50, 50, 50] if step == 1 else [150, 0, 0]
        uz = {n: reference_displacement(force[(n - 2) // 2], 20, 16, 0.3) for n in (2, 4, 6)}
        values = {1: -force[0], 2: force[0], 3: -force[1], 4: force[1], 5: -force[2], 6: force[2]}
        data[(step, "displacements", "ALL")] = [row(n, uz.get(n, 0)) for n in coords]
        data[(step, "forces", "ALL")] = [row(n, values[n]) for n in coords]
        data[(step, "forces", "SUPPORT")] = [row(n, values[n]) for n in (1, 3, 5)]
    monkeypatch.setattr("scripts.wo03_ccx_poisson_diagnostic.parse_native_dat", lambda _p: data)
    result = assess_saved_output(meta, path, tmp_path / "none")
    assert result["status"] == "passed"
    assert (
        result["steps"][0]["total_reaction_plus_applied_from_all_RF"]["force_residual_norm_N"] == 0
    )
    data[(1, "forces", "ALL")][0]["values"][2] += 0.5
    assert assess_saved_output(meta, path, tmp_path / "none")["status"] == "failed_or_unavailable"
