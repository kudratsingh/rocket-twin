"""VP1 price and fixture arithmetic only; no specimen, flight, guide or solver run."""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from decimal import Decimal
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "configs/studies/rp1-validation-package.yaml"


def subtotal(rows: list[dict], quantities: dict | None = None) -> Decimal:
    return sum(
        (
            Decimal(str(row["unit_usd"]))
            * Decimal(
                str(quantities.get(row["id"], 0) if quantities is not None else row["quantity"])
            )
            for row in rows
        ),
        Decimal(0),
    )


def fixture_pair(
    force: float, moment: float, inner_m: float, outer_m: float
) -> tuple[float, float]:
    if not outer_m > inner_m >= 0:
        raise ValueError("Distinct nonnegative physical load positions required")
    outer = (moment - force * inner_m) / (outer_m - inner_m)
    return force - outer, outer


def build() -> dict:
    start, cpu = time.monotonic(), time.process_time()
    p = yaml.safe_load(PLAN.read_text())
    if (
        hashlib.sha256((ROOT / p["frozen_configuration"]).read_bytes()).hexdigest()
        != p["configuration_sha256"]
    ):
        raise ValueError("AD1 frozen identity changed")
    if any(
        p[k]
        for k in (
            "purchase_authorized",
            "supplier_contact_authorized",
            "physical_work_authorized",
            "paid_service_authorized",
        )
    ):
        raise ValueError("Review packet cannot silently acquire execution authority")
    rows = p["materials"]
    total = subtotal(rows)
    initial = subtotal(rows, p["initial_room_only_material_order"])
    f, m = p["preserved"]["fin_force_N"], p["preserved"]["fin_moment_Nm"]
    inner, outer = fixture_pair(f, m, 0.01, 0.04)
    result = {
        "id": p["id"],
        "status": "review_and_inquiry_only_no_execution",
        "plan_sha256": hashlib.sha256(PLAN.read_bytes()).hexdigest(),
        "producer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "first_authorization_usd": 0,
        "published_material_order_usd": str(total),
        "initial_room_material_order_usd": str(initial),
        "expected_all_in_total_usd": None,
        "unknown_cost_is_not_zero": True,
        "root_method_accepted": False,
        "test_material_adopted": False,
        "force_pair_N": [inner, outer],
        "force_balance_residual_N": inner + outer - f,
        "moment_balance_residual_Nm": inner * 0.01 + outer * 0.04 - m,
        "independent_root_input_patterns": [
            {"force_N": f, "position_mm": 10, "moment_Nm": f * 0.01},
            {"force_N": m / 0.04, "position_mm": 40, "moment_Nm": m},
        ],
        "coupon_minimum_dimensions_load_cap_N": 2 * 0.025 * 0.0058**2 * 4e6 / (3 * 0.24),
        "three_indicator_instrument_MPE_bound_mm": 0.003 + (0.06 / 0.04) * (0.003 + 0.003),
        "MPE_bound_is_combined_U95": False,
        "home_coupon_priced_tool_basket_plus_stock_usd": str(
            sum(
                (
                    Decimal(x)
                    for x in ["115.40", "173", "161.60", "444.62", "184.50", "39", "69.75"]
                ),
                Decimal(0),
            )
        ),
        "root_priced_instrument_basket_no_loader_fixture_usd": str(
            sum(
                (
                    Decimal(x)
                    for x in [
                        "1371",
                        "519",
                        "750",
                        "85",
                        "161.60",
                        "143.66",
                        "444.62",
                        "184.50",
                        "39",
                        "39",
                    ]
                ),
                Decimal(0),
            )
        ),
        "cost_limits": "Tool baskets are sourced examples, not the cheapest market price or complete accepted fixtures. No owner stock assumed.",
        "no_vehicle_change_g": 0,
    }
    assert total == Decimal(str(p["financial_basis"]["materials_known_total_usd"]))
    assert initial == Decimal(str(p["financial_basis"]["initial_room_material_order_usd"]))
    result["resources"] = {
        "cpu_s": time.process_time() - cpu,
        "wall_s": time.monotonic() - start,
        "arithmetic_budget_CPU_s": 5,
        "wall_stop_s": 10,
        "new_flight_guide_CAD_FEA_thermal_runs": 0,
    }
    if result["resources"]["cpu_s"] > 5 or result["resources"]["wall_s"] > 10:
        raise RuntimeError("Arithmetic budget exhausted; no automatic repeat")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output", type=Path, default=ROOT / "docs/validation/rp1-vp1/accounting.json"
    )
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Retain completed VP1 accounting; no overwrite")
    result = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
