"""Preliminary fin-root attachment and installed-flutter sensitivity equations.

These calculations contain idealized proposed-interface screens, not a bond
qualification. The rail bending quantities use an unverified moment-routing
surrogate and are not established installed-capacity bounds. Root reactions use
the rectangular-panel resultant and a single
force couple across the two side gussets. The kraft shell-only bearing case
intentionally omits backing by G11 rails/rings; actual load sharing requires the
assembled geometry and joint analysis.

References: elementary beam resultants (M=F L/2 for a uniform distributed
cantilever load; sigma=M/S); adhesive average shear F/A and spring stiffness
G A/t; NASA TN 4197, Martin, Eq. 18 for a preliminary cantilever-fin flutter
method. Root-flexibility/flutter scaling is only a static bending-compliance
sensitivity and is not an aeroelastic solution.
"""

from __future__ import annotations

import math
from typing import Any


def normal_force_coefficient_per_radian(
    span_m: float, root_chord_m: float, tip_chord_m: float
) -> float:
    """Low-angle finite-wing normal-force slope used for a panel load screen."""
    area = span_m * (root_chord_m + tip_chord_m) / 2
    if min(area, span_m) <= 0:
        raise ValueError("Fin planform dimensions must be positive")
    aspect_ratio = 2 * span_m**2 / area
    return 2 * math.pi * aspect_ratio / (2 + math.sqrt(4 + aspect_ratio**2))


def average_shear_stress_pa(force_n: float, bonded_area_mm2: float) -> float:
    if force_n < 0 or bonded_area_mm2 <= 0:
        raise ValueError("Force must be nonnegative and bonded area positive")
    return force_n / (bonded_area_mm2 * 1e-6)


def average_bearing_stress_pa(force_n: float, contact_area_mm2: float) -> float:
    return average_shear_stress_pa(force_n, contact_area_mm2)


def design_margin(allowable_pa: float, stress_pa: float, design_factor: float) -> float | None:
    if min(allowable_pa, design_factor) <= 0 or stress_pa < 0:
        raise ValueError("Allowable and design factor must be positive; stress nonnegative")
    if stress_pa == 0:
        return None
    return allowable_pa / (design_factor * stress_pa) - 1


def gusset_pair_rotational_stiffness_nm_rad(
    gusset_face_area_mm2: float,
    gusset_spacing_mm: float,
    bond_shear_modulus_pa: float,
    bondline_thickness_mm: float,
) -> float:
    """Ideal two-face bond spring: sum(G*A/t*r^2), r=spacing/2."""
    if (
        min(gusset_face_area_mm2, gusset_spacing_mm, bond_shear_modulus_pa, bondline_thickness_mm)
        <= 0
    ):
        raise ValueError("Gusset, bond, and spacing values must be positive")
    area = gusset_face_area_mm2 * 1e-6
    radius = gusset_spacing_mm * 0.5e-3
    thickness = bondline_thickness_mm * 1e-3
    one_face_shear_stiffness = bond_shear_modulus_pa * area / thickness
    return 2 * one_face_shear_stiffness * radius**2


def root_flexibility_flutter_sensitivity(
    free_root_flutter_speed_mps: float,
    span_m: float,
    effective_panel_ei_nm2: float,
    root_rotational_stiffness_nm_rad: float,
) -> dict[str, float | str | bool]:
    """Bending-only static-compliance scaling for a finite rotational spring.

    For a constant-EI cantilever, Cbeam=L^3/(3EI); root spring compliance is
    L^2/Ktheta. The square-root ratio is a modal-frequency/flutter sensitivity,
    not a replacement flutter calculation and it excludes torsion/control coupling.
    """
    if (
        min(
            free_root_flutter_speed_mps,
            span_m,
            effective_panel_ei_nm2,
            root_rotational_stiffness_nm_rad,
        )
        <= 0
    ):
        raise ValueError("Flutter sensitivity inputs must be positive")
    compliance_ratio = 1 / (
        1 + 3 * effective_panel_ei_nm2 / (root_rotational_stiffness_nm_rad * span_m)
    )
    frequency_ratio = math.sqrt(compliance_ratio)
    return {
        "free_root_flutter_speed_mps": free_root_flutter_speed_mps,
        "bending_compliance_factor": compliance_ratio,
        "frequency_ratio": frequency_ratio,
        "flexible_root_flutter_speed_sensitivity_mps": free_root_flutter_speed_mps
        * frequency_ratio,
        "status": "sensitivity-only; no flutter pass",
    }


