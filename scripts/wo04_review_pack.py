"""Package recorded drawings/images for local review; no redraw or physical calculation."""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output/rocket-twin-review"
GROUPS = (
    "engineering-walkthrough",
    "engineering-walkthrough-rendered",
    "engineering-workbench-extended",
    "wo03-architecture",
)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    copied = {}
    for group in GROUPS:
        directory = ROOT / "output" / group
        if not directory.exists():
            raise FileNotFoundError(f"Recorded drawings unavailable: {directory}")
        for path in directory.iterdir():
            if (
                path.name == "renderer-check.svg"
                or not path.is_file()
                or not (
                    path.suffix in (".svg", ".png")
                    or path.name.endswith(".metadata.json")
                    or path.name in ("index.html", "source-manifest.json")
                )
            ):
                continue
            target = OUT / group / path.name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)
            copied[str(target.relative_to(OUT))] = hashlib.sha256(target.read_bytes()).hexdigest()
    source = ROOT / "runs/wo03-architecture-space-mass-20261102-v1/record.json"
    record = json.loads(source.read_text())
    shutil.copy2(source, OUT / "architecture-record.json")
    copied["architecture-record.json"] = hashlib.sha256(source.read_bytes()).hexdigest()
    rows = []
    for arrangement in record["arrangements"]:
        for case in arrangement["cases"]:
            speed = next(g["rail_exit_speed_mps"] for g in case["guides"] if g["usable_m"] == 1.5)
            rows.append(
                f"<tr><td>{html.escape(arrangement['id'])}</td><td>{html.escape(case['id'])}</td>"
                f"<td>{case['total_g']:.3f} g</td><td>{case['loaded_static_cal']:.3f} calibre</td>"
                f"<td>{speed:.3f} m/s - fails15</td></tr>"
            )
    page = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Rocket Twin review pack</title>
<style>body{font:16px/1.6 system-ui,sans-serif;background:#101e29;color:#e2edf4;max-width:1200px;margin:auto;padding:26px}a{color:#9bd9f0}h1,h2{line-height:1.3}.notice{border-left:4px solid #e3b776;background:#30291f;padding:16px}table{width:100%;border-collapse:collapse}td,th{border-bottom:1px solid #496173;padding:9px;text-align:left}img{display:block;width:100%;height:auto;border:1px solid #496173}figure{margin:25px 0}code{overflow-wrap:anywhere}.small{font-size:14px;color:#b6cad7}</style>
<h1>Rocket Twin engineering review</h1><p class="notice"><strong>Preliminary - engineering acceptance remains open.</strong> G80 first; C1 remains preliminary. R1/C2/C3 are rejected. A is preferred only for a bounded connection study; A/B are not admitted to detailed CAD. No physical or flight release.</p>
<p>These are actual offline document images and source-defined concept drawings, not browser screenshots or a manufacturing-ready CAD assembly. Current C1 CAD is unavailable;135 allocation/envelope rows are not135 CAD solids. Full rotational inertia and compatible current stress/temperature fields remain unavailable.</p>
<h2>Complete recorded architecture cases</h2><p>Every total includes the separate full50g allowance. Adverse cases add20g aft and the recorded motor-balance probe. The formal guide requirement is15m/s;15.5 is a separate planning target. All longer-guide equipment remains unconfirmed.</p>
<table><thead><tr><th>Architecture</th><th>Case</th><th>Complete mass</th><th>Stability</th><th>1.5m baseline</th></tr></thead><tbody>"""
    page += (
        "".join(rows)
        + """</tbody></table><p>Mass, guide speed and margins above are read from the immutable record; this pack performs no physical calculation. <a href="architecture-record.json">Exact record and sources</a>.</p>
<h2>Start with these three images</h2>
<figure><a href="wo03-architecture/architecture-A-motor-fin-can.png"><img src="wo03-architecture/architecture-A-motor-fin-can.png" alt="Dimensioned A concept, protected motor and recovery spaces, recorded margins and open joints"></a><figcaption>A: actual recorded design intent and force connections. Source-defined concept, not admitted CAD.</figcaption></figure>
<figure><a href="engineering-workbench-extended/comparison-01.png"><img src="engineering-workbench-extended/comparison-01.png" alt="Six candidates and twelve saved mass and stability cases"></a><figcaption>C1 through A/B comparison. Failed thresholds and conceptual status remain explicit.</figcaption></figure>
<figure><a href="engineering-workbench-extended/electrical-01.png"><img src="engineering-workbench-extended/electrical-01.png" alt="Separated main avionics and independent recovery source netlists"></a><figcaption>Recorded electrical topology, with separate recovery power. Missing pins and qualification remain open; glossary is in the view index.</figcaption></figure>
<h2>All drawings and contact sheets</h2><ul>
<li><a href="engineering-walkthrough/index.html">Original25 C1/R1 vector drawings</a> / <a href="engineering-walkthrough-rendered/contact-sheet.png">actual image contact sheet</a></li>
<li><a href="engineering-workbench-extended/index.html">Eleven new workbench SVG/PNG views and explanations</a> / <a href="engineering-workbench-extended/contact-sheet.png">contact sheet</a></li>
<li><a href="wo03-architecture/architecture-B-outer-captured-roots.png">B concept and unresolved connections</a></li></ul>
<h2>Interactive local app</h2><p>Run <code>make preview</code> from the repository, then open <a href="http://127.0.0.1:5173/?workspace=engineering">the engineering workbench</a>. Append <code>&amp;view=comparison</code>, <code>recovery</code>, <code>thermal</code>, <code>electrical</code>, <code>assembly</code> or <code>requirements</code>. Existing3D inspection, experiments and replay remain separate. Browser interactions/host reachability still await the designated-agent ownership prerequisite.</p>
<p class="small">Representative image annotations and arrows were actually inspected. Contact sheets establish page overview, not exhaustive full-size acceptance. Histories/fields from different candidates are not current C1 results. Geometry is concept/envelope unless explicitly identified otherwise. See source manifests/sidecars for units, axes, revisions, assumptions and evidence status.</p></html>"""
    )
    (OUT / "index.html").write_text(page)
    copied["index.html"] = hashlib.sha256((OUT / "index.html").read_bytes()).hexdigest()
    (OUT / "manifest.json").write_text(
        json.dumps(
            {"files_sha256": copied, "physics_run": False, "browser_screenshot": False}, indent=2
        )
        + "\n"
    )
    bundle = OUT / "review-pack.zip"
    with zipfile.ZipFile(bundle, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for relative in [*copied, "manifest.json"]:
            archive.write(OUT / relative, relative)
    print(
        json.dumps(
            {
                "index": str((OUT / "index.html").relative_to(ROOT)),
                "zip": str(bundle.relative_to(ROOT)),
                "bytes": bundle.stat().st_size,
                "files": len(copied),
                "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
            }
        )
    )


if __name__ == "__main__":
    main()
