"""Draw the recorded RP1 attachment definition; display only, with no CAD or solver."""

from __future__ import annotations

import argparse
import json
import math
import struct
import subprocess
import time
import zipfile
from pathlib import Path

import yaml
from wo03_recovery_precedent_drawings import (
    AMBER,
    CORD,
    GHOST,
    INK,
    MUTED,
    NEW,
    SVG,
    WOOD,
    number,
    sha,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "output/rp1-attachment-definition"
CONFIG = ROOT / "configs/studies/rp1-attachment-definition-v2.yaml"
RECORD = ROOT / "runs/wo03-rp1-attachment-definition-20261103-v2/record.json"
HELPER = ROOT / "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift"
SOURCE_HELPER = ROOT / "scripts/wo03_recovery_precedent_drawings.py"
PAPER = "#eee2d2"
BLUE = "#dce8ef"
FAIL = "#ab3a31"


def check(value: object, label: str) -> float:
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"Recorded {label} is unavailable")
    return float(value)


def note(
    svg: SVG, x: int, y: int, lines: list[str], width: int = 78, color: str = MUTED, size: int = 16
):
    return svg.lines(x, y, lines, width=width, size=size, color=color, gap=size + 8)


def node(
    svg: SVG,
    x: int,
    y: int,
    title: str,
    body: str,
    fill: str = "#ffffff",
    w: int = 250,
    h: int = 105,
):
    svg.rect(x, y, w, h, fill=fill, stroke="#8196a4", rx=7)
    svg.lines(x + 11, y + 29, [title], width=27, size=16, gap=20)
    svg.lines(x + 11, y + 66, [body], width=28, size=13, color=MUTED, gap=17)


def tag(svg: SVG, x: int, y: int, label: str, color: str = AMBER, w: int = 310):
    svg.rect(x, y, w, 32, fill="#fff0cc" if color == AMBER else "#fce9e7", stroke=color, rx=5)
    svg.text(x + 10, y + 23, label, size=14, color=color, weight="bold")


