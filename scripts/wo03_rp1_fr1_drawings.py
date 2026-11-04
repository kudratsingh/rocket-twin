"""Draw the recorded FR1 fin-root preflight without new engineering analysis."""

from __future__ import annotations

import argparse
import csv
import html
import json
import struct
import subprocess
import time
import zipfile
from pathlib import Path

import yaml
from wo03_recovery_precedent_drawings import (
    AMBER,
    CORD,
    INK,
    MUTED,
    NEW,
    SVG,
    WOOD,
    number,
    sha,
)

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/rp1-fin-root-replacement.yaml"
CANDIDATE = ROOT / "configs/vehicle/candidates/g80-rp1-fr1.yaml"
RECORD = ROOT / "runs/wo03-rp1-fin-root-20261104-v1/record.json"
SUPPLEMENT = ROOT / "runs/wo03-rp1-fin-root-20261104-v1/joint-supplement.json"
HELPER = ROOT / "runs/wo04-offline-render-feasibility-20261102-v4/native_image_document.swift"
SVG_HELPER = ROOT / "scripts/wo03_recovery_precedent_drawings.py"
OUTPUT = ROOT / "output/rp1-fin-root-fr1"
CARBON = "#333d48"
PAPER = "#ede1d2"
MOUNT = "#dce8ef"
FAIL = "#ad382e"


def box(svg: SVG, x: int, y: int, w: int, h: int, title: str, body: str, fill: str = "#ffffff"):
    svg.rect(x, y, w, h, fill=fill, stroke="#a9bac5", rx=7)
    svg.lines(x + 12, y + 29, [title], size=16, width=31, gap=20)
    svg.lines(x + 12, y + 65, [body], size=14, width=33, gap=19, color=MUTED)