def fin_flutter_domain_assessment(
    *,
    span_m: float,
    sweep_m: float,
    root_chord_m: float,
    tip_chord_m: float,
    base_fin_thickness_m: float,
    root_gusset_thickness_varies: bool,
    root_attachment_stiffness_verified: bool,
    flight_max_q_available: bool,
) -> dict[str, Any]:
    """Check NACA fin-screen geometry and installed root-compliance caveats."""
    rectangular_unswept = abs(sweep_m) <= 1e-9 and abs(root_chord_m - tip_chord_m) <= 1e-9
    base_plate_domain = rectangular_unswept and base_fin_thickness_m > 0
    aspect_ratio = (
        span_m / ((root_chord_m + tip_chord_m) / 2)
        if min(span_m, root_chord_m, tip_chord_m) > 0
        else None
    )
    return {
        "candidate_source_method": "NACA TN 4197 (Martin, 1958), Eq. 18 cantilever fin bending-torsion screen",
        "reference_url": "https://ntrs.nasa.gov/api/citations/19930085030/downloads/19930085030.pdf",
        "calculation_only": True,
        "source_applicability": "conditional empirical panel screen; requires geometry matching the source assumptions, a defensible installed stiffness model, and a current vehicle speed/q bound",
        "speed_bound_source": "not supplied to this geometry-only assessment; attach fresh flight-record metrics before comparing a screen speed",
        "unswept_constant_chord_geometry": rectangular_unswept,
        "base_plate_constant_thickness_ratio_domain": base_plate_domain,
        "localized_root_gusset_thickness_variation": root_gusset_thickness_varies,
        "one_panel_aspect_ratio_span_over_midchord": aspect_ratio,
        "geometric_domain_status": (
            "base plate matches constant-chord/constant-thickness-ratio geometry; root stiffness still requires installed-joint correction"
            if base_plate_domain and root_gusset_thickness_varies
            else (
                "matches preliminary panel geometry"
                if base_plate_domain
                else "outside or incomplete geometric match"
            )
        ),
        "aspect_ratio_domain_note": "This one-panel aspect ratio is low; Martin/NACA TN 4197 notes its underlying bending-torsion relation is stretched when extended to low-aspect-ratio wings. It remains an empirical preliminary screen, with no chart-boundary pass inference.",
        "root_attachment_stiffness_verified": root_attachment_stiffness_verified,
        "current_flight_max_q_available": flight_max_q_available,
        "quantitative_flutter_acceptance": "open",
        "limitations": [
            "The Eq. 18 screen is not an installed root-joint or full-airframe aeroelastic solution.",
            "Actual fin-to-gusset, fin/tab-to-G11 frame, ring and frame-to-body load transfer needs interface modelling and joint evidence.",
            "Do not compare with a historical generic velocity ceiling; bind any velocity comparison to a fresh flight-record speed bound for this same configuration.",
            "Use current reconciled maximum-q flight cases and hot/uncertain orthotropic properties; do not substitute an old generic speed ceiling.",
            "The 12 mm root reinforcement changes local stiffness but does not change the base plate thickness ratio at the three-quarter-span station; include measured/derived installed root stiffness rather than calling the whole fin uniform.",
            "Torsional attachment stiffness, damping, local panel modes, body bending and TVC/guidance/control coupling remain open.",
        ],
    }


