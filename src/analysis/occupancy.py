"""Geometry-derived solid/void allocation for offline thermal interfaces.

Disjoint CAD intersections partition ONE physical interface volume. A thin
mid-radius probe supplies an area estimate separately from full bond volume;
probe refinement is recorded instead of silently assigning full area to both
air and adhesive. This module identifies occupancy, not temperature, contact
quality or optical view factors. Radiation visibility requires first-hit
geometry, as in finite_radiation/cad_radiation; area alone is not visibility.

Reference: conservation of volume for disjoint control volumes, Bergman et al.,
Fundamentals of Heat and Mass Transfer, 7th ed., chapters 1 and 3. All incoming
CAD lengths are mm; this public interface reports mm, mm2 and mm3 explicitly.
"""

from __future__ import annotations

import math
from typing import Any

import cadquery as cq


def annulus(inner_mm: float, outer_mm: float, start_mm: float, length_mm: float) -> Any:
    if not (0 < inner_mm < outer_mm and length_mm > 0):
        raise ValueError("Positive ordered annulus dimensions required")
    return (
        cq.Workplane("XY")
        .circle(outer_mm)
        .circle(inner_mm)
        .extrude(length_mm)
        .translate((0, 0, start_mm))
        .val()
    )


def partition(
    region: Any, materials: dict[str, Any], tolerance_mm3: float = 1e-6
) -> dict[str, Any]:
    """Reject positive solid overlap; retain genuinely unoccupied geometry.

    Caller supplies physical solids only: budget boxes, flexible stowage and
    unmodeled adhesive allowances must not be credited as opaque material.
    """
    if not region.isValid() or region.Volume() <= 0:
        raise ValueError("Interface region is invalid or empty")
    clipped = {name: region.intersect(shape) for name, shape in materials.items()}
    overlaps = []
    for i, (name, shape) in enumerate(clipped.items()):
        if not shape.isValid():
            raise ValueError(f"Invalid material intersection: {name}")
        if shape.Volume() == 0:
            continue
        for other, previous in list(clipped.items())[:i]:
            if previous.Volume() == 0:
                continue
            value = float(shape.intersect(previous).Volume())
            if value > tolerance_mm3:
                overlaps.append({"a": name, "b": other, "volume_mm3": value})
    if overlaps:
        raise ValueError(f"Overlapping physical interface materials: {overlaps}")
    nonempty = [s for s in clipped.values() if s.Volume() > 0]
    empty = region.cut(*nonempty) if nonempty else region
    total = float(region.Volume())
    occupied = {name: float(shape.Volume()) for name, shape in clipped.items()}
    void = float(empty.Volume())
    residual = total - sum(occupied.values()) - void
    if not empty.isValid() or abs(residual) > max(tolerance_mm3, 1e-7 * total):
        raise ValueError(f"Solid/void partition fails volume balance: {residual} mm3")
    return {
        "total_volume_mm3": total,
        "material_volume_mm3": occupied,
        "open_volume_mm3": void,
        "material_volume_fractions": {name: v / total for name, v in occupied.items()},
        "open_volume_fraction": void / total,
        "volume_balance_residual_mm3": residual,
        "positive_material_overlap_mm3": 0.0,
        "occupancy_basis": "nominal actual CAD intersections; no assumed wetting or tolerance claim",
    }


def cylindrical_interface(
    inner_mm: float,
    outer_mm: float,
    start_mm: float,
    length_mm: float,
    materials: dict[str, Any],
    probe_thicknesses_mm: tuple[float, ...] = (0.1, 0.01, 0.001),
) -> dict[str, Any]:
    """Physical gap partition plus independently refined mid-radius areas.

    For a symmetric thin annulus, V/probe_thickness equals cylindrical area
    exactly for an uncut or angle-sector face. Other cut boundaries can vary
    with radius; the refinements expose that dependence. This is not proof
    that a path stays open across the entire radial thickness or sees a
    particular remote surface. End/slot visibility remains a ray problem.
    """
    gap = outer_mm - inner_mm
    midpoint = (outer_mm + inner_mm) / 2
    result = partition(annulus(inner_mm, outer_mm, start_mm, length_mm), materials)
    rows = []
    for thickness in probe_thicknesses_mm:
        if thickness <= 0 or thickness > gap:
            raise ValueError("Probe must be positive and contained within the radial gap")
        p = partition(
            annulus(midpoint - thickness / 2, midpoint + thickness / 2, start_mm, length_mm),
            materials,
        )
        rows.append(
            {
                "probe_thickness_mm": thickness,
                "total_area_mm2": p["total_volume_mm3"] / thickness,
                "material_area_mm2": {
                    k: v / thickness for k, v in p["material_volume_mm3"].items()
                },
                "open_area_mm2": p["open_volume_mm3"] / thickness,
                "area_balance_residual_mm2": p["volume_balance_residual_mm3"] / thickness,
            }
        )
    return {
        "inner_radius_mm": inner_mm,
        "outer_radius_mm": outer_mm,
        "bond_or_gap_thickness_mm": gap,
        "start_station_mm": start_mm,
        "axial_length_mm": length_mm,
        "independent_full_cylinder_area_mm2": 2 * math.pi * midpoint * length_mm,
        **result,
        "area_probe_refinements": rows,
        "area_resolution_scope": "mid-radius geometric occupancy only; radial continuity and visibility separate",
    }