def geometry(cfg: dict, rec: dict, meta: dict) -> SVG:
    route, cord = cfg["route"], cfg["cord"]["kevlar"]
    svg = SVG(
        "RP1-AD1 local attachment and guarded route",
        "Aft from nose in mm; section is a source-linked concept, not a whole-vehicle CAD assembly",
        height=1190,
        status="TEST DEFINITION ONLY",
    )
    svg.text(48, 134, "A  LOCAL LONGITUDINAL SECTION  |  z980–1220 mm", size=20, weight="bold")
    svg.text(
        48,
        161,
        "Schematic radial spacing. Stations and sizes below are from the declared RP1-AD1 source.",
        size=15,
        color=MUTED,
    )
    x = lambda z: 90 + (z - 980) * 6.0
    svg.line(x(980), 302, x(1220), 302, color=GHOST, width=1, dash="7 5")
    svg.rect(x(980), 217, x(1220) - x(980), 170, fill=PAPER)
    svg.rect(
        x(route["motor_tube_mm"][0]),
        263,
        x(route["motor_tube_mm"][1]) - x(route["motor_tube_mm"][0]),
        78,
        fill=BLUE,
    )
    sz0, sz1 = route["heat_abrasion_sleeve"]["axial_station_mm"]
    svg.rect(x(sz0), 252, x(sz1) - x(sz0), 12, fill=CORD, stroke=CORD)
    svg.rect(
        x(route["forward_ring_mm"][0]),
        224,
        x(route["forward_ring_mm"][1]) - x(route["forward_ring_mm"][0]),
        156,
        fill=WOOD,
    )
    svg.rect(x(cfg["fin_joints"]["aft_ring_front_mm"]), 224, 6 * 6, 156, fill=WOOD)
    svg.rect(
        x(route["wrap_axial_mm"][0]),
        259,
        max(8, x(route["wrap_axial_mm"][1]) - x(route["wrap_axial_mm"][0])),
        10,
        fill=CORD,
        stroke=CORD,
    )
    kz0, kz1 = cord["knot_axial_bounds_mm"]
    svg.rect(x(kz0), 224, x(kz1) - x(kz0), 34, fill="none", stroke=FAIL, stroke_dasharray="6 4")
    svg.text(x(kz0) + 7, 247, "UNVERIFIED KNOT BOX", size=14, color=FAIL, weight="bold")
    svg.add(
        "polygon",
        points=f"{x(1080.2)},386 {x(1189.6)},386 {x(1189.6)},444 {x(1080.2)},418",
        fill="#a9d4cb",
        stroke=NEW,
    )
    svg.text(x(1090), 415, "one representative tab/root", size=14, color=INK)
    svg.text(x(1005), 249, "paper body", size=16)
    svg.text(x(986), 281, "80 mm sleeve ends at ring", size=14, color=CORD, weight="bold")
    svg.text(x(1120), 292, "motor tube; no live-motor geometry inferred", size=15)
    svg.dim(x(980), x(1220), 473, "240 mm local segment")
    svg.dim(
        x(route["forward_ring_mm"][0]), x(route["forward_ring_mm"][1]), 515, "moved ring 12.2 mm"
    )
    svg.text(
        48,
        554,
        f"Wrap z {route['wrap_axial_mm'][0]}–{route['wrap_axial_mm'][1]} mm; motor tube OD {route['tube_od_mm']} mm",
        size=16,
    )
    svg.text(
        48,
        583,
        f"Forward ring z {route['forward_ring_mm'][0]}–{route['forward_ring_mm'][1]} mm; aft ring begins z {cfg['fin_joints']['aft_ring_front_mm']} mm",
        size=16,
    )
    svg.text(
        48,
        615,
        f"Knot reservation {cord['knot_reservation_mm']} mm at z {kz0}–{kz1}; R {cord['knot_radial_bounds_mm']} mm is a BOX, not a checked knot.",
        size=16,
        color=FAIL,
    )
    svg.text(
        48,
        637,
        f"Sleeve z {sz0}–{sz1} mm stays ahead of ring; bare rounded passage, cord and sleeve end have NO thermal/chafe capacity credit.",
        size=15,
        color=FAIL,
    )
    svg.text(48, 684, "B  MOTOR-END SYMBOL AND ACCESSIBLE FORWARD JUNCTION", size=20, weight="bold")
    cx, cy = 235, 850
    for radius, color in [(126, INK), (87, WOOD), (51, BLUE)]:
        svg.add("circle", cx=cx, cy=cy, r=radius, fill="none", stroke=color, stroke_width=4)
    a = math.radians(route["passage_angle_deg"])
    ex, ey = cx + 126 * math.cos(a), cy - 126 * math.sin(a)
    svg.arrow([(cx + 72 * math.cos(a), cy - 72 * math.sin(a)), (ex, ey)], color=CORD, width=5)
    svg.text(
        385,
        763,
        f"60° passage: {route['passage_width_mm']} mm width × {route['passage_depth_mm']} mm depth",
        size=17,
    )
    svg.text(
        385,
        794,
        f"Edge roundover {route['passage_edge_roundover_mm']} mm; minimum per-flank {number(rec['cord_geometry']['notch_min_per_flank_mm'])} mm, conditional",
        size=16,
    )
    svg.text(
        385,
        824,
        "Bare cord crosses passage. Bend radius and conditioned chafe/heat capacity unavailable.",
        size=16,
        color=FAIL,
    )
    svg.arrow([(440, 875), (735, 875), (970, 875)], color=CORD, width=4)
    node(svg, 975, 835, "Sleeve before ring", "z980–1060 mm; no credited heat capacity", w=280)
    svg.arrow([(1260, 875), (1370, 875)], color=CORD, width=4)
    node(svg, 1380, 835, "Outside mouth", "Loop-to-loop accessible junction", w=260)
    note(
        svg,
        385,
        972,
        [
            f"Available external reach {number(rec['cord_geometry']['available_external_reach_mm'])} mm against proposed minimum {route['minimum_external_junction_reach_mm']} mm; this is geometry only.",
            f"Factory LOC nylon loops remain uncut. Kevlar raw cut {number(cord['installed_raw_cut_m'] * 1000, 1)} mm; exact finished bearing length unavailable.",
            "Finite connector, packing, chafe, hot cord and installed load capacity remain unverified.",
        ],
        width=125,
    )
    svg.footer(meta, 1115)
    return svg


