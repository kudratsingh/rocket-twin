"""Generate every physical configuration and reconcile bulk-material CAD masses."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import yaml

from src.cad.assembly import export_vehicle, rigid_intersections
from src.cad.verification import verify
from src.vehicle.schema import Vehicle, load_vehicle_data, vehicle_input_paths


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--vehicle")
    parser.add_argument("--reconcile", action="store_true")
    parser.add_argument("--check-only", action="store_true")
    parser.add_argument("--require-benchmark", action="store_true")
    args = parser.parse_args()
    start = time.perf_counter()
    manifest = yaml.safe_load(args.config.read_text())
    paths = manifest["vehicles"] + [
        str(p) for p in sorted(Path("configs/vehicle/wo02").glob("*.yaml"))
    ]

    def load_design(path: str) -> Vehicle:
        data = load_vehicle_data(path)
        if args.reconcile:
            for part in data["parts"]:
                part.pop("cad_mass", None)
        return Vehicle.model_validate(data)

    if args.reconcile and args.require_benchmark:
        parser.error(
            "Reconciliation adopts estimates; verify the regenerated design in a separate run"
        )
    if args.vehicle:
        paths = [p for p in paths if load_design(p).id == args.vehicle]
    if not paths:
        parser.error("Unknown vehicle; no configuration selected")
    inputs = {args.config, Path(__file__).resolve().relative_to(Path.cwd())}
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(Path("src/vehicle").glob("*.py"))
    for path in paths:
        inputs.update(vehicle_input_paths(path))
    hashes = {
        p.resolve().relative_to(Path.cwd()).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in sorted(inputs)
    }
    reports = []
    updates = {}
    for path in paths:
        v = load_design(path)
        report, solids = export_vehicle(v, Path("build") / v.id, not args.check_only)
        report["rigid_intersections"] = rigid_intersections(v, solids)
        report["nominal_interfaces_motion"] = verify(v, solids)
        if not args.check_only:
            (Path("build") / v.id / "manifest.json").write_text(json.dumps(report, indent=2) + "\n")
        reports.append(report)
        for part in report["parts"]:
            updates[part["id"]] = part
        print(
            v.id,
            "mass",
            report["mass_benchmark_passed"],
            "intersections",
            report["rigid_intersections"],
            flush=True,
        )
    if args.reconcile:
        # Apply generated properties to their owning YAML, shared parts once.
        owners = [
            Path(manifest["shared_upper"]),
            *[Path(p) for p in paths],
        ]
        for owner in owners:
            data = yaml.safe_load(owner.read_text())
            for part in data.get("parts", []):
                # Match mode-specific same-id parts against their own report.
                current = next((r for r in reports if r["vehicle"] == data.get("id")), None)
                row = (
                    next((p for p in current["parts"] if p["id"] == part["id"]), None)
                    if current
                    else updates.get(part["id"])
                )
                if row is None:
                    continue
                part["cad_mass"] = row["properties"]
                if part["cad"]["mass_basis"] == "volume_density":
                    part["mass_kg"] = row["cad_mass_kg"]
                    part.pop("density_kg_m3", None)
                    part["estimate"] = True
                part["cg_offset_m"] = -row["properties"]["cg_local_body_m"][0]
            owner.write_text(yaml.safe_dump(data, sort_keys=False))
        print(
            "CAD mass/centroid/inertia adopted as unmeasured design estimates; regenerate and revalidate."
        )
    run = datetime.now(UTC).strftime("wo03-%Y%m%dT%H%M%S%fZ")
    out = Path("runs") / run
    out.mkdir()
    passed = all(
        r["mass_benchmark_passed"]
        and r["print_volume_passed"]
        and not r["rigid_intersections"]
        and r["nominal_interfaces_motion"]["passed"]
        and all(p["valid_solid"] for p in r["parts"])
        for r in reports
    )
    record = {
        "run_id": run,
        "work_order": "03",
        "elapsed_s": time.perf_counter() - start,
        "reports": reports,
        "cad_export_benchmark_passed": passed and not args.reconcile,
        "expanded_wo03_benchmark_passed": False,
        "reconciled_estimates": args.reconcile,
        "input_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "flight_ready": False,
        "cost_usd": 0,
    }
    (out / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(out / "record.json")
    return int(args.require_benchmark and not passed)


if __name__ == "__main__":
    raise SystemExit(main())
