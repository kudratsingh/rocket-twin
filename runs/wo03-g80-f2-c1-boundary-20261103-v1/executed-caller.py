"""One declared boundary-only fine-grid correction; reuse valid prior grids."""

from __future__ import annotations

import json
import os
import resource
import sys
import time
from pathlib import Path

os.environ.update(OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts import wo03_f2_c1_ring as core

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/wo03-f2-c1-boundary-pilot-v1"
OLD = ROOT / "runs/wo03-g80-f2-c1-method-20261103-v1/record.json"

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
    start = time.monotonic()
    failure = None
    fine = None
    previous = json.loads(OLD.read_text())
    known = core.known_answer()
    if core.digest(core.SPEC) != core.EXPECTED_SPEC or core.digest(core.STEP) != core.EXPECTED_STEP:
        raise ValueError("frozen source changed")
    core.PARTITION_KIND = "boundary"
    try:
        fine = core.solve(1.4, 69, OUT)
    except (ValueError, RuntimeError, OSError, KeyError) as error:
        failure = repr(error)
    reports = previous["reports"] + ([fine] if fine else [])
    refinement = {}
    if len(reports) == 3:
        for i, name in enumerate(["seventy_thirty", "single_anchor"]):
            a, b = reports[-2]["cases"][i], reports[-1]["cases"][i]
            change = {
                k: abs(b[k] / a[k] - 1)
                for k in [
                    "maximum_displacement_mm",
                    "absolute_principal_volume_p95_MPa",
                    "absolute_principal_max_MPa",
                ]
            }
            change["displacement_pass"] = change["maximum_displacement_mm"] <= 0.05
            change["regional_stress_pass"] = change["absolute_principal_volume_p95_MPa"] <= 0.10
            change["peak_stress_pass"] = change["absolute_principal_max_MPa"] <= 0.10
            refinement[name] = change
    record = {
        "identity": "G80-F2-C1-boundary-only-replan-v1",
        "source_spec_sha256": core.digest(core.SPEC),
        "source_STEP_sha256": core.digest(core.STEP),
        "source_sha256": {
            str(p.relative_to(ROOT)): core.digest(p)
            for p in [
                Path(__file__),
                Path(core.__file__),
                OLD,
                ROOT / "docs/wo03-g80-f2-c1-method-replan.md",
            ]
        },
        "known_answer": known,
        "reports": reports,
        "failure": failure,
        "refinement": refinement,
        "wall_s": time.monotonic() - start,
        "prior_wall_s": previous["wall_s"],
        "installed_strength_accepted": False,
        "method_refinement_pass": len(reports) == 3
        and all(
            c["displacement_pass"] and c["regional_stress_pass"] and c["peak_stress_pass"]
            for c in refinement.values()
        ),
        "scope": "same hypothetical component fixture on independently generated non-nested grids; no physical joint capacity or actual vehicle load allocation",
    }
    (OUT / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "failure": failure,
                "wall_s": record["wall_s"],
                "nodes": fine["quality"]["nodes"] if fine else None,
                "refinement": refinement,
            }
        )
    )
    raise SystemExit(bool(failure))
