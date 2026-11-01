import math
import struct

import pytest

from scripts.wo03_ccx_backend_diagnostic import parse_vector_fields, transform


def block(field, nodes):
    labels = ("D1", "D2", "D3", "ALL") if field == "DISP" else ("F1", "F2", "F3", "ALL")
    head = f" -4  {field}        4    1\n".encode()
    head += b"".join(f" -5  {label} 1 2 1 0\n".encode() for label in labels)
    return head + b"".join(struct.pack("<ifff", *n) for n in nodes)


def sample():
    nodes = [(1, 0.0, 1.0, 2.0), (2, -1.0, 0.0, 3.0)]
    parts = []
    for i, field in enumerate(("DISP", "FORC", "DISP", "FORC")):
        step = i // 2 + 1
        h = bytearray(b" " * 70)
        h[:10] = b"    1PSTEP"
        for off, val in [(24, i + 1), (36, 1), (48, step)]:
            h[off : off + 12] = f"{val:12d}".encode()
        c = bytearray(b" " * 75)
        c[:7] = b"  100CL"
        c[12:24] = f"{step:12.9f}".encode()
        c[24:36] = f"{2:12d}".encode()
        c[74:75] = b"2"
        parts.append(bytes(h) + b"\n" + bytes(c) + b"\n" + block(field, nodes))
    return b"".join(parts) + b" 9999\n"


def test_reversible_whitelist():
    raw = "*STEP\n*STATIC\n*END STEP\n" * 2
    assert transform(raw, False).count("*NODE OUTPUT\nU,RF\n") == 2
    assert transform(raw, True).count("*STATIC,SOLVER=ITERATIVE CHOLESKY") == 2
    with pytest.raises(ValueError):
        transform(raw + "*NODE OUTPUT\n", False)


def test_strict_vector_decoder():
    x = sample()
    result = parse_vector_fields(x, [1, 2])
    assert result[0]["values"][2] == (-1.0, 0.0, 3.0)
    with pytest.raises(ValueError):
        parse_vector_fields(x, [1, 3])
    with pytest.raises(ValueError):
        parse_vector_fields(x[:-2], [1, 2])
    with pytest.raises(ValueError):
        parse_vector_fields(
            sample().replace(struct.pack("<f", 3.0), struct.pack("<f", math.nan)), [1, 2]
        )


def test_reject_step_mismatch_and_wrong_endian():
    x = sample()
    marker = b"    1PSTEP"
    pos = x.find(marker)
    bad = bytearray(x)
    bad[pos + 48 : pos + 60] = f"{2:12d}".encode()
    with pytest.raises(ValueError):
        parse_vector_fields(bytes(bad), [1, 2])
    pos = x.find(struct.pack("<ifff", 1, 0.0, 1.0, 2.0))
    bad = bytearray(x)
    bad[pos : pos + 4] = struct.pack(">i", 1)
    with pytest.raises(ValueError):
        parse_vector_fields(bytes(bad), [1, 2])


def test_saved_b_dat_synthetic_binary_gates(tmp_path):
    import json
    from pathlib import Path

    from scripts.wo03_ccx_backend_diagnostic import assess_b
    from scripts.wo03_g80_bridge_fea import parse_native_dat

    root = Path(__file__).resolve().parents[1]
    base = root / "build/wo03-ccx-reaction-fixture-preflight-v6-b"
    dat = root / "build/wo03-ccx-reaction-native-b-diagnostic-v1/B/case.dat"
    if not dat.exists() or not (base / "mesh-meta.json").exists():
        pytest.skip("Local saved fixture is not distributed")
    meta = json.loads((base / "mesh-meta.json").read_text())
    parsed = parse_native_dat(dat)
    parts = []
    for i, (step, field, key) in enumerate(
        (
            (1, "DISP", "displacements"),
            (1, "FORC", "forces"),
            (2, "DISP", "displacements"),
            (2, "FORC", "forces"),
        )
    ):
        h = bytearray(b" " * 70)
        h[:10] = b"    1PSTEP"
        for off, val in ((24, i + 1), (36, 1), (48, step)):
            h[off : off + 12] = f"{val:12d}".encode()
        c = bytearray(b" " * 75)
        c[:7] = b"  100CL"
        c[12:24] = f"{step:12.9f}".encode()
        c[24:36] = f'{meta["node_count"]:12d}'.encode()
        c[74:75] = b"2"
        nodes = [(row["id"], *row["values"]) for row in parsed[(step, key, "ALL")]]
        parts.append(bytes(h) + b"\n" + bytes(c) + b"\n" + block(field, nodes))
    frd = tmp_path / "synthetic.frd"
    frd.write_bytes(b"".join(parts) + b" 9999\n")
    got = assess_b(meta, (base / "case.inp").read_text(), dat, frd)
    assert len(got["steps"]) == 2
    assert all(s["force_status"] in ("pass", "unavailable_precision") for s in got["steps"])


def test_extra_field_rejected():
    with pytest.raises(ValueError):
        parse_vector_fields(sample() + b" -4  EXTRA 1 1\n", [1, 2])
