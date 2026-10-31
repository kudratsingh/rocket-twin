"""Recorded actual-CAD common-surface transient: explicit PART-MEAN diagnostic.

Calls the existing thermal-topology integrator. Corresponding legacy opaque gas
paths are replaced, solid contacts/capacities stay once, and actual CAD gas and
radiation are coupled behind material half walls. Nominal-property factors and
part-mean sharing do not qualify local hot spots or the full required matrix.
"""

from __future__ import annotations

import os

for _name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_name] = "1"

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_finite_transient import candidate_topology
from scripts.wo03_thermal_matrix import case_config
from src.analysis.cad_gas_surface_adapter import CadGasSurfaceAdapter
from src.analysis.gas_radiation import GasRadiationNetwork
from src.analysis.recorded_gas import RecordedGasResponse
from src.analysis.thermal_topology import run_thermal_topology
from src.vehicle.schema import Vehicle

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")


def setup_topology(
    base: dict[str, Any],
    vehicle: Vehicle,
    parent_nodes: set[str],
    source: dict[str, Any],
    contact: float,
) -> dict[str, Any]:
    """Retain existing explicit contact assumptions; add declared baffle stacks.

    This preserves the previous lumped solid-contact approximation, not a new
    proof of contact wetting, stiffness or local solid spreading. Gas/radiation
    through occupied contact volumes is separately absent in the actual void.
    """
    study = candidate_topology(base, vehicle, contact)
    parts = {p.id: p for p in vehicle.parts}
    study["part_ids"] = list(
        dict.fromkeys([*study["part_ids"], *sorted(parent_nodes & parts.keys())])
    )
    for stack in source["contact_ledger"]:
        path = stack["path"]
        for name in path[1:-1]:
            if name not in parts:
                raise ValueError("Baffle contact stack names a missing actual part")
            study["pad_conduction_part_ids"].append(name)
            study["pad_conduction_thickness_m"][name] = parts[name].geometry["length_m"]
        for a, b in pairwise(path):
            if [a, b] in study["contact_pairs"] or [b, a] in study["contact_pairs"]:
                raise ValueError("Duplicate baffle solid-contact allocation")
            study["contact_pairs"].append([a, b])
            study["contact_pair_conductance_w_k"][f"{a}->{b}"] = contact
    # Newly exposed actual fin tabs exchange through the gas domain. The old
    # potting/body contact remains once; add one explicit potting/fin bulk link.
    if "fin_set" in parent_nodes and "fin_bonds" in parts:
        study["contact_pairs"].append(["fin_bonds", "fin_set"])
    study["pad_conduction_part_ids"] = list(dict.fromkeys(study["pad_conduction_part_ids"]))
    return study


