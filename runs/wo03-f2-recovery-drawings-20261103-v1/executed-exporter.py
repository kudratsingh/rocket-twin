"""Export source-linked recovery concepts; no physics, CAD, solver or renderer."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)
INK = "#15334a"
MUTED = "#526778"
NEW = "#087f78"
WOOD = "#bf8750"
CORD = "#b3482b"
AMBER = "#986500"
GHOST = "#8795a1"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def number(value, digits=3):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        return "unavailable"
    return f"{value:,.{digits}f}"


class SVG:
    def __init__(self, title, subtitle, height=1180, status="UNADOPTED CONCEPT"):
        self.root = ET.Element(
            f"{{{NS}}}svg",
            {"width": "1700", "height": str(height), "viewBox": f"0 0 1700 {height}"},
        )
        ET.SubElement(self.root, f"{{{NS}}}title").text = title
        self.rect(0, 0, 1700, height, fill="#f5f8fa", stroke="none")
        self.text(48, 56, title, size=30, weight="bold")
        self.text(48, 87, subtitle, size=17, color=MUTED)
        self.rect(1375, 31, 273, 39, fill="#fff0cc", stroke="#d4af61", rx=7)
        self.text(1391, 57, status, size=15 if len(status) > 20 else 18, color=AMBER, weight="bold")

    def add(self, tag, **attrs):
        return ET.SubElement(
            self.root,
            f"{{{NS}}}{tag}",
            {k.replace("_", "-"): str(v) for k, v in attrs.items() if v is not None},
        )

    def rect(self, x, y, w, h, fill="none", stroke=INK, **kw):
        return self.add("rect", x=x, y=y, width=w, height=h, fill=fill, stroke=stroke, **kw)

    def line(self, x1, y1, x2, y2, color=INK, width=2, dash=None):
        return self.add(
            "line",
            x1=x1,
            y1=y1,
            x2=x2,
            y2=y2,
            stroke=color,
            stroke_width=width,
            stroke_dasharray=dash,
        )

    def text(self, x, y, text, size=16, color=INK, weight=None, anchor=None, family="Arial"):
        item = self.add(
            "text",
            x=x,
            y=y,
            fill=color,
            font_size=size,
            font_family=family,
            font_weight=weight,
            text_anchor=anchor,
        )
        item.text = str(text)
        return item

    def lines(self, x, y, lines, size=16, color=INK, gap=23, width=None):
        expanded = []
        for line in lines:
            expanded.extend(textwrap.wrap(line, width=width) if width else [line])
        for i, line in enumerate(expanded):
            self.text(x, y + i * gap, line, size=size, color=color)
        return y + len(expanded) * gap

    def arrow(self, points, color=NEW, width=3, dash=None):
        self.add(
            "polyline",
            points=" ".join(f"{x},{y}" for x, y in points),
            fill="none",
            stroke=color,
            stroke_width=width,
            stroke_dasharray=dash,
            stroke_linejoin="round",
        )
        ax, ay = points[-2]
        bx, by = points[-1]
        length = math.hypot(bx - ax, by - ay)
        if length == 0:
            raise ValueError("Zero-length arrow head")
        ux, uy = (bx - ax) / length, (by - ay) / length
        tip = [
            (bx, by),
            (bx - 11 * ux + 5 * uy, by - 11 * uy - 5 * ux),
            (bx - 11 * ux - 5 * uy, by - 11 * uy + 5 * ux),
        ]
        self.add("polygon", points=" ".join(f"{x},{y}" for x, y in tip), fill=color)

    def dim(self, x1, x2, y, label, color=MUTED):
        self.line(x1, y - 7, x1, y + 7, color=color, width=1)
        self.line(x2, y - 7, x2, y + 7, color=color, width=1)
        self.arrow([(x1, y), (x2, y)], color=color, width=1)
        self.arrow([(x2, y), (x1, y)], color=color, width=1)
        self.text((x1 + x2) / 2, y - 12, label, size=14, color=color, anchor="middle")

    def link(self, x, y, label, href):
        group = self.add("a", href=href)
        node = ET.SubElement(
            group,
            f"{{{NS}}}text",
            {"x": str(x), "y": str(y), "fill": NEW, "font-size": "14", "font-family": "Arial"},
        )
        node.text = label

    def footer(self, metadata, y):
        self.line(48, y - 18, 1652, y - 18, color="#c5d1d9", width=1)
        self.text(
            48,
            y + 3,
            f"Identity: {metadata['identity']} | dimensions mm; ledger g; recorded loads N",
            size=14,
        )
        self.text(
            48,
            y + 25,
            f"Raw specification SHA256: {metadata['specification']['sha256']}",
            size=12,
            family="Menlo",
        )
        self.text(
            48,
            y + 45,
            f"Raw record SHA256:        {metadata['record']['sha256']}",
            size=12,
            family="Menlo",
        )
        self.text(
            48,
            y + 67,
            "Source/build/offline artifact only. No browser, installed strength, thermal or flight acceptance.",
            size=14,
            color=AMBER,
        )

    def write(self, path, metadata):
        node = ET.SubElement(self.root, f"{{{NS}}}metadata")
        node.text = json.dumps(metadata, separators=(",", ":"))
        ET.indent(self.root)
        ET.ElementTree(self.root).write(path, encoding="utf-8", xml_declaration=True)


def part_bounds(part):
    geometry = part["geometry"]
    extent = geometry.get("length_m")
    if extent is None:
        extent = geometry.get("bbox_m", [None])[0]
    if extent is None:
        raise ValueError(f"Missing longitudinal extent: {part['id']}")
    return part["position_m"] * 1000, (part["position_m"] + extent) * 1000


def require_stations(parts):
    expected = {
        "motor_tube": (1055, 1220),
        "forward_ring": (1060, 1072.2),
        "fin_tabs": (1080.2, 1189.6),
        "aft_ring": (1190, 1196),
        "body": (458, 1220),
    }
    result = {}
    for key, bounds in expected.items():
        actual = part_bounds(parts[key])
        if any(abs(a - b) > 0.001 for a, b in zip(actual, bounds)):
            raise ValueError(f"RP1 station differs from declared drawing scope: {key}: {actual}")
        result[key] = actual
    return result


def connection(spec, record, metadata):
    parts = {part["id"]: part for part in spec["parts"]}
    bounds = require_stations(parts)
    wrap = parts["rp1_kevlar_wrap"]["cad"]["parameters"]
    wrap_start, wrap_end = wrap["wrap_axial_min_m"] * 1000, wrap["wrap_axial_max_m"] * 1000
    exit_angle = wrap["exit_angle_deg"]
    if abs(wrap_start - bounds["forward_ring"][1]) > 0.001 or abs(wrap_end - 1077) > 0.001:
        raise ValueError("Wrap station no longer matches the declared RP1 concept")
    historical_path = ROOT / "configs/vehicle/candidates/g80-f2-c1-fit-proposal.yaml"
    historical = yaml.safe_load(historical_path.read_text())
    old_ring = next(part for part in historical["parts"] if part["id"] == "forward_ring")
    old_start, old_end = part_bounds(old_ring)
    svg = SVG(
        "RP1 recovery connection — dimensioned longitudinal concept",
        "z increases aft from nose; source projection with routed cord intent, not manufactured CAD",
    )
    svg.text(48, 132, "A  COMPLETE ROUTE / WHOLE-VEHICLE STATIONS", size=19, weight="bold")
    x = lambda z: 100 + z * 1.16
    y = 270
    svg.line(80, y, 1565, y, color="#a7b6c1", width=1, dash="7 5")
    svg.add(
        "polygon",
        points=f"{x(0)},{y} {x(160)},{y - 38} {x(160)},{y + 38}",
        fill="#dce7ed",
        stroke=INK,
    )
    svg.rect(x(160), y - 38, x(458) - x(160), 76, fill="#eef2f5")
    svg.rect(x(458), y - 38, x(1220) - x(458), 76, fill="#f4eadc")
    svg.rect(x(1055), y - 17, x(1220) - x(1055), 34, fill="#dce8ef")
    svg.rect(x(1060), y - 36, x(1072.2) - x(1060), 72, fill=WOOD)
    svg.rect(
        x(old_start), y - 36, x(old_end) - x(old_start), 72, stroke=GHOST, stroke_dasharray="4 3"
    )
    lip_guard = parts["rp1_lip_guard"]
    lip_station = lip_guard["position_m"] * 1000
    svg.rect(x(lip_station) - 5, y - 39, 10, 29, fill="#ffd579", stroke=AMBER, rx=3)
    svg.arrow(
        [(x(1077), y - 24), (x(650), y - 24), (x(160), y - 24), (x(160), 192), (x(420), 192)],
        color=CORD,
    )
    svg.arrow([(x(420), 192), (x(510), 148)], color=CORD)
    svg.add(
        "path",
        d=f"M {x(460)} 148 Q {x(510)} 95 {x(560)} 148 Z",
        fill="#d7efe9",
        stroke=NEW,
        stroke_width=2,
    )
    svg.arrow([(x(420), 192), (x(220), 168), (x(120), 235)], color=CORD)
    svg.text(x(505), 110, "CANOPY / MAIN NYLON", size=15, anchor="middle")
    svg.text(x(220), 158, "separately retained nose + anchor", size=15, anchor="middle")
    svg.text(
        x(700),
        217,
        "forward routed cord; packing / chafe / finite bonds unresolved",
        size=15,
        anchor="middle",
    )
    for station, label, ty in [
        (0, "0 nose", 339),
        (160, "160 rounded body lip", 364),
        (458, "458 fixed splice", 339),
        (1055, "1055 mount", 364),
        (1220, "1220 aft / motor removal", 339),
    ]:
        svg.line(x(station), y + 39, x(station), ty - 15, width=1, color=MUTED)
        svg.text(x(station), ty, label, size=14, anchor="middle")
    svg.dim(x(458), x(1220), 399, "body 458–1220 mm")
    svg.text(
        x(lip_station),
        386,
        f"lip guard {number(lip_guard['mass_kg'] * 1000, 0)} g ESTIMATE / unqualified",
        size=13,
        color=AMBER,
        anchor="middle",
    )
    svg.text(
        48,
        449,
        "B  AFT DETAIL / AXIAL STATIONS TO SCALE; TRANSVERSE SIZE SCHEMATIC",
        size=19,
        weight="bold",
    )
    dx = lambda z: 95 + (z - 1045) * 5.5
    cy = 626
    svg.rect(dx(1048), cy - 82, dx(1220) - dx(1048), 164, fill="#f6ecdf", stroke=INK)
    svg.rect(dx(1055), cy - 34, dx(1220) - dx(1055), 68, fill="#dce8ef", stroke=INK)
    svg.rect(dx(1055), cy - 22, dx(1220) - dx(1055), 44, fill="#fbfdff", stroke=MUTED)
    svg.text(dx(1140), cy + 5, "MOTOR BORE / AFT REMOVAL CORRIDOR", size=13, anchor="middle")
    for a, b in [bounds["forward_ring"], bounds["aft_ring"]]:
        svg.rect(dx(a), cy - 80, dx(b) - dx(a), 46, fill=WOOD)
        svg.rect(dx(a), cy + 34, dx(b) - dx(a), 46, fill=WOOD)
    for yy in [cy - 80, cy + 34]:
        svg.rect(
            dx(old_start), yy, dx(old_end) - dx(old_start), 46, stroke=GHOST, stroke_dasharray="5 4"
        )
    for yy in [cy - 69, cy + 36]:
        svg.rect(dx(1080.2), yy, dx(1189.6) - dx(1080.2), 33, fill="#e1bb8c", stroke=WOOD)
    for wrap_y in (cy - 44, cy + 34):
        svg.rect(
            dx(wrap_start),
            wrap_y,
            dx(wrap_end) - dx(wrap_start),
            10,
            fill="none",
            stroke=CORD,
            stroke_width=4,
        )
    svg.text(350, 528, "External wrap segments only; motor bore stays clear", size=13, color=CORD)
    svg.arrow(
        [(dx(wrap_start + 2), cy - 44), (dx(wrap_start + 2), cy - 113), (dx(1050), cy - 113)],
        color=CORD,
    )
    svg.text(
        96, 493, "cord exits forward via ONE 60° notch; bore remains clear", size=15, color=CORD
    )
    svg.line(dx(1072.2), cy + 84, dx(1072.2), 764, color=NEW, width=1)
    svg.line(dx(1080.2), cy + 84, dx(1080.2), 764, color=CORD, width=1)
    svg.text(96, 790, "NEW ring 1060–1072.2", size=15, color=NEW)
    svg.text(96, 815, "wrap proposal envelope 1072.2–1077.0", size=15, color=CORD)
    svg.text(96, 840, "old ring 1075–1087.2 ghosted; old tab-end bond is LOST", size=15, color=CORD)
    svg.dim(dx(1080.2), dx(1189.6), 742, "fin tabs 1080.2–1189.6")
    svg.dim(dx(1055), dx(1220), 878, "motor tube 1055–1220 mm; aft ring 1190–1196 mm")
    svg.arrow([(dx(1220), cy), (dx(1220) + 50, cy)], color=MUTED)
    svg.text(1172, 495, "C  DIFFERENT AXIAL STATIONS", size=18, weight="bold")
    ccx, ccy = 1335, 616
    svg.add("circle", cx=ccx, cy=ccy, r=78, fill="#f2e5d2", stroke=WOOD, stroke_width=3)
    svg.add("circle", cx=ccx, cy=ccy, r=38, fill="#f9fcfd", stroke=INK, stroke_width=2)
    svg.add("circle", cx=ccx, cy=ccy, r=46, fill="none", stroke=CORD, stroke_width=5)
    angle = math.radians(exit_angle)
    ex, ey = ccx + 78 * math.cos(angle), ccy - 78 * math.sin(angle)
    svg.arrow(
        [(ccx + 46 * math.cos(angle), ccy - 46 * math.sin(angle)), (ex + 35, ey - 32)], color=CORD
    )
    svg.rect(1437, 582, 74, 54, stroke=AMBER, stroke_dasharray="5 4")
    svg.text(1437, 658, "knot reservation only", size=13, color=AMBER)
    svg.lines(
        1172,
        734,
        [
            "Loop section: just aft of new ring.",
            "Exit notch: 60° on ring.",
            "Tabs: 0° / 120° / 240° farther aft.",
            "Overlay is explanatory, not same-plane CAD.",
            "Actual knot / bend envelope: unavailable.",
            "No rigid support or mechanical capture credit.",
        ],
        size=15,
        gap=24,
    )
    svg.rect(48, 921, 1604, 102, fill="#fff4dc", stroke="#d4b268", rx=8)
    svg.lines(
        68,
        949,
        [
            "OPEN: loop termination, ring/tube/body finite bonds, lost fin-tab end connection, hot cord/bond/substrate properties.",
            "Nose/anchor retention, full harness extraction and actual motor/retainer contact remain separate holds.",
            "No load sharing, contact pressure, knot dimensions or thermal field is invented by this drawing.",
        ],
        size=16,
        gap=26,
    )
    svg.link(
        48,
        1054,
        "Source precedent notes / exact versions",
        "../../docs/wo03-f2-recovery-precedents-source-notes.md",
    )
    svg.link(
        670, 1054, "RP1 specification / raw source", "../../" + metadata["specification"]["path"]
    )
    svg.footer(metadata, 1080)
    return svg


def comparison(spec, record, metadata):
    svg = SVG(
        "Recovery connection precedents — topology and evidence",
        "Four documented versions beside frozen F2-C1 and the one unadopted RP1 recommendation",
        height=1320,
        status="RP1 NOT ADOPTED",
    )
    cards = [
        (
            "01  MAD COW DX3 / K-126 linked manual",
            "Motor-tube loop",
            [
                "Kevlar → loop around mount → forward ring / tube",
                "bonded mount / fin roots → body",
                "Nylon → payload bulkhead eye → payload; nose hold open",
            ],
            "pp2–4; current K-3126 links older manual. No measured joint capacity.",
            "https://www.madcowrocketry.com/content/pdf/dx3.pdf",
            NEW,
        ),
        (
            "02  LOC HI-TECH PK-56 / current linked manual",
            "Forward-ring eyebolt",
            [
                "Sewn-loop nylon → eye / nuts / washers → forward ring",
                "ring + motor tube / body bonds → retained body",
                "payload screw eye / bulkhead → payload → retained nose",
            ],
            "pp1–4; storefront Kevlar/webbing differs. No measured joint capacity.",
            "https://cdn.shopify.com/s/files/1/0568/7489/3503/files/PK-56_HiTech_Build_Instructions.pdf?v=1639515959",
            NEW,
        ),
        (
            "03  LOC HI-TECH PK-56 / historical ©2013",
            "Inner-wall cord mount",
            [
                "Knotted cord ends + epoxy patch → inner paper wall",
                "elastic main cord → payload attachment",
                "Motor-mount rings are a separate body connection",
            ],
            "p2; historical version, not combined with current instructions.",
            "https://www.apogeerockets.com/downloads/instructions/PK-56_Hi-Tech_Assy.pdf",
            GHOST,
        ),
        (
            "04  AEROTECH INITIATOR / linked ©2004 manual",
            "Molded-baffle screw eye",
            [
                "Cord → screw eye → molded baffle / flange / ring",
                "baffle / motor-tube / body assembly → retained body",
                "Elastic cord → molded nose-shoulder loop; canopy ~1 ft from nose",
            ],
            "p3 LABYRINTH / p5 nose + canopy route; kit precedent only.",
            "https://d3l66gvjdr7rqw.cloudfront.net/Templates/170652/myimages/initiator_in_8-04_1674501193528.pdf",
            NEW,
        ),
        (
            "05  FROZEN F2-C1 / NOT ADOPTED",
            "Paired M4 eyes + blind-notched ring",
            [
                "Bridle → 2 provisional eyes / washers → ring",
                "Recovery opens tab-floor gap: adhesive tension / shear",
                "Finished hardware, transverse wood and peel unknown",
            ],
            "Frozen reference only; historical ring ghosted on connection.svg.",
            "../../docs/wo03-g80-f2-c1-decision.md",
            CORD,
        ),
        (
            "06  RP1 / ONE RECOMMENDATION, NOT ADOPTED",
            "Cord wrap aft of moved forward ring",
            [
                "New Kevlar wrap → new forward ring / motor tube",
                "Finite bonds → body; former tab-end bond lost",
                "Main nylon + lip guard → canopy / separately retained nose",
            ],
            "Complete source ledger below; actual knot, heat and joint capacity held.",
            "../../" + metadata["specification"]["path"],
            NEW,
        ),
    ]
    for i, (title, topology, chain, caution, href, color) in enumerate(cards):
        col, row = i % 2, i // 2
        xx, yy = 48 + 824 * col, 124 + 268 * row
        svg.rect(xx, yy, 780, 246, fill="#ffffff", stroke="#c8d4dc", rx=8)
        svg.rect(xx, yy, 7, 246, fill=color, stroke="none")
        svg.text(xx + 22, yy + 29, title, size=17, weight="bold", color=color)
        svg.text(xx + 22, yy + 59, topology, size=22, weight="bold")
        for j, item in enumerate(chain):
            ly = yy + 92 + 29 * j
            svg.arrow([(xx + 22, ly - 5), (xx + 43, ly - 5)], color=color, width=2)
            svg.text(xx + 53, ly, item, size=15)
        svg.lines(xx + 22, yy + 188, [caution], size=13, color=MUTED, gap=18, width=96)
        svg.link(xx + 22, yy + 226, "Original source / exact record", href)
    svg.text(
        48,
        964,
        "RECORDED RP1 PACKAGE / DISPLAY ONLY — NO NEW ENGINEERING COMPUTATION",
        size=18,
        weight="bold",
    )
    for i, case in enumerate(record["cases"]):
        yy = 994 + i * 45
        guide = case.get("guide_mps", {})
        svg.text(
            48,
            yy,
            f"{case['case']}: {number(case.get('total_mass_kg', 0) * 1000 if case.get('total_mass_kg') is not None else None)} g; "
            f"CG {number(case.get('cg_m', 0) * 1000 if case.get('cg_m') is not None else None)} mm; "
            f"static {number(case.get('margin_cal'))} cal; guide1.5 m {number(guide.get('1.5'), 6)} m/s; "
            f"required whole/body {number(case.get('required_whole_mean_proxy_N'))}/{number(case.get('required_body_proxy_N'))} N",
            size=15,
        )
        svg.text(
            48,
            yy + 21,
            f"Formal / planning mass headroom {number(case.get('formal_mass_headroom_g'))} / "
            f"{number(case.get('planning_mass_headroom_g'))} g (negative = fails); "
            f"conditional1.8 m guide {number(guide.get('1.8'), 6)} m/s; equipment unconfirmed",
            size=14,
            color=CORD,
        )
    yy = 1093
    svg.text(
        48,
        yy,
        f"Ledger {len(record['ledger'])} rows | removed {number(record.get('removal_credit_g'))} g | "
        f"added {number(record.get('addition_mass_g'))} g | net {number(record.get('delta_mass_g'))} g | "
        f"complete cost estimate ${number(record.get('complete_cost_estimate_usd'), 2)}",
        size=15,
    )
    ledger_line = "Named ledger rows / source masses (g): " + "; ".join(
        f"{item['id']} {number(item.get('mass_g'))}"
        for item in record["ledger"]
        if any(token in item["id"] for token in ["shock", "leader", "wrap", "notch", "lip"])
    )
    svg.lines(48, 1122, [ledger_line], size=14, gap=20, width=190)
    svg.text(
        48,
        1150,
        "Main: LOC 3/8 in ×12 ft sewn nylon55 g / $20 ESTIMATE; old18 g was unselected. Exact stock / finished mass unconfirmed.",
        size=14,
        color=AMBER,
    )
    svg.text(
        48,
        1172,
        "Unknown capacities stay unavailable. Required severe load, 1.5 m baseline, separate 15.5 planning and full50 g stay explicit.",
        size=15,
        color=AMBER,
    )
    svg.footer(metadata, 1212)
    return svg


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--spec", type=Path, default=Path("configs/vehicle/candidates/g80-f2-rp1-wrap.yaml")
    )
    parser.add_argument(
        "--record",
        type=Path,
        default=Path("runs/wo03-f2-recovery-precedent-20261103-v1/record.json"),
    )
    parser.add_argument("--output", type=Path, default=Path("output/f2-recovery-precedents"))
    args = parser.parse_args()
    spec_path, record_path = ROOT / args.spec, ROOT / args.record
    for path in (spec_path, record_path):
        if not path.is_file():
            raise SystemExit(f"Required source missing; no drawing exported: {path}")
    spec = yaml.safe_load(spec_path.read_text())
    record = json.loads(record_path.read_text())
    if (
        record.get("identity") != "G80-F2-RP1-wrap-recommendation-v1"
        or record.get("adopted") is not False
    ):
        raise SystemExit("Expected exact unadopted RP1 record identity")
    if not record.get("cases") or not record.get("ledger"):
        raise SystemExit("Recorded cases/ledger unavailable; no result labels fabricated")
    sources = record.get("sources", {})
    if str(args.spec) not in sources:
        raise SystemExit("Record does not source-pin the RP1 raw specification")
    for rel, expected in sources.items():
        digest = expected.get("sha256") if isinstance(expected, dict) else expected
        path = ROOT / rel
        if not path.is_file() or sha(path) != digest:
            raise SystemExit(f"Missing or changed record source: {rel}")
    metadata = {
        "identity": record["identity"],
        "adopted": False,
        "representation": "dimensioned_concept_and_record_display",
        "specification": {"path": str(args.spec), "sha256": sha(spec_path)},
        "record": {"path": str(args.record), "sha256": sha(record_path)},
        "exporter": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "sources": sources,
        "units": {"dimensions": "mm", "mass": "g", "loads": "N"},
        "context_sources": {
            rel: sha(ROOT / rel)
            for rel in [
                "docs/wo03-f2-recovery-precedents-source-notes.md",
                "configs/studies/f2-recovery-precedents-sources.yaml",
                "docs/wo03-g80-f2-c1-decision.md",
            ]
        },
        "browser_verified": False,
        "engineering_accepted": False,
        "unknowns": [
            "knot_envelope",
            "conditioned_joint_capacity",
            "thermal_field",
            "installed_load_sharing",
        ],
    }
    drawings = {
        "connection": connection(spec, record, metadata),
        "comparison": comparison(spec, record, metadata),
    }
    out = ROOT / args.output
    out.mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name, drawing in drawings.items():
        path = out / f"{name}.svg"
        drawing.write(path, metadata)
        artifacts.append({"path": str(path.relative_to(ROOT)), "sha256": sha(path)})
    (out / "export-metadata.json").write_text(
        json.dumps({**metadata, "artifacts": artifacts}, indent=2) + "\n"
    )
    print(json.dumps({"identity": record["identity"], "artifacts": artifacts, "rendered": False}))


if __name__ == "__main__":
    main()
