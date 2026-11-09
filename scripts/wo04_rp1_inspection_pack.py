"""Package existing verified RP1 inspection bytes into a local folder and ZIP.

No geometry generation, analysis, installation, public copy or historical catalog.
The fixed registry is checked before and after packaging; existing output stops
a repeat instead of overwriting an evidence packet.
"""

from __future__ import annotations

import hashlib
import html
import json
import shutil
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NAME = "rp1-desktop-inspection-pack"
OUTPUT = ROOT / "output" / NAME
ZIP = OUTPUT.with_suffix(".zip")
REPORT = ROOT / "docs/studies/frontend-desktop-detail-20261108/inspection-pack.json"
REGISTRY = {
    "docs/studies/rp1-inspection-geometry-20261107/manifest.json": (
        "metadata/core-geometry.json",
        "f83054f7fd1e97f39c8c2102e514fe1835c3eec00b3de891579dce715ba7626c",
    ),
    "docs/studies/frontend-desktop-detail-20261108/cad-export.json": (
        "metadata/inspection-step.json",
        "a7af1fadc431dea8958a212e2a552cf2ee833b068dbeaf51dc151d6d7fbbf731",
    ),
    "docs/studies/frontend-desktop-detail-20261108/source-coverage.json": (
        "metadata/source-coverage.json",
        "bc952bb633f0a6b8fe084da0b930aa4aaee056aa55f4383ca6033ff30b0878e0",
    ),
    "web/public/engineering-workbench/rp1-connections.json": (
        "metadata/joint-connections.json",
        "7087e7dc7434a0c4d309055d7897ee79bb140e58e30b24499579e65d5e6b328e",
    ),
}


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def check(relative: str, expected: str) -> bytes:
    path = ROOT / relative
    if not path.resolve().is_relative_to(ROOT.resolve()):
        raise ValueError("Registered input escapes repository")
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Registered source/asset changed: {relative}")
    return data


