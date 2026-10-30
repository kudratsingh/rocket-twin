"""Axially partitioned coaxial thermal reduction of the neutral aft assembly.

The actual spec supplies annular parts and frame-ring stations. In each axial band
only adjacent radial barriers exchange through air conduction and grey diffuse
radiation; contacting liner/shield surfaces exchange through solid half walls and
bounded interface conductance. This removes the legacy case-to-everything radiation
bypass. The liner has radial finite volumes; other parts remain single thermal capacities. Sparse
rails, holes, splits, moving/finite-end view factors, gas circulation, nozzle plume
and bonds are not resolved. Closed long-cylinder gaps are explicit approximations,
not a 3D radiation solution or a universally conservative temperature bound.
Equations and verification references: src.analysis.thermal_radial. Actual thermal
properties, contacts, external case histories and convection remain estimates.
"""

from __future__ import annotations

from itertools import pairwise
from typing import Any

import numpy as np
from scipy.integrate import solve_ivp

from src.analysis.engineering import material_profile
from src.analysis.thermal_radial import (
    SIGMA,
    annular_wall,
    direct_contact_flux,
    opaque_gap_flux,
    wall_heat_rates,
)
from src.vehicle.schema import Part, Vehicle


def _as_float(value: Any) -> float:
    return float(value)


def radial_bounds(part: Part) -> tuple[float, float]:
    """Effective annular surfaces, using the cassette grip rather than its end-block envelope."""
    if part.cad and part.cad.generator == "motor_cassette":
        options = part.cad.parameters
        return (
            float(options["motor_clear_radius_mm"]) * 1e-3,
            float(options["grip_outer_radius_mm"]) * 1e-3,
        )
    return float(part.geometry["inner_radius_m"]), float(part.geometry["radius_m"])


def annular_intervals(part: Part) -> list[tuple[float, float]]:
    """Continuous annular portions only; do not turn a frame's rails into a tube."""
    assert part.cad
    start = part.position_m
    length = part.geometry["length_m"]
    options = part.cad.parameters
    if part.cad.generator == "motor_cassette":
        grip_start = float(options["grip_start_mm"]) * 1e-3
        grip_length = float(options["grip_length_mm"]) * 1e-3
        if grip_start < 0 or grip_start + grip_length > length:
            raise ValueError(f"{part.id}: cassette grip interval exceeds its CAD length")
        # The cassette cage/rails, forestop and aft blocks are not full coaxial
        # barriers. Only its explicit continuous grip ring occludes the radial gap.
        return [(start + grip_start, start + grip_start + grip_length)]
    if part.cad.generator == "mount":
        intervals = [
            (start + z * 0.001, start + (z + options["ring_thickness_mm"]) * 0.001)
            for z in options["ring_stations_mm"]
        ]
        if options.get("pivot_ring"):
            z = start + options["pivot_station_mm"] * 0.001
            intervals.append((z - 0.004, z + 0.004))
        return intervals
    if options.get("tie_rails"):
        # The split clamp's annular 18mm region is an approximation; its split
        # and the sparse rails require a later angular/ray treatment.
        return [(start + length - 0.018, start + length)]
    return [(start, start + length)]


