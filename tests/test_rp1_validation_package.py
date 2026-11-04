"""Prevent an inquiry packet from becoming a fictitious priced/executed test."""

import hashlib
import json
from decimal import Decimal

import pytest
import yaml

from scripts.wo03_rp1_vp1_package import PLAN, ROOT, fixture_pair, subtotal


def test_price_arithmetic_keeps_unquoted_service_unavailable():
    p = yaml.safe_load(PLAN.read_text())
    assert subtotal(p["materials"]) == Decimal("269.49")
    assert subtotal(p["materials"], p["initial_room_only_material_order"]) == Decimal("236.75")
    assert p["financial_basis"]["expected_full_programme_total_usd"] is None
    assert p["financial_basis"]["first_authorization_total_usd"] == 0
    assert not any(
        p[k]
        for k in (
            "purchase_authorized",
            "physical_work_authorized",
            "supplier_contact_authorized",
            "paid_service_authorized",
        )
    )


def test_root_input_pair_balances_without_tip_force_or_extra_factor():
    f1, f2 = fixture_pair(331.125, 8.83, 0.01, 0.04)
    assert f1 + f2 == pytest.approx(331.125)
    assert 0.01 * f1 + 0.04 * f2 == pytest.approx(8.83)
    assert f1 == pytest.approx(147.1666666667)
    assert f2 == pytest.approx(183.9583333333)
    with pytest.raises(ValueError):
        fixture_pair(331.125, 8.83, 0.04, 0.01)
    # Moment-only tip loading would understate the required resultant.
    assert 8.83 / 0.06 < f1 + f2


def test_packet_identity_and_method_limits_are_preserved():
    p = yaml.safe_load(PLAN.read_text())
    record = json.loads((ROOT / "docs/validation/rp1-vp1/accounting.json").read_text())
    assert hashlib.sha256(PLAN.read_bytes()).hexdigest() == record["plan_sha256"]
    assert (
        hashlib.sha256((ROOT / "scripts/wo03_rp1_vp1_package.py").read_bytes()).hexdigest()
        == record["producer_sha256"]
    )
    assert record["three_indicator_instrument_MPE_bound_mm"] > 0.01
    assert record["MPE_bound_is_combined_U95"] is False
    assert record["coupon_minimum_dimensions_load_cap_N"] == pytest.approx(9.34444444444)
    assert p["preserved"]["fin_moment_Nm"] == 8.83
    assert p["preserved"]["tip_movement_limit_mm"] == 1
    assert p["preserved"]["separate_growth_g"] == 50
    assert p["protocol"]["home_triage_can_qualify_joint_or_G"] is False
    assert not p["protocol"]["distributed_panel_loading_verified"]
    messages = sorted((ROOT / "docs/validation/rp1-vp1/messages").glob("*.txt"))
    assert len(messages) == 5
    assert all("UNSENT" in m.read_text() for m in messages)
