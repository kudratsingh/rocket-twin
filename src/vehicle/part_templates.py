"""Pinned, read-only RP1 geometry-template and feature-source registry.

This describes allowlisted local nominal recipes. It does not run CadQuery, create
installed instances, add mass, resolve interfaces, or admit a draft vehicle.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from src.api import rp1_inspection

REGISTRY_ID = "rp1-part-templates-v1"
ROOT = Path(__file__).resolve().parents[2]
STEP_SOURCE = "docs/studies/frontend-desktop-detail-20261108/cad-export.json"
STEP_SHA256 = "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731"
GENERATOR_SOURCE = "src/cad/parts.py"
GENERATOR_SHA256 = "911ae4a960556ebfd4aa468a99deba5fd8d755310669e30c040b155107442b98"
PROJECTION_SOURCE = "src/inspection/rp1_geometry.py"
PROJECTION_SHA256 = "d79db74c6285f9c45d7ffade4bb4e8e95279cf64cc7a3c4f0253c09baedf90d3"
CAD_FRAME = "X=body+y, Y=body-z, Z=station aft from nose tip; origin at nose"
LOCAL_FRAME = {
    "units": "mm",
    "origin": "front_center",
    "axes": "X=body+y, Y=body-z, Z=aft along part",
}
TEMPLATE_SPECS = (
    ("motor-tube-cut", "Motor tube cut", "tube_cut", ("motor_tube",)),
    ("aft-annular-ring", "Aft annular ring", "annular_ring", ("aft_ring",)),
    ("slotted-body-tube", "Slotted body tube", "slotted_tube", ("body",)),
    ("forward-notched-ring", "Forward notched ring", "notched_ring", ("forward_ring",)),
    (
        "continuous-fin-tab",
        "Continuous fin and tab, with separate root gussets",
        "continuous_fin_tab",
        ("fin_set", "fin_tabs", "root_gussets"),
    ),
)
FEATURE_SPECS = {
    "motor-tube-cut": (
        (
            "outer_wall",
            "Outer tube wall",
            "cylindrical_surface",
            ("outer_diameter_mm",),
            ("fin_tabs", "aft_ring"),
            "motor_tube",
            "geometry.radius_m",
        ),
        (
            "bore",
            "Motor bore",
            "cylindrical_surface",
            ("inner_diameter_mm",),
            ("motor",),
            "motor_tube",
            "geometry.inner_radius_m",
        ),
        (
            "front_end",
            "Front cut end",
            "planar_end",
            ("length_mm",),
            ("forward_ring",),
            "motor_tube",
            "geometry.length_m",
        ),
        (
            "aft_end",
            "Aft cut end",
            "planar_end",
            ("length_mm",),
            ("aft_ring", "motor_retainer"),
            "motor_tube",
            "geometry.length_m",
        ),
    ),
    "aft-annular-ring": (
        (
            "outer_edge",
            "Outer ring edge",
            "cylindrical_surface",
            ("outer_diameter_mm",),
            ("body",),
            "aft_ring",
            "geometry.radius_m",
        ),
        (
            "bore",
            "Ring bore",
            "cylindrical_surface",
            ("bore_diameter_mm",),
            ("motor_tube",),
            "aft_ring",
            "geometry.inner_radius_m",
        ),
        (
            "front_face",
            "Front ring face",
            "planar_face",
            ("thickness_mm",),
            ("fin_tabs",),
            "aft_ring",
            "geometry.length_m",
        ),
    ),
    "slotted-body-tube": (
        (
            "slot_edges",
            "Three fin slot edges",
            "cut_edge",
            ("slot_width_mm", "slot_length_mm", "slot_start_mm"),
            ("fin_tabs",),
            "body",
            "cad.parameters.fin_slot_width_mm",
        ),
        (
            "inner_wall",
            "Body inner wall",
            "cylindrical_surface",
            ("inner_diameter_mm",),
            ("forward_ring", "aft_ring"),
            "body",
            "geometry.inner_radius_m",
        ),
    ),
    "forward-notched-ring": (
        (
            "cord_notch",
            "Cord passage notch",
            "cut_edge",
            ("notch_width_mm", "notch_depth_mm", "notch_angle_deg"),
            ("rp1_kevlar_wrap",),
            "forward_ring",
            "route.passage_width_mm",
        ),
        (
            "bore",
            "Forward ring bore",
            "cylindrical_surface",
            ("bore_diameter_mm",),
            ("motor_tube",),
            "forward_ring",
            "geometry.inner_radius_m",
        ),
    ),
    "continuous-fin-tab": (
        (
            "panel",
            "Fin panel",
            "stock_contour",
            ("root_chord_mm", "tip_chord_mm", "span_mm", "thickness_mm"),
            (),
            "fin_set",
            "geometry.root_chord_m",
        ),
        (
            "integral_tab",
            "Integral through-wall tab",
            "stock_contour",
            ("tab_length_mm", "tab_depth_mm", "thickness_mm"),
            ("body", "motor_tube", "aft_ring"),
            "fin_tabs",
            "geometry.bbox_m",
        ),
        (
            "root_gusset",
            "Root gusset region",
            "stock_contour",
            ("gusset_height_mm", "gusset_base_mm"),
            ("body",),
            "root_gussets",
            "geometry.bbox_m",
        ),
    ),
}


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _revision(value: dict[str, Any]) -> str:
    return _sha(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode()
    )


def _mm(value: Any, scale: int = 1000) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("Template dimension must be finite source number")
    return float(Decimal(str(value)) * scale)


def _source(path: str, locator: str) -> dict[str, str]:
    digest = rp1_inspection.PINS[path]
    return {"path": path, "sha256": digest, "locator": locator}


def _param(
    key: str,
    value: Any,
    source_part_id: str,
    locator: str,
    *,
    scale: int = 1000,
    unit: str = "mm",
    source_path: str = rp1_inspection.SPEC,
    tolerance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    result = _mm(value, scale) if unit == "mm" else float(value)
    if result < 0:
        raise ValueError("Template parameter cannot be negative")
    return {
        "key": key,
        "value": result,
        "unit": unit,
        "value_basis": "source_nominal",
        "source": _source(
            source_path,
            (
                f"parts[id={source_part_id}].{locator}"
                if source_path == rp1_inspection.SPEC
                else locator
            ),
        ),
        "tolerance": tolerance,
    }


def _ad1_param(
    key: str,
    value: Any,
    field: str,
    tolerance: dict[str, Any] | None = None,
    *,
    section: str = "fin_joints",
) -> dict[str, Any]:
    return {
        "key": key,
        "value": float(value),
        "unit": "mm",
        "value_basis": "source_nominal",
        "source": _source(rp1_inspection.DEFINITION, f"{section}.{field}"),
        "tolerance": tolerance,
    }


def _tolerance(
    value: Any, part_id: str, field: str, *, path: str = rp1_inspection.SPEC
) -> dict[str, Any]:
    return {
        "plus_minus": float(value),
        "unit": "mm",
        "basis": "proposed_cut_tolerance; not measured or supplier-guaranteed",
        "source": _source(
            path, f"parts[id={part_id}].{field}" if path == rp1_inspection.SPEC else field
        ),
    }


def _parameters(
    name: str, parts: dict[str, dict[str, Any]], definition: dict[str, Any]
) -> list[dict[str, Any]]:
    if name in ("motor-tube-cut", "aft-annular-ring", "slotted-body-tube", "forward-notched-ring"):
        pid = {
            "motor-tube-cut": "motor_tube",
            "aft-annular-ring": "aft_ring",
            "slotted-body-tube": "body",
            "forward-notched-ring": "forward_ring",
        }[name]
        p = parts[pid]
        g = p["geometry"]
        parameters = [
            _param("outer_diameter_mm", g["radius_m"], pid, "geometry.radius_m", scale=2000),
            _param(
                (
                    "inner_diameter_mm"
                    if name in ("motor-tube-cut", "slotted-body-tube")
                    else "bore_diameter_mm"
                ),
                g["inner_radius_m"],
                pid,
                "geometry.inner_radius_m",
                scale=2000,
            ),
            _param(
                "length_mm" if name in ("motor-tube-cut", "slotted-body-tube") else "thickness_mm",
                g["length_m"],
                pid,
                "geometry.length_m",
            ),
        ]
        if name == "aft-annular-ring":
            for parameter, tolerance_field in (
                (parameters[0], "outer_diameter"),
                (parameters[1], "bore_diameter"),
            ):
                parameter["tolerance"] = _tolerance(
                    p["engineering"]["tolerances_mm"][tolerance_field],
                    pid,
                    f"engineering.tolerances_mm.{tolerance_field}",
                )
        if name == "slotted-body-tube":
            o = p["cad"]["parameters"]
            joints = definition["fin_joints"]
            parameters += [
                _ad1_param(
                    "slot_width_mm",
                    joints["external_slot_width_mm"],
                    "external_slot_width_mm",
                    _tolerance(
                        joints["slot_cut_tolerance_mm"],
                        pid,
                        "fin_joints.slot_cut_tolerance_mm",
                        path=rp1_inspection.DEFINITION,
                    ),
                ),
                _param(
                    "slot_length_mm",
                    o["fin_slot_length_mm"],
                    pid,
                    "cad.parameters.fin_slot_length_mm",
                    scale=1,
                ),
                _param(
                    "slot_start_mm",
                    o["fin_slot_start_mm"],
                    pid,
                    "cad.parameters.fin_slot_start_mm",
                    scale=1,
                ),
            ]
        if name == "forward-notched-ring":
            route = definition["route"]
            parameters += [
                _ad1_param(
                    "notch_width_mm",
                    route["passage_width_mm"],
                    "passage_width_mm",
                    tolerance=_tolerance(
                        route["passage_cut_tolerance_mm"],
                        pid,
                        "route.passage_cut_tolerance_mm",
                        path=rp1_inspection.DEFINITION,
                    ),
                    section="route",
                ),
                _ad1_param(
                    "notch_depth_mm",
                    route["passage_depth_mm"],
                    "passage_depth_mm",
                    section="route",
                ),
                _ad1_param(
                    "notch_angle_deg",
                    route["passage_angle_deg"],
                    "passage_angle_deg",
                    section="route",
                ),
            ]
            parameters[-1]["unit"] = "deg"
        return parameters
    fin = parts["fin_set"]
    tab = parts["fin_tabs"]
    g = fin["geometry"]
    joints = definition["fin_joints"]
    return [
        _param("root_chord_mm", g["root_chord_m"], "fin_set", "geometry.root_chord_m"),
        _param("tip_chord_mm", g["tip_chord_m"], "fin_set", "geometry.tip_chord_m"),
        _param("span_mm", g["span_m"], "fin_set", "geometry.span_m"),
        _param("sweep_mm", g["sweep_m"], "fin_set", "geometry.sweep_m"),
        _param("thickness_mm", g["thickness_m"], "fin_set", "geometry.thickness_m"),
        _ad1_param("tab_length_mm", joints["tab_length_mm"], "tab_length_mm"),
        _param("tab_depth_mm", tab["geometry"]["bbox_m"][1], "fin_tabs", "geometry.bbox_m[1]"),
        _ad1_param("gusset_height_mm", joints["gusset_height_mm"], "gusset_height_mm"),
        _ad1_param("gusset_base_mm", joints["gusset_base_width_mm"], "gusset_base_width_mm"),
    ]


def _reuse(
    name: str, parts: dict[str, dict[str, Any]], definition: dict[str, Any]
) -> dict[str, Any]:
    if name == "motor-tube-cut":
        return {
            "geometry": "supported_nominal",
            "draft_admission": False,
            "reason": "Allowlisted local annular tube recipe. Exact bore/motor pairing, liner, retention and hot fit remain unresolved.",
        }
    if name == "aft-annular-ring":
        return {
            "geometry": "supported_nominal",
            "draft_admission": False,
            "reason": "Allowlisted plain annulus recipe only. Frozen CAD flags the complete installed ring proposal unavailable; bonds and fit are unverified.",
        }
    if name == "slotted-body-tube":
        legacy = parts["body"]["cad"]["parameters"]["fin_slot_width_mm"]
        current = definition["fin_joints"]["external_slot_width_mm"]
        if legacy == current:
            raise ValueError("Expected frozen body slot source conflict disappeared")
        return {
            "geometry": "blocked",
            "draft_admission": False,
            "reason": f"AD1 inspection projection already replaces the historical {legacy:g} mm CAD slot with {current:g} mm and the registered installed STEP reflects that projection. A standalone slotted local template and interface contract have not been admitted.",
        }
    if name == "forward-notched-ring":
        if (
            parts["forward_ring"]["cad"]["parameters"].get("complete_geometry_available")
            is not False
        ):
            raise ValueError("Expected unadmitted forward-ring geometry status changed")
        return {
            "geometry": "blocked",
            "draft_admission": False,
            "reason": "AD1 inspection projection includes the ideal passage notch in the registered installed STEP. It omits proposed edge roundovers and is not a standalone reusable ring or qualified cord-contact model.",
        }
    old = parts["fin_set"]["cad"]["parameters"]["tab_length_mm"]
    current = definition["fin_joints"]["tab_length_mm"]
    if (
        old == current
        or parts["fin_tabs"]["cad"]["parameters"].get("complete_geometry_available") is not False
    ):
        raise ValueError("Expected frozen continuous-tab source conflict changed")
    return {
        "geometry": "blocked",
        "draft_admission": False,
        "reason": f"AD1 inspection projection already uses {current:g} mm for the integral tab instead of the historical {old:g} mm fin generator field. A reusable local panel/tab/support interface contract has not been admitted; separate gussets remain separate supports and existing accounting lines.",
    }


def build(root: Path) -> dict[str, Any]:
    """Generate deterministic registry from exact frozen RP1 source, without CAD work."""
    root = root.resolve()
    source_paths = {**rp1_inspection.PINS, STEP_SOURCE: STEP_SHA256}
    before = {path: (root / path).read_bytes() for path in source_paths}
    if any(_sha(before[path]) != expected for path, expected in source_paths.items()):
        raise ValueError("Template registry source hash mismatch")
    if _sha((ROOT / GENERATOR_SOURCE).read_bytes()) != GENERATOR_SHA256:
        raise ValueError("Template generator code hash mismatch")
    if _sha((ROOT / PROJECTION_SOURCE).read_bytes()) != PROJECTION_SHA256:
        raise ValueError("Template inspection projection code hash mismatch")
    document = rp1_inspection.build(root)
    spec = yaml.safe_load(before[rp1_inspection.SPEC])
    definition = yaml.safe_load(before[rp1_inspection.DEFINITION])
    step_source = json.loads(before[STEP_SOURCE])
    if step_source["identity"]["configuration_id"] != rp1_inspection.ID:
        raise ValueError("Template installed STEP source identity mismatch")
    parts = {p["id"]: p for p in spec["parts"]}
    step_parts = {p["id"]: p for p in step_source["parts"]}
    if len(parts) != 55 or len(step_parts) != 26:
        raise ValueError("Template source inventory changed")
    templates: list[dict[str, Any]] = []
    features: list[dict[str, Any]] = []
    template_for_part: dict[str, str] = {}
    for short, label, family, member_ids in TEMPLATE_SPECS:
        tid = f"rp1-template:{short}"
        for pid in member_ids:
            if pid in template_for_part or pid not in parts or pid not in step_parts:
                raise ValueError("Template source member missing or duplicated")
            template_for_part[pid] = tid
        parameters = _parameters(short, parts, definition)
        parameter_keys = {p["key"] for p in parameters}
        if len(parameter_keys) != len(parameters):
            raise ValueError("Template parameter keys duplicate")
        links = []
        feature_ids = []
        for feature_name, feature_label, kind, keys, mates, pid, locator in FEATURE_SPECS[short]:
            if (
                not set(keys) <= parameter_keys
                or pid not in member_ids
                or not set(mates) <= set(parts)
            ):
                raise ValueError("Template feature source link is invalid")
            fid = f"rp1-feature:{pid}:{feature_name}"
            feature_ids.append(fid)
            feature = {
                "id": fid,
                "template_id": tid,
                "source_part_id": pid,
                "label": feature_label,
                "kind": kind,
                "parameter_keys": list(keys),
                "source": (
                    _source(rp1_inspection.DEFINITION, locator)
                    if short == "forward-notched-ring" and feature_name == "cord_notch"
                    else _source(rp1_inspection.SPEC, f"parts[id={pid}].{locator}")
                ),
                "mating_part_ids": list(mates),
                "status": "source_nominal",
                "installed_contact_status": "unknown",
            }
            features.append(feature)
            links.append(
                {
                    "feature_id": fid,
                    "mates": list(mates),
                    "geometry_status": "nominal",
                    "installed_contact_status": "unknown",
                }
            )
        installed = []
        for pid in member_ids:
            row = step_parts[pid]
            if (
                row["source"]["sha256"] != rp1_inspection.PINS[rp1_inspection.SPEC]
                or row["physical_verification"] != "open"
            ):
                raise ValueError("Template installed STEP source or physical status changed")
            installed.append(
                {
                    "source_part_id": pid,
                    "step": {"path": row["path"], "sha256": row["sha256"]},
                    "cad_frame": CAD_FRAME,
                    "front_station_mm": _mm(parts[pid]["position_m"]),
                    "asset_scope": "installed_reference_only",
                }
            )
        reuse = _reuse(short, parts, definition)
        geometry_supported = reuse["geometry"] == "supported_nominal"
        template: dict[str, Any] = {
            "id": tid,
            "label": label,
            "family": family,
            "source_part_ids": list(member_ids),
            "material": parts[member_ids[0]]["material"],
            "parameters": parameters,
            "local_frame": copy.deepcopy(LOCAL_FRAME),
            "installed_references": installed,
            "geometry": {
                "source_cad_generator": parts[member_ids[0]]["cad"]["generator"],
                "local_generator": "src.cad.parts.tube" if geometry_supported else None,
                "generator_source": {"path": GENERATOR_SOURCE, "sha256": GENERATOR_SHA256},
                "installed_projection_source": {
                    "path": PROJECTION_SOURCE,
                    "sha256": PROJECTION_SHA256,
                },
                "local_recipe_supported": geometry_supported,
                "generated_asset": None,
                "installed_step_is_local_template": False,
            },
            "feature_ids": feature_ids,
            "interfaces": links,
            "reuse": reuse,
            "mass_accounting": {
                "source_part_ids": list(member_ids),
                "template_mass_kg": None,
                "incremental_charge": False,
                "basis": "Existing source record accounting only; a display feature is not another mass line",
            },
            "engineering_status": "open",
            "physical_verification": "open",
        }
        template["revision_sha256"] = _revision(template)
        templates.append(template)
    if len(features) != len({item["id"] for item in features}):
        raise ValueError("Template feature IDs duplicate")
    dispositions = []
    blocked_notes = {
        "motor_retainer": "Product19002/009750 conflict; no reusable exact retainer template.",
        "independent_recovery": "Recovery-controller product identity conflict; mounting template blocked.",
        "high_g_accel": "Manufacturer board reference does not establish installed sensor/height identity.",
    }
    for source_part in document["parts"]:
        pid = source_part["id"]
        dispositions.append(
            {
                "source_part_id": pid,
                "template_id": template_for_part.get(pid),
                "source_kind": source_part["type"],
                "source_cad_role": source_part["cad"]["role"],
                "accounting_line": "existing_source_record_only",
                "template_role": (
                    "primary"
                    if pid in {"body", "motor_tube", "forward_ring", "aft_ring", "fin_set"}
                    else (
                        "integral_child"
                        if pid == "fin_tabs"
                        else "associated_support" if pid == "root_gussets" else "none"
                    )
                ),
                "reason": blocked_notes.get(
                    pid,
                    (
                        "Named source template in this packet"
                        if pid in template_for_part
                        else "No validated local reusable geometry template in this bounded packet."
                    ),
                ),
            }
        )
    registry: dict[str, Any] = {
        "schema_version": 1,
        "id": REGISTRY_ID,
        "configuration_id": rp1_inspection.ID,
        "identity": {
            "specification": {
                "path": rp1_inspection.SPEC,
                "sha256": rp1_inspection.PINS[rp1_inspection.SPEC],
            },
            "definition": {
                "path": rp1_inspection.DEFINITION,
                "sha256": rp1_inspection.PINS[rp1_inspection.DEFINITION],
            },
            "record": {
                "path": rp1_inspection.RECORD,
                "sha256": rp1_inspection.PINS[rp1_inspection.RECORD],
            },
            "registered_step": {"path": STEP_SOURCE, "sha256": STEP_SHA256},
            "local_generator_source": {"path": GENERATOR_SOURCE, "sha256": GENERATOR_SHA256},
            "installed_projection_source": {"path": PROJECTION_SOURCE, "sha256": PROJECTION_SHA256},
        },
        "all55_part_ids": [part["id"] for part in document["parts"]],
        "templates": templates,
        "feature_sources": features,
        "dispositions": dispositions,
        "capabilities": {
            "browse": True,
            "inspect": True,
            "draft_admission": False,
            "cad_job_execution": False,
        },
        "engineering_accepted": False,
        "physical_verification": "open",
        "flight_ready": False,
    }
    registry["revision_sha256"] = _revision(registry)
    after = {path: (root / path).read_bytes() for path in source_paths}
    if after != before:
        raise ValueError("Template registry source changed during build")
    return registry


def validate_catalog(root: Path, payload: dict[str, Any]) -> dict[str, Any]:
    """Admit only exact current source projection, including every nested revision."""
    expected = build(root)
    if payload != expected:
        raise ValueError("Template registry differs from frozen source projection")
    return expected


def select_template(
    root: Path,
    payload: dict[str, Any],
    template_id: str,
    revision_sha256: str,
    *,
    action: str = "inspect",
) -> dict[str, Any]:
    """Read-only source selection; it never installs or authorizes a part."""
    registry = validate_catalog(root, payload)
    if action != "inspect":
        raise ValueError("Only read-only template inspection is admitted")
    template = next((row for row in registry["templates"] if row["id"] == template_id), None)
    if template is None or template["revision_sha256"] != revision_sha256:
        raise ValueError("Unknown or stale template revision")
    return {"action": "inspect", "template": copy.deepcopy(template), "draft_admission": False}


def prepare_local_geometry_request(
    root: Path,
    payload: dict[str, Any],
    template_id: str,
    revision_sha256: str,
    parameters: dict[str, float],
) -> dict[str, Any]:
    """Describe an allowlisted nominal local tube/annulus recipe; run no CAD."""
    template = select_template(root, payload, template_id, revision_sha256)["template"]
    if not template["geometry"]["local_recipe_supported"]:
        raise ValueError("Template local geometry is blocked by source evidence")
    nominal = {row["key"]: row["value"] for row in template["parameters"]}
    if parameters != nominal:
        raise ValueError(
            "Only exact source-nominal parameters are admitted in this read-only phase"
        )
    outer = nominal["outer_diameter_mm"] / 2
    inner = (
        nominal["inner_diameter_mm"]
        if "inner_diameter_mm" in nominal
        else nominal["bore_diameter_mm"]
    ) / 2
    length = nominal["length_mm"] if "length_mm" in nominal else nominal["thickness_mm"]
    if not (0 < inner < outer and length > 0):
        raise ValueError("Invalid source annulus dimensions")
    return {
        "template_id": template_id,
        "template_revision_sha256": revision_sha256,
        "generator": "src.cad.parts.tube",
        "parameters_mm": {"outer_radius_mm": outer, "inner_radius_mm": inner, "length_mm": length},
        "local_frame": copy.deepcopy(LOCAL_FRAME),
        "cad_execution": False,
        "draft_admission": False,
        "mass_kg": None,
    }