def fin_and_paths(cfg: dict, rec: dict, supplement: dict, meta: dict) -> SVG:
    c = cfg["construction"]
    recovery = cfg["recovery_and_service"]
    g = rec["geometry"]
    svg = SVG(
        "FR1 monolithic fin, local interfaces and parallel paths",
        "Sourced dimensions in mm; single-fin schematic, not a whole-vehicle CAD or spatial stress result",
        height=1370,
        status="STOPPED PREFLIGHT",
    )
    svg.text(48, 139, "A  ONE ROCK WEST 204-11 FIN AND INTEGRAL TAB", size=20, weight="bold")
    svg.text(
        48,
        168,
        "Planform shown in its own local coordinates; outboard fin and tab are one proposed carbon part.",
        size=15,
        color=MUTED,
    )
    root, tip, span, sweep = (c["planform_mm"][key] for key in ("root", "tip", "span", "sweep"))
    x0, yroot, scale = 105, 510, 4.35
    pts = [
        (x0, yroot),
        (x0 + root * scale, yroot),
        (x0 + (sweep + tip) * scale, yroot - span * scale),
        (x0 + sweep * scale, yroot - span * scale),
    ]
    svg.add(
        "polygon",
        points=" ".join(f"{x},{y}" for x, y in pts),
        fill="#b6c2c7",
        stroke=CARBON,
        stroke_width=3,
    )
    tab = c["integral_tab_mm"]
    tab0 = x0 + (tab["start"] - c["root_station_mm"]) * scale
    tab1 = x0 + (tab["end"] - c["root_station_mm"]) * scale
    svg.rect(tab0, yroot, tab1 - tab0, tab["depth"] * scale, fill=CARBON, stroke=CARBON)
    svg.dim(x0, x0 + root * scale, 665, f"root {root} mm")
    svg.dim(x0 + sweep * scale, x0 + (sweep + tip) * scale, 222, f"tip {tip} mm")
    svg.dim(tab0, tab1, 615, f"integral tab {number(tab['end'] - tab['start'], 1)} mm")
    svg.line(78, yroot, 78, yroot - span * scale, color=MUTED, width=1)
    svg.text(64, 380, f"span {span} mm", size=14, color=MUTED)
    svg.text(292, 332, f"leading sweep {sweep} mm", size=15)
    svg.text(
        168,
        554,
        f"tab depth {number(tab['depth'])} mm; inner flat R{number(tab['inner_flat_radius'], 2)}",
        size=15,
        color="#ffffff",
    )
    svg.text(
        48,
        705,
        f"204-11 nominal {number(cfg['stock']['nominal_thickness_mm'])} mm; source min/max {number(cfg['stock']['minimum_thickness_mm'])}/{number(cfg['stock']['maximum_thickness_mm'])} mm.",
        size=16,
    )
    svg.text(
        48,
        733,
        f"Three fins; body slot {number(c['body_slot_width_mm'])} mm; conditional minimum per-flank {number(g['slot_minimum_per_flank_mm'], 4)} mm.",
        size=16,
    )
    svg.text(
        48,
        762,
        f"Continuous tab/mount and body/root fillets: nominal leg {number(c['fillet_leg_nominal_mm'], 0)} mm, min {number(c['fillet_leg_minimum_mm'])} mm. No wood wedges.",
        size=16,
        color=FAIL,
    )

    svg.text(858, 139, "B  STATIONED RING / WRAP / KNOT REGION", size=20, weight="bold")
    svg.text(
        858,
        168,
        "Radial spacing schematic; station labels are sourced, knot shape is a reservation only.",
        size=15,
        color=MUTED,
    )
    xp = lambda z: 870 + (z - 1050) * 4.55
    svg.rect(xp(1050), 270, xp(1220) - xp(1050), 170, fill=PAPER)
    svg.rect(xp(1055), 315, xp(1220) - xp(1055), 76, fill=MOUNT)
    svg.rect(xp(1060), 276, xp(1072.2) - xp(1060), 158, fill=WOOD)
    svg.rect(xp(1190), 276, xp(1196) - xp(1190), 158, fill=WOOD)
    svg.rect(xp(1072.2), 307, xp(1077) - xp(1072.2), 8, fill=CORD, stroke=CORD)
    svg.rect(xp(1080.2), 439, xp(1189.6) - xp(1080.2), 44, fill=CARBON, stroke=CARBON)
    svg.rect(
        xp(1077), 275, xp(1127) - xp(1077), 39, fill="none", stroke=FAIL, stroke_dasharray="7 5"
    )
    svg.text(xp(1080), 299, "KNOT BOX, not shape", size=12, color=FAIL)
    svg.text(886, 250, "forward ring z1060–1072.2", size=14, color=WOOD)
    svg.text(1440, 250, "aft ring z1190–1196", size=14, color=WOOD)
    svg.text(
        1060, 510, "tab z1080.2–1189.6; no front-ring contact or direct aft butt stop", size=15
    )
    svg.text(
        858,
        546,
        f"Knot box z{recovery['knot_station_mm'][0]}–{recovery['knot_station_mm'][1]}, R{recovery['knot_radial_mm'][0]}–{recovery['knot_radial_mm'][1]} at 60°.",
        size=15,
    )
    svg.text(
        858,
        574,
        f"Projected knot/fillet gap {number(g['knot_box_vs_fillet_min_projection_mm'])} mm; actual knot/packing and CAD motion unverified.",
        size=15,
        color=FAIL,
    )
    svg.text(
        858,
        602,
        f"Recovery wrap/tab station clearance {number(g['recovery_wrap_to_tab_clearance_mm'])} mm; sleeve stays z980–1060.",
        size=15,
    )
    svg.text(
        858,
        630,
        "Bare rounded notch, thermal/chafe, motor service and installed contacts remain open.",
        size=15,
        color=FAIL,
    )

    svg.text(48, 817, "C  PARALLEL PROPOSED FIN-ROOT SUPPORTS", size=20, weight="bold")
    box(
        svg,
        52,
        857,
        300,
        118,
        "Outboard carbon panel",
        "Retained 8.83 N m envelope; single fin load",
        "#eaf0f2",
    )
    svg.arrow([(355, 916), (442, 916)], color=NEW, width=4)
    box(svg, 445, 857, 260, 118, "Integral root/tab", "Finite joint and root compliance", "#eaf0f2")
    svg.line(708, 916, 770, 916, color=NEW, width=4)
    svg.line(770, 890, 770, 1160, color=NEW, width=4)
    for y, title, body, fill in [
        (832, "Motor-tube fillets", "Tab/mount shear and tube/ring transfer", MOUNT),
        (
            967,
            "Body/root fillets",
            f"130 mm contact; one face {number(supplement['body_one_face_area_mm2'])} mm²; peel unknown",
            PAPER,
        ),
        (
            1102,
            "Aft tab-end adhesive",
            f"Filled gap; {number(supplement['aft_tab_end']['area_mm2'])} mm²; stiffness unknown",
            "#fff1df",
        ),
    ]:
        svg.arrow([(770, y + 58), (839, y + 58)], color=NEW, width=4)
        box(svg, 843, y, 346, 118, title, body, fill)
        svg.arrow([(1190, y + 58), (1297, y + 58)], color=NEW, width=4)
    svg.line(1300, 890, 1300, 1160, color=NEW, width=4)
    svg.arrow([(1300, 1022), (1317, 1022)], color=NEW, width=4)
    box(
        svg,
        1320,
        963,
        325,
        118,
        "Body + motor structure",
        "Finite ring/body/mount support; sharing unproven",
        "#f0f4f6",
    )
    svg.text(
        48,
        1253,
        "Parallel arrows indicate proposed routes only. No equal sharing, fixed ground, root peel or finished bond strength is established.",
        size=16,
        color=FAIL,
    )
    svg.footer(meta, 1285)
    return svg


