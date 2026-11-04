"""Independent elementary beam answers and preserved FR1 admission boundaries."""

import hashlib
import json
import math
from pathlib import Path

import numpy as np
import pytest

from scripts.wo03_rp1_fin_root import supported_root
from src.vehicle.schema import Vehicle, load_vehicle

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "runs/wo03-rp1-fin-root-20261104-v1"


def test_root_beam_known_answers_and_reciprocal_work():
    E, t, g = 2e9, 0.003, 0.017451
    ei = E * 0.1094 * t**3 / 12
    force = supported_root(10, 0, E, t, 0, 1e30, 1e30)
    assert force["body_translation_m"] == pytest.approx(10 * g**3 / (3 * ei))
    assert force["body_rotation_rad"] == pytest.approx(10 * g**2 / (2 * ei))
    couple = supported_root(0, 2, E, t, 0, 1e30, 1e30)
    assert couple["body_translation_m"] == pytest.approx(2 * g**2 / (2 * ei))
    assert couple["body_rotation_rad"] == pytest.approx(2 * g / ei)
    pin = supported_root(10, 2, E, t, 1e30, 1e30, 1e30)
    assert pin["body_translation_m"] == pytest.approx(0, abs=1e-15)
    assert pin["body_rotation_rad"] == pytest.approx(2 * g / (4 * ei))
    c = supported_root(10, 2, E, t, 1e6, 1e7, 200)["compliance"]
    assert c[0][1] == c[1][0]
    assert min(np.linalg.eigvalsh(c)) > 0


def test_load_provenance_is_not_silently_relaxed():
    r = json.loads((FOLDER / "record.json").read_text())
    l = r["load_trace"]
    assert l["retained_M_Nm"] == 8.83
    assert l["retained_F_N"] == pytest.approx(331.125)
    area = 0.06 * (0.13 + 0.065) / 2
    ar = 2 * 0.06**2 / area
    f = 40000 * area * (2 * math.pi * ar / (2 + math.sqrt(4 + ar**2))) * math.radians(5) * 3
    assert l["direct_40kPa_5deg_DF3_F_N"] == pytest.approx(f)
    assert l["direct_40kPa_5deg_DF3_M_Nm"] == pytest.approx(2.90525502506)
    assert not l["revision_adopted"]


def test_no_rigid_support_or_unknown_material_becomes_acceptance():
    r = json.loads((FOLDER / "record.json").read_text())
    assert not r["adopted"]
    assert r["physical_inertia"] is None
    for p in r["structural_sensitivity"]:
        assert p["qualified_strength_pass"] is None
        assert p["qualified_movement_pass"] is None
        for c in p["finite_roots"]:
            assert c["total_tip_mm"] > 1
            assert abs(c["force_balance_residual_N"]) < 1e-10
            assert abs(c["moment_balance_residual_Nm"]) < 1e-10
    s = json.loads((FOLDER / "joint-supplement.json").read_text())
    assert s["body_one_face_area_mm2"] == pytest.approx(129.9 * 5.8)
    assert not s["body_single_face_screen_pass"]
    assert s["complete_installed_movement"] is None
    assert s["aft_tab_end"]["qualified_capacity_or_stiffness"] is None
    assert not s["aft_tab_end"]["direct_butt_contact"]


def test_complete_ledger_harness_stock_and_allowance_cases():
    r = json.loads((FOLDER / "record.json").read_text())
    assert len(r["ledger"]) == len({p["id"] for p in r["ledger"]})
    assert sum(p["mass_g"] for p in r["ledger"]) == pytest.approx(r["physical_mass_g"])
    assert r["wood_purchase_retained_and_reallocated_usd"] == 69.75
    assert len(r["cases"]) == 8
    for c in r["cases"]:
        assert c["growth_g"] == 50
        assert c["extra_aft_g"] == (20 if c["case"] == "adverse" else 0)
        assert c["motor_cg_probe_mm"] == (12.8 if c["case"] == "adverse" else 0)
        assert not c["nylon_probe_is_bound"]
        assert c["guide_mps"]["1.5"] >= 15
        assert c["guide_mps"]["1.5"] < 15.5
    for p, h in r["sources"].items():
        assert hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h


def test_monolithic_carbon_is_nonmetallic_without_allowing_metal_fin():
    v = load_vehicle(ROOT / "configs/vehicle/candidates/g80-rp1-fr1.yaml")
    assert next(p for p in v.parts if p.id == "fin_set").material == "carbon_epoxy"
    d = v.model_dump(by_alias=True)
    next(p for p in d["parts"] if p["id"] == "fin_set")["material"] = "aluminum"
    with pytest.raises(ValueError, match="structural material must be nonmetallic"):
        Vehicle.model_validate(d)
