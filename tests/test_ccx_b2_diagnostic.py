from types import SimpleNamespace

import pytest

from scripts.wo03_ccx_b2_diagnostic import field_consistency, run_b2


def test_b2_is_disabled():
    with pytest.raises(ValueError, match="not admitted"):
        run_b2({"native_execution_authorized": False})


def test_detects_per_node_field_disagreement(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.write_bytes(b"A")
    b.write_bytes(b"B")

    def fields(raw, ids):
        delta = 0.01 if raw == b"B" else 0.0
        return [
            {"field": name, "step": step, "values": {1: (delta, 0.0, 0.0)}}
            for step, name in ((1, "DISP"), (1, "FORC"), (2, "DISP"), (2, "FORC"))
        ]

    reader = SimpleNamespace(parse_vector_fields=fields, float32_radius=lambda x: 1e-8)
    row = {"id": 1, "rounding_half_width": [1e-7] * 3}
    data = {(step, name, "ALL"): [row] for step in (1, 2) for name in ("displacements", "forces")}
    differing = field_consistency(
        {"node_coordinates_mm": {"1": [0, 0, 0]}}, a, a, b, b, reader, lambda _: data
    )
    assert differing[0]["nodes"][0]["diagnostic_pass"] is None
    assert differing[1]["nodes"][0]["diagnostic_pass"] is False
    assert (
        len(
            field_consistency(
                {"node_coordinates_mm": {"1": [0, 0, 0]}}, a, a, a, a, reader, lambda _: data
            )
        )
        == 4
    )
