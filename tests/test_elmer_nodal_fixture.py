import pytest

from scripts.wo03_elmer_nodal_fixture import cload, replace_traction


def test_preserves_source_tokens_and_replaces_only_traction():
    deck = "*STEP\n*CLOAD,OP=NEW\n1,3,2\n*END STEP\n*STEP\n*CLOAD,OP=NEW\n7,3,-2.0643179024326e-05\n8,3,150.000020643179\n*END STEP\n"
    loads = cload(deck)
    base = "header\n" + "".join(
        f"Boundary Condition {i}\n  Target Boundaries(1) = {i}\n  Force 3 = Real {v}\nEnd\n"
        for i, v in ((1, "9375000"), (2, "0"), (3, "0"))
    )
    out = replace_traction(base, loads)
    assert out.startswith("header\n")
    assert "Target Nodes(1) = 7\n  Displacement 3 Load = Real -2.0643179024326e-05\n" in out
    assert "Force 3 = Real" not in out
    with pytest.raises(ValueError):
        replace_traction(base.replace("9375000", "1"), loads)


def test_duplicate_or_nonaxial_loads_rejected():
    deck = "*STEP\n*CLOAD,OP=NEW\n1,3,2\n*END STEP\n*STEP\n*CLOAD,OP=NEW\n7,3,2\n7,3,3\n*END STEP\n"
    with pytest.raises(ValueError):
        cload(deck)
    with pytest.raises(ValueError):
        cload(deck.replace("7,3,3", "8,2,3"))
