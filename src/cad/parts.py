"""Parametric preliminary rocket CAD in millimetres, driven by resolved YAML.

CAD X=body +y, CAD Y=body -z, CAD Z=station aft; this is right handed.
Specific generators keep load paths, joints and mechanisms explicit. Purchased
and flexible components are envelopes with supplied/estimated mass, not solid
bulk-density models. CAD geometric properties are unmeasured manufactured intent.
References: CadQuery 2.8 Workplane/Shape/export documentation; Goldstein ch. 5.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))
import importlib

cq: Any = importlib.import_module("cadquery")
import numpy as np

from src.vehicle.cad_contract import digest
from src.vehicle.geometry import nose_radius
from src.vehicle.schema import Part


def shape_digest(part: Part) -> str:
    return digest(part.geometry, part.cad.model_dump() if part.cad else None)


def tube(ro: float, ri: float, length: float) -> Any:
    return cq.Workplane("XY").circle(ro).circle(ri).extrude(length).val()


def box(x: float, y: float, z: float) -> Any:
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, False)).val()


def compound(solids: list[Any]) -> Any:
    return cq.Compound.makeCompound(solids)


def local_shape(part: Part) -> Any:
    if not part.cad:
        raise ValueError(f"{part.id}: missing CAD definition")
    g = part.geometry
    o = part.cad.parameters
    kind = part.cad.generator
    if kind in ("thrust_plate", "sector_pads", "motor_cassette", "retainer_plate"):
        from src.cad.retention_parts import build_retention

        return build_retention(kind, g, o)
    length = g.get("length_m", g.get("bbox_m", [0])[0]) * 1000
    radius = g.get("radius_m", 0) * 1000
    if kind == "nose":
        # Piecewise-linear revolved ogive, with a separate real hollow shoulder.
        xs = np.linspace(0, length, 81)
        rs = nose_radius(xs, length, radius, g["shape"])
        points = [(float(r), float(z)) for r, z in zip(rs, xs)]
        wall = g["wall_m"] * 1000
        inner = [(max(0, float(r) - wall), float(z)) for r, z in zip(rs[::-1], xs[::-1])]
        shape = (
            cq.Workplane("XZ").polyline(points + inner).close().revolve(360, (0, 0), (0, 1)).val()
        )
        shoulder = tube(
            o["shoulder_outer_mm"], o["shoulder_inner_mm"], o["shoulder_length_mm"]
        ).translate((0, 0, length))
        return shape.fuse(shoulder)
    if kind in ("tube", "liner", "guard", "coupler"):
        shape = tube(radius, g["inner_radius_m"] * 1000, length)
        if kind == "coupler":
            for i, angle in enumerate([0, 120, 240]):
                slot = (
                    box(
                        o.get("key_widths_mm", [o["key_width_mm"]] * 3)[i],
                        o["key_depth_mm"],
                        o["key_length_mm"],
                    )
                    .translate((0, radius, o["key_start_mm"]))
                    .rotate((0, 0, 0), (0, 0, 1), angle)
                )
                shape = shape.cut(slot)
        if o.get("fin_slots"):
            for angle in [0, 120, 240]:
                slot = (
                    box(6, o["fin_slot_width_mm"], o["fin_slot_length_mm"])
                    .translate((radius, 0, o["fin_slot_start_mm"]))
                    .rotate((0, 0, 0), (0, 0, 1), angle)
                )
                shape = shape.cut(slot)
        return shape
    if kind == "joint_stop":
        length = o["ring_thickness_mm"]
        shape = tube(radius, g["inner_radius_m"] * 1000, length)
        keys = [
            box(
                o.get("key_widths_mm", [o["key_width_mm"]] * 3)[i],
                o["key_depth_mm"],
                o["key_length_mm"],
            )
            .translate((0, o["key_radius_mm"], length))
            .rotate((0, 0, 0), (0, 0, 1), a)
            for i, a in enumerate([0, 120, 240])
        ]
        return compound([shape, *keys])
    if kind == "sled":
        width = o["width_mm"]
        thick = o["thickness_mm"]
        # Ladder plate in XZ, thickness along CAD Y.
        shape = box(width, thick, length)
        n = o["windows"]
        pitch = length / n
        for i in range(n):
            cut = box(width - 2 * o["rail_mm"], thick + 2, pitch - o["crossbar_mm"]).translate(
                (0, 0, i * pitch + o["crossbar_mm"] / 2)
            )
            shape = shape.cut(cut)
        for z in [o["end_hole_mm"], length - o["end_hole_mm"]]:
            hole = cq.Solid.makeCylinder(
                o["hole_diameter_mm"] / 2,
                thick + 4,
                cq.Vector(0, -thick / 2 - 2, z),
                cq.Vector(0, 1, 0),
            )
            shape = shape.cut(hole)
        return shape
    if kind == "bulkhead":
        shape = cq.Workplane("XY").circle(radius).extrude(length)
        solid = shape.faces(">Z").workplane().hole(o["anchor_hole_mm"]).val()
        if o.get("relief_sector"):
            relief = o["relief_sector"]
            angles = np.deg2rad(np.linspace(relief["angles_deg"][0], relief["angles_deg"][1], 41))
            points = [
                (relief["keep_radius_mm"] * np.cos(a), relief["keep_radius_mm"] * np.sin(a))
                for a in angles
            ]
            points += [((radius + 2) * np.cos(a), (radius + 2) * np.sin(a)) for a in angles[::-1]]
            solid = solid.cut(cq.Workplane("XY").polyline(points).close().extrude(length).val())
        return solid
    if kind == "anchor":
        stem = cq.Solid.makeCylinder(1.5, length)
        eye = tube(4, 2, 3).translate((0, 0, 0))
        washer = tube(4, 1.7, 1).translate((0, 0, o.get("washer_station_mm", 14)))
        return compound([stem, eye, washer])
    if kind == "mount":
        rings = [
            tube(radius, g["inner_radius_m"] * 1000, thickness).translate((0, 0, z))
            for z, thickness in zip(
                o["ring_stations_mm"],
                o.get("ring_thicknesses_mm", [o["ring_thickness_mm"]] * len(o["ring_stations_mm"])),
                strict=True,
            )
        ]
        rails = []
        for a in [0, 120, 240]:
            rail = box(o["rail_depth_mm"], o["rail_width_mm"], length).translate(
                (o["rail_radius_mm"], 0, 0)
            )
            slot = box(
                o["rail_depth_mm"] + 2,
                o.get("fin_slot_width_mm", 2.4),
                o.get("fin_slot_length_mm", 62),
            ).translate((o["rail_radius_mm"], 0, o.get("tab_slot_start_mm", 65)))
            rails.append(
                (rail if o.get("fin_channels") else rail.cut(slot)).rotate((0, 0, 0), (0, 0, 1), a)
            )
        if o.get("pivot_ring"):
            rings.append(
                tube(radius, g["inner_radius_m"] * 1000, 8).translate(
                    (0, 0, o["pivot_station_mm"] - 4)
                )
            )
        shape = rings[0]
        for other in rings[1:] + rails:
            shape = shape.fuse(other)
        for block in o.get("retainer_blocks", []):
            angle = block["angle_deg"]
            solid = box(*block["size_mm"]).translate(tuple(block["position_mm"]))
            hole = cq.Solid.makeCylinder(
                block["bolt_hole_mm"] / 2,
                block["size_mm"][2] + 2,
                cq.Vector(block["position_mm"][0], 0, block["position_mm"][2] - 1),
            )
            pocket = box(*block["nut_pocket_size_mm"]).translate(
                tuple(block["nut_pocket_position_mm"])
            )
            solid, hole, pocket = [
                item.rotate((0, 0, 0), (0, 0, 1), angle) for item in (solid, hole, pocket)
            ]
            shape = shape.fuse(solid).cut(hole).cut(pocket)
        if o.get("pivot_ring"):
            z = o["pivot_station_mm"]
            shape = shape.cut(
                cq.Solid.makeCylinder(
                    1.7, 2 * radius + 4, cq.Vector(0, -radius - 2, z), cq.Vector(0, 1, 0)
                )
            )
        if o.get("fin_channels"):
            for angle in [0, 120, 240]:
                shape = shape.cut(
                    box(
                        o.get("fin_channel_depth_mm", 5),
                        o.get("fin_slot_width_mm", 2.4),
                        o.get("fin_slot_length_mm", 62),
                    )
                    .translate(
                        (o.get("fin_channel_radius_mm", 32), 0, o.get("tab_slot_start_mm", 65))
                    )
                    .rotate((0, 0, 0), (0, 0, 1), angle)
                )
        if o.get("trim_outer_cylinder"):
            shape = shape.intersect(cq.Solid.makeCylinder(radius, length))
        return shape
    if kind in ("gimbal_outer", "gimbal_inner", "cradle"):
        shape = tube(radius, g["inner_radius_m"] * 1000, 18 if o.get("tie_rails") else length)
        if o.get("tie_rails"):
            shape = shape.translate((0, 0, length - 18))
            for angle in [60, 180, 300]:
                shape = shape.fuse(
                    box(2, 4, length).translate((17, 0, 0)).rotate((0, 0, 0), (0, 0, 1), angle)
                )
        if kind == "cradle":
            shape = shape.cut(
                box(o["split_width_mm"], radius + 2, length + 2).translate((0, radius / 2, -1))
            )
        # Axial drive lug, away from the other ring's plane.
        if o.get("lug"):
            x, y, z = o["lug_center_mm"]
            lug = (
                box(*o["lug_size_mm"])
                .rotate((0, 0, 0), (0, 0, 1), o.get("lug_angle_deg", 0))
                .translate((x, y, z))
            )
            if o.get("bridge"):
                bridge = (
                    box(*o["bridge"]["size_mm"])
                    .rotate((0, 0, 0), (0, 0, 1), o["bridge"].get("angle_deg", 0))
                    .translate(tuple(o["bridge"]["position_mm"]))
                )
                shape = shape.fuse(bridge)
            shape = shape.fuse(lug)
        if kind == "gimbal_outer":
            for axis in [(1, 0, 0), (0, 1, 0)]:
                shape = shape.cut(
                    cq.Solid.makeCylinder(
                        1.7,
                        2 * radius + 4,
                        cq.Vector(-axis[0] * (radius + 2), -axis[1] * (radius + 2), length / 2),
                        cq.Vector(*axis),
                    )
                )
        elif kind == "gimbal_inner":
            shape = shape.cut(
                cq.Solid.makeCylinder(
                    1.7, 2 * radius + 4, cq.Vector(-radius - 2, 0, length / 2), cq.Vector(1, 0, 0)
                )
            )
        for center in o.get("socket_centers_mm", []):
            shape = shape.cut(cq.Solid.makeSphere(2.2, cq.Vector(*center), angleDegrees1=-90))
        for hole in o.get("radial_mount_screws", []):
            angle = np.deg2rad(hole["angle_deg"])
            direction = cq.Vector(-np.cos(angle), -np.sin(angle), 0)
            start = cq.Vector(radius * np.cos(angle), radius * np.sin(angle), hole["station_mm"])
            shape = shape.cut(
                cq.Solid.makeCylinder(hole["diameter_mm"] / 2, hole["depth_mm"], start, direction)
            )
            if hole.get("countersink_diameter_mm"):
                shape = shape.cut(
                    cq.Solid.makeCone(
                        hole["countersink_diameter_mm"] / 2,
                        1.25,
                        hole["countersink_depth_mm"],
                        start,
                        direction,
                    )
                )
        if o.get("link_bore"):
            bore = o["link_bore"]
            shape = shape.cut(
                cq.Solid.makeCylinder(
                    1.6, bore["length_mm"], cq.Vector(*bore["start_mm"]), cq.Vector(*bore["axis"])
                )
            )
        return shape
    if kind == "fins":
        h = g["span_m"] * 1000
        r = g["radius_m"] * 1000
        t = g["thickness_m"] * 1000
        root, tip, sweep = (g[k] * 1000 for k in ["root_chord_m", "tip_chord_m", "sweep_m"])
        # XZ plane normal -Y: root on X=r, axial station in Z.
        one = (
            cq.Workplane("XZ")
            .polyline([(r, 0), (r + h, sweep), (r + h, sweep + tip), (r, root)])
            .close()
            .extrude(t / 2, both=True)
            .val()
        )
        if o.get("tab_depth_mm"):
            tab = box(o["tab_depth_mm"], t, o["tab_length_mm"]).translate(
                (r - o["tab_depth_mm"] / 2, 0, o["tab_offset_mm"])
            )
            one = one.fuse(tab)
        if o.get("root_gusset_span_mm"):
            # Two triangular wood gussets, fitted to the cylindrical shell.
            # They are represented in the manufactured fin assembly's mass.
            span = o["root_gusset_span_mm"]
            base = o["root_gusset_base_mm"]
            inset = o.get("root_gusset_inset_mm", 1)
            body = cq.Solid.makeCylinder(r, root + 2, cq.Vector(0, 0, -1))
            for side in (-1, 1):
                gusset = (
                    cq.Workplane("XY")
                    .polyline(
                        [
                            (r - inset, side * t / 2),
                            (r - inset, side * (t / 2 + base)),
                            (r + span, side * t / 2),
                        ]
                    )
                    .close()
                    .extrude(root)
                    .val()
                    .cut(body)
                )
                one = one.fuse(gusset)
        return compound(
            [one.rotate((0, 0, 0), (0, 0, 1), i * 360 / g["count"]) for i in range(g["count"])]
        )
    if kind == "rail_guides":
        shapes = []
        for z in o["stations_mm"]:
            lug = tube(o["outer_radius_mm"], o["hole_radius_mm"], o["length_mm"]).translate(
                (o["radius_mm"], 0, z)
            )
            foot = box(o["foot_width_mm"], o["foot_depth_mm"], o["length_mm"]).translate(
                (o["foot_radius_mm"], 0, z)
            )
            foot = foot.cut(
                cq.Solid.makeCylinder(
                    o["body_radius_mm"], o["length_mm"] + 2, cq.Vector(0, 0, z - 1)
                )
            )
            shapes.append(lug.fuse(foot))
        return compound(shapes)
    if kind == "fastener_set":
        shapes = []
        for screw in o["radial_screws"]:
            angle = np.deg2rad(screw["angle_deg"])
            direction = cq.Vector(-np.cos(angle), -np.sin(angle), 0)
            r, depth = screw["outer_radius_mm"], screw["head_depth_mm"]
            start = cq.Vector(r * np.cos(angle), r * np.sin(angle), 0)
            head = cq.Solid.makeCone(
                screw["head_diameter_mm"] / 2,
                screw["shank_diameter_mm"] / 2,
                depth,
                start,
                direction,
            )
            shank = cq.Solid.makeCylinder(
                screw["shank_diameter_mm"] / 2,
                screw["length_mm"] - depth,
                start + direction.multiply(depth),
                direction,
            )
            shapes.append(head.fuse(shank))
        return compound(shapes)
    if kind == "pins":
        shapes = []
        for item in o["pins"]:
            x, y, z = item["start_mm"]
            axis = item["axis"]
            shapes.append(
                cq.Solid.makeCylinder(
                    item["radius_mm"], item["length_mm"], cq.Vector(x, y, z), cq.Vector(*axis)
                )
            )
        return compound(shapes)
    if kind == "links":
        shapes = []
        for a, b in o["segments_mm"]:
            start = np.array(a)
            vector = np.array(b) - start
            if o.get("end_trim_mm"):
                vector = vector * (1 - o["end_trim_mm"] / np.linalg.norm(vector))
            shapes.append(
                cq.Solid.makeCylinder(
                    o["radius_mm"],
                    float(np.linalg.norm(vector)),
                    cq.Vector(*start),
                    cq.Vector(*vector),
                )
            )
        return compound(shapes)
    if kind == "brackets":
        shape = compound(
            [box(*s["size_mm"]).translate(tuple(s["position_mm"])) for s in o["blocks"]]
        )
        if "trim_radius_mm" in o:
            shape = shape.intersect(cq.Solid.makeCylinder(o["trim_radius_mm"], length))
        for pocket in o.get("pockets", []):
            shape = shape.cut(box(*pocket["size_mm"]).translate(tuple(pocket["position_mm"])))
        return shape
    if kind == "vendor_motor":
        return cq.Workplane("XY").circle(radius).extrude(length).val()
    if kind in ("envelope", "budget"):
        l, w, h = g["bbox_m"]
        shape = box(w * 1000, h * 1000, l * 1000)
        for x, z in o.get("mount_holes_mm", []):
            hole = cq.Solid.makeCylinder(
                o.get("hole_diameter_mm", 2.5) / 2,
                h * 1000 + 2,
                cq.Vector(x, -h * 500 - 1, z),
                cq.Vector(0, 1, 0),
            )
            shape = shape.cut(hole)
        return shape
    raise ValueError(f"{part.id}: unimplemented generator {kind}")


def placed_shape(part: Part) -> Any:
    return local_shape(part).translate(
        (part.lateral_offset_m[0] * 1000, -part.lateral_offset_m[1] * 1000, part.position_m * 1000)
    )


def properties(part: Part, shape: Any) -> dict[str, Any]:
    volume = shape.Volume()
    c = shape.Center()
    matrix = np.array(cq.Shape.matrixOfInertia(shape))
    transform = np.array([[0, 0, -1], [1, 0, 0], [0, -1, 0]])
    return {
        "shape_sha256": shape_digest(part),
        "volume_m3": volume * 1e-9,
        "cg_local_body_m": (transform @ np.array([c.x, c.y, c.z]) * 1e-3).tolist(),
        "inertia_per_kg_m2": (transform @ matrix @ transform.T / volume * 1e-6).tolist(),
        "basis": (
            "bulk-density manufactured solid"
            if part.cad and part.cad.mass_basis == "volume_density"
            else "uniform envelope inertia; supplied/estimated mass, unmeasured"
        ),
    }
