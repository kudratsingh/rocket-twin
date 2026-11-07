"""Read-only verified AD1 inspection geometry, separate from canonical analysis CAD."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from src.inspection.rp1_geometry import EVIDENCE, FOLDER, GEOMETRY_ID, audit, sha, sources


def _path(root: Path, relative: str) -> Path:
    folder = (root / FOLDER).resolve()
    if not folder.is_relative_to(root.resolve()):
        raise ValueError("Inspection geometry folder escapes repository")
    path = (root / relative).resolve()
    if not path.is_relative_to(folder) or path.suffix != ".glb":
        raise ValueError("Inspection geometry asset path escapes allowlist")
    return path


def build(root: Path) -> dict[str, Any]:
    """Return all 55 audited records and verify generated meshes against saved evidence.

    Missing output raises FileNotFoundError; source-only callers may retain their
    existing explicit unavailable-geometry state. This function never generates.
    """
    expected = audit(root)
    expected_sources = sources(root)
    evidence_bytes = (root / EVIDENCE).read_bytes()
    output_bytes = (root / FOLDER / "manifest.json").read_bytes()
    if evidence_bytes != output_bytes:
        raise ValueError("Inspection geometry manifest differs from saved evidence")
    manifest: dict[str, Any] = json.loads(output_bytes)
    source = expected["source"]
    geometry_sha = sha(
        json.dumps(
            {"sources": expected_sources, "geometry_id": GEOMETRY_ID}, sort_keys=True
        ).encode()
    )
    identity = {**source["identity"], "inspection_geometry_sha256": geometry_sha}
    counts = dict(Counter(row["maturity"] for row in expected["parts"]))
    if (
        manifest["id"] != source["id"]
        or manifest["geometry_id"] != GEOMETRY_ID
        or manifest["sources"] != expected_sources
        or manifest["identity"] != identity
        or manifest["coverage"]
        != {
            "source_parts": 55,
            "mesh_parts": counts.get("source_dimensioned", 0)
            + counts.get("simplified_envelope", 0),
            "by_maturity": counts,
            "complete_installed_geometry": False,
        }
        or manifest["identity"]["specification_sha256"]
        != source["identity"]["specification_sha256"]
        or manifest["identity"]["resolved_spec_sha256"] is not None
        or manifest["identity"]["cad_revision_sha256"] is not None
        or manifest["mass_or_inertia_generated"] is not False
        or manifest["engineering_accepted"] is not False
        or manifest["flight_ready"] is not False
    ):
        raise ValueError("Inspection geometry source or identity mismatch")
    if len(manifest["parts"]) != len(expected["parts"]):
        raise ValueError("Inspection geometry coverage mismatch")
    for row, baseline in zip(manifest["parts"], expected["parts"], strict=True):
        if any(
            row[key] != value for key, value in baseline.items() if key not in ("mesh", "bounds_m")
        ):
            raise ValueError("Inspection geometry part linkage mismatch")
        mesh = row["mesh"]
        represented = row["maturity"] in ("source_dimensioned", "simplified_envelope")
        if represented != (mesh is not None):
            raise ValueError("Inspection geometry part representation mismatch")
        if mesh is not None:
            if mesh["path"] != f"{FOLDER}/parts/{row['id']}.glb" or mesh["units"] != "m":
                raise ValueError("Inspection geometry mesh identity mismatch")
            if sha(_path(root, mesh["path"]).read_bytes()) != mesh["sha256"]:
                raise ValueError("Inspection geometry mesh hash mismatch")
    assembly = manifest["assembly"]
    if (
        assembly["path"] != f"{FOLDER}/assembly.glb"
        or sha(_path(root, assembly["path"]).read_bytes()) != assembly["sha256"]
    ):
        raise ValueError("Inspection geometry assembly hash mismatch")
    if (root / EVIDENCE).read_bytes() != evidence_bytes or (
        root / FOLDER / "manifest.json"
    ).read_bytes() != output_bytes:
        raise ValueError("Inspection geometry manifest changed during read")
    if sources(root) != expected_sources:
        raise ValueError("Inspection geometry sources changed during read")
    return manifest


def asset(root: Path, part_id: str) -> tuple[Path, str]:
    """Resolve one stable source part ID, or assembly, with its verified SHA-256."""
    document = build(root)
    if part_id == "assembly":
        row = document["assembly"]
    else:
        part = next((p for p in document["parts"] if p["id"] == part_id), None)
        if part is None or part["mesh"] is None:
            raise ValueError("Unknown or unavailable inspection part mesh")
        row = part["mesh"]
    path = _path(root, row["path"])
    # Recheck the returned file after manifest validation to close ordinary drift.
    if sha(path.read_bytes()) != row["sha256"]:
        raise ValueError("Inspection geometry mesh changed during read")
    return path, row["sha256"]
