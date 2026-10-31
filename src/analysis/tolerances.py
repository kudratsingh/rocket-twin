"""Spec-driven interval and thermal tolerance stacks for WO-03 interfaces.

This is a screening calculator. Its study assumptions are explicit and all
dimensions are read from resolved vehicle parts/CAD parameter blocks. Missing
purchased dimensions stay unavailable. It does not prove continuous motion,
wiring clearance, fit, or hardware qualification.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from src.vehicle.schema import Vehicle, load_vehicle, vehicle_input_paths


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _material_cte(part: Any, engineering: dict[str, Any]) -> float | None:
    profile = part.engineering.material_profile if part.engineering else part.material
    material = engineering.get("materials", {}).get(profile, {})
    bounds = material.get("cte_range_per_k")
    if bounds is not None:
        return max(abs(float(x)) for x in bounds)
    value = material.get("cte_per_k")
    return float(value) if value is not None else None


def _material_cte_range(part: Any, engineering: dict[str, Any]) -> tuple[float, float] | None:
    profile = part.engineering.material_profile if part.engineering else part.material
    material = engineering.get("materials", {}).get(profile, {})
    bounds = material.get("cte_range_per_k")
    if bounds is not None:
        lo, hi = (float(x) for x in bounds)
        if lo > hi:
            raise ValueError("CTE bounds must be ordered")
        return lo, hi
    value = _material_cte(part, engineering)
    return (value, value) if value is not None else None


def _material_limit_c(part: Any, engineering: dict[str, Any]) -> float | None:
    profile = part.engineering.material_profile if part.engineering else part.material
    value = engineering.get("materials", {}).get(profile, {}).get("limit_c")
    return float(value) if value is not None else None


def _domain_temperature(
    part: Any, engineering: dict[str, Any], study: dict[str, Any]
) -> dict[str, float] | None:
    limit = _material_limit_c(part, engineering)
    if limit is None:
        return None
    ambient = float(study["ambient_reference_c"])
    cap = min(float(study["maximum_external_case_sensitivity_c"]), limit)
    return {
        "minimum_c": ambient,
        "maximum_c": cap,
        "delta_t_k_minimum": 0.0,
        "delta_t_k_maximum": max(0.0, cap - ambient),
        "declared_material_limit_c": limit,
    }


def _tolerance(part: Any, dimension: str, interpretation: str) -> float | None:
    if not part.engineering:
        return None
    tolerance = part.engineering.tolerances_mm
    if interpretation == "radius_from_hole" and "hole_diameter" in tolerance:
        return float(tolerance["hole_diameter"]) / 2
    if interpretation == "radius_from_diameter" and "diameter" in tolerance:
        return float(tolerance["diameter"]) / 2
    return float(tolerance["linear"]) if "linear" in tolerance else None


def _thermal_gap_bounds(
    host_nominal_mm: float,
    insert_nominal_mm: float,
    host_cte_per_k: float | tuple[float, float] | None,
    insert_cte_per_k: float | tuple[float, float] | None,
    host_delta_t_k: list[float],
    insert_delta_t_k: list[float],
) -> tuple[float, float] | None:
    if host_cte_per_k is None or insert_cte_per_k is None:
        return None
    host_ctes = host_cte_per_k if isinstance(host_cte_per_k, tuple) else (host_cte_per_k,)
    insert_ctes = insert_cte_per_k if isinstance(insert_cte_per_k, tuple) else (insert_cte_per_k,)
    shifts = [
        host_cte * host_nominal_mm * host_dt - insert_cte * insert_nominal_mm * insert_dt
        for host_cte in host_ctes
        for insert_cte in insert_ctes
        for host_dt in host_delta_t_k
        for insert_dt in insert_delta_t_k
    ]
    return min(shifts), max(shifts)


def interval_stack(
    host_mm: float,
    insert_mm: float,
    host_tolerance_mm: float | None,
    insert_tolerance_mm: float | None,
    required_minimum_mm: float,
    thermal_gap_shift_mm: tuple[float, float] | None = (0.0, 0.0),
    clearance_factor: float = 1.0,
) -> dict[str, Any]:
    """Return simple worst-case host-minus-insert interval clearance."""
    if host_tolerance_mm is None or insert_tolerance_mm is None or thermal_gap_shift_mm is None:
        return {
            "minimum_mm": None,
            "nominal_mm": host_mm - insert_mm,
            "maximum_mm": None,
            "required_minimum_mm": required_minimum_mm,
            "status": "unavailable",
        }
    if clearance_factor <= 0:
        raise ValueError("clearance_factor must be positive")
    nominal = (host_mm - insert_mm) / clearance_factor
    variation = (host_tolerance_mm + insert_tolerance_mm) / clearance_factor
    minimum = nominal - variation + thermal_gap_shift_mm[0] / clearance_factor
    maximum = nominal + variation + thermal_gap_shift_mm[1] / clearance_factor
    return {
        "minimum_mm": minimum,
        "nominal_mm": nominal,
        "maximum_mm": maximum,
        "required_minimum_mm": required_minimum_mm,
        "status": "pass" if minimum >= required_minimum_mm else "fail",
    }


def _pair(
    name: str,
    host: Any,
    insert: Any,
    host_dim_mm: float,
    insert_dim_mm: float,
    required_mm: float,
    engineering: dict[str, Any],
    study: dict[str, Any],
    host_tol_kind: str = "linear",
    insert_tol_kind: str = "linear",
    clearance_factor: float = 1.0,
    clearance_definition: str = "host-minus-insert dimensional clearance",
) -> dict[str, Any]:
    host_tolerance = _tolerance(host, name, host_tol_kind)
    insert_tolerance = _tolerance(insert, name, insert_tol_kind)
    host_cte = _material_cte_range(host, engineering)
    insert_cte = _material_cte_range(insert, engineering)
    host_domain = _domain_temperature(host, engineering, study)
    insert_domain = _domain_temperature(insert, engineering, study)
    domain_thermal = (
        _thermal_gap_bounds(
            host_dim_mm,
            insert_dim_mm,
            host_cte,
            insert_cte,
            [host_domain["delta_t_k_minimum"], host_domain["delta_t_k_maximum"]],
            [insert_domain["delta_t_k_minimum"], insert_domain["delta_t_k_maximum"]],
        )
        if host_domain is not None and insert_domain is not None
        else None
    )
    sensitivity_thermal = _thermal_gap_bounds(
        host_dim_mm,
        insert_dim_mm,
        host_cte,
        insert_cte,
        [float(v) for v in study["host_delta_t_k"]],
        [float(v) for v in study["insert_delta_t_k"]],
    )
    nominal_result = interval_stack(
        host_dim_mm,
        insert_dim_mm,
        host_tolerance,
        insert_tolerance,
        required_mm,
        (0.0, 0.0),
        clearance_factor,
    )
    operating_result = interval_stack(
        host_dim_mm,
        insert_dim_mm,
        host_tolerance,
        insert_tolerance,
        required_mm,
        domain_thermal,
        clearance_factor,
    )
    sensitivity_result = interval_stack(
        host_dim_mm,
        insert_dim_mm,
        host_tolerance,
        insert_tolerance,
        required_mm,
        sensitivity_thermal,
        clearance_factor,
    )
    return {
        "interface": name,
        "host_part": host.id,
        "insert_part": insert.id,
        "dimensions_source": "resolved Vehicle part geometry/CAD parameters",
        "tolerance_source": "PartEngineering.tolerances_mm interpreted by study assumption",
        "clearance_definition": clearance_definition,
        "clearance_factor": clearance_factor,
        "host_tolerance_allowance_mm": host_tolerance,
        "insert_tolerance_allowance_mm": insert_tolerance,
        "host_cte_per_k": host_cte,
        "insert_cte_per_k": insert_cte,
        "host_material_screen_domain": host_domain,
        "insert_material_screen_domain": insert_domain,
        "design_operating_fit": operating_result,
        "manufacturing_nominal": nominal_result,
        "out_of_range_hot_sensitivity": sensitivity_result,
        "thermal_delta_t_k": {
            "host_independent_range": study["host_delta_t_k"],
            "insert_independent_range": study["insert_delta_t_k"],
        },
        "thermal_gap_shift_bounds_mm": list(domain_thermal) if domain_thermal is not None else None,
        **operating_result,
    }


def _unavailable(
    name: str, host: Any, insert: Any, nominal_mm: float | None, required_mm: float, reason: str
) -> dict[str, Any]:
    return {
        "interface": name,
        "host_part": host.id,
        "insert_part": insert.id,
        "minimum_mm": None,
        "nominal_mm": nominal_mm,
        "maximum_mm": None,
        "required_minimum_mm": required_mm,
        "status": "unavailable",
        "reason": reason,
    }


def analyze_vehicle(
    vehicle: Vehicle, engineering: dict[str, Any], study: dict[str, Any], config_id: str
) -> dict[str, Any]:
    parts = {part.id: part for part in vehicle.parts}
    required = study["minimum_required_clearance_mm"]
    host_delta_t = [float(v) for v in study["host_delta_t_k"]]
    insert_delta_t = [float(v) for v in study["insert_delta_t_k"]]
    stacks: list[dict[str, Any]] = []

    coupler = parts["interface_coupler"]
    for host_id in ["body_upper", "aft_shell"]:
        host = parts[host_id]
        stacks.append(
            _pair(
                f"{host_id}_inner_radius_to_coupler_outer_radius",
                host,
                coupler,
                host.geometry["inner_radius_m"] * 1000,
                coupler.geometry["radius_m"] * 1000,
                float(required["radial_fit"]),
                engineering,
                study,
                host_tol_kind="radius_from_hole",
            )
        )

    stop = parts["joint_stop"]
    assert coupler.cad is not None and stop.cad is not None
    slot_widths = coupler.cad.parameters.get("key_widths_mm", [])
    key_widths = stop.cad.parameters.get("key_widths_mm", [])
    if len(slot_widths) == len(key_widths) and slot_widths:
        for index, (slot, key) in enumerate(zip(slot_widths, key_widths, strict=True)):
            stacks.append(
                _pair(
                    f"key_{index + 1}_slot_width_to_key_width",
                    coupler,
                    stop,
                    float(slot),
                    float(key),
                    float(required["key_flank"]),
                    engineering,
                    study,
                    clearance_factor=2.0,
                    clearance_definition="centered per-flank clearance = (slot width - key width)/2; key centering is unverified",
                )
            )
            row = stacks[-1]
            row["unilateral_clearance_bounds_mm"] = [
                0.0,
                max(0.0, float(row["maximum_mm"]) * 2),
            ]
            row["key_centering_verified"] = False
            row["unilateral_status"] = "unavailable"
    else:
        stacks.append(
            _unavailable(
                "keyed_joint_width_stack",
                coupler,
                stop,
                None,
                float(required["key_flank"]),
                "Resolved CAD parameters do not provide matching slot/key width arrays.",
            )
        )

    liner, mount, motor = parts["motor_liner"], parts["motor_mount"], parts["motor"]
    mount_bore_mm = mount.geometry["inner_radius_m"] * 1000
    mount_at_carrier_mm = mount.geometry["radius_m"] * 1000
    cassette = bool(mount.cad and mount.cad.generator == "motor_cassette")
    if cassette:
        assert mount.cad
        o = mount.cad.parameters
        # Installation traverses the rails as well as the grip bore. The
        # largest end-block envelope is not the surface at the gimbal plane.
        mount_bore_mm = min(
            o["motor_clear_radius_mm"], o["rail_center_radius_mm"] - o["rail_radial_width_mm"] / 2
        )
        mount_at_carrier_mm = max(
            o["grip_outer_radius_mm"],
            math.hypot(
                o["rail_center_radius_mm"] + o["rail_radial_width_mm"] / 2,
                o["rail_tangential_width_mm"] / 2,
            ),
        )
    sleeve_outer = parts.get("motor_radiant_shield", liner)
    stacks.append(
        _pair(
            "motor_mount_inner_radius_to_liner_outer_radius",
            mount,
            sleeve_outer,
            mount_bore_mm,
            sleeve_outer.geometry["radius_m"] * 1000,
            float(required["radial_fit"]),
            engineering,
            study,
            host_tol_kind="linear" if cassette else "radius_from_hole",
        )
    )
    stacks[-1][
        "dimensions_source"
    ] = "Smallest rail/grip installation radius and outermost liner/foil surface from resolved CAD parameters; installed concentricity remains separate."
    stacks.append(
        _unavailable(
            "liner_inner_radius_to_motor_case_radius",
            liner,
            motor,
            (liner.geometry["inner_radius_m"] - motor.geometry["radius_m"]) * 1000,
            float(required["radial_fit"]),
            "Nominal resolved-source-hypothesis dimensions exist, but exact purchased motor-case OD tolerance and lot identity are unavailable.",
        )
    )

    carrier_id = "gimbal_inner" if vehicle.tvc else "aft_shell"
    carrier = parts[carrier_id]
    stacks.append(
        _pair(
            f"{carrier_id}_inner_radius_to_motor_mount_outer_radius",
            carrier,
            mount,
            carrier.geometry["inner_radius_m"] * 1000,
            mount_at_carrier_mm,
            float(required["radial_fit"]),
            engineering,
            study,
            host_tol_kind="radius_from_hole",
        )
    )
    stacks[-1][
        "dimensions_source"
    ] = "Carrier-plane grip/rail-corner radius; remote cassette end-block envelope is excluded from this local fit and remains in the motion checks."

    motion_bound: dict[str, Any]
    if not vehicle.tvc:
        for label in ["pivot_pin_bearing", "linkage_rod_bore", "combined_pitch_yaw_motion"]:
            stacks.append(
                {
                    "interface": label,
                    "minimum_mm": None,
                    "nominal_mm": None,
                    "maximum_mm": None,
                    "required_minimum_mm": float(
                        required["combined_motion_radial"]
                        if label == "combined_pitch_yaw_motion"
                        else required["pivot_radial"]
                    ),
                    "status": "not_applicable",
                }
            )
        motion_bound = {"status": "not_applicable"}
    else:
        inner_host = parts["gimbal_inner"]
        links = parts["gimbal_links"]
        assert inner_host.cad is not None and links.cad is not None
        for host_id, pin_id in [
            ("tvc_gimbal", "outer_pivots"),
            ("gimbal_frame", "outer_pivots"),
            ("gimbal_inner", "inner_pivots"),
            ("tvc_gimbal", "inner_pivots"),
        ]:
            host, pin = parts[host_id], parts[pin_id]
            assert host.cad is not None and pin.cad is not None
            bore_diameter = host.cad.parameters.get("pivot_bore_diameter_mm")
            interface_name = f"{host_id}_bearing_hole_to_{pin_id}"
            if bore_diameter is None:
                stacks.append(
                    _unavailable(
                        interface_name,
                        host,
                        pin,
                        None,
                        float(required["pivot_radial"]),
                        "No resolved-spec bearing-bore diameter. Generator default is not dimensional evidence.",
                    )
                )
            else:
                pin_radius = max(float(item["radius_mm"]) for item in pin.cad.parameters["pins"])
                row = _pair(
                    interface_name,
                    host,
                    pin,
                    float(bore_diameter) / 2,
                    pin_radius,
                    float(required["pivot_radial"]),
                    engineering,
                    study,
                    host_tol_kind="radius_from_hole",
                    insert_tol_kind="radius_from_diameter",
                    clearance_definition="one-sided radial bearing clearance; half the bore-minus-pin diametral gap",
                )
                row["axial_retention_status"] = (
                    "open; a bearing-clearance pass does not retain the pin"
                )
                stacks.append(row)
        bore_length = float(inner_host.cad.parameters["link_bore"]["length_mm"])
        rod_diameter = float(links.cad.parameters["radius_mm"]) * 2
        link_bore_diameter = inner_host.cad.parameters["link_bore"].get("diameter_mm")
        if link_bore_diameter is None:
            stacks.append(
                _unavailable(
                    "linkage_rod_to_bore_and_rod_end_envelope",
                    inner_host,
                    links,
                    None,
                    float(required["linkage_radial"]),
                    f"Rod diameter {rod_diameter:.3f} mm and axial bore length {bore_length:.3f} mm are present, but bore radius/rod-end articulation are generator/purchased details not represented by the resolved specification.",
                )
            )
        else:
            row = _pair(
                "linkage_rod_to_bore_and_rod_end_envelope",
                inner_host,
                links,
                float(link_bore_diameter) / 2,
                rod_diameter / 2,
                float(required["linkage_radial"]),
                engineering,
                study,
                host_tol_kind="radius_from_hole",
                insert_tol_kind="radius_from_diameter",
                clearance_definition="radial rod-to-bore clearance only; excludes rod-end articulation and assembly withdrawal",
            )
            row["articulation_status"] = (
                "unavailable: exact purchased rod ends, angular limits and wiring still require closure"
            )
            stacks.append(row)

        assert vehicle.tvc is not None
        shell, pivot = parts["aft_shell"], vehicle.tvc.pivot_position_m
        front = liner.position_m
        back = liner.position_m + liner.geometry["length_m"]
        lever_mm = max(abs(front - pivot), abs(back - pivot)) * 1000
        max_axis_rad = vehicle.tvc.max_deflection_rad
        combined_angle = math.acos(math.cos(max_axis_rad) ** 2)
        nominal_radial_extent = liner.geometry["radius_m"] * 1000 + lever_mm * math.sin(
            combined_angle
        )
        nominal_clearance = shell.geometry["inner_radius_m"] * 1000 - nominal_radial_extent
        shell_tol = _tolerance(shell, "combined-shell-radius", "radius_from_hole")
        liner_tol = _tolerance(liner, "combined-liner-radius", "linear")
        alpha_shell = _material_cte(shell, engineering)
        alpha_liner = _material_cte(liner, engineering)
        if None in (shell_tol, liner_tol, alpha_shell, alpha_liner):
            motion_bound = {"status": "unavailable", "nominal_clearance_mm": nominal_clearance}
        else:
            assert shell_tol is not None
            assert liner_tol is not None
            assert alpha_shell is not None
            assert alpha_liner is not None
            shell_domain = _domain_temperature(shell, engineering, study)
            liner_domain = _domain_temperature(liner, engineering, study)
            if shell_domain is None or liner_domain is None:
                motion_bound = {
                    "status": "unavailable",
                    "nominal_geometric_clearance_mm": nominal_clearance,
                }
                domain_thermal_loss = None
            else:
                domain_thermal_loss = (
                    abs(alpha_shell * shell.geometry["inner_radius_m"] * 1000)
                    * shell_domain["delta_t_k_maximum"]
                    + abs(alpha_liner * liner.geometry["radius_m"] * 1000)
                    * liner_domain["delta_t_k_maximum"]
                )
            sensitivity_thermal_loss = abs(
                alpha_shell * shell.geometry["inner_radius_m"] * 1000
            ) * max(abs(v) for v in host_delta_t) + abs(
                alpha_liner * liner.geometry["radius_m"] * 1000
            ) * max(
                abs(v) for v in insert_delta_t
            )
            eccentricity = float(study["combined_motion_uncertainty_mm"]["centerline_eccentricity"])
            shaft_uncertainty = float(
                study["combined_motion_uncertainty_mm"]["shaft_or_pivot_location"]
            )
            base_clearance = (
                nominal_clearance
                - float(shell_tol)
                - float(liner_tol)
                - eccentricity
                - shaft_uncertainty
            )
            operating = (
                {
                    "minimum_mm": base_clearance - domain_thermal_loss,
                    "maximum_mm": nominal_clearance
                    + float(shell_tol)
                    + float(liner_tol)
                    + domain_thermal_loss
                    + eccentricity
                    + shaft_uncertainty,
                    "status": (
                        "pass"
                        if base_clearance - domain_thermal_loss
                        >= float(required["combined_motion_radial"])
                        else "fail"
                    ),
                }
                if domain_thermal_loss is not None
                else {"minimum_mm": None, "maximum_mm": None, "status": "unavailable"}
            )
            sensitivity = {
                "minimum_mm": base_clearance - sensitivity_thermal_loss,
                "maximum_mm": nominal_clearance
                + float(shell_tol)
                + float(liner_tol)
                + sensitivity_thermal_loss
                + eccentricity
                + shaft_uncertainty,
                "status": (
                    "pass"
                    if base_clearance - sensitivity_thermal_loss
                    >= float(required["combined_motion_radial"])
                    else "fail"
                ),
            }
            motion_bound = {
                "status": operating["status"],
                "nominal_geometric_clearance_mm": nominal_clearance,
                "minimum_bound_mm": operating["minimum_mm"],
                "maximum_geometric_clearance_mm": operating["maximum_mm"],
                "within_material_screen_domain": operating,
                "out_of_range_hot_sensitivity": sensitivity,
                "required_minimum_mm": float(required["combined_motion_radial"]),
                "max_combined_axis_angle_deg": math.degrees(combined_angle),
                "liner_pivot_lever_mm": lever_mm,
                "shell_liner_tolerance_allowance_mm": float(shell_tol) + float(liner_tol),
                "within_domain_thermal_allowance_mm": domain_thermal_loss,
                "out_of_range_thermal_sensitivity_allowance_mm": sensitivity_thermal_loss,
                "thermal_delta_t_k": {
                    "shell_material_domain": shell_domain,
                    "liner_material_domain": liner_domain,
                    "out_of_range_shell_sensitivity": host_delta_t,
                    "out_of_range_liner_sensitivity": insert_delta_t,
                },
                "shell_cte_per_k": alpha_shell,
                "liner_cte_per_k": alpha_liner,
                "centerline_eccentricity_allowance_mm": eccentricity,
                "shaft_or_pivot_location_uncertainty_mm": shaft_uncertainty,
                "basis": "Within-domain design screen uses independent shell/liner temperature bounds from 15 C to each declared material limit. Out-of-range sensitivity separately varies temperatures to the 250 C case scenario. Both use cylinder radial extent plus axial lever*sin(combined orthogonal angle), shell/liner tolerances, eccentricity and shaft/pivot uncertainty; neither is a paired temperature history or full mechanism/wiring proof.",
            }
        stacks.append(
            {
                "interface": "motor_liner_shell_combined_pitch_yaw_radial_bound",
                "minimum_mm": motion_bound.get("minimum_bound_mm"),
                "nominal_mm": motion_bound.get("nominal_geometric_clearance_mm"),
                "maximum_mm": motion_bound.get("maximum_geometric_clearance_mm"),
                "required_minimum_mm": float(required["combined_motion_radial"]),
                "status": motion_bound["status"],
            }
        )

    unknowns = list(study.get("critical_unknowns", []))
    critical_unknowns = [
        "Exact purchased motor-case OD tolerance unavailable.",
        "Actual assembled concentricity and thermal component histories are unmeasured.",
    ]
    if vehicle.tvc:
        critical_unknowns.extend(
            [
                "Pivot bearing-hole dimensions are not spec-owned.",
                "Servo spline/rod-end geometry and full mechanism/wiring envelopes are unavailable.",
            ]
        )
    acceptance = not critical_unknowns and all(
        row["status"] in ("pass", "not_applicable") for row in stacks
    )
    return {
        "configuration_id": config_id,
        "vehicle_id": vehicle.id,
        "resolved_spec_sha256": _sha256(vehicle.model_dump_json(by_alias=True).encode()),
        "stacks": stacks,
        "combined_motion_bound": motion_bound,
        "critical_unknowns": critical_unknowns,
        "other_study_unknowns": unknowns,
        "tolerance_interpretation": study["tolerance_interpretation"],
        "thermal_delta_basis": study["thermal_delta_basis"],
        "acceptance": "open" if not acceptance else "screen_pass_only",
        "acceptance_passed": acceptance,
        "physical_fit_verified": False,
        "continuous_full_mechanism_verified": False,
    }


def generate(config_path: Path, root: Path = Path(".")) -> Path:
    config_bytes = (root / config_path).read_bytes()
    study = yaml.safe_load(config_bytes)
    engineering_path = root / study["engineering_inputs"]
    engineering_bytes = engineering_path.read_bytes()
    engineering = yaml.safe_load(engineering_bytes)
    thermal_record_path = root / study["thermal_evidence_record"]
    thermal_record = json.loads(thermal_record_path.read_text())
    run_id = "wo03-tolerances-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir = root / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    mode_reports = []
    code_inputs = {
        root / config_path,
        engineering_path,
        root / "src/analysis/tolerances.py",
        root / "scripts/wo03_tolerances.py",
        root / "src/cad/verification.py",
        root / "src/cad/parts.py",
        thermal_record_path,
    }
    inputs: set[Path] = set(code_inputs)
    vehicles = []
    for config_id, relpath in study["configurations"].items():
        vehicle_path = root / relpath
        vehicle = load_vehicle(vehicle_path)
        inputs.update(vehicle_input_paths(vehicle_path))
        vehicles.append((config_id, vehicle_path, vehicle))
    before_inputs = {
        str(path.resolve().relative_to(root.resolve())): _sha256(path.read_bytes())
        for path in sorted(inputs)
        if path.exists()
    }
    for config_id, vehicle_path, vehicle in vehicles:
        report = analyze_vehicle(vehicle, engineering, study, config_id)
        thermal_mode = next(
            (item for item in thermal_record["vehicles"] if item.get("vehicle") == vehicle.id),
            None,
        )
        hot_case = (
            next(
                (
                    item
                    for item in thermal_mode.get("thermal", [])
                    if item.get("case") == "upper-hot-soak"
                ),
                None,
            )
            if thermal_mode
            else None
        )
        over_temperature = [
            {
                "part_id": item["part_id"],
                "peak_c": item["peak_c"],
                "screen_limit_c": item["screen_limit_c"],
                "margin_k": item["margin_k"],
            }
            for item in (hot_case.get("peaks", []) if hot_case else [])
            if item.get("passed") is False
        ]
        report["thermal_evidence"] = {
            "record": str(thermal_record_path.resolve().relative_to(root.resolve())),
            "run_id": thermal_record.get("run_id"),
            "case": "upper-hot-soak",
            "out_of_screen_limit_parts": over_temperature,
            "thermal_gate_status": "open" if over_temperature else "unresolved",
            "limitation": "Exploratory thermal screen with estimated properties/boundaries; not a measured paired thermal history or qualified allowable.",
        }
        mode_inputs = set(vehicle_input_paths(vehicle_path)) | code_inputs
        report["source_sha256"] = {
            str(path.resolve().relative_to(root.resolve())): _sha256(path.read_bytes())
            for path in sorted(mode_inputs)
            if path.exists()
        }
        report["study_config_sha256"] = _sha256(config_bytes)
        report["engineering_inputs_sha256"] = _sha256(engineering_bytes)
        report["thermal_evidence_sha256"] = _sha256(thermal_record_path.read_bytes())
        report["cad_identity"] = {
            part.id: getattr(getattr(part, "cad_mass", None), "shape_sha256", None)
            for part in vehicle.parts
        }
        report_path = root / "build" / vehicle.id / "tolerances.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False).encode() + b"\n"
        report_path.write_bytes(encoded)
        mode_reports.append(
            {
                "configuration_id": config_id,
                "vehicle_id": vehicle.id,
                "report": str(report_path.relative_to(root)),
                "report_sha256": _sha256(encoded),
                "resolved_spec_sha256": report["resolved_spec_sha256"],
                "acceptance": report["acceptance"],
                "acceptance_passed": report["acceptance_passed"],
                "critical_unknowns": report["critical_unknowns"],
            }
        )
    final_inputs = {
        str(path.resolve().relative_to(root.resolve())): _sha256(path.read_bytes())
        for path in sorted(inputs)
        if path.exists()
    }
    inputs_unchanged = before_inputs == final_inputs
    record = {
        "run_id": run_id,
        "work_order": "03",
        "study_config_sha256": _sha256(config_bytes),
        "engineering_inputs_sha256": _sha256(engineering_bytes),
        "thermal_evidence_sha256": _sha256(thermal_record_path.read_bytes()),
        "input_sha256_before": before_inputs,
        "input_sha256_after": final_inputs,
        "inputs_unchanged": inputs_unchanged,
        "vehicles": mode_reports,
        "acceptance": "open",
        "acceptance_passed": all(item["acceptance_passed"] for item in mode_reports),
        "physical_fit_verified": False,
        "continuous_full_mechanism_verified": False,
        "flight_ready": False,
        "active_adoption": False,
        "cost_usd": 0,
    }
    path = run_dir / "record.json"
    path.write_text(json.dumps(record, indent=2, sort_keys=True, allow_nan=False) + "\n")
    return path
