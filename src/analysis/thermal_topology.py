"""Axially partitioned coaxial thermal reduction of the neutral aft assembly.

The actual spec supplies annular parts and frame-ring stations. In each axial band
only adjacent radial barriers exchange through air conduction and grey diffuse
radiation. This removes the legacy case-to-everything radiation bypass. The liner
has radial finite volumes; other parts remain single thermal capacities. Sparse
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
from src.analysis.thermal_radial import SIGMA, annular_wall, opaque_gap_flux, wall_heat_rates
from src.vehicle.schema import Part, Vehicle


def annular_intervals(part: Part) -> list[tuple[float, float]]:
    """Continuous annular portions only; do not turn a frame's rails into a tube."""
    assert part.cad
    start = part.position_m
    length = part.geometry["length_m"]
    options = part.cad.parameters
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
    severe: bool,
    cells: int = 8,
    max_step_s: float = 2,
) -> dict[str, Any]:
    assert vehicle.motor
    parts = {p.id: p for p in vehicle.parts}
    liner = parts["motor_liner"]
    motor = parts["motor"]
    settings = cfg["thermal"]
    scenario = int(severe)
    ambient = settings["ambient_c"][scenario] + 273.15
    peak = settings["external_case_peak_c"][scenario] + 273.15
    tau = settings["post_burn_cooling_tau_s"][scenario]
    air_k = settings["air_conductivity_w_m_k"][scenario]
    emissivity = settings["emissivity"][scenario]
    convection = settings["surface_h_w_m2_k"][1 - scenario]
    burn = vehicle.motor.burn_time_s

    def profile(part: Part) -> dict[str, Any]:
        return dict(cfg["materials"].get(material_profile(part), cfg["materials"]["commercial"]))

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
    gaps = []
    descriptions = []
    for start, end in pairwise(cuts):
        if end - start < 1e-10:
            continue
        midpoint = (start + end) / 2
        present = sorted(
            {name for a, b, name in barriers if a <= midpoint <= b},
            key=lambda name: parts[name].geometry["inner_radius_m"],
        )
        sequence = [liner.id, *present]
        descriptions.append({"axial_interval_m": [start, end], "radial_sequence": sequence})
        for source, target in pairwise(sequence):
            a, b = parts[source], parts[target]
            ra, rb = a.geometry["radius_m"], b.geometry["inner_radius_m"]
            if rb <= ra:
                raise ValueError(f"Overlapping coaxial barriers: {source}/{target}")
            length = end - start
            # Receiver/source body nodes are logarithmic midsurfaces. The actual
            # liner outermost cell centre replaces the whole-wall mean radius.
            ca = (
                float(wall.centres_m[-1])
                if source == liner.id
                else np.sqrt(a.geometry["inner_radius_m"] * a.geometry["radius_m"])
            )
            cb = np.sqrt(b.geometry["inner_radius_m"] * b.geometry["radius_m"])
            resistance_a = np.log(ra / ca) / (2 * np.pi * profile(a)["conductivity_w_m_k"] * length)
            resistance_b = np.log(cb / rb) / (2 * np.pi * profile(b)["conductivity_w_m_k"] * length)
            gaps.append(
                (
                    cells - 1 if source == liner.id else index[source],
                    index[target],
                    float(resistance_a),
                    float(resistance_b),
                    ra,
                    rb,
                    length,
                )
            )
    contacts = [
        (index[a], index[b], study["contact_conductance_w_k"][scenario])
        for a, b in study["contact_pairs"]
        if a in index and b in index
    ]
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
        )
        q[0] += case_heat
        for a, b, resistance_a, resistance_b, ra, rb, length in gaps:
            flux = opaque_gap_flux(
                float(temperature[a]),
                float(temperature[b]),
                resistance_a,
                resistance_b,
                ra,
                rb,
                length,
                air_k,
                emissivity,
            )
            q[a] -= flux
            q[b] += flux
        for a, b, conductance in contacts:
            flux = conductance * (temperature[b] - temperature[a])
            q[a] += flux
            q[b] -= flux
        shell_n = index["aft_shell"]
        shell_loss = shell_area * (
            convection * (ambient - temperature[shell_n])
            + emissivity * SIGMA * (ambient**4 - temperature[shell_n] ** 4)
        )
        q[shell_n] += shell_loss
        external = case_heat + shell_loss
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
        limit = profile(parts[name])["limit_c"]
        peaks.append(
            {
                "part_id": name,
                "peak_c": maximum,
                "peak_time_s": float(times[np.argmax(temperatures[:, n])]),
                "screen_limit_c": limit,
                "margin_k": limit - maximum,
                "passed": maximum <= limit,
                "evidence": "calculated with estimated inputs",
            }
        )
    return {
        "model": "neutral-coaxial-opaque-bands-v2",
        "case": "upper-hot-soak" if severe else "lower-case-scenario",
        "radial_cells": cells,
        "radial_centres_m": wall.centres_m.tolist(),
        "times_s": times.tolist(),
        "part_ids": ids,
        "temperature_k": temperatures.tolist(),
        "liner_radial_temperature_k": states[:, :cells].tolist(),
        "liner_radial_peak_c": float(states[:, :cells].max() - 273.15),
        "peaks": peaks,
        "radial_bands": descriptions,
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