def paths(cfg: dict, rec: dict, meta: dict) -> SVG:
    fin = rec["fin"]
    recovery = rec["recovery_connections"]
    svg = SVG(
        "RP1-AD1 load paths and joint evidence",
        "Arrows show intended transfer only; source scalars are not spatial stress or accepted sharing",
        height=1310,
        status="FAIL / UNQUALIFIED",
    )
    rows = [
        (
            "FIN BENDING / TORQUE",
            [
                ("Plywood panel", "5.8 mm minimum source ply"),
                ("Through-body tab", "109.4 mm length; no front-ring support"),
                ("Motor-tube fillets", "continuous six-sided proposal"),
                ("Gusset + saddle", "finite body/root bonds"),
                ("Paper body", "peel / ovalization unknown"),
            ],
            NEW,
        ),
        (
            "RECOVERY BODY BRANCH",
            [
                ("Factory nylon loop", "uncut; finished strength unknown"),
                ("Outside junction", "loop-to-loop, accessible"),
                ("Kevlar + guard", "wrap/choker at motor tube"),
                ("Tube and ring bonds", "finite contact; no fixed ground"),
                ("Retained body", "paper/bond/peel unresolved"),
            ],
            CORD,
        ),
        (
            "AFT FIN / END TRANSFER",
            [
                ("Fin root/tab", "109.4 mm; inner flat R15.95"),
                ("Aft-end adhesive", "no direct tab butt contact"),
                ("Aft ring", "z1190–1196 mm"),
                ("Body bond", "finite; local peel unknown"),
                ("Airframe", "installed stiffness unknown"),
            ],
            WOOD,
        ),
    ]
    for ri, (heading, entries, color) in enumerate(rows):
        y = 150 + ri * 254
        svg.text(48, y, f"{chr(65 + ri)}  {heading}", size=19, weight="bold")
        if ri == 0:
            # Parallel physical routes, not tube fillets feeding an external wedge.
            node(svg, 52, 208, "Plywood panel", "5.8 mm minimum ply", w=264, h=70)
            node(svg, 379, 208, "Integral root / tab", "Two paths; split unknown", w=264, h=70)
            node(svg, 706, 170, "Tab / tube fillets", "Finite bond and tube", w=264, h=65)
            node(svg, 706, 258, "External root wedges", "Fin-face bonds", w=264, h=65)
            node(svg, 1033, 170, "Tube / ring joints", "Bending, shear, peel open", w=264, h=65)
            node(svg, 1033, 258, "Curved saddle bonds", "Normal / peel unknown", w=264, h=65)
            node(svg, 1360, 208, "Paper body", "Flexible / ovalization open", w=264, h=70)
            svg.arrow([(320, 243), (370, 243)], color=NEW, width=4)
            svg.arrow([(647, 243), (674, 243), (674, 202), (697, 202)], color=NEW, width=3)
            svg.arrow([(674, 243), (674, 290), (697, 290)], color=NEW, width=3)
            for yy in [202, 290]:
                svg.arrow([(974, yy), (1024, yy)], color=NEW, width=3)
                svg.arrow([(1301, yy), (1325, yy), (1325, 243), (1351, 243)], color=NEW, width=3)
            svg.text(
                53,
                353,
                "Parallel routes shown; no equal sharing or rigid ground. Aft-end path is detailed in C.",
                size=16,
                color=FAIL,
            )
            continue
        for i, (title, body) in enumerate(entries):
            x = 52 + i * 327
            node(
                svg, x, y + 28, title, body, fill="#eaf1f4" if ri == 0 else "#fff8ed", w=264, h=119
            )
            if i < 4:
                svg.arrow([(x + 268, y + 88), (x + 315, y + 88)], color=color, width=4)
        if ri == 0:
            svg.text(
                53,
                y + 179,
                "Front ring is NOT a tab support. Aft-end adhesive has no proven contact/normal capacity.",
                size=16,
                color=FAIL,
            )
        elif ri == 1:
            svg.text(
                53,
                y + 179,
                "Full route is one coupled chain; no equal sharing, fixed support or finished sewn/loop rating is credited.",
                size=16,
                color=FAIL,
            )
        else:
            svg.text(
                53,
                y + 179,
                "Ideal panel/strip scalars do not measure installed root rotation or flutter.",
                size=16,
                color=FAIL,
            )
    svg.rect(48, 916, 1604, 253, fill="#fff4e9", stroke="#dbaca0", rx=8)
    svg.text(68, 952, "D  RECORDED SCREEN AND MISSING CAPACITY", size=19, color=FAIL, weight="bold")
    ideal = fin["ideal_composite_strip_lower_deflection_only"][-1]
    svg.text(
        68,
        991,
        f"Best-case strip panel: {number(ideal['maximum_bending_Pa'] / 1e6)} MPa and {number(ideal['deflection_m'] * 1000)} mm → FAIL preliminary panel screen.",
        size=20,
        color=FAIL,
        weight="bold",
    )
    svg.text(
        68,
        1022,
        f"Source hot wood estimate {number(cfg['fin_joints']['hot_wood_strength_Pa'] / 1e6)} MPa; minimum ply {cfg['fin_joints']['panel_minimum_thickness_mm']} mm. This is a scalar strip, not a stress map.",
        size=16,
    )
    svg.text(
        68,
        1053,
        f"Adverse recovery body proxy {number(recovery['adverse_body_proxy_N'])} N; inner-ring mean if full force {number(recovery['inner_ring_mean_shear_if_full_force_Pa'] / 1e6)} MPa.",
        size=16,
    )
    svg.text(
        68,
        1084,
        "Root normal/peel, annular bending, rope pressure, asymmetric load and conditioned joint capacities unavailable.",
        size=16,
        color=FAIL,
    )
    svg.text(
        68,
        1115,
        "No installed movement, flutter or thermal conclusion follows from these source scalars.",
        size=16,
        color=AMBER,
    )
    svg.footer(meta, 1210)
    return svg


