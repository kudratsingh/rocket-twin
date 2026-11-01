"""Historical G12 layered-fin geometry; provenance, not an adopted design.

Extracted without AST changes from scripts/wo03_trainer_fin_root.py SHA-256
479e1f2035ca71d65af1f28316a4f3af4dc2684eac1def04703e9107a674e5e4.
Function AST SHA-256 (ast.dump include_attributes=False, Python 3.11):
_part df0fbfda64ddab9f47d29fe0d851653196c81873b3bf9ee351520ea63a3c2218;
layered_shapes e6aa54c044af9ddcbe5db1a425779425c152649358df0df7801114d8810bc5b4.
Shapes are nominal and do not establish material qualification.
"""

from __future__ import annotations

from typing import Any

from src.cad.parts import box, compound, cq, tube
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Vehicle


def _part(vehicle: Vehicle, ident: str):  # type: ignore[no-untyped-def]
    return next(p for p in vehicle.parts if p.id == ident)


def layered_shapes(v: Vehicle, c: dict[str, Any]) -> list[tuple[str, Any, float]]:
    """Explicit nonoverlapping nominal material solids for one three-fin set.

    Carbon density is derived from supplier areal mass / stated actual thickness.
    The cap's thin adhesive is charged as an equivalent cured mass, not hidden in
    its laminate density. Main root potting is the actual trimmed channel void.
    """
    fin = _part(v, "fin_set")
    assert fin.cad
    g, p = fin.geometry, fin.cad.parameters
    r, span, chord = (g[k] * 1000 for k in ("radius_m", "span_m", "root_chord_m"))
    core, skin, bond, band = (
        c[k] * 1000
        for k in ("core_thickness_m", "skin_thickness_m", "face_bond_thickness_m", "root_band_m")
    )
    outer = core / 2 + bond + skin
    foot = c["foot_bond_thickness_m"] * 1000
    side_bond = c["gusset_face_bond_thickness_m"] * 1000
    body = cq.Solid.makeCylinder(r, chord + 2, cq.Vector(0, 0, -1))
    body_plus = cq.Solid.makeCylinder(r + foot, chord + 2, cq.Vector(0, 0, -1))
    skin_density = c["skin_areal_mass_kg_m2"] / c["skin_thickness_m"]
    tab = box(p["tab_depth_mm"], core, p["tab_length_mm"]).translate(
        (r - p["tab_depth_mm"] / 2, 0, p["tab_offset_mm"])
    )
    root = box(band, core, chord).translate((r + band / 2, 0, 0)).fuse(tab)
    one = [
        ("root_insert_and_tab", root, DENSITY_KG_M3["plywood"]),
        (
            "foam_core",
            box(span - band, core, chord).translate((r + band + (span - band) / 2, 0, 0)),
            c["core_density_kg_m3"],
        ),
    ]
    for side in (-1, 1):
        one += [
            (
                f"skin_{side}",
                box(span, skin, chord).translate(
                    (r + span / 2, side * (core / 2 + bond + skin / 2), 0)
                ),
                skin_density,
            ),
            (
                f"face_bond_{side}",
                box(span, bond, chord).translate((r + span / 2, side * (core / 2 + bond / 2), 0)),
                DENSITY_KG_M3["epoxy"],
            ),
        ]
        wedge = (
            cq.Workplane("XY")
            .polyline(
                [
                    (r - p["root_gusset_inset_mm"], side * (outer + side_bond)),
                    (
                        r - p["root_gusset_inset_mm"],
                        side * (outer + side_bond + p["root_gusset_base_mm"]),
                    ),
                    (r + p["root_gusset_span_mm"], side * (outer + side_bond)),
                ]
            )
            .close()
            .extrude(chord)
            .val()
        )
        one += [
            (f"gusset_{side}", wedge.cut(body_plus), DENSITY_KG_M3["plywood"]),
            (f"foot_bond_{side}", wedge.intersect(body_plus).cut(body), DENSITY_KG_M3["epoxy"]),
            (
                f"gusset_face_bond_{side}",
                box(band, side_bond, chord)
                .translate((r + band / 2, side * (outer + side_bond / 2), 0))
                .cut(body_plus),
                DENSITY_KG_M3["epoxy"],
            ),
        ]
    # Fill only the actual channel void inside the G11 outer cylinder. Its
    # shared faces meet the channel walls/floor and the solid plywood tab.
    frame = _part(v, "gimbal_frame")
    assert frame.cad
    fp = frame.cad.parameters
    channel = (
        box(fp["fin_channel_depth_mm"], fp["fin_slot_width_mm"], p["tab_length_mm"])
        .translate((fp["fin_channel_radius_mm"], 0, p["tab_offset_mm"]))
        .intersect(cq.Solid.makeCylinder(frame.geometry["radius_m"] * 1000, chord))
    )
    one.append(("tab_potting", channel.cut(root), DENSITY_KG_M3["epoxy"]))
    shell = _part(v, "aft_shell")
    gap_inner = frame.geometry["radius_m"] * 1000
    gap_outer = shell.geometry["inner_radius_m"] * 1000
    if gap_outer <= gap_inner:
        raise ValueError("Root-gap backing hypothesis requires a positive frame/shell gap")
    backing = (
        tube(gap_outer, gap_inner, chord)
        .intersect(box(10, fp["rail_width_mm"], chord).translate((gap_inner, 0, 0)))
        .cut(
            box(10, fp["fin_slot_width_mm"], p["tab_length_mm"]).translate(
                (gap_inner, 0, p["tab_offset_mm"])
            )
        )
    )
    one.append(("frame_shell_gap_bond", backing, DENSITY_KG_M3["epoxy"]))
    cap = c["edge_cap_thickness_m"] * 1000
    lap = c["edge_cap_overlap_m"] * 1000
    for aft in (False, True):
        z0 = chord if aft else -cap
        web = box(span, 2 * outer, cap).translate((r + span / 2, 0, z0))
        for side in (-1, 1):
            # Close the foam span only. Root-band gussets occupy these face
            # corners; do not let glass laps overlap the actual wood solids.
            flange = box(span - band, cap, lap).translate(
                (r + band + (span - band) / 2, side * (outer + cap / 2), chord - lap if aft else 0)
            )
            one.append((f"cap_lap_{aft}_{side}", flange, DENSITY_KG_M3["fiberglass"]))
        one.append((f"cap_web_{aft}", web, DENSITY_KG_M3["fiberglass"]))
    return [
        (name, compound([shape.rotate((0, 0, 0), (0, 0, 1), i * 120) for i in range(3)]), density)
        for name, shape, density in one
    ]
