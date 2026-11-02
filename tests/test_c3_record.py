"""Read-only C3 admission evidence; never rerun its stopped design packet."""

import ast
import hashlib
import json
import math
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo03-c3-continuous-connection-20261102-v1"
CONFIG = ROOT / "configs/studies/wo03-c3-continuous-connection.yaml"


class NormalizeDictSyntax(ast.NodeTransformer):
    """Ignore only the lint conversion dict(a=x) -> {'a': x}."""

    def visit_Call(self, node):
        self.generic_visit(node)
        if (
            isinstance(node.func, ast.Name)
            and node.func.id == "dict"
            and not node.args
            and all(kw.arg is not None for kw in node.keywords)
        ):
            return ast.Dict(
                keys=[ast.Constant(value=kw.arg) for kw in node.keywords],
                values=[kw.value for kw in node.keywords],
            )
        return node


def test_execution_identity_keeps_archived_code_and_original_failures():
    record = json.loads((RUN / "record.json").read_text())
    c2run = ROOT / "runs/wo03-c2-sandwich-socket-20261102-v2"
    archive = json.loads((c2run / "source-dependencies/manifest.json").read_text())
    for relative, expected in record["input_sha256"].items():
        path = ROOT / relative
        if relative.startswith("build/"):
            path = ROOT / archive[relative]["archive_path"]
        if relative == "scripts/wo03_c3_continuous_connection.py":
            path = RUN / "executed-script.py"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    assert (RUN / "executed-config.yaml").read_bytes() == CONFIG.read_bytes()
    original = NormalizeDictSyntax().visit(ast.parse((RUN / "executed-script.py").read_text()))
    maintained = NormalizeDictSyntax().visit(
        ast.parse((ROOT / "scripts/wo03_c3_continuous_connection.py").read_text())
    )
    assert ast.dump(original, include_attributes=False) == ast.dump(
        maintained, include_attributes=False
    )
    assert json.loads((c2run / "record.json").read_text())["status"].startswith("not_admitted")
    assert (ROOT / "runs/wo03-c2-sandwich-socket-20261102-v1/failure.json").exists()
    assert record["resources"]["CAD_FEA_thermal_freeflight_executed"] is False
    assert record["resources"]["threads"] == 1
    for kind in ("cpu", "wall"):
        assert 0 < record["resources"][kind + "_s"] < record["resources"][kind + "_limit_s"]


def test_complete_stock_ledger_couples_growth_balance_and_opening_force():
    record = json.loads((RUN / "record.json").read_text())
    c1 = json.loads(
        (ROOT / "runs/wo03-g80-mass-balance-revision-20261102-v2/record.json").read_text()
    )
    rows = record["replacement_ledger"]
    assert len({r["id"] for r in rows}) == len(rows)
    assert record["gross_added_g"] - record["gross_removed_g"] == pytest.approx(
        record["net_added_mass_g"]
    )
    assert not any("remove_C1_closed" in row["id"] for row in rows)
    assert sum("remove_C1_integral_end_hardpoint" in row["id"] for row in rows) == 6
    assert sum("remove_C1_forward_motor_key_carrier" in row["id"] for row in rows) == 3
    assert sum("face_bond" in row["id"] for row in rows) == 2
    assert any("edge_finish" in row["id"] for row in rows)
    assert any("selected_root_shim" in row["id"] for row in rows)
    assert all(row["function"] and row["basis"] for row in rows)
    delta_moment = math.fsum(row["mass_delta_g"] * row["station_mm"] for row in rows)
    for case, base in zip(record["cases"], c1["mass_scenario_results"][2:4], strict=True):
        assert case["separate_full_growth_g"] == 50
        assert case["total_g"] == pytest.approx(case["nominal_plus_optional20g_g"] + 50)
        assert case["total_g"] == pytest.approx(
            base["loaded_mass_kg"] * 1000 + math.fsum(r["mass_delta_g"] for r in rows)
        )
        assert case["total_g"] * case["cg_mm"] == pytest.approx(
            base["loaded_first_moment_kg_m"] * 1e6 + delta_moment
        )
        assert case["severe_recovery_DF3_mean_N"] == pytest.approx(
            3 * case["total_g"] / 1000 * (20.4**2 / (2 * 0.3) + 9.80665)
        )
        assert case["full_intrinsic_inertia"] is None
    assert record["cases"][1]["total_g"] - record["cases"][0]["total_g"] == pytest.approx(20)


def test_incompatible_geometry_and_missing_strength_stop_admission():
    record = json.loads((RUN / "record.json").read_text())
    cfg = yaml.safe_load(CONFIG.read_text())
    assert record["status"] == "not_admitted_stop_before_CAD_FEA"
    geom = record["geometry"]
    assert geom["aft_node_motor_arm_collision"] is True
    assert geom["nominal_overlap_axial_radial_tangent_mm"] == [4, 12, 6.6]
    assert geom["harness_nominal_min_gap_mm"] > 0
    assert geom["harness_after_motion_manufacturing_mm"] < cfg["criteria"]["clearance_mm"]
    checks = record["connection_checks"]
    assert checks["primary_pad_bond_removed_from_proposed_load_path"] is True
    for key in (
        "qualified_G11_bearing_tearout_peel_allowables",
        "finite_cap_and_skirt_compliance",
        "global_channel_torsion_and_root_floor_motion",
        "installed_flutter",
    ):
        assert checks[key] is None
    assert record["thermal"]["substrate_screen_c"] == 45
    assert record["thermal"]["no_new_temperature_calculation"] is True


def test_baseline_and_conditional_guide_failures_are_never_rounded_into_passes():
    record = json.loads((RUN / "record.json").read_text())
    nominal, adverse = record["cases"]
    assert nominal["loaded_margin_cal"] > 1 > adverse["loaded_margin_cal"]
    for case in record["cases"]:
        assert case["formal_1p971m_headroom_g"] < 0
        assert case["planning_1p971m_headroom_g"] < case["formal_1p971m_headroom_g"]
        assert {g["usable_m"] for g in case["guides"]} == {1.5, 1.8, 1.971}
        for guide in case["guides"]:
            assert guide["rail_exit_speed_mps"] < 15
            assert guide["rail_screen_pass"] is False
            assert guide["worst_case_mass_kg"] == pytest.approx(case["total_g"] / 1000)
            assert guide["planning_margin_mps"] == pytest.approx(guide["formal_margin_mps"] - 0.5)