def article(cfg: dict, rec: dict, meta: dict) -> SVG:
    test = cfg["test_article"]
    z0, z1 = test["vehicle_station_range_mm"]
    svg = SVG(
        "RP1-AD1 sacrificial attachment test article",
        "Representative 240 mm station segment and proposed fixture sequence; no live motor or released test",
        height=1230,
        status="OWNER TEST HOLD",
    )
    svg.text(48, 136, "A  DIMENSIONED VEHICLE-STATION ARTICLE", size=20, weight="bold")
    x = lambda z: 105 + (z - z0) * 5.55
    svg.line(x(z0), 292, x(z1), 292, color=GHOST, width=1, dash="7 5")
    svg.rect(x(z0), 222, x(z1) - x(z0), 140, fill=PAPER)
    svg.rect(
        x(z0),
        218,
        x(z0 + test["fore_body_grip_engagement_mm"]) - x(z0),
        148,
        fill="#ced7db",
        stroke=GHOST,
        stroke_dasharray="7 4",
    )
    sz0, sz1 = cfg["route"]["heat_abrasion_sleeve"]["axial_station_mm"]
    svg.rect(x(sz0), 256, x(sz1) - x(sz0), 9, fill=CORD, stroke=CORD)
    svg.rect(
        x(cfg["route"]["motor_tube_mm"][0]),
        268,
        x(z1) - x(cfg["route"]["motor_tube_mm"][0]),
        48,
        fill=BLUE,
    )
    svg.rect(
        x(cfg["route"]["forward_ring_mm"][0]),
        226,
        x(cfg["route"]["forward_ring_mm"][1]) - x(cfg["route"]["forward_ring_mm"][0]),
        132,
        fill=WOOD,
    )
    svg.rect(x(cfg["fin_joints"]["aft_ring_front_mm"]), 226, 6 * 5.55, 132, fill=WOOD)
    svg.text(x(z0) + 12, 245, "proposed compliant fore grip", size=14)
    svg.text(x(1090), 300, "EMPTY motor tube", size=17, weight="bold")
    svg.dim(x(z0), x(z1), 405, f"{z0}–{z1} mm vehicle station; {test['body_length_mm']} mm article")
    svg.dim(
        x(z0),
        x(z0 + test["fore_body_grip_engagement_mm"]),
        447,
        f"{test['fore_body_grip_engagement_mm']} mm fore grip",
    )
    tag(svg, 1185, 136, "NO LIVE MOTOR", color=FAIL, w=340)
    svg.text(
        48,
        489,
        "Grip is a proposed split saddle with compliant liner. Measure slip, ovalization and reaction distribution; do not model it as fixed.",
        size=16,
        color=FAIL,
    )
    svg.text(48, 528, "B  ASSEMBLY AND INSPECTION SEQUENCE", size=20, weight="bold")
    steps = [
        (
            "01  Stock and cuts",
            "Same identified body/mount stock; minimum ply; inspect ring/slot, roundover and conditioned adhesive batch.",
        ),
        (
            "02  Fin / ring joints",
            "Build representative tabs, fillets, gussets and aft adhesive; inspect actual coverage and gaps.",
        ),
        (
            "03  Recovery route",
            "Reeve source Kevlar; preserve factory nylon loops; mark knot tails, guard and accessible junction.",
        ),
        (
            "04  Fit the fixture",
            "Engage 60 mm proposed fore grip; verify no tube crush/slip and document load/reaction path.",
        ),
        (
            "05  Owner test hold",
            "Review grips, guards, calibration, hot setup and loading protocol before any physical loading.",
        ),
    ]
    for i, (title, body) in enumerate(steps):
        y = 565 + i * 97
        svg.rect(52, y, 1596, 79, fill="#ffffff", stroke="#b8c8d1", rx=6)
        svg.text(68, y + 28, title, size=17, weight="bold", color=NEW if i < 4 else FAIL)
        svg.lines(390, y + 28, [body], width=129, size=15, color=INK, gap=20)
    svg.text(
        48,
        1081,
        f"Proposed load-system range ≥ {number(test['minimum_load_system_range_N'], 0)} N. No owner hardware, test date, fixture qualification or physical result is recorded.",
        size=16,
        color=FAIL,
    )
    svg.footer(meta, 1140)
    return svg


