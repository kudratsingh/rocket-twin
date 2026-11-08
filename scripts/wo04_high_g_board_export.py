"""Extract one pinned official Eagle XML drawing as read-only 2D footprint data.

The source is parsed as data, never executed. No board/package height, installed
fit or finished three-dimensional component model is inferred.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
BLOB = "4a768fc9f113ba6f95c6e930a3fac436d066f82a"
SHA256 = "7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c"
SOURCE = ROOT / ".cache/hardware-detail-sources/Adafruit_ADXL375_4a768fc9.brd"
NOTICE = ROOT / ".cache/hardware-detail-sources/Adafruit_ADXL375_README.md"
OUTPUT = ROOT / "web/src/data/highGBoardLayout.json"


def number(node: ET.Element, key: str, default: float = 0) -> float:
    result = float(node.get(key, str(default)))
    if not math.isfinite(result):
        raise ValueError("Nonfinite manufacturer coordinate")
    return result


def wire_points(node: ET.Element) -> list[list[float]]:
    x1, y1, x2, y2 = [number(node, k) for k in ("x1", "y1", "x2", "y2")]
    angle = math.radians(number(node, "curve"))
    if abs(angle) < 1e-12:
        return [[x1, y1], [x2, y2]]
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy)
    offset = length / (2 * math.tan(angle / 2))
    cx, cy = (x1 + x2) / 2 - dy / length * offset, (y1 + y2) / 2 + dx / length * offset
    radius = math.hypot(x1 - cx, y1 - cy)
    start = math.atan2(y1 - cy, x1 - cx)
    count = max(2, math.ceil(abs(math.degrees(angle)) / 5))
    return [
        [
            cx + radius * math.cos(start + angle * i / count),
            cy + radius * math.sin(start + angle * i / count),
        ]
        for i in range(count + 1)
    ]


def extract(raw: bytes, attribution: str) -> dict[str, Any]:
    if (
        hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest() != BLOB
        or hashlib.sha256(raw).hexdigest() != SHA256
    ):
        raise ValueError("Manufacturer board bytes do not match pinned immutable artifact")
    if "5374" not in attribution or "Creative Commons" not in attribution:
        raise ValueError("Manufacturer attribution notice unavailable")
    root = ET.fromstring(raw)
    board = root.find("./drawing/board")
    if board is None:
        raise ValueError("Pinned source has no Eagle board")
    outline = [wire_points(w) for w in board.findall("./plain/wire") if w.get("layer") == "20"]
    if len(outline) != 8:
        raise ValueError("Unexpected board outline; stop instead of guessing")
    packages = {
        (lib.get("name"), p.get("name")): p
        for lib in board.findall("./libraries/library")
        for p in lib.findall("./packages/package")
    }
    placements = []
    shapes = []
    for element in board.findall("./elements/element"):
        ref = element.get("name", "")
        package = element.get("package", "")
        rot = element.get("rot", "R0")
        ex, ey = number(element, "x"), number(element, "y")
        degrees = (
            float(re.search(r"R([-\d.]+)", rot).group(1)) if re.search(r"R([-\d.]+)", rot) else 0
        )
        theta = math.radians(degrees)
        mirrored = "M" in rot
        pkg = packages[(element.get("library"), package)]
        placement = {
            "ref": ref,
            "value": element.get("value", ""),
            "library": element.get("library"),
            "package": package,
            "position_mm": [ex, ey],
            "rotation_deg": degrees,
            "side": "bottom" if mirrored else "top",
            "source_texts": [t.text for t in pkg.findall("text") if t.text],
            "height_mm": None,
        }
        placements.append(placement)
        # Bottom mirrored graphics are listed, not guessed into a top-side drawing.
        if mirrored:
            placement["drawing_note"] = (
                "Bottom/mirrored source footprint listed; not projected in this bounded top view"
            )
            continue
        if package.startswith(("ADAFRUIT", "STEMMAQT", "PCBFEAT")):
            placement["drawing_note"] = (
                "Decorative manufacturer artwork listed; omitted from footprint drawing"
            )
            continue

        def point(
            x: float, y: float, ex: float = ex, ey: float = ey, theta: float = theta
        ) -> list[float]:
            return [
                ex + x * math.cos(theta) - y * math.sin(theta),
                ey + x * math.sin(theta) + y * math.cos(theta),
            ]

        for node in pkg:
            layer = node.get("layer")
            if node.tag == "wire" and layer in ("21", "51"):
                shapes.append(
                    {
                        "kind": "polyline",
                        "ref": ref,
                        "points_mm": [point(*p) for p in wire_points(node)],
                        "width_mm": number(node, "width"),
                        "role": "silk" if layer == "21" else "documentation",
                    }
                )
            elif node.tag in ("smd", "rectangle") and (node.tag == "smd" or layer in ("21", "51")):
                if node.tag == "smd":
                    cx, cy, dx, dy = [number(node, k) for k in ("x", "y", "dx", "dy")]
                else:
                    x1, y1, x2, y2 = [number(node, k) for k in ("x1", "y1", "x2", "y2")]
                    cx, cy, dx, dy = (x1 + x2) / 2, (y1 + y2) / 2, x2 - x1, y2 - y1
                local_angle = math.radians(float(node.get("rot", "R0").replace("R", "")))
                corners = [
                    point(
                        cx + x * math.cos(local_angle) - y * math.sin(local_angle),
                        cy + x * math.sin(local_angle) + y * math.cos(local_angle),
                    )
                    for x, y in (
                        (-dx / 2, -dy / 2),
                        (dx / 2, -dy / 2),
                        (dx / 2, dy / 2),
                        (-dx / 2, dy / 2),
                    )
                ]
                shapes.append(
                    {
                        "kind": "polygon",
                        "ref": ref,
                        "points_mm": corners,
                        "role": "pad" if node.tag == "smd" else "silk",
                        "source_roundness_percent": number(node, "roundness"),
                    }
                )
            elif node.tag in ("pad", "hole"):
                center = point(number(node, "x"), number(node, "y"))
                shapes.append(
                    {
                        "kind": "circle",
                        "ref": ref,
                        "center_mm": center,
                        "radius_mm": number(node, "drill") / 2,
                        "role": "drill",
                        "name": node.get("name"),
                        "copper_outer_shape": "not inferred when not explicit",
                    }
                )
            elif node.tag == "circle" and layer in ("21", "51"):
                shapes.append(
                    {
                        "kind": "circle",
                        "ref": ref,
                        "center_mm": point(number(node, "x"), number(node, "y")),
                        "radius_mm": number(node, "radius"),
                        "role": "silk",
                    }
                )
    points = [p for segment in outline for p in segment]
    outline_bounds = [
        [min(p[i] for p in points) for i in range(2)],
        [max(p[i] for p in points) for i in range(2)],
    ]
    for shape in shapes:
        if "points_mm" in shape:
            points.extend(shape["points_mm"])
        else:
            x, y = shape["center_mm"]
            r = shape["radius_mm"]
            points.extend([[x - r, y - r], [x + r, y + r]])
    bounds = [
        [min(p[i] for p in points) for i in range(2)],
        [max(p[i] for p in points) for i in range(2)],
    ]
    mounts = [
        s
        for s in shapes
        if s["role"] == "drill"
        and next(p for p in placements if p["ref"] == s["ref"])["package"]
        == "MOUNTINGHOLE_2.5_PLATED"
    ]
    if len(mounts) != 4 or len(placements) != 26:
        raise ValueError("Unexpected manufacturer placement/hole coverage")
    return {
        "schema_version": 1,
        "id": "adafruit-5374-pcb-2d-4a768fc9-v1",
        "part_id": "high_g_accel",
        "configuration_id": "G80-F2-RP1-AD1-definition-v2",
        "specification_sha256": "811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660",
        "source": {
            "manufacturer": "Adafruit Industries",
            "product_id": "5374",
            "url": "https://github.com/adafruit/Adafruit_ADXL375_PCB/blob/main/Adafruit%20ADXL375.brd",
            "immutable_blob_url": f"https://api.github.com/repos/adafruit/Adafruit_ADXL375_PCB/git/blobs/{BLOB}",
            "git_blob_sha": BLOB,
            "sha256": SHA256,
            "bytes": len(raw),
            "eagle_version": root.get("version"),
        },
        "license": {
            "name": "Creative Commons Attribution-ShareAlike 3.0 Unported",
            "spdx": "CC-BY-SA-3.0",
            "url": "https://github.com/adafruit/Adafruit_ADXL375_PCB/blob/main/license.txt",
            "credit": "Designed by Limor Fried/Ladyada for Adafruit Industries",
            "upstream_notice": attribution,
        },
        "units": "mm",
        "frame": "Manufacturer PCB XY, origin retained, +Y up; no installed vehicle registration",
        "outline_segments_mm": outline,
        "outline_bounds_mm": outline_bounds,
        "pcb_size_mm": [round(outline_bounds[1][i] - outline_bounds[0][i], 5) for i in range(2)],
        "drawing_bounds_mm": bounds,
        "nominal_product_envelope_mm": [25.6, 17.7, 4.6],
        "pcb_minus_nominal_xy_mm": [-0.2, 0.08],
        "mating_tolerance_mm": None,
        "placements": placements,
        "shapes": shapes,
        "mounting_holes": mounts,
        "maturity": "Manufacturer PCB layout drawing only; not incoming hardware, full 3D assembly or installed fit",
        "missing": [
            "All component/package heights and actual header population undefined",
            "Board revision of incoming hardware unverified",
            "Bottom/mirrored source graphics listed but not projected; routing, decorative artwork and true font outlines omitted",
            "Pad/drill outlines are footprints, not installed package bodies",
            "SMD pad corner roundness is retained in data but drawn as rectangular footprints",
            "U1 source value is ADXL343 in official ADXL375/PID5374 file; source label retained, silicon identity not inferred",
            "PCB25.4×17.78mm versus nominal product25.6×17.7mm: datums/tolerances undefined; no fit pass or silent scale correction",
        ],
        "engineering_accepted": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    args = parser.parse_args()
    data = extract(args.source.read_bytes(), NOTICE.read_text().rstrip() + "\n")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2) + "\n")
    print(
        json.dumps(
            {
                "id": data["id"],
                "pcb_size_mm": data["pcb_size_mm"],
                "drawing_bounds_mm": data["drawing_bounds_mm"],
                "placements": len(data["placements"]),
                "shapes": len(data["shapes"]),
            }
        )
    )


if __name__ == "__main__":
    main()
