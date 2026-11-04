"""Portable VP1 inquiry-review pack from versioned sources; no engineering solve."""

from __future__ import annotations

import hashlib
import json
import shutil
import zipfile
from html import escape
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/validation/rp1-vp1"
OUT = ROOT / "output/rp1-validation-vp1"


def main() -> None:
    p = yaml.safe_load((ROOT / "configs/studies/rp1-validation-package.yaml").read_text())
    a = json.loads((DOC / "accounting.json").read_text())
    vehicle = yaml.safe_load((ROOT / p["frozen_configuration"]).read_text())
    by = {x["id"]: x for x in vehicle["parts"]}
    pins = {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in [
            "configs/studies/rp1-validation-package.yaml",
            p["frozen_configuration"],
            "docs/validation/rp1-vp1/accounting.json",
            "docs/validation/rp1-vp1/protocol.md",
            "docs/validation/rp1-vp1/package-summary.md",
        ]
    }
    assert pins[p["frozen_configuration"]] == p["configuration_sha256"]
    assert pins["configs/studies/rp1-validation-package.yaml"] == a["plan_sha256"]
    OUT.mkdir(parents=True, exist_ok=True)
    src = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 900" width="1280" height="900">',
        '<rect width="1280" height="900" fill="#10202d"/><style>text{font-family:Arial,sans-serif;fill:#ebf1f8} .n{fill:#f3c767} .s{fill:#a9c0d3}</style>',
        '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="4" orient="auto"><path d="M0 0L8 4L0 8" fill="#f3c767"/></marker></defs>',
        "<metadata>"
        + escape(
            json.dumps(
                {
                    "id": p["id"],
                    "source_sha256": pins,
                    "status": "Planning concept; fixture not accepted; no test performed",
                }
            )
        )
        + "</metadata>",
    ]

    def text(x, y, t, size=20, cls=""):
        src.append(f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}">{escape(t)}</text>')

    text(30, 40, "VP1 — plywood validation: inquiry-ready, not approved to execute", 27)
    text(
        30,
        75,
        "Root-input illustration, not a distributed-pressure or complete-tip test. Units: mm, N, N·m.",
        19,
        "s",
    )
    src.append(
        '<rect x="40" y="120" width="240" height="245" rx="8" fill="#233d50" stroke="#88a8bf"/>'
    )
    text(60, 155, "Actual flexible body")
    text(60, 187, "tube / rings / bonds")
    text(60, 223, "No rigid-root claim", 19, "n")
    text(60, 255, "Lab grip/reaction and", 18)
    text(60, 282, "uncertainty agreement", 18)
    text(60, 309, "are required first.", 18)
    src.append('<rect x="280" y="285" width="840" height="45" fill="#789a9b" stroke="#d1e2e5"/>')
    text(530, 360, "Fin span direction outward → 0–60 mm (concept, not CAD)", 19, "s")
    for pos, f in zip((10, 40), a["force_pair_N"], strict=True):
        x = 280 + 14 * pos
        src.append(
            f'<line x1="{x}" y1="145" x2="{x}" y2="279" stroke="#f3c767" stroke-width="4"/><polygon points="{x-7},265 {x+7},265 {x},281" fill="#f3c767"/>'
        )
        text(x - 65, 125, f"{f:.3f} N", 23, "n")
        text(x - 48, 265, f"{pos} mm", 18)
    text(
        30,
        415,
        "Verified input sum: 331.125 N; turning moment: 8.830 N·m. Design factor 3 is already applied.",
        21,
        "n",
    )
    text(
        30,
        448,
        "Actual load sharing, pad centroids, friction, fixture motion and root rotation must be measured.",
        19,
    )
    text(
        30,
        480,
        "A single 147.167 N tip force at 60 mm matches moment but understates shear. Do not substitute it.",
        18,
        "s",
    )
    text(
        30,
        530,
        "Local article identity: vehicle stations 980–1220 mm from nose; test geometry pending admission.",
        20,
    )
    src.append(
        '<rect x="40" y="580" width="1200" height="155" fill="none" stroke="#b8cddd" stroke-width="3"/>'
    )

    def axial(z):
        return 40 + (z - 980) * 5

    src.append(
        f'<rect x="{axial(1055)}" y="635" width="{(1220-1055)*5}" height="55" fill="#c2ac80"/>'
    )
    fore = by["forward_ring"]["cad"]["parameters"]
    for z0, z1 in ((fore["front_station_m"] * 1000, fore["aft_station_m"] * 1000), (1190, 1196)):
        src.append(
            f'<rect x="{axial(z0)}" y="582" width="{(z1-z0)*5}" height="151" fill="#6f94a6"/>'
        )
    tab = by["fin_tabs"]["cad"]["parameters"]
    z0 = tab["front_station_m"] * 1000
    z1 = tab["aft_station_m"] * 1000
    src.append(f'<rect x="{axial(z0)}" y="590" width="{(z1-z0)*5}" height="35" fill="#90a98c"/>')
    text(52, 565, "Paper body; axial schematic", 18)
    text(70, 770, "980 mm datum", 18)
    text(430, 770, "Forward ring 1060–1072.2", 16)
    text(760, 565, "Integral tab 1080.2–1189.6", 18)
    text(860, 770, "Aft ring 1190–1196", 17)
    text(780, 720, "Motor tube 1055–1220", 18)
    text(
        30,
        810,
        "Axial dimensions only; radial layers are schematic. Aft0.4 mm glue gap is not a butt stop.",
        19,
        "n",
    )
    text(30, 845, p["id"] + " | no material adoption, purchase, contact or physical work", 17, "s")
    text(30, 875, "Frozen AD1 SHA-256 " + p["configuration_sha256"], 14, "s")
    src.append("</svg>")
    (OUT / "fixture-concept.svg").write_text("\n".join(src) + "\n")
    for name in ("package-summary.md", "protocol.md", "accounting.json"):
        text = (DOC / name).read_text()
        if name.endswith(".md"):
            text = (
                text.replace("../../../configs/", "../../configs/")
                .replace("../../wo03-", "../../docs/wo03-")
                .replace("../../../output/rp1-validation-vp1/", "./")
                .replace("(drawing-manifest.json)", "(manifest.json)")
            )
        (OUT / name).write_text(text)
    shutil.copytree(DOC / "messages", OUT / "messages", dirs_exist_ok=True)
    rows = "".join(
        f'<tr><td>{escape(r["sku"])}</td><td>{r["quantity"]} {escape(r["unit"])}</td><td>${r["unit_usd"]:.2f}</td><td><a href="{escape(r["source"],quote=True)}">Source / availability</a></td></tr>'
        for r in p["materials"]
    )
    messages = "".join(
        f"<details><summary>{escape(f.name)} — UNSENT</summary><pre>{escape(f.read_text())}</pre></details>"
        for f in sorted((OUT / "messages").glob("*.txt"))
    )
    html = f"""<!doctype html><html lang="en"><meta charset="utf-8"><title>VP1 validation review</title><style>body{{max-width:1180px;margin:28px auto;padding:0 20px;background:#10202d;color:#eef4fa;font:17px/1.55 system-ui}}a{{color:#9bd8ff}}table{{border-collapse:collapse;width:100%}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #486071}}.status{{background:#3b3020;padding:16px}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:#203647;padding:14px}}img{{width:100%;height:auto}}details{{margin:14px 0}}</style><h1>One ordinary-plywood validation package</h1><p class="status">Inquiry-ready. Recommended authorization: five no-cost requests only ($0). No material adopted; no purchase, specimen or test authorized.</p><p>Single lead: Spruce02-20850 nominal6mm birch + WEST105/206/406. G80 first; G54/G12 PID-to-RL separate. Frozen D1 loads and all physical/flight gates remain.</p><p><a href="package-summary.md">Full owner summary and cost decision</a> · <a href="protocol.md">Staged protocol / uncertainty / stops</a> · <a href="fixture-concept.svg">Standalone source-labeled drawing</a> · <a href="rp1-vp1-review.zip">Review ZIP</a></p><h2>Fixture concept and actual article references</h2><img src="fixture-concept.svg" alt="Planning-only root-input fixture and actual-source local article stations"><h2>Minimum stock reserved for the conditional programme</h2><table><tr><th>Item</th><th>Quantity</th><th>Unit USD</th><th>Source</th></tr>{rows}</table><p>Known first room material order: <strong>${a['initial_room_material_order_usd']}</strong>. Full stock reserve: <strong>${a['published_material_order_usd']}</strong>. Both exclude shipping, tax, preparation, fixtures, calibrated channels and services.</p><p class="status">Expected all-in test cost is UNQUOTED, not zero. $5,000 is an internal affordability screen, not a vendor price or spending authorization. No home-equipment credit.</p><h2>Stages and stop decisions</h2><ol><li>S0: existing product information and one written lab method/price request; one follow-up day5, close documentation day10.</li><li>S1: ten room wood strips +six curved-joint witnesses; lab quote/method and separate owner approval first. Failed measurement/process stops root work.</li><li>S2: only after a credible admitted construction and supported material decision; twenty conditioned strips +twelve joints +three roots. Independent thermal/recovery/flutter/flight gates stay open.</li></ol><h2>Exact draft messages — nothing sent</h2>{messages}<p>This ZIP contains the review content, drawing and five drafts. Full project-source links require the repository checkout. These are offline artifacts, not browser interaction evidence. Figure is a concept, not accepted CAD or calculated stress. Source identity: {escape(p['id'])}.</p></html>"""
    (OUT / "index.html").write_text(html)
    manifest = {
        "id": p["id"],
        "sources": pins,
        "images_are_browser_screenshots": False,
        "native_visual_inspection": "pending",
        "files": {
            str(f.relative_to(OUT)): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in OUT.rglob("*")
            if f.is_file() and f.suffix not in (".zip", ".png") and f.name != "manifest.json"
        },
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    with zipfile.ZipFile(OUT / "rp1-vp1-review.zip", "w", zipfile.ZIP_DEFLATED) as archive:
        for f in OUT.rglob("*"):
            if f.is_file() and f.suffix != ".zip":
                archive.write(f, str(f.relative_to(OUT)))
    print(f"Prepared {OUT}/index.html; no test or browser execution")


if __name__ == "__main__":
    main()
