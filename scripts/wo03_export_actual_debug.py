"""Export recorded FAILED-operator debug histories, never an acceptance pass."""

from __future__ import annotations

import os

os.environ.setdefault("MPLCONFIGDIR", ".cache/matplotlib")

import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analysis.records import AnalysisRecord, export_record, load_compatible
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    path = args.record.resolve(strict=True)
    run = json.loads(path.read_bytes())
    if run.get("mode") != "INVESTIGATION_OF_FAILED_GAS_OPERATOR" or not run["inputs_unchanged"]:
        raise ValueError(
            "This exporter requires an unchanged, explicitly failed-operator investigation"
        )
    output = path.parent / run["output"]
    if sha(output) != run["output_sha256"]:
        raise ValueError("Recorded transient output changed")
    result = json.loads(output.read_bytes())
    candidate_key = next(k for k in run["input_sha256"] if k.endswith("resolved-candidate.json"))
    candidate = path.parent / "source-snapshot" / candidate_key
    if sha(candidate) != run["input_sha256"][candidate_key]:
        raise ValueError("Recorded vehicle snapshot changed")
    vehicle = Vehicle.model_validate_json(candidate.read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != run["candidate_identity"]:
        raise ValueError("Candidate identity mismatch")
    source_case = run["case"]
    case_id = source_case["id"]
    case_description = (
        f"Candidate {identity}; source case {case_id}; nominal material properties. "
        f"Prescribed case peak {result['prescribed_case_peak_c']}°C; "
        f"foil emissivity {source_case['outer_foil_emissivity']}; "
        f"ambient {result['ambient_c']}°C. "
        f"Opening radiative brightness: {run['opening_radiative_brightness']}."
    )
    shapes = {p.id: p.cad_mass.shape_sha256 for p in vehicle.parts if p.cad_mass is not None}
    payload = {"values": result["temperature_k"]}
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False).encode() + b"\n"
    evidence = {
        "provenance": "calculated",
        "validation": "failed",
        "known_case_verified": False,
        "mesh_converged": False,
        "assumptions": [
            case_description,
            "Part-average solid projection with16radial liner cells; one axial liner cell.",
            "Motor fore/cylinder/aft share an explicitly assumed case-temperature history.",
        ],
        "limits": [
            "Source gas operator has gross maximum-principle violations and failed field checks.",
            "These are debug computed values, not credible design temperatures or acceptance evidence.",
            "No spatial/time-step convergence or qualified local solid hot spots.",
            "Global ODE ledger and local heat-route quadrature have different verification status.",
        ],
        "sources": [str(path.relative_to(ROOT)), str(output.relative_to(ROOT))],
        "uncertainty": "Uncontrolled spatial/source-operator error; estimated material/contact/case inputs; no defensible temperature error bar.",
        "required_physical_tests": [
            "Instrumented case/substrate/bonds after numerical/design acceptance."
        ],
        "report": "docs/wo03-actual-debug-transient.md",
    }
    field = {
        "id": "failed-operator-debug-part-temperatures",
        "case_id": case_id,
        "quantity": "temperature",
        "component": "DEBUG part mean from failed gas operator; not a physical prediction",
        "units": "K",
        "association": "part",
        "part_ids": result["part_ids"],
        "times_s": result["times_s"],
        "artifact": "debug-part-temperatures.json",
        "artifact_sha256": hashlib.sha256(encoded).hexdigest(),
        "sample_count": len(result["part_ids"]),
        "evidence": evidence,
        "coverage_notes": "Calculated values exist at part-mean resolution only. Failed validation is mandatory; no green acceptance interpretation.",
        "reported_extrema": {
            "debug_part_mean_peaks_c": [
                {k: r[k] for k in ["part_id", "peak_c", "peak_time_s"]} for r in result["peaks"]
            ]
        },
    }
    missing = sorted(set(shapes) - set(result["part_ids"]))
    fields = [field]
    if missing:
        fields.append(
            {
                "id": "missing-part-temperature",
                "case_id": case_id,
                "quantity": "temperature",
                "component": "No recorded thermal state",
                "units": "K",
                "association": "part",
                "part_ids": missing,
                "sample_count": 0,
                "unavailable_reason": "No temperature state; no ambient/zero substitute.",
                "coverage_notes": "Unavailable coverage, separate from failed calculated data.",
                "evidence": {
                    **evidence,
                    "provenance": "unavailable",
                    "validation": "unavailable",
                    "known_case_verified": False,
                },
            }
        )
    record = AnalysisRecord.model_validate(
        {
            "run_id": run["run_id"],
            "identity": {
                "configuration_id": vehicle.id,
                "resolved_spec_sha256": identity,
                "cad_revision_sha256": run["cad_revision_sha256"],
                "part_shape_sha256": shapes,
            },
            "cases": {
                case_id: {
                    "mode": run["mode"],
                    "source_case": run["case"],
                    "temperature_acceptance": "unavailable_due_to_failed_source_numerics",
                    "credible_prediction": False,
                    "substrate_screen_c": 45,
                    "gas_source_field_checks_pass": False,
                }
            },
            "fields": fields,
            "tools": {"producer": "offline_recorded_debug_export_no_new_solve"},
            "input_sha256": {
                str(path.relative_to(ROOT)): sha(path),
                str(output.relative_to(ROOT)): sha(output),
            },
        }
    )
    folder = path.parent / "analysis-debug"
    manifest = export_record(folder, record, {"debug-part-temperatures.json": payload})
    load_compatible(manifest, record.identity)
    values = np.asarray(result["temperature_k"]) - 273.15
    ids = result["part_ids"]
    times = np.asarray(result["times_s"])
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), facecolor="#f5f6f8")
    for name in ["motor_mount", "aft_shell"]:
        axes[0].plot(
            times,
            values[:, ids.index(name)],
            label="Wooden motor support" if name == "motor_mount" else "Aft body substrate",
            lw=2,
        )
    axes[0].axhline(45, color="#b51f36", ls="--", label="45°C project screen")
    axes[0].set_title("Debug substrate means — acceptance unavailable")
    axes[0].set_ylabel("Computed part-average temperature (°C)")
    for suffix, label, color in [
        ("", "Foil panels", "#25748e"),
        ("_foil_bond", "Foil-side adhesive", "#b76b2f"),
    ]:
        subset = [
            i
            for i, n in enumerate(ids)
            if n.startswith("fitting_baffle_")
            and ((not suffix and n.endswith(("front", "aft"))) or (suffix and n.endswith(suffix)))
        ]
        band = values[:, subset]
        axes[1].fill_between(times, band.min(axis=1), band.max(axis=1), color=color, alpha=0.2)
        axes[1].plot(
            times, band.max(axis=1), color=color, lw=2, label=label + " (range across8 baffles)"
        )
    axes[1].set_title("Debug baffle assembly means")
    axes[1].set_ylabel("Computed part-average temperature (°C)")
    for ax in axes:
        ax.set_xlabel("Time after ignition (s)")
        ax.grid(alpha=0.18)
        ax.legend(fontsize=8)
    fig.suptitle(
        f"FAILED NUMERICAL MODEL — investigation only | candidate {identity[:7]}…",
        color="#a51f32",
        fontsize=13,
    )
    fig.text(
        0.5,
        0.01,
        "No credible temperature prediction: source operator violates temperature bounds; spatial/time refinement and heat-route quadrature remain open.",
        ha="center",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.04, 1, 0.92))
    plot = path.parent / "debug-temperature-history.png"
    fig.savefig(plot, dpi=150)
    plt.close(fig)
    export = {
        "source_record": str(path.relative_to(ROOT)),
        "source_sha256": sha(path),
        "analysis_manifest": str(manifest.relative_to(ROOT)),
        "analysis_manifest_sha256": sha(manifest),
        "compatible_consumer_passed": True,
        "registration_on_active_vehicle": False,
        "plot": str(plot.relative_to(ROOT)),
        "plot_sha256": sha(plot),
        "quantity_resolution": "part_average",
        "validation": "failed",
        "temperature_prediction_credible": False,
        "thermal_acceptance": False,
        "flight_ready": False,
    }
    (path.parent / "debug-export-record.json").write_text(json.dumps(export, indent=2) + "\n")
    print(json.dumps(export))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
