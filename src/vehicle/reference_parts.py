"""Two geometry-only local references projected from registered, frozen CAD cases.

No CAD module/kernel is imported or executed. All reads use fixed known paths;
missing local assets report unavailable, corrupt/foreign assets fail closed.
Analytic features are nominal datums, never persistent face IDs or fit evidence.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import stat
from contextlib import ExitStack
from decimal import Decimal
from pathlib import Path
from typing import Any

import yaml

from src.api.parts_bank import digest
from src.api.rp1_inspection import ID as CONFIGURATION
from src.api.rp1_inspection import PINS, SPEC

CONFIG_PATH = "configs/parts-bank/reference-local-v1.yaml"
CONFIG_SHA256 = "a95d6147d1614c0939b266a297e43ec9d265585c30c445f1297554381713de07"
MANIFEST_PATH = "docs/studies/frontend-template-bank-20261109/geometry.json"
MANIFEST_SHA256 = "6316ccef56c168e14d8a14a6570d162f35eb43bcadf4bd6132226b51d91799d2"
SOURCE_PINS = {
    CONFIG_PATH: CONFIG_SHA256,
    MANIFEST_PATH: MANIFEST_SHA256,
    **PINS,
    "src/vehicle/part_templates.py": "10705f374160cbb0fe59026208280754e2702e53f9f44d24561579301511bcff",
    "scripts/wo04_part_template_geometry.py": "ddb1f80ee0ffa8468745def46c538466045e48cab336d70d44f08b6f93a864b5",
    "src/cad/parts.py": "911ae4a960556ebfd4aa468a99deba5fd8d755310669e30c040b155107442b98",
    "src/inspection/rp1_geometry.py": "d79db74c6285f9c45d7ffade4bb4e8e95279cf64cc7a3c4f0253c09baedf90d3",
    "docs/studies/frontend-desktop-detail-20261108/cad-export.json": "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731",
}
CASES = (
    (
        "reference-local-v1:motor-tube-nominal",
        "motor-tube-cut",
        "motor_tube",
        15.6845,
        14.5845,
        165.0,
    ),
    ("reference-local-v1:aft-annulus-nominal", "aft-annular-ring", "aft_ring", 32.2, 15.95, 6.0),
)
ASSET_PATHS = {
    f"output/rp1-template-geometry-v1/{case[1]}.{ext}" for case in CASES for ext in ("step", "glb")
}
CAD_FRAME = {
    "units": "mm",
    "origin": "front_center",
    "axes": "X=body+y, Y=body-z, Z=aft along part",
}
VIEWER_FRAME = {"units": "m", "mapping": "viewer[X,Y,Z]=[cadX/1000,-cadZ/1000,cadY/1000]"}
MAX_BYTES = 8 * 1024 * 1024


class ReferencePartsError(ValueError):
    """A source, request, registered frame or existing asset cannot be admitted."""


def _read(root: Path, relative: str) -> bytes:
    if relative not in SOURCE_PINS and relative not in ASSET_PATHS:
        raise ReferencePartsError("Only exact registered reference paths may be read")
    if root.is_symlink():
        raise ReferencePartsError("Reference server root cannot be a symlink")
    try:
        with ExitStack() as stack:
            directory = os.open(
                root.resolve(strict=True), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            )
            stack.callback(os.close, directory)
            for name in Path(relative).parts[:-1]:
                directory = os.open(
                    name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
                )
                stack.callback(os.close, directory)
            fd = os.open(
                Path(relative).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory
            )
            stack.callback(os.close, fd)
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_BYTES:
                raise ReferencePartsError(
                    "Reference inputs must be bounded single-link regular files"
                )
            with os.fdopen(fd, "rb", closefd=False) as stream:
                data = stream.read(MAX_BYTES + 1)
            if len(data) > MAX_BYTES:
                raise ReferencePartsError("Reference input exceeds read bound")
            return data
    except FileNotFoundError:
        raise
    except OSError as error:
        raise ReferencePartsError("Unsafe reference source/cache path") from error


def _sources(root: Path) -> dict[str, bytes]:
    try:
        data = {path: _read(root, path) for path in SOURCE_PINS}
    except FileNotFoundError as error:
        raise ReferencePartsError(
            "Reference source/frame inputs unavailable; no geometry is admitted"
        ) from error
    if any(hashlib.sha256(data[path]).hexdigest() != pin for path, pin in SOURCE_PINS.items()):
        raise ReferencePartsError(
            "Reference source bytes differ from their exact pinned identities"
        )
    return data


def _features(outer: float, inner: float, length: float) -> list[dict[str, Any]]:
    common = {
        "scope": "analytic_nominal_datum",
        "frame": "local_cad_mm",
        "cad_face_ids": None,
        "mesh_triangle_ids": None,
        "tolerance_mm": None,
        "mating_admitted": False,
    }
    return [
        {
            **common,
            "id": "axis",
            "kind": "analytic_axis",
            "origin_mm": [0.0, 0.0, 0.0],
            "direction": [0.0, 0.0, 1.0],
            "axial_range_mm": [0.0, length],
        },
        *[
            {
                **common,
                "id": name,
                "kind": "analytic_cylinder",
                "axis": "axis",
                "radius_mm": radius,
                "axial_range_mm": [0.0, length],
            }
            for name, radius in (("bore", inner), ("outer_cylinder", outer))
        ],
        *[
            {
                **common,
                "id": name,
                "kind": "analytic_annular_plane",
                "origin_mm": [0.0, 0.0, z],
                "normal": [0.0, 0.0, 1.0],
                "radial_range_mm": [inner, outer],
                "normal_basis": "Positive local axis convention; not a kernel face orientation",
            }
            for name, z in (("start_plane", 0.0), ("end_plane", length))
        ],
    ]


def _check_manifest(config: dict[str, Any], manifest: dict[str, Any]) -> None:
    if (
        config["id"] != "reference-local-v1"
        or config["schema_version"] != 1
        or config["scope"] != "geometry_only_planning"
        or config["source_configuration_id"] != CONFIGURATION
        or manifest["id"] != "rp1-template-geometry-v1"
        or manifest["configuration_id"] != CONFIGURATION
        or manifest["specification_sha256"] != PINS[SPEC]
        or config["source_registry"] != manifest["registry"]
        or config["local_cad_frame"] != CAD_FRAME
        or config["viewer_frame"] != VIEWER_FRAME
        or manifest["local_cad_frame_mm"] != "front center; X=body+y, Y=body-z, Z=aft along part"
        or manifest["viewer_mapping"] != VIEWER_FRAME["mapping"]
        or manifest["step_units"] != "mm"
        or manifest["viewer_units"] != "m"
        or any(
            manifest[key] is not False
            for key in (
                "mass_or_inertia_generated",
                "draft_admission",
                "vehicle_adoption",
                "engineering_accepted",
                "flight_ready",
            )
        )
        or any(value is not None for value in config["unknown_properties"].values())
        or any(value is not False for value in config["readiness"].values())
        or len(config["definitions"]) != 2
        or len(manifest["representations"]) != 2
    ):
        raise ReferencePartsError("Reference scope, source, frame or false-gate contract differs")


def _availability(root: Path, assets: dict[str, Any]) -> dict[str, Any]:
    missing = []
    for ext in ("step", "glb"):
        asset = assets[ext]
        try:
            data = _read(root, asset["path"])
        except FileNotFoundError:
            missing.append(ext)
            continue
        if len(data) != asset["bytes"] or hashlib.sha256(data).hexdigest() != asset["sha256"]:
            raise ReferencePartsError(
                "Registered local geometry bytes/hash differ; no substitute is admitted"
            )
    return {
        "status": "unavailable" if missing else "verified_registered_local_cache",
        "missing_formats": missing,
        "geometry_available": not missing,
        "public_url_cache_verified": False,
        "generation_attempted": False,
        "reason": (
            "Required local cache absent; no regeneration"
            if missing
            else "Exact existing STEP/GLB bytes verified; no new CAD readback or physical acceptance"
        ),
    }


def build(root: Path) -> dict[str, Any]:
    """Read-only deterministic definitions and separately reported cache availability."""
    before = _sources(root)
    config = yaml.safe_load(before[CONFIG_PATH])
    manifest = json.loads(before[MANIFEST_PATH])
    spec = yaml.safe_load(before[SPEC])
    _check_manifest(config, manifest)
    source_parts = {part["id"]: part for part in spec["parts"]}
    definitions = []
    availability = {}
    for case, authored, representation in zip(
        CASES, config["definitions"], manifest["representations"], strict=True
    ):
        reference_id, slug, source_id, outer, inner, length = case
        parameters = {"outer_radius_mm": outer, "inner_radius_mm": inner, "length_mm": length}
        source_geometry = source_parts[source_id]["geometry"]
        source_parameters = {
            key: float(Decimal(str(source_geometry[field])) * 1000)
            for key, field in (
                ("outer_radius_mm", "radius_m"),
                ("inner_radius_mm", "inner_radius_m"),
                ("length_mm", "length_m"),
            )
        }
        readback = representation["readback"]
        if (
            authored["id"] != reference_id
            or authored["source_part_id"] != source_id
            or authored["parameters_mm"] != parameters
            or source_parameters != parameters
            or authored["source_template_id"] != f"rp1-template:{slug}"
            or representation["template_id"] != authored["source_template_id"]
            or representation["template_revision_sha256"]
            != authored["source_template_revision_sha256"]
            or representation["parameters_mm"] != parameters
            or representation["representation_status"] != "source_nominal_local_only"
            or authored["exact_product"] is not None
            or authored["stock_adoption"] is not False
            or authored["installed_geometry_adoption"] is not False
            or any(readback[key] is not True for key in ("valid", "closed", "annular_bore"))
            or readback["solid_count"] != 1
            or readback["bounds_mm"] != [[-outer, -outer, 0.0], [outer, outer, length]]
            or not math.isclose(readback["outer_diameter_mm"], 2 * outer, rel_tol=0, abs_tol=1e-5)
            or not math.isclose(readback["inner_diameter_mm"], 2 * inner, rel_tol=0, abs_tol=1e-5)
            or readback["length_mm"] != length
            or not 0 <= representation["glb_bounds_error_m"] <= 0.00025
        ):
            raise ReferencePartsError(
                "Exact source nominal parameters or registered readback differ"
            )
        assets = {ext: copy.deepcopy(representation[ext]) for ext in ("step", "glb")}
        for ext, asset in assets.items():
            if (
                asset["path"] != f"output/rp1-template-geometry-v1/{slug}.{ext}"
                or asset["url"]
                != f"/engineering-workbench/rp1-part-templates-geometry/{slug}.{ext}"
            ):
                raise ReferencePartsError("Foreign asset/frame reference is not admitted")
        row = {
            **copy.deepcopy(authored),
            "scope": config["scope"],
            "unknown_properties": copy.deepcopy(config["unknown_properties"]),
            "readiness": copy.deepcopy(config["readiness"]),
            "frames": {
                "local_cad_mm": copy.deepcopy(CAD_FRAME),
                "viewer": copy.deepcopy(VIEWER_FRAME),
            },
            "analytic_features": _features(outer, inner, length),
            "interfaces": None,
            "interfaces_status": "Analytic datums only; no contact or connection contract admitted",
            "representation": {
                "scope": "local_nominal_reference_only",
                "installed_transform": None,
                "assets": assets,
                "recorded_readback": copy.deepcopy(readback),
                "bounds_m": copy.deepcopy(representation["bounds_m"]),
                "frame_source": MANIFEST_PATH,
                "kernel_execution_performed": False,
            },
            "provenance": {
                "configuration_id": CONFIGURATION,
                "specification_sha256": PINS[SPEC],
                "source_part_id": source_id,
                "source_locator": f"parts[id={source_id}].geometry",
                "source_mass_policy": "Original source budget estimates are not new installed reference mass; no mass/cost credit or charge is generated",
                "geometry_manifest_sha256": MANIFEST_SHA256,
                "generator": copy.deepcopy(manifest["cad_generator"]),
                "source_registry": copy.deepcopy(manifest["registry"]),
            },
        }
        row["revision_sha256"] = digest(row)
        definitions.append(row)
        availability[reference_id] = _availability(root, assets)
    if _sources(root) != before:
        raise ReferencePartsError("Reference sources changed during read")
    result = {
        "schema_version": 1,
        "id": config["id"],
        "scope": config["scope"],
        "definitions": definitions,
        "source_pins": copy.deepcopy(SOURCE_PINS),
        "source_catalog_changed": False,
        "add_replace_connect_implemented": False,
        "engineering_accepted": False,
        "simulation_eligible": False,
        "flight_ready": False,
        "revision_scope": "Definition/source content only; local cache availability is reported separately",
    }
    result["revision_sha256"] = digest(result)
    return {
        **result,
        "availability": availability,
    }


def select_reference(
    root: Path, reference_id: str, revision_sha256: str, parameters_mm: dict[str, float]
) -> dict[str, Any]:
    """Select exact nominal reference metadata; never create an instance or geometry."""
    catalog = build(root)
    row = next((item for item in catalog["definitions"] if item["id"] == reference_id), None)
    if row is None:
        raise ReferencePartsError("Unknown namespaced local reference ID")
    if revision_sha256 != row["revision_sha256"]:
        raise ReferencePartsError("Reference revision differs; reload source definitions")
    if (
        not isinstance(parameters_mm, dict)
        or parameters_mm != row["parameters_mm"]
        or any(
            type(value) not in (int, float) or not math.isfinite(value)
            for value in parameters_mm.values()
        )
    ):
        raise ReferencePartsError("Only the exact nominal reference parameters are admitted")
    return {
        "definition": copy.deepcopy(row),
        "availability": copy.deepcopy(catalog["availability"][reference_id]),
        "action": "inspect_geometry_reference",
        "instance_created": False,
        "engineering_accepted": False,
        "simulation_eligible": False,
        "flight_ready": False,
    }