def support_and_load(cfg: dict, rec: dict, supplement: dict, meta: dict) -> SVG:
    trace = rec["load_trace"]
    s = rec["structural_sensitivity"]
    joint = rec["joint_demand"]
    svg = SVG(
        "FR1 retained load, finite support and stopped screen",
        "Recorded scalar screens only; support springs are sensitivities, not measured installed stiffness",
        height=1240,
        status="FAIL / UNQUALIFIED",
    )
    svg.text(48, 139, "A  WHICH LOAD IS ACTUALLY RETAINED?", size=20, weight="bold")
    box(
        svg,
        52,
        178,
        740,
        141,
        "Retained legacy envelope",
        f"{number(trace['retained_M_Nm'], 2)} N m, {number(trace['retained_F_N'])} N; design factor 3 already applied",
        "#eaf1f4",
    )
    box(
        svg,
        858,
        178,
        790,
        141,
        "Direct current-planform definition",
        f"40 kPa / 5° / DF3 gives {number(trace['direct_40kPa_5deg_DF3_M_Nm'], 6)} N m; revision NOT adopted",
        "#fff2e2",
    )
    svg.text(
        52,
        353,
        "8.83 N m came from a legacy 90 mm planform rescaled onto this 60 mm fin; do not substitute the smaller direct case.",
        size=16,
        color=FAIL,
    )
    svg.text(48, 409, "B  FINITE SUPPORT MODEL — NOT A FIXED WALL", size=20, weight="bold")
    box(
        svg,
        56,
        460,
        330,
        127,
        "Panel + integral tab",
        "Short tab beam; outboard tapered panel integrated separately",
        "#eaf1f4",
    )
    svg.arrow([(390, 525), (471, 525)], color=NEW, width=4)
    box(
        svg,
        476,
        460,
        333,
        127,
        "Root translation / rotation",
        "Shared motion from body, mount and estimated tube torsion",
        "#eaf1f4",
    )
    svg.line(814, 525, 850, 525, color=NEW, width=4)
    svg.arrow([(850, 525), (895, 525)], color=NEW, width=4)
    svg.arrow([(850, 525), (850, 614), (1450, 614), (1450, 591)], color=NEW, width=4)
    box(
        svg,
        900,
        460,
        348,
        127,
        "Finite body spring Kb",
        "100 kN/m to 100 MN/m exploratory inputs",
        PAPER,
    )
    box(
        svg,
        1270,
        460,
        360,
        127,
        "Finite mount spring Km",
        "1 to 10 MN/m; ring ends not fixed ground",
        MOUNT,
    )
    svg.text(
        52,
        660,
        f"Estimated mount rotation stiffness {number(rec['mount_rotation_bound']['Kr_Nm_rad'])} N m/rad assumes rigid ring-end rotations; actual compliance lowers it.",
        size=16,
    )
    svg.text(48, 695, "C  TOTAL TIP MOVEMENT AT RETAINED 8.83 N m", size=20, weight="bold")
    svg.rect(48, 730, 1604, 214, fill="#ffffff", stroke="#afc1ca", rx=7)
    # Bar lengths are display scales for saved results, not a new physics result.
    bar_x, bar_w = 475, 910
    limit_x = bar_x + bar_w * 1 / 1.5
    svg.line(limit_x, 757, limit_x, 900, color=FAIL, width=2, dash="7 5")
    svg.text(limit_x + 8, 771, "1.000 mm screen", size=14, color=FAIL)
    values = [
        (
            "Rigid/ideal diagnostic",
            s[0]["ideal_body_mount_translation_and_rotation"]["total_tip_mm"],
            WOOD,
        ),
        ("Best finite support", min(row["total_tip_mm"] for row in s[0]["finite_roots"]), FAIL),
    ]
    for i, (name, value, color) in enumerate(values):
        y = 801 + i * 79
        svg.text(68, y, name, size=17, weight="bold")
        svg.rect(bar_x, y - 21, value / 1.5 * bar_w, 29, fill=color, stroke="none", rx=3)
        svg.text(1410, y, f"{number(value)} mm", size=18, color=color, weight="bold")
    svg.text(
        52,
        978,
        "Best finite 1.185 mm short-tab sensitivity fails 1 mm; extra aft-end rotational restraint is uncredited.",
        size=16,
        color=FAIL,
        weight="bold",
    )
    svg.text(
        52,
        1008,
        "Rigid ideal 0.901 mm is diagnostic. Complete installed displacement is unavailable; failed sensitivity is not physical impossibility.",
        size=16,
        color=FAIL,
    )
    svg.text(
        52,
        1038,
        f"Actual 130 mm body root: one-face mean {number(supplement['body_single_face_mean_shear_Pa'] / 1e6)} MPa > {number(joint['existing_hot_shear_screen_Pa'] / 1e6)} MPa estimate. Record subregion 109.4 mm: {number(joint['single_face_mean_shear_Pa'] / 1e6)} MPa.",
        size=15,
        color=FAIL,
    )
    svg.text(
        52,
        1068,
        f"Aft filled bond {number(supplement['aft_tab_end']['area_mm2'])} mm²: {number(supplement['aft_tab_end']['mean_shear_force_screen_N'])} N mean-shear / {number(supplement['aft_tab_end']['elastic_pure_moment_screen_Nm'], 4)} N m elastic pure-moment screens at 1 MPa; capacity unknown.",
        size=15,
        color=FAIL,
    )
    svg.text(
        52,
        1098,
        "204-11 CLT unit interpretation, hot finished modulus/strength, local peel, ring stiffness and partition remain unqualified.",
        size=16,
    )
    svg.footer(meta, 1152)
    return svg


