"""Independent dimensions/force bookkeeping for the bounded A1 packet."""

import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-a1-connections-20261102-v1"


def test_known_clearance_stacks_have_independent_expected_answers():
    spec = importlib.util.spec_from_file_location(
        "a1_script", ROOT / "scripts/wo03_a1_connections.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # A100/98mm diameter fit, +/-0.1mm per radius and0.25mm explicit loss.
    answer = module.radial_bounds(50, 49, 0.1, 0.1, 0.1, 0.05)
    assert answer["minimum_cold_mm"] == pytest.approx(0.8)
    assert answer["minimum_bounded_mm"] == pytest.approx(0.55)
    assert answer["maximum_bounded_mm"] == pytest.approx(1.45)
    assert module.radial_bounds(32.2, 32, 0.1)["minimum_cold_mm"] == pytest.approx(0, abs=1e-12)


def test_complete_mass_force_and_first_moment_use_one_ledger():
    if not RUN.exists():
        pytest.skip("Pre-execution: no bounded packet has run")
    r = json.loads((RUN / "record.json").read_text())
    old = json.loads(
        (ROOT / "runs/wo03-architecture-space-mass-20261102-v1/record.json").read_text()
    )["arrangements"][0]
    rows = r["replacement_ledger"]
    assert len({x["id"] for x in rows}) == len(rows)
    delta = math.fsum(x["mass_delta_g"] for x in rows)
    first = math.fsum(x["mass_delta_g"] * x["station_mm"] for x in rows)
    for c, b in zip(r["complete_cases"], old["cases"], strict=True):
        assert c["total_g"] == pytest.approx(b["total_g"] + delta)
        assert c["total_g"] * c["cg_mm"] == pytest.approx(b["total_g"] * b["cg_mm"] + first)
        assert c["severe_recovery_DF3_N"] == pytest.approx(
            max(1782.253, 3 * c["total_g"] / 1000 * (20.4**2 / 0.6 + 9.80665))
        )
        assert c["separate_growth_g"] == 50
        assert c["full_intrinsic_inertia"] is None and c["validated_new_cp_mm"] is None
    assert r["complete_cases"][1]["total_g"] - r["complete_cases"][0]["total_g"] == pytest.approx(
        20
    )
    assert r["section_demands"]["root_outer_reaction_N"] + r["section_demands"][
        "root_inner_reaction_N"
    ] == pytest.approx(220.75869590217366)


def test_admission_and_provenance_do_not_turn_bounds_into_qualification():
    if not RUN.exists():
        pytest.skip("Pre-execution: no bounded packet has run")
    import hashlib

    from src.api.workbench import build_workbench

    r = json.loads((RUN / "record.json").read_text())
    archives = json.loads(
        (
            ROOT / "runs/wo03-c2-sandwich-socket-20261102-v2/source-dependencies/manifest.json"
        ).read_text()
    )
    for path, expected in r["input_sha256"].items():
        if path == "web/public/engineering-workbench/g80-c1.json":
            data = (json.dumps(build_workbench(), indent=2, allow_nan=False) + "\n").encode()
        elif path.startswith("build/"):
            data = (ROOT / archives[path]["archive_path"]).read_bytes()
        else:
            data = (ROOT / path).read_bytes()
        assert hashlib.sha256(data).hexdigest() == expected, path
    assert r["status"].startswith("not_admitted")
    assert r["section_demands"]["qualified_drilled_G11_bearing_pa"] is None
    assert r["resources"]["CAD_FEA_heat_freeflight"] is False
    assert r["resources"]["cpu_s"] < 20 and r["resources"]["wall_s"] < 30
    assert r["space"]["old_R24_harness_min_in_new_sleeve_mm"] < 0.1
    assert r["space"]["routed_R21_harness_min_in_sleeve_mm"] > 0.1
    assert r["space"]["angular_gap_between_legs_and_inner_doublers_deg"] > 0
