"""Bounded local F2 splice and fin/ring definition, not whole-vehicle CAD acceptance."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import resource
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import cadquery as cq
import numpy as np
import yaml

from src.vehicle.geometry import nose_radius


def tube(ro, ri, l):
    return cq.Workplane("XY").circle(ro).circle(ri).extrude(l).val()


def box(x, y, z):
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).val()


def run(spec, out):
    start = time.monotonic()
    # These deliberately local dimensions belong to one recorded candidate.
    # A changed source needs a new geometry definition, not a relabelled result.
    expected = "7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78"
    if hashlib.sha256(spec.read_bytes()).hexdigest() != expected:
        raise ValueError("Local F2 geometry is pinned to the selected v2 specification")
    d = yaml.safe_load(spec.read_text())
    by = {p["id"]: p for p in d["parts"]}
    out.mkdir(parents=True, exist_ok=False)
    full = tube(32.3, 15.8845, 12.2)
    ring = full
    for a in [0, 120, 240]:
        cut = box(22, 6.5, 7.4).translate((24.1, 0, 4.8)).rotate((0, 0, 0), (0, 0, 1), a)
        ring = ring.cut(cut)
    for a in [30, 210]:
        x, y = 23 * math.cos(math.radians(a)), 23 * math.sin(math.radians(a))
        ring = ring.cut(cq.Solid.makeCylinder(2.25, 14, cq.Vector(x, y, -1)))
    tabs = []
    for a in [0, 120, 240]:
        tabs.append(
            box(17.5165, 6, 109.8)
            .translate(((15.8845 + 33.401) / 2, 0, 5))
            .rotate((0, 0, 0), (0, 0, 1), a)
        )
    cg_tab = cq.Compound.makeCompound(tabs)
    unnotched = sum(full.intersect(t).Volume() for t in tabs)
    after = sum(ring.intersect(t).Volume() for t in tabs)
    sleeve = tube(32.225, 31.336, 100)
    seam = box(0.2, 4, 102).translate((0, 32, -1))
    sleeve = sleeve.cut(seam)
    theta = np.linspace(math.pi / 2 - 0.242, math.pi / 2 + 0.242, 31)
    pts = [(31.236 * math.cos(t), 31.236 * math.sin(t)) for t in theta] + [
        (30.347 * math.cos(t), 30.347 * math.sin(t)) for t in theta[::-1]
    ]
    patch = cq.Workplane("XY").polyline(pts).close().extrude(100).val()
    upper = tube(33.401, 32.512, 150).translate((0, 0, -100))
    lower = tube(33.401, 32.512, 150).translate((0, 0, 50))
    objects = {
        "notched_forward_ring": ring,
        "integral_fin_tabs": cg_tab,
        "formed_splice_sleeve": sleeve,
        "internal_seam_patch": patch,
        "upper_splice_tube": upper,
        "lower_splice_tube": lower,
    }
    for name, shape in objects.items():
        if not shape.isValid() or shape.Volume() <= 0:
            raise ValueError("invalid " + name)
        cq.exporters.export(shape, str(out / (name + ".step")))
    # Corner/section sampling is bounded and explicitly not a continuous service sweep.
    checks = []
    for id in [
        "flight_computer",
        "battery",
        "high_g_accel",
        "imu",
        "baro",
        "micro_sd",
        "logger_regulator",
        "logger_power_switch",
    ]:
        p = by[id]
        g = p["geometry"]
        L, W, H = g["bbox_m"]
        yc, zc = p.get("lateral_offset_m", [0, 0])
        zs = np.linspace(p["position_m"], p["position_m"] + L, 21)
        radius = nose_radius(zs, 0.160, 0.033401, "ogive") - 0.0012
        if zs.max() > 0.16:
            radius = np.where(zs > 0.16, 0.0308, radius)
        envelope = max(
            math.hypot(yc + sy * W / 2, zc + sz * H / 2) for sy in [-1, 1] for sz in [-1, 1]
        )
        checks.append(
            {
                "part": id,
                "minimum_sampled_radial_clearance_mm": float((radius.min() - envelope) * 1000),
                "axial_samples": 21,
                "scope": "axis-aligned envelope corners/ogive slices; excludes connector projections, insertion paths and wiring",
            }
        )
    report = {
        "identity": d["id"],
        "spec_sha256": hashlib.sha256(spec.read_bytes()).hexdigest(),
        "scope": "two local joint models and algebraic nose-envelope screen; not full rocket CAD or strength acceptance",
        "ring": {
            "full_unnotched_volume_mm3": full.Volume(),
            "notched_holed_volume_mm3": ring.Volume(),
            "removed_volume_mm3": full.Volume() - ring.Volume(),
            "before_tab_overlap_mm3": unnotched,
            "after_tab_overlap_mm3": after,
            "nominal_side_gap_mm": 0.25,
            "front_end_gap_mm": 0.2,
            "tab_to_tube_bond_centre_gap_mm": 0.2,
            "tab_to_tube_bond_edge_gap_mm": math.hypot(15.8845, 3) - 15.6845,
            "axial_thread_requirement_mm": 12.2 + 2 + 3.2 + 2,
            "fastener_status": "requires>=25mm usable thread; exact eye not selected,30mm provisional thread,45mm total envelope",
        },
        "splice": {
            "overlap_each_mm": 50,
            "radial_gap_nom_mm": 0.287,
            "minimum_declared_conditioned_gap_mm": 0.15,
            "maximum_declared_conditioned_gap_mm": 0.425,
            "receiving_basis": "body ID64.9--65.15mm, fitted sleeve OD64.45±.05mm, additional differential radial envelope±.05mm; proposed incoming/conditioning acceptance, not supplier tolerances",
            "minimum_centred_bore_mm": 60.694,
            "adhesive_nominal_film_g": math.pi * (32.512**2 - 32.225**2) * 100 * 0.0012,
            "patch_sleeve_intersection_mm3": patch.intersect(sleeve).Volume(),
            "tube_sleeve_intersection_mm3": upper.intersect(sleeve).Volume()
            + lower.intersect(sleeve).Volume(),
            "no_air_gap_parallel_to_filled_epoxy": True,
        },
        "nose_envelope_checks": checks,
        "geometry_checks_pass": after < 1e-6 and patch.intersect(sleeve).Volume() < 1e-6,
        "status": "local geometry only; no eye, bond, support-stiffness, thermal, flutter or flight release",
        "wall_s": time.monotonic() - start,
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--spec", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    r = run(a.spec, a.output)
    print(json.dumps(r, indent=2))
