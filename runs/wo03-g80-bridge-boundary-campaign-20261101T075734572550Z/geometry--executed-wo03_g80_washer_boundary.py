"""Strict, washer-only boundary sizing proposal; does not create a mesh."""

from __future__ import annotations

import hashlib
import math
from pathlib import Path

import numpy as np


def verify_source_hashes(root, config):
    """Verify original source files; callers obtain centers from those STEP faces."""
    actual = {}
    for item in [config["bridge_step"], *config["washer_center_source_step"]]:
        path = Path(root) / item["path"]
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        if value != item["sha256"]:
            raise ValueError(f"Source hash mismatch: {path}")
        actual[item["path"]] = value
    return actual


def _circle(gmsh, tag, center, radius, tolerance):
    if gmsh.model.getType(1, tag) != "Circle":
        raise ValueError(f"Unsupported non-circle boundary curve {tag}")
    bounds = gmsh.model.getParametrizationBounds(1, tag)
    lo, hi = float(bounds[0][0]), float(bounds[1][0])
    if not math.isfinite(lo + hi) or hi <= lo:
        raise ValueError(f"Invalid circle parameter bounds {tag}")
    parameters = [lo + (hi - lo) * u for u in (0.0, 0.25, 0.5, 0.75, 1.0)]
    points = np.asarray(gmsh.model.getValue(1, tag, parameters)).reshape(-1, 3)
    center = np.asarray(center, dtype=float)
    if center.shape != (3,) or not np.isfinite(points).all():
        raise ValueError("Invalid center or sampled circle")
    if np.max(np.abs(points[:, 2] - center[2])) > tolerance:
        raise ValueError(f"Curve {tag} outside source washer plane")
    if np.max(np.abs(np.linalg.norm(points[:, :2] - center[:2], axis=1) - radius)) > tolerance:
        raise ValueError(f"Curve {tag} does not match source-centered radius")
    length = float(gmsh.model.occ.getMass(1, tag))
    if (
        not math.isfinite(length)
        or length <= tolerance
        or length > 2 * math.pi * radius + tolerance
    ):
        raise ValueError(f"Unsupported circle trim or arc length on {tag}")
    # A Gmsh circle has constant-radius parametrization in radians; verify trimming.
    if abs(length / radius - (hi - lo)) > tolerance / radius * 4:
        raise ValueError(f"Unsupported parametrization for circle {tag}")
    return length


def apply_washer_boundary(
    gmsh,
    patches,
    *,
    outer_radius=4.5,
    inner_radius=1.7,
    outer_segments=96,
    inner_segments=32,
    tolerance=1e-5,
):
    """Select verified full washer rings and size only their existing OCC curves.

    Each patch has `face_tags` and the matching verified STEP `center_xyz_mm`.
    Curves shared by adjacent Gmsh faces retain their existing tags and therefore
    receive one conformal discretization. Unsupported partial rings are rejected.
    """
    if outer_radius <= inner_radius or inner_radius <= 0 or min(outer_segments, inner_segments) < 3:
        raise ValueError("Invalid boundary specification")
    assignments = {}
    reports = []
    for index, patch in enumerate(patches):
        faces = [(2, int(face)) for face in patch["face_tags"]]
        if not faces:
            raise ValueError("Patch owns no face")
        all_faces = set(faces)
        if len(all_faces) != len(faces):
            raise ValueError("Duplicate patch face")
        # Combined boundary removes internal edges between split patch faces.
        boundary = gmsh.model.getBoundary(faces, combined=True, oriented=False, recursive=False)
        tags = sorted({int(tag) for dim, tag in boundary if dim == 1})
        if not tags:
            raise ValueError("Patch owns no exterior curves")
        grouped = {"outer": [], "inner": []}
        for tag in tags:
            matches = []
            for label, radius in [("outer", outer_radius), ("inner", inner_radius)]:
                try:
                    length = _circle(gmsh, tag, patch["center_xyz_mm"], radius, tolerance)
                except ValueError:
                    continue
                matches.append((label, length))
            if len(matches) != 1:
                raise ValueError(f"Unsupported or ambiguous washer boundary curve {tag}")
            label, length = matches[0]
            grouped[label].append((tag, length))
        detail = []
        for label, radius, count in [
            ("outer", outer_radius, outer_segments),
            ("inner", inner_radius, inner_segments),
        ]:
            group = grouped[label]
            if not group or abs(
                sum(length for _, length in group) - 2 * math.pi * radius
            ) > tolerance * max(4, len(group)):
                raise ValueError(f"Unsupported incomplete or overlapping {label} ring")
            for tag, length in group:
                segments = max(1, math.ceil(count * length / (2 * math.pi * radius) - 1e-10))
                if tag in assignments and assignments[tag] != segments:
                    raise ValueError("Shared boundary has conflicting resolution")
                assignments[tag] = segments
                detail.append(
                    {
                        "curve_tag": tag,
                        "ring": label,
                        "arc_length_mm": length,
                        "segments": segments,
                        "full_circle_equivalent": count,
                    }
                )
        reports.append(
            {"patch_index": index, "center_xyz_mm": list(patch["center_xyz_mm"]), "curves": detail}
        )
    for tag, segments in assignments.items():
        gmsh.model.mesh.setTransfiniteCurve(tag, segments + 1)
    return {
        "patches": reports,
        "sized_curve_tags": sorted(assignments),
        "untouched_other_curves": True,
    }