def worker(config: Path, folder: Path, args: Any) -> int:
    started = time.perf_counter()
    config = config.resolve(strict=True)
    cfg = yaml.safe_load(config.read_text())
    paths = {
        k: ROOT / cfg[k]
        for k in [
            "factor_record",
            "gas_operator",
            "gas_metadata",
            "parent_map",
            "candidate",
            "candidate_record",
            "surface_groups",
            "acceptance_matrix",
            "engineering",
            "topology",
            "construction",
            "radiosity_record",
        ]
    }
    factor_record = json.loads(paths["factor_record"].read_text())
    if not factor_record.get("inputs_unchanged"):
        raise ValueError("Actual source factor input-identity verification is not complete")
    failed_gas_checks = not factor_record.get("numerical_checks_pass")
    if failed_gas_checks and not args.investigate_failed_operator:
        raise ValueError(
            "Actual gas field checks failed; ordinary transient execution remains blocked"
        )
    if not factor_record.get("native_successful_factor_available"):
        raise ValueError(
            "A complete actual response operator is unavailable; partial maps are forbidden"
        )
    artifact_hashes = {a["path"]: a["sha256"] for a in factor_record.get("artifacts", [])}
    for key in ("gas_operator", "gas_metadata"):
        relative = str(paths[key].relative_to(ROOT))
        if artifact_hashes.get(relative) != sha(paths[key]):
            raise ValueError("Gas cache is not the exact artifact in the checked source record")
    gas = RecordedGasResponse.load(
        paths["gas_operator"],
        paths["gas_metadata"],
        operator_sha256=sha(paths["gas_operator"]),
        metadata_sha256=sha(paths["gas_metadata"]),
    )
    source = json.loads(paths["candidate_record"].read_text())
    vehicle = Vehicle.model_validate_json(paths["candidate"].read_bytes())
    identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
    if identity != source["candidate_identity"] or identity != cfg["candidate_identity"]:
        raise ValueError("Actual resolved vehicle identity mismatch")
    parent_data = json.loads(paths["parent_map"].read_text())
    gas_metadata = json.loads(paths["gas_metadata"].read_text())
    source_hashes = factor_record["input_sha256"]
    if gas_metadata["input_sha256"] != source_hashes:
        raise ValueError("Gas metadata and source-factor input identities differ")
    if parent_data["source_operator_sha256"] != source_hashes["wall_operator"]:
        raise ValueError("Part projection belongs to a different material-wall operator")
    for key, source_key in (
        ("surface_groups", "groups"),
        ("engineering", "engineering"),
        ("acceptance_matrix", "thermal_acceptance"),
    ):
        if sha(paths[key]) != source_hashes[source_key]:
            raise ValueError("Transient physical inputs differ from the source factor")
    parent = parent_data["component_bulk_parent_map"]
    if set(parent) != set(gas.bulk_ids):
        raise ValueError("Actual gas component states and explicit parent projection disagree")
    groups = json.loads(paths["surface_groups"].read_text())
    if [g["group_id"] for g in groups] != list(gas.group_ids):
        raise ValueError("Optical and gas groups are not the same ordered actual surfaces")
    acceptance = yaml.safe_load(paths["acceptance_matrix"].read_text())
    engineering = yaml.safe_load(paths["engineering"].read_text())
    base = yaml.safe_load(paths["topology"].read_text())
    construction = yaml.safe_load(paths["construction"].read_text())
    radiosity = json.loads(paths["radiosity_record"].read_text())
    if radiosity["candidate_identity"] != identity:
        raise ValueError("Radiation and actual vehicle have incompatible identities")
    rows = [r for r in acceptance["cases"] if r["id"] == args.case]
    if len(rows) != 1:
        raise ValueError("Select one unchanged thermal-matrix source case")
    case = rows[0]
    scenario = case["source_scenario_index"]
    if (
        engineering["thermal"]["air_conductivity_w_m_k"][scenario]
        != gas.diagnostics["conductivity_w_m_k"]
    ):
        raise ValueError("This case needs its own gas-conductivity factor; reuse is incompatible")
    corner = next(
        c for c in acceptance["material_property_uncertainty"]["factors"] if c["id"] == "nominal"
    )
    settings = case_config(engineering, case, None, corner)
    foil = case["outer_foil_emissivity"]
    optical = next(r for r in radiosity["operators"] if r["foil_emissivity"] == foil)
    operator_path = ROOT / optical["operator"]
    if sha(operator_path) != optical["operator_sha256"]:
        raise ValueError("Recorded actual radiation operator changed")
    with np.load(operator_path) as npz:
        c = npz["inward_w_k4"].copy()
        area = npz["group_area_m2"].copy()
    if not np.allclose(area, gas.group_areas_m2, rtol=1e-9, atol=1e-20):
        raise ValueError("Optical and gas surface areas differ; explicit transfer is required")
    names = tuple(dict.fromkeys(g["part_id"] for g in groups if g["reservoir"]))
    index = {n: i for i, n in enumerate(names)}
    network = GasRadiationNetwork(
        gas,
        c,
        tuple(-1 if g["reservoir"] else i for i, g in enumerate(groups)),
        tuple(index[g["part_id"]] if g["reservoir"] else -1 for g in groups),
        names,
        "Original actual-CAD radiation groups use gas-field area means and group-uniform radiation loads; not resolved spatial radiosity",
    )
    prescribed = {}
    metadata = gas.provenance["source_metadata"]
    factor_config = yaml.safe_load((ROOT / cfg["factor_config"]).read_text())
    for name in gas.prescribed_ids:
        if name == factor_config["shared_motor_case_temperature_id"]:
            prescribed[name] = "case"
        elif name == factor_config["ambient_physical_gas_temperature_id"]:
            prescribed[name] = "ambient"
        else:
            raise ValueError("A prescribed physical motor/gas state lacks an explicit hypothesis")
    contact = construction["scope"]["interface_contact_conductance_w_k"]
    study = setup_topology(base, vehicle, set(parent.values()), source, contact)
    adapter = CadGasSurfaceAdapter(
        network,
        parent,
        prescribed,
        {n: args.brightness for n in names},
        {
            "candidate_identity": identity,
            "cad_revision_sha256": source["cad_revision_sha256"],
            "factor": str(paths["factor_record"].relative_to(ROOT)),
            "source_factor_metadata": metadata,
            "solid_contacts": "existing part-lumped links plus explicitly declared four-link baffle stacks; physical contact/spreading uncertainty remains",
            "new_fin_bulk_contact": "one fin_bonds to fin_set lumped link; complete fin-part capacity, not local tab temperature",
            "liner_axial_resolution": "one axial cell with16radial cells, end path L/2; not axial convergence",
            "radiative_opening_brightness_mode": args.brightness,
        },
        absolute_tolerance_k=cfg["surface_tolerance_k"],
    )
    inputs = [
        config,
        Path(__file__),
        *paths.values(),
        operator_path,
        ROOT / cfg["factor_config"],
        ROOT / "src/analysis/cad_gas_surface_adapter.py",
        ROOT / "src/analysis/gas_radiation.py",
        ROOT / "src/analysis/recorded_gas.py",
        ROOT / "src/analysis/thermal_topology.py",
        ROOT / "src/analysis/thermal_radial.py",
        ROOT / "scripts/wo03_finite_transient.py",
        ROOT / "scripts/wo03_thermal_matrix.py",
    ]
    hashes = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    for p, h in hashes.items():
        target = folder / "source-snapshot" / p
        target.parent.mkdir(parents=True, exist_ok=True)
        raw = (ROOT / p).read_bytes()
        if hashlib.sha256(raw).hexdigest() != h:
            raise ValueError("Input changed during snapshot")
        target.write_bytes(raw)
    write(
        folder / "progress.json",
        {
            "phase": "executing_existing_transient_integrator",
            "candidate_identity": identity,
            "case": case,
            "brightness": args.brightness,
            "material_corner": "nominal_only",
            "failed_gas_operator_investigation": failed_gas_checks,
        },
    )
    output = run_thermal_topology(
        vehicle,
        settings,
        study,
        int(scenario),
        cells=16,
        max_step_s=args.max_step_s,
        scenario_index=scenario,
        heat_flow_step_s=cfg["heat_flow_step_s"],
        surface_exchange=adapter,
    )
    write(folder / "thermal-results.json", output)
    record = {
        "run_id": folder.name,
        "candidate_identity": identity,
        "cad_revision_sha256": source["cad_revision_sha256"],
        "case": case,
        "material_corner": "nominal",
        "mode": (
            "INVESTIGATION_OF_FAILED_GAS_OPERATOR"
            if failed_gas_checks
            else "PROVISIONAL_COARSE_DIAGNOSTIC"
        ),
        "source_gas_numerical_checks_pass": not failed_gas_checks,
        "temperature_prediction_credible": False,
        "temperature_acceptance": (
            "unavailable_due_to_failed_source_numerics"
            if failed_gas_checks
            else "unavailable_pending_refinement"
        ),
        "source_field_check_failures_retained": factor_record.get("field_checks", []),
        "source_air_conductivity_w_m_k": gas.diagnostics["conductivity_w_m_k"],
        "physical_motor_end_aliases": metadata["physical_boundary_alias_table"],
        "opening_radiative_brightness": args.brightness,
        "input_sha256": hashes,
        "inputs_unchanged": all(sha(ROOT / p) == h for p, h in hashes.items()),
        "output": "thermal-results.json",
        "output_sha256": sha(folder / "thermal-results.json"),
        "part_average_peaks": output["peaks"],
        "surface_adapter": adapter.metadata(),
        "scope": {
            "actual_geometry_fixed_neutral_G54_only": True,
            "existing_part_mean_solid_projection": True,
            "local_solid_hot_spots": "unavailable",
            "full_required_case_material_gap_contact_matrix_complete": False,
            "gas_spatial_convergence": False,
            "optical_local_convergence": False,
            "material_quadrature_convergence": False,
            "active_adoption": False,
            "thermal_acceptance": False,
            "flight_ready": False,
        },
        "elapsed_s": time.perf_counter() - started,
        "cost_usd": 0,
    }
    write(folder / "record.json", record)
    print(
        json.dumps(
            {
                "record": str((folder / "record.json").relative_to(ROOT)),
                "elapsed_s": record["elapsed_s"],
            }
        )
    )
    return 0 if record["inputs_unchanged"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=ROOT / "configs/studies/wo03-actual-transient.yaml"
    )
    parser.add_argument("--case", default="combined_300C_eps09_at35C")
    parser.add_argument("--brightness", choices=("ambient", "case"), default="ambient")
    parser.add_argument("--max-step-s", type=float, default=1.0)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument(
        "--investigate-failed-operator",
        action="store_true",
        help="Explicit debug-only transient of a complete operator with failed field checks; never a credible prediction or acceptance result",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.worker:
        assert args.output is not None
        return worker(args.config, args.output, args)
    cfg = yaml.safe_load(args.config.read_text())
    run_id = "wo03-actual-transient-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    folder = ROOT / "runs" / run_id
    folder.mkdir()
    cmd = [
        sys.executable,
        str(Path(__file__)),
        "--config",
        str(args.config),
        "--case",
        args.case,
        "--brightness",
        args.brightness,
        "--max-step-s",
        str(args.max_step_s),
        "--worker",
        "--output",
        str(folder),
    ]
    if args.investigate_failed_operator:
        cmd.append("--investigate-failed-operator")
    started = time.perf_counter()
    time_capped = False
    with (folder / "worker.log").open("w") as log:
        try:
            result = subprocess.run(
                cmd, stdout=log, stderr=subprocess.STDOUT, timeout=cfg["child_seconds"], check=False
            )
            code = result.returncode
        except subprocess.TimeoutExpired:
            time_capped = True
            code = -1
    if code or not (folder / "record.json").is_file():
        write(
            folder / "record.json",
            {
                "run_id": run_id,
                "status": (
                    "INCOMPLETE_TIME_LIMIT"
                    if time_capped
                    else "EXECUTION_ERROR_NO_TRANSIENT_RESULT"
                ),
                "calculation_completion": "incomplete",
                "numerical_accuracy": "unestablished_for_incomplete_attempt; consult_source_factor_record",
                "temperature_acceptance": "unavailable",
                "source_gas_failed_operator_investigation": args.investigate_failed_operator,
                "exit_code": code,
                "elapsed_s": time.perf_counter() - started,
                "worker_log": "worker.log",
                "thermal_acceptance": False,
                "flight_ready": False,
            },
        )
    print(folder / "record.json")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
