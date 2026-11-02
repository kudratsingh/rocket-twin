"""Regression for the archived S2 first-pair failure and JSON output stop."""

import importlib.util
import json
from pathlib import Path

import numpy as np


def study_module():
    path = Path(__file__).resolve().parents[1] / "scripts/wo03_g80_saddle_study.py"
    spec = importlib.util.spec_from_file_location("saddle_study", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_first_refinement_cannot_be_hidden_by_passing_final_pair():
    root = Path(__file__).resolve().parents[1]
    raw = json.loads((root / "runs/wo03-g80-saddle-study-20261102-v2/record.json").read_text())
    report = study_module().quadrature_report(raw["quadrature"], 0.00185, 0.05)
    assert report["pass"] is False
    assert report["adjacent_pair_mass_change_g"]["32_to_64"]["fore"] > 0.05
    assert all(x < 0.05 for x in report["adjacent_pair_mass_change_g"]["64_to_128"].values())


def test_numpy_output_scalars_have_plain_json_representations():
    assert json.loads(
        json.dumps(
            {"pass": np.bool_(True), "mass": np.float64(0.5)}, default=study_module().json_scalar
        )
    ) == {"pass": True, "mass": 0.5}
