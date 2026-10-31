"""Register an existing compatible offline analysis for the local read-only API.

Copies immutable recorded artifacts; never relabels identity or launches a solve.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.records import AnalysisRecord, Identity, load_compatible


def register(source: Path, build: Path) -> Path:
    source = source.resolve(strict=True)
    record = AnalysisRecord.model_validate_json(source.read_bytes())
    folder = (build / record.identity.configuration_id).resolve(strict=True)
    if not folder.is_relative_to(build.resolve()):
        raise ValueError("Configuration directory escapes build root")
    cad = json.loads((folder / "manifest.json").read_text())
    identity = Identity.model_validate(cad["identity"])
    load_compatible(source, identity)
    target = folder / "analysis" / record.run_id
    if target.exists():
        existing = target / "manifest.json"
        if existing.read_bytes() != source.read_bytes():
            raise ValueError("Refusing to overwrite a different recorded analysis identity")
        load_compatible(existing, identity)
        return existing
    target.mkdir(parents=True)
    # Only manifest-declared, hash-checked artifacts are exposed by the API.
    for name in {field.artifact for field in record.fields if field.artifact}:
        origin = source.parent / name
        if not origin.resolve(strict=True).is_relative_to(source.parent):
            raise ValueError("Analysis artifact escapes source directory")
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(origin, destination)
    shutil.copyfile(source, target / "manifest.json")
    load_compatible(target / "manifest.json", identity)
    (target / "registration-source.json").write_text(
        json.dumps(
            {
                "source_manifest": str(source),
                "source_manifest_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                "identity_unchanged": True,
                "new_computation_performed": False,
                "flight_ready": False,
            },
            indent=2,
        )
        + "\n"
    )
    return target / "manifest.json"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifests", nargs="+", type=Path)
    parser.add_argument("--build", type=Path, default=Path("build"))
    args = parser.parse_args()
    for source in args.manifests:
        print(register(source, args.build))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
