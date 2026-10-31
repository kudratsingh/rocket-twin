"""Execute installed fin screens for current fixed/TVC flight envelopes.

This driver runs the existing minimum-thickness panel FEA and adds explicit
fin-root/frame/shell demand screens at fresh-record maximum q with a separate
CN=2 sensitivity. It is numerical evidence only; all acceptance remains open.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from datetime import UTC, datetime
from itertools import pairwise
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.wo03_fin_acceptance import (
    ORTHOTROPIC,
    TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION,
    _component_screen,
    _minimum_thickness_copy,
    panel_force_n,
    run_acceptance,
)
from src.analysis.fin_attachment import (
    analyze_fin_attachment,
    fin_flutter_domain_assessment,
    normal_force_coefficient_per_radian,
)
from src.analysis.fin_fea import run_shell
from src.analysis.fin_fields import export_fin_fields
from src.analysis.vibration import flutter_screen
from src.vehicle.schema import Part, load_vehicle, vehicle_input_paths


def _part(vehicle_parts: list[Part], part_type: str, part_id: str | None = None) -> Part:
    found = next(
        (p for p in vehicle_parts if p.type == part_type and (part_id is None or p.id == part_id)),
        None,
    )
    if found is None:
        raise ValueError(f"Required structural part unavailable: type={part_type}, id={part_id}")
    return found


def _hashes(paths: set[Path], root: Path) -> dict[str, str]:
    return {
        path.resolve()
        .relative_to(root.resolve())
        .as_posix(): hashlib.sha256(path.read_bytes())
        .hexdigest()
        for path in sorted(paths)
        if path.is_file()
    }


def _matching_envelopes(vehicle_id: str, flight: dict[str, Any]) -> list[dict[str, Any]]:
    ids = {vehicle_id}
    output = []
    for candidate_id in sorted(ids):
        cases = [c for c in flight.get("cases", []) if c.get("vehicle") == candidate_id]
        if not cases:
            continue
        case = max(cases, key=lambda c: float(c["metrics"]["max_dynamic_pressure_pa"]))
        output.append(case)
    return output


def run_coincident_analysis(
    vehicle_paths: list[Path], flight_record_path: Path, output_root: Path
) -> list[Path]:
    """Extract historical/sim q(t)*CN(alpha) without running structural solvers."""
    root = Path.cwd()
    flight_record_path = (
        flight_record_path if flight_record_path.is_absolute() else root / flight_record_path
    )
    flight = json.loads(flight_record_path.read_text())
    run_id = "wo03-fin-coincident-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    outputs: list[Path] = []
    record_hashes = flight.get("input_sha256", {})
    for supplied in vehicle_paths:
        vehicle_path = supplied if supplied.is_absolute() else root / supplied
        vehicle = load_vehicle(vehicle_path)
        fin = _part(vehicle.parts, "fin_set")
        slope = normal_force_coefficient_per_radian(
            float(fin.geometry["span_m"]),
            float(fin.geometry["root_chord_m"]),
            float(fin.geometry["tip_chord_m"]),
        )
        matching_ids = {vehicle.id}
        candidates = [
            case for case in flight.get("cases", []) if case.get("vehicle") in matching_ids
        ]
        if not candidates:
            raise ValueError(f"No matching flight cases found for {vehicle.id}")
        config_by_vehicle = {
            str(case["vehicle"]): str(case["config"])
            for case in candidates
            if case.get("config") is not None
        }
        inputs = {flight_record_path, vehicle_path, *vehicle_input_paths(vehicle_path)}
        for candidate in candidates:
            candidate_id = str(candidate["vehicle"])
            scenario = candidate.get("scenario")
            inputs.add(
                flight_record_path.parent
                / (f"{candidate_id}-{scenario}.parquet" if scenario else f"{candidate_id}.parquet")
            )
            config_path = candidate.get("config") or config_by_vehicle.get(candidate_id)
            if config_path:
                inputs.add(root / str(config_path))
        hash_before = _hashes(inputs, root)
        case_results = []
        for case in candidates:
            case_id = str(case["vehicle"])
            scenario = case.get("scenario")
            parquet_name = f"{case_id}-{scenario}.parquet" if scenario else f"{case_id}.parquet"
            parquet_path = flight_record_path.parent / parquet_name
            if not parquet_path.is_file():
                case_results.append(
                    {
                        "case_vehicle": case_id,
                        "scenario": scenario,
                        "status": "unavailable",
                        "reason": f"Telemetry file missing: {parquet_name}",
                    }
                )
                continue
            table = pq.read_table(
                parquet_path,
                columns=["time_s", "dynamic_pressure_pa", "alpha_rad", "landed"],
            )
            rows = table.to_pydict()
            n = len(rows["time_s"])
            peak = {
                "qcn_bound_pa": -1.0,
                "time_s": None,
                "q_pa": None,
                "alpha_rad": None,
                "alpha_deg": None,
                "cn_bound": None,
            }
            peak_qcn = -1.0
            max_q = 0.0
            max_speed = float(case.get("metrics", {}).get("max_speed_mps", 0.0))
            alpha_abs_max = 0.0
            landed_rows_excluded = 0
            for index in range(n):
                if float(rows["landed"][index]) > 0.5:
                    landed_rows_excluded += 1
                    continue
                q_pa = max(0.0, float(rows["dynamic_pressure_pa"][index]))
                alpha_rad = abs(float(rows["alpha_rad"][index]))
                alpha_abs_max = max(alpha_abs_max, alpha_rad)
                max_q = max(max_q, q_pa)
                cn_bound = min(slope * alpha_rad, 2.0)
                qcn = q_pa * cn_bound
                if qcn > peak_qcn:
                    peak_qcn = qcn
                    peak = {
                        "qcn_bound_pa": qcn,
                        "time_s": float(rows["time_s"][index]),
                        "q_pa": q_pa,
                        "alpha_rad": alpha_rad,
                        "alpha_deg": alpha_rad * 180 / math.pi,
                        "cn_bound": cn_bound,
                    }
            case_config = case.get("config") or config_by_vehicle.get(case_id)
            config_identity = None
            if case_config and case_config in record_hashes:
                current_path = root / case_config
                config_identity = {
                    "path": case_config,
                    "record_sha256": record_hashes[case_config],
                    "current_sha256": (
                        hashlib.sha256(current_path.read_bytes()).hexdigest()
                        if current_path.is_file()
                        else None
                    ),
                    "matches_current": current_path.is_file()
                    and hashlib.sha256(current_path.read_bytes()).hexdigest()
                    == record_hashes[case_config],
                }
            case_results.append(
                {
                    "case_vehicle": case_id,
                    "scenario": scenario,
                    "parquet_path": parquet_path.resolve().relative_to(root.resolve()).as_posix(),
                    "rows": n,
                    "landed_rows_excluded": landed_rows_excluded,
                    "max_dynamic_pressure_pa": max_q,
                    "record_max_speed_mps": max_speed,
                    "max_abs_alpha_rad": alpha_abs_max,
                    "max_abs_alpha_deg": alpha_abs_max * 180 / math.pi,
                    "coincident_qcn_peak": peak,
                    "full_cartesian_max_q_times_cn2_pa": max_q * 2.0,
                    "flight_config_identity": config_identity,
                    "status": "historical sim-derived load estimate; source identity and aero-force validity are not qualification",
                }
            )
        mode_dir = output_root / vehicle.id / run_id
        mode_dir.mkdir(parents=True, exist_ok=True)
        report = {
            "run_id": run_id,
            "vehicle_id": vehicle.id,
            "source_config": vehicle_path.resolve().relative_to(root.resolve()).as_posix(),
            "resolved_spec_sha256": hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "flight_record_id": flight.get("run_id"),
            "flight_record_path": flight_record_path.resolve()
            .relative_to(root.resolve())
            .as_posix(),
            "flight_record_identity_current": all(
                item.get("flight_config_identity", {}).get("matches_current", False)
                for item in case_results
                if item.get("flight_config_identity") is not None
            ),
            "normal_force_slope_per_radian": slope,
            "coefficient_method": "Finite-aspect-ratio linear small-angle panel slope; estimated comparison only, not a validated aero-force model.",
            "coefficient_bound": 2.0,
            "small_angle_validity": "No calibrated angle-of-attack validity range is established here. Report observed max |alpha|; linear slope outside small angles must not be treated as validated. The CN=2 cap is a sensitivity bound only.",
            "case_results": case_results,
            "status": "historical development evidence only; coincident q(t)*CN(alpha) is model-estimated and does not establish operational structural qualification",
            "acceptance": "open",
            "acceptance_passed": False,
            "flight_ready": False,
            "cost_usd": 0,
            "input_sha256_before": hash_before,
        }
        hash_after = _hashes(inputs, root)
        report["input_sha256_after"] = hash_after
        report["inputs_unchanged"] = hash_before == hash_after
        report_path = mode_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        outputs.append(report_path)
    return outputs


def run_installed(
    vehicle_paths: list[Path],
    flight_record_path: Path,
    output_root: Path,
    panel_report_paths: list[Path] | None = None,
) -> list[Path]:
    root = Path.cwd()
    flight_record_path = (
        flight_record_path if flight_record_path.is_absolute() else root / flight_record_path
    )
    flight = json.loads(flight_record_path.read_text())
    if not flight.get("run_id") or not isinstance(flight.get("cases"), list):
        raise ValueError("Flight record must identify a run and contain cases")
    reports: list[Path] = []
    cached_panel_reports: list[tuple[Path, dict[str, Any]]] = []
    for candidate in panel_report_paths or []:
        candidate_path = candidate if candidate.is_absolute() else root / candidate
        cached_panel_reports.append((candidate_path, json.loads(candidate_path.read_text())))
    for supplied_path in vehicle_paths:
        vehicle_path = supplied_path if supplied_path.is_absolute() else root / supplied_path
        vehicle = load_vehicle(vehicle_path)
        fin = _part(vehicle.parts, "fin_set")
        if fin.material != "plywood":
            raise ValueError(
                f"{vehicle.id}: installed orthotropic plywood model requires plywood fins"
            )
        minimum_thickness_m = float(_minimum_thickness_copy(fin).geometry["thickness_m"])
        frame_id = "gimbal_frame" if vehicle.tvc is not None else "motor_mount"
        frame = next((p for p in vehicle.parts if p.id == frame_id), None)
        shell = _part(vehicle.parts, "body_tube", "aft_shell")
        if frame is None or frame.cad is None or fin.cad is None:
            raise ValueError(f"{vehicle.id}: CAD parameters required for installed geometry")
        fp = dict(frame.cad.parameters)
        finp = dict(fin.cad.parameters)
        engineering_path = root / "configs/engineering/wo03.yaml"
        engineering = yaml.safe_load(engineering_path.read_text())
        materials = engineering["materials"]
        loads_config = engineering["loads"]
        frame_profile = materials.get(frame.material)
        if frame_profile is None or "strength_pa" not in frame_profile:
            raise ValueError(f"No engineering strength profile for frame material {frame.material}")
        plywood_profile = materials["plywood"]
        cardboard_profile = materials["cardboard"]
        epoxy_profile = materials["epoxy"]
        ring_stations = [float(v) for v in fp.get("ring_stations_mm", [])]
        ring_thickness = float(fp["ring_thickness_mm"])
        ring_count = len(ring_stations)
        unsupported = max((b - a for a, b in pairwise(ring_stations)), default=None)
        tab_width = float(finp["tab_depth_mm"])
        tab_length = float(finp["tab_length_mm"])
        gusset_span = float(finp["root_gusset_span_mm"])
        slot_width = float(fp.get("fin_slot_width_mm", 7.3))
        flight_cases = _matching_envelopes(vehicle.id, flight)
        if not flight_cases:
            raise ValueError(f"No matching fresh flight envelope for {vehicle.id}")
        coincident_path = run_coincident_analysis(
            [vehicle_path], flight_record_path, output_root / "coincident-data"
        )[0]
        coincident_report = json.loads(coincident_path.read_text())
        coincident_candidates = [
            row
            for row in coincident_report["case_results"]
            if row.get("case_vehicle") == vehicle.id and row.get("status") != "unavailable"
        ]
        if not coincident_candidates:
            raise ValueError(f"No telemetry-derived coincident load for {vehicle.id}")
        coincident_case = max(
            coincident_candidates,
            key=lambda row: float(row["coincident_qcn_peak"]["qcn_bound_pa"]),
        )
        coincident_peak = coincident_case["coincident_qcn_peak"]
        fresh_speed_bound = max(
            float(candidate.get("metrics", {}).get("max_speed_mps", 0.0))
            for candidate in flight.get("cases", [])
            if candidate.get("vehicle") == vehicle.id
        )
        if fresh_speed_bound <= 0:
            raise ValueError(f"No positive fresh maximum-speed value for {vehicle.id}")

        paths = set(vehicle_input_paths(vehicle_path)) | {
            flight_record_path,
            Path("src/analysis/fin_attachment.py"),
            Path("src/analysis/fin_fea.py"),
            Path("src/analysis/fin_fields.py"),
            Path("src/analysis/vibration.py"),
            Path("scripts/wo03_fin_acceptance.py"),
            Path("scripts/wo03_fin_installed.py"),
            engineering_path,
            coincident_path,
        }
        paths.update(path for path, _ in cached_panel_reports)
        paths.add(coincident_path)
        hash_before = _hashes(paths, root)

        run_id = "wo03-fin-installed-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        mode_dir = output_root / vehicle.id / run_id
        mode_dir.mkdir(parents=True, exist_ok=False)
        # A cached report is reusable only when resolved config, fin shape and
        # all source hashes in that report still identify this exact panel run.
        resolved_hash = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        panel_report: dict[str, Any] | None = None
        panel_report_source_path: Path | None = None
        for candidate_path, candidate_report in cached_panel_reports:
            if (
                candidate_report.get("vehicle_id") == vehicle.id
                and candidate_report.get("resolved_spec_sha256") == resolved_hash
                and candidate_report.get("source_fin_shape_sha256")
                == (fin.cad_mass.shape_sha256 if fin.cad_mass else None)
            ):
                hashes = candidate_report.get("input_sha256_before", {})
                if hashes and all(
                    Path(name).is_file()
                    and hashlib.sha256(Path(name).read_bytes()).hexdigest() == expected
                    for name, expected in hashes.items()
                ):
                    panel_report = candidate_report
                    panel_report_source_path = candidate_path
                    break
        panel_report_path: Path | None = None
        if panel_report is None:
            panel_report_path = run_acceptance(vehicle_path, mode_dir / "panel-fea", None)
            panel_report = json.loads(panel_report_path.read_text())
            panel_report_source_path = panel_report_path
        panel_run_dir = (
            panel_report_source_path.parent
            if panel_report_source_path is not None
            else Path("build/wo03-fin-acceptance") / vehicle.id / panel_report["run_id"]
        )
        spatial_record: dict[str, Any]
        try:
            spatial = export_fin_fields(
                vehicle,
                panel_run_dir / "static-cold" / "5.0",
                mode_dir / "spatial-analysis",
                run_id,
                panel_report["input_sha256_before"],
                known_case_verified=False,
                mesh_converged=bool(panel_report["validation"]["mesh_convergence"]),
            )
            spatial_record = {
                "status": "exported",
                "analysis_record": spatial.model_dump(mode="json"),
                "source_folder": (panel_run_dir / "static-cold" / "5.0")
                .resolve()
                .relative_to(root.resolve())
                .as_posix(),
                "limitations": "Original S6 mesh geometry and solver node/element IDs are retained. Only registered fields are exported; CAD faces are not invented.",
            }
        except (ValueError, FileNotFoundError, TypeError) as error:
            spatial_record = {
                "status": "unavailable",
                "reason": f"{type(error).__name__}: {error}",
                "limitations": "No fallback geometry or synthetic CAD faces are generated.",
            }
        scenarios: list[dict[str, Any]] = []
        for case in flight_cases:
            q = float(case["metrics"]["max_dynamic_pressure_pa"])
            speed = float(case["metrics"]["max_speed_mps"])
            force = panel_force_n(fin, q, 0.0, coefficient_bound=2.0)
            shell_cases = []
            for temperature_label, fraction in (
                ("cold-estimated", 1.0),
                ("hot-half-property-sensitivity", TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION),
            ):
                result = run_shell(
                    mode_dir / case["vehicle"] / temperature_label / "5.0mm",
                    fin.model_copy(
                        update={
                            "geometry": {
                                **fin.geometry,
                                "thickness_m": minimum_thickness_m,
                            },
                            "cad_mass": None,
                        }
                    ),
                    5.0,
                    force_n=force,
                    stiffness_fraction=fraction,
                    orthotropic=ORTHOTROPIC,
                )
                shell_cases.append(
                    {
                        "property_scenario": temperature_label,
                        "strength_fraction": fraction,
                        "fea_mesh_and_modes": result,
                        "directional_stress_screen": _component_screen(result, fraction),
                    }
                )
            coincident_qcn_pa = float(coincident_peak["qcn_bound_pa"])
            coincident_force = panel_force_n(fin, coincident_qcn_pa, 0.0, coefficient_bound=1.0)
            coincident_fea: list[dict[str, Any]] = []
            coincident_attachment: list[dict[str, Any]] = []
            for temperature_label, fraction in (
                ("cold-estimated", 1.0),
                ("hot-half-property-sensitivity", TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION),
            ):
                coincident_result = run_shell(
                    mode_dir / "coincident-qcn" / temperature_label / "5.0mm",
                    fin.model_copy(
                        update={
                            "geometry": {
                                **fin.geometry,
                                "thickness_m": minimum_thickness_m,
                            },
                            "cad_mass": None,
                        }
                    ),
                    5.0,
                    force_n=coincident_force,
                    stiffness_fraction=fraction,
                    orthotropic=ORTHOTROPIC,
                )
                coincident_fea.append(
                    {
                        "property_scenario": temperature_label,
                        "strength_fraction": fraction,
                        "fea_mesh_and_modes": coincident_result,
                        "directional_stress_screen": _component_screen(coincident_result, fraction),
                    }
                )
                coincident_attachment.append(
                    {
                        "property_scenario": temperature_label,
                        "result": analyze_fin_attachment(
                            configuration_id=vehicle.id,
                            dynamic_pressure_pa=coincident_qcn_pa,
                            normal_coefficient=1.0,
                            span_m=float(fin.geometry["span_m"]),
                            root_chord_m=float(fin.geometry["root_chord_m"]),
                            tip_chord_m=float(fin.geometry["tip_chord_m"]),
                            gusset_span_mm=gusset_span,
                            gusset_base_thickness_mm=float(finp["root_gusset_base_mm"]),
                            tab_engagement_length_mm=tab_length,
                            tab_radial_width_mm=tab_width,
                            tab_slot_width_mm=slot_width,
                            body_wall_thickness_mm=float(shell.geometry["wall_m"]) * 1000,
                            frame_rail_width_mm=float(fp["rail_width_mm"]),
                            frame_rail_radial_depth_mm=float(fp["rail_depth_mm"]),
                            rails_sharing_one_fin=1,
                            frame_material_name=frame.material,
                            frame_strength_bound_pa=float(frame_profile["strength_pa"]),
                            wood_bound_pa=float(plywood_profile["strength_pa"]),
                            kraft_bound_pa=float(cardboard_profile["strength_pa"]),
                            bond_shear_allowable_pa=float(epoxy_profile["strength_pa"]),
                            hot_bond_allowable_pa=float(epoxy_profile["hot_strength_screen_pa"]),
                            design_factor=float(loads_config["design_factor"]),
                            ring_count=ring_count,
                            ring_thickness_mm=ring_thickness,
                            temperature_strength_fraction=fraction,
                            unsupported_shell_span_mm=unsupported,
                        ),
                    }
                )
            attachment_rows = []
            for temperature_label, fraction in (
                ("cold-estimated", 1.0),
                ("hot-half-property-sensitivity", TEMPERATURE_STIFFNESS_AND_STRENGTH_FRACTION),
            ):
                attachment_rows.append(
                    {
                        "property_scenario": temperature_label,
                        "result": analyze_fin_attachment(
                            configuration_id=vehicle.id,
                            dynamic_pressure_pa=q,
                            normal_coefficient=2.0,
                            span_m=float(fin.geometry["span_m"]),
                            root_chord_m=float(fin.geometry["root_chord_m"]),
                            tip_chord_m=float(fin.geometry["tip_chord_m"]),
                            gusset_span_mm=gusset_span,
                            gusset_base_thickness_mm=float(finp["root_gusset_base_mm"]),
                            tab_engagement_length_mm=tab_length,
                            tab_radial_width_mm=tab_width,
                            tab_slot_width_mm=slot_width,
                            body_wall_thickness_mm=float(shell.geometry["wall_m"]) * 1000,
                            frame_rail_width_mm=float(fp["rail_width_mm"]),
                            frame_rail_radial_depth_mm=float(fp["rail_depth_mm"]),
                            rails_sharing_one_fin=1,
                            frame_material_name=frame.material,
                            frame_strength_bound_pa=float(frame_profile["strength_pa"]),
                            wood_bound_pa=float(plywood_profile["strength_pa"]),
                            kraft_bound_pa=float(cardboard_profile["strength_pa"]),
                            bond_shear_allowable_pa=float(epoxy_profile["strength_pa"]),
                            hot_bond_allowable_pa=float(epoxy_profile["hot_strength_screen_pa"]),
                            design_factor=float(loads_config["design_factor"]),
                            ring_count=ring_count,
                            ring_thickness_mm=ring_thickness,
                            temperature_strength_fraction=fraction,
                            unsupported_shell_span_mm=unsupported,
                        ),
                    }
                )
            flutter = fin_flutter_domain_assessment(
                span_m=float(fin.geometry["span_m"]),
                sweep_m=float(fin.geometry["sweep_m"]),
                root_chord_m=float(fin.geometry["root_chord_m"]),
                tip_chord_m=float(fin.geometry["tip_chord_m"]),
                base_fin_thickness_m=minimum_thickness_m,
                root_gusset_thickness_varies=gusset_span > 0,
                root_attachment_stiffness_verified=False,
                flight_max_q_available=True,
            )
            min_thickness_vehicle = vehicle.model_copy(
                update={
                    "parts": [
                        (
                            part.model_copy(
                                update={
                                    "geometry": {
                                        **part.geometry,
                                        "thickness_m": minimum_thickness_m,
                                    }
                                }
                            )
                            if part.id == fin.id
                            else part
                        )
                        for part in vehicle.parts
                    ]
                }
            )
            flutter_cfg = {"vibration": {**engineering["vibration"]}}
            flutter_cfg["vibration"]["speed_envelope_mps"] = fresh_speed_bound
            flutter_at_speed = flutter_screen(min_thickness_vehicle, flutter_cfg)
            screen_range = [float(v) for v in flutter_at_speed["screen_speed_range_mps"]]
            flutter["numerical_screen"] = {
                "source_method": "Existing WO-03 vibration implementation of Martin/NACA TN 4197 Eq. 18, evaluated on the minimum-thickness rectangular unswept base panel with current study material ranges.",
                "minimum_thickness_m": minimum_thickness_m,
                "speed_range_mps": screen_range,
                "fresh_flight_max_speed_mps": fresh_speed_bound,
                "ratio_range_to_fresh_speed": [
                    screen_range[0] / fresh_speed_bound,
                    screen_range[1] / fresh_speed_bound,
                ],
                "plus_20_percent_speed_bound_mps": 1.2 * fresh_speed_bound,
                "ratio_range_to_plus_20_percent_speed": [
                    screen_range[0] / (1.2 * fresh_speed_bound),
                    screen_range[1] / (1.2 * fresh_speed_bound),
                ],
                "current_flight_case_count_for_speed_bound": sum(
                    candidate.get("vehicle") == vehicle.id for candidate in flight["cases"]
                ),
                "calculation_only": True,
                "acceptance": "open",
                "scope_note": "The source's constant-chord/constant-thickness base-panel geometry applies to this unswept rectangular fin. Root/gusset variation is local; installed root rotational/torsional stiffness, damping, body coupling, aeroelastic modes and flight validation remain unresolved.",
            }
            flutter["limitations"] = [
                "The screen is conditional and empirical, not an installed fin/body aeroelastic analysis.",
                "Finite root bond, plywood/frame support flexibility, torsional joint stiffness and damping remain unmeasured.",
                "Low panel aspect ratio limits confidence in extending the bending-torsion relation.",
                "The fresh simulated speed is a comparison bound only; it does not establish a flight envelope.",
            ]
            flutter["source_module_legacy_taper_note_excluded"] = (
                "The generic vibration helper includes a tapered-panel caveat; the current resolved fin is rectangular and constant-chord, so the geometry-specific domain assessment above supersedes that caveat."
            )
            flutter.update(
                {
                    "calculation_only": True,
                    "flight_record_id": flight["run_id"],
                    "flight_case_vehicle": case["vehicle"],
                    "fresh_record_max_q_pa": q,
                    "fresh_record_max_speed_mps": speed,
                    "max_speed_source_metric": "metrics.max_speed_mps",
                    "quantitative_flutter_acceptance": "open",
                    "applicability_status": "conditional preliminary base-panel screen; installed root and low-aspect-ratio limitations are unresolved",
                }
            )
            scenarios.append(
                {
                    "case_vehicle": case["vehicle"],
                    "case_config": case.get("config"),
                    "max_q_pa": q,
                    "max_speed_mps": speed,
                    "load_basis": "off-nominal Cartesian sensitivity: fresh-record maximum q times CN=2; maximum q and CN=2 are not known to coincide in flight and this is not an operational maximum or validated post-stall coefficient",
                    "flight_coincident_q_times_cn_available": False,
                    "per_fin_normal_force_n_at_CN2": force,
                    "coincident_q_times_cn_load": {
                        "record_case_vehicle": coincident_case["case_vehicle"],
                        "record_scenario": coincident_case.get("scenario"),
                        "flight_peak": coincident_peak,
                        "normal_force_coefficient_method": coincident_report["coefficient_method"],
                        "input_identity_current": coincident_case.get(
                            "flight_config_identity", {}
                        ).get("matches_current", False),
                        "estimated_per_fin_force_n": coincident_force,
                        "fea_cold_hot": coincident_fea,
                        "installed_attachment_cold_hot": coincident_attachment,
                        "status": "coincident q(t)*estimated C_N(alpha) load estimate; source identity, aero coefficient and post-stall validity remain conditional",
                    },
                    "minimum_thickness_fea_cold_hot": shell_cases,
                    "installed_attachment_cold_hot": attachment_rows,
                    "flutter_method_applicability": flutter,
                }
            )

        report = {
            "run_id": run_id,
            "vehicle_id": vehicle.id,
            "source_config": vehicle_path.resolve().relative_to(root.resolve()).as_posix(),
            "flight_record_id": flight["run_id"],
            "flight_record_path": flight_record_path.resolve()
            .relative_to(root.resolve())
            .as_posix(),
            "resolved_spec_sha256": hashlib.sha256(
                vehicle.model_dump_json(by_alias=True).encode()
            ).hexdigest(),
            "fin_shape_sha256": panel_report.get("source_fin_shape_sha256"),
            "panel_fea_target_identity": {
                "vehicle_id": vehicle.id,
                "resolved_spec_sha256": resolved_hash,
                "part_id": fin.id,
                "source_fin_shape_sha256": fin.cad_mass.shape_sha256 if fin.cad_mass else None,
                "minimum_thickness_m": minimum_thickness_m,
                "parent_run_id": panel_report.get("run_id"),
            },
            "panel_cache_proof": None,
            "panel_fea_report": panel_report,
            "panel_fea_report_source": (
                panel_report_source_path.resolve().relative_to(root.resolve()).as_posix()
                if panel_report_source_path is not None
                else "no cached report source path"
            ),
            "spatial_analysis_record": spatial_record,
            "coincident_load_record": {
                "run_id": coincident_report.get("run_id"),
                "path": coincident_path.resolve().relative_to(root.resolve()).as_posix(),
                "flight_record_identity_current": coincident_report.get(
                    "flight_record_identity_current"
                ),
                "scope": "q(t)*estimated CN(alpha) extracted from this campaign's Parquet; nonqualification",
            },
            "installed_scenarios": scenarios,
            "frame_geometry_source": {
                "frame_part_id": frame.id,
                "material": frame.material,
                "rail_width_mm": fp["rail_width_mm"],
                "rail_radial_depth_mm": fp["rail_depth_mm"],
                "ring_stations_mm": ring_stations,
                "ring_thickness_mm": ring_thickness,
                "rail_radius_mm": fp.get("rail_radius_mm"),
                "material_profile_source": "configs/engineering/wo03.yaml",
                "main_fin_normal_bending_axis": "radial X, using I_X = radial_depth*tangential_width^3/12",
                "crossload_axis": "reported separately as uncertainty, not used as the normal-load axis",
                "assumed_rails_sharing_each_fin": 1,
            },
            "bond_and_body_scope": {
                "root_rotational_stiffness": "unavailable; no test-derived or CAD-calculated Ktheta is presumed",
                "peel": "unrated; shear-only estimates do not qualify peel",
                "kraft_wall": "0.5 mm shell-only strip screen receives no G11 backing strength credit",
                "joint_status": "open: assembled frame/ring/body load sharing and bond geometry require connected FEA and proof evidence",
            },
            "acceptance": "open",
            "acceptance_passed": False,
            "flight_ready": False,
            "active_adoption": False,
            "cost_usd": 0,
        }
        hash_after = _hashes(paths, root)
        report["input_sha256_before"] = hash_before
        report["input_sha256_after"] = hash_after
        report["inputs_unchanged"] = hash_before == hash_after
        report_path = mode_dir / "report.json"
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n")
        reports.append(report_path)
    return reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vehicle",
        type=Path,
        action="append",
        required=True,
        help="Resolved mode YAML; repeat once for performance and once for finned TVC.",
    )
    parser.add_argument("--flight-record", type=Path, required=True)
    parser.add_argument(
        "--coincident-only",
        action="store_true",
        help="Extract sim q(t)*CN(alpha) estimates from Parquet without running structural solvers.",
    )
    parser.add_argument(
        "--panel-report",
        type=Path,
        action="append",
        default=[],
        help="Optional existing panel FEA report; reused only after exact vehicle/spec/fin/source hash checks. Repeatable.",
    )
    parser.add_argument("--output", type=Path, default=Path("build/wo03-fin-installed"))
    args = parser.parse_args()
    reports = (
        run_coincident_analysis(args.vehicle, args.flight_record, args.output)
        if args.coincident_only
        else run_installed(args.vehicle, args.flight_record, args.output, args.panel_report)
    )
    print("\n".join(str(path) for path in reports))
    return 0 if all(json.loads(p.read_text())["inputs_unchanged"] for p in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())