def comparison(cfg: dict, rec: dict, meta: dict) -> SVG:
    svg = SVG(
        "RP1-AD1 coupled mass and guide comparison",
        "Four saved cases; 55 g nylon budget and 68 g commerce-metadata probe are not measured stock bounds",
        height=1070,
        status="PLANNING OPEN",
    )
    svg.text(
        48,
        137,
        "A  COMPLETE RECORDED CASES  |  full separate 50 g included",
        size=20,
        weight="bold",
    )
    headers = [
        (52, "Case"),
        (390, "Mass g"),
        (570, "CG mm"),
        (730, "Static cal"),
        (900, "1.5 m m/s"),
        (1100, "Formal headroom g"),
        (1360, "Planning headroom g"),
    ]
    for x, label in headers:
        svg.text(x, 191, label, size=16, weight="bold")
    svg.line(48, 206, 1650, 206, color="#91a4b1", width=1)
    for i, case in enumerate(rec["cases"]):
        y = 237 + i * 124
        svg.rect(
            48,
            y - 29,
            1604,
            106,
            fill="#ffffff" if i % 2 == 0 else "#edf3f6",
            stroke="#d3dee4",
            rx=5,
        )
        name = f"{case['case']} / nylon {number(case['nylon_mass_probe_g'], 0)} g"
        svg.text(54, y + 5, name, size=16, weight="bold")
        svg.text(
            54,
            y + 33,
            "metadata sensitivity" if case["nylon_mass_probe_g"] != 55 else "source allocation",
            size=13,
            color=AMBER,
        )
        svg.text(390, y + 5, number(case["total_mass_g"]), size=16)
        svg.text(570, y + 5, number(case["cg_mm"]), size=16)
        svg.text(730, y + 5, number(case["margin_cal"]), size=16)
        svg.text(
            900,
            y + 5,
            number(case["guide_mps"]["1.5"], 4),
            size=16,
            color=FAIL if case["formal_speed_margin_mps"] < 0 else NEW,
        )
        svg.text(
            1100,
            y + 5,
            number(case["formal_mass_headroom_g"]),
            size=16,
            color=FAIL if case["formal_mass_headroom_g"] < 0 else NEW,
        )
        svg.text(1360, y + 5, number(case["planning_mass_headroom_g"]), size=16, color=FAIL)
        svg.text(
            390,
            y + 34,
            f"1.8 m conditional {number(case['guide_mps']['1.8'], 4)} m/s  |  adverse +20 g and motor-CG probe only where marked",
            size=14,
            color=MUTED,
        )
    svg.rect(48, 754, 1604, 175, fill="#fff3e4", stroke="#d9b980", rx=7)
    svg.text(68, 788, "B  INTERPRETATION BOUNDARIES", size=19, weight="bold", color=AMBER)
    svg.text(
        68,
        821,
        f"Net addition to frozen balanced RP1: {number(rec['net_addition_to_balanced_g'])} g; physical inertia unavailable; full flight not run.",
        size=16,
    )
    svg.text(
        68,
        851,
        "Formal 15 m/s and separate planning 15.5 m/s at 1.5 m usable guide; longer usable travel is conditional equipment.",
        size=16,
    )
    svg.text(
        68,
        881,
        "The 68 g commerce metadata has no reliable unit/scope and is a sensitivity probe, not a mass bound.",
        size=16,
        color=FAIL,
    )
    svg.footer(meta, 970)
    return svg


