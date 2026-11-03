"""F2-C1 frozen sources and complete-proposal boundaries, no solver execution."""

import hashlib
import json
from pathlib import Path

import pytest

from src.vehicle.schema import load_vehicle

ROOT = Path(__file__).resolve().parents[1]


def test_f2_c1_changes_no_frozen_vehicle_and_keeps_full_allowances():
    original = ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml"
    assert (
        hashlib.sha256(original.read_bytes()).hexdigest()
        == "7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78"
    )
    r = json.loads((ROOT / "runs/wo03-g80-f2-c1-definition-20261103-v1/record.json").read_text())
    p = ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"
    assert r["proposal_spec_sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
    assert r["reuse"]["checked_numeric_equivalence"] and not r["adopted"]
    assert r["physical_full_inertia"] is None
    cases = [c for c in r["cases"] if c["variant"] == "C1_fit_proposal"]
    assert [c["total_mass_kg"] for c in cases] == pytest.approx([0.918750003, 0.938750003])
    assert all(c["growth_kg"] == 0.05 for c in cases)
    assert cases[1]["extra_aft_kg"] == 0.02 and cases[1]["motor_cg_probe_m"] == 0.0128
    assert all(15 < c["guide_mps"]["1.5"] < 15.5 for c in cases)
    assert all(
        c["margin_cal"] > 1 and c["formal_mass_headroom_g"] > 0 > c["planning_mass_headroom_g"]
        for c in cases
    )


def test_conditional_fits_cannot_become_measured_or_strength_acceptance():
    r = json.loads((ROOT / "runs/wo03-g80-f2-c1-definition-20261103-v1/record.json").read_text())
    assert len(r["fits"]) == 7 and all(
        f["minimum_mm"] >= 0.1 and not f["measured"] and not f["environmental_bounds_verified"]
        for f in r["fits"]
    )
    before = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml")
    after = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml")
    old = {p.id: p for p in before.parts}
    new = {p.id: p for p in after.parts}
    assert all(new[i].resolved_mass_kg == p.resolved_mass_kg for i, p in old.items())
    assert sum(p.resolved_mass_kg for i, p in new.items() if i not in old) * 1000 == pytest.approx(
        1.190021618
    )
    assert r["wood_removal_mass_credit_g"] == 0
    assert new["forward_ring"].cad.parameters["notch_width_m"] == 0.0066
    assert new["forward_ring"].cad.generator.startswith("unadmitted_")
