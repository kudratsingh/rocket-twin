"""Bound one forward-shifted layered trainer fin and its real root interfaces.

This isolated study does not change active configurations. SI calculations use
uniform-pressure beam resultants M=w(L-x)^2/2, V=w(L-x), unit-load integration
delta_b=int(M*(L-x)/EI dx), delta_s=int(V/GA dx), and bonded-surface springs
K=int(B.T D B dA). Thin closed-section torsion uses Bredt-Batho
GJ=4 A_m^2 / int(ds/(G t)) (Roark, torsion of thin-walled closed sections).
Static divergence is the elementary positive-feedback condition
Ktheta=q*S*CNa*e; it is not a dynamic-flutter solution. Beam reduction omits
chordwise/edge stress and local peel; missing quantities never become zero/pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fin_acceptance import panel_force_n
from scripts.wo03_recovery_mass_budget import budget
from src.analysis.fin_attachment import normal_force_coefficient_per_radian
from src.cad.assembly import mesh, rigid_intersections
from src.cad.parts import (
    box,
    compound,
    cq,
    local_shape,
    placed_shape,
    properties,
    shape_digest,
    tube,
)
from src.vehicle.aero import center_of_pressure
from src.vehicle.benchmark import screen_launch
from src.vehicle.mass import mass_properties
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import CADMass, Vehicle, load_vehicle, vehicle_input_paths


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _part(vehicle: Vehicle, ident: str):
    return next(p for p in vehicle.parts if p.id == ident)


def shifted_copy(base: Vehicle, cfg: dict[str, Any]) -> Vehicle:
    """Move complete root and both real slot definitions, then reconcile CAD."""
    v = base.model_copy(deep=True)
    fin, shell, frame = (_part(v, ident) for ident in ("fin_set", "aft_shell", "gimbal_frame"))
    shift = float(cfg["forward_shift_m"])
    fin.position_m -= shift
    fin.geometry["thickness_m"] = 0.005
    assert fin.cad and shell.cad and frame.cad
    fin.cad.parameters["root_gusset_span_mm"] = 20
    shell.cad.parameters["fin_slot_start_mm"] -= shift * 1000
    frame.cad.parameters["tab_slot_start_mm"] -= shift * 1000
    for p in (fin, shell, frame):
        props = properties(p, local_shape(p))
        p.cad_mass = CADMass.model_validate(props)
        p.mass_kg = props["volume_m3"] * DENSITY_KG_M3[p.material]
        p.cg_offset_m = -props["cg_local_body_m"][0]
    return v


def root_support_extents(vehicle: Vehicle) -> dict[str, Any]:
    fin, shell, frame = (_part(vehicle, x) for x in ("fin_set", "aft_shell", "gimbal_frame"))
    assert fin.cad and shell.cad and frame.cad
    front = fin.position_m
    end = front + fin.geometry["root_chord_m"]
    shell_end = shell.position_m + shell.geometry["length_m"]
    frame_end = frame.position_m + frame.geometry["length_m"]
    tab_front = front + fin.cad.parameters["tab_offset_mm"] / 1000
    tab_end = tab_front + fin.cad.parameters["tab_length_mm"] / 1000
    return {
        "configuration_id": vehicle.id,
        "frame_part_id": frame.id,
        "root_stations_m": [front, end],
        "shell_stations_m": [shell.position_m, shell_end],
        "frame_stations_m": [frame.position_m, frame_end],
        "tab_stations_m": [tab_front, tab_end],
        "shell_slot_front_station_m": shell.position_m
        + shell.cad.parameters["fin_slot_start_mm"] / 1000,
        "frame_channel_front_station_m": frame.position_m
        + frame.cad.parameters["tab_slot_start_mm"] / 1000,
        "unsupported_foot_aft_length_m": max(0.0, end - shell_end),
        "unsupported_tab_aft_length_m": max(0.0, tab_end - frame_end),
        "whole_foot_inside_shell_axial_extent": front >= shell.position_m - 1e-12
        and end <= shell_end + 1e-12,
        "whole_tab_inside_frame_axial_extent": tab_front >= frame.position_m - 1e-12
        and tab_end <= frame_end + 1e-12,
        "interpretation": "Axial support coverage only; radial gaps, stiffness and actual bonds are separately evaluated, not granted by these booleans.",
    }


def layered_shapes(v: Vehicle, c: dict[str, Any]) -> list[tuple[str, Any, float]]:
    """Explicit nonoverlapping nominal material solids for one three-fin set.

    Carbon density is derived from supplier areal mass / stated actual thickness.
    The cap's thin adhesive is charged as an equivalent cured mass, not hidden in
    its laminate density. Main root potting is the actual trimmed channel void.
    """
    fin = _part(v, "fin_set")
    assert fin.cad
    g, p = fin.geometry, fin.cad.parameters
    r, span, chord = (g[k] * 1000 for k in ("radius_m", "span_m", "root_chord_m"))
    core, skin, bond, band = (
        c[k] * 1000
        for k in ("core_thickness_m", "skin_thickness_m", "face_bond_thickness_m", "root_band_m")
    )
    outer = core / 2 + bond + skin
    foot = c["foot_bond_thickness_m"] * 1000
    side_bond = c["gusset_face_bond_thickness_m"] * 1000
    body = cq.Solid.makeCylinder(r, chord + 2, cq.Vector(0, 0, -1))
    body_plus = cq.Solid.makeCylinder(r + foot, chord + 2, cq.Vector(0, 0, -1))
    skin_density = c["skin_areal_mass_kg_m2"] / c["skin_thickness_m"]
    tab = box(p["tab_depth_mm"], core, p["tab_length_mm"]).translate(
        (r - p["tab_depth_mm"] / 2, 0, p["tab_offset_mm"])
    )
    root = box(band, core, chord).translate((r + band / 2, 0, 0)).fuse(tab)
    one = [
        ("root_insert_and_tab", root, DENSITY_KG_M3["plywood"]),
        (
            "foam_core",
            box(span - band, core, chord).translate((r + band + (span - band) / 2, 0, 0)),
            c["core_density_kg_m3"],
        ),
    ]
    for side in (-1, 1):
        one += [
            (
                f"skin_{side}",
                box(span, skin, chord).translate(
                    (r + span / 2, side * (core / 2 + bond + skin / 2), 0)
                ),
                skin_density,
            ),
            (
                f"face_bond_{side}",
                box(span, bond, chord).translate((r + span / 2, side * (core / 2 + bond / 2), 0)),
                DENSITY_KG_M3["epoxy"],
            ),
        ]
        wedge = (
            cq.Workplane("XY")
            .polyline(
                [
                    (r - p["root_gusset_inset_mm"], side * (outer + side_bond)),
                    (
                        r - p["root_gusset_inset_mm"],
                        side * (outer + side_bond + p["root_gusset_base_mm"]),
                    ),
                    (r + p["root_gusset_span_mm"], side * (outer + side_bond)),
                ]
            )
            .close()
            .extrude(chord)
            .val()
        )
        one += [
            (f"gusset_{side}", wedge.cut(body_plus), DENSITY_KG_M3["plywood"]),
            (f"foot_bond_{side}", wedge.intersect(body_plus).cut(body), DENSITY_KG_M3["epoxy"]),
            (
                f"gusset_face_bond_{side}",
                box(band, side_bond, chord)
                .translate((r + band / 2, side * (outer + side_bond / 2), 0))
                .cut(body_plus),
                DENSITY_KG_M3["epoxy"],
            ),
        ]
    # Fill only the actual channel void inside the G11 outer cylinder. Its
    # shared faces meet the channel walls/floor and the solid plywood tab.
    frame = _part(v, "gimbal_frame")
    assert frame.cad
    fp = frame.cad.parameters
    channel = (
        box(fp["fin_channel_depth_mm"], fp["fin_slot_width_mm"], p["tab_length_mm"])
        .translate((fp["fin_channel_radius_mm"], 0, p["tab_offset_mm"]))
        .intersect(cq.Solid.makeCylinder(frame.geometry["radius_m"] * 1000, chord))
    )
    one.append(("tab_potting", channel.cut(root), DENSITY_KG_M3["epoxy"]))
    shell = _part(v, "aft_shell")
    gap_inner = frame.geometry["radius_m"] * 1000
    gap_outer = shell.geometry["inner_radius_m"] * 1000
    if gap_outer <= gap_inner:
        raise ValueError("Root-gap backing hypothesis requires a positive frame/shell gap")
    backing = (
        tube(gap_outer, gap_inner, chord)
        .intersect(box(10, fp["rail_width_mm"], chord).translate((gap_inner, 0, 0)))
        .cut(
            box(10, fp["fin_slot_width_mm"], p["tab_length_mm"]).translate(
                (gap_inner, 0, p["tab_offset_mm"])
            )
        )
    )
    one.append(("frame_shell_gap_bond", backing, DENSITY_KG_M3["epoxy"]))
    cap = c["edge_cap_thickness_m"] * 1000
    lap = c["edge_cap_overlap_m"] * 1000
    for aft in (False, True):
        z0 = chord if aft else -cap
        web = box(span, 2 * outer, cap).translate((r + span / 2, 0, z0))
        for side in (-1, 1):
            # Close the foam span only. Root-band gussets occupy these face
            # corners; do not let glass laps overlap the actual wood solids.
            flange = box(span - band, cap, lap).translate(
                (r + band + (span - band) / 2, side * (outer + cap / 2), chord - lap if aft else 0)
            )
            one.append((f"cap_lap_{aft}_{side}", flange, DENSITY_KG_M3["fiberglass"]))
        one.append((f"cap_web_{aft}", web, DENSITY_KG_M3["fiberglass"]))
    return [
        (name, compound([shape.rotate((0, 0, 0), (0, 0, 1), i * 120) for i in range(3)]), density)
        for name, shape, density in one
    ]


def composite_properties(layers: list[tuple[str, Any, float]]) -> dict[str, Any]:
    """Sum actual per-material mass, centroid and full inertia in CAD mm axes."""
    rows, total = [], 0.0
    moment = np.zeros(3)
    for name, shape, density in layers:
        volume = float(shape.Volume())
        mass = volume * 1e-9 * density
        center = np.array(shape.Center().toTuple())
        rows.append(
            {
                "name": name,
                "volume_mm3": volume,
                "density_kg_m3": density,
                "mass_kg": mass,
                "centroid_cad_mm": center.tolist(),
                "valid_solid": bool(shape.isValid()),
                "solid_count": len(shape.Solids()),
            }
        )
        total += mass
        moment += mass * center
    center = moment / total
    inertia = np.zeros((3, 3))
    for row, (_, shape, _) in zip(rows, layers, strict=True):
        d = np.asarray(row["centroid_cad_mm"]) - center
        inertia += row["mass_kg"] * (
            np.asarray(cq.Shape.matrixOfInertia(shape)) / row["volume_mm3"]
            + np.dot(d, d) * np.eye(3)
            - np.outer(d, d)
        )
    transform = np.array([[0, 0, -1], [1, 0, 0], [0, -1, 0]])
    return {
        "layers": rows,
        "mass_kg": total,
        "cg_local_body_m": (transform @ center * 1e-3).tolist(),
        "inertia_per_kg_m2": (transform @ inertia @ transform.T / total * 1e-6).tolist(),
        "volume_m3": sum(r["volume_mm3"] for r in rows) * 1e-9,
    }


def reconcile_root_adhesive_budget(
    vehicle: Vehicle,
    material_rows: list[dict[str, Any]],
    cap_bond_mass_kg: float,
    tip_seal_mass_kg: float,
    cfg: dict[str, Any],
) -> dict[str, Any]:
    """Allocate old tab/gusset allowance once, retaining residual fillet mass.

    This changes only a supplied mass budget. All explicit material solids,
    additional manufacturing bonds and their masses remain untouched.
    """
    rule = cfg["root_adhesive_budget"]
    allowance = _part(vehicle, rule["part_id"])
    tab_budget = float(rule["baseline_tabs_and_fillets_kg"])
    gusset_budget = float(rule["baseline_gussets_kg"])
    baseline = tab_budget + gusset_budget
    if not allowance.cad or (
        allowance.cad.mass_basis != "supplied_or_estimated"
        or allowance.cad.role != "distributed_budget"
        or abs(allowance.resolved_mass_kg - baseline) > 1e-12
    ):
        raise ValueError(
            "Root adhesive allocation requires the unreconciled baseline allowance exactly once"
        )
    masses = {row["name"]: float(row["mass_kg"]) for row in material_rows}
    if len(masses) != len(material_rows):
        raise ValueError("Duplicate material names in adhesive ledger")
    tab = masses["tab_potting"]
    gusset_names = [
        f"{kind}_{side}" for kind in ("gusset_face_bond", "foot_bond") for side in (-1, 1)
    ]
    gussets = sum(masses[name] for name in gusset_names)
    if tab <= 0 or gussets <= 0 or tab > tab_budget or gussets > gusset_budget:
        raise ValueError(
            "Explicit root bonds exceed or invalidate their existing allowance; resolve the bill explicitly"
        )
    overlap = tab + gussets
    residual = baseline - overlap
    added = {
        "skin_core_manufacturing_bonds": masses["face_bond_-1"] + masses["face_bond_1"],
        "structural_cap_bonds": cap_bond_mass_kg,
        "outer_tip_seal": tip_seal_mass_kg,
        "new_frame_shell_gap_bonds": masses["frame_shell_gap_bond"],
    }
    if min(added.values()) <= 0:
        raise ValueError("Every additional construction bond/seal must remain charged")
    allowance.mass_kg = residual
    allowance.learn = (
        f"Residual fin-root adhesive allowance after allocating {overlap*1000:.6f} g of the "
        f"original {baseline*1000:.3f} g budget to the explicit tab, gusset-face and curved-foot "
        "bonds already included in fin_set. This remaining mass covers unmodeled fillets and "
        "application variation; new skin/core/cap/seal/backing bonds remain additional."
    )
    assert allowance.build
    allowance.build.notes = (
        f"Original root budget: {tab_budget*1000:.3f} g tabs/fillets plus "
        f"{gusset_budget*1000:.3f} g gussets. Explicit tab potting {tab*1000:.6f} g and "
        f"gusset/foot bonds {gussets*1000:.6f} g are allocated to fin_set, leaving "
        f"{residual*1000:.6f} g here. No credit is taken for new skin/core bonds, cap bonds, "
        "tip seal or frame/shell gap pads. Strength, cure and actual applied mass remain unverified."
    )
    return {
        "baseline_part_id": allowance.id,
        "baseline_allowance_kg": baseline,
        "baseline_tabs_and_fillets_kg": tab_budget,
        "baseline_gussets_kg": gusset_budget,
        "explicit_tab_potting_kg_allocated_from_old_budget": tab,
        "explicit_gusset_face_and_foot_bonds_kg_allocated_from_old_budget": gussets,
        "overlap_removed_from_residual_budget_kg": overlap,
        "residual_unmodeled_fillets_and_application_allowance_kg": residual,
        "residual_tabs_and_fillets_kg": tab_budget - tab,
        "residual_gussets_kg": gusset_budget - gussets,
        "existing_root_interfaces_total_after_allocation_kg": overlap + residual,
        "additional_new_construction_mass_kg": added,
        "total_bond_and_seal_mass_before_reconciliation_kg": baseline
        + overlap
        + sum(added.values()),
        "total_bond_and_seal_mass_after_reconciliation_kg": baseline + sum(added.values()),
        "residual_budget_mass_station_m_unchanged": allowance.cg_station_m,
        "geometry_changed": False,
        "fin_set_mass_changed_by_this_allocation": False,
        "basis": rule["allocation_basis"],
        "qualification": "Mass bookkeeping only; no bond strength, hot peel or applied-mass qualification",
    }


def layered_panel(
    c: dict[str, Any], force_n: float, span: float, chord: float, points: int = 32
) -> dict[str, Any]:
    """Piecewise sandwich beam bending + core shear at minimum dimensions."""
    tc = c["core_thickness_m"] - c["core_thickness_tolerance_m"]
    ts = c["skin_thickness_m"] - c["skin_thickness_tolerance_m"]
    tb = c["face_bond_thickness_m"]
    fraction = c["hot_property_fraction"]
    es = c["skin_youngs_pa_typical"] * fraction
    ec = c["core_youngs_pa_typical"] * fraction
    gc = c["core_shear_pa_typical"] * fraction
    ep = 2e9 * fraction
    gp = 0.2e9 * fraction
    d = tc + 2 * tb + ts
    skin_i = 2 * chord * (ts**3 / 12 + ts * (d / 2) ** 2)
    skin_ei = es * skin_i
    root_ei = skin_ei + ep * chord * tc**3 / 12
    outer_ei = skin_ei + ec * chord * tc**3 / 12
    w = force_n / span
    bending = shear = 0.0
    section_rows = []
    abscissa, weights = np.polynomial.legendre.leggauss(points)
    band = c["root_band_m"]
    for left, right, ei, ga, label in [
        (0.0, band, root_ei, gp * chord * tc, "solid-root-band"),
        (band, span, outer_ei, gc * chord * tc, "foam-panel"),
    ]:
        x = left + (abscissa + 1) * (right - left) / 2
        wt = weights * (right - left) / 2
        bending += float(np.sum(wt * w * (span - x) ** 3 / (2 * ei)))
        shear += float(np.sum(wt * w * (span - x) / ga))
        moment = w * (span - left) ** 2 / 2
        transverse = w * (span - left)
        section_rows.append(
            {
                "physical_region": label,
                "spanwise_interval_m": [left, right],
                "EI_nm2": ei,
                "GA_n": ga,
                "peak_spanwise_face_absolute_stress_pa": es * moment / ei * (d / 2 + ts / 2),
                "peak_core_shear_pa": transverse / (chord * tc),
                "face_to_core_mean_interlaminar_shear_pa": transverse / (chord * d),
                "required_hot_face_tension_and_compression_bound_DF3_pa": c["design_factor"]
                * es
                * moment
                / ei
                * (d / 2 + ts / 2),
            }
        )
    foam = section_rows[-1]
    return {
        "force_n": force_n,
        "minimum_core_thickness_m": tc,
        "minimum_skin_thickness_m": ts,
        "skin_centroid_spacing_m": d,
        "quadrature_points_per_physical_region": points,
        "bending_tip_deflection_m": bending,
        "core_shear_tip_deflection_m": shear,
        "panel_only_tip_deflection_m": bending + shear,
        "root_translation_and_rotation_compliance_budget_m": 0.001 - bending - shear,
        "required_bending_root_rotation_stiffness_nm_rad_if_no_translation": (
            force_n * span**2 / (2 * (0.001 - bending - shear)) if bending + shear < 0.001 else None
        ),
        "regions": section_rows,
        "foam_shear_hot_DF3_margin_typical_property": c["core_shear_strength_pa_typical"]
        * fraction
        / (c["design_factor"] * foam["peak_core_shear_pa"])
        - 1,
        "stress_components_not_calculated": [
            "chordwise normal",
            "in-plane span/chord shear",
            "local cap/root edge",
            "bond peel",
            "skin wrinkling and microbuckling",
        ],
        "strength_acceptance_passed": False,
        "scope": "Piecewise 1D bending/core-shear reduction; includes no gusset stiffening credit and no ideal-root compliance credit. It is not a replacement for three-level installed shell/solid FEA or all-component convergence.",
    }


def curved_foot(
    c: dict[str, Any],
    force_n: float,
    span: float,
    chord: float,
    radius: float,
    thickness: float,
    bond_t: float,
) -> dict[str, Any]:
    """Finite full-foot spring on a rigid cylinder, never installed qualification."""
    half = thickness / 2 + c["gusset_face_bond_thickness_m"]
    radial = 0.020
    base = 0.003
    inset = 0.001

    # Intersect the actual wedge hypotenuse and outer body circle at the foot.
    def inside(y: float) -> float:
        x = math.sqrt(radius**2 - y**2)
        return y - half - base * (radius + radial - x) / (radial + inset)

    lo, hi = half, half + base
    for _ in range(64):
        mid = (lo + hi) / 2
        if inside(mid) > 0:
            hi = mid
        else:
            lo = mid
    yend = (lo + hi) / 2
    a, b = math.asin(half / radius), math.asin(yend / radius)
    gauss, wt = np.polynomial.legendre.leggauss(64)
    e = c["hot_adhesive_youngs_pa_estimate"]
    shear = e / (2 * (1 + c["adhesive_poisson_estimate"]))
    stiffness = np.zeros((3, 3))
    patches = []
    for side in (-1, 1):
        phi = side * ((a + b) / 2 + gauss * (b - a) / 2)
        area = wt * (b - a) / 2 * radius * chord
        for angle, da in zip(phi, area, strict=True):
            n = np.array([math.cos(angle), math.sin(angle)])
            t = np.array([-math.sin(angle), math.cos(angle)])
            x, y = radius * n - np.array([radius, 0.0])
            k = (e * np.outer(n, n) + shear * np.outer(t, t)) / bond_t
            operator = np.array([[1, 0, -y], [0, 1, x]])
            stiffness += operator.T @ k @ operator * da
            patches.append((operator, k, n, t, float(da)))
    load = np.array([0.0, force_n, force_n * span / 2])
    motion = np.linalg.solve(stiffness, load)
    normals, tangents = [], []
    recovered = np.zeros(3)
    for operator, k, n, t, da in patches:
        traction = k @ operator @ motion
        normals.append(float(n @ traction))
        tangents.append(float(t @ traction))
        recovered += operator.T @ traction * da
    condensed = stiffness[2, 2] - stiffness[2, :2] @ np.linalg.solve(
        stiffness[:2, :2], stiffness[:2, 2]
    )
    return {
        "actual_foot_area_per_side_m2": radius * (b - a) * chord,
        "foot_tangential_y_interval_m": [half, yend],
        "fin_face_bond_area_per_side_m2": radial * chord,
        "rejected_triangular_cross_section_as_face_area_m2": radial * chord / 2,
        "bondline_m": bond_t,
        "hot_adhesive_E_pa_estimate": e,
        "rigid_backing_condensed_Ktheta_nm_rad": float(condensed),
        "root_translation_m": motion[:2].tolist(),
        "root_rotation_rad": float(motion[2]),
        "added_tip_motion_from_rigid_root_m": float(motion[1] + span * motion[2]),
        "mean_spring_peak_normal_traction_pa": max(abs(x) for x in normals),
        "mean_spring_peak_shear_traction_pa": max(abs(x) for x in tangents),
        "required_hot_normal_strength_DF3_pa": max(abs(x) for x in normals) * c["design_factor"],
        "required_hot_shear_strength_DF3_pa": max(abs(x) for x in tangents) * c["design_factor"],
        "force_and_moment_residual": (recovered - load).tolist(),
        "installed_stiffness_lower_bound": None,
        "peel_acceptance_passed": False,
        "scope": "Smooth full-area elastic adhesive foundation; rigid wood/root and rigid cylinder make this an optimistic stiffness bound. No edge singularity is clipped or called passed. Paper through-thickness, frame/ring/shell flexibility, bond-edge peel and continuity remain unresolved.",
    }


def torsion_targets(
    c: dict[str, Any], panel: dict[str, Any], q: float, span: float, chord: float
) -> dict[str, Any]:
    slope = normal_force_coefficient_per_radian(span, chord, chord)
    d, ts = panel["skin_centroid_spacing_m"], panel["minimum_skin_thickness_m"]
    target_q = q * 1.2**2
    required = target_q * (span * chord) * slope * chord / 4
    rows = []
    for cold_shear in c["cold_skin_shear_pa_estimate"]:
        gs = cold_shear * c["hot_property_fraction"]
        gc = c["cold_cap_shear_pa_estimate"] * c["hot_property_fraction"]
        gj = (
            4
            * (chord * d) ** 2
            / (2 * chord / (gs * ts) + 2 * d / (gc * c["edge_cap_thickness_m"]))
        )
        # In the root band the leading/trailing face laps stop at the gussets.
        # Retain only the solid wood core's torsion, no closed-box/root-skin
        # stiffness credit. This remains a layered torsion approximation.
        tc = panel["minimum_core_thickness_m"]
        root_gj = (
            0.2e9
            * c["hot_property_fraction"]
            * chord
            * tc**3
            * (1 / 3 - 0.21 * tc / chord * (1 - tc**4 / (12 * chord**4)))
        )
        panel_k = 1 / (c["root_band_m"] / root_gj + (span - c["root_band_m"]) / gj)
        rows.append(
            {
                "skin_shear_pa_estimate_hot": gs,
                "GJ_nm2_thin_closed_box": gj,
                "root_band_GJ_nm2_solid_wood_only": root_gj,
                "panel_torsion_stiffness_nm_rad": panel_k,
                "required_root_torsion_K_nm_rad_series_model": (
                    required * panel_k / (panel_k - required) if panel_k > required else None
                ),
            }
        )
    return {
        "historical_max_q_pa": q,
        "provisional_target_q_pa": target_q,
        "positive_feedback_eccentricity_m_assumed": chord / 4,
        "required_total_static_torsion_K_nm_rad": required,
        "scenarios": rows,
        "root_torsion_stiffness_available": False,
        "dynamic_flutter_acceptance_passed": False,
        "NACA_TN4197_substitution_allowed": False,
        "scope": "Necessary static-divergence stiffness target only. Bredt closed-box sensitivity requires intact bonded structural glass leading/trailing edge caps and intact skins/core. No guaranteed skin shear/Poisson/full laminate data, installed torsion, damping or dynamic aeroelastic solution; homogeneous NACA thickness substitution is inapplicable to this sandwich.",
    }


def run(config: Path, output: Path) -> Path:
    cfg = yaml.safe_load(config.read_text())
    c = cfg["root_closure"]
    base_path = Path(cfg["base_vehicle"])
    flight_path = Path(cfg["flight_record"])
    budget_path = Path(cfg["budget_config"])
    inputs = {
        config,
        base_path,
        flight_path,
        budget_path,
        Path(__file__),
        *vehicle_input_paths(base_path),
    }
    inputs.update(Path("src/cad").glob("*.py"))
    inputs.update(Path("src/vehicle").glob("*.py"))
    historical_panel_path = Path(c["historical_panel_report"])
    historical_refinement_path = Path(c["historical_refinement_report"])
    prior_unreconciled_path = Path(c["prior_unreconciled_record"])
    inputs.update(
        {
            historical_panel_path,
            historical_refinement_path,
            prior_unreconciled_path,
            Path("scripts/wo03_fin_acceptance.py"),
            Path("scripts/wo03_recovery_mass_budget.py"),
            Path("src/analysis/fin_attachment.py"),
        }
    )
    before = {str(p): sha(p) for p in sorted(inputs) if p.is_file()}
    base = load_vehicle(base_path)
    v = shifted_copy(base, c)
    ply = v.model_copy(deep=True)
    bc = yaml.safe_load(budget_path.read_text())
    battery = _part(v, "battery")
    battery.mass_kg = bc["main_battery_trade"]["supplied_mass_kg"]
    battery.geometry = {"bbox_m": bc["main_battery_trade"]["envelope_m"]}
    battery.cg_offset_m = battery.geometry["bbox_m"][0] / 2
    battery.cad_mass = None
    layers = layered_shapes(v, c)
    composite = composite_properties(layers)
    # Charge structural-cap bonding and the explicit outer-tip closure once.
    fin = _part(v, "fin_set")
    span, chord = (float(fin.geometry[k]) for k in ("span_m", "root_chord_m"))
    cap_bond_mass = (
        3
        * 4
        * (span - c["root_band_m"])
        * c["edge_cap_overlap_m"]
        * c["edge_cap_bond_thickness_m"]
        * DENSITY_KG_M3["epoxy"]
    )
    reserve = cap_bond_mass + c["tip_edge_seal_mass_kg"]
    fin.mass_kg = composite["mass_kg"] + reserve
    fin.geometry["thickness_m"] = c["core_thickness_m"] + 2 * (
        c["skin_thickness_m"] + c["face_bond_thickness_m"]
    )
    fin.material = "carbon_epoxy_sandwich"
    assert fin.cad
    fin.cad.generator = "wo03_layered_trainer_fin_study"
    fin.cad.mass_basis = "supplied_or_estimated"
    fin.cad.parameters["layered_study"] = c
    fin.cad.notes = "Explicit study-only layer geometry/mass from scripts/wo03_trainer_fin_root.py; unsupported by the active CAD generator. No adopted manufacture or engineering pass."
    fin.cad_mass = CADMass(
        shape_sha256=shape_digest(fin),
        volume_m3=composite["volume_m3"],
        cg_local_body_m=composite["cg_local_body_m"],
        inertia_per_kg_m2=composite["inertia_per_kg_m2"],
        basis="Mass-weighted explicit material solids; cap-bond/tip-seal mass conservatively co-located with the whole fin-set centroid/inertia",
    )
    fin.cg_offset_m = -composite["cg_local_body_m"][0]
    adhesive_ledger = reconcile_root_adhesive_budget(
        v, composite["layers"], cap_bond_mass, c["tip_edge_seal_mass_kg"], c
    )
    prior_unreconciled = json.loads(prior_unreconciled_path.read_text())
    prior_masses = {
        row["name"]: row["mass_kg"] for row in prior_unreconciled["material_solids"]["layers"]
    }
    if set(prior_masses) != {row["name"] for row in composite["layers"]}:
        raise ValueError(
            "Bookkeeping-only correction unexpectedly changed material-solid identities"
        )
    geometry_mass_change = max(
        abs(row["mass_kg"] - prior_masses[row["name"]]) for row in composite["layers"]
    )
    if (
        geometry_mass_change > 1e-12
        or abs(fin.mass_kg - prior_unreconciled["layered_fin_mass_kg"]) > 1e-12
    ):
        raise ValueError(
            "Bookkeeping-only correction unexpectedly changed explicit fin/root material mass"
        )
    v.id = c["id"]
    v.name = "Experimental forward-shifted carbon/PVC trainer fin"
    output.mkdir(parents=True, exist_ok=True)
    (output / "study-inputs.yaml").write_text(config.read_text())
    resolved = output / "resolved-candidate.yaml"
    resolved.write_text(yaml.safe_dump(v.model_dump(by_alias=True), sort_keys=False))
    # Read back the exact reviewable copy before evaluating mass/static/guide.
    v = load_vehicle(resolved)
    fin = _part(v, "fin_set")
    fin_shape = compound([shape for _, shape, _ in layers])
    cq.exporters.export(fin_shape, str(output / "fin-layers.step"))
    solids = {
        p.id: (
            fin_shape.translate((0, 0, p.position_m * 1000))
            if p.id == "fin_set"
            else placed_shape(p)
        )
        for p in v.parts
    }
    collisions = rigid_intersections(v, solids, moving_ids={"fin_set", "aft_shell", "gimbal_frame"})
    local_layers = {name: shape for name, shape, _ in layers}
    placed_layers = {
        name: shape.translate((0, 0, fin.position_m * 1000)) for name, shape in local_layers.items()
    }
    contact_pairs = [
        ("tab_potting", "gimbal_frame"),
        ("tab_potting", "root_insert_and_tab"),
        ("frame_shell_gap_bond", "gimbal_frame"),
        ("frame_shell_gap_bond", "aft_shell"),
        ("foot_bond_-1", "aft_shell"),
        ("foot_bond_1", "aft_shell"),
        ("gusset_face_bond_-1", "skin_-1"),
        ("gusset_face_bond_1", "skin_1"),
    ]
    contact_checks = [
        {
            "a": a,
            "b": b,
            "minimum_distance_mm": placed_layers[a].distance(
                placed_layers[b] if b in placed_layers else solids[b]
            ),
        }
        for a, b in contact_pairs
    ]
    cq.exporters.export(compound(list(solids.values())), str(output / "assembly.step"))
    import trimesh

    scene = trimesh.Scene()
    for ident, shape in solids.items():
        p = _part(v, ident)
        scene.add_geometry(
            mesh(shape, v.airframe["length_m"], p.cad.color), node_name=ident, geom_name=ident
        )
    scene.export(output / "assembly.glb")
    flight = json.loads(flight_path.read_text())
    flight_cases = [x for x in flight["cases"] if x.get("vehicle") == base.id]
    envelope = max(flight_cases, key=lambda x: x["metrics"]["max_dynamic_pressure_pa"])
    q = float(envelope["metrics"]["max_dynamic_pressure_pa"])
    force = max(panel_force_n(_part(base, "fin_set"), 40000, 5), 2 * q * span * chord)
    historical_panel = json.loads(historical_panel_path.read_text())
    historical_static = historical_panel["static_40kpa_5deg"]
    force_ratio = force / historical_static["force_per_fin_n"]
    scaled_old_hot_components = {
        name: {
            "stress_pa_linear_scaling": component["regional_peak_absolute_stress_pa"] * force_ratio,
            "DF3_margin_linear_scaling": (component["screen_margin"] + 1) / force_ratio - 1,
        }
        for name, component in historical_static["hot_strength_screen"]["components"].items()
    }
    panels = [layered_panel(c, force, span, chord, n) for n in (16, 32, 64)]
    feet = [
        curved_foot(
            c,
            force,
            span,
            chord,
            float(fin.geometry["radius_m"]),
            float(fin.geometry["thickness_m"]),
            t,
        )
        for t in c["root_bond_thickness_sensitivity_m"]
    ]
    cp = center_of_pressure(v)
    properties_by_depletion = [mass_properties(v, f) for f in (0.0, 1.0)]
    static = []
    fin_only_static = []
    guide = []
    for depletion, props in zip((0.0, 1.0), properties_by_depletion, strict=True):
        extra = v.design.mass_allowance_kg
        cg = (props.mass_kg * props.cg_m + extra * v.airframe["length_m"]) / (props.mass_kg + extra)
        fin_only_static.append(
            {
                "depletion_fraction": depletion,
                "full_growth_mass_kg": props.mass_kg + extra,
                "cp_station_m": cp,
                "cg_station_m_full_growth_at_aft": cg,
                "margin_cal": (cp - cg) / v.airframe["body_diameter_m"],
            }
        )
    for thermal in c["added_thermal_mass_kg_hypothesis"]:
        increment = (
            c["added_recovery_mass_kg_hypothesis"] + thermal - cfg["package_a_rail_mass_saving_kg"]
        )
        for depletion, props in zip((0.0, 1.0), properties_by_depletion, strict=True):
            extra = v.design.mass_allowance_kg + increment
            cg = (props.mass_kg * props.cg_m + extra * v.airframe["length_m"]) / (
                props.mass_kg + extra
            )
            static.append(
                {
                    "depletion_fraction": depletion,
                    "thermal_increment_kg_hypothesis": thermal,
                    "nominal_vehicle_mass_kg": props.mass_kg,
                    "full_growth_and_hypothesis_mass_kg": props.mass_kg + extra,
                    "cp_station_m": cp,
                    "cg_station_m_all_extra_at_aft": cg,
                    "margin_cal": (cp - cg) / v.airframe["body_diameter_m"],
                }
            )
        guide.append(
            {
                "thermal_increment_kg_hypothesis": thermal,
                "increment_kg_including_rail_saving_hypothesis": increment,
                "screens": [
                    screen_launch(
                        v, dt, study_nominal_mass_kg=properties_by_depletion[0].mass_kg + increment
                    )
                    for dt in bc["numerical_timestep_s"]
                ],
            }
        )
    b = budget(v, bc["dedicated_recovery_part_ids"], bc["numerical_timestep_s"])
    record = {
        "id": c["id"],
        "record_kind": "isolated layered construction and forward root correction",
        "accepted": False,
        "flight_ready": False,
        "input_sha256": before,
        "inputs_unchanged": before == {str(p): sha(p) for p in sorted(inputs) if p.is_file()},
        "resolved_copy": str(resolved),
        "resolved_copy_sha256": sha(resolved),
        "resolved_spec_sha256": hashlib.sha256(
            v.model_dump_json(by_alias=True).encode()
        ).hexdigest(),
        "source_baseline_vehicle_id": base.id,
        "support_before": root_support_extents(base),
        "support_after": root_support_extents(v),
        "shifted_5mm_ply_fin_mass_kg": _part(ply, "fin_set").resolved_mass_kg,
        "layered_fin_mass_kg": fin.resolved_mass_kg,
        "saving_vs_5mm_20mm_kg": _part(ply, "fin_set").resolved_mass_kg - fin.resolved_mass_kg,
        "material_solids": composite,
        "root_adhesive_ledger": adhesive_ledger,
        "prior_unreconciled_record": {
            "path": str(prior_unreconciled_path),
            "sha256": sha(prior_unreconciled_path),
            "fin_set_mass_kg_unchanged": prior_unreconciled["layered_fin_mass_kg"],
            "maximum_material_solid_mass_change_kg": geometry_mass_change,
        },
        "cap_bond_mass_kg": cap_bond_mass,
        "outer_tip_seal_mass_kg_estimate": c["tip_edge_seal_mass_kg"],
        "mass_inertia_reserve_approximation": "Cap bonding and tip seal use the fin-set centroid and inertia; revisit their local distribution before integrated adoption.",
        "nominal_changed_part_rigid_intersections": collisions,
        "nominal_interface_minimum_distances": contact_checks,
        "interface_distance_scope": "Minimum distance verifies some nominal contact at each stated interface, not its complete bonded area or strength. Axial coverage and explicit solids/masses are separate. Cure, voids, free edges and flexible contact remain unqualified.",
        "nominal_intersection_threshold_mm3": 0.05,
        "interface_status": {
            "whole_axial_root_supported": root_support_extents(v)[
                "whole_foot_inside_shell_axial_extent"
            ],
            "tab_potting_modeled_and_mass_charged": True,
            "frame_to_shell_radial_gap_m": _part(v, "aft_shell").geometry["inner_radius_m"]
            - _part(v, "gimbal_frame").geometry["radius_m"],
            "finite_frame_shell_gap_bond_geometry_and_mass_included": True,
            "frame_shell_bond_strength_and_stiffness_verified": False,
            "combined_motion_tolerance_and_access_passed": False,
        },
        "cad_exports": {
            p.name: {"path": str(p), "sha256": sha(p)}
            for p in (output / "fin-layers.step", output / "assembly.step", output / "assembly.glb")
        },
        "historical_envelope": {
            "flight_record": str(flight_path),
            "sha256": sha(flight_path),
            "source_vehicle_id": base.id,
            "scenario_count": len(flight_cases),
            "max_q_scenario": envelope.get("scenario"),
            "max_q_pa": q,
            "max_speed_mps": max(x["metrics"]["max_speed_mps"] for x in flight_cases),
            "same_candidate_configuration": False,
            "applicability": "Historical envelope transfer only. Shift/mass/geometry changes require fresh affected JAX/RocketPy/uncertainty runs; no same-candidate flight validation.",
        },
        "selected_force_n": force,
        "load_basis": "Maximum of retained 40kPa/5deg screen and CN=2 at maximum q over every matching historical scenario; no design factor applied to deflection, DF3 applied once to strength demands.",
        "old_5mm_hot_deflection_scaled_to_selected_force_m": historical_static["hot_fine_mesh"][
            "max_displacement_m"
        ]
        * force_ratio,
        "old_5mm_hot_strength_scaled_to_selected_force": scaled_old_hot_components,
        "layered_panel_quadrature_levels": panels,
        "quadrature_relative_deflection_change_final_two": abs(
            panels[-1]["panel_only_tip_deflection_m"] / panels[-2]["panel_only_tip_deflection_m"]
            - 1
        ),
        "curved_foot_bond_upper_stiffness_sensitivity": feet,
        "torsion_and_flutter": torsion_targets(c, panels[-1], q, span, chord),
        "full_growth_static_with_explicit_additions": static,
        "fin_only_full_growth_static": fin_only_static,
        "mass_properties_by_depletion": [
            {
                "depletion_fraction": depletion,
                "nominal_mass_kg": props.mass_kg,
                "cg_station_m": props.cg_m,
                "full_inertia_kg_m2": props.inertia_kg_m2.tolist(),
            }
            for depletion, props in zip((0.0, 1.0), properties_by_depletion, strict=True)
        ],
        "guide_with_explicit_additions": guide,
        "mass_budget": b,
        "incremental_headroom_with_rail_saving_hypothesis_kg": b["maximum_increment_kg"]
        + cfg["package_a_rail_mass_saving_kg"],
        "historical_FEA_failures_retained": {
            "five_level_report": str(historical_panel_path),
            "five_level_report_sha256": sha(historical_panel_path),
            "five_level_final_change": historical_static["cold_convergence"][
                "stress_component_fine_vs_middle_fraction"
            ],
            "sixth_level_report": str(historical_refinement_path),
            "sixth_level_report_sha256": sha(historical_refinement_path),
            "sixth_level_convergence": json.loads(historical_refinement_path.read_text())[
                "convergence"
            ],
            "same_criteria": "All regional stress components must change <10%; low absolute stress does not waive the requirement. New beam reduction supplies no Syy/tauXY result or installed FEA pass.",
        },
        "open_critical_methods": [
            "Same-candidate flight envelope and independent reference comparison after the forward shift and complete mass package.",
            "Three-level installed layered solid/shell FEA: all directional stress components, solid root, curved foot, finite potting, frame/ring/shell/body continuity, local peel and manufactured edge geometry.",
            "Guaranteed hot compression/face-wrinkling/core/bond properties and full orthotropic laminate constants; typical tension alone cannot pass compression.",
            "Finite frame-to-shell gap bonds are explicit and mass-charged; paper through-thickness and all bond-edge peel/normal strength and frame/ring stiffness are unresolved. Rigid-cylinder foot result gives no assembled stiffness lower bound.",
            "Installed torsional stiffness/damping and applicable dynamic bending/torsion/body/TVC aeroelastic calculation. Static divergence and NACA panel sensitivities are not flutter acceptance.",
        ],
        "engineering_acceptance_passed": False,
        "sources_and_property_status": {
            "sources": c["sources"],
            "property_status": c["property_status"],
        },
    }
    path = output / "record.json"
    path.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    print(path, flush=True)
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/studies/wo03-trainer-fin-package.yaml")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("build/wo03-trainer-fin-root/pvc5-forward25-backed-reconciled"),
    )
    args = parser.parse_args()
    run(args.config, args.output)


if __name__ == "__main__":
    main()