def main() -> None:
    started_wall, started_cpu = time.monotonic(), time.process_time()
    if OUTPUT.exists() or ZIP.exists() or REPORT.exists():
        raise SystemExit("Pack/report already exists; no overwrite or automatic repeat")
    raw = {path: check(path, expected) for path, (_, expected) in REGISTRY.items()}
    core, step, coverage, connections = [json.loads(data) for data in raw.values()]
    if (
        core["identity"] != step["identity"]
        or core["identity"] != coverage["identity"]
        or step["status"] != "complete_inspection_reconstruction"
        or core["coverage"]["source_parts"] != 55
        or core["coverage"]["mesh_parts"] != 26
        or len(core["parts"]) != 55
        or len(step["parts"]) != 26
        or len(step["assemblies"]) != 2
        or len(connections["drawings"]) != 4
        or core["identity"]["inspection_geometry_sha256"]
        != "238d01e5e3381560aab9eb99673617803ab020e01a8cf171ba4dffe67228b608"
    ):
        raise ValueError("Fixed source identity/coverage mismatch")
    sources = dict(core["sources"])
    sources.update({step["script"]["path"]: step["script"]["sha256"]})
    if step["source_hashes"] != core["sources"]:
        raise ValueError("STEP/core source tuple differs")
    for path, expected in sources.items():
        check(path, expected)
    if (ROOT / "output/rp1-inspection-geometry/manifest.json").read_bytes() != raw[
        next(iter(REGISTRY))
    ]:
        raise ValueError("Core generated/saved manifests differ")
    inputs: list[dict[str, str]] = []
    for path, (target, expected) in REGISTRY.items():
        inputs.append({"source": path, "path": target, "sha256": expected})
    for row in [*core["parts"], {"id": "assembly", "mesh": core["assembly"]}]:
        if row["mesh"]:
            target = "glb/assembly.glb" if row["id"] == "assembly" else f"glb/parts/{row['id']}.glb"
            inputs.append(
                {"source": row["mesh"]["path"], "path": target, "sha256": row["mesh"]["sha256"]}
            )
    for row in [*step["parts"], *step["assemblies"]]:
        relative = f"parts/{row['id']}.step" if row in step["parts"] else f"{row['id']}.step"
        if row["path"] != f"output/rp1-inspection-step/{relative}":
            raise ValueError("Unregistered STEP source path")
        inputs.append({"source": row["path"], "path": f"step/{relative}", "sha256": row["sha256"]})
    for row in connections["drawings"]:
        if row["path"] != f"output/rp1-attachment-definition/{row['id']}.svg":
            raise ValueError("Unregistered joint drawing path")
        inputs.append(
            {"source": row["path"], "path": f"drawings/{row['id']}.svg", "sha256": row["sha256"]}
        )
    if len(inputs) != 63 or len({row["path"] for row in inputs}) != 63:
        raise ValueError("Expected63 distinct registered input assets")
    for row in inputs:
        check(row["source"], row["sha256"])

    OUTPUT.mkdir(parents=True)
    for row in inputs:
        target = OUTPUT / row["path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / row["source"], target)
        if digest(target.read_bytes()) != row["sha256"]:
            raise ValueError("Copied asset differs")
        if row["path"].startswith("metadata/"):
            target.chmod(0o444)
    readme = """# RP1 desktop inspection pack

Open index.html for local links to the exact files. Open STEP files in your CAD
viewer and GLB files in a compatible 3D viewer; the HTML index is a file directory,
not an embedded WebGL/CAD application. No network or backend is required for the
included bytes. Nothing in this folder is a manufacturing, build or flight pack.

Start with step/critical_motor_fin_ring_joint.step (9 source records /18 solids),
step/rp1_ad1_v2_inspection_26_records.step (26 records /36 solids), or
glb/assembly.glb. Individual files retain stable IDs under step/parts and glb/parts.
The four drawings are saved AD1 concepts, not newly analyzed or manufacturing CAD.

SOURCE AND FRAME
Frozen G80-F2-RP1-AD1-definition-v2; exact identity/hashes are in manifest.json.
STEP: millimetres; origin at nose; X=body+y, Y=body-z, Z=station aft from nose.
Original placement is [lateral[0],-lateral[1],station]*1000, not exploded separation.
GLB: metres; X=cadX/1000, Y=length_m-cadZ/1000, Z=cadY/1000.
Thus GLB +Y points toward the nose while STEP +Z points aft. Do not overlay the
two formats without the documented mapping or silently scale one to match.

COVERAGE AND LIMITS
55 stable source records:10 source-dimensioned nominal shapes,16 simplified
envelopes,25 mass/process allowances and4 missing geometries. Only26 records have
solids; the other29 records are metadata, not omitted manufactured parts.
No threads, final retainer, cord/knot contacts, proposed ring edge roundovers,
unknown electronics internals, bonds or missing guide hardware were invented.
The optional finer ring/tube GLBs and manufacturer PCB reference are outside this
core-only pack. All copied source JSON is unchanged/read-only. The earlier source
coverage audit predates STEP export; inspection-step.json establishes the newer
STEP artifacts without upgrading their physical definition.

ENGINEERING STATUS
Frozen AD1's saved wood-fin component screen fails; it is not an installed fin pass.
FR1 fails evaluated finite movement/body-bond screens. FP1's nominal movement uses
an unverified attachment input and fails material sensitivities. FP1/FR1 are
unadopted studies, not included replacement assemblies. D1 remains the retained
load/attachment decision with whole-root/source evidence and physical acceptance
open. This packaging changes no load, allowance, configuration, mass/inertia or
engineering result. Physical/build, thermal, recovery, flutter, WO-10 owner review
and flight-release gates remain open. All five inquiries remain UNSENT.
G54 and G12 PID-to-RL remain separate committed tracks.

INTEGRITY
manifest.json lists every included file except itself, with SHA-256. The tracked
inspection-pack.json additionally identifies the ZIP and package manifest. All
source/asset pins were checked before and after copying; every ZIP entry was read
back and hashed. This checks delivery integrity, not browser/CAD visual quality,
manufacturability, fit, material properties or flight readiness.
"""
    (OUTPUT / "README.md").write_text(readme)
    table = []
    for row in core["parts"]:
        pid = row["id"]
        links = (
            f'<a href="glb/parts/{pid}.glb">GLB</a> · <a href="step/parts/{pid}.step">STEP</a>'
            if row["mesh"]
            else "No solid; see metadata"
        )
        table.append(
            f"<tr><td>{html.escape(pid)}</td><td>{html.escape(row['maturity'])}</td><td>{links}</td></tr>"
        )
    index = """<!doctype html><html lang="en"><meta charset="utf-8"><title>RP1 inspection files</title>
<style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 20px}table{border-collapse:collapse;width:100%}td,th{padding:7px;text-align:left;border-bottom:1px solid #bbb}a{color:#0756a6}</style>
<h1>RP1 desktop inspection files</h1><p>Existing nominal source geometry and envelopes. Not a manufacturing, build or flight pack.</p>
<p><a href="README.md">Read source frames and limitations first</a> · <a href="manifest.json">Package hashes</a></p>
<h2>Start here</h2><ul><li><a href="step/critical_motor_fin_ring_joint.step">Critical motor/fin/ring joint STEP</a> —9 records /18 solids</li>
<li><a href="step/rp1_ad1_v2_inspection_26_records.step">Full inspection STEP</a> —26 records /36 solids; CAD mm, nose origin, +Z aft</li>
<li><a href="glb/assembly.glb">Full inspection GLB</a> —metres, +Y toward nose</li></ul>
<p>This index links files; it does not render CAD or validate a viewer. 55 source records;26 have solids,29 remain non-spatial/missing records.</p>
<h2>Source records</h2><table><tr><th>Stable ID</th><th>Representation</th><th>Files</th></tr>"""
    index += "".join(table) + "</table><h2>Saved joint drawings</h2><ul>"
    index += "".join(
        f'<li><a href="drawings/{row["id"]}.svg">{html.escape(row["label"])}</a></li>'
        for row in connections["drawings"]
    )
    index += (
        "</ul><h2>Read-only metadata</h2><ul>"
        + "".join(f'<li><a href="{target}">{target}</a></li>' for target, _ in REGISTRY.values())
        + "</ul></html>"
    )
    (OUTPUT / "index.html").write_text(index)
    package_files = [
        *inputs,
        *(
            {"path": name, "sha256": digest((OUTPUT / name).read_bytes())}
            for name in ("README.md", "index.html")
        ),
    ]
    manifest = {
        "schema_version": 1,
        "id": NAME,
        "identity": core["identity"],
        "coverage": core["coverage"],
        "source_hashes": sources,
        "files": package_files,
        "manifest_excludes_itself": True,
        "engineering_accepted": False,
        "manufacturing_clearance": False,
        "flight_ready": False,
        "source_records_metadata": "metadata/core-geometry.json",
        "units": {"step": "mm", "glb": "m"},
        "mapping": "viewer=[cadX/1000,length_m-cadZ/1000,cadY/1000]",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    entries = [
        *package_files,
        {"path": "manifest.json", "sha256": digest((OUTPUT / "manifest.json").read_bytes())},
    ]
    with zipfile.ZipFile(ZIP, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for row in sorted(entries, key=lambda item: item["path"]):
            info = zipfile.ZipInfo(f"{NAME}/{row['path']}", date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (
                0o100444 if row["path"].startswith("metadata/") else 0o100644
            ) << 16
            archive.writestr(info, (OUTPUT / row["path"]).read_bytes())
    with zipfile.ZipFile(ZIP) as archive:
        expected = {f"{NAME}/{row['path']}": row["sha256"] for row in entries}
        if set(archive.namelist()) != set(expected) or len(archive.namelist()) != len(expected):
            raise ValueError("ZIP entry inventory differs")
        for name, expected_hash in expected.items():
            if digest(archive.read(name)) != expected_hash:
                raise ValueError(f"ZIP entry hash differs: {name}")
        if archive.testzip() is not None:
            raise ValueError("ZIP CRC check failed")
    for path, expected in sources.items():
        check(path, expected)
    for row in inputs:
        check(row["source"], row["sha256"])
        if digest((OUTPUT / row["path"]).read_bytes()) != row["sha256"]:
            raise ValueError("Pack copy changed after ZIP validation")
    report = {
        **{
            key: manifest[key]
            for key in (
                "schema_version",
                "identity",
                "coverage",
                "engineering_accepted",
                "manufacturing_clearance",
                "flight_ready",
            )
        },
        "id": NAME,
        "status": "verified_local_pack",
        "folder": str(OUTPUT.relative_to(ROOT)),
        "zip": {
            "path": str(ZIP.relative_to(ROOT)),
            "bytes": ZIP.stat().st_size,
            "sha256": digest(ZIP.read_bytes()),
            "entries": len(entries),
        },
        "package_manifest": {
            "path": f"output/{NAME}/manifest.json",
            "sha256": entries[-1]["sha256"],
        },
        "files": entries,
        "source_hashes": sources,
        "checks": {
            "before_after_source_and_asset_hashes": True,
            "copied_bytes": True,
            "zip_entry_inventory": True,
            "zip_entry_hashes": True,
            "zip_crc": True,
        },
        "runtime": {
            "wall_seconds": time.monotonic() - started_wall,
            "cpu_seconds": time.process_time() - started_cpu,
        },
        "cost_usd": 0,
        "cad_regenerated": False,
        "public_copy": False,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    print(
        json.dumps({key: report[key] for key in ("status", "zip", "package_manifest", "runtime")})
    )


if __name__ == "__main__":
    main()
