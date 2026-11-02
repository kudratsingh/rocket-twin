"""Read-only, versioned presentation of the frozen C1 engineering records.

No CAD, solver, simulator or vehicle-model import belongs here. Arithmetic is
limited to unit conversion and ledger reconciliation of recorded values. These
schematics describe preliminary interfaces, never admission of detailed C1 CAD.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAPPING = "configs/engineering/workbench.yaml"


class WorkbenchUnavailable(ValueError):
    """An unavailable or changed frozen input must not produce partial evidence."""


def _read(root: Path, relative: str) -> bytes:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise WorkbenchUnavailable(f"Source path escapes repository: {relative}")
    try:
        return path.read_bytes()
    except OSError as error:
        raise WorkbenchUnavailable(f"Required workbench source unavailable: {relative}") from error


def _sources(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    mapping_bytes = _read(root, MAPPING)
    mapping = yaml.safe_load(mapping_bytes)
    records: dict[str, Any] = {}
    manifest: list[dict[str, Any]] = []
    for source_id, entry in mapping["sources"].items():
        raw = _read(root, entry["path"])
        digest = hashlib.sha256(raw).hexdigest()
        if digest != entry["sha256"]:
            raise WorkbenchUnavailable(f"Frozen source hash mismatch: {entry['path']}")
        manifest.append({"id": source_id, **entry})
        if entry["path"].endswith(".json"):
            records[source_id] = json.loads(raw)
        elif entry["path"].endswith(".yaml"):
            records[source_id] = yaml.safe_load(raw)
    manifest.append(
        {
            "id": "presentation_mapping",
            "path": MAPPING,
            "sha256": hashlib.sha256(mapping_bytes).hexdigest(),
            "description": "Versioned presentation mapping; no new physical data",
        }
    )
    # Export code is part of the source manifest as well as the frozen records.
    code_path = "src/api/workbench.py"
    manifest.append(
        {
            "id": "exporter",
            "path": code_path,
            "sha256": hashlib.sha256(_read(root, code_path)).hexdigest(),
            "description": "Read-only exporter implementation",
        }
    )
    audit = records["connection_audit"]
    attachment_sha = mapping["sources"]["attachment_record"]["sha256"]
    if audit["source_record_sha256"] != attachment_sha:
        raise WorkbenchUnavailable("Connection audit does not identify the attachment record")
    for source_id, entry in records["source_lock"]["version_identity"]["files"].items():
        # Verify the actual frozen files consumed by this export. Other archived
        # scripts remain identified in the source lock, without requiring a solver checkout.
        matching = [x for x in manifest if x["path"] == entry["path"]]
        if matching and matching[0]["sha256"] != entry["sha256"]:
            raise WorkbenchUnavailable(f"Source lock identity mismatch: {source_id}")
    return mapping, records, manifest


def _subsystem(part_id: str) -> str:
    if "guide" in part_id or "rail_button" in part_id:
        return "launch"
    if any(x in part_id for x in ("fin", "cheek", "shim_stock")):
        return "fins"
    if any(x in part_id for x in ("motor", "thrust", "thermal", "radiant")):
        return "propulsion"
    if any(x in part_id for x in ("recovery", "loop", "saddle", "parachute", "shock", "canopy")):
        return "recovery"
    if part_id in {
        "avionics_bay",
        "flight_computer",
        "imu",
        "baro",
        "battery",
        "regulator_5v",
        "pyro_mosfet",
        "arming_switch",
        "harness",
        "high_g_accel",
        "micro_sd",
    }:
        return "avionics"
    if any(
        x in part_id
        for x in ("receiver", "C1_", "cap_", "skirt", "body_", "aft_shell", "coupler", "joint")
    ):
        return "structure"
    return "airframe"


def _part(part_id: str, **values: Any) -> dict[str, Any]:
    return {
        "id": part_id,
        "label": part_id.replace("_", " "),
        "source_part_ids": [part_id],
        "subsystem": _subsystem(part_id),
        "function": "Retained component or explicit allocation",
        "material": "Not specified for this allocated item",
        "manufacturing": "Unselected / unbuilt",
        "mass_g": None,
        "mass_basis": "Unavailable",
        "geometry_maturity": "undefined",
        "state": "estimated",
        "shape": "envelope",
        "start_mm": None,
        "length_mm": None,
        "radius_mm": None,
        "source_ids": ["source_lock"],
        "connections": [],
        "findings": [],
        **values,
    }


def _parts_and_distribution(r: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    lock = r["source_lock"]
    spec = r["source_spec"]
    ledger = lock["resolved_mass_ledger_application"]
    accounting = r["c1_record"]["fin_panel_accounting"]
    removed = r["s3_record"]["removed_source_parts_g"]
    parts: list[dict[str, Any]] = []
    distribution: list[dict[str, Any]] = []

    def append(part: dict[str, Any], station: float) -> None:
        parts.append(part)
        distribution.append(
            {
                "id": part["id"],
                "label": part["label"],
                "station_mm": station,
                "mass_g": part["mass_g"],
                "subsystem": part["subsystem"],
                "state": part["state"],
                "part_id": part["id"],
            }
        )

    for source in spec["parts"]:
        pid = source["id"]
        if pid in removed:
            continue
        geo = source["geometry"]
        bbox = geo.get("bbox_m")
        length = geo.get("length_m", bbox[0] if bbox else None)
        mass = source["mass_kg"] * 1000
        # The rectangular panel alone is replaced; gussets/original-tab CAD
        # residual remains once, separately from the retained S3 tab-depth delta.
        if pid == "fin_set":
            append(
                _part(
                    "fin_source_cad_residual",
                    label="Retained original fin tabs / gusset residual",
                    source_part_ids=[pid],
                    mass_g=accounting["original_fin_CAD_residual_retained_g"],
                    mass_basis="Original fin-set CAD mass minus rectangular panel mass only",
                    function="Retained original fin attachment stock; not a second panel",
                    source_ids=["c1_record"],
                    findings=["Residual detailed shape is unavailable for C1"],
                ),
                accounting["original_fin_centroid_mm"],
            )
            continue
        shape = "box" if bbox else "shell"
        if pid == "motor":
            shape = "motor"
        elif "cord" in pid or pid == "harness":
            shape = "harness"
        part = _part(
            pid,
            label=pid.replace("_", " "),
            function=(source.get("engineering") or {}).get("function", source["learn"]),
            material=source["material"],
            manufacturing=(source.get("build") or {}).get("method", "Unselected"),
            mass_g=mass,
            mass_basis="Frozen source-73 mass input; estimate/CAD-derived input, not measured C1",
            geometry_maturity="envelope",
            shape=shape,
            start_mm=source["position_m"] * 1000,
            length_mm=length * 1000 if length is not None else None,
            radius_mm=geo.get("radius_m", 0) * 1000 if "radius_m" in geo else None,
            inner_radius_mm=(
                geo.get("inner_radius_m", 0) * 1000 if "inner_radius_m" in geo else None
            ),
            thickness_mm=geo.get("wall_m", 0) * 1000 if "wall_m" in geo else None,
            source_ids=["source_spec", "source_lock"],
            findings=["Retained source envelope; complete C1 CAD revision unavailable"],
        )
        if pid == "rail_guides":
            part.update(
                label="Original rod lugs (not rail buttons)",
                findings=[
                    "3.4 mm rod bores; retained old-lug geometry. Actual supported launch hardware unconfirmed."
                ],
            )
        if pid == "motor":
            part["findings"].append(
                "Exact purchased variant, nozzle/case tolerances and installed CG remain unverified"
            )
        append(part, (source["position_m"] + source["cg_offset_m"]) * 1000)

    for row in (
        ledger["source_s3_custom_component_rows_retained"] + ledger["c1_added_component_rows"]
    ):
        append(
            _part(
                row["id"],
                mass_g=row["mass_g"],
                mass_basis=row["basis"],
                function=row.get("function", row["basis"]),
                findings=[
                    f"Source field: {row['source_config_field']}",
                    "Budget/geometry estimate, not installed qualification",
                ],
            ),
            row["station_mm"],
        )

    fin = lock["fin_geometry"]["selected_proposed_geometry_mm"]
    append(
        _part(
            "c1_fin_panels",
            label="Three swept/tapered C1 plywood fin panels",
            source_part_ids=["fin_set"],
            subsystem="fins",
            material="Plywood; estimated 715 kg/m³ profile",
            manufacturing="Cut; grain/hot properties unqualified",
            mass_g=accounting["new_panel_mass_g"],
            mass_basis="Recorded trapezoid integration; replaces rectangular panels once",
            function="Aerodynamic restoring force; carries bending into captured tab/socket",
            geometry_maturity="envelope",
            state="failed",
            shape="fin",
            start_mm=fin["station"],
            length_mm=fin["root"],
            radius_mm=spec["airframe"]["body_diameter_m"] * 500,
            span_mm=fin["span"],
            root_chord_mm=fin["root"],
            tip_chord_mm=fin["tip"],
            sweep_mm=fin["sweep"],
            thickness_mm=fin["thickness"],
            azimuth_deg=[0, 120, 240],
            source_ids=["source_lock", "attachment_record", "connection_audit"],
            connections=["fin_root"],
            findings=[
                "Hot ideal-root panel motion exceeds installed 1 mm target; flutter unavailable"
            ],
        ),
        accounting["new_panel_centroid_mm"],
    )

    dimensions = lock["c1_selected_dimensions_from_frozen_config"]
    receiver = dimensions["receiver_replacement"]["closed_g11_body_annulus"]
    caps = lock["source_s3_dimensions_retained_or_referenced"]["caps_and_body_interfaces"]
    for part in parts:
        pid = part["id"]
        if pid == "C1_closed_G11_body_annulus":
            part.update(
                label="C1 continuous closed receiver",
                material="G11; estimated profile",
                geometry_maturity="envelope",
                shape="shell",
                start_mm=receiver["start_end_mm"][0],
                length_mm=receiver["start_end_mm"][1] - receiver["start_end_mm"][0],
                radius_mm=receiver["inner_outer_radius_mm"][1],
                inner_radius_mm=receiver["inner_outer_radius_mm"][0],
                thickness_mm=receiver["thickness_mm"],
                connections=["fin_root", "receiver_end", "motor_service"],
                state="failed",
            )
            part["findings"].append(
                "Slotted laminate buckling, hot properties and actual finite end connections remain open"
            )
        elif pid in {"fore_integral_G11_annular_cap", "C1_aft_cap_15p8_bore"}:
            aft = pid.startswith("C1_")
            service = dimensions["independent_motor_service"]
            part.update(
                geometry_maturity="envelope",
                shape="ring",
                material="G11; estimated profile",
                start_mm=caps["front_stations_mm"][int(aft)],
                length_mm=caps["thickness_mm"],
                radius_mm=caps["outer_radius_mm"],
                inner_radius_mm=(
                    service["aft_cap_bore_radius_mm"] if aft else caps["source_bore_radius_mm"]
                ),
                connections=["receiver_end", "recovery_endpoint"],
            )
        elif pid == "fore_integral_body_skirt":
            start, end = caps["fore_body_skirt_start_end_mm"]
            inner, outer = caps["fore_skirt_inner_outer_radius_mm"]
            part.update(
                geometry_maturity="envelope",
                shape="shell",
                material="G11; estimated profile",
                start_mm=start,
                length_mm=end - start,
                radius_mm=outer,
                inner_radius_mm=inner,
                connections=["receiver_end"],
                findings=part["findings"]
                + ["Windowed skirt/body peel and paper crushing unavailable"],
            )
        elif pid.startswith(("C1_fin_socket_", "C1_radial_mount_pad_")):
            part.update(
                geometry_maturity="concept",
                shape="box",
                material="G11; estimated profile",
                start_mm=1090,
                length_mm=100,
                radius_mm=None,
                connections=["fin_root"],
                state="failed",
            )
        elif "raw_Bally" in pid:
            part.update(
                geometry_maturity="concept",
                shape="harness",
                material="Bally 2745 aramid raw webbing",
                start_mm=1000,
                length_mm=None,
                radius_mm=24,
                connections=["recovery_endpoint"],
                findings=part["findings"]
                + ["Raw webbing rating is not finished sewn hot/chafe assembly capacity"],
            )

    growth = lock["identity"]["separate_growth"]
    distribution.append(
        {
            "id": "separate_growth",
            "label": "Separate full growth allowance (once)",
            "station_mm": growth["station_mm"],
            "mass_g": growth["mass_g"],
            "subsystem": "allowance",
            "state": "estimated",
            "part_id": None,
        }
    )
    nominal = math.fsum(x["mass_g"] for x in distribution if x["id"] != "separate_growth")
    expected = lock["identity"]["nominal_mass_excluding_separate_growth_g"]
    if not math.isclose(nominal, expected, abs_tol=1e-8):
        raise WorkbenchUnavailable(
            f"Complete C1 ledger does not reconcile: {nominal} != {expected} g"
        )
    full = math.fsum(x["mass_g"] for x in distribution)
    cg = math.fsum(x["mass_g"] * x["station_mm"] for x in distribution) / full
    if not math.isclose(cg, lock["identity"]["loaded_cg_mm"], abs_tol=1e-7):
        raise WorkbenchUnavailable("Complete C1 first moment does not reconcile")
    return parts, distribution


def _dimension(
    label: str, value: float | None, unit: str = "mm", state: str = "estimated"
) -> dict[str, Any]:
    return {"label": label, "value": value, "unit": unit, "state": state}


def _joints(r: dict[str, Any]) -> list[dict[str, Any]]:
    lock = r["source_lock"]
    dims = lock["source_s3_dimensions_retained_or_referenced"]
    fin = dims["fin_root_interface"]
    cap = dims["caps_and_body_interfaces"]
    service = lock["c1_selected_dimensions_from_frozen_config"]["independent_motor_service"]

    def material(label: str, thickness: float | None, pid: str) -> dict[str, Any]:
        return {
            "label": label,
            "material": "G11 estimated profile",
            "thickness_mm": thickness,
            "part_id": pid,
            "state": "estimated",
        }

    return [
        {
            "id": "fin_root",
            "label": "Fin tab, shims and closed socket",
            "kind": "fin_root",
            "part_ids": [
                "c1_fin_panels",
                "C1_fin_socket_side_plate_1",
                "C1_fin_socket_floor_1",
                "C1_fin_socket_outer_bridge_1",
                "C1_closed_G11_body_annulus",
            ],
            "description": "Opposing side contacts carry bending. Tangential pins stop axial loss; their axes do not replace the fin-normal bending path.",
            "state": "failed",
            "source_ids": [
                "source_lock",
                "attachment_config",
                "attachment_record",
                "connection_audit",
                "c2_record",
            ],
            "dimensions": [
                _dimension("Tab depth", fin["candidate_s3_deeper_tab_depth_mm"]),
                _dimension("Tab length", fin["tab_length_mm"]),
                _dimension("Pin station from nose", fin["axial_pin_stations_mm"][0]),
                _dimension("Pin diameter", 5),
                _dimension(
                    "Socket contact radial depth", r["attachment_config"]["fin"]["contact_depth_mm"]
                ),
                _dimension("Socket centre radius", 24.3),
                _dimension("External root radius", 33),
                _dimension(
                    "C1 recorded 3.179 mm aggregate: superseded receiver-lever proxy",
                    r["connection_audit"]["structures"]["C1"][
                        "corrected_hot_panel_play_and_ideal_receiver_motion_m"
                    ]
                    * 1000,
                    state="superseded",
                ),
                _dimension(
                    "R1 recorded 1.039 mm aggregate: superseded receiver-lever proxy",
                    r["connection_audit"]["structures"]["R1"][
                        "corrected_hot_panel_play_and_ideal_receiver_motion_m"
                    ]
                    * 1000,
                    state="superseded",
                ),
                _dimension(
                    "Corrected calculated C1 aggregate scalar proxy; axis-radius conversion only",
                    r["c2_record"]["prior_receiver_radius_datum_correction"]["C1"][
                        "panel_socket_play_receiver_only_tip_m"
                    ]
                    * 1000,
                    state="failed",
                ),
                _dimension(
                    "Corrected calculated R1 aggregate scalar proxy; axis-radius conversion only",
                    r["c2_record"]["prior_receiver_radius_datum_correction"]["R1"][
                        "panel_socket_play_receiver_only_tip_m"
                    ]
                    * 1000,
                    state="failed",
                ),
                _dimension(
                    "Corrected calculated C1 receiver-only tip-motion scalar proxy",
                    r["c2_record"]["prior_receiver_radius_datum_correction"]["C1"][
                        "receiver_only_tip_m"
                    ]
                    * 1000,
                    state="calculated",
                ),
                _dimension(
                    "Corrected calculated R1 receiver-only tip-motion scalar proxy",
                    r["c2_record"]["prior_receiver_radius_datum_correction"]["R1"][
                        "receiver_only_tip_m"
                    ]
                    * 1000,
                    state="calculated",
                ),
                _dimension(
                    "Corrected rocket-axis-to-fin-tip radius for scalar conversion",
                    r["c2_record"]["prior_receiver_radius_datum_correction"]["C1"][
                        "rocket_axis_to_fin_tip_m"
                    ]
                    * 1000,
                    state="calculated",
                ),
                _dimension(
                    "C1 bridge minimum mean hot bond shear",
                    r["attachment_record"]["structures"]["C1"]["attachment"][
                        "cheek_to_bridge_min_mean_hot_bond_shear_pa"
                    ]
                    / 1e6,
                    "MPa",
                    "failed",
                ),
                _dimension(
                    "Stopped R1 bridge minimum mean hot bond shear",
                    r["attachment_record"]["structures"]["R1"]["attachment"][
                        "cheek_to_bridge_min_mean_hot_bond_shear_pa"
                    ]
                    / 1e6,
                    "MPa",
                    "failed",
                ),
                _dimension(
                    "Body-root moment; DF3 once",
                    r["attachment_record"]["load_case"]["moment_DF3_once_Nm"],
                    "N m",
                    "calculated",
                ),
                _dimension(
                    "Socket-centre moment; DF3 once",
                    r["attachment_record"]["structures"]["C1"]["attachment"][
                        "socket_center_moment_DF3_Nm"
                    ],
                    "N m",
                    "calculated",
                ),
                _dimension(
                    "Receiver rocket-axis torque; DF3 once",
                    r["connection_audit"]["structures"]["C1"]["rocket_axis_torque_DF3_once_Nm"],
                    "N m",
                    "calculated",
                ),
            ],
            "layers": [
                {
                    "label": "C1 plywood tab",
                    "material": "Plywood; hot direction unqualified",
                    "thickness_mm": 6.35,
                    "part_id": "c1_fin_panels",
                    "state": "estimated",
                },
                material("Opposing socket cheeks", 2, "C1_fin_socket_side_plate_1"),
                material("Socket floor", 2, "C1_fin_socket_floor_1"),
                material("Outer bridge", 2, "C1_fin_socket_outer_bridge_1"),
                {
                    "label": "Actual controlled bond/shim stack",
                    "material": "Unselected adhesive / shim",
                    "thickness_mm": None,
                    "part_id": "C1_socket_joint_process_hardware",
                    "state": "unavailable",
                },
            ],
            "findings": [
                "C2's saved datum correction replaces only the receiver-axis rotation-to-tip conversion: prior proxy used socket-to-tip 98.7 mm, corrected axis-to-tip radius is 123 mm. Original C1/R1 records remain unchanged. These calculated scalar proxies are not installed displacement fields or acceptance.",
                "Bridge estimated hot shear fails; peel and peak local pressure unavailable",
                "Paper slot is not an infinitely stiff clamp",
                "Retain existing shims and fin bonds in complete mass",
            ],
            "assembly_steps": [
                "Illustration only: fit tab through the paper shell slot into opposing socket cheeks.",
                "Illustrate controlled shim/contact fit, closed floor and bridge; leave undefined bond details visible.",
                "Illustrate tangential 5 mm captive axial-retention pin at 1180 mm, with keeper access.",
                "Verify actual hot contact, installed motion and flutter before construction release.",
            ],
        },
        {
            "id": "recovery_endpoint",
            "label": "Harness loops, cap saddles and endpoint",
            "kind": "recovery",
            "part_ids": [
                "raw_Bally_2745_loop_0",
                "fore_integral_G11_annular_cap",
                "C1_aft_cap_15p8_bore",
                "recovery_backbone_extra_mass",
            ],
            "description": "Protected aramid backbone joins three sewn loop candidates around cap saddles. Complete load sharing and upper/nose restraint remain unresolved.",
            "state": "unavailable",
            "source_ids": ["source_lock", "s3_config", "attachment_record"],
            "dimensions": [
                _dimension("Saddle radius", cap["saddle_radius_mm"]),
                _dimension("Saddle radial centre", cap["saddle_radial_center_mm"]),
                _dimension("Saddle radial width", cap["saddle_radial_width_mm"]),
                _dimension("Cap thickness", cap["thickness_mm"]),
                _dimension("Qualified sewn endpoint capacity", None, "N", "unavailable"),
            ],
            "layers": [
                {
                    "label": "Sewn loop candidate",
                    "material": "Bally 2745 aramid; raw rating only",
                    "thickness_mm": None,
                    "part_id": "raw_Bally_2745_loop_0",
                    "state": "unavailable",
                },
                material("Rounded cap saddle", None, "fore_integral_G11_annular_cap"),
            ],
            "findings": [
                "Single-M3 full-recovery tension exceeds provisional 200 MPa screen",
                "Finished sewn loop/chafe/hot contact capacity unavailable; no equal-sharing credit",
            ],
            "assembly_steps": [
                "Illustrate each loop around its rounded saddle, outside motor service volume.",
                "Show backbone continuing forward to the actual upper recovery connection.",
                "Show cap fasteners retained during independent motor removal.",
                "Qualify sewing, chafe, hot contact and complete load path; raw webbing strength is insufficient.",
            ],
        },
        {
            "id": "receiver_end",
            "label": "Receiver ends, cap joints and windowed body skirt",
            "kind": "receiver_end",
            "part_ids": [
                "C1_closed_G11_body_annulus",
                "fore_integral_G11_annular_cap",
                "fore_integral_body_skirt",
                "C1_integral_end_hardpoint_0_1",
                "fore_cap_M3_complete_set_0",
            ],
            "description": "Continuous receiver meets cap faces; integral end nodes carry barrel joints. Fore skirt transfers to the paper shell through real bonded/contact/retainer interfaces.",
            "state": "unavailable",
            "source_ids": ["source_lock", "connection_audit", "s3_config"],
            "dimensions": [
                _dimension("Fore barrel station", cap["barrel_nut_stations_mm"][0]),
                _dimension("Aft barrel station", cap["barrel_nut_stations_mm"][1]),
                _dimension("Screw bore", r["attachment_config"]["receiver"]["M3_bore_shaft_mm"][0]),
                _dimension("Screw shaft", 3),
                _dimension("Fore skirt start", cap["fore_body_skirt_start_end_mm"][0]),
                _dimension("Fore skirt end", cap["fore_body_skirt_start_end_mm"][1]),
                _dimension("Qualified body/skirt peel capacity", None, "N", "unavailable"),
            ],
            "layers": [
                material("C1 receiver wall", 0.8, "C1_closed_G11_body_annulus"),
                material("Integral cap", 6, "fore_integral_G11_annular_cap"),
                material("Fore body skirt", 1, "fore_integral_body_skirt"),
                {
                    "label": "Paper shell",
                    "material": "Cardboard",
                    "thickness_mm": 0.5,
                    "part_id": "aft_shell",
                    "state": "estimated",
                },
            ],
            "findings": [
                "Uncut tube torsion stiffness is an upper bound, not installed stiffness",
                "Hot bearing, pocket ligaments, paper crushing and peel unavailable",
                "Six end nodes are mass allocations, not proof of equal force sharing",
            ],
            "assembly_steps": [
                "Illustrate receiver face seating at fore and aft caps with integral nodes.",
                "Show retained screw/barrel connections and actual finite fit clearance.",
                "Show skirt windows and route loops without cutting their load path.",
                "Keep paper/bond/retainer capacities unresolved until actual geometry and material verification.",
            ],
        },
        {
            "id": "motor_service",
            "label": "Forward thrust stop and independent aft motor capture",
            "kind": "motor",
            "part_ids": [
                "motor",
                "motor_front_annulus",
                "motor_front_stop_key_0",
                "C1_independent_motor_retainer_arm_1",
                "C1_aft_cap_15p8_bore",
            ],
            "description": "Forward annulus/keys transfer thrust to receiver; separately removable arms provide reverse capture with float, leaving recovery cap and harness in place.",
            "state": "unavailable",
            "source_ids": ["source_lock", "s3_config", "connection_audit"],
            "dimensions": [
                _dimension("Aft cap bore diameter", service["aft_cap_bore_radius_mm"] * 2),
                _dimension("Aft cap outer diameter", service["cap_outer_radius_mm"] * 2),
                _dimension(
                    "Keeper arm radial length", service["arm_radial_tangential_axial_mm"][0]
                ),
                _dimension("Nominal floating travel", service["floating_travel_mm"]),
                _dimension("Verified nozzle envelope", None, "mm", "unavailable"),
            ],
            "layers": [
                material("Independent arm", 4, "C1_independent_motor_retainer_arm_1"),
                material("Aft cap", 6, "C1_aft_cap_15p8_bore"),
                {
                    "label": "Case / liner / shield / pads",
                    "material": "Supplier case plus retained source layers",
                    "thickness_mm": None,
                    "part_id": "motor_liner",
                    "state": "unavailable",
                },
            ],
            "findings": [
                "Proposed passage and disassembly only; no swept CAD or purchased nozzle tolerance acceptance",
                "No new temperature result; hot arm/bearing and radial clearances remain open",
            ],
            "assembly_steps": [
                "Illustrate removing each captive independent keeper and aft arm.",
                "Withdraw motor through proposed 31.6 mm cap bore while retaining recovery cap/loops.",
                "Illustrate retained pads, liner and shield; no hot case compression credit.",
                "Verify actual nozzle passage, floating travel and loaded access before accepting service.",
            ],
        },
        {
            "id": "avionics_service",
            "label": "Removable sled and independent recovery power",
            "kind": "compartment",
            "part_ids": [
                "avionics_bay",
                "recovery_bulkhead",
                "independent_recovery",
                "recovery_battery",
                "recovery_power_switch",
            ],
            "description": "Main sensor/computer sled and independent recovery controller/power remain at saved source stations. No relocation or ballast is selected.",
            "state": "estimated",
            "source_ids": ["source_spec", "c1_record"],
            "dimensions": [
                _dimension("Bulkhead front", 225),
                _dimension("Bulkhead aft", 230),
                _dimension("Sled front", 240),
                _dimension("Sled length", 210),
            ],
            "layers": [
                {
                    "label": "Custom sled",
                    "material": "ASA",
                    "thickness_mm": 2,
                    "part_id": "avionics_bay",
                    "state": "estimated",
                }
            ],
            "findings": [
                "Independent recovery cell/switch/hardware retained; empty nose is not an available equipment bay"
            ],
            "assembly_steps": [
                "Illustrate opening upper interface and withdrawing retained sled.",
                "Keep independent recovery battery, switch and output harness identified separately.",
                "Check connector access and physical retention without moving the saved mass stations.",
            ],
        },
    ]


def _paths(r: dict[str, Any]) -> list[dict[str, Any]]:
    load = r["attachment_record"]["load_case"]
    attachment = r["attachment_record"]["structures"]["C1"]["attachment"]
    audit = r["connection_audit"]["structures"]["C1"]
    opening = r["attachment_record"]["coupled_cases"][0]["severe_recovery_DF3_mean_N"]

    def node(
        pid: str | None,
        label: str,
        state: str = "unavailable",
        note: str = "Actual installed capacity remains open",
    ) -> dict[str, Any]:
        return {
            "id": label.lower().replace(" ", "_"),
            "part_id": pid,
            "label": label,
            "state": state,
            "note": note,
        }

    def path(
        pid: str,
        label: str,
        nodes: list[dict[str, Any]],
        values: list[tuple[str, float | None, str, str]],
        part: str,
        arrows: list[dict[str, Any]],
        description: str,
        sources: list[str],
        assumptions: list[str],
    ) -> dict[str, Any]:
        edges = []
        for index, (edge_label, value, unit, state) in enumerate(values):
            edges.append(
                {
                    "id": f"{pid}_{index}",
                    "from": nodes[index]["id"],
                    "to": nodes[index + 1]["id"],
                    "label": edge_label,
                    "part_ids": [
                        p for p in (nodes[index]["part_id"], nodes[index + 1]["part_id"]) if p
                    ],
                    "state": state,
                    "value": value,
                    "unit": unit,
                    "note": "Recorded demand/screen only; finite connections and capacity are not inferred",
                    "source_ids": sources,
                }
            )
        return {
            "id": pid,
            "label": label,
            "case_id": "C1_nominal",
            "description": description,
            "state": "failed" if any(x["state"] == "failed" for x in edges) else "unavailable",
            "nodes": nodes,
            "edges": edges,
            "assumptions": assumptions,
            "source_ids": sources,
            "free_body": {
                "part_id": part,
                "label": label,
                "arrows": arrows,
                "supports": [
                    "Actual mating contacts and finite joints shown in path; stiffness/capacity unavailable"
                ],
            },
        }

    def arrow(
        label: str, direction: str, value: float | None, unit: str, state: str = "calculated"
    ) -> dict[str, Any]:
        return {
            "label": label,
            "direction": direction,
            "value": value,
            "unit": unit,
            "state": state,
        }

    return [
        path(
            "fin_bending",
            "Fin normal force and bending",
            [
                node(
                    "c1_fin_panels",
                    "External fin root",
                    "failed",
                    "8.83035 Nm about body-root datum",
                ),
                node(
                    "C1_fin_socket_side_plate_1",
                    "Opposing socket contact",
                    "failed",
                    "10.75095 Nm about socket centre; force/couple transported 8.7 mm",
                ),
                node(
                    "C1_fin_socket_outer_bridge_1",
                    "Outer bridge",
                    "failed",
                    "7.133 MPa mean versus provisional 1 MPa hot screen",
                ),
                node(
                    "C1_closed_G11_body_annulus",
                    "Continuous receiver",
                    "failed",
                    "16.11538 Nm about rocket axis; corrected audit",
                ),
                node("C1_integral_end_hardpoint_0_1", "Finite end joints"),
                node("fore_integral_body_skirt", "Windowed skirt"),
                node("aft_shell", "Paper body and upper joint"),
            ],
            [
                ("Body-root factored moment", load["moment_DF3_once_Nm"], "N m", "calculated"),
                (
                    "Socket-centre factored moment",
                    attachment["socket_center_moment_DF3_Nm"],
                    "N m",
                    "calculated",
                ),
                ("Outer bridge reaction", attachment["outer_bridge_reaction_DF3_N"], "N", "failed"),
                (
                    "Receiver rocket-axis torque",
                    audit["rocket_axis_torque_DF3_once_Nm"],
                    "N m",
                    "calculated",
                ),
                ("End attachment capacity", None, "N m", "unavailable"),
                ("Skirt/body capacity", None, "N", "unavailable"),
            ],
            "c1_fin_panels",
            [
                arrow("Fin-normal force; DF3 once", "right", load["force_DF3_once_N"], "N"),
                arrow("Body-root moment; DF3 once", "moment", load["moment_DF3_once_Nm"], "N m"),
                arrow(
                    "Opposing contact +", "left", attachment["contact_positive_negative_N"][0], "N"
                ),
                arrow(
                    "Opposing contact −", "right", attachment["contact_positive_negative_N"][1], "N"
                ),
            ],
            "One-fin starting envelope at 40 kPa and 5°. Root, socket-centre and rocket-axis moments use different datums and remain distinct.",
            ["source_lock", "attachment_record", "connection_audit"],
            [
                "DF3 already included once; service movement uses unfactored force",
                "Contact equilibrium is not peak crushing/bond capacity",
                "Paper slot, bridge and end joints are finite; no grounded clamp",
                "Three symmetric fins do not imply three same-sign full roll moments",
            ],
        ),
        path(
            "recovery",
            "Recovery opening to retained components",
            [
                node("parachute", "Canopy and lines"),
                node("S3_connector", "Connector and backbone"),
                node("raw_Bally_2745_loop_0", "Sewn loops"),
                node("C1_aft_cap_15p8_bore", "Cap saddles"),
                node("C1_closed_G11_body_annulus", "Receiver and cap joints", "failed"),
                node("fore_integral_body_skirt", "Body connection"),
                node("recovery_anchor", "Upper and nose restraint"),
            ],
            [
                ("Complete mean opening demand", opening, "N", "calculated"),
                ("Finished endpoint capacity", None, "N", "unavailable"),
                ("Hot/chafe saddle contact capacity", None, "N", "unavailable"),
                ("Single-M3 full-load demand", opening, "N", "failed"),
                ("Actual body load branches", None, "N", "unavailable"),
                ("Upper/nose restraint capacity", None, "N", "unavailable"),
            ],
            "C1_aft_cap_15p8_bore",
            [
                arrow("Opening mean demand; DF3 once", "up", opening, "N"),
                arrow("Actual participating mass branches", "down", None, "N", "unavailable"),
            ],
            "Recorded energy-equivalent severe mean opening screen for complete nominal C1 +50 g, not a measured peak or equal-sharing claim.",
            ["source_lock", "attachment_record", "s3_config"],
            [
                "20.4 m/s stopping over 0.3 m, DF3 once",
                "Finished webbing/seam/contact rating remains unavailable",
                "Do not assume all parachute tension enters paper or three equal loop reactions",
            ],
        ),
        path(
            "motor_forward",
            "Motor forward thrust path",
            [
                node("motor", "Motor shoulder"),
                node("thrust_pads", "Forward mica pads"),
                node("motor_front_annulus", "Forward annulus and keys"),
                node("motor_front_key_5mm_cross_pin_complete_set_0", "Positive cross pins"),
                node("C1_forward_motor_key_carrier_1", "Integral key carriers"),
                node("C1_closed_G11_body_annulus", "Receiver to body"),
            ],
            [
                ("Exact installed thrust interface", None, "N", "unavailable"),
                ("Hot contact capacity", None, "N", "unavailable"),
                ("Pin bearing / ligament capacity", None, "N", "unavailable"),
                ("Carrier local capacity", None, "N", "unavailable"),
                ("Body end connection", None, "N", "unavailable"),
            ],
            "motor_front_annulus",
            [
                arrow("Motor thrust", "up", None, "N", "unavailable"),
                arrow("Finite key/pin reactions", "down", None, "N", "unavailable"),
            ],
            "Retained front interface with new C1 carrier foundations; no old S3 local screen becomes C1 installed acceptance.",
            ["source_lock", "s3_config"],
            [
                "No equal pin sharing or fixed receiver support",
                "Exact motor case/shoulder/nozzle and hot properties remain unqualified",
            ],
        ),
        path(
            "motor_reverse",
            "Independent aft motor capture and service",
            [
                node("motor", "Aft motor shoulder"),
                node("aft_thrust_pads", "Aft mica pads"),
                node("C1_independent_motor_retainer_arm_1", "Removable arms"),
                node("motor_aft_hard_stop_spacer_0", "Finite hard stops"),
                node("C1_aft_cap_15p8_bore", "Aft cap and captive keepers"),
                node("C1_closed_G11_body_annulus", "Continuous receiver"),
            ],
            [
                ("Reverse contact demand", None, "N", "unavailable"),
                ("Hot arm capacity", None, "N", "unavailable"),
                (
                    "Floating travel interface",
                    r["source_lock"]["c1_selected_dimensions_from_frozen_config"][
                        "independent_motor_service"
                    ]["floating_travel_mm"],
                    "mm",
                    "estimated",
                ),
                ("Cap/keeper capacity", None, "N", "unavailable"),
                ("Receiver joint capacity", None, "N", "unavailable"),
            ],
            "C1_independent_motor_retainer_arm_1",
            [
                arrow("Reverse motor force", "down", None, "N", "unavailable"),
                arrow("Hard stop reactions", "up", None, "N", "unavailable"),
            ],
            "Proposed independent arms allow motor withdrawal while cap and harness stay installed; swept geometry and hot service remain unavailable.",
            ["source_lock", "s3_config", "connection_audit"],
            [
                "No spring or keeper selected",
                "No hot case compression or old annulus service pass inherited",
            ],
        ),
        path(
            "guide",
            "Launch guide reaction and attachments",
            [
                node(None, "Actual pad or guide"),
                node("rail_guides", "Retained rod lugs"),
                node("body_upper", "Lug foot and paper shell"),
                node("S3_future_rail_button_conversion_extra", "Unselected rail button conversion"),
            ],
            [
                ("Guide equipment / compatibility", None, "N", "unavailable"),
                ("Lug foot attachment capacity", None, "N", "unavailable"),
                ("Actual rail-button geometry / mass", None, "g", "unavailable"),
            ],
            "rail_guides",
            [
                arrow("Wind / guide normal reaction", "left", None, "N", "unavailable"),
                arrow("Actual lug/button attachment reaction", "right", None, "N", "unavailable"),
            ],
            "Old rod lugs provide only the conditional starting-position illustration. No rail button or site equipment is selected.",
            ["source_spec", "s3_config", "c1_record"],
            [
                "1.5 m usable remains baseline",
                "Illustrative 1.971 m travel is not confirmed equipment",
                "5 g extra reserve is additional to existing lugs, not a purchased button mass",
            ],
        ),
    ]


def build_workbench(root: Path = ROOT) -> dict[str, Any]:
    """Prepare one complete read-only document from hash-checked saved records.

    Missing/changed evidence raises ``WorkbenchUnavailable``. Callers must expose
    that failure explicitly; silently retaining a prior document would conceal
    stale evidence. No server startup or physical calculation is performed.
    """
    try:
        mapping, r, manifest = _sources(root)
        parts, distribution = _parts_and_distribution(r)
        part_ids = {p["id"] for p in parts}
        revision_changes = []
        for row in r["attachment_record"]["R1_added_ledger"]:
            linked_ids = mapping["revision_part_links"].get(row["id"], [])
            if any(pid not in part_ids for pid in linked_ids):
                raise WorkbenchUnavailable(
                    f"R1 location link identifies unknown C1 part: {row['id']}"
                )
            revision_changes.append(
                {
                    "id": row["id"],
                    "revision": "R1",
                    "label": row["id"].removeprefix("R1_").replace("_", " "),
                    "mass_g": row["mass_g"],
                    "station_mm": row["station_mm"],
                    "part_ids": linked_ids,
                    "state": "estimated",
                }
            )
        if not math.isclose(
            math.fsum(row["mass_g"] for row in revision_changes),
            r["attachment_record"]["R1_added_mass_g"],
            abs_tol=1e-8,
        ):
            raise WorkbenchUnavailable("Recorded R1 added-mass ledger does not reconcile")
        lock = r["source_lock"]
        spec = r["source_spec"]
        cases = []
        for case in r["attachment_record"]["coupled_cases"]:
            is_r1 = case["id"].startswith("R1")
            adverse = bool(case["extra_aft_g"])
            cases.append(
                {
                    "id": case["id"],
                    "label": ("R1 stopped reinforcement" if is_r1 else "C1 selected preliminary")
                    + (" +20 g / motor-CG probe" if adverse else " nominal"),
                    "state": "failed" if is_r1 else "calculated",
                    "total_g": case["total_with_growth_g"],
                    "nominal_g": case["nominal_without_growth_g"],
                    "growth_g": case["separate_growth_g"],
                    "extra_aft_g": case["extra_aft_g"],
                    "cg_mm": case["cg_mm"],
                    "cp_mm": case["cp_mm"],
                    "burnout_cg_mm": case["burnout_cg_mm"],
                    "loaded_margin_cal": case["static_margin_cal"],
                    "burnout_margin_cal": case["burnout_static_margin_cal"],
                    "recovery_force_n": case["severe_recovery_DF3_mean_N"],
                    "added_mass_g": r["attachment_record"]["R1_added_mass_g"] if is_r1 else 0,
                    "formal_headroom_g": case["illustrative_1p971m_formal_headroom_g"],
                    "planning_headroom_g": case["illustrative_1p971m_planning_headroom_g"],
                    "source_ids": ["attachment_record", "connection_audit"],
                    "findings": [
                        "Headroom is conditional on unconfirmed illustrative 1.971 m usable guide; full separate 50 g retained",
                        "Full intrinsic inertia unavailable; no installed thermal, flutter or flight acceptance",
                    ]
                    + (
                        [
                            "Additional 20 g beyond 50 g; motor-CG +12.8 mm probe is illustrative, not a manufacturer tolerance"
                        ]
                        if adverse
                        else []
                    )
                    + (
                        [
                            "R1 stopped: bridge hot shear and installed movement fail; conditional planning mass exceeded"
                        ]
                        if is_r1
                        else []
                    ),
                    "guide_results": [
                        {
                            "usable_m": g["usable_m"],
                            "speed_mps": g["rail_exit_speed_mps"],
                            "formal_margin_mps": g["formal_speed_margin_mps"],
                            "planning_margin_mps": g["planning_speed_margin_mps"],
                        }
                        for g in case["guide_screens"]
                    ],
                }
            )
        groups = []
        for subsystem in sorted({p["subsystem"] for p in distribution}):
            rows = [p for p in distribution if p["subsystem"] == subsystem]
            groups.append(
                {
                    "id": subsystem,
                    "label": subsystem.title(),
                    "mass_g": math.fsum(p["mass_g"] for p in rows),
                    "state": "estimated",
                    "part_ids": [p["part_id"] for p in rows if p["part_id"]],
                }
            )
        gap_rows = [
            (
                "detailed_cad",
                "No reconciled detailed C1 CAD revision",
                "unavailable",
                [],
                "Viable bounded construction preflight before detailed CAD admission",
            ),
            (
                "inertia",
                "Full C1/R1 intrinsic inertia unavailable",
                "unavailable",
                [],
                "Reconcile complete candidate geometry/mass before publishing tensor",
            ),
            (
                "thermal",
                "Installed C1 temperature / hot contact unavailable",
                "unavailable",
                ["motor", "C1_closed_G11_body_annulus"],
                "Qualify actual geometry or justified thermal bounds within closure-plan budgets",
            ),
            (
                "flutter",
                "Installed fin flutter unavailable",
                "unavailable",
                ["c1_fin_panels"],
                "Actual panel/root/socket/receiver flexible geometry and applicable validation",
            ),
            (
                "fin_motion",
                "C1 and R1 axis-radius-corrected aggregate scalar proxies exceed 1 mm; installed motion remains unqualified",
                "failed",
                ["c1_fin_panels", "C1_closed_G11_body_annulus"],
                "Rejected C2 does not close motion; next interface needs continuous socket-to-structural-receiver/end-joint moment transfer",
            ),
            (
                "bridge",
                "Socket bridge provisional hot shear fails",
                "failed",
                ["C1_fin_socket_outer_bridge_1"],
                "Define positive socket closure and full replacement mass without relaxed allowables",
            ),
            (
                "end_body",
                "End/body/recovery contact capacities unresolved",
                "unavailable",
                ["fore_integral_body_skirt", "raw_Bally_2745_loop_0"],
                "Actual finite end joints, sewn hot/chafe capacity, paper crushing and bond peel",
            ),
            (
                "launch",
                "Exact equipment, club/date and usable guide travel unconfirmed",
                "unavailable",
                ["rail_guides"],
                "Owner confirms actual supported guide/button hardware and usable travel; complete checks before baseline revision",
            ),
            (
                "motor",
                "Exact purchased motor and installed service unresolved",
                "unavailable",
                ["motor"],
                "Exact motor/source/California/site evidence, envelope and loaded independent service verification",
            ),
        ]
        guides = next(p for p in spec["parts"] if p["id"] == "rail_guides")
        guide_geometry = guides["cad"]["parameters"]
        guide_fronts = [guides["position_m"] * 1000 + x for x in guide_geometry["stations_mm"]]
        release = r["s3_config"]["release_geometry"]
        source_parts = {p["id"]: p for p in spec["parts"]}

        def span(pids: list[str]) -> tuple[float, float]:
            starts, ends = [], []
            for pid in pids:
                p = source_parts[pid]
                geometry = p["geometry"]
                length = geometry.get("length_m", geometry.get("bbox_m", [0])[0])
                starts.append(p["position_m"] * 1000)
                ends.append((p["position_m"] + length) * 1000)
            return min(starts), max(ends)

        def region(rid: str, label: str, bounds: tuple[float, float]) -> dict[str, Any]:
            return {"id": rid, "label": label, "start_mm": bounds[0], "end_mm": bounds[1]}

        cap_dims = lock["source_s3_dimensions_retained_or_referenced"]["caps_and_body_interfaces"]
        nose_end = (
            spec["airframe"]["nose"]["length_m"]
            + source_parts["nose_cone"]["geometry"]["shoulder_length_m"]
        ) * 1000
        document = {
            "schema_version": mapping["schema_version"],
            "id": mapping["id"],
            "label": mapping["label"],
            "status": "Selected preliminary C1; R1 stopped; WO-03 open; no build or flight release",
            "generated_from": manifest,
            "identity": {
                "configuration_id": lock["identity"]["selected_candidate_id"],
                "specification_sha256": mapping["sources"]["c1_config"]["sha256"],
                "cad_revision": None,
                "frame": "Axial station mm increases aft from nose tip; radius from rocket centreline; source body +X points toward nose (station = -body X). Display schematic only.",
                "units": "mm, g, N, N m, m/s; any other quantity has explicit unit",
                "status": lock["status"],
            },
            "criteria": {
                "minimum_static_margin_cal": r["attachment_config"]["criteria"][
                    "static_margin_cal"
                ],
                "service_tip_limit_mm": r["attachment_config"]["criteria"][
                    "total_service_tip_displacement_mm"
                ],
                "hot_bond_shear_screen_mpa": r["attachment_config"]["socket"][
                    "bond_hot_shear_estimate_pa"
                ]
                / 1e6,
                "source_ids": ["attachment_config"],
            },
            "arrangement": {
                "overall_length_mm": release["candidate_tail_m"] * 1000,
                "body_diameter_mm": spec["airframe"]["body_diameter_m"] * 1000,
                "nose_length_mm": spec["airframe"]["nose"]["length_m"] * 1000,
                "reference": "Frozen source-73 envelopes with C1 replacement geometry; 1227 mm aft growth/reference station is not a detailed outer mold line.",
                "subsystem_ranges": [
                    region("nose", "Nose and separation", (0, nose_end)),
                    region(
                        "recovery",
                        "Packed recovery / bulkhead",
                        span(["parachute", "shock_cord", "recovery_bulkhead"]),
                    ),
                    region(
                        "avionics",
                        "Avionics / independent recovery electronics",
                        span(["avionics_bay", "recovery_power_switch", "independent_recovery"]),
                    ),
                    region(
                        "interface",
                        "Upper/aft modular interface",
                        span(["interface_coupler", "joint_stop"]),
                    ),
                    region(
                        "receiver",
                        "Receiver and end/body joints",
                        (
                            cap_dims["fore_body_skirt_start_end_mm"][0],
                            cap_dims["front_stations_mm"][1] + cap_dims["thickness_mm"],
                        ),
                    ),
                    region(
                        "motor",
                        "Motor / liner / heat protection",
                        span(["motor", "motor_liner", "aft_thrust_pads"]),
                    ),
                    region(
                        "fins",
                        "Fin panel / captured tabs",
                        (
                            lock["fin_geometry"]["selected_proposed_geometry_mm"]["station"],
                            lock["fin_geometry"]["selected_proposed_geometry_mm"]["station"]
                            + lock["fin_geometry"]["selected_proposed_geometry_mm"]["root"],
                        ),
                    ),
                ],
            },
            "parts": parts,
            "joints": _joints(r),
            "load_paths": _paths(r),
            "cases": cases,
            "mass_distribution": distribution,
            "mass_groups": groups,
            "revision_mass_changes": revision_changes,
            "launch": {
                "baseline_usable_m": spec["design"]["rail_length_m"],
                "formal_mps": lock["identity"]["formal_departure_mps"],
                "planning_mps": lock["identity"]["planning_departure_mps"],
                "equipment_confirmed": False,
                "upper_guide_front_mm": guide_fronts[0],
                "lower_guide_front_mm": guide_fronts[1],
                "guide_length_mm": guide_geometry["length_mm"],
                "assumed_pad_offset_mm": release["assumed_aft_datum_height_m"] * 1000,
                "illustrative_overall_mm": release["illustrative_overall_rail_m"] * 1000,
                "illustrative_usable_mm": release["candidate_usable_m"] * 1000,
                "old_lug_start_loss_mm": (
                    release["candidate_tail_m"]
                    - release["source_upper_lug_leading_edge_m"]
                    + release["assumed_aft_datum_height_m"]
                )
                * 1000,
                "start_loss_basis": "mm = candidate tail station − old upper rod-lug leading-edge station + assumed aft datum pad height; conditional illustration, not selected button geometry",
                "hardware_status": "Original 3.4 mm rod bores retained; rail buttons unselected; 5 g additional conversion reserve is not verified hardware mass",
                "assumptions": [
                    "No ROC/MDARS equipment/date/usable travel confirmed; no longer baseline adopted",
                    "Conditional old-lug start-loss geometry only, not rail-button design",
                    "Stored guide screens: thrust×0.85, 0.5 N friction, Cd0.8, constant loaded mass, full separate50g",
                    "1.8 m C1 departure14.975 m/s fails formal15; separate15.5 planning remains",
                    "Mass ceilings/headrooms are configuration and guide-model conditional; they clear no other gate",
                ],
                "source_ids": ["source_spec", "s3_config", "c1_record", "attachment_record"],
            },
            "inventory": [
                {
                    "id": "saved_preview",
                    "label": "Saved inspection / experiments / replay",
                    "category": "frontend_code",
                    "browser_verified": False,
                    "note": "Existing preview remains separate; this export does not repeat or supersede its prior browser verification",
                },
                {
                    "id": "c1_reports",
                    "label": "C1 source lock, mass/balance, attachment and corrected audit",
                    "category": "report_only",
                    "browser_verified": False,
                    "note": "Saved hash-checked numerical records feed this walkthrough; no new solver/flight calculation",
                },
                {
                    "id": "c1_mesh",
                    "label": "Detailed C1 geometry / compatible engineering fields",
                    "category": "engineering_missing",
                    "browser_verified": False,
                    "note": "No C1 detailed CAD or current compatible stress/temperature field. Archived 72-part candidate belongs to another identity.",
                },
                {
                    "id": "walkthrough_export",
                    "label": "Versioned walkthrough JSON",
                    "category": "frontend_code",
                    "browser_verified": False,
                    "note": "Read-only source-hash export with explicit schematic maturity; visual/browser verification is separate",
                },
            ],
            "gaps": [
                {
                    "id": gid,
                    "label": label,
                    "state": state,
                    "part_ids": pids,
                    "next_verification": nxt,
                    "source_ids": [
                        "source_lock",
                        "attachment_record",
                        "connection_audit",
                        "c2_record",
                    ],
                }
                for gid, label, state, pids, nxt in gap_rows
            ],
            "historical_candidates": [
                {
                    "id": "experimental-g80-retention-72",
                    "label": "Archived 72-part retention CAD",
                    "state": "historical",
                    "reason": "Different saved identity; never assigned to C1 or used for current C1 thermal/stress results",
                    "source_ids": ["source_lock"],
                },
                {
                    "id": "S3",
                    "label": "Heavy three-channel S3 receiver",
                    "state": "superseded",
                    "reason": "Three channels and eight replaced rows removed once. Failed service/mass/stability findings remain historical; C1 preserves retained functions.",
                    "source_ids": ["s3_record", "source_lock"],
                },
                {
                    "id": "R1",
                    "label": "Carbon-face / thicker receiver reinforcement",
                    "state": "failed",
                    "reason": "Stopped before CAD/native analysis: +70.111 g, bridge hot shear, corrected aggregate scalar motion proxy, conditional planning mass and adverse stability fail; no installed field/acceptance",
                    "source_ids": ["attachment_record", "connection_audit", "c2_record"],
                },
                {
                    "id": "C2",
                    "label": "Rejected sandwich fin / integral triangular socket preflight",
                    "state": "failed",
                    "reason": (
                        f"Rejected before detailed CAD/FEA: net +{r['c2_record']['net_added_mass_g']:.6f} g; "
                        f"complete nominal/adverse totals {r['c2_record']['cases'][0]['total_g']:.6f}/"
                        f"{r['c2_record']['cases'][1]['total_g']:.6f} g; "
                        f"receiver-doubler hot bond {r['c2_record']['receiver_joint']['mean_DF3_hot_bond_shear_pa']/1e6:.6f} MPa; "
                        f"aggregate service scalar proxy {r['c2_record']['panel_and_finite_root']['aggregate_service_motion_proxy_m']*1000:.6f} mm. "
                        + r["c2_record"]["decision"]
                        + " C1 geometry/cases remain unchanged; no C2 geometry or spatial overlay is supplied."
                    ),
                    "source_ids": ["c2_record"],
                },
                {
                    "id": "G54_G12",
                    "label": "Separate G54 upgrade and G12 controls tracks",
                    "state": "unavailable",
                    "reason": "Committed independent tracks; no G80-specific evidence closes their findings or aggregate WO-03",
                    "source_ids": ["source_lock"],
                },
            ],
        }
        return document
    except WorkbenchUnavailable:
        raise
    except (OSError, ValueError, KeyError, TypeError, StopIteration) as error:
        raise WorkbenchUnavailable(f"Workbench source contract invalid: {error}") from error
