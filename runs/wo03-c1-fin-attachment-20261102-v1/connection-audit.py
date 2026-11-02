"""Read-only closure of v1 hand-screen identities; no guide/native rerun."""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
path = HERE / "record.json"
original = path.read_bytes()
r = json.loads(original)
out = {
    "source_record_sha256": hashlib.sha256(original).hexdigest(),
    "scope": "Derived joint demands and corrected receiver-only torque reference, not installed acceptance or another physics campaign",
    "receiver_motion_correction": "v1 receiver-only elastic term used body-root moment, and first audit used socket-center moment. Receiver/end torsion must use rocket-axis moment including F times full 33 mm root radius. Both prior records are preserved; only torque-dependent proxies are superseded. Decisions unchanged.",
    "structures": {},
}
for name, structure in r["structures"].items():
    p = structure["attachment"]
    axis_torque = p["reference_root_moment_DF3_Nm"] + r["load_case"]["force_DF3_once_N"] * 0.033
    transported_axis_torque = (
        p["socket_center_moment_DF3_Nm"] + r["load_case"]["force_DF3_once_N"] * 0.0243
    )
    if not math.isclose(axis_torque, transported_axis_torque, abs_tol=1e-12):
        raise ValueError("Force/couple transport changed axis torque")
    service_torque = axis_torque / 3
    lever = 0.0987
    corrected_receiver_motion = service_torque / p["receiver_hot_upper_stiffness_Nm_rad"] * lever
    panel = structure["panel_states"][1]["levels"][-1]["tip_m"]
    finite = []
    gj = 2e9 * p["receiver_unslotted_torsional_J_m4"]
    # One key per end taking full end torque; Eeff includes local-contact flexibility.
    # These are explicit sensitivity inputs, not supplier/assembled stiffness bounds.
    for effective_E in (0.1e9, 1e9):
        key_k = effective_E * 36e-6 / 0.006 * 0.027**2
        branches = [1 / (length / gj + 1 / key_k) for length in (0.13, 0.0718)]
        finite.append(
            {
                "effective_key_contact_E_pa_unvalidated": effective_E,
                "single_key_rotational_stiffness_Nm_rad": key_k,
                "two_finite_end_branches_Nm_rad": sum(branches),
                "elastic_tip_motion_m": service_torque / sum(branches) * lever,
                "key_per_flank_gap_only_tip_motion_m": 0.00002 / 0.027 * lever,
                "total_panel_socket_key_gap_finite_receiver_motion_m": panel
                + p["socket_play_only_tip_motion_m"]
                + 0.00002 / 0.027 * lever
                + service_torque / sum(branches) * lever,
            }
        )
    torque = [axis_torque * 0.0718 / 0.2018, axis_torque * 0.13 / 0.2018]
    transverse = p["single_fin_factored_transverse_end_reactions_N"]
    joint = []
    area = 0.75 * 2 * math.pi * 0.032 * 0.0255
    for i in range(2):
        bolt_force = torque[i] / 0.024
        key_force = torque[i] / 0.027
        joint.append(
            {
                "end": ["fore", "aft"][i],
                "ideal_share_torque_DF3_Nm": torque[i],
                "transverse_DF3_N": transverse[i],
                "single_M3_tangential_DF3_N": bolt_force,
                "single_M3_shear_pa": bolt_force / (math.pi * 0.003**2 / 4),
                "single_end_barrel_mean_bearing_pa": bolt_force / (0.006 * 0.006275),
                "single_end_barrel_two_ligament_mean_shear_pa": bolt_force
                / (2 * ((0.014 if i == 0 else 0.008) - 0.0062 / 2) * 0.006275),
                "one_R1_key_full_end_torque_N": key_force,
                "R1_key_36mm2_mean_shear_or_bearing_pa": key_force / 36e-6,
                "capacity_status": "Demand only; actual hot bearing/interlaminar/fastener allowable, cap pocket ligaments and attachment stiffness unavailable",
            }
        )
    # Same q/alpha screen over all three 120-degree fins: linear normal force projection.
    # Net torque sum_i sin(alpha_direction-phi_i) is zero, not three same-sign maxima.
    residual = sum(math.sin(math.radians(phi)) for phi in (0, 120, 240))
    out["structures"][name] = {
        "rocket_axis_torque_DF3_once_Nm": axis_torque,
        "axis_torque_transport_residual_Nm": axis_torque - transported_axis_torque,
        "corrected_receiver_only_service_motion_m": corrected_receiver_motion,
        "corrected_hot_panel_play_and_ideal_receiver_motion_m": panel
        + p["socket_play_only_tip_motion_m"]
        + corrected_receiver_motion,
        "corrected_1mm_remaining_m": 0.001
        - panel
        - p["socket_play_only_tip_motion_m"]
        - corrected_receiver_motion,
        "finite_joint_sensitivities_not_validated_bounds": finite if name == "R1" else None,
        "end_joint_demands": joint,
        "fore_skirt_aero_torque_mean_shear_pa": torque[0] / (area * 0.032),
        "fore_skirt_transverse_mean_shear_pa": transverse[0] / area,
        "fore_skirt_effective_bond_area_m2": area,
        "body_bond_peel_local_crushing_and_paper_capacity": None,
        "socket_bridge_hot_1MPa_shear_estimate_ratio": 1e6
        / p["cheek_to_bridge_min_mean_hot_bond_shear_pa"],
        "three_fins_small_angle_equal_geometry_roll_torque_sum_residual": residual,
        "multi_fin_validity": "Single-fin envelope establishes local demands. Three same-sign full moments are not this symmetric steady case; asymmetric gust/fault roll, pitch and recovery cases remain to resolve with actual flexible supports.",
    }
# Geometric hot fits already saved for the source: do not call them new temperatures.
out["inherited_clearance_sensitivities"] = {
    "outer_receiver_to_body_cold_min_mm": 0.200,
    "outer_receiver_to_body_G11_150C_min_mm": 0.108,
    "required_min_mm": 0.100,
    "R1_outer_radius_unchanged": True,
    "R1_inner_radius_reduction_mm": 0.2,
    "motor_relative_axial_closure_bound_mm": 2.0352,
    "nominal_floating_travel_less_manufacturing_mm": 2.7,
    "remaining_axial_travel_mm": 2.7 - 2.0352,
    "status": "Inherited source bounded-input sensitivities only. New root/shim/key/contact paths, purchased nozzle/case, radial inner clearances and service need actual geometry and hot properties. No new fit/thermal acceptance.",
}
if path.read_bytes() != original:
    raise ValueError("Original record changed")
output = HERE / "connection-audit.json"
if output.exists():
    raise FileExistsError(output)
output.write_text(json.dumps(out, indent=2, sort_keys=True, allow_nan=False) + "\n")
print(
    json.dumps(
        {
            "record_unchanged": True,
            "C1_total_tip_mm": out["structures"]["C1"][
                "corrected_hot_panel_play_and_ideal_receiver_motion_m"
            ]
            * 1000,
            "R1_total_tip_mm": out["structures"]["R1"][
                "corrected_hot_panel_play_and_ideal_receiver_motion_m"
            ]
            * 1000,
        }
    )
)
