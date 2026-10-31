"""Prepare an explicitly reconciled actual-CAD radiation screening operator.

No rays, geometry, temperatures or limits are changed. Raw multinomial counts
remain authoritative. Bonferroni-adjusted marginal Clopper-Pearson intervals
check whether the reconciliation lies within conservative simultaneous sampling
intervals. This is not local convergence or a bound on transient temperature.
"""

from __future__ import annotations

import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from scipy.stats import beta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.engineering import material_profile
from src.analysis.finite_radiation import condense_radiosity, reciprocal_enclosure
from src.analysis.radiation_sampling import reciprocal_counts
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def simultaneous_intervals(hits: Any, counts: Any, family_alpha: float) -> tuple[Any, Any]:
    """Exact binomial marginals, Bonferroni over all ordered ray pairs."""
    hits = np.asarray(hits)
    counts = np.asarray(counts)
    if (
        hits.ndim != 2
        or hits.shape[0] != hits.shape[1]
        or counts.shape != (len(hits),)
        or counts.dtype.kind not in "iu"
        or hits.dtype.kind not in "iu"
        or np.any(counts <= 0)
        or np.any(hits < 0)
        or not np.array_equal(hits.sum(axis=1), counts)
        or not 0 < family_alpha < 1
    ):
        raise ValueError("Closed integer count matrix and family alpha in(0,1) required")
    tail = family_alpha / (2 * hits.size)
    n = np.broadcast_to(counts[:, None], hits.shape)
    lower, upper = np.zeros(hits.shape), np.ones(hits.shape)
    positive = hits > 0
    below_all = hits < n
    lower[positive] = beta.ppf(tail, hits[positive], n[positive] - hits[positive] + 1)
    zero = hits == 0
    upper[zero] = -np.expm1(np.log(tail) / n[zero])
    mid = positive & below_all
    upper[mid] = beta.ppf(1 - tail, hits[mid] + 1, n[mid] - hits[mid])
    return lower, upper


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-cad-radiosity.yaml"
    )
    parser.add_argument("--preset", choices=("tiny", "sim", "rl", "real"), default="tiny")
    args = parser.parse_args()
    started = time.perf_counter()
    cfg = yaml.safe_load(args.config.read_text())
    paths = {
        key: ROOT / cfg[key]
        for key in ("ray_operator", "surface_groups", "candidate", "engineering")
    }
    for key, expected in cfg["expected_sha256"].items():
        if sha(paths[key]) != expected:
            raise ValueError("Pinned radiation input changed: " + key)
    hashes = {
        str(p.relative_to(ROOT)): sha(p)
        for p in [
            args.config,
            Path(__file__),
            ROOT / "src/analysis/finite_radiation.py",
            ROOT / "src/analysis/radiation_sampling.py",
            *paths.values(),
        ]
    }
    vehicle = Vehicle.model_validate_json(paths["candidate"].read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != cfg["candidate_identity"]:
        raise ValueError("Candidate identity mismatch")
    groups = json.loads(paths["surface_groups"].read_text())
    raw = np.load(paths["ray_operator"])
    hits, counts = raw["hits"], raw["counts"]
    view, area = raw["raw_view_factors"], raw["group_area_m2"]
    if not np.array_equal(np.arange(len(groups)), [g["group_id"] for g in groups]):
        raise ValueError("Radiative groups are not in exact source order")
    if not np.array_equal(view, hits / counts[:, None]):
        raise ValueError("Raw view factors disagree with raw integer counts")
    unweighted, unweighted_projection = reciprocal_enclosure(view, area)
    lower, upper = simultaneous_intervals(hits, counts, cfg["sampling_family_alpha"])
    tolerance = 1e-12
    old_bad = (unweighted < lower - tolerance) | (unweighted > upper + tolerance)
    unweighted_failure = {
        "projection": unweighted_projection,
        "entries_outside_simultaneous_intervals": int(old_bad.sum()),
        "largest_interval_exceedance": float(
            np.maximum(lower - unweighted, unweighted - upper).max()
        ),
        "rejected_for_transient_use": bool(old_bad.any()),
        "affected_directed_pairs": [
            {
                "source_group": int(i),
                "target_group": int(j),
                "raw": float(view[i, j]),
                "reconciled": float(unweighted[i, j]),
                "lower": float(lower[i, j]),
                "upper": float(upper[i, j]),
            }
            for i, j in np.argwhere(old_bad)
        ],
    }
    balanced, projection = reciprocal_counts(hits, area)
    incompatible = (balanced < lower - tolerance) | (balanced > upper + tolerance)
    no_new_zero_pair = not np.any((hits == 0) & (hits.T == 0) & (balanced != 0))
    compatibility = {
        "method": "Bonferroni simultaneous Clopper-Pearson binomial marginal intervals over all ordered pairs",
        "family_alpha": cfg["sampling_family_alpha"],
        "ordered_pairs": int(hits.size),
        "projection_entries_outside_intervals": int(incompatible.sum()),
        "maximum_interval_exceedance": float(np.maximum(lower - balanced, balanced - upper).max()),
        "largest_interval_width": float((upper - lower).max()),
        "simultaneous_intervals_do_not_establish_local_convergence": True,
        "no_positive_pair_with_zero_hits_in_both_directions": no_new_zero_pair,
        "raw_counts_and_view_factors_unchanged": True,
    }
    if incompatible.any() or not no_new_zero_pair:
        raise ValueError("Projected operator is incompatible with declared sampling intervals")
    material = yaml.safe_load(paths["engineering"].read_text())["materials"]
    parts = {p.id: p for p in vehicle.parts}
    run_id = "wo03-cad-radiosity-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    output = ROOT / "runs" / run_id
    output.mkdir()
    for path in hashes:
        target = output / "source-snapshot" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / path).read_bytes())
    np.savez_compressed(
        output / "reconciled-enclosure.npz",
        reciprocal_view_factors=balanced,
        group_area_m2=area,
        raw_view_factors=view,
        hits=hits,
        counts=counts,
        interval_lower=lower,
        interval_upper=upper,
    )
    rows = []
    for foil in cfg["foil_emissivities"]:
        emissivities = []
        for g in groups:
            if g["reservoir"]:
                emissivities.append(1.0)
                continue
            p = parts[g["part_id"]]
            if p.material.lower() == "aluminum":
                emissivities.append(float(foil))
            else:
                profile = material[material_profile(p)]
                value = profile.get("surface_emissivity", cfg["unlisted_surface_emissivity"])
                if isinstance(value, list):
                    raise ValueError(
                        "Scenario-dependent emissivity needs an explicit scenario mapping"
                    )
                emissivities.append(float(value))
        operator = condense_radiosity(
            balanced, area, emissivities, [f"surface_{g['group_id']}" for g in groups]
        )
        path = output / f"foil-{foil:.1f}-operator.npz"
        np.savez_compressed(
            path,
            inward_w_k4=operator.inward_operator_w_k4,
            group_area_m2=area,
            emissivity=np.array(emissivities),
            group_ids=np.arange(len(groups)),
        )
        rows.append(
            {
                "foil_emissivity": foil,
                "operator": str(path.relative_to(ROOT)),
                "operator_sha256": sha(path),
                "algebra_checks": operator.checks,
                "isothermal_heat_max_w": float(
                    np.abs(operator.heat_rates(np.full(len(groups), 350))).max()
                ),
            }
        )
    record = {
        "run_id": run_id,
        "candidate_identity": identity,
        "cad_revision_sha256": cfg["cad_revision_sha256"],
        "input_sha256": hashes,
        "inputs_unchanged": all(sha(ROOT / p) == h for p, h in hashes.items()),
        "sampling_consistency": compatibility,
        "projection": projection,
        "rejected_unweighted_projection": unweighted_failure,
        "operators": rows,
        "scope": {
            "screening_operator_only": True,
            "measured_or_spatially_converged": False,
            "temperature_solve": False,
            "active_adoption": False,
            "thermal_acceptance": False,
            "flight_ready": False,
        },
        "elapsed_s": time.perf_counter() - started,
        "cpu_workers": 1,
        "cost_usd": 0,
    }
    (output / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "record": str((output / "record.json").relative_to(ROOT)),
                "sampling_consistency": compatibility,
                "elapsed_s": record["elapsed_s"],
            }
        )
    )
    return 0 if record["inputs_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