def cases(cfg: dict, rec: dict, meta: dict) -> SVG:
    svg = SVG(
        "FR1 complete recorded mass and launch screens",
        "Eight nominal/max stock-thickness cases; full separate 50 g included in each saved total",
        height=1580,
        status="STOPPED PREFLIGHT",
    )
    svg.text(
        48,
        139,
        "A  EIGHT SAVED CASES — 55 g allocation / 68 g metadata sensitivity",
        size=20,
        weight="bold",
    )
    svg.text(
        48,
        168,
        "Both nylon values are unmeasured; minimum 2.921 mm stock was not one of these eight vehicle cases.",
        size=15,
        color=FAIL,
    )
    columns = [
        (55, "Case"),
        (210, "Stock mm"),
        (355, "Nylon g"),
        (475, "Total g"),
        (610, "CG mm"),
        (730, "Static cal"),
        (855, "1.5 m m/s"),
        (1015, "1.8 m m/s*"),
        (1190, "Formal g"),
        (1390, "Planning g"),
    ]
    for x, heading in columns:
        svg.text(x, 214, heading, size=15, weight="bold")
    svg.line(48, 228, 1652, 228, color="#9bb1bd", width=1)
    for i, row in enumerate(rec["cases"]):
        y = 259 + i * 122
        svg.rect(
            48,
            y - 24,
            1604,
            104,
            fill="#ffffff" if i % 2 == 0 else "#eaf1f4",
            stroke="#cfdae0",
            rx=5,
        )
        values = [
            (55, row["case"], INK),
            (210, number(row["stock_thickness_mm"]), INK),
            (355, number(row["nylon_mass_g"], 0), INK),
            (475, number(row["total_mass_g"]), INK),
            (610, number(row["cg_mm"]), INK),
            (730, number(row["margin_cal"]), INK),
            (855, number(row["guide_mps"]["1.5"], 4), NEW),
            (1015, number(row["guide_mps"]["1.8"], 4), AMBER),
            (1190, number(row["formal_headroom_g"]), NEW),
            (1390, number(row["planning_headroom_g"]), FAIL),
        ]
        for x, value, color in values:
            svg.text(
                x, y + 11, value, size=16, color=color, weight="bold" if x in (855, 1390) else None
            )
        svg.text(
            55,
            y + 46,
            (
                "Adverse includes +20 g aft and +12.8 mm motor-CG probe"
                if row["case"] == "adverse"
                else "Nominal motor-CG probe; separate full 50 g included"
            ),
            size=14,
            color=MUTED,
        )
        svg.text(
            828,
            y + 46,
            "formal 15 m/s conditional pass; separate 15.5 planning miss",
            size=14,
            color=FAIL,
        )
    svg.text(
        48,
        1243,
        "* 1.8 m values require unconfirmed usable guide/equipment. Formal 1.5 m results are conditional source-model screens.",
        size=16,
        color=AMBER,
    )
    svg.rect(48, 1275, 1604, 201, fill="#fff2e7", stroke="#d8b78e", rx=7)
    svg.text(
        68, 1311, "B  MASS ACCOUNTING IS PROPOSED, NOT ADMITTED", size=19, weight="bold", color=FAIL
    )
    svg.text(
        68,
        1348,
        f"Net proposed change from AD1: {number(rec['net_mass_change_from_AD1_g'])} g; nominal physical mass {number(rec['physical_mass_g'])} g before full 50 g.",
        size=16,
    )
    svg.text(
        68,
        1378,
        "Removed wedge, finish and slot-fill mass can be credited only if the replacement support function is verified.",
        size=16,
        color=FAIL,
    )
    svg.text(
        68,
        1408,
        "All eight formal speed screens pass conditionally; all eight separate 15.5 m/s planning screens miss.",
        size=16,
    )
    svg.text(
        68,
        1438,
        "Installed fin/root strength, total movement, finished hot properties, inertia, fit and flight acceptance remain open.",
        size=16,
        color=FAIL,
    )
    svg.footer(meta, 1498)
    return svg


