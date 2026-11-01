"""One bounded, isolated G80 keeper integration; never modifies active vehicle assets."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import resource
import sys
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / "build/wo03-g80-integration-staging"
CHECKOUT = STAGE / "checkout"
CONFIG = ROOT / "configs/studies/wo03-g80-retention-integration.yaml"
OUTPUT = STAGE / "stage1-result"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def raw_parts(raw, cfg):
    recipe = cfg["recipe_mm"]
    base = next(p for p in raw["parts"] if p["id"] == "motor_mount")
    hardware = next(p for p in raw["parts"] if p["id"] == "retention_hardware")
    raw["parts"] = [p for p in raw["parts"] if p["id"] not in ("motor_mount", "retention_hardware")]
    mount = copy.deepcopy(base)
    mount.pop("cad_mass", None)
    mount["cad"]["generator"] = "g80_keeper_service"
    mount["cad"]["parameters"].update(service_recipe_mm=recipe, service_kind="mount")
    mount["learn"] = (
        "Plywood mounting frame retains its rails and forward rings; removed rear ring material and block regions are replaced by separate keeper and guides. Joints and load sharing remain unqualified."
    )
    raw["parts"].append(mount)
    mapping = {"motor_mount": "modified_mount"}

    def add(kind, index=None):
        pid = "service_" + kind + (f"_{index}" if index is not None else "")
        is_wood = kind == "guide"
        is_g11 = kind in ("keeper", "bridge")
        manufactured = is_wood or is_g11
        row = {
            "id": pid,
            "type": "commercial",
            "parent": "motor_mount",
            "position_m": cfg["mount_station_m"],
            "lateral_offset_m": [0.0, 0.0],
            "geometry": {
                "length_m": cfg["part_geometry_length_m"],
                "radius_m": cfg["part_envelope_radius_m"],
            },
            "material": "plywood" if is_wood else "G11" if is_g11 else "stainless_steel_A2",
            "mass_kg": 0.01 if manufactured else cfg["mass_g_each"][kind] / 1000,
            "cg_offset_m": 0.1,
            "estimate": True,
            "learn": f"{kind.replace('_',' ').title()} is an explicitly placed keeper-service component. Geometry and mass are nominal estimates; installed load transfer and hardware qualification remain open.",
            "build": {
                "method": "cut" if manufactured else "purchased",
                "cost_usd": 0.0,
                "generator": "g80_keeper_service",
                "notes": "Staged source-identical geometry; estimated manufacture or supplier-average hardware mass; no qualification.",
            },
            "cad": {
                "generator": "g80_keeper_service",
                "parameters": {
                    "service_kind": kind,
                    "service_index": index or 0,
                    "service_recipe_mm": recipe,
                },
                "mass_basis": "volume_density" if manufactured else "supplied_or_estimated",
                "role": "manufactured" if manufactured else "purchased_envelope",
                "moving_group": "fixed",
                "color": "#b6a58b" if manufactured else "#999999",
                "notes": "Nominal G80 keeper-service proposal; no as-built mass, hardware grade or joint proof.",
            },
        }
        raw["parts"].append(row)
        source = (
            "guide"
            if kind == "guide"
            else kind.removeprefix("m3_") if kind.startswith("m3_") else kind
        )
        mapping[pid] = source + (f"_{index}" if index is not None else "")

    for i in range(3):
        add("guide", i)
    add("keeper")
    add("bridge")
    for k in ("m3_screw", "m3_nut", "m3_washer", "m2_screw", "m2_nut"):
        for i in range(3):
            add(k, i)
    reserve = copy.deepcopy(hardware)
    reserve.update(
        id="retention_locking_materials_reserve",
        type="commercial",
        parent="aft_shell",
        position_m=cfg["locking_reserve_station_m"],
        lateral_offset_m=[0.0, 0.0],
        geometry={"bbox_m": cfg["locking_reserve_bbox_m"]},
        material="commercial",
        mass_kg=cfg["locking_materials_reserve_g"] / 1000,
        cg_offset_m=cfg["locking_reserve_bbox_m"][0] / 2,
        estimate=True,
        learn="Estimated allowance for future retention locking and assembly materials. The actual locking mechanism, location, installation and qualification are not selected.",
    )
    reserve["cad"] = {
        "generator": "budget",
        "parameters": {},
        "mass_basis": "supplied_or_estimated",
        "role": "distributed_budget",
        "moving_group": "fixed",
        "color": "#888888",
        "notes": "One gram reserve only; not growth or an installed locking mechanism.",
    }
    reserve["build"] = {
        "method": "assembled",
        "cost_usd": 0.0,
        "generator": "budget",
        "notes": "Estimated material reserve, not an approved locking design.",
    }
    reserve.pop("cad_mass", None)
    reserve.pop("engineering", None)
    raw["parts"].append(reserve)
    if len(raw["parts"]) != 72 or len(mapping) != 21:
        raise ValueError("Part count or ownership mismatch")
    for part in raw["parts"]:
        part.pop("cad_mass", None)
    return raw, mapping


def child():
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    os.chdir(CHECKOUT)
    sys.path.insert(0, str(CHECKOUT))
    import cadquery as cq
    import numpy as np
    from OCP.OSD import OSD_Parallel, OSD_ThreadPool

    from src.cad.assembly import export_vehicle
    from src.cad.parts import local_shape, properties
    from src.vehicle.mass import mass_properties
    from src.vehicle.materials import DENSITY_KG_M3
    from src.vehicle.schema import CADMass, Vehicle

    OSD_Parallel.SetUseOcctThreads_s(True)
    pool = OSD_ThreadPool.DefaultPool_s()
    pool.Init(1)
    if pool.NbThreads() != 1:
        raise ValueError("OCCT pool is not one thread")
    start = time.monotonic()
    cfg = yaml.safe_load(
        (CHECKOUT / "configs/studies/wo03-g80-retention-integration.yaml").read_text()
    )
    baseline = CHECKOUT / "inputs/baseline.yaml"
    if sha(baseline) != cfg["source_yaml_sha256"]:
        raise ValueError("Baseline YAML changed")
    source = yaml.safe_load(baseline.read_text())
    raw, mapping = raw_parts(copy.deepcopy(source), cfg)
    vehicle = Vehicle.model_validate(raw)
    OUT = OUTPUT
    OUT.mkdir(parents=True, exist_ok=False)
    comparison = {}
    parts = {p.id: p for p in vehicle.parts}
    # Each new physical shape is compared in the common mount-local frame.
    for pid, ref in mapping.items():
        part = parts[pid]
        shape = local_shape(part)
        reference = cq.importers.importStep(str(CHECKOUT / "inputs/keeper" / f"{ref}.step")).val()
        if (
            not shape.isValid()
            or shape.Volume() <= 0
            or not reference.isValid()
            or reference.Volume() <= 0
        ):
            raise ValueError(f"Invalid solid {pid}")
        va, vb = shape.Volume(), reference.Volume()
        ca, cb = shape.Center(), reference.Center()
        ba, bb = shape.BoundingBox(), reference.BoundingBox()
        bbox_a = [ba.xmin, ba.xmax, ba.ymin, ba.ymax, ba.zmin, ba.zmax]
        bbox_b = [bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax]
        inertia_a = np.asarray(cq.Shape.matrixOfInertia(shape))
        inertia_b = np.asarray(cq.Shape.matrixOfInertia(reference))
        symmetric = shape.cut(reference).Volume() + reference.cut(shape).Volume()
        row = {
            "source_step": f"{ref}.step",
            "source_step_sha256": sha(CHECKOUT / "inputs/keeper" / f"{ref}.step"),
            "volume_mm3": va,
            "reference_volume_mm3": vb,
            "symmetric_difference_mm3": symmetric,
            "centroid_delta_mm": [ca.x - cb.x, ca.y - cb.y, ca.z - cb.z],
            "max_bbox_difference_mm": max(abs(a - b) for a, b in zip(bbox_a, bbox_b, strict=True)),
            "max_inertia_matrix_difference_mm5": float(np.max(np.abs(inertia_a - inertia_b))),
        }
        comparison[pid] = row
        (OUT / "geometry-comparison-progress.json").write_text(
            json.dumps(comparison, indent=2) + "\n"
        )
        if (
            row["max_inertia_matrix_difference_mm5"]
            > max(1e-4, float(np.max(np.abs(inertia_b))) * 1e-8)
            or symmetric > 1e-4
            or abs(va - vb) > 1e-4
            or max(map(abs, row["centroid_delta_mm"])) > 1e-5
            or row["max_bbox_difference_mm"] > 1e-5
        ):
            raise ValueError(f"Source geometric equivalence failed: {pid}")
    # Recompute every CAD cache under real staged revision, then normally validate.
    for part in vehicle.parts:
        shape = local_shape(part)
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError(f"Invalid generated part {part.id}")
        props = properties(part, shape)
        part.cad_mass = CADMass.model_validate(props)
        if part.id in mapping and part.cad.mass_basis == "volume_density":
            part.mass_kg = props["volume_m3"] * DENSITY_KG_M3[part.material]
        offset = -props["cg_local_body_m"][0]
        if (
            offset < -1e-12
            or offset > part.geometry.get("length_m", part.geometry.get("bbox_m", [0])[0]) + 1e-12
        ):
            raise ValueError(f"Invalid CAD CG offset {part.id}")
        part.cg_offset_m = max(offset, 0.0)
    vehicle = Vehicle.model_validate(vehicle.model_dump(mode="json", by_alias=True))
    if len(vehicle.parts) != 72:
        raise ValueError("Final Vehicle count differs")
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    (OUT / "resolved-candidate.yaml").write_text(
        yaml.safe_dump(vehicle.model_dump(mode="json", by_alias=True), sort_keys=False)
    )
    manifest, _ = export_vehicle(vehicle, OUT, True)
    if len(manifest["parts"]) != 72 or not all(
        r["valid_solid"] and r["mass_within_10pct"] for r in manifest["parts"]
    ):
        raise ValueError("Export part or mass validation failed")
    states = []
    for burn in (0.0, 1.0):
        m = mass_properties(vehicle, burn_fraction=burn)
        states.append(
            {
                "burn_fraction": burn,
                "mass_kg": m.mass_kg,
                "cg_station_m": m.cg_m,
                "cg_lateral_m": m.cg_lateral_m,
                "inertia_kg_m2": m.inertia_kg_m2.tolist(),
            }
        )
    growth_states = []
    for state in states:
        m0 = state["mass_kg"]
        g = cfg["full_growth_allowance_kg"]
        cg = state["cg_station_m"]
        lateral = np.asarray(state["cg_lateral_m"])
        total = m0 + g
        combined_cg = (m0 * cg + g * cfg["full_growth_station_m"]) / total
        combined_lateral = m0 * lateral / total
        d0 = np.array([combined_cg - cg, *(lateral - combined_lateral)])
        dg = np.array([combined_cg - cfg["full_growth_station_m"], *(-combined_lateral)])
        shift = lambda d: np.dot(d, d) * np.eye(3) - np.outer(d, d)
        inertia = np.asarray(state["inertia_kg_m2"]) + m0 * shift(d0) + g * shift(dg)
        growth_states.append(
            {
                "burn_fraction": state["burn_fraction"],
                "mass_kg": total,
                "cg_station_m": combined_cg,
                "cg_lateral_m": combined_lateral.tolist(),
                "inertia_kg_m2": inertia.tolist(),
                "growth_station_m": cfg["full_growth_station_m"],
            }
        )
    u = resource.getrusage(resource.RUSAGE_SELF)
    rec = {
        "status": "stage1_candidate_only_no_acceptance",
        "identity": identity,
        "source_identity": cfg["source_identity"],
        "part_count": 72,
        "geometry_comparison": comparison,
        "states": states,
        "states_with_full_50g_growth": growth_states,
        "mass_budget_kg": mass_properties(vehicle).budget_kg,
        "staged_cad_revision": manifest["identity"]["cad_revision_sha256"],
        "generator_revision": "real staged revision in each validated CADMass digest",
        "cpu_s": u.ru_utime + u.ru_stime,
        "wall_s": time.monotonic() - start,
        "worker_peak_rss_bytes_macos": u.ru_maxrss,
        "original_retention_hardware_removed_once": True,
        "locking_reserve_kg": 0.001,
        "growth_allowance_kg": cfg["full_growth_allowance_kg"],
        "flight_ready": False,
        "acceptance": False,
        "limitations": [
            "No flight/static/motion/FEA/thermal validation in stage1",
            "Locking method and hardware qualification unresolved",
            "No adoption or preview change",
        ],
    }
    (OUT / "record.json").write_text(json.dumps(rec, indent=2) + "\n")
    print(
        json.dumps(
            {"status": rec["status"], "identity": identity, "states": states, "cpu_s": rec["cpu_s"]}
        ),
        flush=True,
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--child", action="store_true")
    a = p.parse_args()
    if a.child:
        child()
        return
    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)
    # Executed exactly once only after preflight, direct-child CPU and wall guards.
    sys.path.insert(0, str(ROOT))
    from scripts.wo03_owned_process import OwnedProcessError, darwin_process_callbacks, run_owned

    cfg = yaml.safe_load(CONFIG.read_text())
    from src.vehicle.schema import load_vehicle

    baseline = ROOT / "build/wo03-g80-integrated-candidate-v1/resolved-candidate.yaml"
    source_vehicle = load_vehicle(baseline)
    if (
        len(source_vehicle.parts) != 52
        or hashlib.sha256(source_vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        != cfg["source_identity"]
    ):
        raise ValueError("Original canonical candidate identity or part count changed")
    if sha(baseline) != sha(CHECKOUT / "inputs/baseline.yaml") or sha(CONFIG) != sha(
        CHECKOUT / "configs/studies/wo03-g80-retention-integration.yaml"
    ):
        raise ValueError("Staged baseline or study configuration differs from source")
    for p in (ROOT / "build/wo03-g80-keeper-service-v1").glob("*.step"):
        if sha(p) != sha(CHECKOUT / "inputs/keeper" / p.name):
            raise ValueError(f"Staged STEP input differs: {p.name}")
    inputs = [
        CONFIG,
        Path(__file__).resolve(),
        ROOT / "build/wo03-g80-integrated-candidate-v1/resolved-candidate.yaml",
        *sorted((ROOT / "build/wo03-g80-keeper-service-v1").glob("*.step")),
        *sorted((CHECKOUT / "src/cad").glob("*.py")),
        *sorted((CHECKOUT / "src/vehicle").glob("*.py")),
        CHECKOUT / "inputs/baseline.yaml",
        CHECKOUT / "configs/studies/wo03-g80-retention-integration.yaml",
        *sorted((CHECKOUT / "inputs/keeper").glob("*.step")),
    ]
    hashes = {str(p): sha(p) for p in inputs}
    (STAGE / "stage1-source-before.json").write_text(json.dumps(hashes, indent=2) + "\n")
    rss, desc = darwin_process_callbacks()
    env = dict(os.environ)
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[name] = "1"
    status = None
    error = None
    try:
        status = run_owned(
            [sys.executable, str(Path(__file__).resolve()), "--child"],
            log_path=STAGE / "stage1-child.log",
            status_path=STAGE / "stage1-owned-status.json",
            wall_limit_s=cfg["max_child_wall_s"],
            rss_callback=rss,
            descendants_callback=desc,
            cwd=CHECKOUT,
            env=env,
        )
    except (OwnedProcessError, OSError, ValueError) as exc:
        error = f"{type(exc).__name__}: {exc}"
    finally:
        after = {str(p): sha(p) for p in inputs}
        statusfile = STAGE / "stage1-owned-status.json"
        if statusfile.exists():
            status = json.loads(statusfile.read_text())
        ledger = {
            "status": (
                "complete"
                if error is None and hashes == after and (OUTPUT / "record.json").exists()
                else "stopped"
            ),
            "error": error,
            "source_before": hashes,
            "source_after": after,
            "sources_unchanged": hashes == after,
            "owned_status": status,
            "setup_cpu": "not fully measured; reserve 30 CPU s; no active source or preview mutated",
            "acceptance": False,
        }
        (STAGE / "stage1-ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
    if ledger["status"] != "complete":
        raise RuntimeError(f"Stage 1 stopped: {error}")
    print("Isolated stage1 complete; no engineering acceptance", flush=True)


if __name__ == "__main__":
    main()
