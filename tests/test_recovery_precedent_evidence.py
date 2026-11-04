"""Frozen source, coupled-budget and explicit admission boundaries; no solver."""

import hashlib
import json
import math
from pathlib import Path

import pytest
import yaml

from src.vehicle.schema import load_vehicle

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-f2-recovery-precedent-20261103-v1/record.json"


def test_rp1_replacement_is_once_only_and_historical_source_is_frozen():
    r = json.loads(RUN.read_text())
    for path, expected in r["sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    old = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml")
    new = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-rp1-wrap.yaml")
    before = {p.id: p for p in old.parts}
    after = {p.id: p for p in new.parts}
    assert before.keys() - after.keys() == {"body_recovery_eye", "heat_leader"}
    assert set(r["removal_functions"]) == before.keys() - after.keys()
    assert r["removal_credit_g"] == 26 and r["new_cut_mass_credit_g"] == 0
    assert len(r["ledger"]) == len(after) == len({p["id"] for p in r["ledger"]})
    for pid in before.keys() & after.keys() - {"shock_cord", "forward_ring"}:
        assert before[pid].resolved_mass_kg == after[pid].resolved_mass_kg
    assert sum(p["mass_g"] for p in r["ledger"]) / 1000 + 0.05 == pytest.approx(
        r["cases"][0]["total_mass_kg"]
    )
    assert r["addition_mass_g"] - r["removal_credit_g"] == pytest.approx(r["delta_mass_g"])


def test_failed_departure_and_required_load_cannot_become_adoption():
    r = json.loads(RUN.read_text())
    assert not r["adopted"] and r["physical_full_inertia"] is None
    nominal, adverse = r["cases"]
    assert nominal["growth_kg"] == adverse["growth_kg"] == 0.05
    assert adverse["extra_aft_kg"] == 0.02 and adverse["motor_cg_probe_m"] == 0.0128
    assert adverse["total_mass_kg"] - nominal["total_mass_kg"] == pytest.approx(0.02)
    for c in r["cases"]:
        assert c["guide_mps"]["1.5"] < 15
        assert c["formal_mass_headroom_g"] < 0 and c["planning_mass_headroom_g"] < 0
        assert c["required_whole_mean_proxy_N"] == pytest.approx(
            3 * c["total_mass_kg"] * (20.4**2 / (2 * 0.3) + 9.80665)
        )
        assert 0 < c["required_body_proxy_N"] < c["required_whole_mean_proxy_N"]
    assert 0 < r["maximum_main_cord_mass_g_adverse_formal"] < 55
    assert r["maximum_main_cord_mass_g_adverse_planning"] < 0
    assert r["label_only_strength_N"]["LOC3/16nylon"] < adverse["required_whole_mean_proxy_N"]


def test_ring_move_and_sources_keep_unverified_connections_explicit():
    new = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-rp1-wrap.yaml")
    p = {part.id: part for part in new.parts}
    assert (
        p["forward_ring"].position_m + p["forward_ring"].geometry["length_m"]
        < p["fin_tabs"].position_m
    )
    assert p["fin_tabs"].cad.parameters["front_ring_support_available"] is False
    assert p["forward_ring"].cad.generator.startswith("unadmitted_")
    assert not p["rp1_kevlar_wrap"].cad.parameters["knot_envelope_verified"]
    sources = yaml.safe_load(
        (ROOT / "configs/studies/f2-recovery-precedents-primary.yaml").read_text()
    )
    assert len(sources["sources"]) == sources["budget"]["actual_unique_direct_urls"] == 12
    assert all(s["supported_scope"] and s["source_class"] for s in sources["sources"])
    r = json.loads(RUN.read_text())
    assert all(math.isfinite(c["cg_m"]) for c in r["cases"])


def test_single_balance_correction_replaces_only_ballast_function_and_keeps_gates():
    run = ROOT / "runs/wo03-f2-recovery-balanced-20261103-v2/record.json"
    r = json.loads(run.read_text())
    for path, expected in r["sources"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == expected
    before = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-rp1-wrap.yaml")
    after = load_vehicle(ROOT / "configs/vehicle/candidates/g80-f2-rp1-balanced.yaml")
    old = {p.id: p for p in before.parts}
    new = {p.id: p for p in after.parts}
    assert old.keys() - new.keys() == {"nose_ballast", "ballast_capsule"}
    assert new["nose_service_hardware"].resolved_mass_kg == 0.003
    assert new["rp1_kevlar_wrap"].cad.parameters["raw_length_m"] == 1.8288
    assert 1.8288 - 0.45 - 0.93 > 0.3
    assert r["addition_mass_g"] - r["removal_credit_g"] == pytest.approx(r["delta_mass_g"])
    for c in r["cases"]:
        assert c["growth_kg"] == 0.05
        assert 15 < c["guide_mps"]["1.5"] < 15.5
        assert c["margin_cal"] > 1 and c["burnout_margin_cal"] > 1
        assert c["aft_stowage_sensitivity"]["margin_cal"] > 1
        assert c["formal_mass_headroom_g"] > 0 > c["planning_mass_headroom_g"]
    assert r["cases"][1]["extra_aft_kg"] == 0.02
    assert r["cases"][1]["motor_cg_probe_m"] == 0.0128
    assert not r["adopted"] and r["physical_full_inertia"] is None
    assert r["resources"]["cpu_s"] < r["resources"]["cpu_limit_s"] == 6
