"""Recorded actual-CAD surface exchange hook for the existing transient solver.

This optional diagnostic projection keeps the existing solid PART-MEAN states:
component Robin paths see their explicitly named parent temperature and their
heat rates sum back to that parent. Heat capacities and existing solid contacts
remain owned once by thermal_topology.py. Liner radial cells stay distinct.
Gas and radiation retain the common physical surface calculation.

This is NOT a bound on local solid temperature or an assertion that disconnected
components equilibrate instantly in hardware. The caller must retain that
infinite-internal-redistribution approximation in every result/export. A positive
part-mean margin cannot close a local hot-spot finding. References and numerical
verification: gas_radiation.py and robin_gas.py; parent projection is the incidence
mapping T_component=S*T_parent, Q_parent=S.T*Q_component.
"""

from __future__ import annotations

from typing import Any

import numpy as np

from src.analysis.gas_radiation import GasRadiationNetwork, GasRadiationSolution


class CadGasSurfaceAdapter:
    def __init__(
        self,
        network: GasRadiationNetwork,
        component_bulk_to_transient_node: dict[str, str],
        prescribed_temperature_hypotheses: dict[str, str],
        brightness_temperature_hypotheses: dict[str, str],
        provenance: dict[str, Any],
        *,
        absolute_tolerance_k: float = 1e-8,
    ):
        """Hypotheses must explicitly select ``case`` or ``ambient`` per input.

        Motor ends are not silently assigned case temperature; a caller choosing
        that hypothesis must name each end independently in the metadata. No
        spatial gradient, physical measurement or operating limit is inferred.
        """
        gas = network.gas
        if set(component_bulk_to_transient_node) != set(gas.bulk_ids):
            raise ValueError("Every component bulk must have an explicit transient-state mapping")
        if set(prescribed_temperature_hypotheses) != set(gas.prescribed_ids):
            raise ValueError("Every prescribed gas/motor temperature needs an explicit hypothesis")
        if set(brightness_temperature_hypotheses) != set(network.brightness_ids):
            raise ValueError("Every opening brightness needs its own explicit hypothesis")
        if any(
            mode not in {"case", "ambient"}
            for mode in [
                *prescribed_temperature_hypotheses.values(),
                *brightness_temperature_hypotheses.values(),
            ]
        ):
            raise ValueError("Supported diagnostic temperature hypotheses are case or ambient")
        if absolute_tolerance_k <= 0:
            raise ValueError("Positive surface tolerance required")
        self.network = network
        self.bulk_nodes = dict(component_bulk_to_transient_node)
        self.prescribed = dict(prescribed_temperature_hypotheses)
        self.brightness = dict(brightness_temperature_hypotheses)
        self.provenance = dict(provenance)
        self.tolerance = absolute_tolerance_k
        self.mapping: Any = None
        self.last_solution: GasRadiationSolution | None = None
        self.last_inputs: Any = None
        self.maximum_residual_k = 0.0
        self.maximum_energy_residual_w = 0.0
        self.calls = 0
        self.node_names: tuple[str, ...] = ()

    def prepare(
        self, node_names: list[str], case_gap: dict[str, Any], interfaces: list[dict[str, Any]]
    ) -> None:
        if len(set(node_names)) != len(node_names):
            raise ValueError("Transient node identities must be unique")
        if not set(self.bulk_nodes.values()) <= set(node_names):
            raise ValueError(
                "Actual-CAD thermal material states are missing from transient capacities"
            )
        if not np.isclose(
            case_gap["air_conductivity_w_m_k"],
            self.network.gas.diagnostics["conductivity_w_m_k"],
            rtol=1e-12,
            atol=0,
        ):
            raise ValueError("Gas operator conductivity disagrees with the current scenario")
        index = {name: i for i, name in enumerate(node_names)}
        self.mapping = np.zeros((len(self.network.gas.bulk_ids), len(node_names)))
        for i, name in enumerate(self.network.gas.bulk_ids):
            self.mapping[i, index[self.bulk_nodes[name]]] = 1
        # Keep each explicit FV identity; no whole-liner mean projection.
        for name in self.network.gas.bulk_ids:
            if name.startswith("motor_liner.cell_") and self.bulk_nodes[name] != name:
                raise ValueError("Liner radial finite-volume states cannot collapse to a part mean")
        self.node_names = tuple(node_names)
        self.last_inputs = None
        self.provenance["legacy_opaque_gaps_replaced"] = sum(
            i["model"] != "direct_solid_contact" for i in interfaces
        )
        self.provenance["legacy_direct_solid_contacts_retained_by_caller"] = sum(
            i["model"] == "direct_solid_contact" for i in interfaces
        )

    def _solution(self, temperature: Any, case: float, ambient: float) -> GasRadiationSolution:
        if self.mapping is None:
            raise ValueError("Actual-CAD adapter must prepare against the current transient states")
        t = np.asarray(temperature, dtype=float)
        if t.shape != (len(self.node_names),):
            raise ValueError("Transient temperatures do not match the prepared state mapping")
        values = {"case": case, "ambient": ambient}
        prescribed = np.array([values[self.prescribed[n]] for n in self.network.gas.prescribed_ids])
        brightness = np.array([values[self.brightness[n]] for n in self.network.brightness_ids])
        key = (t.tobytes(), float(case), float(ambient))
        if self.last_inputs == key:
            assert self.last_solution is not None
            return self.last_solution
        result = self.network.solve(
            self.mapping @ t,
            prescribed,
            brightness,
            initial_surface_k=(
                None if self.last_solution is None else self.last_solution.surface_area_mean_k
            ),
            absolute_tolerance_k=self.tolerance,
        )
        self.calls += 1
        self.maximum_residual_k = max(self.maximum_residual_k, result.surface_residual_k)
        self.maximum_energy_residual_w = max(
            self.maximum_energy_residual_w, abs(result.enclosure_energy_residual_w)
        )
        self.last_inputs, self.last_solution = key, result
        return result

    def rates(
        self, temperature: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> tuple[Any, float, list[tuple[str, str, str, str, float]]]:
        solution = self._solution(temperature, case_temperature_k, ambient_temperature_k)
        nb = len(self.network.gas.bulk_ids)
        heat = self.mapping.T @ solution.heat_into_material_and_gas_reservoir_w[:nb]
        external = -float(
            solution.heat_into_material_and_gas_reservoir_w[nb:].sum()
            + solution.heat_into_radiative_brightness_reservoir_w.sum()
        )
        links = [
            (
                f"actual_cad_surface:{name}",
                "actual_cad_common_surface_field",
                name,
                "net_common_surface_gas_and_radiation",
                float(heat[i]),
            )
            for i, name in enumerate(self.node_names)
        ]
        return heat, external, links

    def jacobian(
        self, temperature: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> tuple[Any, Any]:
        solution = self._solution(temperature, case_temperature_k, ambient_temperature_k)
        nb = len(self.network.gas.bulk_ids)
        derivative = solution.state_heat_jacobian_w_k
        heat_jac = self.mapping.T @ derivative[:nb] @ self.mapping
        # All internal surface exchange sums to zero including radiative
        # brightness reservoirs, so d(net heat into material)=sum dQ_material.
        return heat_jac, np.sum(heat_jac, axis=0)

    def metadata(self) -> dict[str, Any]:
        return {
            "method": "actual_CAD_gas_common_surface_with_explicit_parent_mean_projection",
            "provenance": self.provenance,
            "component_bulk_to_transient_node": self.bulk_nodes,
            "prescribed_gas_temperature_hypotheses": self.prescribed,
            "radiative_brightness_hypotheses": self.brightness,
            "surface_calls": self.calls,
            "maximum_surface_residual_k": self.maximum_residual_k,
            "maximum_enclosure_energy_residual_w": self.maximum_energy_residual_w,
            "capacities_and_existing_solid_contacts_owned_once_by_transient_caller": True,
            "part_mean_projection_is_physical_isothermality_or_local_temperature_bound": False,
            "local_solid_hot_spots": "unavailable",
            "engineering_acceptance": False,
            "flight_ready": False,
        }
