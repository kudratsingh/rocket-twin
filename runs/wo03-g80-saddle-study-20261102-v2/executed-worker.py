"""One bounded S2 mass/guide hand-study. No CAD or structural solver."""

from __future__ import annotations

import hashlib
import json
import math
import os
import resource
import shutil
import sys
import time
import traceback
from itertools import pairwise
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-g80-saddle-study.yaml"
OUT = ROOT / "runs/wo03-g80-saddle-study-20261102-v2"


def json_scalar(value):
    import numpy as np

    if isinstance(value, np.generic):
        return value.item()
    raise TypeError(f"Unsupported JSON value: {type(value).__name__}")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def collar(config, order, aft):
    import numpy as np
    from numpy.polynomial.legendre import leggauss

    x, w = leggauss(order)
    angles = (x + 1) * math.pi / 6
    weights = w * math.pi / 6
    total_v = total_m = 0.0
    # Six-fold reflection symmetry of the three arm and saddle axes.
    for theta, wt in zip(angles, weights, strict=True):
        boundaries = [0.0, 12.0, 18.0, 32.2]
        for direction, inner, outer, halfwidth in (
            (math.pi / 3, 12.0, 31.6, 8.0),
            (0.0, 18.0, 31.6, 6.0 if aft else 4.0),
        ):
            delta = theta - direction
            co, si = math.cos(delta), abs(math.sin(delta))
            if co <= 0:
                continue
            lo = inner / co
            hi = min(outer / co, 32.2, halfwidth / si if si > 1e-14 else 1e6)
            if lo < hi:
                boundaries.extend([lo, hi])
        boundaries = sorted({min(32.2, max(0.0, v)) for v in boundaries})
        for low, high in pairwise(boundaries):
            if high - low < 1e-13:
                continue
            r = (x + 1) * (high - low) / 2 + low
            rw = w * (high - low) / 2
            h = np.where((r >= 12) & (r <= 18), 16.0, 0.0)
            ds = theta - math.pi / 3
            xs = r * math.cos(ds)
            ys = r * math.sin(ds)
            mask = (xs >= 12) & (xs <= 31.6) & (np.abs(ys) <= 8)
            sh = 8 + np.sqrt(np.maximum(0.0, 64 - ys * ys))
            h = np.maximum(h, np.where(mask, sh, 0))
            xa = r * math.cos(theta)
            ya = np.abs(r * math.sin(theta))
            half = 6.0 if aft else 4.0
            h = np.maximum(
                h, np.where((xa >= 18) & (xa <= 31.6) & (ya <= half), 16.0 if aft else 11.0, 0)
            )
            total_v += 6 * wt * float(np.dot(rw, r * h))
            total_m += 6 * wt * float(np.dot(rw, r * h * h / 2))
    return {"volume_mm3": total_v, "axial_distance_from_plane_mm": total_m / total_v}


