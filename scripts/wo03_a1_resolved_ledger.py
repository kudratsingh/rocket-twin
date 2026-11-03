"""Export the frozen A1 component ledger by exact ID, without design calculations.

This bookkeeping replay reads executed C1, A, and A1 records. It does not call
CAD, structural, thermal, guide, or flight code. Point-mass first moments are
the only arithmetic beyond summing component masses.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import shutil
import signal
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
C1 = Path("web/public/engineering-workbench/g80-c1.json")
A = Path("runs/wo03-architecture-space-mass-20261102-v1/record.json")
A1 = Path("runs/wo03-a1-connections-20261102-v1/record.json")
OUT = Path("runs/wo03-a1-bookkeeping-20261102-v1")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def require_close(actual: float, expected: float, label: str) -> None:
    if not math.isclose(actual, expected, rel_tol=0, abs_tol=1e-9):
        raise ValueError(f"{label}: {actual} != {expected}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preset", choices=["tiny"], default="tiny")
    args = parser.parse_args()
    assert args.preset == "tiny"
    out = ROOT / OUT
    if out.exists():
        raise FileExistsError(f"Refuse overwrite of immutable export: {out}")
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    signal.setitimer(signal.ITIMER_REAL, 5)
    start_cpu, start_wall = time.process_time(), time.monotonic()
    source_paths = [C1, A, A1, Path("scripts/wo03_a1_resolved_ledger.py")]
    hashes = {str(p): digest(ROOT / p) for p in source_paths}
    c1 = json.loads((ROOT / C1).read_text())
    a_record = json.loads((ROOT / A).read_text())
    a1_record = json.loads((ROOT / A1).read_text())
    if hashes[str(C1)] != a_record["input_sha256"][str(C1)]:
        raise ValueError("C1 source differs from frozen A source")
    if hashes[str(A)] != a1_record["input_sha256"][str(A)]:
        raise ValueError("A source differs from frozen A1 source")
    a = next(x for x in a_record["arrangements"] if x["id"] == "A_motor_fin_can")
    c1_parts = {p["id"]: p for p in c1["parts"]}
    c1_stations = {p["id"]: p["station_mm"] for p in c1["mass_distribution"]}
    if (
        len(c1_parts) != len(c1["parts"])
        or set(c1_stations) - set(c1_parts) != {"separate_growth"}
        or not set(c1_parts) <= set(c1_stations)
    ):
        raise ValueError("C1 source IDs or stations are incomplete/duplicated")
    a_removed = a["removed_part_ids"]
    if len(a_removed) != len(set(a_removed)) or not set(a_removed) <= set(c1_parts):
        raise ValueError("A source removals are not unique C1 IDs")
    a_negative = {x["id"] for x in a["replacement_ledger"] if x["mass_delta_g"] < 0}
    if a_negative != {"remove_" + x for x in a_removed}:
        raise ValueError("A source signed removal ledger differs from removed_part_ids")

    rows: dict[str, dict] = {}

    def add(
        pid: str, mass: float, station: float, function: str, provenance: list[str], basis: str
    ) -> None:
        if pid in rows or mass < 0 or not math.isfinite(mass) or not math.isfinite(station):
            raise ValueError(f"Duplicate, negative or nonfinite component: {pid}")
        rows[pid] = {
            "id": pid,
            "mass_g": mass,
            "station_mm": station,
            "first_moment_kg_m": mass * station * 1e-6,
            "function": function,
            "source_ids": provenance,
            "mass_basis": basis,
        }

    for pid, p in c1_parts.items():
        if pid not in a_removed:
            add(
                pid,
                p["mass_g"],
                c1_stations[pid],
                p["function"],
                [str(C1), *p.get("source_ids", [])],
                p["mass_basis"],
            )
    a_additions = [x for x in a["replacement_ledger"] if x["mass_delta_g"] > 0]
    for x in a_additions:
        add(x["id"], x["mass_delta_g"], x["station_mm"], x["function"], [str(A)], x["basis"])
    a_mass = math.fsum(x["mass_g"] for x in rows.values())
    a_first = math.fsum(x["first_moment_kg_m"] for x in rows.values())
    require_close(a_mass + 50, a["cases"][0]["total_g"], "A total with separate growth")
    require_close(
        (a_first + 50 * 1227 * 1e-6) / (a_mass + 50) * 1e6, a["cases"][0]["cg_mm"], "A CG"
    )

    removals = [x for x in a1_record["replacement_ledger"] if x["mass_delta_g"] < 0]
    additions = [x for x in a1_record["replacement_ledger"] if x["mass_delta_g"] > 0]
    if len(removals) != 8 or len(additions) != 20:
        raise ValueError("Unexpected A1 replacement count")
    removed_ids = []
    for x in removals:
        pid = x["id"].removeprefix("remove_")
        if not x["id"].startswith("remove_") or pid not in rows or pid in removed_ids:
            raise ValueError(f"A1 removal lacks unique existing ID: {x['id']}")
        old = rows.pop(pid)
        require_close(-x["mass_delta_g"], old["mass_g"], f"A1 removal mass {pid}")
        require_close(x["station_mm"], old["station_mm"], f"A1 removal station {pid}")
        removed_ids.append(pid)
    for x in additions:
        add(x["id"], x["mass_delta_g"], x["station_mm"], x["function"], [str(A1)], x["basis"])
    if len(rows) != 90:
        raise ValueError(f"Expected 90 nonnegative components, found {len(rows)}")
    subtotal = math.fsum(x["mass_g"] for x in rows.values())
    first = math.fsum(x["first_moment_kg_m"] for x in rows.values())
    growth = 50.0
    growth_station = 1227.0
    nominal = next(x for x in a1_record["complete_cases"] if x["id"] == "nominal")
    adverse = next(
        x for x in a1_record["complete_cases"] if x["id"] == "additional20g_motorCG_probe"
    )
    require_close(subtotal + growth, nominal["total_g"], "A1 nominal total")
    require_close(subtotal + growth + 20, adverse["total_g"], "A1 adverse total")
    require_close(subtotal - a_mass, a1_record["net_delta_from_A_g"], "A1 mass delta")
    require_close(
        first - a_first, a1_record["first_moment_delta_from_A_kg_m"], "A1 first-moment delta"
    )
    require_close(
        (first + growth * growth_station * 1e-6) / nominal["total_g"] * 1e6,
        nominal["cg_mm"],
        "A1 nominal CG",
    )
    # The adverse motor-CG probe is inherited as a case result. Do not infer a
    # physical motor station from that hypothetical variation.
    result = {
        "id": "G80_A1_nonnegative_component_bookkeeping_20261102_v1",
        "status": "accounting_export_only_A1_not_admitted",
        "input_sha256": hashes,
        "source_component_count": len(c1_parts),
        "A_removed_C1_ids": a_removed,
        "A1_removed_from_A_ids": removed_ids,
        "component_count": len(rows),
        "components": sorted(rows.values(), key=lambda x: x["id"]),
        "subtotal_without_separate_growth_g": subtotal,
        "subtotal_first_moment_kg_m": first,
        "separate_growth": {
            "mass_g": growth,
            "station_mm": growth_station,
            "first_moment_kg_m": growth * growth_station * 1e-6,
        },
        "nominal_total_g": nominal["total_g"],
        "nominal_first_moment_kg_m": first + growth * growth_station * 1e-6,
        "additional_adverse_aft_g": 20,
        "adverse_total_g": adverse["total_g"],
        "adverse_motor_CG_probe": "Inherited A1 case; no physical component or intrinsic inertia inferred",
        "full_intrinsic_inertia": None,
        "validated_new_CP_mm": None,
        "resources": {
            "cpu_limit_s": 1,
            "wall_limit_s": 5,
            "cpu_s": time.process_time() - start_cpu,
            "wall_s": time.monotonic() - start_wall,
            "engineering_or_guide_rerun": False,
        },
    }
    out.mkdir(parents=False)
    shutil.copy2(Path(__file__), out / "executed-script.py")
    (out / "record.json").write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    signal.setitimer(signal.ITIMER_REAL, 0)
    print(
        f"{result['component_count']} components; subtotal {subtotal:.9f} g; nominal {nominal['total_g']:.9f} g"
    )


if __name__ == "__main__":
    main()