def analyze_fin_attachment(
    *,
    configuration_id: str,
    dynamic_pressure_pa: float,
    normal_coefficient: float,
    span_m: float,
    root_chord_m: float,
    tip_chord_m: float,
    gusset_span_mm: float,
    tab_engagement_length_mm: float,
    tab_radial_width_mm: float,
    body_wall_thickness_mm: float,
    frame_rail_width_mm: float,
    frame_rail_radial_depth_mm: float,
    rails_sharing_one_fin: int,
    bond_shear_allowable_pa: float = 2e6,
    wood_bound_pa: float = 10e6,
    kraft_bound_pa: float = 2e6,
    g11_bound_pa: float = 50e6,
    frame_material_name: str = "G11",
    frame_strength_bound_pa: float | None = None,
    design_factor: float = 3.0,
    temperature_strength_fraction: float = 1.0,
    gusset_base_thickness_mm: float = 3.0,
    hot_bond_allowable_pa: float = 1e6,
    tab_slot_width_mm: float | None = None,
    ring_count: int | None = None,
    ring_thickness_mm: float | None = None,
    bond_shear_modulus_pa: float | None = None,
    bondline_thickness_mm: float | None = None,
    actual_bond_area_mm2: float | None = None,
    unsupported_shell_span_mm: float | None = None,
) -> dict[str, Any]:
    """Produce provisional per-fin interface demands with uncertainty explicit.

    The gusset triangular-face area is a nominal geometric estimate. An optional
    measured/derived bonded area can replace it. `rails_sharing_one_fin` defaults
    to one independent longitudinal rail; greater load sharing must be justified.
    """
    positive = [
        dynamic_pressure_pa,
        span_m,
        root_chord_m,
        tip_chord_m,
        gusset_span_mm,
        tab_engagement_length_mm,
        tab_radial_width_mm,
        body_wall_thickness_mm,
        frame_rail_width_mm,
        frame_rail_radial_depth_mm,
        design_factor,
        temperature_strength_fraction,
        gusset_base_thickness_mm,
    ]
    if min(positive) <= 0 or rails_sharing_one_fin < 1:
        raise ValueError("Attachment screen geometry/load/allowable inputs must be positive")
    area_planform = span_m * (root_chord_m + tip_chord_m) / 2
    if normal_coefficient < 0:
        raise ValueError("Normal coefficient must be nonnegative")
    force_n = dynamic_pressure_pa * area_planform * normal_coefficient
    root_moment_nm = force_n * span_m / 2
    lever_m = gusset_span_mm * 1e-3
    couple_force_n = root_moment_nm / lever_m
    triangular_face_area_mm2 = 0.5 * gusset_span_mm * root_chord_m * 1000
    gusset_base_area_mm2 = gusset_base_thickness_mm * root_chord_m * 1000
    bond_area_one_face = actual_bond_area_mm2 or triangular_face_area_mm2
    direct_gusset_shear = average_shear_stress_pa(force_n, 2 * bond_area_one_face)
    couple_peel_per_face = average_bearing_stress_pa(couple_force_n, bond_area_one_face)
    bond_allowable = (
        hot_bond_allowable_pa if temperature_strength_fraction < 1 else bond_shear_allowable_pa
    )
    gusset_shear_margin = design_margin(bond_allowable, direct_gusset_shear, design_factor)
    gusset_base_stress = average_bearing_stress_pa(couple_force_n, gusset_base_area_mm2)
    wood_allowable = wood_bound_pa * temperature_strength_fraction
    gusset_base_margin = design_margin(wood_allowable, gusset_base_stress, design_factor)

    tab_bond_area_mm2 = tab_engagement_length_mm * tab_radial_width_mm
    if tab_slot_width_mm is None:
        slot_fit: dict[str, Any] = {
            "status": "unavailable",
            "reason": "Slot width is not supplied.",
        }
    else:
        if tab_slot_width_mm <= 0:
            raise ValueError("Tab slot width must be positive")
        diametral_gap = tab_slot_width_mm - tab_radial_width_mm
        slot_fit = {
            "status": "nominal-clearance" if diametral_gap >= 0 else "nominal-interference",
            "slot_width_mm": tab_slot_width_mm,
            "tab_width_mm": tab_radial_width_mm,
            "total_width_clearance_mm": diametral_gap,
            "nominal_per_side_clearance_mm_if_centered": diametral_gap / 2,
            "limitation": "Nominal dimensional subtraction only; tolerance, body curvature, adhesive fill, wear and actual centering are not verified.",
        }
    tab_bond_shear = average_shear_stress_pa(force_n, tab_bond_area_mm2)
    tab_bond_peel_eq = root_moment_nm * 1000 / (tab_bond_area_mm2 * tab_radial_width_mm / 2) * 1e6
    tab_bond_margin = design_margin(bond_allowable, tab_bond_shear, design_factor)

    shell_bearing_area_mm2 = body_wall_thickness_mm * tab_engagement_length_mm
    shell_bearing = average_bearing_stress_pa(force_n, shell_bearing_area_mm2)
    kraft_allowable = kraft_bound_pa * temperature_strength_fraction
    shell_bearing_margin = design_margin(kraft_allowable, shell_bearing, design_factor)

    rail_area_mm2 = frame_rail_width_mm * frame_rail_radial_depth_mm
    # Fin-normal pressure acts in CAD Y (tangential); bending is therefore
    # about the rail's radial X axis.  For a rectangle, I_X=d_radial*w_tan^3/12.
    rail_normal_section_modulus_mm3 = frame_rail_radial_depth_mm * frame_rail_width_mm**2 / 6
    # Keep the orthogonal bending axis as a separate uncertainty case.
    rail_crossload_section_modulus_mm3 = frame_rail_width_mm * frame_rail_radial_depth_mm**2 / 6
    rail_shear = force_n / (rails_sharing_one_fin * rail_area_mm2 * 1e-6)
    rail_normal_bending = (
        root_moment_nm * 1000 / (rails_sharing_one_fin * rail_normal_section_modulus_mm3) * 1e6
    )
    rail_crossload_bending = (
        root_moment_nm * 1000 / (rails_sharing_one_fin * rail_crossload_section_modulus_mm3) * 1e6
    )
    frame_bound = g11_bound_pa if frame_strength_bound_pa is None else frame_strength_bound_pa
    frame_allowable = frame_bound * temperature_strength_fraction
    rail_shear_margin = design_margin(frame_allowable, rail_shear, design_factor)
    rail_normal_bending_margin = design_margin(frame_allowable, rail_normal_bending, design_factor)
    rail_crossload_bending_margin = design_margin(
        frame_allowable, rail_crossload_bending, design_factor
    )

    ring_bearing: dict[str, Any]
    if ring_count is None or ring_thickness_mm is None:
        ring_bearing = {
            "status": "unavailable",
            "reason": "Ring count or axial bearing thickness not supplied; ring load sharing and bearing width need actual CAD contact geometry.",
        }
    else:
        if ring_count < 1 or ring_thickness_mm <= 0:
            raise ValueError("Ring count and thickness must be positive")
        # Contact width is conservatively restricted to the provided rail width.
        area = ring_count * ring_thickness_mm * frame_rail_width_mm
        stress = average_bearing_stress_pa(force_n, area)
        ring_bearing = {
            "status": "sensitivity-only",
            "assumed_total_contact_area_mm2": area,
            "force_assumed_equal_per_ring_n": force_n / ring_count,
            "average_bearing_stress_pa": stress,
            "allowable_pa": frame_allowable,
            "design_margin": design_margin(frame_allowable, stress, design_factor),
            "limitation": "Uniform bearing across equal ring contacts; ring curvature, slot notches, local ring bending and actual load sharing omitted.",
        }

    rotational: dict[str, Any]
    if bond_shear_modulus_pa is None or bondline_thickness_mm is None:
        rotational = {
            "status": "unavailable",
            "reason": "Bond shear modulus and cured bondline thickness are needed for rotational spring stiffness.",
        }
    else:
        stiffness = gusset_pair_rotational_stiffness_nm_rad(
            bond_area_one_face,
            gusset_span_mm,
            bond_shear_modulus_pa,
            bondline_thickness_mm,
        )
        rotation = root_moment_nm / stiffness
        rotational = {
            "status": "ideal-bond-spring sensitivity; excludes substrate and frame flexibility",
            "bond_shear_modulus_pa": bond_shear_modulus_pa,
            "bondline_thickness_mm": bondline_thickness_mm,
            "gusset_pair_rotational_stiffness_nm_rad": stiffness,
            "root_rotation_rad": rotation,
            "tip_motion_from_root_rotation_mm": rotation * span_m * 1000,
            "required_verification": "Measure/derive adhesive and substrate compliance; root tab, body shell and support-ring flexibility can dominate this ideal spring.",
        }

    shell_strip: dict[str, Any]
    if unsupported_shell_span_mm is None:
        shell_strip = {
            "status": "unavailable",
            "reason": "Unsupported body-shell span between actual backing rings/rails is required for local kraft wall bending sensitivity.",
        }
    else:
        if unsupported_shell_span_mm <= 0:
            raise ValueError("Unsupported shell span must be positive")
        # Simply supported strip, center-load upper sensitivity over chord length.
        strip_moment_nmm = force_n * unsupported_shell_span_mm / 4
        z_mm3 = tab_engagement_length_mm * body_wall_thickness_mm**2 / 6
        stress = strip_moment_nmm / z_mm3 * 1e6
        shell_strip = {
            "status": "simply-supported strip sensitivity",
            "unsupported_span_mm": unsupported_shell_span_mm,
            "moment_nmm": strip_moment_nmm,
            "section_modulus_mm3": z_mm3,
            "bending_stress_pa": stress,
            "allowable_after_DF_pa": kraft_allowable / design_factor,
            "margin": design_margin(kraft_allowable, stress, design_factor),
            "limitation": "Single-strip idealization; curved-shell membrane action and G11 ring/rail backing are omitted, so this is a weak unsupported-shell bound, not the assembled frame result.",
        }

    return {
        "configuration_id": configuration_id,
        "loads_per_fin": {
            "dynamic_pressure_pa": dynamic_pressure_pa,
            "normal_coefficient": normal_coefficient,
            "planform_area_m2": area_planform,
            "normal_force_n": force_n,
            "root_moment_nm_uniform_load_arm_span_over_2": root_moment_nm,
            "gusset_couple_force_n_m_over_spacing": couple_force_n,
            "load_basis": "Uniform pressure resultant applied over a rectangular/trapezoidal single-fin planform; root moment arm approximated as span/2. Inputs must come from the current load case, not a historical speed bound.",
        },
        "materials_and_criteria": {
            "plywood_gusset_strength_bound_pa": wood_bound_pa,
            "kraft_body_strength_bound_pa": kraft_bound_pa,
            "frame_strength_bound_pa": frame_bound,
            "frame_material_name": frame_material_name,
            "wood_bond_shear_allowable_pa": bond_shear_allowable_pa,
            "hot_bond_allowable_pa": hot_bond_allowable_pa,
            "gusset_base_thickness_mm": gusset_base_thickness_mm,
            "temperature_strength_fraction": temperature_strength_fraction,
            "design_factor": design_factor,
            "status": "provisional estimated bounds; lot, grain, cure, temperature and test evidence absent",
        },
        "gusset_bonds": {
            "nominal_triangular_face_area_per_side_mm2": triangular_face_area_mm2,
            "used_area_per_side_mm2": bond_area_one_face,
            "direct_shear_stress_pa_equal_share_two_faces": direct_gusset_shear,
            "direct_shear_design_margin": gusset_shear_margin,
            "moment_couple_force_per_face_n": couple_force_n,
            "average_peel_equivalent_stress_pa": couple_peel_per_face,
            "peel_margin": None,
            "peel_status": "unavailable: supplied bond bound is shear-only and peel allowable/edge geometry are not qualified",
            "bond_margin_status": (
                "screen-pass"
                if gusset_shear_margin is not None and gusset_shear_margin >= 0
                else "screen-fail"
            ),
            "gusset_base_area_per_side_mm2": gusset_base_area_mm2,
            "average_gusset_base_axial_stress_pa_from_couple": gusset_base_stress,
            "wood_strength_bound_pa": wood_allowable,
            "gusset_base_material_margin_DF3": gusset_base_margin,
            "gusset_base_material_status": (
                "screen-pass"
                if gusset_base_margin is not None and gusset_base_margin >= 0
                else "screen-fail"
            ),
        },
        "tab_and_body": {
            "nominal_tab_bond_area_mm2": tab_bond_area_mm2,
            "tab_slot_nominal_fit": slot_fit,
            "tab_direct_shear_stress_pa": tab_bond_shear,
            "tab_direct_shear_margin": tab_bond_margin,
            "tab_moment_equivalent_peel_stress_pa": tab_bond_peel_eq,
            "tab_peel_status": "unavailable: geometry-specific adhesive peel allowable and transfer width are not known",
            "kraft_shell_bearing_area_mm2": shell_bearing_area_mm2,
            "kraft_shell_bearing_stress_pa_no_G11_load_share": shell_bearing,
            "kraft_shell_bearing_margin_no_G11_load_share": shell_bearing_margin,
            "kraft_shell_bearing_status": (
                "screen-pass"
                if shell_bearing_margin is not None and shell_bearing_margin >= 0
                else "screen-fail"
            ),
            "kraft_shell_interpretation": "One 0.5 mm wall bearing strip over the tab engagement length, with no G11 backing credit. A screen failure identifies dependence on the G11 frame/ring path; it does not model that assembled reinforcement.",
        },
        "structural_frame": {
            "material": frame_material_name,
            "strength_bound_pa": frame_bound,
            "temperature_strength_fraction": temperature_strength_fraction,
            "rails_sharing_one_fin_assumed": rails_sharing_one_fin,
            "rail_cross_section_area_mm2": rail_area_mm2,
            "rail_normal_bending_axis": "radial X; fin-normal pressure is tangential CAD Y",
            "input_span_root_moment_axis": "axial CAD Z: radial span X crossed with tangential force Y",
            "span_root_to_rail_bending_moment_routing_verified": False,
            "rail_bending_quantity_status": "unverified load-routing surrogate; not an installed rail traction or capacity prediction",
            "rail_normal_section_modulus_mm3": rail_normal_section_modulus_mm3,
            "rail_normal_bending_stress_pa_single_support_bound": rail_normal_bending,
            "rail_normal_bending_margin": rail_normal_bending_margin,
            "rail_crossload_section_modulus_mm3": rail_crossload_section_modulus_mm3,
            "rail_crossload_bending_stress_pa_single_support_bound": rail_crossload_bending,
            "rail_crossload_bending_margin": rail_crossload_bending_margin,
            "rail_crossload_interpretation": "Orthogonal bending uncertainty case; not the main fin-normal pressure axis.",
            "rail_average_shear_stress_pa": rail_shear,
            "rail_shear_margin": rail_shear_margin,
            "ring_bearing_screen": ring_bearing,
            "status": "span-root axial-Z moment has not been transformed into longitudinal-rail radial-X bending; reported rail margins are surrogate screens only; connected ring/shell load routing remains unresolved",
        },
        "body_shell_local_bending": shell_strip,
        "root_rotational_flexibility": rotational,
        "load_path": "fin panel -> triangular side-gusset bonds -> fin/tab-to-G11 interface -> G11 longitudinal rail and backing rings -> kraft body wall; actual continuity, fasteners/adhesive, slot-edge peel and frame-to-shell load sharing remain unqualified.",
        "open_items": [
            "Actual tab-to-frame adhesive footprint, thickness, cure and peel strength are not resolved by nominal CAD dimensions.",
            "Root gusset and fin-face bonds require hot/cold coupon and assembled proof tests.",
            "G11 rail/ring local bending, slot concentration, body-shell bearing and full load-sharing need connected structural model with actual contact geometry.",
            "Root rotational stiffness is not a test result; measure assembled response before using in flutter.",
            "No stress result here qualifies the assembly; all margins remain preliminary screens.",
        ],
        "acceptance": "open",
        "acceptance_passed": False,
        "flight_ready": False,
    }
