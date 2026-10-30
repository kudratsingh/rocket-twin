"""Parametric nonmetallic retention hardware for WO-03 CAD studies.

All dimensions are millimetres. Local CAD axes follow the assembly convention:
XY is the radial plane, +Z is aft, and +Y is the requested inner-gimbal relief
side. These are geometry primitives only; no dimensions imply an allowable,
fastener qualification, or flight release.
"""

from __future__ import annotations

import importlib
import math
import os
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

os.environ.setdefault("XDG_CACHE_HOME", str(Path(".cache").resolve()))
cq: Any = importlib.import_module("cadquery")


def _value(mapping: Mapping[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} must be a finite positive number")
    return value


def _length_mm(geometry: Mapping[str, Any]) -> float:
    if "length_mm" in geometry:
        return _positive(geometry["length_mm"], "geometry.length_mm")
    if "length_m" in geometry:
        return _positive(float(geometry["length_m"]) * 1000, "geometry.length_m")
    bbox = geometry.get("bbox_m")
    if bbox is not None and len(bbox) >= 1:
        return _positive(float(bbox[0]) * 1000, "geometry.bbox_m[0]")
    raise ValueError("geometry requires length_mm, length_m or bbox_m[0]")


def _radius_mm(geometry: Mapping[str, Any], params: Mapping[str, Any], key: str) -> float:
    if key in params:
        return _positive(params[key], f"params.{key}")
    if key in geometry:
        return _positive(geometry[key], f"geometry.{key}")
    m_key = key.replace("_mm", "_m")
    if m_key in geometry:
        return _positive(float(geometry[m_key]) * 1000, f"geometry.{m_key}")
    if key == "outer_radius_mm" and "radius_m" in geometry:
        return _positive(float(geometry["radius_m"]) * 1000, "geometry.radius_m")
    if key == "inner_radius_mm" and "inner_radius_m" in geometry:
        return _positive(float(geometry["inner_radius_m"]) * 1000, "geometry.inner_radius_m")
    raise ValueError(f"missing {key}")


def _tube(ro: float, ri: float, length: float, z0: float = 0.0) -> Any:
    if ri < 0 or ri >= ro:
        raise ValueError("tube radii must satisfy 0 <= inner < outer")
    if ri == 0:
        return cq.Solid.makeCylinder(ro, length, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))
    outer = cq.Solid.makeCylinder(ro, length, cq.Vector(0, 0, z0), cq.Vector(0, 0, 1))
    inner = cq.Solid.makeCylinder(ri, length + 2, cq.Vector(0, 0, z0 - 1), cq.Vector(0, 0, 1))
    return outer.cut(inner)


def _box(x: float, y: float, z: float, center: tuple[float, float, float]) -> Any:
    return cq.Workplane("XY").box(x, y, z, centered=(True, True, True)).val().translate(center)


def _bolt_points(params: Mapping[str, Any]) -> list[tuple[float, float]]:
    holes = params.get("bolt_holes")
    if holes is not None:
        return [(float(h["x_mm"]), float(h["y_mm"])) for h in holes]
    count = int(params.get("bolt_count", 0))
    if count <= 0:
        return []
    radius = _positive(params["bolt_circle_radius_mm"], "bolt_circle_radius_mm")
    start_deg = float(params.get("bolt_start_angle_deg", 0.0))
    return [
        (
            radius * math.cos(math.radians(start_deg + 360 * i / count)),
            radius * math.sin(math.radians(start_deg + 360 * i / count)),
        )
        for i in range(count)
    ]


def _axial_holes(
    shape: Any, points: Sequence[tuple[float, float]], diameter: float, thickness: float
) -> Any:
    if not points:
        return shape
    radius = _positive(diameter, "bolt_hole_diameter_mm") / 2
    for x, y in points:
        cutter = cq.Solid.makeCylinder(
            radius,
            thickness + 2,
            cq.Vector(x, y, -1),
            cq.Vector(0, 0, 1),
        )
        shape = shape.cut(cutter)
    return shape


