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
    heat_flow_step_s: float = 1.0,
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
    prelaunch_powered_soak_s = float(study.get("prelaunch_powered_soak_s", 0.0))
    if prelaunch_powered_soak_s < 0:
        raise ValueError("prelaunch_powered_soak_s must be nonnegative")

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
    pad_thickness_overrides = study.get("pad_conduction_thickness_m", {})
    pad_data: dict[str, dict[str, float]] = {}
    for part_id in pad_conduction_ids:
        pad = parts[part_id]
        if pad.cad_mass is None:
            raise ValueError(f"{part_id}: pad conduction requires recorded CAD volume")
        thickness = float(pad_thickness_overrides.get(part_id, pad.geometry["length_m"]))
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
    ids = [liner.id, *other_ids]
    initial_part_overrides = study.get("initial_part_temperature_c", {})
    # A few study-level component names intentionally span vehicle variants.
    # The older fixed-mount vehicles have one gimbal_servo assembly rather than
    # separate pitch/yaw servos and no servo_support node. Apply the hottest
    # servo bound to that lumped assembly, and record omitted components.
    normalized_initial_overrides: dict[str, float] = {}
    absent_initial_overrides: list[str] = []
    for name, value in initial_part_overrides.items():
        if name in ids:
            normalized_initial_overrides[name] = float(value)
        elif name in {"servo_pitch", "servo_yaw"} and "gimbal_servo" in ids:
            normalized_initial_overrides["gimbal_servo"] = max(
                normalized_initial_overrides.get("gimbal_servo", -float("inf")),
                float(value),
            )
        elif name in {"servo_pitch", "servo_yaw", "servo_support"}:
            absent_initial_overrides.append(name)
        else:
            absent_initial_overrides.append(name)
    unknown_initial_parts = sorted(
        name
        for name in absent_initial_overrides
        if name not in {"servo_pitch", "servo_yaw", "servo_support"}
    )
    if unknown_initial_parts:
        raise ValueError(
            f"initial temperature overrides name absent thermal parts: {unknown_initial_parts}"
        )
    if "initial_temperature_c" in study:
        initial_base_k = float(study["initial_temperature_c"]) + 273.15
    else:
        initial_base_k = float(ambient)
    initial_temperature = np.full(count, initial_base_k)
    liner_initial_c = normalized_initial_overrides.get(liner.id)
    if liner_initial_c is not None:
        initial_temperature[:cells] = float(liner_initial_c) + 273.15
    for part_index, name in enumerate(other_ids):
        if name in normalized_initial_overrides:
            initial_temperature[cells + part_index] = normalized_initial_overrides[name] + 273.15
    if np.any(initial_temperature <= 0):
        raise ValueError("initial part temperatures must be above absolute zero")
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
    lumped_contact_metadata = []
    pair_overrides = study.get("contact_pair_conductance_w_k", {})
    for a, b in study["contact_pairs"]:
        if a not in parts or b not in parts:
            continue
        if a not in index and a != liner.id:
            continue
        if b not in index and b != liner.id:
            continue
        node_a = cells - 1 if a == liner.id else index[a]
        node_b = cells - 1 if b == liner.id else index[b]
        pair_key = f"{a}->{b}"
        override = pair_overrides.get(pair_key)
        base_conductance = float(
            override[scenario]
            if isinstance(override, (tuple, list))
            else override if override is not None else study["contact_conductance_w_k"][scenario]
        )
        effective_conductance = pad_lumped_conductance(base_conductance, (a, b))
        lumped_contact_metadata.append(
            {
                "source_part_id": a,
                "target_part_id": b,
                "base_conductance_w_k": base_conductance,
                "effective_conductance_w_k": effective_conductance,
                "pair_specific_override": override is not None,
            }
        )
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
        if t < 0 or (prelaunch_powered_soak_s > 0 and t == 0):
            return float(ambient)
        return float(peak if t <= burn else ambient + (peak - ambient) * np.exp(-(t - burn) / tau))

    def rates(t: float, state: Any) -> tuple[Any, float, list[tuple[str, str, str, str, float]]]:
        temperature = state[:count]
        q = np.zeros(count)
        q[:cells] = wall_heat_rates(wall, temperature[:cells])
        links: list[tuple[str, str, str, str, float]] = []
        radial_flow = wall.internal_conductance_w_k * np.diff(temperature[:cells])
        for cell, flow in enumerate(radial_flow):
            links.append(
                (
                    f"liner_radial_cell_{cell}_to_{cell + 1}",
                    f"motor_liner.cell_{cell}",
                    f"motor_liner.cell_{cell + 1}",
                    "internal_radial_conduction",
                    float(-flow),
                )
            )
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
        links.append(
            (
                "motor_case_to_liner_inner",
                "motor_case_boundary",
                "motor_liner.cell_0",
                "prescribed_case_gap",
                float(case_heat),
            )
        )
        case_contact_heat = 0.0
        case_temperature = boundary(t)
        for node, part_id, conductance in case_contacts:
            flux = conductance * (case_temperature - temperature[node])
            q[node] += flux
            case_contact_heat += flux
            links.append(
                (
                    f"case_contact:{part_id}",
                    "motor_case_boundary",
                    part_id,
                    "estimated_case_contact",
                    float(flux),
                )
            )
        for interface_index, interface in enumerate(interfaces):
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
            links.append(
                (
                    f"radial_interface_{interface_index}:{interface['source_part_id']}->{interface['target_part_id']}",
                    str(interface["source_part_id"]),
                    str(interface["target_part_id"]),
                    str(interface["model"]),
                    float(flux),
                )
            )
        for a, b, conductance, source_id, target_id in contacts:
            flux = conductance * (temperature[b] - temperature[a])
            q[a] += flux
            q[b] -= flux
            links.append(
                (
                    f"lumped_contact:{source_id}->{target_id}",
                    source_id,
                    target_id,
                    "estimated_lumped_contact",
                    float(-flux),
                )
            )
        shell_n = index["aft_shell"]
        shell_loss = shell_area * (
            convection * (ambient - temperature[shell_n])
            + surface_emissivity(shell) * SIGMA * (ambient**4 - temperature[shell_n] ** 4)
        )
        q[shell_n] += shell_loss
        external = case_heat + case_contact_heat + shell_loss
        links.append(
            (
                "aft_shell_external_convection_and_radiation",
                "ambient",
                "aft_shell",
                "external_boundary",
                float(shell_loss),
            )
        )
        for node, conductance in external_cooling:
            flux = conductance * (ambient - temperature[node])
            q[node] += flux
            external += flux
            part_id = other_ids[node - cells]
            links.append(
                (
                    f"upper_bay_cooling:{part_id}",
                    "ambient",
                    part_id,
                    "estimated_lumped_external_cooling",
                    float(flux),
                )
            )
        if "flight_computer" in index:
            power = settings["electronics_heat_w"][scenario]
            q[index["flight_computer"]] += power
            external += power
            links.append(
                (
                    "flight_computer_electronics_power",
                    "electrical_power",
                    "flight_computer",
                    "estimated_internal_heat_source",
                    float(power),
                )
            )
        return q, float(external), links

    def rhs(t: float, state: Any) -> Any:
        q, external, _ = rates(t, state)
        return np.concatenate((q / capacities, [external]))

    end = burn + settings["soak_s"]
    times_after_ignition = np.unique(np.append(np.arange(0.0, end, 1.0), [burn, end]))
    initial_state = np.append(initial_temperature, 0.0)
    prelaunch_energy_balance: dict[str, Any] | None = None
    if prelaunch_powered_soak_s == 0:
        # Retain the historical solve path exactly when the optional warm-up is off.
        times = times_after_ignition
        solution = solve_ivp(
            rhs,
            (0, end),
            initial_state,
            method="BDF",
            t_eval=times,
            rtol=1e-8,
            atol=1e-7,
            max_step=max_step_s,
            dense_output=True,
        )
        if not solution.success:
            raise RuntimeError(solution.message)
        assert solution.sol is not None
        dense_state = solution.sol
        states = solution.y[:count].T
        external_energy_history = solution.y[-1]
        solver_evaluations = solution.nfev
        initial_temperature = solution.y[:count, 0]
        final_temperature = solution.y[:count, -1]
        net_external_energy = float(solution.y[-1, -1])
    else:
        start = -prelaunch_powered_soak_s
        times_before_ignition = np.unique(np.append(np.arange(start, 0.0, 1.0), [start, 0.0]))
        prelaunch = solve_ivp(
            rhs,
            (start, 0.0),
            initial_state,
            method="BDF",
            t_eval=times_before_ignition,
            rtol=1e-8,
            atol=1e-7,
            max_step=max_step_s,
            dense_output=True,
        )
        if not prelaunch.success:
            raise RuntimeError(prelaunch.message)
        assert prelaunch.sol is not None
        ignition_state = prelaunch.y[:, -1]
        post_burn = solve_ivp(
            rhs,
            (0.0, end),
            ignition_state,
            method="BDF",
            t_eval=times_after_ignition,
            rtol=1e-8,
            atol=1e-7,
            max_step=max_step_s,
            dense_output=True,
        )
        if not post_burn.success:
            raise RuntimeError(post_burn.message)
        assert post_burn.sol is not None
        times = np.concatenate((times_before_ignition[:-1], times_after_ignition))
        states = np.vstack((prelaunch.y[:count, :-1].T, post_burn.y[:count].T))
        external_energy_history = np.concatenate((prelaunch.y[-1, :-1], post_burn.y[-1]))

        def dense_state(sample_times: Any) -> Any:
            samples = np.asarray(sample_times, dtype=float)
            if samples.ndim == 0:
                value = float(samples)
                return prelaunch.sol(value) if value < 0.0 else post_burn.sol(value)
            return np.column_stack(
                [
                    prelaunch.sol(float(value)) if value < 0.0 else post_burn.sol(float(value))
                    for value in samples
                ]
            )

        solver_evaluations = prelaunch.nfev + post_burn.nfev
        initial_temperature = prelaunch.y[:count, 0]
        final_temperature = post_burn.y[:count, -1]
        net_external_energy = float(post_burn.y[-1, -1])
        ignition_temperature = ignition_state[:count]
        prelaunch_stored_energy = float(capacities @ (ignition_temperature - initial_temperature))
        prelaunch_external_energy = float(ignition_state[-1])
        ids_for_warmup = [liner.id, *other_ids]
        ignition_part_temperature = np.concatenate(
            (
                [ignition_temperature[:cells] @ wall.capacities_j_k / sum(wall.capacities_j_k)],
                ignition_temperature[cells:],
            )
        )
        prelaunch_energy_balance = {
            "units": {"temperature": "K", "energy": "J", "time": "s", "power": "W"},
            "duration_s": prelaunch_powered_soak_s,
            "interval_s_ignition_relative": [start, 0.0],
            "start_condition": "thermal nodes initialized from configured ambient plus any study-level part overrides; electronics power active through prelaunch interval",
            "case_boundary_during_prelaunch_c": float(ambient - 273.15),
            "electronics_power_w": float(settings["electronics_heat_w"][scenario]),
            "electronics_energy_input_j": float(
                settings["electronics_heat_w"][scenario] * prelaunch_powered_soak_s
            ),
            "start_temperature_c": float(initial_base_k - 273.15),
            "start_temperature_by_part_c": {
                name: float(value - 273.15)
                for name, value in zip(
                    ids,
                    np.concatenate(
                        (
                            [
                                initial_temperature[:cells]
                                @ wall.capacities_j_k
                                / sum(wall.capacities_j_k)
                            ],
                            initial_temperature[cells:],
                        )
                    ),
                    strict=True,
                )
            },
            "ignition_temperature_by_part_c": {
                name: float(value - 273.15)
                for name, value in zip(ids_for_warmup, ignition_part_temperature, strict=True)
            },
            "ignition_temperature_by_node_c": {
                **{
                    f"{liner.id}.cell_{index}": float(value - 273.15)
                    for index, value in enumerate(ignition_temperature[:cells])
                },
                **{
                    name: float(ignition_temperature[cells + index] - 273.15)
                    for index, name in enumerate(other_ids)
                },
            },
            "stored_energy_since_uniform_ambient_j": prelaunch_stored_energy,
            "net_external_energy_since_uniform_ambient_j": prelaunch_external_energy,
            "energy_balance_residual_j": prelaunch_stored_energy - prelaunch_external_energy,
            "evidence": "calculated using the shared thermal rates/RHS; electronics power is the configured estimated 1 W flight-computer load for this scenario",
        }
    temperatures = np.column_stack(
        (
            states[:, :cells] @ wall.capacities_j_k / sum(wall.capacities_j_k),
            states[:, cells:],
        )
    )
    initial_part_temperature = np.concatenate(
        (
            [initial_temperature[:cells] @ wall.capacities_j_k / sum(wall.capacities_j_k)],
            initial_temperature[cells:],
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

    def sample_rates(sample_times: np.ndarray) -> tuple[np.ndarray, dict[str, dict[str, Any]]]:
        sampled_states = dense_state(sample_times)[:count].T
        node_rates = np.zeros((len(sample_times), count))
        histories: dict[str, dict[str, Any]] = {}
        for sample_index, (sample_time, sample_state) in enumerate(
            zip(sample_times, sampled_states, strict=True)
        ):
            q, _, links = rates(float(sample_time), sample_state)
            node_rates[sample_index] = q
            for name, source_id, target_id, kind, flux_w in links:
                entry = histories.setdefault(
                    name,
                    {
                        "connection": name,
                        "source": source_id,
                        "target": target_id,
                        "type": kind,
                        "positive_direction": f"{source_id} -> {target_id}",
                        "flux_w": [],
                    },
                )
                entry["flux_w"].append(float(flux_w))
        return node_rates, histories

    if heat_flow_step_s <= 0:
        raise ValueError("heat_flow_step_s must be positive")
    fine_step_s = min(heat_flow_step_s, max_step_s)
    timeline_start = -prelaunch_powered_soak_s
    fine_times = np.unique(np.append(np.arange(timeline_start, end, fine_step_s), [0.0, burn, end]))
    fine_node_rates, fine_links = sample_rates(fine_times)
    coarse_node_rates, coarse_links = sample_rates(times)
    for name, entry in fine_links.items():
        flux = np.asarray(entry["flux_w"], dtype=float)
        positive = np.maximum(flux, 0.0)
        negative = np.maximum(-flux, 0.0)
        coarse_flux = np.asarray(coarse_links[name]["flux_w"], dtype=float)
        del entry["flux_w"]
        entry.update(
            {
                "units": {"flux": "W", "energy": "J", "time": "s"},
                "history_times_s": times.tolist(),
                "flux_w_by_time": coarse_flux.tolist(),
                "net_energy_j": float(np.trapezoid(flux, fine_times)),
                "positive_energy_j": float(np.trapezoid(positive, fine_times)),
                "negative_energy_j": float(np.trapezoid(negative, fine_times)),
                "positive_peak_w": float(positive.max()),
                "negative_peak_w": float(negative.max()),
                "coarse_1s_net_energy_j": float(np.trapezoid(coarse_flux, times)),
                "quadrature_refinement_delta_j": float(
                    np.trapezoid(flux, fine_times) - np.trapezoid(coarse_flux, times)
                ),
            }
        )
    node_names = [f"motor_liner.cell_{i}" for i in range(cells)] + other_ids
    node_balance = []
    for node, name in enumerate(node_names):
        stored_j = float(capacities[node] * (final_temperature[node] - initial_temperature[node]))
        net_fine_j = float(np.trapezoid(fine_node_rates[:, node], fine_times))
        net_coarse_j = float(np.trapezoid(coarse_node_rates[:, node], times))
        node_balance.append(
            {
                "node": name,
                "heat_capacity_j_k": float(capacities[node]),
                "initial_temperature_k": float(initial_temperature[node]),
                "final_temperature_k": float(final_temperature[node]),
                "stored_energy_j": stored_j,
                "integrated_net_heat_fine_j": net_fine_j,
                "balance_residual_fine_j": stored_j - net_fine_j,
                "integrated_net_heat_1s_j": net_coarse_j,
                "balance_residual_1s_j": stored_j - net_coarse_j,
                "quadrature_refinement_delta_j": net_fine_j - net_coarse_j,
            }
        )
    heat_flow = {
        "units": {"flux": "W", "energy": "J", "temperature": "K", "time": "s"},
        "times_s": times.tolist(),
        "fine_sample_step_s": fine_step_s,
        "integration": "trapezoid; fine sampling uses the ODE solver dense output at <=0.5 s without changing solver integration or the thermal solution",
        "sign_convention": "positive follows source -> target; negative_energy_j is the magnitude of reverse flow",
        "connections": list(fine_links.values()),
        "node_energy_balance": node_balance,
        "maximum_abs_node_balance_residual_fine_j": max(
            abs(row["balance_residual_fine_j"]) for row in node_balance
        ),
        "maximum_abs_node_balance_residual_1s_j": max(
            abs(row["balance_residual_1s_j"]) for row in node_balance
        ),
    }
    return {
        "model": "neutral-coaxial-material-shield-v3",
        "case": case_ids[scenario],
        "scenario_index": scenario,
        "ambient_c": float(ambient - 273.15),
        "prescribed_case_peak_c": float(peak - 273.15),
        "prelaunch_powered_soak_s": prelaunch_powered_soak_s,
        "prelaunch_energy_balance": prelaunch_energy_balance,
        "initial_condition": {
            "units": {"temperature": "C"},
            "basis": "configured ambient unless study initial_temperature_c or per-part overrides are provided",
            "configured_ambient_c": float(ambient - 273.15),
            "requested_part_overrides_c": {
                name: float(value) for name, value in initial_part_overrides.items()
            },
            "overrides_not_present_in_vehicle": sorted(absent_initial_overrides),
            "initial_temperature_by_part_c": {
                name: float(value - 273.15)
                for name, value in zip(ids, initial_part_temperature, strict=True)
            },
            "initial_temperature_by_node_c": {
                **{
                    f"{liner.id}.cell_{index}": float(value - 273.15)
                    for index, value in enumerate(initial_temperature[:cells])
                },
                **{
                    name: float(initial_temperature[cells + index] - 273.15)
                    for index, name in enumerate(other_ids)
                },
            },
        },
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
        "lumped_contact_paths": lumped_contact_metadata,
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
            np.max(np.abs((states - initial_temperature) @ capacities - external_energy_history))
        ),
        "net_external_energy_j": net_external_energy,
        "heat_flow": heat_flow,
        "solver_max_step_s": max_step_s,
        "solver_evaluations": solver_evaluations,
        "case_boundary_basis": settings["case_boundary_basis"],
        "limitations": study["limitations"],
        "thermal_acceptance_passed": False,
        "flight_ready": False,
    }
