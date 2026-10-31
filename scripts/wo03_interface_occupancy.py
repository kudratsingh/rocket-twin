"""Partition actual adhesive/solid/open interfaces and write a connection table."""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.occupancy import cylindrical_interface
from src.cad.parts import local_shape
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-interface-occupancy.yaml"


def main() -> int:
    started = time.perf_counter()
    cfg = yaml.safe_load(CONFIG.read_text())
    source_path = ROOT / cfg["candidate_record"]
    source = json.loads(source_path.read_bytes())
    candidate = source_path.parent / "resolved-candidate.json"
    vehicle = Vehicle.model_validate_json(candidate.read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != source["candidate_identity"]:
        raise ValueError("Source record and actual resolved candidate disagree")
    parts = {p.id: p for p in vehicle.parts}
    paths = [
        CONFIG,
        source_path,
        candidate,
        Path(__file__),
        ROOT / "src/analysis/occupancy.py",
        ROOT / "src/vehicle/schema.py",
        *sorted((ROOT / "src/cad").glob("*.py")),
    ]
    hashes = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    run_id = "wo03-interface-occupancy-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir()
    for name, expected in hashes.items():
        raw = (ROOT / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("Source changed during immutable snapshot")
        target = folder / "source-snapshot" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
    solids = {}
    selected = [parts[name] for name in ("fin_set", "motor_mount", "aft_shell")]
    selected += [p for p in vehicle.parts if p.id.startswith("mount_shell_bond_")]
    for p in selected:
        solids[p.id] = local_shape(p).translate(
            (1000 * p.lateral_offset_m[0], -1000 * p.lateral_offset_m[1], 1000 * p.position_m)
        )
    rows = []
    for bond in vehicle.parts:
        if not bond.id.startswith("mount_shell_bond_"):
            continue
        result = cylindrical_interface(
            1000 * parts["motor_mount"].geometry["radius_m"],
            1000 * parts["aft_shell"].geometry["inner_radius_m"],
            1000 * bond.position_m,
            1000 * bond.geometry["length_m"],
            {
                "adhesive": solids[bond.id],
                "fin": solids["fin_set"],
                "support": solids["motor_mount"],
                "body": solids["aft_shell"],
            },
            tuple(cfg["probe_thicknesses_mm"]),
        )
        rows.append({"region": bond.id, **result})
        print(
            json.dumps({"region": bond.id, "area": result["area_probe_refinements"][-1]}),
            flush=True,
        )
    record = {
        "run_id": run_id,
        "candidate_identity": identity,
        "cad_revision_sha256": source["cad_revision_sha256"],
        "source_sha256": hashes,
        "inputs_unchanged": all(
            hashlib.sha256((ROOT / p).read_bytes()).hexdigest() == h for p, h in hashes.items()
        ),
        "connections": rows,
        "uncertainty": cfg["uncertainty"],
        "correction_rule": "Remove only adhesive/other-solid occupied volumes from gas and direct view. Retain real open volume; actual receiving surfaces and visibility require first-hit CAD evidence. Never assign the whole gap independently to glue and air.",
        "limits": [
            "Nominal occupancy only; no measured wetting, voids or contact quality.",
            "Mid-radius area is not a radial-connectivity or optical view-factor result.",
            "Unmodeled adhesive budget is not physical opaque coverage.",
            "Each changed gap, baffle, slot, fin or support revision requires regeneration.",
        ],
        "elapsed_s": time.perf_counter() - started,
        "cost_usd": 0,
        "thermal_acceptance_passed": False,
        "active_adoption": False,
        "flight_ready": False,
    }
    (folder / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    text = [
        "# Actual adhesive-interface occupancy",
        "",
        f"Executed `{run_id}`; candidate `{identity}`, CAD `{source['cad_revision_sha256']}`.",
        "",
        "Nominal geometry partitions one physical space. These areas do not replace the visibility model or establish bond quality. The prior full-annulus gas path is invalid wherever glue or another solid occupies it. Actual openings remain available for gas transfer and geometry-resolved radiation.",
        "",
        "| Region | Start, mm | Thickness, mm | Glue area, mm² | Other solid, mm² | Open area, mm² | Mechanism and correction |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        area = row["area_probe_refinements"][-1]
        a = area["material_area_mm2"]
        text.append(
            f"| {row['region']} | {row['start_station_mm']:.3f} | {row['bond_or_gap_thickness_mm']:.3f} | {a['adhesive']:.6f} | {sum(v for k,v in a.items() if k!='adhesive'):.6f} | {area['open_area_mm2']:.6f} | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |"
        )
    text += [
        "",
        "The record retains full volume balance and three area-probe refinements (0.1/0.01/0.001 mm). Full wetting is nominal CAD, not a process guarantee. Preserve the existing 0.32–0.68 mm gap variants and 2/10/50 W/K per-ring contact sensitivities; each requires its own geometry. Missing potting/meniscus cannot be assumed. Bond and air areas are disjoint; temperatures and radiation visibility remain separate calculations.",
        "",
        "Part-average transient temperatures cannot establish local interface hot spots. Later owner stages retain bond sectioning/wetting, hot-load and instrumented soak measurements. No candidate adoption, thermal acceptance or flight release.",
        "",
        f"Evidence: `{folder/'record.json'}`. Regenerate with `.venv/bin/python scripts/wo03_interface_occupancy.py`.",
    ]
    (ROOT / "docs/wo03-interface-occupancy.md").write_text("\n".join(text) + "\n")
    print(folder / "record.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