def _thrust_plate(geometry: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
    ro = _radius_mm(geometry, params, "outer_radius_mm")
    ri = _radius_mm(geometry, params, "inner_radius_mm")
    thickness = _positive(
        _value(params, "thickness_mm", default=_length_mm(geometry)), "thickness_mm"
    )
    shape = _tube(ro, ri, thickness)
    fingers = params.get("bond_fingers")
    if fingers:
        for finger_angle in (0, 120, 240):
            for side in (-1, 1):
                finger = _box(
                    float(fingers["radial_depth_mm"]),
                    float(fingers["wall_mm"]),
                    float(fingers["length_mm"]),
                    (
                        float(fingers["radius_mm"]),
                        side * float(fingers["side_center_mm"]),
                        float(fingers["length_mm"]) / 2,
                    ),
                ).rotate((0, 0, 0), (0, 0, 1), finger_angle)
                shape = shape.fuse(
                    finger.intersect(cq.Solid.makeCylinder(ro, float(fingers["length_mm"])))
                )

    # Three centered radial slots clear the fixed-frame rail envelope. Width is
    # tangential; depth is radial. Side gap is applied independently on each side.
    notches = params.get("rail_notches")
    if notches:
        notch_width = _positive(notches["width_mm"], "rail_notches.width_mm")
        gap = float(notches.get("side_gap_mm", 0.0))
        depth = _positive(notches["depth_mm"], "rail_notches.depth_mm")
        if gap < 0 or not math.isfinite(gap):
            raise ValueError("rail_notches.side_gap_mm must be finite and nonnegative")
        width = notch_width + 2 * gap
        rail_radius = float(notches.get("rail_radius_mm", ro - depth / 2))
        if not 0 < rail_radius < ro:
            raise ValueError("rail radius is outside the thrust plate")
        radial_width = depth + 2 * gap
        open_to_od = bool(notches.get("open_to_od", False))
        if rail_radius - radial_width / 2 <= ri or (
            not open_to_od and rail_radius + radial_width / 2 >= ro
        ):
            raise ValueError("rail notch envelope does not fit within the thrust plate radii")
        for angle in (0.0, 120.0, 240.0):
            if open_to_od:
                inner = rail_radius - radial_width / 2
                radial_width_open = ro + 1 - inner
                slot = _box(
                    radial_width_open,
                    width,
                    thickness + 2,
                    (inner + radial_width_open / 2, 0, thickness / 2),
                )
            else:
                slot = _box(
                    radial_width,
                    width,
                    thickness + 2,
                    (rail_radius, 0, thickness / 2),
                )
            slot = slot.rotate((0, 0, 0), (0, 0, 1), angle)
            shape = shape.cut(slot)

    bolt_points = _bolt_points(params)
    if bolt_points:
        shape = _axial_holes(shape, bolt_points, params["bolt_hole_diameter_mm"], thickness)
    return shape.clean()


def _sector(
    ri: float, ro: float, angle_center_deg: float, angle_width_deg: float, thickness: float
) -> Any:
    if ri < 0 or ri >= ro:
        raise ValueError("sector radii must satisfy 0 <= inner < outer")
    if not 0 < angle_width_deg < 180:
        raise ValueError("sector angle must be between 0 and 180 degrees")
    steps = max(8, math.ceil(angle_width_deg / 3))
    start = angle_center_deg - angle_width_deg / 2
    outer_points = [
        (
            ro * math.cos(math.radians(start + i * angle_width_deg / steps)),
            ro * math.sin(math.radians(start + i * angle_width_deg / steps)),
        )
        for i in range(steps + 1)
    ]
    inner_points = [
        (
            ri * math.cos(math.radians(start + i * angle_width_deg / steps)),
            ri * math.sin(math.radians(start + i * angle_width_deg / steps)),
        )
        for i in range(steps, -1, -1)
    ]
    return cq.Workplane("XY").polyline(outer_points + inner_points).close().extrude(thickness).val()


def _sector_pads(geometry: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
    ri = _radius_mm(geometry, params, "inner_radius_mm")
    ro = _radius_mm(geometry, params, "outer_radius_mm")
    thickness = _positive(
        _value(params, "thickness_mm", default=_length_mm(geometry)), "thickness_mm"
    )
    width = _positive(params["sector_angle_deg"], "sector_angle_deg")
    solids = [_sector(ri, ro, angle, width, thickness) for angle in (0.0, 120.0, 240.0)]
    return cq.Compound.makeCompound(solids)


def _radial_hole(
    shape: Any,
    angle_deg: float,
    z: float,
    diameter: float,
    countersink_diameter: float | None,
    countersink_throat_diameter: float | None,
    countersink_depth: float,
    outer_radius: float,
    depth: float,
) -> Any:
    angle = math.radians(angle_deg)
    direction = cq.Vector(-math.cos(angle), -math.sin(angle), 0)
    origin = cq.Vector(
        (outer_radius + 1) * math.cos(angle), (outer_radius + 1) * math.sin(angle), z
    )
    hole_radius = _positive(diameter, "radial_hole_diameter_mm") / 2
    cutter = cq.Solid.makeCylinder(
        hole_radius, _positive(depth, "radial_hole_depth_mm"), origin, direction
    )
    shape = shape.cut(cutter)
    if countersink_diameter is not None and countersink_depth > 0:
        sink_radius = _positive(countersink_diameter, "countersink_diameter_mm") / 2
        throat_radius = (
            _positive(
                countersink_throat_diameter or diameter,
                "countersink_throat_diameter_mm",
            )
            / 2
        )
        sink_depth = _positive(countersink_depth, "countersink_depth_mm")
        if throat_radius > sink_radius:
            raise ValueError("countersink throat diameter must not exceed its mouth diameter")
        start = cq.Vector(outer_radius * math.cos(angle), outer_radius * math.sin(angle), z)
        cone = cq.Solid.makeCone(sink_radius, throat_radius, sink_depth, start, direction)
        shape = shape.cut(cone)
    return shape


def _motor_cassette(geometry: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
    length = _length_mm(geometry)
    motor_clear = _positive(params.get("motor_clear_radius_mm", 15.3), "motor_clear_radius_mm")
    grip_ro = _positive(params.get("grip_outer_radius_mm", 19.5), "grip_outer_radius_mm")
    grip_start = float(params.get("grip_start_mm", 55.0))
    grip_length = _positive(params.get("grip_length_mm", 18.0), "grip_length_mm")
    if grip_start < 0 or grip_start + grip_length > length:
        raise ValueError("grip ring must lie within the cassette geometry length")
    if motor_clear >= grip_ro:
        raise ValueError("motor clear radius must be smaller than grip outer radius")

    rail_center = _positive(params.get("rail_center_radius_mm", 17.5), "rail_center_radius_mm")
    rail_radial = _positive(params.get("rail_radial_width_mm", 4.0), "rail_radial_width_mm")
    rail_tangent = _positive(
        params.get("rail_tangential_width_mm", 6.0), "rail_tangential_width_mm"
    )
    rail_start = float(params.get("rail_start_mm", 0.0))
    if rail_start < 0 or rail_start >= length:
        raise ValueError("rail_start_mm must be within the cassette length")
    rail_angles = [float(a) for a in params.get("rail_angles_deg", (0.0, 120.0, 240.0))]
    if len(rail_angles) != 3:
        raise ValueError("motor cassette requires exactly three rail angles")
    rails = []
    for angle in rail_angles:
        angle_start = float(
            params.get("rail_start_by_angle_mm", {}).get(str(int(angle)), rail_start)
        )
        rail = _box(
            rail_radial,
            rail_tangent,
            length - angle_start,
            (rail_center, 0, (length + angle_start) / 2),
        ).rotate((0, 0, 0), (0, 0, 1), angle)
        rails.append(rail)

    # Fore stop is the explicit axial thrust path from the motor shoulder into
    # the longitudinal G11 rails. The liner is only a fit/thermal envelope.
    fore = params.get("fore_thrust_stop", {})
    fore_enabled = bool(fore.get("enabled", True))
    fore_t = _positive(fore.get("thickness_mm", 4.0), "fore_thrust_stop.thickness_mm")
    fore_ro = _positive(fore.get("outer_radius_mm", grip_ro), "fore_thrust_stop.outer_radius_mm")
    fore_ri = float(fore.get("inner_radius_mm", motor_clear))
    fore_station = float(fore.get("station_mm", 0.0))
    if not 0 <= fore_station < length or fore_station + fore_t > length:
        raise ValueError("fore thrust stop lies outside cassette")
    if fore_ri < 0 or fore_ri >= fore_ro:
        raise ValueError("fore thrust stop radii must satisfy 0 <= inner < outer")
    pieces = list(rails)
    if fore_enabled:
        stop = _tube(fore_ro, fore_ri, fore_t, fore_station)
        if "rod_relief" in fore:
            relief = fore["rod_relief"]
            stop = stop.cut(
                _sector(
                    relief["keep_radius_mm"],
                    fore_ro + 1,
                    relief["center_deg"],
                    relief["width_deg"],
                    fore_t + 2,
                ).translate((0, 0, fore_station - 1))
            )
        pieces.append(stop)

    grip = _tube(grip_ro, motor_clear, grip_length, grip_start)
    # Gimbal bridge relief: a shallow +Y pocket spanning CAD X +/-3 mm and the
    # requested station interval. It removes only cassette material in that zone.
    notch = params.get("inner_gimbal_notch", {"enabled": True})
    if notch and notch.get("enabled", True):
        x_half = _positive(notch.get("half_width_mm", 3.0), "inner_gimbal_notch.half_width_mm")
        y_min = _positive(notch.get("y_min_mm", 18.7), "inner_gimbal_notch.y_min_mm")
        z0 = float(notch.get("start_mm", 55.0))
        z1 = float(notch.get("end_mm", 67.0))
        if z0 < grip_start or z1 > grip_start + grip_length or z1 <= z0:
            raise ValueError("inner gimbal notch must lie within the grip ring station interval")
        notch_depth = max(0.0, grip_ro - y_min) + 1.0
        if notch_depth > 0:
            cut = _box(
                2 * x_half, notch_depth, z1 - z0, (0.0, y_min + notch_depth / 2, (z0 + z1) / 2)
            )
            grip = grip.cut(cut)
    pieces.append(grip)

    # Optional bolted front flange and ears. Ears are placed on the bolt circle
    # and fused into the fore stop only when explicitly requested.
    front_plate = params.get("front_plate", {})
    if front_plate.get("enabled", False):
        plate_t = _positive(front_plate.get("thickness_mm", 3.0), "front_plate.thickness_mm")
        plate_ro = _positive(
            front_plate.get("outer_radius_mm", grip_ro), "front_plate.outer_radius_mm"
        )
        plate_ri = _positive(
            front_plate.get("inner_radius_mm", motor_clear), "front_plate.inner_radius_mm"
        )
        station = float(front_plate.get("station_mm", 0.0))
        if station < 0 or station + plate_t > length:
            raise ValueError("front plate lies outside cassette")
        pieces.append(_tube(plate_ro, plate_ri, plate_t, station))
        if front_plate.get("ears_enabled", False):
            ear = front_plate.get("ear", {})
            count = int(ear.get("count", 3))
            circle = _positive(
                ear.get("bolt_circle_radius_mm", 23.5), "front_plate.ear.bolt_circle_radius_mm"
            )
            er = _positive(ear.get("radial_width_mm", 8.0), "front_plate.ear.radial_width_mm")
            et = _positive(
                ear.get("tangential_width_mm", 8.0), "front_plate.ear.tangential_width_mm"
            )
            for i in range(count):
                a = 360 * i / count + float(ear.get("start_angle_deg", 0.0))
                center = (circle, 0.0, station + plate_t / 2)
                pieces.append(_box(er, et, plate_t, center).rotate((0, 0, 0), (0, 0, 1), a))

    # Rear retainer attachment blocks transfer plate loads into the three rails.
    rear = params.get("rear_retainer_blocks", {"enabled": True})
    rear_bolt_points: list[tuple[float, float, float, float]] = []
    if rear and rear.get("enabled", True):
        rb = rear.get("block", {})
        count = int(rb.get("count", 3))
        circle = _positive(
            rb.get("center_radius_mm", 23.5), "rear_retainer_blocks.block.center_radius_mm"
        )
        radial = _positive(
            rb.get("radial_width_mm", 8.0), "rear_retainer_blocks.block.radial_width_mm"
        )
        tangent = _positive(
            rb.get("tangential_width_mm", 8.0), "rear_retainer_blocks.block.tangential_width_mm"
        )
        axial = _positive(
            rb.get("axial_length_mm", 6.0), "rear_retainer_blocks.block.axial_length_mm"
        )
        rail_overlap = float(rb.get("rail_overlap_mm", 0.1))
        if not math.isfinite(rail_overlap) or rail_overlap < 0:
            raise ValueError("rear_retainer_blocks.block.rail_overlap_mm must be nonnegative")
        station = float(rb.get("station_mm", length - axial))
        block_hole_diameter = _positive(
            rb.get("bolt_hole_diameter_mm", 3.0),
            "rear_retainer_blocks.block.bolt_hole_diameter_mm",
        )
        if station < 0 or station + axial > length:
            raise ValueError("rear retainer blocks lie outside cassette")
        if count < 1:
            raise ValueError("rear retainer block count must be positive")
        if circle - rail_overlap / 2 - radial / 2 > rail_center + rail_radial / 2 + 1e-9:
            raise ValueError("rear retainer block does not reach a cassette rail")
        block_angles = [float(a) for a in rb.get("angles_deg", [])]
        if not block_angles:
            block_angles = [
                360 * i / count + float(rb.get("start_angle_deg", 0.0)) for i in range(count)
            ]
        if len(block_angles) != count:
            raise ValueError("rear retainer block angles must match block count")
        if any(
            min(abs((a - r + 180) % 360 - 180) for r in rail_angles) > 1e-6 for a in block_angles
        ):
            raise ValueError("rear retainer blocks must align with cassette rail angles")
        for a in block_angles:
            rad = math.radians(a)
            x, y = circle * math.cos(rad), circle * math.sin(rad)
            block_radius = circle - rail_overlap / 2
            center = (block_radius, 0.0, station + axial / 2)
            pieces.append(_box(radial, tangent, axial, center).rotate((0, 0, 0), (0, 0, 1), a))
            rear_bolt_points.append((x, y, station, block_hole_diameter))

    shape = pieces[0]
    for piece in pieces[1:]:
        shape = shape.fuse(piece)
    shape = shape.clean()

    for x, y, station, hole_diameter in rear_bolt_points:
        shape = shape.cut(
            cq.Solid.makeCylinder(
                hole_diameter / 2,
                length - station + 2,
                cq.Vector(x, y, station - 1),
                cq.Vector(0, 0, 1),
            )
        )

    # Radial mount screws cross each rail. Conical countersinks face outward.
    for hole in params.get("radial_mount_screws", []):
        angle = float(hole["angle_deg"])
        if min(abs((angle - r + 180) % 360 - 180) for r in rail_angles) > 1e-6:
            raise ValueError("radial mount screw angle must align with a cassette rail")
        shape = _radial_hole(
            shape,
            angle,
            float(hole["station_mm"]),
            float(hole["diameter_mm"]),
            hole.get("countersink_diameter_mm"),
            hole.get("countersink_throat_diameter_mm"),
            float(hole.get("countersink_depth_mm", 0.0)),
            max(grip_ro, rail_center + rail_radial / 2),
            float(hole.get("depth_mm", 8.0)),
        )
    return shape.clean()


def _retainer_plate(geometry: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
    ro = _radius_mm(geometry, params, "outer_radius_mm")
    ri = _radius_mm(geometry, params, "inner_radius_mm")
    thickness = _positive(
        _value(params, "thickness_mm", default=_length_mm(geometry)), "thickness_mm"
    )
    if ri >= ro:
        raise ValueError("retainer radii must satisfy inner < outer")
    shape = _tube(ro, ri, thickness)
    circle = _positive(params["bolt_circle_radius_mm"], "bolt_circle_radius_mm")
    count = int(params.get("bolt_count", 3))
    if count < 1:
        raise ValueError("bolt_count must be positive")
    start = float(params.get("bolt_start_angle_deg", 0.0))
    points = [
        (
            circle * math.cos(math.radians(start + 360 * i / count)),
            circle * math.sin(math.radians(start + 360 * i / count)),
        )
        for i in range(count)
    ]
    hole_diameter = _positive(params["bolt_hole_diameter_mm"], "bolt_hole_diameter_mm")
    shape = _axial_holes(shape, points, hole_diameter, thickness)

    ears = params.get("ears", {})
    if ears.get("enabled", False):
        ear_count = int(ears.get("count", count))
        ear_circle = _positive(ears.get("center_radius_mm", circle), "ears.center_radius_mm")
        radial = _positive(ears.get("radial_width_mm", 8.0), "ears.radial_width_mm")
        tangent = _positive(ears.get("tangential_width_mm", 8.0), "ears.tangential_width_mm")
        for i in range(ear_count):
            angle = start + 360 * i / ear_count
            ear = _box(radial, tangent, thickness, (ear_circle, 0, thickness / 2))
            shape = shape.fuse(ear.rotate((0, 0, 0), (0, 0, 1), angle))
    for block in params.get("blocks", []):
        size = block["size_mm"]
        position = block["position_mm"]
        shape = shape.fuse(_box(float(size[0]), float(size[1]), float(size[2]), tuple(position)))
    # Re-cut holes after ears/blocks are united so they pass through the full retainer.
    shape = _axial_holes(
        shape,
        points,
        hole_diameter,
        thickness + max([float(b["size_mm"][2]) for b in params.get("blocks", [])] or [0]),
    )
    return shape.clean()


def build_retention(kind: str, geometry: Mapping[str, Any], params: Mapping[str, Any]) -> Any:
    """Build one retention feature in local millimetre coordinates.

    Args:
        kind: ``thrust_plate``, ``sector_pads``, ``motor_cassette`` or
            ``retainer_plate``.
        geometry: Part geometry mapping. Use SI shape keys for integration
            (``length_m``, ``radius_m``, ``inner_radius_m``) or explicit
            ``length_mm``/radius overrides when a study part needs them.
        params: Feature dimensions in mm. Optional features are enabled only
            when their corresponding mapping has ``enabled: true``; motor
            cassette fore thrust stop and rear retainer blocks default on.

    Returns:
        A valid CadQuery solid, or a compound containing the three separate
        mica sector pads. Mica pads are compression/thermal shims only and do
        not belong in a motor thrust load path.
    """
    if not isinstance(geometry, Mapping) or not isinstance(params, Mapping):
        raise TypeError("geometry and params must be mappings")
    builders = {
        "thrust_plate": _thrust_plate,
        "sector_pads": _sector_pads,
        "motor_cassette": _motor_cassette,
        "retainer_plate": _retainer_plate,
    }
    try:
        shape = builders[kind](geometry, params)
    except KeyError as error:
        if kind not in builders:
            raise ValueError(f"unsupported retention kind: {kind}") from error
        raise
    if not shape.isValid() or shape.Volume() <= 0:
        raise ValueError(f"{kind} generated invalid or zero-volume geometry")
    return shape