def png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()[:24]
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", data[16:24])


def package(out: Path):
    archive = out / "drawing-pack.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in ["index.html", "README.md", "manifest.json"]:
            zipped.write(out / name, arcname=name)
        for path in sorted(out.glob("*.svg")) + sorted(out.glob("*.png")):
            zipped.write(path, arcname=path.name)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package-only", action="store_true", help="Rezip inspected artifacts without rendering"
    )
    args = parser.parse_args()
    out = DEFAULT_OUT
    out.mkdir(parents=True, exist_ok=True)
    if args.package_only:
        archive = package(out)
        print(json.dumps({"zip": str(archive.relative_to(ROOT)), "sha256": sha(archive)}))
        return
    cfg = yaml.safe_load(CONFIG.read_text())
    rec = json.loads(RECORD.read_text())
    if cfg.get("id") != rec.get("identity") or rec.get("adopted") is not False:
        raise SystemExit("RP1 attachment source identity mismatch")
    for rel, expected in rec["sources"].items():
        path = ROOT / rel
        if not path.is_file() or sha(path) != expected:
            raise SystemExit(f"Missing or changed pinned source: {rel}")
    if sha(ROOT / cfg["source"]) != cfg["source_sha256"]:
        raise SystemExit("Balanced source identity changed")
    meta = {
        "identity": rec["identity"],
        "adopted": False,
        "status": rec["decision"],
        "representation": "local_concept_and_recorded_scalars_not_whole_CAD",
        "specification": {"path": str(CONFIG.relative_to(ROOT)), "sha256": sha(CONFIG)},
        "record": {"path": str(RECORD.relative_to(ROOT)), "sha256": sha(RECORD)},
        "exporter": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "helper": {"path": str(SOURCE_HELPER.relative_to(ROOT)), "sha256": sha(SOURCE_HELPER)},
        "native_renderer": {"path": str(HELPER.relative_to(ROOT)), "sha256": sha(HELPER)},
        "sources": rec["sources"],
        "units": {"length": "mm", "mass": "g", "force": "N", "stress": "MPa"},
        "browser_verified": False,
        "engineering_accepted": False,
    }
    drawings = {
        "01-local-attachment": geometry(cfg, rec, meta),
        "02-load-paths": paths(cfg, rec, meta),
        "03-test-article": article(cfg, rec, meta),
        "04-coupled-cases": comparison(cfg, rec, meta),
    }
    started = time.monotonic()
    (out / "swift-module-cache").mkdir(parents=True, exist_ok=True)
    artifacts = []
    for name, drawing in drawings.items():
        svg_path, png_path = out / f"{name}.svg", out / f"{name}.png"
        drawing.write(svg_path, meta)
        remaining = 120 - (time.monotonic() - started)
        if remaining <= 1:
            raise SystemExit("Native render batch exceeded 120 seconds")
        subprocess.run(
            [
                "/usr/bin/swift",
                "-module-cache-path",
                str(out / "swift-module-cache"),
                str(HELPER),
                str(svg_path),
                str(png_path),
            ],
            check=True,
            timeout=remaining,
            capture_output=True,
            text=True,
        )
        artifacts.append(
            {
                "id": name,
                "svg": {"path": str(svg_path.relative_to(ROOT)), "sha256": sha(svg_path)},
                "png": {
                    "path": str(png_path.relative_to(ROOT)),
                    "sha256": sha(png_path),
                    "pixels": png_size(png_path),
                },
            }
        )
    elapsed = time.monotonic() - started
    if elapsed > 120:
        raise SystemExit("Native render batch exceeded 120 seconds")
    manifest = {
        **meta,
        "artifacts": artifacts,
        "native_render_seconds": elapsed,
        "native_render_limit_seconds": 120,
        "visual_inspection": [],
        "limits": [
            "AppKit native SVG snapshot, not browser evidence",
            "No CAD, continuum solver, paid run or physical test was executed",
        ],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cards = "".join(
        f'<article><h2>{item["id"].replace("-", " ").title()}</h2><a href="{item["id"]}.png"><img src="{item["id"]}.png" alt="Offline {item["id"]} drawing"></a><p><a href="{item["id"]}.svg">SVG</a> · <a href="{item["id"]}.png">PNG</a></p></article>'
        for item in artifacts
    )
    (out / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>RP1 attachment definition</title>'
        "<style>body{font:16px/1.5 system-ui;background:#e9eff3;color:#15334a;max-width:1500px;margin:auto;padding:28px}img{width:100%;height:auto;border:1px solid #8aa1af}article{background:white;padding:20px;margin:22px 0}a{color:#087f78}</style>"
        "<h1>RP1 attachment definition · offline drawings</h1><p>Recorded local concept and test definition only. No whole-vehicle CAD, browser, installed joint or flight acceptance.</p>"
        '<p><a href="README.md">Review notes</a> · <a href="manifest.json">Source manifest</a> · <a href="drawing-pack.zip">ZIP</a></p>'
        + cards
        + "</html>\n"
    )
    (out / "README.md").write_text(
        "# RP1 attachment definition offline drawings\n\n"
        f"Identity: `{rec['identity']}`. Source config SHA-256 `{sha(CONFIG)}`; executed record SHA-256 `{sha(RECORD)}`.\n\n"
        "Four source-linked SVGs and native AppKit PNGs were generated. Visual inspection is pending; see manifest.\n\n"
        "These are local concept/test diagrams, not whole-vehicle CAD or browser evidence. No installed joint, thermal, flutter, recovery or flight acceptance follows.\n"
    )
    archive = package(out)
    print(
        json.dumps(
            {
                "identity": rec["identity"],
                "artifacts": len(artifacts),
                "native_seconds": elapsed,
                "manifest": str((out / "manifest.json").relative_to(ROOT)),
                "zip_sha256": sha(archive),
            }
        )
    )


if __name__ == "__main__":
    main()
