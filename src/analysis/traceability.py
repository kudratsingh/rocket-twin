"""Source-driven WO-03 requirements, interfaces and FMEA publication."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.vehicle.schema import load_vehicle, vehicle_input_paths


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _get_path(obj: dict[str, Any], path: str) -> tuple[bool, Any]:
    value: Any = obj
    for key in path.split("."):
        if not isinstance(value, dict) or key not in value:
            return False, None
        value = value[key]
    return True, value


def validate_catalog(catalog: dict[str, Any]) -> None:
    requirements = catalog.get("requirements", [])
    interfaces = catalog.get("interfaces", [])
    fmea = catalog.get("fmea", [])
    configuration_ids = set(catalog.get("configurations", {}))
    req_ids = [item["id"] for item in requirements]
    interface_ids = [item["id"] for item in interfaces]
    fmea_ids = [item["id"] for item in fmea]
    if (
        len(req_ids) != len(set(req_ids))
        or len(interface_ids) != len(set(interface_ids))
        or len(fmea_ids) != len(set(fmea_ids))
    ):
        raise ValueError("duplicate requirement, interface, or FMEA ID")
    req_set, interface_set = set(req_ids), set(interface_ids)
    for item, key in [
        *((r, "applies_to") for r in requirements),
        *((i, "applies_to") for i in interfaces),
        *((f, "applicable_configurations") for f in fmea),
    ]:
        unknown_configs = set(item.get(key, [])) - configuration_ids
        if unknown_configs:
            raise ValueError(
                f"{item['id']} references unknown configurations: {sorted(unknown_configs)}"
            )
    for req in requirements:
        unknown = set(req.get("interfaces", [])) - interface_set
        if unknown:
            raise ValueError(f"{req['id']} references unknown interfaces: {sorted(unknown)}")
    for interface in interfaces:
        unknown = set(interface.get("requirements", [])) - req_set
        if unknown:
            raise ValueError(
                f"{interface['id']} references unknown requirements: {sorted(unknown)}"
            )
    for row in fmea:
        unknown_req = set(row.get("requirements", [])) - req_set
        unknown_if = set(row.get("interfaces", [])) - interface_set
        if unknown_req or unknown_if:
            raise ValueError(
                f"{row['id']} has invalid references: requirements={sorted(unknown_req)}, interfaces={sorted(unknown_if)}"
            )


def resolve_requirements(
    catalog: dict[str, Any], vehicle: Any, config_id: str
) -> list[dict[str, Any]]:
    dumped = vehicle.model_dump(mode="json", by_alias=True)
    result = []
    for requirement in catalog["requirements"]:
        if config_id not in requirement.get("applies_to", []):
            continue
        paths = requirement.get("spec_paths", [])
        resolved = []
        for path in paths:
            present, value = _get_path(dumped, path)
            available = present and value is not None
            resolved.append(
                {
                    "path": path,
                    "status": "resolved" if available else "unavailable",
                    "value": value if available else None,
                }
            )
        result.append({**requirement, "resolved_spec": resolved})
    return result


def resolve_interfaces(catalog: dict[str, Any], config_id: str) -> list[dict[str, Any]]:
    """Retain the full interface register and label mode applicability explicitly."""
    if config_id not in catalog.get("configurations", {}):
        raise ValueError(f"unknown configuration: {config_id}")
    return [
        {
            **interface,
            "applicability_status": (
                "applicable" if config_id in interface.get("applies_to", []) else "not_applicable"
            ),
        }
        for interface in catalog["interfaces"]
    ]


def _cell(value: Any) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, (dict, list)):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False)
    return str(value).replace("|", "\\|").replace("\n", " ")


def _doc_link(path: str) -> str:
    return "../" + path if path.startswith("runs/") else path.removeprefix("docs/")


def _evidence(values: list[str]) -> str:
    if not values:
        return "None recorded"
    return "; ".join(f"[{Path(path).parent.name}]({_doc_link(path)})" for path in values)


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    return (
        "| "
        + " | ".join(headers)
        + " |\n|"
        + "|".join(["---"] * len(headers))
        + "|\n"
        + "".join("| " + " | ".join(_cell(v) for v in row) + " |\n" for row in rows)
    )


def render_docs(catalog: dict[str, Any], docs: Path) -> None:
    validate_catalog(catalog)
    req_rows = []
    for r in catalog["requirements"]:
        req_rows.append(
            [
                r["id"],
                ", ".join(r.get("applies_to", [])),
                r.get("purpose_source"),
                r.get("acceptance"),
                ", ".join(r.get("spec_paths", [])) or "—",
                ", ".join(r.get("related_parts", [])),
                ", ".join(r.get("interfaces", [])),
                r.get("verification_method"),
                ", ".join(r.get("responsible_wo", [])),
                _evidence(r.get("evidence", [])),
                r.get("status"),
                r.get("evidence_basis"),
            ]
        )
    evidence_refs = "\n\n## Evidence pointers\n\n" + "\n".join(
        f"- [`{e['path']}`]({_doc_link(e['path'])}) — {e['scope']} {e['limitation']}"
        for e in catalog.get("evidence_sources", [])
    )
    (docs / "requirements.md").write_text(
        "# Requirements and verification matrix\n\nGenerated from `configs/engineering/traceability.yaml`. Criteria with `spec_paths` resolve from each active `Vehicle.model_dump()`; a missing field is `unavailable`, never zero. Evidence links identify scoped records, not blanket passes. Per-requirement statuses are preserved; expanded WO-03 acceptance remains `"
        + catalog.get("expanded_wo03_acceptance", "unspecified")
        + "` and no physical qualification is claimed.\n\n"
        + _table(
            [
                "ID",
                "Configurations",
                "Purpose / source",
                "Criterion",
                "Active spec paths",
                "Parts",
                "Interfaces",
                "Method",
                "WO",
                "Evidence",
                "Status",
                "Evidence basis",
            ],
            req_rows,
        )
        + evidence_refs
    )
    int_rows = [
        [
            i["id"],
            i["name"],
            ", ".join(i.get("applies_to", [])),
            ", ".join(i.get("requirements", [])),
            i.get("datums_axes_units"),
            ", ".join(i.get("spec_parts", [])),
            "; ".join(i.get("dimensions_source", [])),
            i.get("load_retention"),
            i.get("indexing_identity"),
            i.get("clearance"),
            i.get("power_connectors"),
            "; ".join(i.get("unresolved", [])),
            "; ".join(i.get("evidence", [])) or "None recorded",
        ]
        for i in catalog["interfaces"]
    ]
    (docs / "interfaces.md").write_text(
        "# Interface register\n\nGenerated from `configs/engineering/traceability.yaml`. Statements describe current design intent and open dependencies; they do not establish measured fit or qualification.\n\n"
        + _table(
            [
                "ID",
                "Boundary",
                "Configurations",
                "Requirements",
                "Datums / axes / units",
                "Parts",
                "Dimension sources",
                "Load / retention",
                "Indexing / identity",
                "Clearance",
                "Power / connectors",
                "Unresolved",
                "Evidence",
            ],
            int_rows,
        )
    )
    fm_rows = [
        [
            f["id"],
            f["failure_mode"],
            ", ".join(f.get("applicable_configurations", [])),
            f.get("cause"),
            f.get("local_system_effect"),
            f.get("severity"),
            f.get("likelihood"),
            f.get("likelihood_basis"),
            f.get("detection"),
            f.get("mitigation_design_change"),
            f.get("residual_risk"),
            ", ".join(f.get("requirements", [])),
            ", ".join(f.get("interfaces", [])),
            f.get("verification_test"),
            f.get("status"),
        ]
        for f in catalog["fmea"]
    ]
    (docs / "fmea.md").write_text(
        "# Initial failure modes and effects analysis\n\nGenerated from `configs/engineering/traceability.yaml`. Severity is qualitative; likelihood is unknown without failure-rate data. Abort cannot stop a solid motor, and centering a finless gimbal does not stabilize coast.\n\n"
        + _table(
            [
                "ID",
                "Failure mode",
                "Configurations",
                "Cause",
                "Effect",
                "Severity",
                "Likelihood",
                "Basis",
                "Detection",
                "Mitigation",
                "Residual risk",
                "Requirements",
                "Interfaces",
                "Later verification",
                "Status",
            ],
            fm_rows,
        )
    )


def generate(
    catalog_path: Path,
    preset: str,
    platform_path: Path = Path("configs/platform.yaml"),
    root: Path = Path("."),
) -> list[Path]:
    del preset  # Interface standardization; resolution is deterministic and CPU-only.
    catalog_bytes = (root / catalog_path).read_bytes()
    catalog = yaml.safe_load(catalog_bytes)
    validate_catalog(catalog)
    vehicles: dict[str, Path] = {
        key: Path(value) for key, value in catalog["configurations"].items()
    }
    out_paths = []
    for config_id, path in vehicles.items():
        vehicle = load_vehicle(root / path)
        resolved_hash = sha256(vehicle.model_dump_json(by_alias=True).encode())
        source_hashes = {
            str(p.relative_to(root)): sha256(p.read_bytes())
            for p in vehicle_input_paths(root / path)
        }
        source_hashes[str(platform_path)] = sha256((root / platform_path).read_bytes())
        cad_py = sorted((root / "src/cad").glob("*.py"))
        cad_identity = {
            "cad_generator_sha256": sha256(b"".join(p.read_bytes() for p in cad_py)),
            "part_shape_sha256": {
                p.id: getattr(getattr(p, "cad_mass", None), "shape_sha256", None)
                for p in vehicle.parts
            },
        }
        entry = {
            "configuration_id": config_id,
            "vehicle_id": vehicle.id,
            "resolved_spec_sha256": resolved_hash,
            "catalog_sha256": sha256(catalog_bytes),
            "source_sha256": source_hashes,
            "cad_identity": cad_identity,
            "evidence_sources": catalog.get("evidence_sources", []),
            "delivery_priority": catalog.get("delivery_priority", {}),
            "requirements": resolve_requirements(catalog, vehicle, config_id),
            "interfaces": resolve_interfaces(catalog, config_id),
            "fmea": [
                f for f in catalog["fmea"] if config_id in f.get("applicable_configurations", [])
            ],
        }
        target = root / "build" / vehicle.id / "traceability.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(entry, indent=2, sort_keys=True, allow_nan=False) + "\n")
        out_paths.append(target)
    render_docs(catalog, root / "docs")
    return out_paths
