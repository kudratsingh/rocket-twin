"""Prepare only: preserve known B nodal load and request StressSolve stresses."""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-elmer-stress-fixture.yaml"
OUT = ROOT / "build/wo03-elmer-stress-fixture-v2"
ORDER = ("xx", "yy", "zz", "xy", "yz", "xz")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def check_stress(fields, loaded_mask, expected=9_375_000.0):
    """Compare named nodal components; relative scale is explicitly proposed."""
    if set(fields) != set(ORDER):
        raise ValueError("Missing, duplicate, or unexpected stress components")
    mask = np.asarray(loaded_mask, dtype=bool)
    if not mask.any() or mask.all():
        raise ValueError("Both loaded and unloaded nodes required")
    arrays = [np.asarray(fields[k]) for k in ORDER]
    if any(a.dtype != np.float64 for a in arrays):
        raise ValueError("Stress must be Float64")
    actual = np.column_stack(arrays)
    if actual.shape != (len(mask), 6) or not np.isfinite(actual).all():
        raise ValueError("Malformed or nonfinite stress")
    target = np.zeros_like(actual)
    target[mask, 2] = expected
    errors = np.max(np.abs(actual - target), axis=0)
    return {
        "component_order": ORDER,
        "max_abs_error_pa": errors.tolist(),
        "max_error_normalized_by_loaded_axial": float(max(errors) / expected),
        "original_axial_criterion_pass": bool(errors[2] / expected < 0.02),
        "all_components_primary_2pct_scale_pass": bool(max(errors) / expected < 0.02),
    }


def main():
    cfg = yaml.safe_load(CONFIG.read_text())
    if cfg["native_execution_authorized"]:
        raise ValueError("No native execution implemented")
    source = ROOT / cfg["source_prepared"]
    known = ROOT / cfg["source_result"]
    result = json.loads(known.read_text())
    if result["status"] != "single_nodal_rhs_known_answer_pass_not_qualified":
        raise ValueError("Known nodal fixture not passed")
    sources = sorted(ROOT.glob(cfg["stress_source_glob"]))
    if len(sources) != 1:
        raise ValueError("Pinned StressSolve source ambiguous")
    original = (source / "case.sif").read_bytes()
    needle = b"  Calculate Loads = Logical True\n"
    if original.count(needle) != 1:
        raise ValueError("SIF insertion not unique")
    modified = original.replace(needle, needle + b"  Calculate Stresses = Logical True\n")
    if modified.replace(b"  Calculate Stresses = Logical True\n", b"", 1) != original:
        raise ValueError("SIF changed beyond stress request")
    target = OUT / "prepared"
    target.mkdir(exist_ok=False)
    shutil.copytree(source / "mesh", target / "mesh")
    (target / "case.sif").write_bytes(modified)
    solver = ROOT / ".cache/elmer-evaluation/setup-v1/prefix/bin/ElmerSolver"
    module = ROOT / ".cache/elmer-evaluation/structural-module-v1/artifacts/StressSolve.dylib"
    if (
        sha(solver) != "006922a630d1daa404ff1191a39dc33a44aa4b6d0c5bac907f07861db4232d6e"
        or sha(module) != "792f1fd46d06d8b0cf05865a0492237221200fe2d20e96a5698cbf219fc14e1f"
    ):
        raise ValueError("Pinned solver/module mismatch")
    files = [
        solver,
        module,
        CONFIG,
        Path(__file__),
        known,
        sources[0],
        source / "case.sif",
        *sorted((source / "mesh").iterdir()),
    ]
    before = {str(p): sha(p) for p in files}
    assert all(sha(p) == sha(target / "mesh" / p.name) for p in (source / "mesh").iterdir())
    record = {
        "status": "prepared_no_native",
        "source_sha256_before": before,
        "source_sha256_after": {str(p): sha(p) for p in files},
        "prepared_sif_sha256": sha(target / "case.sif"),
        "sif_change": "one Calculate Stresses logical true line",
        "criterion": "existing loaded axial <2%; primary-declared full tensor <2% of loaded axial reference",
        "native_execution_authorized": False,
    }
    (OUT / "preflight.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({"status": record["status"], "sif_sha256": record["prepared_sif_sha256"]}))


if __name__ == "__main__":
    main()