def png_pixels(path: Path) -> tuple[int, int]:
    head = path.read_bytes()[:24]
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"Not a PNG: {path}")
    return struct.unpack(">II", head[16:24])


def package(out: Path) -> Path:
    archive = out / "drawing-pack.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
        for name in ("index.html", "README.md", "manifest.json", "parts.csv", "parts.html"):
            zipped.write(out / name, arcname=name)
        for path in sorted(out.glob("*.svg")) + sorted(out.glob("*.png")):
            zipped.write(path, arcname=path.name)
    return archive


def write_parts(rec: dict) -> dict:
    """Copy all recorded ledger rows and separate proposed removals without recomputation."""
    rows = [
        {
            "row_type": "recorded_ledger",
            "id": item["id"],
            "mass_g": item["mass_g"],
            "cg_mm": item["cg_mm"],
            "cost_usd": item["cost_usd"],
            "basis": item["basis"],
            "function_replacement": "",
        }
        for item in rec["ledger"]
    ]
    rows += [
        {
            "row_type": "proposed_removal_not_admitted",
            "id": item["id"],
            "mass_g": item["mass_g"],
            "cg_mm": "",
            "cost_usd": "",
            "basis": "",
            "function_replacement": item["function_replacement"],
        }
        for item in rec["removed"]
    ]
    if len(rec["ledger"]) != 53 or len(rec["removed"]) != 3:
        raise ValueError("Recorded FR1 parts/removal count changed")
    fieldnames = ["row_type", "id", "mass_g", "cg_mm", "cost_usd", "basis", "function_replacement"]
    csv_path, html_path = OUTPUT / "parts.csv", OUTPUT / "parts.html"
    with csv_path.open("w", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    def table(items: list[dict], columns: list[tuple[str, str]]) -> str:
        head = "".join(f"<th>{html.escape(label)}</th>" for _, label in columns)
        body = "".join(
            "<tr>"
            + "".join(f"<td>{html.escape(str(row[key]))}</td>" for key, _ in columns)
            + "</tr>"
            for row in items
        )
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"

    ledger_cols = [
        ("id", "Part / budget"),
        ("mass_g", "Mass g"),
        ("cg_mm", "CG mm"),
        ("cost_usd", "Cost USD"),
        ("basis", "Recorded function / basis"),
    ]
    removal_cols = [
        ("id", "Proposed removal"),
        ("mass_g", "Mass g"),
        ("function_replacement", "Replacement function and condition"),
    ]
    html_path.write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        "<title>FR1 recorded parts ledger</title><style>body{font:15px/1.45 system-ui;color:#15334a;background:#f5f8fa;margin:24px auto;max-width:1500px}table{border-collapse:collapse;width:100%;background:white}th,td{padding:10px;border:1px solid #b6c9d4;text-align:left;vertical-align:top}th{background:#dce8ef;position:sticky;top:0}tr:nth-child(even){background:#f0f5f7}td:nth-child(2),td:nth-child(3),td:nth-child(4){white-space:nowrap}section{margin:28px 0}a{color:#087f78}</style>"
        f"<h1>FR1 recorded parts ledger</h1><p>Source <code>{html.escape(str(RECORD.relative_to(ROOT)))}</code> · SHA-256 <code>{sha(RECORD)}</code>. "
        "This is proposal accounting for a stopped preflight; the removals below have no admitted functional credit.</p>"
        '<p><a href="index.html">Drawing gallery</a> · <a href="parts.csv">Exact CSV values</a></p>'
        "<p>Rock West 204-11 plate $108.99 is charged once to fin_set. The earlier $69.75 wood sheet purchase remains charged once to forward_ring and is still needed for rings and nose. Cost placement is ledger allocation, not a second purchase.</p>"
        "<section><h2>53 recorded ledger rows</h2>" + table(rows[:53], ledger_cols) + "</section>"
        "<section><h2>3 proposed removals — conditional, not adopted</h2>"
        + table(rows[53:], removal_cols)
        + "</section></html>\n"
    )
    return {
        "ledger_rows": 53,
        "proposed_removal_rows": 3,
        "csv": {"path": str(csv_path.relative_to(ROOT)), "sha256": sha(csv_path)},
        "html": {"path": str(html_path.relative_to(ROOT)), "sha256": sha(html_path)},
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-only", action="store_true")
    args = parser.parse_args()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    if args.package_only:
        archive = package(OUTPUT)
        print(json.dumps({"zip": str(archive.relative_to(ROOT)), "sha256": sha(archive)}))
        return
    cfg = yaml.safe_load(CONFIG.read_text())
    rec = json.loads(RECORD.read_text())
    supplement = json.loads(SUPPLEMENT.read_text())
    if cfg["id"] != rec["identity"] or rec["adopted"] is not False or len(rec["cases"]) != 8:
        raise SystemExit("FR1 source identity or case-count mismatch")
    if sha(ROOT / cfg["source"]) != cfg["source_sha256"]:
        raise SystemExit("FR1 baseline source changed")
    if supplement.get("identity") != rec["identity"] or supplement.get("source_sha256") != sha(
        RECORD
    ):
        raise SystemExit("FR1 joint supplement source changed")
    for rel, expected in rec["sources"].items():
        if sha(ROOT / rel) != expected:
            raise SystemExit(f"Pinned FR1 source changed: {rel}")
    if (
        sha(CONFIG) != rec["sources"][str(CONFIG.relative_to(ROOT))]
        or sha(CANDIDATE) != rec["sources"][str(CANDIDATE.relative_to(ROOT))]
    ):
        raise SystemExit("FR1 config or candidate changed")
    meta = {
        "identity": rec["identity"],
        "adopted": False,
        "status": rec["decision"],
        "representation": "local_concept_and_recorded_scalar_screens_not_CAD_or_field_maps",
        "specification": {"path": str(CONFIG.relative_to(ROOT)), "sha256": sha(CONFIG)},
        "candidate": {"path": str(CANDIDATE.relative_to(ROOT)), "sha256": sha(CANDIDATE)},
        "record": {"path": str(RECORD.relative_to(ROOT)), "sha256": sha(RECORD)},
        "joint_supplement": {"path": str(SUPPLEMENT.relative_to(ROOT)), "sha256": sha(SUPPLEMENT)},
        "exporter": {"path": str(Path(__file__).relative_to(ROOT)), "sha256": sha(Path(__file__))},
        "svg_helper": {"path": str(SVG_HELPER.relative_to(ROOT)), "sha256": sha(SVG_HELPER)},
        "native_renderer": {"path": str(HELPER.relative_to(ROOT)), "sha256": sha(HELPER)},
        "sources": rec["sources"],
        "units": {"length": "mm", "mass": "g", "force": "N", "moment": "N m", "stress": "MPa"},
        "browser_verified": False,
        "engineering_accepted": False,
    }
    parts = write_parts(rec)
    drawings = {
        "01-fin-and-parallel-paths": fin_and_paths(cfg, rec, supplement, meta),
        "02-finite-support-screen": support_and_load(cfg, rec, supplement, meta),
        "03-eight-mass-guide-cases": cases(cfg, rec, meta),
    }
    (OUTPUT / "swift-module-cache").mkdir(exist_ok=True)
    started = time.monotonic()
    artifacts = []
    for name, drawing in drawings.items():
        svg_path, png_path = OUTPUT / f"{name}.svg", OUTPUT / f"{name}.png"
        drawing.write(svg_path, meta)
        remaining = 120 - (time.monotonic() - started)
        if remaining <= 1:
            raise SystemExit("Native AppKit render exceeded 120 s")
        subprocess.run(
            [
                "/usr/bin/swift",
                "-module-cache-path",
                str(OUTPUT / "swift-module-cache"),
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
                    "pixels": png_pixels(png_path),
                },
            }
        )
    elapsed = time.monotonic() - started
    if elapsed > 120:
        raise SystemExit("Native AppKit render exceeded 120 s")
    manifest = {
        **meta,
        "artifacts": artifacts,
        "parts": parts,
        "native_render_seconds": elapsed,
        "native_render_limit_seconds": 120,
        "visual_inspection": [],
        "limits": [
            "Native AppKit image document is offline evidence, not browser verification",
            "No CAD, continuum simulation, physical loading or qualification was run",
        ],
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    cards = "".join(
        f'<article><h2>{a["id"].replace("-", " ").title()}</h2><a href="{a["id"]}.png"><img src="{a["id"]}.png" alt="Offline {a["id"]} drawing"></a><p><a href="{a["id"]}.svg">SVG</a> · <a href="{a["id"]}.png">PNG</a></p></article>'
        for a in artifacts
    )
    (OUTPUT / "index.html").write_text(
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>FR1 fin root preflight</title>'
        "<style>body{font:16px/1.5 system-ui;background:#e9eff3;color:#15334a;max-width:1500px;margin:auto;padding:28px}img{width:100%;height:auto;border:1px solid #8aa1af}article{background:white;padding:20px;margin:22px 0}a{color:#087f78}</style>"
        "<h1>FR1 stopped fin-root preflight · offline drawings</h1><p>Three recorded concept/screen drawings. No installed strength, thermal or flight acceptance.</p>"
        '<p><a href="README.md">Review notes</a> · <a href="manifest.json">Source manifest</a> · <a href="parts.html">53-part ledger</a> · <a href="parts.csv">CSV</a> · <a href="drawing-pack.zip">ZIP</a></p>'
        + cards
        + "</html>\n"
    )
    (OUTPUT / "README.md").write_text(
        "# FR1 offline fin-root preflight drawings\n\n"
        f"Identity `{rec['identity']}`; config SHA-256 `{sha(CONFIG)}`; candidate SHA-256 `{sha(CANDIDATE)}`; record SHA-256 `{sha(RECORD)}`.\n\n"
        f"Joint supplement SHA-256 `{sha(SUPPLEMENT)}`; it corrects body-root contact area and bounds uncredited aft-end support.\n\n"
        "The linked `parts.csv` and `parts.html` copy all 53 recorded mass/CG/cost/function rows plus three clearly labeled proposed removals. The $69.75 wood sheet allocation moved to the forward ring and remains needed for rings and nose; the $108.99 CFRP plate is charged once to the fin set.\n\n"
        "Three source-linked SVGs and native AppKit PNGs were generated. Visual inspection pending; see manifest.\n\n"
        "The fin/root preflight is stopped. Scalar models and geometry projections are not spatial stress maps, installed support or finished hot strength. No browser, CAD, physical test or flight acceptance follows.\n"
    )
    archive = package(OUTPUT)
    print(
        json.dumps(
            {
                "identity": rec["identity"],
                "artifacts": len(artifacts),
                "native_seconds": elapsed,
                "manifest": str((OUTPUT / "manifest.json").relative_to(ROOT)),
                "zip_sha256": sha(archive),
            }
        )
    )


if __name__ == "__main__":
    main()
