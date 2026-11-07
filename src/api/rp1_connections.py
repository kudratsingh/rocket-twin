"""Source-pinned AD1 connection diagrams and existing drawing descriptors.

No engineering calculation, CAD generation, simulation or physical work occurs here.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import yaml

from src.api import rp1_inspection

ID = "RP1-AD1-connections-v1"
SPEC = rp1_inspection.SPEC
DEFINITION = rp1_inspection.DEFINITION
AD1 = rp1_inspection.RECORD
D1 = "runs/wo03-rp1-d1-20261104-v1/record.json"
AD1_DOC = "docs/wo03-rp1-attachment-definition.md"
D1_DOC = "docs/wo03-rp1-load-attachment-decision.md"
MANIFEST = "output/rp1-attachment-definition/manifest.json"
PINS = {
    **rp1_inspection.PINS,
    D1: "7bd208322dc8d866b56e4422d369d06d1a06b8966b7cc614a22c086bef1aa6a4",
    AD1_DOC: "012cd168e03807460debd5bb9dbc543f058d02597f87bd83945a769794a1aa4a",
    D1_DOC: "af6eabd641063d262d0190ee46f5bbc847e54af5c7a3a1f1c442f0a57740bb47",
    MANIFEST: "948d26808de0290e210aec28e03cc29a31d3c84cd65a8d73635c3973e935b8d7",
}
DRAWING_IDS = ("01-local-attachment", "02-load-paths", "03-test-article", "04-coupled-cases")
DRAWING_LABELS = ("Local attachment", "Load paths", "Representative test article", "Coupled cases")


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _snapshot(root: Path) -> dict[str, bytes]:
    snapshots = {path: (root / path).read_bytes() for path in PINS}
    if any(_digest(snapshots[path]) != pin for path, pin in PINS.items()):
        raise ValueError("Connection source hash mismatch")
    manifest = json.loads(snapshots[MANIFEST])
    if (
        manifest["identity"] != rp1_inspection.ID
        or manifest["sources"].get(SPEC) != PINS[SPEC]
        or manifest["specification"] != {"path": DEFINITION, "sha256": PINS[DEFINITION]}
        or manifest["record"] != {"path": AD1, "sha256": PINS[AD1]}
    ):
        raise ValueError("Drawing manifest source mismatch")
    entries = manifest["artifacts"]
    if tuple(a["id"] for a in entries) != DRAWING_IDS:
        raise ValueError("Drawing identity mismatch")
    for entry in entries:
        path, expected = entry["svg"]["path"], entry["svg"]["sha256"]
        if path != f"output/rp1-attachment-definition/{entry['id']}.svg":
            raise ValueError("Unexpected drawing path")
        snapshots[path] = (root / path).read_bytes()
        if _digest(snapshots[path]) != expected:
            raise ValueError("Drawing hash mismatch")
    return snapshots


def build(root: Path) -> dict[str, Any]:
    data = _snapshot(root)
    spec = yaml.safe_load(data[SPEC])
    definition = yaml.safe_load(data[DEFINITION])
    ad1 = json.loads(data[AD1])
    d1 = json.loads(data[D1])
    manifest = json.loads(data[MANIFEST])
    if (
        spec["id"] != rp1_inspection.ID
        or definition["id"] != rp1_inspection.ID
        or ad1["identity"] != rp1_inspection.ID
        or ad1["adopted"] is not False
        or d1["id"] != "RP1-D1-load-attachment-decision-v1"
        or d1["sources"].get(SPEC) != PINS[SPEC]
        or d1["sources"].get(AD1) != PINS[AD1]
        or ad1["sources"].get(SPEC) != PINS[SPEC]
        or ad1["sources"].get(DEFINITION) != PINS[DEFINITION]
    ):
        raise ValueError("Connection source identity/linkage mismatch")
    part_ids = [part["id"] for part in spec["parts"]]
    if len(part_ids) != 55 or len(set(part_ids)) != 55:
        raise ValueError("Connection source part coverage mismatch")
    parts = {part["id"]: part for part in spec["parts"]}
    fin, fj, route, required = (
        parts["fin_set"]["geometry"],
        definition["fin_joints"],
        definition["route"],
        d1["required_case"],
    )
    sources = [
        {"id": key, "path": path, "sha256": PINS[path]}
        for key, path in [
            ("spec", SPEC),
            ("definition", DEFINITION),
            ("ad1-record", AD1),
            ("d1-record", D1),
            ("ad1-decision", AD1_DOC),
            ("d1-decision", D1_DOC),
            ("drawing-manifest", MANIFEST),
        ]
    ]
    drawings = [
        {
            "id": entry["id"],
            "label": label,
            "path": entry["svg"]["path"],
            "sha256": entry["svg"]["sha256"],
            "status": "Saved source-dimensioned concept; not manufacturing CAD or browser verification",
        }
        for entry, label in zip(manifest["artifacts"], DRAWING_LABELS, strict=True)
    ]

    def node(id: str, label: str, ids: list[str], note: str) -> dict[str, Any]:
        return {"id": id, "label": label, "part_ids": ids, "note": note}

    def edge(id: str, source: str, target: str, label: str, note: str) -> dict[str, str]:
        return {"id": id, "from": source, "to": target, "label": label, "note": note}

    def dimension(
        id: str, label: str, value: Any, unit: str, source_id: str, note: str
    ) -> dict[str, Any]:
        return {
            "id": id,
            "label": label,
            "value": value,
            "unit": unit,
            "source_id": source_id,
            "note": note,
        }

    def finding(
        id: str, label: str, status: str, detail: str, source_id: str, measurement: str
    ) -> dict[str, str]:
        return {
            "id": id,
            "label": label,
            "status": status,
            "detail": detail,
            "source_id": source_id,
            "measurement_needed": measurement,
        }

    fin_nodes = [
        node(
            "pressure",
            "Distributed fin load",
            [],
            "Retained per-fin force and moment, not measured flight loads.",
        ),
        node(
            "panel",
            "Fin panel",
            ["fin_set"],
            "One integral fin and tab; source dimensions are estimates.",
        ),
        node(
            "tab",
            "Integral fin tab",
            ["fin_tabs"],
            "Finite stiffness; no front-ring contact or rigid support assumed.",
        ),
        node(
            "external",
            "External fillets and wedges",
            ["outer_fin_fillets", "root_gussets", "root_extra_bond_finish"],
            "One parallel load route into the body.",
        ),
        node(
            "internal",
            "Internal tab bonds",
            ["fin_internal_bonds"],
            "Parallel bond route into the motor tube; peel and slip unknown.",
        ),
        node(
            "tube",
            "Motor tube",
            ["motor_tube"],
            "Finite tube ovalization and torsion remain unknown.",
        ),
        node(
            "ring-bonds",
            "Ring bore and perimeter bonds",
            ["ring_bonds"],
            "Actual bond reaction split and stiffness are unknown.",
        ),
        node(
            "aft-end",
            "Aft tab-end adhesive",
            [],
            "No direct butt contact is credited across the proposed gap.",
        ),
        node(
            "aft-ring",
            "Aft ring",
            ["aft_ring"],
            "Finite ring, bond and body deformation require evidence.",
        ),
        node(
            "body",
            "Body shell",
            ["body"],
            "Body flexibility and global bending remain unavailable.",
        ),
        node(
            "forward-ring",
            "Forward ring",
            ["forward_ring"],
            "Forward of tab; not a direct front-tab support.",
        ),
    ]
    fin_edges = [
        edge(
            "pressure-panel",
            "pressure",
            "panel",
            "Distributed fin load",
            "Equivalent resultant; not a single tip force.",
        ),
        edge("panel-tab", "panel", "tab", "Integral panel to tab", "No rigid-root claim."),
        edge(
            "panel-external",
            "panel",
            "external",
            "Parallel external fillet route",
            "No equal sharing or uniform peel assumed.",
        ),
        edge(
            "external-body",
            "external",
            "body",
            "Fillets to body",
            "Capacity and finite compliance unknown.",
        ),
        edge(
            "tab-internal",
            "tab",
            "internal",
            "Parallel motor-side bond route",
            "Actual contact and joint stiffness not established.",
        ),
        edge("internal-tube", "internal", "tube", "Bonds to tube", "Tube is not a rigid mandrel."),
        edge(
            "tube-ring-bonds",
            "tube",
            "ring-bonds",
            "Tube to ring bore bonds",
            "Force split depends on finite stiffness and contact.",
        ),
        edge(
            "ring-bonds-body",
            "ring-bonds",
            "body",
            "Ring perimeter to body",
            "No assumed equal load sharing.",
        ),
        edge(
            "tab-aft-end",
            "tab",
            "aft-end",
            "Aft tab adhesive",
            "Adhesive gap; no direct butt stop.",
        ),
        edge(
            "aft-end-ring",
            "aft-end",
            "aft-ring",
            "Aft adhesive to aft ring",
            "Finite stiffness and capacity unknown.",
        ),
        edge(
            "aft-ring-body",
            "aft-ring",
            "body",
            "Aft ring to body",
            "Body and ring motion remain unknown.",
        ),
    ]
    recovery_nodes = [
        node(
            "canopy",
            "Canopy and bridle",
            ["parachute"],
            "Nominal packing and opening remain unverified.",
        ),
        node(
            "junction",
            "Distal connector junction",
            ["recovery_connectors"],
            "Product and capacities unresolved; separate nose branch.",
        ),
        node(
            "nylon",
            "Uncut nylon and sewn loops",
            ["shock_cord"],
            "55 g estimate; 68 g is an unverified sensitivity, not a bound.",
        ),
        node(
            "leader",
            "Leader eye and cord",
            ["rp1_kevlar_wrap"],
            "Proposed knots and finished capacity unverified.",
        ),
        node(
            "choker",
            "Tube choker and ring contact",
            ["rp1_kevlar_wrap", "forward_ring", "rp1_notch_sealer"],
            "Local force entry; contact, chafe and finishing not qualified.",
        ),
        node(
            "sleeve",
            "Protective sleeve",
            ["ad1_cord_sleeve"],
            "Forward of ring; not load bearing and not in notch.",
        ),
        node("mount", "Motor tube", ["motor_tube"], "Finite tube and ring joints receive load."),
        node(
            "rings",
            "Ring and bonds",
            ["forward_ring", "ring_bonds"],
            "Inner and outer load sharing depends on contact and stiffness.",
        ),
        node(
            "body",
            "Continuous body",
            ["body", "upper_body"],
            "Stiffness and contact paths unverified.",
        ),
        node(
            "nose-eye",
            "Nose eye and plate",
            ["nose_recovery_eye", "nose_anchor_plate"],
            "Separate branch, not automatically half the load.",
        ),
    ]
    recovery_edges = [
        edge(
            "canopy-junction",
            "canopy",
            "junction",
            "Bridle to distal junction",
            "Connector capacity remains unknown.",
        ),
        edge(
            "junction-nylon",
            "junction",
            "nylon",
            "Distal sewn nylon loop",
            "Finished loop capacity unavailable.",
        ),
        edge(
            "nylon-leader",
            "nylon",
            "leader",
            "Proximal loop to leader eye hitch",
            "No knot efficiency credited.",
        ),
        edge(
            "leader-choker",
            "leader",
            "choker",
            "Leader to tube choker",
            "Actual contact and chafe unknown.",
        ),
        edge(
            "choker-mount",
            "choker",
            "mount",
            "Local tube contact",
            "No uniform circumference pressure assumed.",
        ),
        edge(
            "choker-rings",
            "choker",
            "rings",
            "Local ring/annulus contact",
            "Ring load partition unknown.",
        ),
        edge("mount-rings", "mount", "rings", "Tube to ring bonds", "Bond force split unknown."),
        edge(
            "rings-body",
            "rings",
            "body",
            "Ring perimeter to body",
            "Finite compliance and joints remain unverified.",
        ),
        edge(
            "junction-nose",
            "junction",
            "nose-eye",
            "Separate nose branch",
            "No equal half-force assumption.",
        ),
    ]
    fin_connection = {
        "id": "fin-root",
        "label": "Fin root and body",
        "summary": "Parallel finite load paths from distributed fin force; no rigid root or equal force sharing.",
        "part_ids": list(dict.fromkeys(p for n in fin_nodes for p in n["part_ids"])),
        "nodes": fin_nodes,
        "edges": fin_edges,
        "dimensions": [
            dimension(
                "span",
                "Fin span",
                fin["span_m"],
                "m",
                "spec",
                "Source planform, not installed measurement.",
            ),
            dimension("root", "Root chord", fin["root_chord_m"], "m", "spec", "Source planform."),
            dimension("tip", "Tip chord", fin["tip_chord_m"], "m", "spec", "Source planform."),
            dimension(
                "tab-length",
                "Tab length",
                fj["tab_length_mm"],
                "mm",
                "definition",
                "Proposed source definition.",
            ),
            dimension(
                "aft-tab-end",
                "Aft tab end station",
                fj["aft_tab_end_mm"],
                "mm",
                "definition",
                "Aft from nose datum.",
            ),
            dimension(
                "aft-ring-front",
                "Aft ring front station",
                fj["aft_ring_front_mm"],
                "mm",
                "definition",
                "Aft from nose datum; adhesive gap, no direct butt support.",
            ),
            dimension(
                "force",
                "Retained factored per-fin force",
                required["force_N"],
                "N",
                "d1-record",
                "Consistent with retained moment; factor already applied.",
            ),
            dimension(
                "moment",
                "Retained factored per-fin moment",
                required["moment_Nm"],
                "N·m",
                "d1-record",
                "Factor applied once; not measured flight load.",
            ),
        ],
        "findings": [
            finding(
                "wood-failed",
                "AD1 optimistic wood component screen failed",
                "failed-screen",
                "Saved optimistic bonded wood component model exceeds retained motion and material screens; it does not include validated installed root.",
                "ad1-record",
                "Conditioned material response and complete-root behavior require a separately authorized representative method.",
            ),
            finding(
                "installed-unknown",
                "Installed root displacement and peel unavailable",
                "unknown",
                "Finite tab, bonds, tube, ring and body stiffness/peel are not measured; no installed pass.",
                "ad1-record",
                "Later measure complete-root response and joint behavior under an accepted, authorized protocol.",
            ),
            finding(
                "force-rule",
                "Retained load and 1 mm limit",
                "requirement",
                "331.125 N and 8.83 N·m already include design factor 3 once; complete tip movement plus uncertainty remains limited to 1 mm.",
                "d1-decision",
                "Validate distributed panel load transformation and complete root before an acceptance claim.",
            ),
        ],
        "drawing_ids": ["01-local-attachment", "02-load-paths", "03-test-article"],
    }
    recovery = {
        "id": "recovery",
        "label": "Recovery leader and load path",
        "summary": "Nylon, leader and tube choker with separate nose branch; no equal split or qualified finished attachment.",
        "part_ids": list(dict.fromkeys(p for n in recovery_nodes for p in n["part_ids"])),
        "nodes": recovery_nodes,
        "edges": recovery_edges,
        "dimensions": [
            dimension(
                "motor-tube",
                "Motor tube station interval",
                route["motor_tube_mm"],
                "mm",
                "definition",
                "Aft from nose datum.",
            ),
            dimension(
                "forward-ring",
                "Forward ring station interval",
                route["forward_ring_mm"],
                "mm",
                "definition",
                "Aft from nose datum.",
            ),
            dimension(
                "wrap",
                "Choker station interval",
                route["wrap_axial_mm"],
                "mm",
                "definition",
                "Proposed concept.",
            ),
            dimension(
                "notch-width",
                "Notch width",
                route["passage_width_mm"],
                "mm",
                "definition",
                "Proposed cut; fit and conditioned clearance not established.",
            ),
            dimension(
                "notch-depth",
                "Notch radial depth",
                route["passage_depth_mm"],
                "mm",
                "definition",
                "Proposed cut; actual section unverified.",
            ),
            dimension(
                "knot-angle",
                "Knot sector",
                route["passage_angle_deg"],
                "deg",
                "definition",
                "First fin at 0 degrees.",
            ),
            dimension(
                "sleeve",
                "Protective sleeve station interval",
                route["heat_abrasion_sleeve"]["axial_station_mm"],
                "mm",
                "definition",
                "Sleeve ends ahead of ring, outside notch.",
            ),
            dimension(
                "finished-capacity",
                "Finished attachment capacity",
                ad1["recovery_connections"]["finished_attachment_capacity_N"],
                "N",
                "ad1-record",
                "Unknown, not zero.",
            ),
        ],
        "findings": [
            finding(
                "finished-unknown",
                "Finished cord and connection capacity unavailable",
                "unknown",
                "Raw product ratings do not establish finished knot, sewn loop, connector, or ring capacity.",
                "ad1-decision",
                "A separately authorized representative test must characterize actual terminations and connections.",
            ),
            finding(
                "fit-unknown",
                "Notch, dressed knot and sleeve fit unavailable",
                "unknown",
                "Nominal envelope and cold clearance do not establish a real conditioned moving-cord fit or chafe/thermal capacity.",
                "ad1-decision",
                "Inspect actual supplied geometry, dressed knot, clearance, routing and sleeve after separate physical-work authorization.",
            ),
            finding(
                "separate-path",
                "Unequal and separate load routes",
                "requirement",
                "Tautening and snagged or slack branches can load differently; no equal share or uniform circumferential pressure is credited.",
                "ad1-decision",
                "Characterize contact and reactions before adopting load sharing.",
            ),
        ],
        "drawing_ids": ["01-local-attachment", "02-load-paths", "04-coupled-cases"],
    }
    connections = [fin_connection, recovery]
    valid = set(part_ids)
    for connection in connections:
        if not set(connection["part_ids"]) <= valid or any(
            not set(n["part_ids"]) <= valid for n in connection["nodes"]
        ):
            raise ValueError("Connection references unknown part IDs")
    result = {
        "schema_version": 1,
        "id": ID,
        "configuration": {"id": rp1_inspection.ID, "path": SPEC, "sha256": PINS[SPEC]},
        "status": "Source-linked unadopted concepts; no physical qualification or flight release",
        "part_ids": part_ids,
        "sources": sources,
        "drawings": drawings,
        "connections": connections,
    }
    if _snapshot(root) != data:
        raise ValueError("Connection source changed during export")
    return result


def asset(root: Path, drawing_id: str) -> tuple[Path, str]:
    """Resolve one allowlisted, source-pinned existing drawing; reject unknown IDs."""
    if drawing_id not in DRAWING_IDS:
        raise ValueError("Unknown drawing ID")
    document = build(root)
    entry = next(d for d in document["drawings"] if d["id"] == drawing_id)
    return root / entry["path"], entry["sha256"]