def run_thermal_topology(
    vehicle: Vehicle,
    cfg: dict[str, Any],
    study: dict[str, Any],
    severe: bool | int,
    cells: int = 8,
    max_step_s: float = 2,
    *,
    scenario_index: int | None = None,
) -> dict[str, Any]:
    assert vehicle.motor
    parts = {p.id: p for p in vehicle.parts}
    liner = parts["motor_liner"]
    motor = parts["motor"]
    settings = cfg["thermal"]
    scenario = int(severe) if scenario_index is None else scenario_index
    case_ids = settings.get("case_ids", ["lower-case-scenario", "upper-hot-soak"])
    if scenario < 0 or scenario >= len(case_ids):
        raise ValueError(f"Thermal scenario index {scenario} is not configured")
    ambient = settings["ambient_c"][scenario] + 273.15
    peak = settings["external_case_peak_c"][scenario] + 273.15
    tau = settings["post_burn_cooling_tau_s"][scenario]
    air_k = settings["air_conductivity_w_m_k"][scenario]
    emissivity = settings["emissivity"][scenario]
    if "surface_h_w_m2_k_by_case" in settings:
        convection = settings["surface_h_w_m2_k_by_case"][scenario]
    else:
        convection = settings["surface_h_w_m2_k"][1 - scenario]
    burn = vehicle.motor.burn_time_s

    def profile(part: Part) -> dict[str, Any]:
        return dict(cfg["materials"].get(material_profile(part), cfg["materials"]["commercial"]))

    def surface_emissivity(part: Part) -> float:
        part_profile = profile(part)
        value = part_profile.get(
            "surface_emissivity_by_scenario",
            part_profile.get(
                "surface_emissivity",
                settings.get("surface_emissivity", settings["emissivity"]),
            ),
        )
        if isinstance(value, (tuple, list)):
            value = value[scenario]
        return float(value)

    pad_conduction_ids = set(study.get("pad_conduction_part_ids", [])) & set(parts)
    pad_data: dict[str, dict[str, float]] = {}
    for part_id in pad_conduction_ids:
        pad = parts[part_id]
        if pad.cad_mass is None:
            raise ValueError(f"{part_id}: pad conduction requires recorded CAD volume")
        thickness = float(pad.geometry["length_m"])
        if thickness <= 0:
            raise ValueError(f"{part_id}: pad thickness must be positive")
        area = float(pad.cad_mass.volume_m3) / thickness
        pad_material = profile(pad)
        conductivity = float(pad_material["conductivity_w_m_k"])
        bounds = pad_material.get("conductivity_range_w_m_k", [conductivity, conductivity])
        pad_data[part_id] = {
            "area_m2": area,
            "thickness_m": thickness,
            "conductivity_nominal_w_m_k": conductivity,
            "conductivity_min_w_m_k": float(bounds[0]),
            "conductivity_max_w_m_k": float(bounds[1]),
            "full_path_conductance_nominal_w_k": conductivity * area / thickness,
            "full_path_conductance_min_w_k": float(bounds[0]) * area / thickness,
            "full_path_conductance_max_w_k": float(bounds[1]) * area / thickness,
        }

    def pad_lumped_conductance(interface_conductance: float, part_ids: tuple[str, ...]) -> float:
        resistance = 1 / interface_conductance
        for part_id in part_ids:
            data = pad_data.get(part_id)
            if data is not None:
                resistance += (data["thickness_m"] / 2) / (
                    data["conductivity_nominal_w_m_k"] * data["area_m2"]
                )
        return 1 / resistance

    lg = liner.geometry
    wall = annular_wall(
        lg["inner_radius_m"],
        lg["radius_m"],
        lg["length_m"],
        profile(liner)["conductivity_w_m_k"],
        liner.resolved_mass_kg * profile(liner)["cp_j_kg_k"],
        cells,
    )
    other_ids = [name for name in study["part_ids"] if name in parts and name != liner.id]
    index = {name: cells + i for i, name in enumerate(other_ids)}
    capacities = np.concatenate(
        (
            wall.capacities_j_k,
            [
                parts[name].resolved_mass_kg * profile(parts[name])["cp_j_kg_k"]
                for name in other_ids
            ],
        )
    )
    count = len(capacities)
    z0, z1 = liner.position_m, liner.position_m + lg["length_m"]
    barriers = []
    for name in study["annular_barrier_part_ids"]:
        if name not in parts:
            continue
        part = parts[name]
        for start, end in annular_intervals(part):
            if start < z1 and end > z0:
                barriers.append((max(start, z0), min(end, z1), name))
    cuts = sorted({z0, z1, *(z for start, end, _ in barriers for z in [start, end])})
    interfaces: list[dict[str, Any]] = []
    descriptions = []
    excluded_overlapping_barriers: set[tuple[str, str]] = set()
    direct_contacts = {
        frozenset((str(pair[0]), str(pair[1]))) for pair in study.get("direct_contact_pairs", [])
    }
    direct_contact_conductance = float(
        study.get("direct_contact_conductance_w_k", study["contact_conductance_w_k"])[scenario]
    )
    for start, end in pairwise(cuts):
        if end - start < 1e-10:
            continue
        midpoint = (start + end) / 2
        candidates = sorted(
            {name for a, b, name in barriers if a <= midpoint <= b},
            key=lambda name: radial_bounds(parts[name])[0],
        )
        present: list[str] = []
        outer_radius = float(liner.geometry["radius_m"])
        for name in candidates:
            inner_radius = radial_bounds(parts[name])[0]
            if inner_radius < outer_radius - 1e-12:
                overlapping = present[-1] if present else liner.id
                excluded_overlapping_barriers.add((name, overlapping))
                continue
            present.append(name)
            outer_radius = radial_bounds(parts[name])[1]
        sequence = [liner.id, *present]
        band_interfaces = []
        for source, target in pairwise(sequence):
            a, b = parts[source], parts[target]
            _, ra = radial_bounds(a)
            rb, _ = radial_bounds(b)
            direct = frozenset((source, target)) in direct_contacts
            if direct and not np.isclose(ra, rb, rtol=0.0, atol=1e-12):
                raise ValueError(
                    f"Direct contact {source}/{target} requires coincident radii; got {ra}/{rb}"
                )
            if not direct and rb <= ra:
                raise ValueError(f"Overlapping coaxial barriers: {source}/{target}")
            length = end - start
            # Receiver/source body nodes are logarithmic midsurfaces. The actual
            # liner outermost cell centre replaces the whole-wall mean radius.
            ca = (
                float(wall.centres_m[-1])
                if source == liner.id
                else np.sqrt(radial_bounds(a)[0] * radial_bounds(a)[1])
            )
            cb = np.sqrt(radial_bounds(b)[0] * radial_bounds(b)[1])
            resistance_a = np.log(ra / ca) / (2 * np.pi * profile(a)["conductivity_w_m_k"] * length)
            resistance_b = np.log(cb / rb) / (2 * np.pi * profile(b)["conductivity_w_m_k"] * length)
            interface = {
                "source_part_id": source,
                "target_part_id": target,
                "source_node": cells - 1 if source == liner.id else index[source],
                "target_node": index[target],
                "source_half_wall_resistance_k_w": float(resistance_a),
                "target_half_wall_resistance_k_w": float(resistance_b),
                "source_surface_radius_m": float(ra),
                "target_surface_radius_m": float(rb),
                "length_m": float(length),
                "model": "direct_solid_contact" if direct else "opaque_gap",
                "contact_conductance_w_k": direct_contact_conductance if direct else None,
                "source_surface_emissivity": surface_emissivity(a),
                "target_surface_emissivity": surface_emissivity(b),
            }
            interfaces.append(interface)
            band_interfaces.append(
                {
                    "source_part_id": source,
                    "target_part_id": target,
                    "model": interface["model"],
                }
            )
        descriptions.append(
            {
                "axial_interval_m": [start, end],
                "radial_sequence": sequence,
                "interfaces": band_interfaces,
            }
        )
    direct_overlap_length: dict[frozenset[str], float] = {}
    for interface in interfaces:
        if interface["model"] == "direct_solid_contact":
            pair = frozenset((str(interface["source_part_id"]), str(interface["target_part_id"])))
            direct_overlap_length[pair] = direct_overlap_length.get(pair, 0.0) + _as_float(
                interface["length_m"]
            )
    for interface in interfaces:
        if interface["model"] == "direct_solid_contact":
            pair = frozenset((str(interface["source_part_id"]), str(interface["target_part_id"])))
            total_length = direct_overlap_length[pair]
            interface["contact_conductance_w_k"] = (
                direct_contact_conductance * _as_float(interface["length_m"]) / total_length
            )
    contacts = []
    for a, b in study["contact_pairs"]:
        if a not in parts or b not in parts:
            continue
        if a not in index and a != liner.id:
            continue
        if b not in index and b != liner.id:
            continue
        node_a = cells - 1 if a == liner.id else index[a]
        node_b = cells - 1 if b == liner.id else index[b]
        base_conductance = float(study["contact_conductance_w_k"][scenario])
        effective_conductance = pad_lumped_conductance(base_conductance, (a, b))
        contacts.append(
            (
                node_a,
                node_b,
                effective_conductance,
                a,
                b,
            )
        )
    case_contacts = []
    for part_id in study.get("prescribed_case_contact_part_ids", []):
        if part_id not in index:
            continue
        base_conductance = float(study["case_contact_conductance_w_k"][scenario])
        effective_conductance = pad_lumped_conductance(base_conductance, (part_id,))
        case_contacts.append((index[part_id], part_id, effective_conductance))
        if part_id in pad_data:
            pad_data[part_id]["case_interface_conductance_w_k"] = base_conductance
            pad_data[part_id]["effective_case_half_path_conductance_w_k"] = effective_conductance
    for _, _, conductance, source_id, target_id in contacts:
        for part_id in {source_id, target_id} & pad_conduction_ids:
            pad_data[part_id]["structural_interface_conductance_w_k"] = float(
                study["contact_conductance_w_k"][scenario]
            )
            pad_data[part_id]["effective_structural_half_path_conductance_w_k"] = conductance
    thermal_graph: dict[str, set[str]] = {name: set() for name in [liner.id, *other_ids]}
    for interface in interfaces:
        source = str(interface["source_part_id"])
        target = str(interface["target_part_id"])
        thermal_graph[source].add(target)
        thermal_graph[target].add(source)
    for _, _, _, source_id, target_id in contacts:
        thermal_graph[source_id].add(target_id)
        thermal_graph[target_id].add(source_id)
    case_coupled = {liner.id, *(part_id for _, part_id, _ in case_contacts)}
    frontier = list(case_coupled)
    while frontier:
        current = frontier.pop()
        for neighbor in thermal_graph[current] - case_coupled:
            case_coupled.add(neighbor)
            frontier.append(neighbor)
    required_support_nodes = set(study.get("required_case_coupled_part_ids", [])) & set(parts)
    uncoupled_support_nodes = sorted(required_support_nodes - case_coupled)
    if uncoupled_support_nodes:
        raise ValueError(
            "Thermal support nodes are present without a modeled conductive/radiative "
            f"path from the case/liner: {uncoupled_support_nodes}"
        )
    shell = parts["aft_shell"]
    shell_area = 2 * np.pi * shell.geometry["radius_m"] * shell.geometry["length_m"]
    external_cooling = [
        (index[name], conductance)
        for name, conductance in study["upper_bay_cooling_w_k"].items()
        if name in index
    ]

    def boundary(t: float) -> float:
        return float(peak if t <= burn else ambient + (peak - ambient) * np.exp(-(t - burn) / tau))

    def rhs(t: float, state: Any) -> Any:
        temperature = state[:count]
        q = np.zeros(count)
        q[:cells] = wall_heat_rates(wall, temperature[:cells])
        case_heat = opaque_gap_flux(
            boundary(t),
            float(temperature[0]),
            0,
            wall.inner_half_resistance_k_w,
            motor.geometry["radius_m"],
            lg["inner_radius_m"],
            lg["length_m"],
            air_k,
            emissivity,
            inner_surface_emissivity=surface_emissivity(motor),
            outer_surface_emissivity=surface_emissivity(liner),
        )
        q[0] += case_heat
        case_contact_heat = 0.0
        case_temperature = boundary(t)
        for node, _, conductance in case_contacts:
            flux = conductance * (case_temperature - temperature[node])
            q[node] += flux
            case_contact_heat += flux
        for interface in interfaces:
            a = int(interface["source_node"])
            b = int(interface["target_node"])
            resistance_a = float(interface["source_half_wall_resistance_k_w"])
            resistance_b = float(interface["target_half_wall_resistance_k_w"])
            if interface["model"] == "direct_solid_contact":
                flux = direct_contact_flux(
                    float(temperature[a]),
                    float(temperature[b]),
                    resistance_a,
                    resistance_b,
                    float(interface["contact_conductance_w_k"]),
                )
            else:
                flux = opaque_gap_flux(
                    float(temperature[a]),
                    float(temperature[b]),
                    resistance_a,
                    resistance_b,
                    float(interface["source_surface_radius_m"]),
                    float(interface["target_surface_radius_m"]),
                    float(interface["length_m"]),
                    air_k,
                    emissivity,
                    inner_surface_emissivity=float(interface["source_surface_emissivity"]),
                    outer_surface_emissivity=float(interface["target_surface_emissivity"]),
                )
            q[a] -= flux
            q[b] += flux
        for a, b, conductance, _, _ in contacts:
            flux = conductance * (temperature[b] - temperature[a])
            q[a] += flux
            q[b] -= flux
        shell_n = index["aft_shell"]
        shell_loss = shell_area * (
            convection * (ambient - temperature[shell_n])
            + surface_emissivity(shell) * SIGMA * (ambient**4 - temperature[shell_n] ** 4)
        )
        q[shell_n] += shell_loss
        external = case_heat + case_contact_heat + shell_loss
        for node, conductance in external_cooling:
            flux = conductance * (ambient - temperature[node])
            q[node] += flux
            external += flux
        if "flight_computer" in index:
            power = settings["electronics_heat_w"][scenario]
            q[index["flight_computer"]] += power
            external += power
        return np.concatenate((q / capacities, [external]))

    end = burn + settings["soak_s"]
    times = np.unique(np.append(np.arange(0, end, 1.0), [burn, end]))
    solution = solve_ivp(
        rhs,
        (0, end),
        np.append(np.full(count, ambient), 0),
        method="BDF",
        t_eval=times,
        rtol=1e-8,
        atol=1e-7,
        max_step=max_step_s,
    )
    if not solution.success:
        raise RuntimeError(solution.message)
    states = solution.y[:count].T
    ids = [liner.id, *other_ids]
    temperatures = np.column_stack(
        (
            states[:, :cells] @ wall.capacities_j_k / sum(wall.capacities_j_k),
            states[:, cells:],
        )
    )
    peaks = []
    for n, name in enumerate(ids):
        maximum = float(temperatures[:, n].max() - 273.15)
        material = profile(parts[name])
        limit = float(material["limit_c"])
        peak_row = {
            "part_id": name,
            "peak_c": maximum,
            "peak_time_s": float(times[np.argmax(temperatures[:, n])]),
            "screen_limit_c": limit,
            "margin_k": limit - maximum,
            "passed": maximum <= limit,
            "evidence": "calculated with estimated inputs",
        }
        sensitivities = material.get("temperature_limit_sensitivity_c", [])
        if sensitivities:
            peak_row["temperature_limit_sensitivity"] = [
                {
                    "limit_c": float(sensitivity),
                    "margin_k": float(sensitivity) - maximum,
                    "passed": maximum <= float(sensitivity),
                    "basis": "conditional material/process sensitivity; not hardware qualification",
                }
                for sensitivity in sensitivities
            ]
        peaks.append(peak_row)
    return {
        "model": "neutral-coaxial-material-shield-v3",
        "case": case_ids[scenario],
        "scenario_index": scenario,
        "ambient_c": float(ambient - 273.15),
        "prescribed_case_peak_c": float(peak - 273.15),
        "post_burn_cooling_tau_s": float(tau),
        "air_conductivity_w_m_k": float(air_k),
        "external_convection_w_m2_k": float(convection),
        "radial_cells": cells,
        "radial_centres_m": wall.centres_m.tolist(),
        "times_s": times.tolist(),
        "part_ids": ids,
        "temperature_k": temperatures.tolist(),
        "liner_radial_temperature_k": states[:, :cells].tolist(),
        "liner_radial_peak_c": float(states[:, :cells].max() - 273.15),
        "peaks": peaks,
        "radial_bands": descriptions,
        "excluded_overlapping_annular_barriers": [
            {"excluded_part_id": part_id, "overlaps_part_id": other_id}
            for part_id, other_id in sorted(excluded_overlapping_barriers)
        ],
        "interfaces": interfaces,
        "prescribed_case_contact_paths": [
            {"part_id": part_id, "conductance_w_k": conductance}
            for _, part_id, conductance in case_contacts
        ],
        "pad_conduction": [
            {
                "part_id": part_id,
                **values,
                "basis": "CAD volume/thickness cross-section; half-thickness conduction in series with estimated interface conductance",
            }
            for part_id, values in sorted(pad_data.items())
        ],
        "case_coupled_part_ids": sorted(case_coupled),
        "required_case_coupled_support_part_ids": sorted(required_support_nodes),
        "energy_residual_j": float(
            np.max(np.abs((states - ambient) @ capacities - solution.y[-1]))
        ),
        "net_external_energy_j": float(solution.y[-1, -1]),
        "solver_max_step_s": max_step_s,
        "solver_evaluations": solution.nfev,
        "case_boundary_basis": settings["case_boundary_basis"],
        "limitations": study["limitations"],
        "thermal_acceptance_passed": False,
        "flight_ready": False,
    }
