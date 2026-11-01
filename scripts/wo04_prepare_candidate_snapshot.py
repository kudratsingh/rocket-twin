"""Prepare the archived 72-part candidate for read-only inspection, without CAD regeneration."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STAGED = ROOT / "build/wo03-g80-integration-staging/checkout"
SOURCE = ROOT / "build/wo03-g80-integration-staging/stage1-result-metadata-final-v2"
RECORD = ROOT / "runs/wo03-g80-staged-retention-20261101-v1/record.json"
DEST = ROOT / "build/wo04-g80-retention-snapshot"
ALIAS = "experimental-g80-retention-72"
IDENTITY = "90b2a9ad780fc81d11171363432c46088531817ddb6570fe9f800429bde2bdfc"
CAD = "344f646f81e15d42ab54e7d996179581d638c6046bf1d006935b028709eca53f"


def digest(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def worker(root: Path, output: Path) -> None:
    sys.path.insert(0, str(root))
    from src.api.app import CatalogEntry, build_snapshot
    from src.vehicle.mass import mass_properties

    entry = CatalogEntry(
        "candidate.yaml",
        "Experimental G80 retention candidate",
        "candidate",
        "Experimental/unadopted — engineering acceptance open",
        "candidate",
        "Archived 72-part retention proposal; inspection only. Active baseline unchanged.",
    )
    snapshot = build_snapshot(entry, root)
    if (
        snapshot.unavailable_reason
        or snapshot.identity.resolved_spec_sha256 != IDENTITY
        or snapshot.identity.cad_revision_sha256 != CAD
        or len(snapshot.vehicle.parts) != 72
    ):
        raise ValueError(f"Staged validation/identity failed: {snapshot.unavailable_reason}")
    data = snapshot.data
    data["id"] = ALIAS
    data["snapshot_only"] = True
    data["spec"] = None
    data["checks"] = []
    data["findings"] = [
        {
            "id": "BRIDGE-RF",
            "status": "failed",
            "title": "Bridge reaction-force and reciprocity checks failed",
            "detail": "The isolated bridge model has unresolved equilibrium and reciprocity failures; no qualified load path.",
            "source": "docs/wo03-g80-bridge-fea.md",
        },
        {
            "id": "THERMAL",
            "status": "open",
            "title": "Thermal method remains unqualified",
            "detail": "No accepted compatible temperature field or physical thermal qualification.",
            "source": "docs/wo03-elmer-campaign-decision.md",
        },
        {
            "id": "PHYSICAL",
            "status": "open",
            "title": "Root, flutter and recovery remain open",
            "detail": "Installed fin root, flutter, recovery load path and physical tests remain unresolved.",
            "source": "docs/STATUS.md",
        },
    ]
    data["analysis_status"] = {
        "status": "unavailable",
        "compatible_runs": 0,
        "detail": "No accepted compatible stress or temperature field is attached to this archived snapshot.",
    }
    rows = {r["id"]: r for r in snapshot.manifest["parts"]}
    for p in data["parts"]:
        p["mesh_url"] = f"/api/vehicles/{ALIAS}/meshes/{p['id']}.glb"
        p["source"][
            "spec_path"
        ] = "runs/wo03-g80-staged-retention-20261101-v1/resolved-candidate.yaml"
        p["source"]["spec_inputs"] = []
        row = rows[p["id"]]
        # Service generator geometry uses an accounting envelope, not a part's physical dimensions.
        if p["source"]["cad_generator"] == "g80_keeper_service":
            p["dimensions"] = {}
            p["cad_bounding_size_mm"] = row["bbox_mm"]
    published = json.loads(RECORD.read_text())
    if (
        abs(data["summary"]["nominal_mass_kg"] - published["stage1"]["states"][0]["mass_kg"])
        > 1e-12
        or abs(data["summary"]["cg_m"] - published["stage1"]["states"][0]["cg_station_m"]) > 1e-12
    ):
        raise ValueError("Snapshot mass/CG differs from published candidate record")
    mass = []
    for n in range(21):
        fraction = n / 20
        prop = mass_properties(snapshot.vehicle, fraction)
        cp = data["summary"]["cp_m"]
        mass.append(
            {
                "burn_fraction": fraction,
                "mass_kg": prop.mass_kg,
                "cg_m": prop.cg_m,
                "cp_m": cp,
                "stability_margin_cal": (cp - prop.cg_m)
                / snapshot.vehicle.airframe["body_diameter_m"],
                "inertia_kg_m2": prop.inertia_kg_m2.tolist(),
                "identity": snapshot.identity.model_dump(),
                "growth_allowance_included": False,
                "flight_ready": False,
            }
        )
    output.write_text(json.dumps({"data": data, "mass": mass}, allow_nan=False, indent=2) + "\n")


def main() -> None:
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(Path(sys.argv[2]), Path(sys.argv[3]))
        return
    record = json.loads(RECORD.read_text())
    manifest = json.loads((SOURCE / "manifest.json").read_text())
    if (
        record["candidate_identity"] != IDENTITY
        or record["staged_api_cad_revision_sha256"] != CAD
        or digest(SOURCE / "record.json")
        != record["provenance"]["local_source_artifact_sha256"]["stage1_record"]
        or digest(SOURCE / "manifest.json")
        != record["provenance"]["local_source_artifact_sha256"]["stage1_manifest"]
        or digest(SOURCE / "resolved-candidate.yaml")
        != record["provenance"]["packaged_file_source_sha256"]["resolved-candidate.yaml"]
    ):
        raise ValueError("Archived source hashes/identity do not match published record")
    if (
        manifest["identity"]["resolved_spec_sha256"] != IDENTITY
        or manifest["identity"]["cad_revision_sha256"] != CAD
        or len(manifest["parts"]) != 72
    ):
        raise ValueError("Archived manifest identity or coverage mismatch")
    with tempfile.TemporaryDirectory(prefix="rocket-candidate-") as directory:
        root = Path(directory)
        shutil.copytree(STAGED / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(STAGED / "configs", root / "configs")
        shutil.copyfile(SOURCE / "resolved-candidate.yaml", root / "candidate.yaml")
        folder = root / "build/modular-performance-v1"
        folder.mkdir(parents=True)
        shutil.copyfile(SOURCE / "manifest.json", folder / "manifest.json")
        (folder / "parts").mkdir()
        for row in manifest["parts"]:
            name = row["id"]
            if not name.replace("_", "").isalnum() or row["mesh"] != f"parts/{name}.glb":
                raise ValueError("Unsafe mesh identity")
            shutil.copyfile(SOURCE / row["mesh"], folder / row["mesh"])
        output = root / "projection.json"
        subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--worker", str(root), str(output)],
            cwd=root,
            check=True,
        )
        projection = json.loads(output.read_text())
        target = DEST.with_name(DEST.name + "-preparing")
        if target.exists() or DEST.exists():
            raise FileExistsError("Snapshot already exists; preserve it and choose a fresh output")
        target.mkdir(parents=True)
        shutil.copytree(folder / "parts", target / "parts")
        shutil.copyfile(output, target / "projection.json")
        hashes = {r["id"]: digest(target / "parts" / f"{r['id']}.glb") for r in manifest["parts"]}
        index = {
            "candidate_identity": IDENTITY,
            "cad_revision_sha256": CAD,
            "published_record_sha256": digest(RECORD),
            "source_manifest_sha256": digest(SOURCE / "manifest.json"),
            "source_resolved_sha256": digest(SOURCE / "resolved-candidate.yaml"),
            "projection_sha256": digest(target / "projection.json"),
            "mesh_sha256": hashes,
        }
        (target / "index.json").write_text(json.dumps(index, indent=2) + "\n")
        if len(projection["data"]["parts"]) != 72:
            raise ValueError("Incomplete projection")
        target.rename(DEST)
        print(
            json.dumps(
                {
                    "directory": str(DEST),
                    "index_sha256": digest(DEST / "index.json"),
                    "projection_sha256": index["projection_sha256"],
                    "part_count": len(hashes),
                }
            )
        )


if __name__ == "__main__":
    main()
