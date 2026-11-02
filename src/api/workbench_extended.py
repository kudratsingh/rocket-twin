"""Source-checked extension to the frozen walkthrough: recorded data, no solves.

Graph positions are presentation topology, never physical coordinates. Physical
quantities are copied from saved sources, with unit conversion only. Historical
thermal identities cannot populate the current C1 geometry or qualify its design.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.api.workbench import ROOT, WorkbenchUnavailable, build_workbench

MAPPING = "configs/engineering/workbench-extended.yaml"


def _read(root: Path, relative: str) -> bytes:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise WorkbenchUnavailable(f"Extended source path escapes repository: {relative}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise WorkbenchUnavailable(f"Extended source unavailable: {relative}") from error


def _quantity(
    label: str, value: float | None, unit: str, state: str = "estimated"
) -> dict[str, Any]:
    return {"label": label, "value": value, "unit": unit, "state": state}


def _node(
    nid: str,
    label: str,
    part_ids: list[str],
    sources: list[str],
    note: str,
    state: str = "unavailable",
    **extra: Any,
) -> dict[str, Any]:
    return {
        "id": nid,
        "label": label,
        "state": state,
        "part_ids": part_ids,
        "source_ids": sources,
        "note": note,
        **extra,
    }


def _edge(
    eid: str,
    start: str,
    end: str,
    label: str,
    part_ids: list[str],
    sources: list[str],
    note: str,
    state: str = "unavailable",
    quantities: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        **_node(eid, label, part_ids, sources, note, state),
        "from": start,
        "to": end,
        "quantities": quantities or [],
    }


def _graph(
    gid: str,
    label: str,
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    sources: list[str],
    note: str,
    configuration: str,
    compatible: bool = True,
    state: str = "unavailable",
) -> dict[str, Any]:
    return {
        "id": gid,
        "label": label,
        "state": state,
        "configuration_id": configuration,
        "compatible_with_c1": compatible,
        "note": note,
        "source_ids": sources,
        "nodes": nodes,
        "edges": edges,
    }


def _step(
    sid: str,
    label: str,
    description: str,
    part_ids: list[str],
    sources: list[str],
    state: str = "unavailable",
) -> dict[str, Any]:
    return {
        "id": sid,
        "label": label,
        "description": description,
        "state": state,
        "part_ids": part_ids,
        "source_ids": sources,
    }


def _load(
    root: Path,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    raw = _read(root, MAPPING)
    config = yaml.safe_load(raw)
    records: dict[str, Any] = {}
    sources = []
    for sid, entry in config["sources"].items():
        content = _read(root, entry["path"])
        if hashlib.sha256(content).hexdigest() != entry["sha256"]:
            raise WorkbenchUnavailable(f"Extended frozen source hash mismatch: {entry['path']}")
        sources.append({"id": sid, **entry})
        if entry["path"].endswith(".json"):
            records[sid] = json.loads(content)
        elif entry["path"].endswith(".yaml"):
            records[sid] = yaml.safe_load(content)
    base = build_workbench(root)
    for source in base["generated_from"]:
        if source["path"].endswith(".json"):
            records[source["id"]] = json.loads(_read(root, source["path"]))
        elif source["path"].endswith(".yaml"):
            records[source["id"]] = yaml.safe_load(_read(root, source["path"]))
    sources = base["generated_from"] + sources
    sources.append(
        {
            "id": "extended_mapping",
            "path": MAPPING,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "description": "Versioned separate extension presentation mapping",
        }
    )
    code = "src/api/workbench_extended.py"
    sources.append(
        {
            "id": "extended_exporter",
            "path": code,
            "sha256": hashlib.sha256(_read(root, code)).hexdigest(),
            "description": "Read-only extension exporter implementation",
        }
    )
    return config, records, base, sources


def _candidates(r: dict[str, Any], base: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    affected = [
        "c1_fin_panels",
        "C1_closed_G11_body_annulus",
        "C1_fin_socket_side_plate_1",
        "fore_integral_G11_annular_cap",
        "C1_aft_cap_15p8_bore",
    ]
    for cid in ("C1", "R1", "C2", "C3"):
        if cid in {"C1", "R1"}:
            cases = [
                {k: value for k, value in case.items() if k not in {"state", "added_mass_g"}}
                for case in base["cases"]
                if case["id"].startswith(cid + "_")
            ]
            for case in cases:
                case["source_ids"] = ["attachment_record"]
            net = 0 if cid == "C1" else r["attachment_record"]["R1_added_mass_g"]
            source_ids = ["source_lock", "attachment_record", "connection_audit", "c2_record"]
            stop = (
                (
                    "Selected preliminary mass/balance only. Fin/socket hot strength and scalar motion screens fail; "
                    "actual receiver/end/body/recovery, thermal and flutter remain unqualified."
                )
                if cid == "C1"
                else r["attachment_record"]["decision"]
            )
            corrections = r["c2_record"]["prior_receiver_radius_datum_correction"][cid]
            quantities = [
                _quantity(
                    "Axis-radius-corrected aggregate scalar proxy",
                    corrections["panel_socket_play_receiver_only_tip_m"] * 1000,
                    "mm",
                    "failed",
                ),
                _quantity(
                    "Rocket-axis torque; DF3 once",
                    corrections["axis_torque_DF3_Nm"],
                    "N m",
                    "calculated",
                ),
            ]
        else:
            sid = "c2_record" if cid == "C2" else "source_c3"
            record = r[sid]
            source_ids = [sid]
            cases = []
            for index, case in enumerate(record["cases"]):
                cases.append(
                    {
                        "id": case["id"],
                        "label": "Nominal" if index == 0 else "Additional 20 g / motor-CG probe",
                        "total_g": case["total_g"],
                        "nominal_g": case["nominal_plus_optional20g_g"],
                        "growth_g": case["separate_full_growth_g"],
                        "extra_aft_g": (
                            0
                            if index == 0
                            else r["attachment_config"]["criteria"]["extra_aft_sensitivity_g"]
                        ),
                        "cg_mm": case["cg_mm"],
                        "cp_mm": case["cp_mm"],
                        "loaded_margin_cal": case["loaded_margin_cal"],
                        "burnout_cg_mm": case["burnout_cg_mm"],
                        "burnout_margin_cal": case["burnout_margin_cal"],
                        "recovery_force_n": case["severe_recovery_DF3_mean_N"],
                        "formal_headroom_g": case["formal_1p971m_headroom_g"],
                        "planning_headroom_g": case["planning_1p971m_headroom_g"],
                        "guide_results": [
                            {
                                "usable_m": g["usable_m"],
                                "speed_mps": g["rail_exit_speed_mps"],
                                "formal_margin_mps": g["formal_margin_mps"],
                                "planning_margin_mps": g["planning_margin_mps"],
                            }
                            for g in case["guides"]
                        ],
                        "source_ids": [sid],
                        "findings": (
                            [
                                "Separate full 50 g retained; no geometry adoption, installed qualification or full inertia",
                                "Guide/headroom conditional on unconfirmed illustrative 1.971 m usable equipment",
                                "Additional probe is beyond separate 50 g; motor-CG shift is illustrative, not manufacturer tolerance",
                            ]
                            if index
                            else ["Separate full 50 g retained; candidate not admitted"]
                        ),
                    }
                )
            net, stop = record["net_added_mass_g"], record["decision"]
            if cid == "C2":
                quantities = [
                    _quantity(
                        "Receiver doubler minimum mean hot bond shear",
                        record["receiver_joint"]["mean_DF3_hot_bond_shear_pa"] / 1e6,
                        "MPa",
                        "failed",
                    ),
                    _quantity(
                        "Aggregate service scalar proxy",
                        record["panel_and_finite_root"]["aggregate_service_motion_proxy_m"] * 1000,
                        "mm",
                        "failed",
                    ),
                ]
            else:
                quantities = [
                    _quantity(
                        "Nominal aft node / motor arm overlap, axial",
                        record["geometry"]["nominal_overlap_axial_radial_tangent_mm"][0],
                        "mm",
                        "failed",
                    ),
                    _quantity(
                        "Nominal aft node / motor arm overlap, radial",
                        record["geometry"]["nominal_overlap_axial_radial_tangent_mm"][1],
                        "mm",
                        "failed",
                    ),
                    _quantity(
                        "Nominal aft node / motor arm overlap, tangential",
                        record["geometry"]["nominal_overlap_axial_radial_tangent_mm"][2],
                        "mm",
                        "failed",
                    ),
                    _quantity(
                        "Harness gap after motion/manufacturing sensitivity",
                        record["geometry"]["harness_after_motion_manufacturing_mm"],
                        "mm",
                        "failed",
                    ),
                ]
        result.append(
            {
                "id": cid,
                "label": {
                    "C1": "Selected preliminary C1",
                    "R1": "Stopped R1 reinforcement",
                    "C2": "Rejected C2 sandwich / local receiver doubler",
                    "C3": "Rejected C3 continuous channels / end nodes",
                }[cid],
                "state": "estimated" if cid == "C1" else "failed",
                "active": False,
                "stop_joint_ids": (
                    ["receiver_end", "motor_service"] if cid == "C3" else ["fin_root"]
                ),
                "part_ids": affected,
                "source_ids": source_ids,
                "stop_reason": stop,
                "net_added_mass_g": net,
                "full_intrinsic_inertia": None,
                "cases": cases,
                "quantities": quantities,
            }
        )
    result.extend(_architecture_candidates(r))
    return result


def _architecture_candidates(r: dict[str, Any]) -> list[dict[str, Any]]:
    """Append two source-defined concepts without mapping their geometry onto C1."""
    packet = r["architecture_record"]
    config = r["architecture_config"]
    sources = [
        "architecture_record",
        "architecture_config",
        "architecture_executed_script",
        "architecture_research",
    ]
    result = []
    for arrangement in packet["arrangements"]:
        cases = []
        for index, case in enumerate(arrangement["cases"]):
            cases.append(
                {
                    "id": case["id"],
                    "label": "Nominal" if index == 0 else "Additional 20 g / motor-CG probe",
                    "total_g": case["total_g"],
                    "nominal_g": case["subtotal_without_separate_growth_g"],
                    "growth_g": case["separate_growth_g"],
                    "extra_aft_g": 0 if index == 0 else config["criteria"]["additional_aft_g"],
                    "cg_mm": case["cg_mm"],
                    "cp_mm": case["cp_mm"],
                    "loaded_margin_cal": case["loaded_static_cal"],
                    "burnout_cg_mm": case["burnout_cg_mm"],
                    "burnout_margin_cal": case["burnout_static_cal"],
                    "recovery_force_n": case["required_severe_recovery_DF3_mean_N"],
                    "formal_headroom_g": case["conditional1p971_formal_headroom_g"],
                    "planning_headroom_g": case["conditional1p971_planning_headroom_g"],
                    "baseline_formal_headroom_g": case["baseline_formal_headroom_g"],
                    "baseline_planning_headroom_g": case["baseline_planning_headroom_g"],
                    "guide_results": [
                        {
                            "usable_m": guide["usable_m"],
                            "speed_mps": guide["rail_exit_speed_mps"],
                            "formal_margin_mps": guide["formal_margin_mps"],
                            "planning_margin_mps": guide["planning_margin_mps"],
                        }
                        for guide in case["guides"]
                    ],
                    "source_ids": sources,
                    "findings": [
                        "Separate full 50 g retained; baseline usable 1.5 m and formal 15 / planning 15.5 m/s unchanged",
                        "Both baseline cases fail formal departure; conditional longer-guide results do not revise the baseline or confirm equipment",
                        "formal_headroom_g/planning_headroom_g refer only to illustrative 1.971 m usable; baseline headrooms are separate explicit fields",
                        "No detailed CAD, installed root/receiver/thermal/flutter qualification or full inertia supplied",
                    ]
                    + (
                        [
                            "Additional 20 g is beyond the separate 50 g; motor-CG probe is illustrative, not supplier tolerance"
                        ]
                        if index
                        else []
                    ),
                }
            )
        demand = arrangement["section_demands"]
        preferred = packet["preferred_direction"].startswith(arrangement["id"] + "_")
        result.append(
            {
                "id": arrangement["id"],
                "candidate_identity": arrangement["id"],
                "geometry_maturity": "concept",
                "label": (
                    "Architecture A · integrated motor/fin can"
                    if arrangement["id"] == config["A"]["id"]
                    else "Architecture B · outer captured roots"
                ),
                "state": "failed",
                "active": False,
                "preferred_for_next_joint_study": preferred,
                "part_ids": [],
                "stop_joint_ids": [],
                "source_ids": sources,
                "stop_reason": (
                    "Not admitted: both 1.5 m baseline departure cases fail formal 15 m/s. "
                    + (
                        "A is preferred only for a bounded connection-demand study, not detailed CAD or adoption. "
                        if preferred
                        else "B's saved best-case panel/play/tube proxy exceeds 1 mm; it is not installed movement proof. "
                    )
                    + "Unresolved source admission items: "
                    + "; ".join(
                        item.replace("_", " ") for item in arrangement["unresolved_admission"]
                    )
                    + ". Exact retainer fit, hot cap/root and finished sewn-bend capacities remain unqualified."
                ),
                "net_added_mass_g": arrangement["net_mass_delta_g"],
                "full_intrinsic_inertia": None,
                "cases": cases,
                "quantities": [
                    _quantity(
                        "Signed net mass change versus frozen C1",
                        arrangement["net_mass_delta_g"],
                        "g",
                        "estimated",
                    ),
                    _quantity(
                        "Panel/play/ideal-tube best-case scalar proxy; not installed proof",
                        demand["panel_play_ideal_tube_best_case_proxy_mm"],
                        "mm",
                        "calculated",
                    ),
                    _quantity(
                        "Actual installed tube/joint movement",
                        demand["installed_tube_joint_motion_mm"],
                        "mm",
                        "unavailable",
                    ),
                    _quantity(
                        "Whole severe recovery at one saddle demand",
                        demand["whole_recovery_at_one_saddle_N"],
                        "N",
                        "calculated",
                    ),
                    _quantity(
                        "Root peel or socket bearing allowable",
                        demand["root_bond_normal_peel_or_socket_bearing_allowable"],
                        "Pa",
                        "unavailable",
                    ),
                    _quantity(
                        "Exact retainer envelope / root hot-fit acceptance",
                        arrangement["space"]["exact_retainer_envelope_and_root_hot_fit"],
                        "1",
                        "unavailable",
                    ),
                ],
            }
        )
    return result


def _recovery(r: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    source = r["s3_config"]["recovery"]
    spec_parts = {p["id"]: p for p in r["source_spec"]["parts"]}
    config_id = base["identity"]["configuration_id"]
    nodes = []
    packed = [
        "nose_cone",
        "parachute",
        "shock_cord",
        "recovery_protection",
        "recovery_bulkhead",
        "recovery_anchor",
    ]
    for pid in packed:
        part = spec_parts[pid]
        geometry = part["geometry"]
        length = geometry.get("length_m", geometry.get("bbox_m", [0])[0])
        nodes.append(
            _node(
                pid,
                pid.replace("_", " "),
                [pid],
                ["source_spec"],
                "Saved packing envelope only; extraction, folding, retention and deployment are unverified",
                "estimated",
                quantities=[
                    _quantity("Envelope front station", part["position_m"] * 1000, "mm"),
                    _quantity("Envelope axial length", length * 1000, "mm"),
                ],
            )
        )
    nodes += [
        _node(
            "junction",
            "Connector / forward backbone junction",
            ["S3_connector", "recovery_backbone_extra_mass"],
            ["s3_config", "source_lock"],
            "No finished hot multileg/connector capacity or equal sharing",
            quantities=[_quantity("Junction station", source["primary_junction_station_mm"], "mm")],
        ),
        _node(
            "fore_cap",
            "Fore saddles / cap",
            ["fore_integral_G11_annular_cap"],
            ["source_lock"],
            "Actual saddle contact and cap joints unqualified",
        ),
        _node(
            "aft_cap",
            "Aft saddles / independent service cap",
            ["C1_aft_cap_15p8_bore"],
            ["source_lock"],
            "Independent motor removal must retain this cap and harness",
        ),
        _node(
            "receiver",
            "Continuous receiver and end/body joints",
            ["C1_closed_G11_body_annulus", "fore_integral_body_skirt"],
            ["source_lock"],
            "Finite end/body/paper branches unresolved; no all-paper load assumption",
        ),
    ]
    edges = [
        _edge(
            "canopy-cord",
            "parachute",
            "shock_cord",
            "Canopy lines to shock cord",
            ["parachute", "shock_cord"],
            ["source_spec"],
            "Routing/finished joint capacity unavailable",
        ),
        _edge(
            "cord-junction",
            "shock_cord",
            "junction",
            "Forward backbone",
            ["shock_cord", "recovery_backbone_extra_mass"],
            ["source_lock", "s3_config"],
            "Exact complete routing and upper/nose restraint remain unqualified",
        ),
        _edge(
            "cap-receiver",
            "aft_cap",
            "receiver",
            "Cap/end contact and retention",
            ["C1_aft_cap_15p8_bore", "C1_closed_G11_body_annulus"],
            ["source_lock", "attachment_record"],
            "Single-M3 full opening demand fails provisional screen; branch fractions unknown",
            "failed",
        ),
        _edge(
            "fore-receiver",
            "fore_cap",
            "receiver",
            "Fore cap / windowed skirt / body",
            ["fore_integral_G11_annular_cap", "fore_integral_body_skirt"],
            ["source_lock"],
            "Actual hot contact, paper crushing and peel unknown",
        ),
        _edge(
            "upper-anchor",
            "shock_cord",
            "recovery_anchor",
            "Upper / nose restraint branch",
            ["recovery_anchor"],
            ["source_spec"],
            "Branch topology illustration; no assumed full force or load split",
        ),
        _edge(
            "bulkhead-anchor",
            "recovery_anchor",
            "recovery_bulkhead",
            "Anchor and bulkhead attachment",
            ["recovery_anchor", "recovery_bulkhead"],
            ["source_spec"],
            "Actual attachment capacity/upper-body transfer not qualified",
        ),
    ]
    for i in range(source["closed_loops_count"]):
        pid = f"raw_Bally_2745_loop_{i}"
        nodes.append(
            _node(
                pid,
                f"Sewn loop {i+1}; two legs",
                [pid],
                ["s3_config", "source_lock"],
                "Raw webbing rating is not finished seam/chafe/hot dynamic capacity",
                quantities=[
                    _quantity("Webbing width", source["width_mm"], "mm"),
                    _quantity("Azimuth", source["loop_azimuths_deg"][i], "deg"),
                    _quantity(
                        "Finished hot endpoint capacity",
                        source["finished_eye_seam_hot_dynamic_capacity_n"],
                        "N",
                        "unavailable",
                    ),
                ],
            )
        )
        for end in ("fore_cap", "aft_cap"):
            edges.append(
                _edge(
                    f"{pid}-{end}",
                    pid,
                    end,
                    "Loop saddle contact",
                    [pid],
                    ["s3_config"],
                    "No equal loop or leg force sharing; seam/contact capacity unavailable",
                )
            )
        edges.append(
            _edge(
                f"junction-{pid}",
                "junction",
                pid,
                "Multileg connector branch",
                [pid, "S3_connector"],
                ["s3_config"],
                "Actual branch forces remain unknown",
            )
        )
    return {
        "topology": _graph(
            "recovery",
            "Recovery backbone, three loop branches and packing envelopes",
            nodes,
            edges,
            ["source_lock", "source_spec", "s3_config"],
            "Illustrated topology is not a solved deployment, branch-force or packing model",
            config_id,
        ),
        "opening_assumptions": [
            _quantity("Nominal descent/opening speed", source["nominal_velocity_mps"], "m/s"),
            _quantity("Severe opening speed", source["severe_velocity_mps"], "m/s"),
            _quantity("Stopping distance", source["stopping_travel_m"], "m"),
            _quantity("Design factor applied once", source["design_factor"], "1"),
            _quantity(
                "Source canopy diameter", r["source_spec"]["recovery"]["canopy_diameter_m"], "m"
            ),
            _quantity(
                "Source canopy drag coefficient",
                r["source_spec"]["recovery"]["drag_coefficient"],
                "1",
            ),
            _quantity("Source trigger lag", r["source_spec"]["recovery"]["trigger_lag_s"], "s"),
        ],
        "packing_steps": [
            _step(
                "packing-envelope",
                "Locate recorded packed envelopes",
                "Show parachute, cord and protection at saved source stations; folded volume and extraction forces are not specified.",
                packed,
                ["source_spec"],
                "estimated",
            ),
            _step(
                "packing-power",
                "Keep independent recovery power and arming accessible",
                "Source keeps a separate recovery battery, switch, controller and output harness. Actual routing, arming access and snag-free packing require physical verification.",
                [
                    "independent_recovery",
                    "recovery_battery",
                    "recovery_power_switch",
                    "recovery_output_harness",
                ],
                ["source_spec"],
                "estimated",
            ),
            _step(
                "packing-stop",
                "Packing acceptance unavailable",
                "No qualified fold, ejection pressure, nose retention, cord routing or deployment/extraction result is supplied.",
                packed,
                ["source_spec", "source_lock"],
            ),
        ],
        "extraction_steps": [
            _step(
                "extraction-upper",
                "Upper separation illustration",
                "Follow the saved nose/recovery separation arrangement; motion, retention and actual extraction are unverified.",
                ["nose_cone", "parachute", "shock_cord"],
                ["source_spec"],
            ),
            _step(
                "extraction-motor",
                "Motor service remains a separate operation",
                "Remove independent keeper arms then motor through proposed cap bore while retaining the recovery cap and loops; this is a sourced service illustration, not validated access.",
                ["C1_independent_motor_retainer_arm_1", "C1_aft_cap_15p8_bore", "motor"],
                ["source_lock"],
            ),
        ],
        "notes": [
            "Opening demand is a complete-mass energy-equivalent mean, not a measured peak",
            "Per-candidate opening forces are copied in candidate_comparison; they must not be reused at a different mass",
            "Three loops/two legs do not establish equal sharing",
            "G54/G12/new candidates have no inherited physical recovery acceptance",
        ],
    }


def _thermal(r: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    old = r["historical_thermal_topology"]
    old_sid = ["historical_thermal_topology"]
    ids = list(old["part_ids"])
    nodes = [
        _node(
            pid,
            pid.replace("_", " "),
            [],
            old_sid,
            "Historical model component identity, not a current C1 spatial mapping",
            "historical",
        )
        for pid in ids
    ]
    edges = []
    for category in ("direct_contact_pairs", "contact_pairs"):
        for index, (start, end) in enumerate(old[category]):
            edges.append(
                _edge(
                    f"{category}-{index}",
                    start,
                    end,
                    category.replace("_", " "),
                    [],
                    old_sid,
                    "Exact saved topology pair; conductance estimates belong to historical configuration only",
                    "historical",
                )
            )
    present = {p["id"]: p for p in base["parts"]}
    interface_pairs = [
        ("motor", "thrust_pads"),
        ("motor", "aft_thrust_pads"),
        ("motor_liner", "motor_radiant_shield"),
        ("C1_fin_socket_side_plate_1", "C1_closed_G11_body_annulus"),
        ("C1_closed_G11_body_annulus", "fore_integral_G11_annular_cap"),
        ("fore_integral_body_skirt", "aft_shell"),
    ]
    current_ids = sorted({pid for pair in interface_pairs for pid in pair})
    current_nodes = [
        _node(
            pid,
            present[pid]["label"],
            [pid],
            ["source_lock", "source_spec"],
            "Identified interface component; no compatible C1 local temperature",
            quantities=[_quantity("Local C1 temperature", None, "degC", "unavailable")],
        )
        for pid in current_ids
    ]
    current_edges = [
        _edge(
            f"current-interface-{i}",
            start,
            end,
            "Unqualified C1 interface / heat path",
            [start, end],
            ["source_lock", "source_spec"],
            "Interface identification only; contact area, conductance, bypass and local hot spots not qualified",
            quantities=[_quantity("Qualified contact conductance", None, "W/K", "unavailable")],
        )
        for i, (start, end) in enumerate(interface_pairs)
    ]
    materials = []
    material_units = {
        "density_kg_m3": "kg/m3",
        "cp_j_kg_k": "J/(kg K)",
        "conductivity_w_m_k": "W/(m K)",
        "limit_c": "degC",
        "surface_emissivity": "1",
    }
    for mid, properties in r["historical_thermal_materials"]["materials"].items():
        pids = (
            [p["id"] for p in base["parts"] if p["material"].split(";")[0].lower() == mid.lower()]
            if mid != "commercial"
            else []
        )
        materials.append(
            {
                "id": mid,
                "label": mid,
                "state": "estimated",
                "part_ids": pids,
                "source_ids": ["historical_thermal_materials"],
                "note": properties["basis"],
                "properties": [
                    _quantity(key.replace("_", " "), properties[key], unit)
                    for key, unit in material_units.items()
                    if key in properties
                ],
            }
        )
    s3 = r["s3_config"]
    cap = s3["end_caps"]
    service = r["source_lock"]["c1_selected_dimensions_from_frozen_config"][
        "independent_motor_service"
    ]
    openings = [
        {
            "id": "service-ports",
            "label": "Retained pin service ports through paper shell",
            "state": "estimated",
            "part_ids": ["aft_shell", "service_port_covers"],
            "source_ids": ["s3_config", "source_lock"],
            "note": s3["service_ports"]["note"],
            "dimensions": [
                _quantity("Port count", s3["service_ports"]["shell_ports_count"], "1"),
                _quantity("Port diameter", s3["service_ports"]["diameter_mm"], "mm"),
            ]
            + [
                _quantity(f"Axial station {i+1}", value, "mm")
                for i, value in enumerate(s3["service_ports"]["axial_stations_mm"])
            ],
        },
        {
            "id": "strap-slots",
            "label": "Cap strap-leg slots",
            "state": "estimated",
            "part_ids": ["fore_integral_G11_annular_cap", "C1_aft_cap_15p8_bore"],
            "source_ids": ["s3_config", "source_lock"],
            "note": "Saved geometric openings; no removed-mass credit or validated view factor",
            "dimensions": [
                _quantity("Count per cap", cap["strap_leg_slots"]["count_per_cap"], "1"),
                _quantity(
                    "Slot radial length",
                    cap["strap_leg_slots"]["radial_length_tangential_width_mm"][0],
                    "mm",
                ),
                _quantity(
                    "Slot tangential width",
                    cap["strap_leg_slots"]["radial_length_tangential_width_mm"][1],
                    "mm",
                ),
            ],
        },
        {
            "id": "skirt-windows",
            "label": "Fore-skirt bight-clearance windows",
            "state": "estimated",
            "part_ids": ["fore_integral_body_skirt"],
            "source_ids": ["s3_config", "source_lock"],
            "note": cap["fore_integral_body_skirt"]["bight_clearance_windows"]["note"],
            "dimensions": [
                _quantity(
                    "Window front",
                    cap["fore_integral_body_skirt"]["bight_clearance_windows"]["start_end_mm"][0],
                    "mm",
                ),
                _quantity(
                    "Window aft",
                    cap["fore_integral_body_skirt"]["bight_clearance_windows"]["start_end_mm"][1],
                    "mm",
                ),
                _quantity(
                    "Removed circumference fraction",
                    cap["fore_integral_body_skirt"]["bight_clearance_windows"][
                        "removed_circumference_fraction"
                    ],
                    "1",
                ),
            ],
        },
        {
            "id": "motor-passage",
            "label": "C1 independent motor passage",
            "state": "estimated",
            "part_ids": ["C1_aft_cap_15p8_bore", "motor"],
            "source_ids": ["source_lock"],
            "note": "Bore proposal, not verified nozzle passage or hot service; no radiant closure implied",
            "dimensions": [_quantity("Bore radius", service["aft_cap_bore_radius_mm"], "mm")],
        },
    ]
    history = []
    layout = r["historical_thermal_layout"]["sources"]["pre_baffle_proxy"]
    for index, row in enumerate(layout["rows"]):
        worst = row["worst"]
        history.append(
            {
                "id": f"historical-proxy-{index}",
                "label": f"{row['case']['id']} / {row['corner']['id']} / {row['end_mode']}",
                "state": "superseded",
                "configuration_id": layout["matrix_scope"],
                "candidate_identity": layout["candidate_identity"],
                "cad_revision": layout["cad_revision_sha256"],
                "compatible_with_c1": False,
                "kind": "historical_scalar_screen",
                "source_ids": ["historical_thermal_layout"],
                "note": f"Historical G54 coaxial proxy worst mean: {worst['part_id']}; local actual geometry and C1 incompatible. A prior passing scalar does not transfer. No time-series samples exported.",
                "metrics": [
                    _quantity(
                        "Worst recorded part mean peak", worst["peak_c"], "degC", "superseded"
                    ),
                    _quantity("Peak time", worst["peak_time_s"], "s", "superseded"),
                    _quantity("Provisional screen", worst["screen_limit_c"], "degC", "superseded"),
                    _quantity("Saved margin", worst["margin_k"], "K", "superseded"),
                ],
            }
        )
    campaign = r["historical_thermal_campaign"]
    for cid, rows in campaign["cases"].items():
        for row in rows:
            history.append(
                {
                    "id": f"elmer-{cid}-{row['level']}",
                    "label": f"Elmer known fixture {cid}, level {row['level']}",
                    "state": (
                        "failed"
                        if not row["absolute_field_within_existing_1e-7K"]
                        else "historical"
                    ),
                    "configuration_id": f"analytic_fixture_{cid}",
                    "candidate_identity": None,
                    "cad_revision": None,
                    "compatible_with_c1": False,
                    "kind": "solver_verification",
                    "source_ids": ["historical_thermal_campaign"],
                    "note": row["scope"]
                    + "; actual-baffle campaign closed unqualified; null balances stay unavailable, no field/time history exported",
                    "metrics": [
                        _quantity(
                            "Maximum nodal temperature error",
                            row["max_nodal_error_k"],
                            "K",
                            "calculated",
                        ),
                        _quantity(
                            "Exact-field criterion",
                            campaign["criteria"]["temperature_absolute_tolerance_k"],
                            "K",
                            "estimated",
                        ),
                        _quantity("Global balance", row["global_balance_w"], "W", "unavailable"),
                        _quantity("Local balance", row["local_balance_w"], "W", "unavailable"),
                    ],
                }
            )
    return {
        "topology": _graph(
            "historical-thermal",
            "Historical neutral coaxial model topology",
            nodes,
            edges,
            old_sid,
            "Saved historical contact list only; removed mount/TVC parts are not C1 geometry",
            old["version"],
            False,
            "historical",
        ),
        "current_interfaces": _graph(
            "c1-thermal-interfaces",
            "C1 interfaces requiring heat-path qualification",
            current_nodes,
            current_edges,
            ["source_lock", "source_spec"],
            "No compatible C1 thermal topology solution or spatial field",
            base["identity"]["configuration_id"],
        ),
        "materials": materials,
        "openings": openings,
        "history": history,
        "compatible_spatial_field": None,
        "notes": [
            "No current C1 temperatures, spatial maps or time-series curves are supplied",
            "Required burn/soak matrix including 300 degC case / dirty foil / 35 degC ambient and 45 degC substrate screen remains",
            "Historical G54/TVC/fixture results do not qualify C1, G80, G54 or G12 installed configurations",
            "Real seams, slots, ports, end exposure, finite contacts, directional properties and hot spots remain unqualified",
            "Closed Elmer campaign does not authorize another automatic thermal solve",
        ],
    }


def _electrical(r: dict[str, Any], base: dict[str, Any]) -> dict[str, Any]:
    saved = r["source_spec"]["netlist"]
    pids = {net["from"] for net in saved} | {
        pid for net in saved for pid in (net["to"] if isinstance(net["to"], list) else [net["to"]])
    }
    nodes = [
        _node(
            pid,
            pid.replace("_", " "),
            [pid],
            ["source_spec"],
            "Saved component/net identity; physical wiring/pins and qualification unresolved",
            "estimated",
        )
        for pid in sorted(pids)
    ]
    nets, edges = [], []
    for index, net in enumerate(saved):
        targets = net["to"] if isinstance(net["to"], list) else [net["to"]]
        nets.append(
            {
                "id": f"net-{index}",
                **net,
                "to": targets,
                "state": "estimated",
                "part_ids": [net["from"], *targets],
                "source_ids": ["source_spec"],
                "note": "Exact source net. Null gauge/pin remains unspecified; no extra return, continuity or isolation path invented.",
            }
        )
        for target in targets:
            edges.append(
                _edge(
                    f"net-{index}-{target}",
                    net["from"],
                    target,
                    net["net"],
                    [net["from"], target],
                    ["source_spec"],
                    "Source connectivity only; net labels do not validate physical implementation",
                    "estimated",
                    [
                        _quantity(
                            "Recorded wire gauge",
                            net["gauge_awg"],
                            "AWG",
                            "estimated" if net["gauge_awg"] is not None else "unavailable",
                        )
                    ],
                )
            )
    planned = [
        _node(
            "sensors",
            "Sensor / estimator model",
            ["imu", "baro", "high_g_accel"],
            ["source_spec"],
            "Planned later-WO calibrated estimation/control path; not C1 controller validation",
        ),
        _node(
            "pid",
            "PID baseline (planned WO-06)",
            [],
            ["pid_work_order"],
            "Committed later work; no controller result supplied",
        ),
        _node(
            "rl",
            "RL comparison (planned WO-07)",
            [],
            ["rl_work_order"],
            "Committed later work; no trained-policy performance supplied",
        ),
        _node(
            "abort",
            "Independent firmware abort / recovery gates",
            ["independent_recovery"],
            ["source_spec", "firmware_work_order"],
            "WO-10 owner firmware/abort review remains required; source arming intent is not accepted firmware",
        ),
        _node(
            "actuation",
            "G12 TVC actuation (separate mode)",
            [],
            ["source_spec"],
            "Current C1 G80 is fixed-motor; no servos or gimbal adopted here",
        ),
    ]
    control_edges = [
        _edge(
            "sensor-pid",
            "sensors",
            "pid",
            "Planned control input",
            [],
            ["source_spec"],
            "Functional plan only",
        ),
        _edge(
            "sensor-rl",
            "sensors",
            "rl",
            "Planned comparison input",
            [],
            ["source_spec"],
            "Functional plan only",
        ),
        _edge(
            "pid-abort",
            "pid",
            "abort",
            "Planned command supervision",
            [],
            ["source_spec"],
            "No accepted firmware/abort implementation follows",
        ),
        _edge(
            "rl-abort",
            "rl",
            "abort",
            "Planned command supervision",
            [],
            ["source_spec"],
            "No accepted policy/abort implementation follows",
        ),
        _edge(
            "abort-actuation",
            "abort",
            "actuation",
            "Separate G12 control track",
            [],
            ["source_spec"],
            "No fixed-motor C1 actuation path",
        ),
    ]
    return {
        "topology": _graph(
            "electrical-nets",
            "Source netlist and separate recovery power",
            nodes,
            edges,
            ["source_spec"],
            "Logical connectivity; pin assignment, measured continuity, isolation and final wiring remain unresolved",
            base["identity"]["configuration_id"],
            True,
            "estimated",
        ),
        "nets": nets,
        "power_independence": [
            "Main battery→regulator→flight computer remains separate from recovery battery→recovery power switch→independent recovery controller",
            "RECOVERY_RETURN is preserved exactly as the saved recovery-battery/controller net; no shared main-ground connection is introduced",
            "Independent supply topology is a source design intent, not measured electrical independence or an accepted deployment circuit",
            "All source pin fields are null; no pin mapping invented",
        ],
        "control_blocks": _graph(
            "planned-control",
            "Planned PID-to-RL / abort blocks; separate G12 modes",
            planned,
            control_edges,
            ["source_spec", "pid_work_order", "rl_work_order", "firmware_work_order"],
            "Later work-order plan only; C1 is fixed-motor and this is not executable wiring or validated control",
            "separate_G12_control_track",
            False,
        ),
    }


def build_workbench_extended(root: Path = ROOT) -> dict[str, Any]:
    """Read and prepare one extension document, failing on source identity drift."""
    try:
        mapping, r, base, sources = _load(root)
        assembly_steps = [
            _step(
                f"{joint['id']}-{i}",
                f"{joint['label']} · illustration {i+1}",
                text,
                joint["part_ids"],
                joint["source_ids"],
                "estimated",
            )
            for joint in base["joints"]
            for i, text in enumerate(joint["assembly_steps"])
        ]
        req_nodes, req_edges = [], []
        for gap in base["gaps"]:
            req_nodes.append(
                _node(
                    gap["id"],
                    gap["label"],
                    gap["part_ids"],
                    gap["source_ids"],
                    gap["next_verification"],
                    gap["state"],
                    kind="requirement",
                )
            )
            for pid in gap["part_ids"]:
                nid = f"part:{pid}"
                if not any(n["id"] == nid for n in req_nodes):
                    part = next(p for p in base["parts"] if p["id"] == pid)
                    req_nodes.append(
                        _node(
                            nid,
                            part["label"],
                            [pid],
                            part["source_ids"],
                            part["function"],
                            part["state"],
                            kind="part",
                        )
                    )
                req_edges.append(
                    _edge(
                        f"{gap['id']}:{pid}",
                        gap["id"],
                        nid,
                        "Requirement applies to component",
                        [pid],
                        gap["source_ids"],
                        "Open requirement link, not closure evidence",
                        gap["state"],
                    )
                )
            for sid in gap["source_ids"]:
                nid = f"source:{sid}"
                if not any(n["id"] == nid for n in req_nodes):
                    src = next(s for s in sources if s["id"] == sid)
                    req_nodes.append(
                        _node(
                            nid,
                            src["description"],
                            [],
                            [sid],
                            src["path"],
                            "historical",
                            kind="evidence",
                        )
                    )
                req_edges.append(
                    _edge(
                        f"{gap['id']}:{sid}",
                        gap["id"],
                        nid,
                        "Recorded evidence / remaining finding",
                        gap["part_ids"],
                        [sid],
                        "Recorded source does not grant physical acceptance",
                        gap["state"],
                    )
                )
        document = {
            "schema_version": mapping["schema_version"],
            "id": mapping["id"],
            "label": mapping["label"],
            "status": "Read-only recorded extension; no new candidate adoption, thermal/stress field, build or flight acceptance",
            "identity": base["identity"],
            "generated_from": sources,
            "candidate_comparison": _candidates(r, base),
            "recovery": _recovery(r, base),
            "thermal": _thermal(r, base),
            "electrical": _electrical(r, base),
            "assembly": {
                "joints": base["joints"],
                "steps": assembly_steps,
                "notes": [
                    "Copied source service illustrations; no validated insertion, continuous sweep, tool access or maintenance release",
                    "C3 node/arm interference is a failed preflight, not a new assembly instruction",
                ],
            },
            "requirements": _graph(
                "physical-requirements",
                "Physical requirements, components and recorded findings",
                req_nodes,
                req_edges,
                ["source_lock", "attachment_record", "source_c3"],
                "All engineering/build/paid/WO-10/flight gates remain; numerical screens are distinct from physical qualification",
                base["identity"]["configuration_id"],
            ),
        }
        # Projection integrity only: all interactive component/source links resolve.
        part_ids = {p["id"] for p in base["parts"]}
        source_ids = {s["id"] for s in sources}

        def validate(value: Any) -> None:
            if isinstance(value, dict):
                if "part_ids" in value and any(pid not in part_ids for pid in value["part_ids"]):
                    raise WorkbenchUnavailable(
                        f"Unknown extension component link: {value.get('id')}"
                    )
                if "source_ids" in value and any(
                    sid not in source_ids for sid in value["source_ids"]
                ):
                    raise WorkbenchUnavailable(
                        f"Unknown extension evidence link: {value.get('id')}"
                    )
                if "nodes" in value and "edges" in value:
                    node_ids = {n["id"] for n in value["nodes"]}
                    if any(
                        e["from"] not in node_ids or e["to"] not in node_ids for e in value["edges"]
                    ):
                        raise WorkbenchUnavailable(f"Disconnected extension graph: {value['id']}")
                for child in value.values():
                    validate(child)
            elif isinstance(value, list):
                for child in value:
                    validate(child)

        validate(document)
        return document
    except WorkbenchUnavailable:
        raise
    except (OSError, ValueError, KeyError, TypeError, StopIteration, yaml.YAMLError) as error:
        raise WorkbenchUnavailable(
            f"Extended workbench source contract invalid: {error}"
        ) from error
