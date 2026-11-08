"""Source-preserving RP1 inspection projection; display meshes never resolve physics."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlencode

from src.api import rp1_geometry, rp1_inspection, rp1_presentation


def build(root: Path) -> dict[str, Any]:
    document = rp1_inspection.build(root)
    try:
        geometry = rp1_geometry.build(root)
    except (OSError, ValueError, KeyError) as error:
        document["summary"]["inspection_geometry"] = {
            "status": "unavailable",
            "reason": str(error),
            "source_parts": len(document["parts"]),
            "mesh_parts": 0,
            "complete_installed_geometry": False,
        }
        rp1_presentation.attach(document, root, None)
        return document
    document["identity"]["inspection_geometry_sha256"] = geometry["identity"][
        "inspection_geometry_sha256"
    ]
    document["mesh_frame"] = geometry["viewer_frame"] + "; metres; already globally placed"
    document["status"] = (
        "Source-derived inspection model; estimates and installed engineering acceptance open"
    )
    document["description"] = (
        "Frozen AD1 v2 with separately identified display geometry. Source-dimensioned ideal solids "
        "and simplified envelopes do not supply canonical inertia, engineering CAD or flight approval."
    )
    document["summary"]["inspection_geometry"] = {
        **geometry["coverage"],
        "id": geometry["geometry_id"],
        "status": "source-derived display representation",
        "geometry_sha256": geometry["identity"]["inspection_geometry_sha256"],
        "bounds_m": geometry["bounds_m"],
        "frame": geometry["viewer_frame"],
        "source_datum": geometry["source_datum"],
        "units": geometry["units"],
        "mass_or_inertia_generated": False,
        "engineering_accepted": False,
    }
    audited = {row["id"]: row for row in geometry["parts"]}
    if set(audited) != {part["id"] for part in document["parts"]}:
        raise ValueError("RP1 geometry/source part set mismatch")
    for part in document["parts"]:
        row = audited[part["id"]]
        part["representation"] = {
            **part["representation"],
            "role": row["maturity"],
            "maturity": row["maturity"],
            "description": row["description"],
            "outer_body": part["outer_body"],
            "geometry_source": row.get("source"),
        }
        mesh = row["mesh"]
        part["inspection_shape_sha256"] = row["inspection_shape_sha256"]
        part["inspection_bounds_m"] = row["bounds_m"]
        if mesh is not None:
            query = urlencode(
                {
                    "spec": document["identity"]["specification_sha256"],
                    "geometry": document["identity"]["inspection_geometry_sha256"],
                    "mesh": mesh["sha256"],
                }
            )
            part["mesh_url"] = (
                f"/api/design/{rp1_inspection.ID}/inspection-mesh/{part['id']}?{query}"
            )
            part["color"] = "#89bdcf" if row["maturity"] == "source_dimensioned" else "#d5ac76"
    rp1_presentation.attach(document, root, geometry)
    return document
