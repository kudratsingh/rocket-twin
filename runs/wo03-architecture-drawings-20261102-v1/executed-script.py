"""Presentation-only SVGs from immutable A/B records; no engineering execution."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-architecture-space-mass.yaml"
SOURCE = ROOT / "runs/wo03-architecture-space-mass-20261102-v1/record.json"
OUT = ROOT / "output/wo03-architecture"
RUN = ROOT / "runs/wo03-architecture-drawings-20261102-v1"
HELPER = ROOT / "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift"
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
COLORS = {
    "bg": "#101923",
    "panel": "#182532",
    "text": "#e1ebf2",
    "muted": "#acc0ce",
    "line": "#53697a",
    "root": "#c5a6f2",
    "thrust": "#88bdf7",
    "recovery": "#f0c378",
    "bond": "#d9dfeb",
    "red": "#efaaa3",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def element(parent, kind, **attrs):
    return ET.SubElement(
        parent,
        f"{{{NS}}}{kind}",
        {key.replace("_", "-"): str(value) for key, value in attrs.items()},
    )


def text(parent, x, y, value, size=15, fill=None, weight="400", anchor="start"):
    node = element(
        parent,
        "text",
        x=x,
        y=y,
        font_size=size,
        fill=fill or COLORS["text"],
        font_weight=weight,
        text_anchor=anchor,
    )
    node.text = str(value)
    return node


def line(parent, x1, y1, x2, y2, color=None, width=1.5, dash=None, marker=None):
    attrs = {
        "x1": x1,
        "y1": y1,
        "x2": x2,
        "y2": y2,
        "stroke": color or COLORS["line"],
        "stroke_width": width,
    }
    if dash:
        attrs["stroke_dasharray"] = dash
    node = element(parent, "line", **attrs)
    if marker:
        # Explicit display arrowheads survive the existing native SVG importer.
        angle = math.atan2(y2 - y1, x2 - x1)
        points = [(x2, y2)]
        for sign in (-1, 1):
            points.append(
                (
                    x2 - 9 * math.cos(angle) + sign * 4 * math.sin(angle),
                    y2 - 9 * math.sin(angle) - sign * 4 * math.cos(angle),
                )
            )
        element(
            parent,
            "polygon",
            points=" ".join(f"{x},{y}" for x, y in points),
            fill=color or COLORS[marker],
        )
    return node


def rect(parent, x, y, width, height, fill, stroke=None, dash=None, rx=0):
    attrs = {"x": x, "y": y, "width": width, "height": height, "fill": fill, "rx": rx}
    if stroke:
        attrs.update(stroke=stroke, stroke_width=1.5)
    if dash:
        attrs["stroke_dasharray"] = dash
    return element(parent, "rect", **attrs)


def wrap(value, width=62):
    lines = []
    for word in value.split():
        if not lines or len(lines[-1]) + len(word) + 1 > width:
            lines.append(word)
        else:
            lines[-1] += " " + word
    return lines


def paragraph(parent, x, y, value, width=62, size=14, fill=None, leading=20):
    for index, part in enumerate(wrap(value, width)):
        text(parent, x, y + index * leading, part, size, fill)


def draw(config, source, architecture, identities):
    is_a = architecture["id"].startswith("A_")
    title = "A | Integrated motor-fin can" if is_a else "B | Captured outer roots"
    svg = ET.Element(
        f"{{{NS}}}svg",
        {"viewBox": "0 0 1600 1440", "width": "1600", "height": "1440", "role": "img"},
    )
    element(svg, "title").text = title + " — dimensioned concept / both not admitted"
    element(svg, "desc").text = (
        "Source-linked longitudinal and connection drawing. Nose origin z=0; displayed region z=900 through1227mm. Concept envelopes, not CAD or spatial stress."
    )
    element(svg, "metadata").text = json.dumps(
        {
            "architecture": architecture["id"],
            "status": architecture["status"],
            "units": "mm, g, N, cal, m/s",
            "origin": "z=0 at nose; stations increase aft",
            "representation": "Dimensioned concept/envelope, not CAD, stress, thermal or validated motion",
            "inputs_sha256": identities,
        },
        sort_keys=True,
    )
    defs = element(svg, "defs")
    for key in ("root", "thrust", "recovery", "bond"):
        marker = element(
            defs, "marker", id=key, markerWidth=10, markerHeight=10, refX=8, refY=5, orient="auto"
        )
        element(marker, "path", d="M0 0L9 5L0 10Z", fill=COLORS[key])
    pattern = element(
        defs,
        "pattern",
        id="reservation",
        width=9,
        height=9,
        patternUnits="userSpaceOnUse",
        patternTransform="rotate(40)",
    )
    line(pattern, 0, 0, 0, 9, COLORS["thrust"], 1)
    rect(svg, 0, 0, 1600, 1440, COLORS["bg"])
    group = element(svg, "g", font_family="Arial, Helvetica, sans-serif")
    text(group, 42, 40, title, 27, weight="700")
    text(
        group,
        42,
        68,
        "CONCEPT / ENVELOPE — NOT ADMITTED | A is preferred joint direction only; no engineering acceptance",
        16,
        COLORS["red"],
        "700",
    )
    text(
        group,
        42,
        94,
        "Units: mm unless stated | z=0 at nose, positive aft | shown aft-region geometry; radial display ×3",
        14,
        COLORS["muted"],
    )
    text(
        group,
        42,
        117,
        "Config SHA-256: " + identities[str(CONFIG.relative_to(ROOT))],
        12,
        COLORS["muted"],
    )
    text(
        group,
        42,
        137,
        "Record SHA-256: " + identities[str(SOURCE.relative_to(ROOT))],
        12,
        COLORS["muted"],
    )

    rect(group, 42, 157, 1516, 112, COLORS["panel"], COLORS["line"], rx=7)
    headers = [
        (60, "Recorded complete case"),
        (350, "Total incl. separate50 g"),
        (650, "Loaded / burnout static cal"),
        (1030, "Guide1.5 /1.8 /1.971 m, m/s"),
    ]
    for x, label in headers:
        text(group, x, 181, label, 13, COLORS["muted"])
    for index, case in enumerate(architecture["cases"]):
        y = 212 + index * 32
        text(group, 60, y, "Nominal" if index == 0 else "Additional20 g / motor-CG probe", 14)
        text(group, 350, y, f"{case['total_g']:.3f} g", 17, weight="700")
        text(
            group, 650, y, f"{case['loaded_static_cal']:.3f} / {case['burnout_static_cal']:.3f}", 16
        )
        text(
            group,
            1030,
            y,
            " / ".join(f"{item['rail_exit_speed_mps']:.3f}" for item in case["guides"]),
            16,
        )
    text(
        group,
        42,
        293,
        "Both fail the unchanged1.5 m formal departure screen. Longer-guide numbers are conditional; no equipment confirmed.",
        14,
        COLORS["red"],
    )
    text(
        group,
        42,
        327,
        "01  LONGITUDINAL FIN-PLANE CUT — one representative fin / axis stations, no shell or bond qualification",
        16,
        weight="700",
    )
    x0, y0, sx, sr = 100, 507, 4.18, 3
    px = lambda z: x0 + (z - 900) * sx
    py = lambda r: y0 - r * sr
    common = config["common"]

    def shell(item, color, key="r_inner_outer_mm"):
        ri, ro = item[key]
        start, end = item["start_end_mm"]
        for sign in (-1, 1):
            top = min(py(sign * ri), py(sign * ro))
            rect(group, px(start), top, (end - start) * sx, (ro - ri) * sr, color, color)

    # All dimensions below are presentation transforms of config coordinates.
    shell(common["outer_can"], "#9dbac7")
    shell(common["motor_tube"], COLORS["thrust"])
    shell(common["fore_load_cap"], COLORS["recovery"])
    shell(common["fore_cuff"], COLORS["recovery"])
    for station in common["centering_rings"]["stations_mm"]:
        ring = {
            "r_inner_outer_mm": common["centering_rings"]["r_inner_outer_mm"],
            "start_end_mm": [
                station - common["centering_rings"]["thickness_mm"] / 2,
                station + common["centering_rings"]["thickness_mm"] / 2,
            ],
        }
        shell(ring, COLORS["thrust"])
    for key in ("motor_body_and_liner", "retainer_service"):
        volume = config["protected_volumes"][key]
        start, end = volume["start_end_mm"]
        radius = volume["radius_mm"]
        rect(
            group,
            px(start),
            py(radius),
            (end - start) * sx,
            2 * radius * sr,
            "url(#reservation)",
            COLORS["thrust"],
            "6 4",
        )
    root_start, root_end = config["B"]["socket_ring_stations_mm"]
    root_inner = (
        config["A"]["inner_outer_root_support_r_mm"][0]
        if is_a
        else config["B"]["root_r_inner_outer_mm"][0]
    )
    root_outer = common["outer_can"]["r_inner_outer_mm"][1]
    rect(
        group,
        px(root_start),
        py(root_outer),
        (root_end - root_start) * sx,
        (root_outer - root_inner) * sr,
        "#574763",
        COLORS["root"],
    )
    if not is_a:
        for station in config["B"]["socket_ring_stations_mm"]:
            item = {
                "r_inner_outer_mm": config["B"]["socket_rings_inner_outer_mm"],
                "start_end_mm": [
                    station - config["B"]["socket_ring_thickness_mm"] / 2,
                    station + config["B"]["socket_ring_thickness_mm"] / 2,
                ],
            }
            shell(item, COLORS["root"])
        line(group, px(root_start), py(root_inner), px(root_end), py(root_inner), COLORS["root"], 5)
    # Recovery at other azimuths is deliberately diagrammed outside this section.
    legs = config["protected_volumes"]["recovery_legs"]
    start, end = legs["start_end_mm"]
    line(group, px(start), 370, px(end), 370, COLORS["recovery"], 4)
    for z in (start, end):
        line(group, px(z), 362, px(z), 378, COLORS["recovery"])
    text(
        group,
        (px(start) + px(end)) / 2,
        352,
        f"Forward bridles z{start}–{end}; projected topology, not this fin-plane",
        13,
        COLORS["recovery"],
        anchor="middle",
    )
    line(group, px(900), y0, px(1227), y0, COLORS["line"], 1, "8 5")
    text(group, px(900) - 8, y0 - 8, "r=0", 12, COLORS["muted"], anchor="end")
    text(group, px(1227) + 10, y0 + 5, "aft", 13, COLORS["muted"])
    for z in (900, 950, 1000, 1050, 1100, 1150, 1200, 1227):
        line(group, px(z), 630, px(z), 640)
        text(group, px(z), 658, str(z), 12, COLORS["muted"], anchor="middle")
    line(group, px(900), 635, px(1227), 635)
    text(
        group,
        px(900),
        680,
        "Axial station z [mm from nose]; station markers are not a ground support",
        12,
        COLORS["muted"],
    )
    marks = [
        ((922 + 1212) / 2, 33, "1"),
        (1132, -17.2, "2"),
        (1007, -28, "3"),
        (1030, -31.3, "4"),
        (1140, 25, "5"),
        (1210, -23, "6"),
    ]
    for z, radius, label in marks:
        element(
            group,
            "circle",
            cx=px(z),
            cy=py(radius),
            r=12,
            fill=COLORS["bg"],
            stroke=COLORS["text"],
            stroke_width=1.5,
        )
        text(group, px(z), py(radius) + 5, label, 13, anchor="middle")
    text(
        group,
        px(root_start) + 10,
        393,
        "5  Dense through-body root; panel continues outward (not drawn)",
        12,
        COLORS["root"],
    )
    rect(group, px(1075), 490, 220, 26, COLORS["bg"], rx=4)
    text(
        group,
        px(1075) + 110,
        508,
        f"Motor reservation R{config['protected_volumes']['motor_body_and_liner']['radius_mm']}",
        13,
        COLORS["thrust"],
        anchor="middle",
    )
    rect(group, px(1197), 470, 116, 43, COLORS["bg"], rx=4)
    text(
        group,
        px(1197) + 58,
        487,
        f"Retainer R{config['protected_volumes']['retainer_service']['radius_mm']}",
        12,
        COLORS["thrust"],
        anchor="middle",
    )
    text(group, px(1197) + 58, 505, "reserved", 12, COLORS["thrust"], anchor="middle")
    text(group, 42, 715, "DIMENSION KEY / RECORDED LIMITATIONS", 15, weight="700")
    labels = [
        "1  Structural outer can R32.2–33; z922–1212. Fin slots exist; intact-tube stiffness is an optimistic reference.",
        "2  Structural motor tube R15.8–17.2; z1069–1195. Rings R17.2–32.2, thickness3; centres1072/1192.",
        "3  Fore load cap R12–32, thickness6; z1004–1010. R6 sewn-eye saddles z1010–1016: capacity unknown.",
        "4  Integral cuff R30.8–31.8; z1010–1050. Actual windows z1010–1018 at60/180/300°; see plan inset.",
        (
            "5  A: root depth15.8; support radii17.2/32.2;100-long ×12-wide bond patches. Peel and installed motion unknown."
            if is_a
            else "5  B: root R26–33, depth7; cheeks100×7×3; floor100×9.5×1.5;3-thick socket rings at1090/1190."
        ),
        "6  Motor service R15.8, z1069–1195; retainer R23, z1195–1227.20 g retainer +5 g adapter/bond reserved only.",
    ]
    for index, label in enumerate(labels):
        paragraph(group, 42, 744 + index * 35, label, 118, size=13, leading=17)

    text(group, 1120, 715, "02  CUFF / BRIDLE PLAN", 15, weight="700")
    cx, cy, scale = 1340, 842, 2.55
    for radius in common["outer_can"]["r_inner_outer_mm"]:
        element(
            group,
            "circle",
            cx=cx,
            cy=cy,
            r=radius * scale,
            fill="none",
            stroke="#9dbac7",
            stroke_width=1.5,
        )
    # Cuff windows are true open sectors; surviving arcs are not solid shielding.
    for start_angle, end_angle in ((-30, 30), (90, 150), (210, 270)):
        r = sum(common["fore_cuff"]["r_inner_outer_mm"]) / 2
        a, b = math.radians(start_angle), math.radians(end_angle)
        path = f"M{cx+r*scale*math.cos(a)} {cy-r*scale*math.sin(a)} A{r*scale} {r*scale} 0 0 0 {cx+r*scale*math.cos(b)} {cy-r*scale*math.sin(b)}"
        element(
            group,
            "path",
            d=path,
            fill="none",
            stroke=COLORS["recovery"],
            stroke_width=common["fore_cuff"]["r_inner_outer_mm"][1]
            - common["fore_cuff"]["r_inner_outer_mm"][0]
            + 2,
        )
    for angle in legs["axes_deg"]:
        for offset in legs["tangential_offsets_mm"]:
            a = math.radians(angle)
            rr = legs["centre_radius_mm"]
            xx = cx + scale * (rr * math.cos(a) - offset * math.sin(a))
            yy = cy - scale * (rr * math.sin(a) + offset * math.cos(a))
            node = rect(
                group,
                xx - legs["width_radial_mm"] * scale / 2,
                yy - legs["thickness_tangential_mm"] * scale / 2,
                legs["width_radial_mm"] * scale,
                legs["thickness_tangential_mm"] * scale,
                COLORS["recovery"],
            )
            node.set("transform", f"rotate({-angle} {xx} {yy})")
    text(group, cx, cy - 4, "z1010–1018", 12, COLORS["muted"], anchor="middle")
    text(group, cx, cy + 14, "true windows", 12, COLORS["muted"], anchor="middle")
    paragraph(
        group,
        1120,
        951,
        "Six broad legs:12.7 radial ×0.55 tangential; R24, t±6 at60/180/300°. Seam50; finished capacity unknown.",
        48,
        12,
        COLORS["muted"],
        17,
    )
    text(
        group,
        42,
        985,
        "03  FORCE / CONNECTION PATHS — schematic arrows, not spatial stress or solved reaction distribution",
        15,
        weight="700",
    )
    paths = [
        (
            "root",
            "FIN",
            [
                "Panel / dense root",
                "Tube + outer-can bonds" if is_a else "Cheeks / floor / socket rings",
                "Finite outer can / cuff",
                "Actual body / upper joint",
            ],
        ),
        (
            "thrust",
            "MOTOR",
            [
                "Actual thrust-ring contact?",
                "Tube / retainer adapter",
                "Finite rings / outer can",
                "Cuff / body bond",
            ],
        ),
        (
            "recovery",
            "RECOVERY",
            [
                "Backbone / sewn eyes",
                "R6 saddles / finite cap",
                "Windowed cuff / body lap",
                "Retained component joints",
            ],
        ),
        (
            "bond",
            "JOINTS",
            [
                "Contact / bond dimensions",
                "Root peel / cap spread?",
                "Finite body support?",
                "Capacity UNSATISFIED",
            ],
        ),
    ]
    for index, (color, label, nodes) in enumerate(paths):
        y = 1019 + index * 49
        text(group, 42, y + 18, label, 12, COLORS[color], "700")
        for n, label_text in enumerate(nodes):
            x = 150 + n * 345
            rect(
                group,
                x,
                y - 2,
                305,
                36,
                COLORS["panel"],
                COLORS[color],
                "5 4" if color == "bond" else None,
                rx=4,
            )
            text(group, x + 152.5, y + 21, label_text, 13, anchor="middle")
            if n < 3:
                line(group, x + 307, y + 16, x + 337, y + 16, COLORS[color], 2, marker=color)
    demands = architecture["section_demands"]
    rect(group, 42, 1231, 1516, 151, COLORS["panel"], COLORS["line"], rx=6)
    text(
        group,
        60,
        1257,
        "OPEN: sewn-eye/R6 bend capacity • root peel / socket bearing • cap load spreading • exact motor / retainer hot fit",
        15,
        COLORS["red"],
        "700",
    )
    text(
        group,
        60,
        1283,
        "20 g retainer and R23 envelope are reservations, not manufacturer-verified dimensions or installed mass.",
        14,
    )
    text(
        group,
        60,
        1307,
        f"Recorded ideal panel/play/tube proxy: {demands['panel_play_ideal_tube_best_case_proxy_mm']:.3f} mm; real installed movement unavailable.",
        14,
    )
    text(
        group,
        60,
        1331,
        f"Recorded adverse recovery screen: {architecture['cases'][1]['required_severe_recovery_DF3_mean_N']:.3f} N; no equal saddle/joint sharing or ideal ground.",
        14,
    )
    text(
        group,
        60,
        1355,
        "Full inertia, installed flutter and compatible temperatures unavailable. Required thermal / physical / flight gates unchanged.",
        14,
    )
    text(
        group,
        42,
        1410,
        f"Source identity: {config['id']} / {architecture['id']} | Presentation only; shapes are source-defined envelopes, not detailed CAD.",
        12,
        COLORS["muted"],
    )
    return ET.tostring(svg, encoding="unicode", xml_declaration=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--render",
        action="store_true",
        help="Use the existing AppKit SVG-to-PNG helper,120s combined maximum",
    )
    args = parser.parse_args()
    started = time.monotonic()
    config = yaml.safe_load(CONFIG.read_text())
    source = json.loads(SOURCE.read_text())
    assert source["input_sha256"][str(CONFIG.relative_to(ROOT))] == sha(CONFIG)
    assert source["selected_before_execution"] == config["budget"]["selected"]
    assert len(source["arrangements"]) == 2
    inputs = {
        str(path.relative_to(ROOT)): sha(path) for path in (CONFIG, SOURCE, Path(__file__), HELPER)
    }
    OUT.mkdir(parents=True, exist_ok=True)
    RUN.mkdir(parents=True, exist_ok=True)
    files = []
    for architecture in source["arrangements"]:
        name = (
            "architecture-A-motor-fin-can"
            if architecture["id"].startswith("A_")
            else "architecture-B-outer-captured-roots"
        )
        path = OUT / f"{name}.svg"
        svg = draw(config, source, architecture, inputs)
        ET.fromstring(svg)
        path.write_text(svg + "\n")
        files.append(path)
    render = {
        "requested": args.render,
        "renderer": str(HELPER.relative_to(ROOT)),
        "combined_limit_s": 120,
        "observations": [],
    }
    if args.render:
        deadline = time.monotonic() + 120
        for svg in files.copy():
            png = svg.with_suffix(".png")
            command = [
                "/usr/bin/swift",
                "-module-cache-path",
                "/private/tmp/rocket-twin-architecture-swift-cache",
                str(HELPER),
                str(svg),
                str(png),
            ]
            try:
                result = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=max(1, deadline - time.monotonic()),
                    env={**os.environ, "TMPDIR": "/private/tmp"},
                    check=False,
                )
                render["observations"].append(
                    {
                        "input": str(svg.relative_to(ROOT)),
                        "exit_code": result.returncode,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                    }
                )
                if result.returncode == 0:
                    files.append(png)
                else:
                    break
            except subprocess.TimeoutExpired:
                render["observations"].append(
                    {
                        "input": str(svg.relative_to(ROOT)),
                        "status": "combined_renderer_budget_exhausted",
                    }
                )
                break
    record = {
        "id": "wo03-architecture-drawings-20261102-v1",
        "status": "presentation_only_both_architectures_not_admitted",
        "input_sha256": inputs,
        "outputs_sha256": {str(path.relative_to(ROOT)): sha(path) for path in files},
        "render": render,
        "browser_verified": False,
        "engineering_calculation_executed": False,
        "elapsed_s": time.monotonic() - started,
    }
    (RUN / "record.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(
        json.dumps(
            {
                "status": record["status"],
                "outputs": list(record["outputs_sha256"]),
                "render": render,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
