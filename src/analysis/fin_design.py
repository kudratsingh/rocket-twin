"""Bounded mass/stiffness trade for solid and plywood/balsa fin constructions.

The calculations are transparent beam/panel screens, not material qualification,
failure allowables, flutter prediction, or an active vehicle design update.
Derivation: EI=E*b*t^3/12 for solid sections; symmetric face-sheet EI uses the
parallel-axis theorem. A unit tip force gives virtual moment (L-x), so distributed
tip displacement is integral M(x)*(L-x)/EI(x) dx; core shear adds integral V/(kGA) dx.
The point-tip-load upper screen FL^3/(3EI) remains separate. Sources: Oxford,
Engineering Mechanics of Deformable Solids, "Virtual Work Methods: Virtual Forces"
https://academic.oup.com/book/4888/chapter/147320289 ; MIT 3.054 (2015), lectures
16-17 sandwich beam notes (face bending plus core shear),
https://ocw.mit.edu/courses/3-054-cellular-solids-structure-properties-and-applications-spring-2015/17788388b717f5b5900281db3ebf15e3_MIT3_054S15_L17_trans.pdf .
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import yaml

from src.vehicle.aero import center_of_pressure
from src.vehicle.mass import mass_properties
from src.vehicle.schema import Part, Vehicle, load_vehicle, vehicle_input_paths


@dataclass(frozen=True)
class FinConstruction:
    name: str
    category: str
    thickness_m: float
    density_kg_m3: float
    youngs_pa: float
    strength_pa: float
    skin_thickness_m: float | None = None
    core_thickness_m: float | None = None
    core_density_kg_m3: float | None = None
    core_shear_modulus_pa: float | None = None
    core_shear_strength_pa: float | None = None
    adhesive_areal_mass_kg_m2: float = 0.0
    property_status: str = "estimated transfer"


def rectangular_beam_ei(youngs_pa: float, width_m: float, thickness_m: float) -> float:
    """Bending stiffness EI for a rectangular section, SI units."""
    return youngs_pa * width_m * thickness_m**3 / 12.0


def rectangular_root_stress(moment_nm: float, width_m: float, thickness_m: float) -> float:
    """Extreme-fiber bending stress for a rectangular cantilever section."""
    return 6.0 * moment_nm / (width_m * thickness_m**2)


def cantilever_tip_deflection(force_n: float, span_m: float, ei_nm2: float) -> float:
    """Point-load-at-tip Euler-Bernoulli displacement screen."""
    return force_n * span_m**3 / (3.0 * ei_nm2)


def sandwich_ei(skin_youngs_pa: float, width_m: float, skin_m: float, core_m: float) -> float:
    """Face-sheet bending EI; core axial/bending contribution is omitted."""
    face_offset = (core_m + skin_m) / 2.0
    face_i = skin_m**3 / 12.0 + skin_m * face_offset**2
    return 2.0 * skin_youngs_pa * width_m * face_i


def sandwich_skin_stress(
    moment_nm: float, ei_nm2: float, skin_youngs_pa: float, skin_m: float, core_m: float
) -> float:
    """Outer-surface face stress from curvature of the symmetric sandwich beam."""
    outer_fiber = core_m / 2.0 + skin_m
    return skin_youngs_pa * moment_nm * outer_fiber / ei_nm2


def sandwich_core_shear_stress(force_n: float, width_m: float, core_m: float) -> float:
    """Uniform average core shear diagnostic; local peaks and load introduction omitted."""
    return force_n / (width_m * core_m)


def timoshenko_tip_deflection(
    force_n: float,
    span_m: float,
    ei_nm2: float,
    shear_modulus_pa: float,
    shear_area_m2: float,
    shear_factor: float = 5.0 / 6.0,
) -> tuple[float, float, float]:
    """Return Euler-Bernoulli, core-shear, and combined tip-load displacement."""
    bending = cantilever_tip_deflection(force_n, span_m, ei_nm2)
    shear = force_n * span_m / (shear_factor * shear_modulus_pa * shear_area_m2)
    return bending, shear, bending + shear


def distributed_tapered_tip_deflection(
    force_n: float,
    span_m: float,
    root_chord_m: float,
    tip_chord_m: float,
    ei_per_width_n_m: float,
    core_shear_modulus_pa: float | None = None,
    core_thickness_m: float | None = None,
    shear_factor: float = 5.0 / 6.0,
) -> tuple[float, float, float]:
    """Virtual-work displacement for pressure distributed over a tapered planform.

    ``EI(x) = ei_per_width * chord(x)``. Sandwich faces carry bending and the core
    carries transverse shear. The integrated load and moment resultants are exact
    for linearly tapered chord; 96-point Gauss quadrature evaluates virtual work.
    Return Euler-Bernoulli, shear, and total tip displacement in metres.
    """
    if min(force_n, span_m, root_chord_m, tip_chord_m, ei_per_width_n_m) <= 0:
        raise ValueError("Distributed-beam inputs must be positive")
    if (core_shear_modulus_pa is None) != (core_thickness_m is None):
        raise ValueError("Core shear modulus and thickness must be supplied together")
    if core_shear_modulus_pa is not None and core_shear_modulus_pa <= 0:
        raise ValueError("Core shear modulus must be positive")
    if core_thickness_m is not None and core_thickness_m <= 0:
        raise ValueError("Core thickness must be positive")
    planform_area = span_m * (root_chord_m + tip_chord_m) / 2.0
    pressure = force_n / planform_area
    taper = (tip_chord_m - root_chord_m) / span_m
    abscissa, weights = np.polynomial.legendre.leggauss(96)
    x = (abscissa + 1.0) * span_m / 2.0
    quadrature = weights * span_m / 2.0
    chord = root_chord_m + taper * x
    remaining = span_m - x
    shear_force = pressure * (chord * remaining + taper * remaining**2 / 2.0)
    moment = pressure * (chord * remaining**2 / 2.0 + taper * remaining**3 / 3.0)
    ei = ei_per_width_n_m * chord
    bending = float(np.sum(quadrature * moment * remaining / ei))
    shear = 0.0
    if core_shear_modulus_pa is not None and core_thickness_m is not None:
        shear_area = chord * core_thickness_m
        shear = float(
            np.sum(quadrature * shear_force / (shear_factor * core_shear_modulus_pa * shear_area))
        )
    return bending, shear, bending + shear


def constructions(config: dict[str, Any]) -> list[FinConstruction]:
    materials = config["materials"]
    grids = config["grids"]
    sandwich = config["sandwich"]
    plywood = materials["plywood"]
    g10 = materials["g10"]
    core = materials["balsa_core"]
    items: list[FinConstruction] = []
    for mm in grids["solid_plywood_thickness_mm"]:
        items.append(
            FinConstruction(
                name=f"solid-plywood-{mm:g}mm",
                category="solid_plywood",
                thickness_m=mm * 1e-3,
                density_kg_m3=float(plywood["density_kg_m3"]),
                youngs_pa=float(plywood["youngs_pa"]),
                strength_pa=float(plywood["weak_direction_screen_strength_pa"]),
                property_status=str(plywood["status"]),
            )
        )
    for mm in grids["solid_g10_thickness_mm"]:
        items.append(
            FinConstruction(
                name=f"solid-g10-{mm:g}mm",
                category="solid_g10",
                thickness_m=mm * 1e-3,
                density_kg_m3=float(g10["density_kg_m3"]),
                youngs_pa=float(g10["estimated_youngs_pa"]),
                strength_pa=float(g10["sample_flexural_strength_pa"]),
                property_status=str(g10["status"]),
            )
        )
    for skin_mm in grids["sandwich_skin_thickness_mm"]:
        for core_mm in grids["sandwich_core_thickness_mm"]:
            skin = skin_mm * 1e-3
            core_t = core_mm * 1e-3
            items.append(
                FinConstruction(
                    name=f"ply-balsa-skin{skin_mm:g}-core{core_mm:g}mm",
                    category="plywood_balsa_sandwich",
                    thickness_m=2.0 * skin + core_t,
                    density_kg_m3=float(plywood["density_kg_m3"]),
                    youngs_pa=float(plywood["youngs_pa"]),
                    strength_pa=float(plywood["weak_direction_screen_strength_pa"]),
                    skin_thickness_m=skin,
                    core_thickness_m=core_t,
                    core_density_kg_m3=float(core["density_kg_m3"]),
                    core_shear_modulus_pa=float(core["shear_modulus_pa"]),
                    core_shear_strength_pa=float(core["typical_shear_strength_pa"]),
                    adhesive_areal_mass_kg_m2=float(sandwich["adhesive_areal_mass_kg_m2"]),
                    property_status=(
                        str(plywood["status"])
                        + "; "
                        + str(core["status"])
                        + "; adhesive areal mass is an explicit estimate"
                    ),
                )
            )
    return items


def planform_geometry(fin: Part) -> dict[str, float]:
    g = fin.geometry
    span, root, tip, sweep = (
        float(g[k]) for k in ("span_m", "root_chord_m", "tip_chord_m", "sweep_m")
    )
    area = span * (root + tip) / 2.0
    abscissa, weights = np.polynomial.legendre.leggauss(32)
    y = (abscissa + 1.0) * span / 2.0
    chord = root + (tip - root) * y / span
    leading = sweep * y / span
    weighted_area = weights * span / 2.0 * chord
    planform_centroid_m = float(
        np.sum(weighted_area * (leading + chord / 2.0)) / np.sum(weighted_area)
    )
    cad = fin.cad.parameters if fin.cad else {}
    tab_depth_m = float(cad.get("tab_depth_mm", 0.0)) * 1e-3
    tab_length_m = float(cad.get("tab_length_mm", 0.0)) * 1e-3
    tab_offset_m = float(cad.get("tab_offset_mm", 0.0)) * 1e-3
    count = int(g["count"])
    tab_volume_m3 = tab_depth_m * float(g["thickness_m"]) * tab_length_m * count
    return {
        "span_m": span,
        "root_chord_m": root,
        "tip_chord_m": tip,
        "sweep_m": sweep,
        "area_per_fin_m2": area,
        "planform_centroid_station_m": fin.position_m + planform_centroid_m,
        "tab_volume_m3": tab_volume_m3,
        "tab_centroid_station_m": fin.position_m + tab_offset_m + tab_length_m / 2.0,
        "count": float(count),
    }


def construction_mass(
    fin: Part, construction: FinConstruction, geometry: dict[str, float]
) -> dict[str, float]:
    count = geometry["count"]
    area = geometry["area_per_fin_m2"]
    tab_volume = geometry["tab_volume_m3"]
    if construction.category == "solid_plywood" or construction.category == "solid_g10":
        planform_volume = area * construction.thickness_m * count
        tab_volume = (
            geometry["tab_volume_m3"] * construction.thickness_m / fin.geometry["thickness_m"]
        )
        planform_mass = planform_volume * construction.density_kg_m3
        tab_mass = tab_volume * construction.density_kg_m3
        adhesive_mass = 0.0
        total_volume = planform_volume + tab_volume
        centroid = (
            planform_mass * geometry["planform_centroid_station_m"]
            + tab_mass * geometry["tab_centroid_station_m"]
        ) / (planform_mass + tab_mass)
    else:
        assert construction.skin_thickness_m is not None
        assert construction.core_thickness_m is not None
        assert construction.core_density_kg_m3 is not None
        planform_skin_volume = area * count * 2.0 * construction.skin_thickness_m
        planform_core_volume = area * count * construction.core_thickness_m
        planform_mass = (
            area
            * count
            * 2.0
            * construction.skin_thickness_m
            * float(_plywood_density(construction))
            + planform_core_volume * construction.core_density_kg_m3
        )
        adhesive_mass = area * count * construction.adhesive_areal_mass_kg_m2
        tab_volume = (
            geometry["tab_volume_m3"] * construction.thickness_m / fin.geometry["thickness_m"]
        )
        tab_mass = tab_volume * float(_plywood_density(construction))
        planform_mass += adhesive_mass
        total_volume = planform_skin_volume + planform_core_volume + tab_volume
        centroid = (
            planform_mass * geometry["planform_centroid_station_m"]
            + tab_mass * geometry["tab_centroid_station_m"]
        ) / (planform_mass + tab_mass)
        planform_volume = planform_skin_volume + planform_core_volume
    total_mass = planform_mass + tab_mass
    return {
        "fin_mass_kg": total_mass,
        "fin_mass_per_fin_kg": total_mass / count,
        "current_fin_mass_kg": fin.resolved_mass_kg,
        "delta_fin_mass_kg": total_mass - fin.resolved_mass_kg,
        "fin_candidate_cg_station_m": centroid,
        "planform_volume_m3": planform_volume,
        "tab_volume_m3": tab_volume,
        "total_material_volume_m3": total_volume,
        "adhesive_mass_kg": adhesive_mass,
        "planform_mass_kg": planform_mass,
        "tab_mass_kg": tab_mass,
    }


def _plywood_density(construction: FinConstruction) -> float:
    # Sandwich construction carries the supplier-derived midpoint separately in the
    # construction density slot; solid-only models use the same field as their material.
    return construction.density_kg_m3


def panel_screen(
    fin: Part,
    construction: FinConstruction,
    q_pa: float,
    alpha_deg: float,
    design_factor: float,
    deflection_limit_m: float,
) -> dict[str, Any]:
    geometry = planform_geometry(fin)
    span = geometry["span_m"]
    root = geometry["root_chord_m"]
    tip = geometry["tip_chord_m"]
    area = geometry["area_per_fin_m2"]
    aspect_ratio = 2.0 * span**2 / area
    normal_force_slope = 2.0 * np.pi * aspect_ratio / (2.0 + np.sqrt(4.0 + aspect_ratio**2))
    force = q_pa * area * normal_force_slope * np.deg2rad(alpha_deg)
    arm = span * (root + 2.0 * tip) / (3.0 * (root + tip))
    moment = force * arm
    if construction.category == "plywood_balsa_sandwich":
        assert construction.skin_thickness_m is not None
        assert construction.core_thickness_m is not None
        assert construction.core_shear_modulus_pa is not None
        assert construction.core_shear_strength_pa is not None
        ei = sandwich_ei(
            construction.youngs_pa,
            root,
            construction.skin_thickness_m,
            construction.core_thickness_m,
        )
        ei_per_width = sandwich_ei(
            construction.youngs_pa,
            1.0,
            construction.skin_thickness_m,
            construction.core_thickness_m,
        )
        stress = sandwich_skin_stress(
            moment,
            ei,
            construction.youngs_pa,
            construction.skin_thickness_m,
            construction.core_thickness_m,
        )
        core_shear = sandwich_core_shear_stress(force, root, construction.core_thickness_m)
        bending_deflection, shear_deflection, total_deflection = timoshenko_tip_deflection(
            force,
            span,
            ei,
            construction.core_shear_modulus_pa,
            root * construction.core_thickness_m,
        )
        core_margin = construction.core_shear_strength_pa / (design_factor * core_shear) - 1.0
    else:
        ei = rectangular_beam_ei(construction.youngs_pa, root, construction.thickness_m)
        ei_per_width = rectangular_beam_ei(construction.youngs_pa, 1.0, construction.thickness_m)
        stress = rectangular_root_stress(moment, root, construction.thickness_m)
        core_shear = None
        bending_deflection = cantilever_tip_deflection(force, span, ei)
        shear_deflection = 0.0
        total_deflection = bending_deflection
        core_margin = None
    if construction.category == "plywood_balsa_sandwich":
        assert construction.core_shear_modulus_pa is not None
        assert construction.core_thickness_m is not None
        distributed_bending, distributed_shear, distributed_total = (
            distributed_tapered_tip_deflection(
                force,
                span,
                root,
                tip,
                ei_per_width,
                construction.core_shear_modulus_pa,
                construction.core_thickness_m,
            )
        )
    else:
        distributed_bending, distributed_shear, distributed_total = (
            distributed_tapered_tip_deflection(force, span, root, tip, ei_per_width)
        )
    skin_margin = construction.strength_pa / (design_factor * stress) - 1.0
    stress_ok = bool(skin_margin >= 0.0 and (core_margin is None or core_margin >= 0.0))
    deflection_ok = bool(total_deflection <= deflection_limit_m)
    distributed_deflection_ok = bool(distributed_total <= deflection_limit_m)
    failure_reasons = []
    if skin_margin < 0.0:
        failure_reasons.append("root skin/solid bending screen")
    if core_margin is not None and core_margin < 0.0:
        failure_reasons.append("core shear screen")
    if not deflection_ok:
        failure_reasons.append("tip deflection screen")
    distributed_failure_reasons = []
    if skin_margin < 0.0:
        distributed_failure_reasons.append("root skin/solid bending screen")
    if core_margin is not None and core_margin < 0.0:
        distributed_failure_reasons.append("core shear screen")
    if not distributed_deflection_ok:
        distributed_failure_reasons.append("distributed-load tip deflection diagnostic")
    return {
        "dynamic_pressure_pa": q_pa,
        "alpha_deg": alpha_deg,
        "force_per_fin_n": force,
        "root_moment_nm": moment,
        "root_skin_stress_pa": stress,
        "root_screen_margin": skin_margin,
        "core_shear_stress_pa": core_shear,
        "core_shear_screen_margin": core_margin,
        "ei_n_m2": ei,
        "tip_bending_deflection_m": bending_deflection,
        "tip_core_shear_deflection_m": shear_deflection,
        "tip_total_deflection_m": total_deflection,
        "tip_load_upper_deflection_m": total_deflection,
        "deflection_limit_m": deflection_limit_m,
        "deflection_screen_margin_m": deflection_limit_m - total_deflection,
        "screen_feasible": stress_ok and deflection_ok,
        "screen_failure_reasons": failure_reasons,
        "screen_status_basis": "conservative tip-load upper displacement plus DF3 stress screens",
        "screen_status": (
            "within modeled panel screen"
            if stress_ok and deflection_ok
            else "outside at least one modeled panel screen"
        ),
        "distributed_tip_bending_deflection_m": distributed_bending,
        "distributed_tip_core_shear_deflection_m": distributed_shear,
        "distributed_tip_total_deflection_m": distributed_total,
        "distributed_deflection_screen_margin_m": deflection_limit_m - distributed_total,
        "distributed_load_screen_feasible": stress_ok and distributed_deflection_ok,
        "distributed_load_screen_failure_reasons": distributed_failure_reasons,
        "distributed_load_screen_status": (
            "within distributed-load diagnostic plus DF3 stress screens"
            if stress_ok and distributed_deflection_ok
            else "outside distributed-load diagnostic or DF3 stress screen"
        ),
        "criteria": "Root skin/solid bending and core shear use DF; deflection compares to declared screen limit. No orthotropic failure criterion.",
        "unresolved": [
            "Flutter and panel torsion",
            "Root tab, bond, peel and local load introduction",
            "Plywood skin wrinkling and core crushing",
            "Temperature-conditioned material properties and fatigue",
        ],
    }


def static_overlay(
    vehicle: Vehicle,
    candidate_mass_kg: float,
    candidate_cg_station_m: float | None,
    growth_kg: float,
    replace_fin: bool = True,
) -> list[dict[str, Any]]:
    cp = center_of_pressure(vehicle)
    body_d = float(vehicle.airframe["body_diameter_m"])
    fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
    applicable = fin is not None and replace_fin
    rows = []
    for burn_fraction in (0.0, 1.0):
        baseline = mass_properties(vehicle, burn_fraction)
        if applicable:
            assert fin is not None and candidate_cg_station_m is not None
            mass = baseline.mass_kg - fin.resolved_mass_kg + candidate_mass_kg
            moment = baseline.mass_kg * baseline.cg_m - fin.resolved_mass_kg * fin.cg_station_m
            moment += candidate_mass_kg * candidate_cg_station_m
            cg = moment / mass
        else:
            mass, cg = baseline.mass_kg, baseline.cg_m
        growth_mass = mass + growth_kg
        growth_cg = (mass * cg + growth_kg * vehicle.airframe["length_m"]) / growth_mass
        rows.append(
            {
                "burn_fraction": burn_fraction,
                "fin_trade_applicable": applicable,
                "cp_m": cp,
                "baseline_mass_kg": baseline.mass_kg,
                "baseline_cg_m": baseline.cg_m,
                "baseline_static_margin_cal": (cp - baseline.cg_m) / body_d,
                "candidate_mass_kg": mass,
                "candidate_cg_m": cg,
                "candidate_static_margin_cal": (cp - cg) / body_d,
                "growth_allowance_kg": growth_kg,
                "growth_mass_kg": growth_mass,
                "growth_cg_m": growth_cg,
                "growth_static_margin_cal": (cp - growth_cg) / body_d,
                "growth_station_m": vehicle.airframe["length_m"],
            }
        )
    return rows


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_trade(config_path: Path, project_root: Path) -> dict[str, Any]:
    config = yaml.safe_load(config_path.read_text())
    designs = constructions(config)
    modes: list[tuple[str, Path, Vehicle]] = []
    for item in config["vehicles"]:
        vehicle_path = project_root / item["path"]
        modes.append((str(item["id"]), vehicle_path, load_vehicle(vehicle_path)))
    fin_modes = [
        (mode_id, vehicle)
        for mode_id, _, vehicle in modes
        if any(part.type == "fin_set" for part in vehicle.parts)
    ]
    if not fin_modes:
        raise ValueError("At least one finned mode is required for this construction trade")
    geometry_keys = ("span_m", "root_chord_m", "tip_chord_m", "sweep_m", "count")

    def geometry_signature(fin: Part) -> tuple[float, ...]:
        tab = fin.cad.parameters if fin.cad else {}
        return tuple(float(fin.geometry[key]) for key in geometry_keys) + (
            float(fin.position_m),
            float(fin.geometry["radius_m"]),
            float(tab.get("tab_depth_mm", 0.0)),
            float(tab.get("tab_length_mm", 0.0)),
            float(tab.get("tab_offset_mm", 0.0)),
        )

    geometry_groups: list[tuple[str, tuple[float, ...], Part]] = []
    for mode_id, vehicle in fin_modes:
        fin = next(part for part in vehicle.parts if part.type == "fin_set")
        signature = geometry_signature(fin)
        if not any(group[1] == signature for group in geometry_groups):
            geometry_groups.append((mode_id, signature, fin))

    loads = config["loads"]
    design_factor = float(loads["design_factor"])
    deflection_limit = float(loads["deflection_limit_m"])
    growth = float(config["mass_static"]["growth_allowance_kg"])
    architecture_rows: list[dict[str, Any]] = []
    load_rows: list[dict[str, Any]] = []
    static_rows: list[dict[str, Any]] = []

    for group_id, signature, reference_fin in geometry_groups:
        for design in designs:
            architecture_name = f"{group_id}-{design.name}"
            geometry = planform_geometry(reference_fin)
            mass = construction_mass(reference_fin, design, geometry)
            for load in loads["dynamic_pressure_pa"]:
                load_rows.append(
                    {
                        "architecture": architecture_name,
                        "geometry_reference_mode": group_id,
                        "category": design.category,
                        "material_property_status": design.property_status,
                        **geometry,
                        **mass,
                        **panel_screen(
                            reference_fin,
                            design,
                            float(load["value"]),
                            float(loads["alpha_deg"]),
                            design_factor,
                            deflection_limit,
                        ),
                        "load_case_id": load["id"],
                        "load_context": load["context"],
                        "design_factor": design_factor,
                    }
                )
            architecture_loads = [
                row for row in load_rows if row["architecture"] == architecture_name
            ]
            within_upper = sum(bool(row["screen_feasible"]) for row in architecture_loads)
            lower_case_pass = next(
                (
                    row["screen_feasible"]
                    for row in architecture_loads
                    if row["dynamic_pressure_pa"] == 25000.0
                ),
                False,
            )
            upper_status = (
                "within both modeled load screens"
                if within_upper == 2
                else (
                    "within 25 kPa screen only"
                    if within_upper == 1 and lower_case_pass
                    else (
                        "outside both modeled load screens"
                        if within_upper == 0
                        else "within 40 kPa screen only"
                    )
                )
            )
            architecture_rows.append(
                {
                    "architecture": architecture_name,
                    "geometry_reference_mode": group_id,
                    "category": design.category,
                    **geometry,
                    **mass,
                    "ei_n_m2_per_fin": architecture_loads[0]["ei_n_m2"],
                    "ei_per_fin_mass_n_m2_kg": architecture_loads[0]["ei_n_m2"]
                    / mass["fin_mass_per_fin_kg"],
                    "screen_cases_within_bounds": within_upper,
                    "screen_feasibility_rank": (
                        1 if within_upper == 2 else 2 if within_upper == 1 else 3
                    ),
                    "screen_feasibility": upper_status,
                    "material_property_status": design.property_status,
                }
            )
            for mode_id, vehicle_path, vehicle in modes:
                mode_fin = next((part for part in vehicle.parts if part.type == "fin_set"), None)
                is_applicable = mode_fin is not None and geometry_signature(mode_fin) == signature
                overlay = static_overlay(
                    vehicle,
                    mass["fin_mass_kg"] if is_applicable else 0.0,
                    mass["fin_candidate_cg_station_m"] if is_applicable else None,
                    growth,
                    replace_fin=is_applicable,
                )
                if mode_fin is None:
                    applicability = "not applicable: finless mode"
                elif is_applicable:
                    applicability = "fin construction overlay; matching preserved planform"
                else:
                    applicability = "not applicable: different preserved planform"
                for sample in overlay:
                    static_rows.append(
                        {
                            "mode": mode_id,
                            "vehicle_id": vehicle.id,
                            "architecture": architecture_name,
                            "geometry_reference_mode": group_id,
                            "configuration_path": str(vehicle_path.relative_to(project_root)),
                            "configuration_sha256": sha256(vehicle_path),
                            "applicability": applicability,
                            **mass,
                            **sample,
                        }
                    )

    trade_rankings: list[dict[str, Any]] = []
    load_ids = sorted({str(row["load_case_id"]) for row in load_rows})
    for mode_id, _ in fin_modes:
        for load_id in load_ids:
            candidates: list[dict[str, Any]] = []
            for load_row in load_rows:
                if load_row["load_case_id"] != load_id:
                    continue
                matching_static = [
                    row
                    for row in static_rows
                    if row["architecture"] == load_row["architecture"]
                    and row["mode"] == mode_id
                    and row["fin_trade_applicable"]
                ]
                if not matching_static:
                    continue
                stress_margins = [float(load_row["root_screen_margin"])]
                core_margin = load_row["core_shear_screen_margin"]
                if core_margin is not None:
                    stress_margins.append(float(core_margin))
                candidates.append(
                    {
                        "mode": mode_id,
                        "load_case_id": load_id,
                        "architecture": load_row["architecture"],
                        "distributed_tip_deflection_m": load_row[
                            "distributed_tip_total_deflection_m"
                        ],
                        "tip_load_upper_deflection_m": load_row["tip_load_upper_deflection_m"],
                        "minimum_df3_stress_margin": min(stress_margins),
                        "worst_50g_aft_growth_static_margin_cal": min(
                            float(row["growth_static_margin_cal"]) for row in matching_static
                        ),
                        "upper_tip_load_screen_feasible": load_row["screen_feasible"],
                        "distributed_screen_feasible": load_row["distributed_load_screen_feasible"],
                    }
                )
            if not candidates:
                continue
            rank_metrics = (
                ("distributed_deflection_rank", "distributed_tip_deflection_m", False),
                ("df3_stress_rank", "minimum_df3_stress_margin", True),
                ("static_margin_rank", "worst_50g_aft_growth_static_margin_cal", True),
            )
            for rank_key, value_key, higher_is_better in rank_metrics:
                order = sorted(
                    range(len(candidates)),
                    key=lambda index: (
                        (
                            -float(candidates[index][value_key])
                            if higher_is_better
                            else float(candidates[index][value_key])
                        ),
                        str(candidates[index]["architecture"]),
                    ),
                )
                for rank, index in enumerate(order, 1):
                    candidates[index][rank_key] = rank
            for candidate in candidates:
                candidate["combined_ordinal_rank_score"] = sum(
                    int(candidate[key])
                    for key in (
                        "distributed_deflection_rank",
                        "df3_stress_rank",
                        "static_margin_rank",
                    )
                )
                candidate["ranking_basis"] = (
                    "Unweighted sum of ordinal ranks: lower distributed deflection, higher DF3 stress "
                    "margin, higher worst 50 g aft-growth static margin. The conservative tip-load "
                    "screen is reported but not filtered."
                )
            candidates.sort(
                key=lambda row: (
                    int(row["combined_ordinal_rank_score"]),
                    str(row["architecture"]),
                )
            )
            for rank, candidate in enumerate(candidates, 1):
                trade_rankings.append({**candidate, "trade_rank": rank, "top_three": rank <= 3})

    source_identities = {
        mode_id: {
            "vehicle_id": vehicle.id,
            "path": str(vehicle_path.relative_to(project_root)),
            "sha256": sha256(vehicle_path),
            "input_sha256": {
                str(input_path.relative_to(project_root)): sha256(input_path)
                for input_path in vehicle_input_paths(vehicle_path)
            },
            "resolved_spec_sha256": hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
        }
        for mode_id, vehicle_path, vehicle in modes
    }
    material_inputs = {
        path: sha256(project_root / path)
        for path in (
            config["source_notes"]["evidence_file"],
            config["source_notes"]["engineering_inputs"],
        )
    }
    reference_config = config.get("reference_2d_screen", {})
    reference_report_path = project_root / reference_config.get("report_path", "")
    reference_comparison: dict[str, Any] = {"status": "reference file not present"}
    if reference_report_path.is_file():
        folder = reference_report_path.parent
        report = yaml.safe_load(reference_report_path.read_text())
        g80_vehicle = next(vehicle for mode_id, _, vehicle in modes if mode_id == "G80-performance")
        g80_fin = next(part for part in g80_vehicle.parts if part.type == "fin_set")
        if g80_fin.cad_mass is None:
            raise ValueError("G80 fin requires resolved CAD mass for reference identity checking")
        raw_mesh_hash = sha256(folder / "analysis-mesh.json")
        deck_hash = sha256(folder / "case.inp")
        force_row = next(
            row
            for row in load_rows
            if row["architecture"]
            == f"G80-performance-{reference_config['comparison_architecture']}"
            and row["load_case_id"] == reference_config["comparison_load_case"]
        )
        checks = {
            "part_identity_matches": report.get("part_id") == g80_fin.id
            and report.get("part_shape_sha256") == g80_fin.cad_mass.shape_sha256,
            "raw_mesh_hash_matches_report": report.get("mesh_sha256") == raw_mesh_hash,
            "input_deck_hash_matches_report": report.get("input_sha256") == deck_hash,
            "applied_force_matches_screen": bool(
                np.isclose(
                    float(report.get("force_n", float("nan"))),
                    float(force_row["force_per_fin_n"]),
                    rtol=1e-7,
                )
            ),
            "youngs_modulus_matches_screen": bool(
                np.isclose(
                    float(report.get("youngs_pa", float("nan"))),
                    constructions(config)[0].youngs_pa,
                    rtol=1e-12,
                )
            ),
        }
        if all(checks.values()) and report.get("solver_executed") is True:
            fea_displacement = float(report["max_displacement_m"])
            distributed_displacement = float(force_row["distributed_tip_total_deflection_m"])
            reference_comparison = {
                "status": "identity and load checks match; one archived numerical comparison",
                "report_path": str(reference_report_path.relative_to(project_root)),
                "report_sha256": sha256(reference_report_path),
                "case_input_sha256": deck_hash,
                "analysis_mesh_raw_sha256": raw_mesh_hash,
                "part_id": report["part_id"],
                "part_shape_sha256": report["part_shape_sha256"],
                "force_n": float(report["force_n"]),
                "youngs_pa": float(report["youngs_pa"]),
                "fea_density_kg_m3": float(report["density_kg_m3"]),
                "study_plywood_density_kg_m3": float(
                    config["materials"]["plywood"]["density_kg_m3"]
                ),
                "fea_max_displacement_m": fea_displacement,
                "distributed_beam_displacement_m": distributed_displacement,
                "relative_difference_model_minus_fea": (
                    distributed_displacement / fea_displacement - 1.0
                ),
                "checks": checks,
                "interpretation": (
                    "Single static reference comparison, not physical validation or calibration. "
                    "For linear static displacement, density does not enter the response at fixed E, "
                    "geometry and force; density changes candidate mass/CG and modal inertia/frequencies."
                ),
            }
        else:
            reference_comparison = {
                "status": "reference identity or input check failed; no displacement comparison used",
                "report_path": str(reference_report_path.relative_to(project_root)),
                "report_sha256": sha256(reference_report_path),
                "checks": checks,
            }
    return {
        "config": config,
        "config_sha256": sha256(config_path),
        "source_identities": source_identities,
        "material_input_sha256": material_inputs,
        "architecture_rows": architecture_rows,
        "load_rows": load_rows,
        "static_rows": static_rows,
        "trade_rankings": trade_rankings,
        "reference_2d_comparison": reference_comparison,
        "limitations": config["limitations"],
    }
