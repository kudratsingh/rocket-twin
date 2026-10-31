"""Finite radiation and gas exchange at the SAME massless physical surfaces.

This adapter assigns actual cylindrical/annular faces a material half-wall path,
adds gas conduction only between the adjacent faces named by the axial topology,
and uses SurfaceNetwork to solve their common temperatures. Direct and lumped
contacts stay in the caller. Fixed motor/fore/aft reservoir radiation is explicit.
The finite view factors are a declared coaxial proxy: angular rails, slots and
sector supports are not restored by this coupling step. It is not a complete-CAD
temperature bound. Equations/references: src.analysis.surface_thermal and
src.analysis.finite_radiation; annular half-wall R=abs(ln(r_face/r_mid))/(2*pi*k*L)
and axial half-wall R=(physical thickness/2)/(k*A), Bergman et al., Fundamentals
of Heat and Mass Transfer, 7th ed., chapters 3 and 13.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any

import numpy as np

from src.analysis.engineering import material_profile
from src.analysis.finite_radiation import Patch, condense_radiosity
from src.analysis.surface_thermal import SurfaceNetwork
from src.vehicle.schema import Part, Vehicle


class FiniteSurfaceAdapter:
    """Prepare once for a declared ODE order; evaluate fully coupled inward watts.

    Physical patches sharing (part, face, radius/plane) are isothermal groups.
    Every ring axial face remains separate by its plane station. This is a
    disclosed surface-temperature resolution, independent of ray refinement.
    """

    RESERVOIRS = ("motor_case_boundary", "fore_end_reservoir", "aft_end_reservoir")

    def __init__(
        self,
        vehicle: Vehicle,
        materials: dict[str, Any],
        patches: list[Patch],
        view_factors: Any,
        emissivities: Any,
        *,
        end_boundary_modes: dict[str, str],
        provenance: dict[str, Any],
        surface_tolerance_w: float = 1e-7,
    ):
        self.vehicle = vehicle
        self.parts = {part.id: part for part in vehicle.parts}
        self.materials = materials
        self.patches = patches
        self.provenance = dict(provenance)
        self.end_boundary_modes = dict(end_boundary_modes)
        self.surface_tolerance_w = float(surface_tolerance_w)
        mount = self.parts["motor_mount"]
        if vehicle.tvc is not None or mount.cad is None or mount.cad.generator != "mount":
            raise ValueError("Finite surface adapter currently supports fixed neutral mounts only")
        if set(end_boundary_modes) != set(self.RESERVOIRS[1:]) or any(
            mode not in {"ambient", "case"} for mode in end_boundary_modes.values()
        ):
            raise ValueError(
                "Both missing end reservoirs require explicit ambient/case assumptions"
            )
        if not np.isfinite(surface_tolerance_w) or surface_tolerance_w <= 0:
            raise ValueError("Positive finite common-surface tolerance required")
        identity = hashlib.sha256(vehicle.model_dump_json(by_alias=True).encode()).hexdigest()
        for key in ("candidate_identity", "source_candidate_identity"):
            if key in provenance and provenance[key] != identity:
                raise ValueError(
                    "Finite-surface source candidate identity does not match the vehicle"
                )
        self.provenance["actual_vehicle_identity_sha256"] = identity
        groups = []
        self.group_patches: dict[str, list[Patch]] = defaultdict(list)
        for patch in patches:
            self._check_patch_geometry(patch)
            if patch.part_id == "motor":
                name = "motor_case_boundary"
            elif patch.part_id == "fore_aperture":
                name = "fore_end_reservoir"
            elif patch.part_id == "aft_aperture":
                name = "aft_end_reservoir"
            elif patch.unknown_boundary:
                raise ValueError(f"Unknown finite reservoir mapping: {patch.part_id}")
            else:
                name = f"surface:{patch.part_id}:{patch.face}:{patch.coordinate_m:.12g}"
                if patch.kind == "annulus":
                    name += f":{patch.lo_m:.12g}:{patch.hi_m:.12g}"
            groups.append(name)
            self.group_patches[name].append(patch)
        self.operator = condense_radiosity(
            view_factors, [patch.area_m2 for patch in patches], emissivities, groups
        )
        self.surface_names = tuple(
            name for name in self.operator.node_names if name not in self.RESERVOIRS
        )
        self.reservoir_names = tuple(
            name for name in self.RESERVOIRS if name in self.operator.node_names
        )
        self.surface_index = {name: i for i, name in enumerate(self.surface_names)}
        self.reservoir_index = {name: i for i, name in enumerate(self.reservoir_names)}
        self.patch_group_names = groups
        order = [
            self.operator.node_names.index(name)
            for name in (*self.surface_names, *self.reservoir_names)
        ]
        self.radiation_matrix = self.operator.inward_operator_w_k4[np.ix_(order, order)]
        self.network: SurfaceNetwork | None = None
        self.node_names: tuple[str, ...] = ()
        self._last_surface_k: Any = None
        self._calls = 0
        self._max_residual_w = 0.0
        self._max_energy_residual_w = 0.0
        self._max_iterations = 0
        self._prepare_metadata: dict[str, Any] = {}

    def _check_patch_geometry(self, patch: Patch) -> None:
        if patch.unknown_boundary:
            return
        if patch.part_id not in self.parts:
            raise ValueError(f"Finite patch has no candidate part: {patch.part_id}")
        part = self.parts[patch.part_id]
        ri = float(part.geometry.get("inner_radius_m", 0.0))
        ro = float(part.geometry["radius_m"])
        if patch.kind == "cylinder":
            expected = ri if patch.face == "inner_cylinder" else ro
            if abs(patch.coordinate_m - expected) > 1e-10:
                raise ValueError(f"Finite patch radius is stale: {patch.part_id}/{patch.face}")
            if (
                patch.lo_m < part.position_m - 1e-10
                or patch.hi_m > part.position_m + part.geometry["length_m"] + 1e-10
            ):
                raise ValueError(f"Finite patch axial coverage is stale: {patch.part_id}")
        elif patch.kind == "annulus":
            if patch.lo_m < ri - 1e-10 or patch.hi_m > ro + 1e-10:
                raise ValueError(f"Finite patch radial coverage is stale: {patch.part_id}")
        else:
            raise ValueError(f"Unsupported physical patch kind: {patch.kind}")

    def _conductivity(self, part: Part) -> float:
        name = material_profile(part)
        if name not in self.materials:
            raise ValueError(f"No material conductivity supplied for {part.id}: {name}")
        value = float(self.materials[name]["conductivity_w_m_k"])
        if not np.isfinite(value) or value <= 0:
            raise ValueError(f"Invalid material conductivity for {part.id}")
        return value

    def _axial_thickness(self, part: Part, patch: Patch) -> float:
        if part.cad and part.cad.generator == "mount":
            params = part.cad.parameters
            widths = params.get(
                "ring_thicknesses_mm",
                [params["ring_thickness_mm"]] * len(params["ring_stations_mm"]),
            )
            matches = []
            for station, width in zip(params["ring_stations_mm"], widths, strict=True):
                front = part.position_m + station * 0.001
                face = front if patch.face == "fore_face" else front + width * 0.001
                if abs(face - patch.coordinate_m) < 1e-10:
                    matches.append(width * 0.001)
            if len(matches) != 1:
                raise ValueError("Ring end-face half wall has ambiguous axial thickness")
            return float(matches[0])
        front = part.position_m
        end = front + part.geometry["length_m"]
        expected = front if patch.face == "fore_face" else end
        if abs(patch.coordinate_m - expected) > 1e-10:
            raise ValueError(f"End face is not at the candidate's physical end: {part.id}")
        return float(part.geometry["length_m"])

    def _material_path(self, patch: Patch, centres: Any) -> tuple[str, float]:
        part = self.parts[patch.part_id]
        conductivity = self._conductivity(part)
        if patch.part_id == "motor_liner":
            if patch.kind != "cylinder":
                raise ValueError("A liner end face needs an explicit radial-cell axial path")
            cell = 0 if patch.face == "inner_cylinder" else len(centres) - 1
            name = f"motor_liner.cell_{cell}"
            middle = float(centres[cell])
        else:
            name = part.id
            ri, ro = float(part.geometry["inner_radius_m"]), float(part.geometry["radius_m"])
            middle = float(np.sqrt(ri * ro))
        if patch.kind == "cylinder":
            resistance = abs(np.log(patch.coordinate_m / middle)) / (
                2 * np.pi * conductivity * (patch.hi_m - patch.lo_m)
            )
        else:
            resistance = self._axial_thickness(part, patch) / (2 * conductivity * patch.area_m2)
        if not np.isfinite(resistance) or resistance <= 0:
            raise ValueError(f"Invalid physical half-wall resistance: {patch.part_id}/{patch.face}")
        return name, float(1 / resistance)

    def _matching_cylinders(self, part: str, face: str, radius: float) -> list[tuple[str, Patch]]:
        return [
            (name, patch)
            for name, members in self.group_patches.items()
            for patch in members
            if patch.part_id == part
            and patch.kind == "cylinder"
            and patch.face == face
            and abs(patch.coordinate_m - radius) < 1e-10
        ]

    def _bond_proxy(self, interface: dict[str, Any]) -> dict[str, Any] | None:
        a, b = float(interface["start_m"]), float(interface["end_m"])
        ri, ro = float(interface["source_surface_radius_m"]), float(
            interface["target_surface_radius_m"]
        )
        for part in self.vehicle.parts:
            if (
                not part.id.startswith("mount_shell_bond_")
                or not part.cad
                or part.cad.generator != "tube"
            ):
                continue
            if (
                part.position_m <= a + 1e-10
                and part.position_m + part.geometry["length_m"] >= b - 1e-10
                and part.geometry["inner_radius_m"] <= ri + 1e-10
                and part.geometry["radius_m"] >= ro - 1e-10
            ):
                slotted = bool(part.cad.parameters.get("fin_slots", False))
                return {
                    "source_part_id": interface["source_part_id"],
                    "target_part_id": interface["target_part_id"],
                    "interval_m": [a, b],
                    "occupying_bond_part_id": part.id,
                    "actual_cad_has_fin_slots": slotted,
                    "classification": (
                        "slotted_bond_full_annulus_proxy_only"
                        if slotted
                        else "physically_full_annular_bond"
                    ),
                    "gas_and_radiation_through_proxy_adhesive": "excluded; existing explicit mount/bond/shell contact paths retained by caller",
                    "actual_slot_channel_fin_tab_potting_coverage": (
                        "unresolved; no complete-angular bound or acceptance"
                        if slotted
                        else "not slotted in source CAD"
                    ),
                }
        return None

    def prepare(
        self, node_names: list[str], case_gap: dict[str, Any], interfaces: list[dict[str, Any]]
    ) -> None:
        if len(set(node_names)) != len(node_names):
            raise ValueError("Thermal node identities must be unique")
        required = {
            "motor_radius_m",
            "liner_inner_radius_m",
            "start_m",
            "end_m",
            "air_conductivity_w_m_k",
            "liner_radial_centres_m",
        }
        if not required <= case_gap.keys():
            raise ValueError("Missing physical case-gap or current liner-cell context")
        self.node_names = tuple(node_names)
        node_index = {name: i for i, name in enumerate(node_names)}
        centres = np.asarray(case_gap["liner_radial_centres_m"], dtype=float)
        if (
            centres.ndim != 1
            or not len(centres)
            or not np.isfinite(centres).all()
            or np.any(centres <= 0)
        ):
            raise ValueError("Current liner radial cell centres must be finite positive radii")
        gm = np.zeros((len(self.surface_names), len(node_names)))
        gg = np.zeros((len(self.surface_names), len(self.surface_names)))
        gb = np.zeros((len(self.surface_names), len(self.reservoir_names)))
        halfwalls: list[dict[str, Any]] = []
        for name in self.surface_names:
            surface = self.surface_index[name]
            for patch in self.group_patches[name]:
                material_name, conductance = self._material_path(patch, centres)
                if material_name not in node_index:
                    raise ValueError(f"Finite surface has no ODE material node: {material_name}")
                gm[surface, node_index[material_name]] += conductance
            halfwalls.append(
                {
                    "surface_id": name,
                    "material_node": material_name,
                    "conductance_w_k": float(gm[surface].sum()),
                    "physical_patch_count": len(self.group_patches[name]),
                }
            )
        air_k = float(case_gap["air_conductivity_w_m_k"])
        if not np.isfinite(air_k) or air_k < 0:
            raise ValueError("Invalid gas conductivity")
        air_rows = []
        exclusions = []

        def add_gap(
            source_part: str,
            target_part: str,
            ra: float,
            rb: float,
            start: float,
            end: float,
            label: str,
        ) -> None:
            if not (0 < ra < rb and start < end):
                raise ValueError("Invalid adjacent coaxial gas-gap geometry")
            sources = self._matching_cylinders(source_part, "outer_cylinder", ra)
            targets = self._matching_cylinders(target_part, "inner_cylinder", rb)
            covered = 0.0
            total_g = 0.0
            for source_name, source_patch in sources:
                for target_name, target_patch in targets:
                    length = min(end, source_patch.hi_m, target_patch.hi_m) - max(
                        start, source_patch.lo_m, target_patch.lo_m
                    )
                    if length <= 1e-12:
                        continue
                    conductance = 2 * np.pi * air_k * length / np.log(rb / ra)
                    covered += length
                    total_g += conductance
                    if source_name in self.reservoir_index:
                        gb[
                            self.surface_index[target_name], self.reservoir_index[source_name]
                        ] += conductance
                    else:
                        i, j = self.surface_index[source_name], self.surface_index[target_name]
                        gg[i, j] += conductance
                        gg[j, i] += conductance
            if abs(covered - (end - start)) > max(1e-10, (end - start) * 1e-8):
                raise ValueError(
                    f"Incomplete or multiply allocated real gas surfaces for {label}: {covered}/{end-start} m"
                )
            air_rows.append(
                {
                    "connection": label,
                    "interval_m": [start, end],
                    "surface_overlap_length_m": covered,
                    "gas_only_conductance_w_k": total_g,
                    "half_walls": "supplied once by physical surface/material paths",
                }
            )

        add_gap(
            "motor",
            "motor_liner",
            float(case_gap["motor_radius_m"]),
            float(case_gap["liner_inner_radius_m"]),
            float(case_gap["start_m"]),
            float(case_gap["end_m"]),
            "motor_case_to_liner_inner",
        )
        for index, interface in enumerate(interfaces):
            if interface["model"] == "direct_solid_contact":
                continue
            if interface["model"] != "opaque_gap":
                raise ValueError("Unknown topology interface cannot be silently omitted")
            proxy = self._bond_proxy(interface)
            if proxy is not None:
                exclusions.append(proxy)
                continue
            add_gap(
                str(interface["source_part_id"]),
                str(interface["target_part_id"]),
                float(interface["source_surface_radius_m"]),
                float(interface["target_surface_radius_m"]),
                float(interface["start_m"]),
                float(interface["end_m"]),
                f"radial_interface_{index}",
            )
        self.network = SurfaceNetwork(gm, gg, gb, self.radiation_matrix)
        covered_nodes = sorted({row["material_node"] for row in halfwalls})
        self._prepare_metadata = {
            "thermal_node_names": list(self.node_names),
            "physical_halfwall_paths": halfwalls,
            "gas_surface_paths": air_rows,
            "legacy_gap_exclusions": exclusions,
            "surface_coupled_material_nodes": covered_nodes,
            "radiation_excluded_material_nodes": sorted(set(node_names) - set(covered_nodes)),
            "sector_pad_angular_occupancy_in_full_annular_gas_paths": "excluded; explicit existing spacer/contact paths remain caller-owned; no full-angular bound",
        }
        self._last_surface_k = None

    def rates(
        self, temperature: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> tuple[Any, float, list[tuple[str, str, str, str, float]]]:
        if self.network is None:
            raise ValueError("Finite surface exchange must prepare the exact ODE context first")
        material = np.asarray(temperature, dtype=float)
        boundaries = []
        for name in self.reservoir_names:
            if name == "motor_case_boundary":
                boundaries.append(case_temperature_k)
            else:
                boundaries.append(
                    ambient_temperature_k
                    if self.end_boundary_modes[name] == "ambient"
                    else case_temperature_k
                )
        solved = self.network.solve(
            material,
            np.array(boundaries),
            initial_surface_k=self._last_surface_k,
            absolute_tolerance_w=self.surface_tolerance_w,
        )
        self._last_surface_k = solved.surface_temperature_k
        self._calls += 1
        self._max_residual_w = max(
            self._max_residual_w, float(np.max(abs(solved.surface_residual_w)))
        )
        self._max_energy_residual_w = max(
            self._max_energy_residual_w, abs(solved.energy_residual_w)
        )
        self._max_iterations = max(self._max_iterations, solved.iterations)
        links = []
        gm = self.network.material_conductance_w_k
        for surface, node in zip(*np.nonzero(gm), strict=True):
            flux = gm[surface, node] * (solved.surface_temperature_k[surface] - material[node])
            links.append(
                (
                    f"finite_surface_to_material:{self.surface_names[surface]}->{self.node_names[node]}",
                    self.surface_names[surface],
                    self.node_names[node],
                    "coupled_finite_surface_halfwall",
                    float(flux),
                )
            )
        for name, heat in zip(self.reservoir_names, solved.reservoir_heat_w, strict=True):
            links.append(
                (
                    f"finite_reservoir:{name}",
                    name,
                    "finite_massless_surfaces",
                    "coupled_finite_reservoir_net_input",
                    float(-heat),
                )
            )
        return solved.material_heat_w, float(-sum(solved.reservoir_heat_w)), links

    def jacobian(
        self, temperature: Any, *, case_temperature_k: float, ambient_temperature_k: float
    ) -> tuple[Any, Any]:
        """Exact implicit material derivatives at the converged physical surfaces."""
        self.rates(
            temperature,
            case_temperature_k=case_temperature_k,
            ambient_temperature_k=ambient_temperature_k,
        )
        assert self.network is not None and self._last_surface_k is not None
        material, reservoir = self.network.material_temperature_jacobian(self._last_surface_k)
        return material, -reservoir.sum(axis=0)

    def metadata(self) -> dict[str, Any]:
        return {
            **self.provenance,
            **self._prepare_metadata,
            "model": "finite_diffuse_radiation_and_gas_common_massless_surfaces_coaxial_proxy_v1",
            "surface_grouping": "part/face/radius-or-plane; annular radial extent retained; axial ray patches on the same cylindrical face share temperature",
            "surface_names": list(self.surface_names),
            "reservoir_names": list(self.reservoir_names),
            "end_boundary_modes": self.end_boundary_modes,
            "condensation": self.operator.checks,
            "common_surface_tolerance_w": self.surface_tolerance_w,
            "surface_solve_calls": self._calls,
            "maximum_surface_residual_w": self._max_residual_w,
            "maximum_surface_energy_residual_w": self._max_energy_residual_w,
            "maximum_surface_newton_iterations": self._max_iterations,
            "material_jacobian": "implicit analytic differentiation of the converged common-surface equations; prescribed reservoir temperatures held fixed",
            "direct_and_lumped_contacts": "caller-owned and retained; no contact radiation added",
            "actual_angular_cad_radiation": "unavailable: rails/slots/sector pads/foil seams excluded by source coaxial matrix",
            "actual_end_nozzle_upper_bay_geometry": "unavailable: explicit black end reservoir uncertainty retained",
            "full_cad_conservative_bound": False,
            "thermal_acceptance_available": False,
            "flight_ready": False,
        }
