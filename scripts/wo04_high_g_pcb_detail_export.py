"""Extract pinned manufacturer PCB XY layers, never invented populated hardware.

Original Eagle bytes are data only. No CAD kernel, board thickness, component Z,
mass, inertia, incoming silicon identity or canonical vehicle geometry is created.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.wo04_high_g_board_export import NOTICE, SOURCE, number, wire_points
from scripts.wo04_high_g_board_export import extract as extract_base

OUTPUT = ROOT / "docs/studies/frontend-component-depth-20261108/high-g-pcb-layout.json"
ID = "adafruit-5374-source-xy-layers-4a768fc9-v1"
MIRROR_LAYERS = {
    a: b
    for a, b in [
        (1, 16),
        (16, 1),
        (21, 22),
        (22, 21),
        (25, 26),
        (26, 25),
        (27, 28),
        (28, 27),
        (29, 30),
        (30, 29),
        (31, 32),
        (32, 31),
        (35, 36),
        (36, 35),
        (39, 40),
        (40, 39),
        (41, 42),
        (42, 41),
        (51, 52),
        (52, 51),
    ]
}


def rotation(value: str | None) -> tuple[float, bool]:
    value = value or "R0"
    match = re.fullmatch(r"S?(M)?R(-?\d+(?:\.\d+)?)", value)
    if not match:
        raise ValueError(f"Unsupported source rotation: {value}")
    degrees = float(match.group(2))
    if not math.isfinite(degrees):
        raise ValueError("Nonfinite source rotation")
    return degrees, bool(match.group(1))


def extract(raw: bytes, attribution: str) -> dict[str, Any]:
    started = time.process_time()
    base = extract_base(raw, attribution)  # Existing immutable blob/SHA/notice admission.
    root = ET.fromstring(raw)
    board = root.find("./drawing/board")
    if board is None:
        raise ValueError("No manufacturer board")
    packages = {
        (lib.get("name"), pkg.get("name")): pkg
        for lib in board.findall("./libraries/library")
        for pkg in lib.findall("./packages/package")
    }
    contacts: dict[tuple[str, str], str] = {}
    nets = []
    for signal in board.findall("./signals/signal"):
        net = signal.get("name", "")
        refs = []
        for node in signal.findall("contactref"):
            ref, pad = node.get("element", ""), node.get("pad", "")
            if (ref, pad) in contacts:
                raise ValueError("Pad belongs to multiple nets")
            contacts[ref, pad] = net
            refs.append({"ref": ref, "pad": pad})
        nets.append({"name": net, "contacts": refs})
    layers = [
        {"id": int(node.get("number", "0")), "name": node.get("name")}
        for node in root.findall("./drawing/layers/layer")
    ]
    placements, pads, drills, vias, traces, copper_polygons = [], [], [], [], [], []
    silk: dict[str, Any] = {
        "lines": [],
        "circles": [],
        "polygons": [],
        "texts": [],
        "rectangle_groups": [],
    }
    documentation: dict[str, Any] = {
        "lines": [],
        "circles": [],
        "polygons": [],
        "texts": [],
        "rectangle_groups": [],
    }
    rectangle_groups: dict[tuple[str, int, str], list[list[float]]] = {}
    omitted = Counter()

    def rounded(point: list[float]) -> list[float]:
        return [round(v, 9) for v in point]

    def graphic(
        node: ET.Element,
        ref: str | None,
        transform: Any,
        mirrored: bool = False,
        scope: str = "plain",
    ) -> None:
        source_layer = int(node.get("layer", "0"))
        layer = MIRROR_LAYERS.get(source_layer, source_layer) if mirrored else source_layer
        target = (
            silk
            if layer in (21, 22)
            else documentation
            if layer in (25, 26, 27, 28, 51, 52)
            else None
        )
        if target is None:
            omitted[f"{scope}:{node.tag}:layer{source_layer}"] += 1
            return
        common = {"ref": ref, "layer": layer, "source_layer": source_layer, "net": None}
        if node.tag == "wire":
            target["lines"].append(
                {
                    **common,
                    "points_mm": [rounded(transform(*p)) for p in wire_points(node)],
                    "width_mm": number(node, "width"),
                    "source_curve_deg": number(node, "curve"),
                }
            )
        elif node.tag == "circle":
            target["circles"].append(
                {
                    **common,
                    "center_mm": rounded(transform(number(node, "x"), number(node, "y"))),
                    "radius_mm": number(node, "radius"),
                    "width_mm": number(node, "width"),
                }
            )
        elif node.tag == "rectangle":
            x1, y1, x2, y2 = [number(node, k) for k in ("x1", "y1", "x2", "y2")]
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            theta, local_mirror = rotation(node.get("rot"))
            if local_mirror:
                raise ValueError("Unexpected mirrored source rectangle")
            angle = math.radians(theta)
            corners = [
                rounded(
                    transform(
                        cx + x * math.cos(angle) - y * math.sin(angle),
                        cy + x * math.sin(angle) + y * math.cos(angle),
                    )
                )
                for x, y in [
                    (-abs(x2 - x1) / 2, -abs(y2 - y1) / 2),
                    (abs(x2 - x1) / 2, -abs(y2 - y1) / 2),
                    (abs(x2 - x1) / 2, abs(y2 - y1) / 2),
                    (-abs(x2 - x1) / 2, abs(y2 - y1) / 2),
                ]
            ]
            group = "silkscreen" if target is silk else "documentation"
            rectangle_groups.setdefault((ref or "", layer, group), []).append(
                [v for p in corners for v in p]
            )
        elif node.tag == "polygon":
            vertices = [
                {
                    "xy_mm": rounded(transform(number(v, "x"), number(v, "y"))),
                    "curve_deg": -number(v, "curve") if mirrored else number(v, "curve"),
                }
                for v in node.findall("vertex")
            ]
            target["polygons"].append(
                {**common, "vertices": vertices, "width_mm": number(node, "width")}
            )
        elif node.tag == "text":
            text = node.text or ""
            if text.startswith(">"):
                omitted[f"{scope}:unresolved_text_placeholder"] += 1
                return
            degrees, text_mirror = rotation(node.get("rot"))
            target["texts"].append(
                {
                    **common,
                    "text": text,
                    "position_mm": rounded(transform(number(node, "x"), number(node, "y"))),
                    "size_mm": number(node, "size"),
                    "source_rotation": node.get("rot", "R0"),
                    "rotation_deg": degrees,
                    "mirrored": text_mirror != mirrored,
                    "font": node.get("font", "proportional"),
                    "align": node.get("align", "bottom-left"),
                    "ratio_percent": number(node, "ratio", 8),
                    "glyph_outlines_available": False,
                }
            )
        else:
            omitted[f"{scope}:{node.tag}"] += 1

    identity = lambda x, y: [x, y]
    for node in board.findall("./plain/*"):
        if node.tag == "wire" and node.get("layer") == "20":
            continue  # The separately pinned outline retains these exact segments.
        graphic(node, None, identity)

    for element in board.findall("./elements/element"):
        if time.process_time() - started > 55:
            raise TimeoutError("Source extraction CPU reserve reached; no retry")
        ref = element.get("name", "")
        degrees, mirrored = rotation(element.get("rot"))
        angle = math.radians(degrees)
        ex, ey = number(element, "x"), number(element, "y")

        def point(
            x: float,
            y: float,
            ex: float = ex,
            ey: float = ey,
            angle: float = angle,
            mirrored: bool = mirrored,
        ) -> list[float]:
            if mirrored:
                x = -x
            return [
                ex + x * math.cos(angle) - y * math.sin(angle),
                ey + x * math.sin(angle) + y * math.cos(angle),
            ]

        pkg = packages[element.get("library"), element.get("package")]
        placements.append(
            {
                "ref": ref,
                "value": element.get("value", ""),
                "library": element.get("library"),
                "package": element.get("package"),
                "position_mm": [ex, ey],
                "rotation_deg": degrees,
                "mirrored": mirrored,
                "source_rotation": element.get("rot", "R0"),
                "side": "bottom" if mirrored else "top",
                "height_mm": None,
            }
        )
        for node in pkg:
            if node.tag in ("smd", "pad"):
                name = node.get("name", "")
                local_angle, _ = rotation(node.get("rot"))
                layer = int(node.get("layer", "17"))
                layer = MIRROR_LAYERS.get(layer, layer) if mirrored else layer
                center = rounded(point(number(node, "x"), number(node, "y")))
                pad = {
                    "ref": ref,
                    "name": name,
                    "kind": node.tag,
                    "layer": layer,
                    "net": contacts.get((ref, name)),
                    "center_mm": center,
                    "rotation_deg": degrees - local_angle if mirrored else degrees + local_angle,
                    "mirrored": mirrored,
                    "source_rotation": node.get("rot", "R0"),
                    "height_mm": None,
                }
                if node.tag == "smd":
                    dx, dy = number(node, "dx"), number(node, "dy")
                    pad.update(size_mm=[dx, dy], roundness_percent=number(node, "roundness"))
                    theta = math.radians(local_angle)
                    pad["points_mm"] = [
                        rounded(
                            point(
                                number(node, "x") + x * math.cos(theta) - y * math.sin(theta),
                                number(node, "y") + x * math.sin(theta) + y * math.cos(theta),
                            )
                        )
                        for x, y in [
                            (-dx / 2, -dy / 2),
                            (dx / 2, -dy / 2),
                            (dx / 2, dy / 2),
                            (-dx / 2, dy / 2),
                        ]
                    ]
                else:
                    pad.update(
                        drill_mm=number(node, "drill"),
                        diameter_mm=number(node, "diameter")
                        if node.get("diameter") is not None
                        else None,
                        shape=node.get("shape", "round"),
                    )
                    drills.append(
                        {
                            "ref": ref,
                            "pad": name,
                            "net": pad["net"],
                            "center_mm": center,
                            "diameter_mm": pad["drill_mm"],
                            "kind": "through_pad_drill",
                        }
                    )
                pads.append(pad)
            elif node.tag == "hole":
                drills.append(
                    {
                        "ref": ref,
                        "pad": None,
                        "net": None,
                        "center_mm": rounded(point(number(node, "x"), number(node, "y"))),
                        "diameter_mm": number(node, "drill"),
                        "kind": "mechanical_hole",
                    }
                )
            elif node.tag not in ("description",):
                if (
                    node.tag == "text"
                    and element.get("smashed") == "yes"
                    and (node.text or "").startswith(">")
                ):
                    continue
                graphic(node, ref, point, mirrored, "package")
        for attribute in element.findall("attribute"):
            if attribute.get("name") in ("NAME", "VALUE"):
                copy = ET.Element("text", attribute.attrib)
                copy.text = ref if attribute.get("name") == "NAME" else element.get("value", "")
                graphic(copy, ref, identity, False, "element_attribute")
    for (ref, layer, group), rects in rectangle_groups.items():
        (silk if group == "silkscreen" else documentation)["rectangle_groups"].append(
            {
                "ref": ref or None,
                "layer": layer,
                "net": None,
                "corner_order": "x1,y1,x2,y2,x3,y3,x4,y4; board XYmm",
                "corners_mm": rects,
            }
        )
    for signal in board.findall("./signals/signal"):
        net = signal.get("name", "")
        for node in signal:
            if node.tag == "wire":
                traces.append(
                    {
                        "net": net,
                        "ref": None,
                        "layer": int(node.get("layer", "0")),
                        "points_mm": [rounded(p) for p in wire_points(node)],
                        "width_mm": number(node, "width"),
                        "source_curve_deg": number(node, "curve"),
                    }
                )
            elif node.tag == "via":
                via = {
                    "net": net,
                    "ref": None,
                    "center_mm": [number(node, "x"), number(node, "y")],
                    "extent": node.get("extent"),
                    "drill_mm": number(node, "drill"),
                    "diameter_mm": number(node, "diameter")
                    if node.get("diameter") is not None
                    else None,
                    "shape": node.get("shape", "round"),
                    "layer": 18,
                }
                vias.append(via)
            elif node.tag == "polygon":
                copper_polygons.append(
                    {
                        "net": net,
                        "ref": None,
                        "layer": int(node.get("layer", "0")),
                        "width_mm": number(node, "width"),
                        "vertices": [
                            {
                                "xy_mm": [number(v, "x"), number(v, "y")],
                                "curve_deg": number(v, "curve"),
                            }
                            for v in node.findall("vertex")
                        ],
                        "source_attributes": dict(node.attrib),
                        "poured_fill_available": False,
                        "meaning": "Source pour boundary only; no calculated copper clearance/thermal/island fill",
                    }
                )
    counts = {
        "placements": len(placements),
        "smd_pads": sum(p["kind"] == "smd" for p in pads),
        "through_pads": sum(p["kind"] == "pad" for p in pads),
        "drills": len(drills),
        "vias": len(vias),
        "traces": len(traces),
        "nets": len(nets),
        "contactrefs": len(contacts),
        "copper_polygon_boundaries": len(copper_polygons),
        "silk_rectangles": sum(len(g["corners_mm"]) for g in silk["rectangle_groups"]),
        "silk_lines": len(silk["lines"]),
        "silk_circles": len(silk["circles"]),
        "silk_polygons": len(silk["polygons"]),
        "silk_texts": len(silk["texts"]),
    }
    if any(
        counts[k] != v
        for k, v in {
            "placements": 26,
            "smd_pads": 68,
            "through_pads": 14,
            "vias": 26,
            "traces": 208,
            "nets": 14,
            "contactrefs": 71,
            "copper_polygon_boundaries": 2,
        }.items()
    ):
        raise ValueError("Source layout coverage differs from pinned board")
    return {
        "schema_version": 1,
        "id": ID,
        "part_id": base["part_id"],
        "configuration_id": base["configuration_id"],
        "specification_sha256": base["specification_sha256"],
        "source": base["source"],
        "license": base["license"],
        "units": "mm",
        "frame": "Manufacturer board XY,+Yup; no vehicle registration; all features are planar source data",
        "transform_convention": "Package-local mirrorX across localY,then source rotation,then placement; mirrored copper/silk layer pairs retained",
        "pcb_thickness_mm": None,
        "component_heights_available": False,
        "pcb_size_mm": base["pcb_size_mm"],
        "outline_bounds_mm": base["outline_bounds_mm"],
        "outline_segments_mm": base["outline_segments_mm"],
        "mounting_holes": base["mounting_holes"],
        "nominal_product_envelope_mm": base["nominal_product_envelope_mm"],
        "pcb_minus_nominal_xy_mm": base["pcb_minus_nominal_xy_mm"],
        "mating_tolerance_mm": None,
        "layers": layers,
        "placements": placements,
        "pads": pads,
        "drills": drills,
        "vias": vias,
        "traces": traces,
        "nets": nets,
        "copper_polygon_boundaries": copper_polygons,
        "silkscreen": silk,
        "documentation": documentation,
        "counts": counts,
        "omitted_source_nodes": dict(omitted),
        "limitations": [
            "XY manufacturer source layers only; rendering separated layers may use labelled display offsets, never physicalZ",
            "PCB thickness,component heights,headers/population,incoming revision and installed registration unavailable",
            "U1 source valueADXL343 retained;incoming ADXL375 silicon identity not inferred",
            "Via copper diameter absent in source remains null; no fabricated annulus/DRC pour fill",
            "Text content/location/font metadata retained; exact glyph paths unavailable",
            "SMD corners retain source roundness; rectangular corner guides are not rounded pad outlines",
            "Source outline25.4×17.78mm differs from product envelope25.6×17.7×4.6mm; no silent scale/fit correction",
        ],
        "engineering_accepted": False,
        "mass_or_inertia_generated": False,
        "canonical_vehicle_geometry_changed": False,
    }


def main() -> None:
    import resource

    resource.setrlimit(resource.RLIMIT_CPU, (59, 60))
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    started = time.process_time()
    result = extract(args.source.read_bytes(), NOTICE.read_text().rstrip() + "\n")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(result, separators=(",", ":"), ensure_ascii=False) + "\n"
    OUTPUT.write_text(encoded)
    print(
        json.dumps(
            {
                "id": ID,
                "counts": result["counts"],
                "bytes": len(encoded.encode()),
                "sha256": hashlib.sha256(encoded.encode()).hexdigest(),
                "cpu_seconds": time.process_time() - started,
            }
        )
    )


if __name__ == "__main__":
    main()