def main():
    import yaml

    started = time.monotonic()
    OUT.mkdir(parents=True, exist_ok=False)
    cfg = yaml.safe_load(CONFIG.read_text())
    shutil.copyfile(CONFIG, OUT / "executed-config.yaml")
    shutil.copyfile(Path(__file__), OUT / "executed-worker.py")
    stage = ROOT / cfg["staged_checkout"]
    sys.path.insert(0, str(stage))
    os.chdir(stage)
    from src.vehicle.benchmark import screen_launch
    from src.vehicle.mass import mass_properties
    from src.vehicle.schema import Vehicle

    source = ROOT / cfg["source_spec"]
    files = [
        CONFIG,
        Path(__file__).resolve(),
        source,
        ROOT / cfg["source_72_spec"],
        ROOT / cfg["source_S1"],
        ROOT / cfg["materials"],
        stage / "src/vehicle/schema.py",
        stage / "src/vehicle/mass.py",
        stage / "src/vehicle/benchmark.py",
    ]
    before = {str(p): sha(p) for p in files}
    r = {
        "status": "started",
        "limits": {"packet_cpu_s": 10, "wall_s": 20, "requested_threads": 1, "native_calls": 0},
        "input_sha256_before": before,
    }
    (OUT / "record.json").write_text(json.dumps(r, indent=2, default=json_scalar) + "\n")
    try:
        v = Vehicle.model_validate(yaml.safe_load(source.read_text()))
        orig = mass_properties(v)
        parts = {p.id: p for p in v.parts}
        c = cfg["collars"]
        g = cfg["growth_kg"]
        rho = c["density_kg_m3"] * 1e-6
        # Literal quadrature geometry is source-locked to these declared dimensions.
        assert (
            c["core_inner_radius_mm"],
            c["core_outer_radius_mm"],
            c["axial_height_mm"],
            c["clip_outer_radius_mm"],
            c["spoke_inner_x_mm"],
            c["spoke_outer_x_mm"],
            c["saddle_radius_mm"],
            c["saddle_base_axial_mm"],
        ) == (12, 18, 16, 32.2, 12, 31.6, 8, 8)
        assert c["saddle_axes_deg"] == [60, 180, 300]
        assert c["fore_arm_axes_deg"] == c["aft_foot_axes_deg"] == [0, 120, 240]
        assert (
            c["fore_arm_inner_x_mm"],
            c["fore_arm_outer_x_mm"],
            c["fore_arm_width_mm"],
            c["fore_arm_height_mm"],
        ) == (18, 31.6, 8, 11)
        assert (
            c["aft_foot_inner_x_mm"],
            c["aft_foot_outer_x_mm"],
            c["aft_foot_width_mm"],
            c["aft_foot_height_mm"],
        ) == (18, 31.6, 12, 16)
        q = {
            str(n): {"fore": collar(c, n, False), "aft": collar(c, n, True)}
            for n in cfg["budget"]["geometry_quadrature_orders"]
        }
        cvol = {k: q["128"][k]["volume_mm3"] for k in ("fore", "aft")}
        changes = {k: abs(q["128"][k]["volume_mm3"] - q["64"][k]["volume_mm3"]) * rho for k in cvol}
        r["quadrature"] = q
        r["quadrature_64_128_mass_change_g"] = changes
        if max(changes.values()) > cfg["budget"]["maximum_volume_mass_change_g"]:
            raise ValueError("Collar mass quadrature exceeds existing 0.05 g check")
        rem = {i: parts[i].resolved_mass_kg for i in cfg["frame_modifications"]["remove_ids"]}
        removed = sum(rem.values())
        ring = cfg["frame_modifications"]
        ring_v = (
            math.pi
            * (ring["ring_bore_new_radius_mm"] ** 2 - ring["ring_bore_old_radius_mm"] ** 2)
            * ring["ring_bore_length_mm"]
        )
        ring_each = ring_v * ring["plywood_density_kg_m3"] * 1e-9
        ca = cfg["carrier"]
        carrier_v = (
            math.pi * (ca["outer_radius_mm"] ** 2 - ca["inner_radius_mm"] ** 2) * ca["length_mm"]
        )
        carrier_mass = carrier_v * ca["density_kg_m3"] * 1e-9
        # Every slot, through-hole and counterbore is subtracted as a full independent solid, so overlaps over-subtract.
        slot = (
            3
            * 2
            * c["strap_slot_radial_mm"]
            * c["strap_slot_tangent_mm"]
            * c["strap_slot_axial_depth_mm"]
        )
        holes = (
            c["keeper_holes_per_collar"]
            * math.pi
            * (c["keeper_hole_d_mm"] / 2) ** 2
            * c["axial_height_mm"]
        )
        counter = (
            c["keeper_holes_per_collar"]
            * math.pi
            * ((c["keeper_counterbore_d_mm"] / 2) ** 2 - (c["keeper_hole_d_mm"] / 2) ** 2)
            * c["keeper_counterbore_depth_mm"]
        )
        cut = slot + holes + counter
        collar_mass = {k: (v - cut) * rho * 1e-3 for k, v in cvol.items()}
        collar_gross = {k: v * rho * 1e-3 for k, v in cvol.items()}
        fingers = (
            c["fore_fingers_count"]
            * math.prod(c["fore_finger_axial_radial_tangent_mm"])
            * rho
            * 1e-3
        )
        s = cfg["straps"]
        loop_len = (
            2 * (c["aft_contact_plane_mm"] - c["fore_contact_plane_mm"])
            + 2 * math.pi * c["saddle_radius_mm"]
            + s["sewn_overlap_mm_per_loop"]
        ) / 1000
        gpm = s["maximum_weight_oz_per_yard"] * 28.349523125 / 0.9144
        strap_mass = s["count"] * loop_len * gpm / 1000
        bk = cfg["backbone"]
        backbone_mass = (
            (bk["primary_length_m"] + sum(bk["branch_lengths_m"]))
            / 0.3048
            * bk["assumed_grams_per_foot"]
            / 1000
        )
        budget = {x["id"]: x["mass_kg"] for x in cfg["budget_parts"]}
        new = {
            "carrier": carrier_mass,
            "fore_collar_independent_cut_lower": collar_mass["fore"],
            "aft_collar_independent_cut_lower": collar_mass["aft"],
            "fingers_untrimmed": fingers,
            "three_loops_max_raw_weight": strap_mass,
            "backbone_assumed": backbone_mass,
            "connector": cfg["primary_connector"]["mass_kg"],
            **budget,
        }
        base = orig.mass_kg - removed - 2 * ring_each
        full = base + sum(new.values()) + g
        # Mass stations: unknown collar cuts assigned gross centroid, backbone envelope is bounded separately.
        stations = {
            "carrier": (ca["station_mm"] + ca["length_mm"] / 2) / 1000,
            "fore_collar_independent_cut_lower": (
                c["fore_contact_plane_mm"] - q["128"]["fore"]["axial_distance_from_plane_mm"]
            )
            / 1000,
            "aft_collar_independent_cut_lower": (
                c["aft_contact_plane_mm"] + q["128"]["aft"]["axial_distance_from_plane_mm"]
            )
            / 1000,
            "fingers_untrimmed": (
                c["fore_finger_station_mm"] + c["fore_finger_axial_radial_tangent_mm"][0] / 2
            )
            / 1000,
            "three_loops_max_raw_weight": (c["fore_contact_plane_mm"] + c["aft_contact_plane_mm"])
            / 2000,
            "backbone_assumed": 0.6105,
            "connector": cfg["primary_connector"]["planning_station_mm"] / 1000,
            **{x["id"]: x["station_m"] for x in cfg["budget_parts"]},
        }
        moment = (
            orig.mass_kg * orig.cg_m
            - sum(parts[i].resolved_mass_kg * parts[i].cg_station_m for i in rem)
            - sum(
                ring_each * (s + ring["ring_bore_length_mm"] / 2) / 1000
                for s in ring["ring_bore_stations_mm"]
            )
            + sum(new[k] * stations[k] for k in new)
            + g * cfg["growth_station_m"]
        )
        cg = moment / full
        uncertainty = (
            backbone_mass * 0.6105 + sum((cut * rho * 1e-3) * 0.016 for _ in range(2))
        ) / full
        launch = screen_launch(v, study_nominal_mass_kg=full - g)
        speed = launch["rail_exit_speed_mps"]
        recovery = {
            str(speed0): cfg["recovery"]["design_factor"]
            * full
            * (speed0**2 / (2 * cfg["recovery"]["stopping_distance_m"]) + 9.80665)
            for speed0 in cfg["recovery"]["speeds_mps"]
        }
        s1 = json.loads((ROOT / cfg["source_S1"]).read_text())
        r.update(
            status="completed_preliminary_not_qualified",
            source_73_mass_kg=orig.mass_kg,
            source_73_cg_station_m=orig.cg_m,
            removed_items_kg=rem,
            removed_total_kg=removed,
            ring_bore={
                "each_volume_mm3": ring_v,
                "each_mass_kg": ring_each,
                "stations_assumed_centers_mm": [
                    x + ring["ring_bore_length_mm"] / 2 for x in ring["ring_bore_stations_mm"]
                ],
            },
            carrier={"volume_mm3": carrier_v, "mass_kg": carrier_mass},
            collar_independent_cut={
                "slot_mm3": slot,
                "through_hole_mm3": holes,
                "counterbore_additional_mm3": counter,
                "total_mm3_each": cut,
                "net_mass_kg": collar_mass,
                "gross_mass_kg": collar_gross,
                "centroid_note": "gross axial centroid used after conservative cut; exact cut positions and overlap absent",
            },
            fore_fingers={
                "mass_kg": fingers,
                "direction_assumption": "aft from fore plane; no union intersection counted",
            },
            strap={
                "loop_length_m": loop_len,
                "max_linear_g_per_m": gpm,
                "three_loop_mass_kg": strap_mass,
            },
            backbone_mass_kg=backbone_mass,
            new_mass_items_kg=new,
            station_assumptions_m=stations,
            full_mass_with_growth_kg=full,
            axial_cg_estimate_m=cg,
            axial_cg_uncertainty_from_backbone_and_cut_station_m=uncertainty,
            full_tensor=None,
            guide=launch,
            required_15_margin_mps=speed - cfg["required_guide_mps"] if speed is not None else None,
            planning_15p5_margin_mps=(
                speed - cfg["planning_target_guide_mps"] if speed is not None else None
            ),
            recovery_factored_N=recovery,
            recovery_design_floor_N=max(
                cfg["recovery"]["required_prior_factored_floor_N"], recovery[str(20.4)]
            ),
            prior_recovery_floor_N=cfg["recovery"]["required_prior_factored_floor_N"],
            S1_full_mass_kg=s1["complete_preliminary_budget_kg"],
            source_plus_growth_kg=orig.mass_kg + g,
            qualification=False,
        )
    except Exception as exc:  # noqa: BLE001
        r.update(status="stopped", error=repr(exc), traceback=traceback.format_exc())
    finally:
        r["input_sha256_after"] = {str(p): sha(p) for p in files}
        r["source_unchanged"] = r["input_sha256_before"] == r["input_sha256_after"]
        u = resource.getrusage(resource.RUSAGE_SELF)
        r.update(
            cpu_s=u.ru_utime + u.ru_stime,
            wall_s=time.monotonic() - started,
            peak_rss_bytes=u.ru_maxrss,
        )
        (OUT / "record.json").write_text(json.dumps(r, indent=2, default=json_scalar) + "\n")
        print(
            json.dumps(
                {
                    k: r.get(k)
                    for k in (
                        "status",
                        "error",
                        "quadrature_64_128_mass_change_g",
                        "full_mass_with_growth_kg",
                        "axial_cg_estimate_m",
                        "required_15_margin_mps",
                        "planning_15p5_margin_mps",
                        "recovery_factored_N",
                        "cpu_s",
                        "wall_s",
                    )
                },
                indent=2,
            )
        )


if __name__ == "__main__":
    main()
