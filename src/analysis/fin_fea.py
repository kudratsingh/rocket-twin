"""Quadratic shell static/modal screens of the actual single-fin planform.

Gmsh independent analysis meshes, CalculiX S6 shell, N/mm/MPa/tonne units.
Consistent uniform pressure loads put zero force on triangle vertices and A*p/3
on midside nodes. Actual root tabs are included and idealized clamped at/below the
body tangent. The root attachment is an upper-stiffness assumption, not a bond
qualification. Regional stresses exclude the first two thicknesses from the ideal
clamp and remain distinct from whole-part/root-joint strength.
Reference: CalculiX 2.23 S6 shell, NODE/EL PRINT and FREQUENCY documentation;
CalculiX *ELASTIC engineering constants, *ORIENTATION and *SHELL SECTION
documentation; Euler-Bernoulli uniform cantilever u=FL^3/(8EI),
f1=1.875104^2/(2piL^2)*sqrt(EI/mu).
"""

from __future__ import annotations

import hashlib
import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np

from src.analysis.fea import solver_path
from src.vehicle.materials import DENSITY_KG_M3
from src.vehicle.schema import Part


def orthotropic_compliance(constants: dict[str, float]) -> np.ndarray:
    """Return the symmetric 3D compliance matrix in SI engineering units."""
    required = (
        "E1_pa",
        "E2_pa",
        "E3_pa",
        "nu12",
        "nu13",
        "nu23",
        "G12_pa",
        "G13_pa",
        "G23_pa",
    )
    if any(key not in constants for key in required):
        raise ValueError("Orthotropic material is missing an engineering constant")
    e1, e2, e3 = (float(constants[key]) for key in ("E1_pa", "E2_pa", "E3_pa"))
    g12, g13, g23 = (float(constants[key]) for key in ("G12_pa", "G13_pa", "G23_pa"))
    nu12, nu13, nu23 = (float(constants[key]) for key in ("nu12", "nu13", "nu23"))
    if min(e1, e2, e3, g12, g13, g23) <= 0:
        raise ValueError("Orthotropic Young and shear moduli must be positive")
    compliance = np.zeros((6, 6), dtype=float)
    compliance[0, 0], compliance[1, 1], compliance[2, 2] = 1 / e1, 1 / e2, 1 / e3
    compliance[0, 1] = compliance[1, 0] = -nu12 / e1
    compliance[0, 2] = compliance[2, 0] = -nu13 / e1
    compliance[1, 2] = compliance[2, 1] = -nu23 / e2
    compliance[3, 3], compliance[4, 4], compliance[5, 5] = 1 / g23, 1 / g13, 1 / g12
    if float(np.linalg.eigvalsh(compliance).min()) <= 0:
        raise ValueError("Orthotropic constants produce a non-positive compliance matrix")
    return compliance


def _resolved_density(part: Any | None, explicit_density_kg_m3: float | None) -> float:
    if explicit_density_kg_m3 is not None:
        if explicit_density_kg_m3 <= 0:
            raise ValueError("density_kg_m3 must be positive")
        return float(explicit_density_kg_m3)
    return float(DENSITY_KG_M3[part.material]) if part else 550.0


def shell_thickness_mm(
    span_x_mm: float, base_thickness_mm: float, cad_parameters: dict[str, Any]
) -> float:
    """Equivalent S6 thickness for paired triangular root-gusset material."""
    keys = ("root_gusset_span_mm", "root_gusset_base_mm", "root_gusset_inset_mm")
    present = [key in cad_parameters for key in keys]
    if any(present) and not all(present):
        raise ValueError("Root gusset thickness profile requires all three CAD parameters")
    if not all(present) or span_x_mm < 0:
        return base_thickness_mm
    gusset_span, gusset_base, gusset_inset = (float(cad_parameters[key]) for key in keys)
    if min(gusset_span, gusset_base) <= 0 or gusset_inset < 0:
        raise ValueError("Root gusset dimensions must be positive except nonnegative inset")
    added = 2 * gusset_base * max(0.0, (gusset_span - span_x_mm) / (gusset_span + gusset_inset))
    return base_thickness_mm + added


def uniform_load_beam_deflection_m(
    force_n: float,
    span_m: float,
    chord_m: float,
    youngs_pa: float,
    thickness_at_m: Any,
) -> float:
    """Euler-Bernoulli cantilever tip deflection for uniform chordwise pressure.

    Uses Gauss integration of w(L-x)^3/(2EI(x)); the thickness callable receives
    spanwise x in metres and returns thickness in metres.
    """
    if min(force_n, span_m, chord_m, youngs_pa) <= 0:
        raise ValueError("Beam fixture inputs must be positive")
    abscissa, weights = np.polynomial.legendre.leggauss(96)
    x = (abscissa + 1) * span_m / 2
    quad_weights = weights * span_m / 2
    load_per_length = force_n / span_m
    thickness = np.asarray([thickness_at_m(float(value)) for value in x])
    if np.any(thickness <= 0):
        raise ValueError("Beam thickness must remain positive")
    ei = youngs_pa * chord_m * thickness**3 / 12
    integrand = load_per_length * (span_m - x) ** 3 / (2 * ei)
    return float(np.sum(quad_weights * integrand))


def run_shell(
    folder: Path,
    part: Part | None,
    size_mm: float,
    young_pa: float = 2e9,
    density_kg_m3: float | None = None,
    force_n: float = 0.001,
    stiffness_fraction: float = 1.0,
    orthotropic: dict[str, float] | None = None,
) -> dict[str, Any]:
    gmsh: Any = importlib.import_module("gmsh")
    if gmsh.__version__ != "4.15.2":
        raise ValueError("Pinned Gmsh 4.15.2 required")
    if part:
        g = part.geometry
        o = part.cad.parameters if part.cad else {}
        span, root, tip, sweep, thickness = [
            g[k] * 1000 for k in ["span_m", "root_chord_m", "tip_chord_m", "sweep_m", "thickness_m"]
        ]
    else:
        span, root, tip, sweep, thickness = 100.0, 10.0, 10.0, 0.0, 1.0
        o = {}
    density_kg_m3 = _resolved_density(part, density_kg_m3)
    base_thickness_mm = float(thickness)
    has_root_gusset_profile = any(
        key in o for key in ("root_gusset_span_mm", "root_gusset_base_mm", "root_gusset_inset_mm")
    )
    if has_root_gusset_profile:
        # Validate the complete profile before allocating Gmsh state.
        shell_thickness_mm(0.0, base_thickness_mm, o)
    folder.mkdir(parents=True, exist_ok=True)
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 0)
        gmsh.model.add("single_fin_shell")
        coords = [(0.0, 0.0), (span, sweep), (span, sweep + tip), (0.0, root)]
        points = [gmsh.model.occ.addPoint(x, y, 0) for x, y in coords]
        lines = [gmsh.model.occ.addLine(a, b) for a, b in zip(points, points[1:] + points[:1])]
        face = gmsh.model.occ.addPlaneSurface([gmsh.model.occ.addCurveLoop(lines)])
        tools = []
        if has_root_gusset_profile:
            band_span = float(o["root_gusset_span_mm"])
            if abs(sweep) > 1e-9 or abs(root - tip) > 1e-9 or span < band_span:
                raise ValueError(
                    "Root-gusset S6 partition currently requires an unswept rectangular planform with adequate span"
                )
            band = gmsh.model.occ.addRectangle(0, 0, 0, band_span, root)
            tools.append((2, band))
        if o.get("tab_depth_mm"):
            tab = gmsh.model.occ.addRectangle(
                -o["tab_depth_mm"], o["tab_offset_mm"], 0, o["tab_depth_mm"], o["tab_length_mm"]
            )
            tools.append((2, tab))
        if tools:
            # Band boundaries conform to the fin and give the root refinement
            # region an explicit geometric partition.
            gmsh.model.occ.fragment([(2, face)], tools)
        gmsh.model.occ.synchronize()
        band_span = float(o.get("root_gusset_span_mm", 0.0))
        local_size = size_mm / 4 if has_root_gusset_profile else size_mm
        gmsh.option.setNumber("Mesh.MeshSizeMin", local_size)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        if has_root_gusset_profile:
            field = gmsh.model.mesh.field.add("Box")
            gmsh.model.mesh.field.setNumber(field, "VIn", local_size)
            gmsh.model.mesh.field.setNumber(field, "VOut", size_mm)
            gmsh.model.mesh.field.setNumber(field, "XMin", -float(o.get("tab_depth_mm", 0.0)))
            gmsh.model.mesh.field.setNumber(field, "XMax", band_span)
            gmsh.model.mesh.field.setNumber(field, "YMin", -1.0)
            gmsh.model.mesh.field.setNumber(field, "YMax", root + 1.0)
            gmsh.model.mesh.field.setNumber(field, "ZMin", -0.1)
            gmsh.model.mesh.field.setNumber(field, "ZMax", 0.1)
            gmsh.model.mesh.field.setNumber(field, "Thickness", max(size_mm / 4, 0.5))
            gmsh.model.mesh.field.setAsBackgroundMesh(field)
        gmsh.model.mesh.generate(2)
        gmsh.write(str(folder / "mesh.msh"))
        tags, xyz, _ = gmsh.model.mesh.getNodes()
        nodes = {int(n): np.array(x) for n, x in zip(tags, np.asarray(xyz).reshape(-1, 3))}
        types, tags, conn = gmsh.model.mesh.getElements(2)
        elements = {}
        for kind, ids, data in zip(types, tags, conn):
            if kind != 9:
                raise ValueError("Expected Gmsh six-node triangles")
            for id, row in zip(ids, np.asarray(data).reshape(-1, 6)):
                elements[int(id)] = [int(n) for n in row]
    finally:
        gmsh.finalize()
    exposed_area = span * (root + tip) / 2
    pressure = force_n / exposed_area
    loads: dict[int, float] = {}
    centroids = {}
    element_thickness: dict[int, float] = {}
    for id, tri in elements.items():
        xyz = np.array([nodes[n] for n in tri[:3]])
        center = xyz.mean(axis=0)
        centroids[id] = center
        element_thickness[id] = shell_thickness_mm(float(center[0]), base_thickness_mm, o)
        if center[0] <= 0:
            continue
        area = float(np.linalg.norm(np.cross(xyz[1] - xyz[0], xyz[2] - xyz[0])) / 2)
        for n in tri[3:]:
            loads[n] = loads.get(n, 0.0) + pressure * area / 3
    if abs(sum(loads.values()) - force_n) > abs(force_n) * 1e-8:
        raise ValueError("Fin traction resultant mismatch")
    root_band_edge_lengths = [
        float(np.linalg.norm(nodes[a] - nodes[b]))
        for element_id, connectivity in elements.items()
        if has_root_gusset_profile and centroids[element_id][0] <= float(o["root_gusset_span_mm"])
        for a, b in (
            (connectivity[0], connectivity[1]),
            (connectivity[1], connectivity[2]),
            (connectivity[2], connectivity[0]),
        )
    ]
    fixed = [n for n, x in nodes.items() if x[0] <= 1e-7]
    deck = ["*HEADING", "Single-fin/strip static and modal screen; N mm MPa tonne", "*NODE"]
    deck += [f"{n}, " + ", ".join(f"{v:.12g}" for v in x) for n, x in nodes.items()]
    deck += ["*ELEMENT,TYPE=S6,ELSET=FIN"] + [
        f"{n}, " + ", ".join(map(str, c)) for n, c in elements.items()
    ]
    for label, ids in [("FIXED", fixed), ("NALL", list(nodes))]:
        deck += [f"*NSET,NSET={label}"] + [
            ", ".join(map(str, ids[i : i + 12])) for i in range(0, len(ids), 12)
        ]
    thickness_groups: dict[int, list[int]] = {}
    if has_root_gusset_profile:
        for element_id, t_mm in element_thickness.items():
            section_key = round(t_mm * 100)
            thickness_groups.setdefault(section_key, []).append(element_id)
        for section_key, element_ids in sorted(thickness_groups.items()):
            deck += [f"*ELSET,ELSET=TSEC_{section_key:05d}"] + [
                ", ".join(map(str, element_ids[i : i + 12])) for i in range(0, len(element_ids), 12)
            ]
    deck += ["*MATERIAL,NAME=LOWERBOUND"]
    if orthotropic is None:
        deck += ["*ELASTIC", f"{young_pa*stiffness_fraction*1e-6:.12g},0.25"]
        section_orientation = ""
    else:
        orthotropic_compliance(orthotropic)
        deck += ["*ELASTIC,TYPE=ENGINEERING CONSTANTS"]
        scaled = [
            float(orthotropic[key]) * (stiffness_fraction if key.endswith("_pa") else 1.0) * 1e-6
            for key in (
                "E1_pa",
                "E2_pa",
                "E3_pa",
                "nu12",
                "nu13",
                "nu23",
                "G12_pa",
                "G13_pa",
                "G23_pa",
            )
        ]
        # CalculiX reads engineering constants as a pair: the first eight
        # constants, then G23 and the single-temperature reference.
        deck.append(",".join(f"{value:.12g}" for value in scaled[:8]))
        deck.append(f"{scaled[8]:.12g},0.0")
        deck += ["*ORIENTATION,NAME=SPAN_CHORD", "1,0,0,0,1,0"]
        section_orientation = ",ORIENTATION=SPAN_CHORD"
    deck += ["*DENSITY", f"{density_kg_m3*1e-12:.12g}"]
    if has_root_gusset_profile:
        for section_key in sorted(thickness_groups):
            deck += [
                f"*SHELL SECTION,ELSET=TSEC_{section_key:05d},MATERIAL=LOWERBOUND"
                + section_orientation,
                f"{section_key / 100:.2f}",
            ]
    else:
        deck += [
            "*SHELL SECTION,ELSET=FIN,MATERIAL=LOWERBOUND" + section_orientation,
            str(thickness),
        ]
    deck += [
        "*BOUNDARY",
        "FIXED,1,6,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    deck += [f"{n},3,{f:.12g}" for n, f in loads.items()]
    deck += [
        "*NODE PRINT,NSET=NALL",
        "U",
        "*NODE PRINT,NSET=FIXED",
        "RF",
        "*EL PRINT,ELSET=FIN",
        "S",
        "*NODE FILE",
        "U",
        "*END STEP",
        "*STEP",
        "*FREQUENCY",
        "6",
        "*NODE PRINT,NSET=NALL",
        "U",
        "*NODE FILE",
        "U",
        "*END STEP",
    ]
    inp = folder / "case.inp"
    inp.write_text("\n".join(deck) + "\n")
    mesh = {
        "frame": "FEM X=span from body tangent; Y=chord aft from fin front; Z=plate normal; mm",
        "nodes": [{"id": n, "xyz_mm": x.tolist()} for n, x in nodes.items()],
        "elements": [
            {
                "id": n,
                "type": "S6",
                "nodes": c,
                "thickness_mm": round(element_thickness[n], 2),
            }
            for n, c in elements.items()
        ],
        "root_refined_band": (
            {
                "spanwise_range_mm": [0.0, float(o["root_gusset_span_mm"])],
                "target_element_size_mm": size_mm / 4,
                "geometry_partitioned": True,
            }
            if has_root_gusset_profile
            else None
        ),
        "part_id": part.id if part else "known-strip",
        "coverage": "One fin, ideal clamped root/tab; other fins are not resolved by this field.",
    }
    (folder / "analysis-mesh.json").write_text(json.dumps(mesh) + "\n")
    result: dict[str, Any] = {
        "part_id": part.id if part else "known-strip",
        "part_shape_sha256": part.cad_mass.shape_sha256 if part and part.cad_mass else None,
        "gmsh": "4.15.2",
        "size_mm": size_mm,
        "root_band_target_element_size_mm": size_mm / 4 if has_root_gusset_profile else None,
        "root_band_element_count": (
            int(sum(center[0] <= float(o["root_gusset_span_mm"]) for center in centroids.values()))
            if has_root_gusset_profile
            else 0
        ),
        "root_band_corner_edge_lengths_mm": {
            "median": float(np.median(root_band_edge_lengths)) if root_band_edge_lengths else None,
            "maximum": float(max(root_band_edge_lengths)) if root_band_edge_lengths else None,
        },
        "nodes": len(nodes),
        "elements": len(elements),
        "force_n": force_n,
        "stiffness_fraction": stiffness_fraction,
        "youngs_pa": young_pa,
        "material_model": (
            "isotropic" if orthotropic is None else "orthotropic engineering constants"
        ),
        "material_axes": (
            None
            if orthotropic is None
            else "1=span, 2=chord, 3=plate normal; explicit shell in-plane orientation"
        ),
        "orthotropic_engineering_constants": orthotropic,
        "compliance_positive_definite": True,
        "density_kg_m3": density_kg_m3,
        "thickness_profile": {
            "base_thickness_mm": base_thickness_mm,
            "root_gusset_parameters": {
                key: float(o[key])
                for key in (
                    "root_gusset_span_mm",
                    "root_gusset_base_mm",
                    "root_gusset_inset_mm",
                )
                if key in o
            },
            "formula": "t(x)=t_base+2*b*max(0,(g-x)/(g+i)) for x>=0; t=t_base for x<0; element thickness sampled at each element centroid and rounded to 0.01 mm section bins.",
            "section_bin_mm": 0.01,
            "minimum_element_thickness_mm": min(element_thickness.values()),
            "maximum_element_thickness_mm": max(element_thickness.values()),
            "section_count": len(thickness_groups) if has_root_gusset_profile else 1,
            "model_status": (
                "Equivalent shell thickening for two side gussets; actual gusset bond/interface and three-dimensional foot detail are not modeled or qualified."
                if has_root_gusset_profile
                else "Constant thickness."
            ),
        },
        "input_sha256": hashlib.sha256(inp.read_bytes()).hexdigest(),
        "mesh_sha256": hashlib.sha256((folder / "analysis-mesh.json").read_bytes()).hexdigest(),
        "attachment": "Ideal clamp at and inside the body tangent; flexible root/bond not qualified",
        "solver_executed": False,
        "flight_ready": False,
    }
    ccx = solver_path()
    if not ccx:
        raise FileNotFoundError("CalculiX2.23 required for executed fin screen")
    proc = subprocess.run(
        [ccx, "-i", "case"],
        cwd=folder,
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    (folder / "solver.log").write_text(proc.stdout + proc.stderr)
    if proc.returncode or not (folder / "case.dat").exists():
        raise RuntimeError("Fin shell solve failed; inspect solver.log")
    displacements: list[list[list[float]]] = []
    stress: list[list[float]] = []
    reaction: list[list[float]] = []
    frequencies: list[float] = []
    section = None
    eigen = False
    modal_started = False
    for line in (folder / "case.dat").read_text().splitlines():
        low = line.lower()
        compact = "".join(line.upper().split())
        if "EIGENVALUEOUTPUT" in compact:
            eigen = True
            section = None
            continue
        if "EIGENVALUENUMBER" in compact:
            modal_started = True
            eigen = False
            section = None
            continue
        if "displacements (" in low:
            displacements.append([])
            section = "U"
            eigen = False
            continue
        if "forces (" in low:
            section = "RF"
            eigen = False
            continue
        if "stresses (" in low:
            section = "S" if not modal_started else None
            eigen = False
            continue
        fields = line.split()
        if not fields:
            if eigen and frequencies:
                eigen = False
            if section == "U" and displacements[-1]:
                section = None
            if section == "RF" and reaction:
                section = None
            if section == "S" and stress:
                section = None
            continue
        try:
            int(fields[0])
            count = 8 if section == "S" else 5 if eigen else 4
            values = [float(x.replace("D", "E")) for x in fields[:count]]
        except ValueError:
            continue
        if eigen and len(values) >= 4:
            frequencies.append(values[3])
        elif section == "U":
            displacements[-1].append(values)
        elif section == "RF":
            reaction.append(values)
        elif section == "S":
            stress.append(values)
    if not displacements or not displacements[0] or not frequencies or not stress:
        raise RuntimeError("Static/modal output parsing incomplete")
    static = displacements[0]
    maxdef = float(max(abs(r[3]) for r in static))
    # CalculiX RF is the nodal force. Subtract CLOAD already applied at
    # constrained nodes to obtain the support reaction (K*u-F).
    reported_rf = sum(r[3] for r in reaction)
    support_cload = sum(loads.get(n, 0) for n in fixed)
    support_reaction = reported_rf - support_cload
    balance = abs(support_reaction + force_n)
    # S6 is expanded to a 3D shell: tensor output remains integration-point data.
    regional_exclusion_mm = 2 * base_thickness_mm
    regional = [r for r in stress if centroids[int(r[0])][0] >= regional_exclusion_mm]

    def vm(r: list[float]) -> float:
        xx, yy, zz, xy, xz, yz = r[2:8]
        return float(
            np.sqrt(
                0.5 * ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2)
                + 3 * (xy**2 + xz**2 + yz**2)
            )
        )

    peak = float(max(vm(r) for r in regional))

    section_stress: dict[str, Any] = {}
    for section_key in (
        sorted(thickness_groups) if has_root_gusset_profile else [round(base_thickness_mm * 100)]
    ):
        section_elements = set(thickness_groups.get(section_key, list(elements)))
        section_rows = [r for r in stress if int(r[0]) in section_elements]
        if not section_rows:
            continue
        section_x = [float(centroids[element_id][0]) for element_id in section_elements]
        section_stress[f"{section_key / 100:.2f}"] = {
            "element_count": len(section_elements),
            "spanwise_centroid_range_mm": [min(section_x), max(section_x)],
            "regional_exclusion_intersects_section": min(section_x) < regional_exclusion_mm,
            "absolute_stress_components_pa": {
                "Sxx_spanwise": max(abs(row[2]) for row in section_rows) * 1e6,
                "Syy_chordwise": max(abs(row[3]) for row in section_rows) * 1e6,
                "tauXY_in_plane": max(abs(row[5]) for row in section_rows) * 1e6,
            },
            "use": "Section-level diagnostic; bins near the ideal clamp are excluded from the regional acceptance screen and do not qualify the gusset/root bond.",
        }

    def component_peak(index: int) -> float:
        return max(abs(row[index]) for row in regional) * 1e6

    (folder / "static-fields.json").write_text(
        json.dumps(
            {
                "displacements_node_mm": static,
                "stress_integration_point_mpa": stress,
                "stress_components": ["xx", "yy", "zz", "xy", "xz", "yz"],
                "regional_exclusion_span_mm": regional_exclusion_mm,
                "von_mises_usage": "Diagnostic isotropic stress only, not an anisotropic plywood failure criterion.",
                "stress_by_actual_shell_thickness_mm": section_stress,
            }
        )
        + "\n"
    )
    (folder / "mode-fields.json").write_text(
        json.dumps(
            {
                "frequencies_hz": frequencies,
                "node_vectors": displacements[1:],
                "normalization": "Solver eigenvectors have arbitrary/mass normalization; not actual displacement amplitude.",
            }
        )
        + "\n"
    )
    result.update(
        solver_executed=True,
        max_displacement_m=maxdef * 1e-3,
        regional_von_mises_pa=peak * 1e6,
        regional_stress_by_actual_thickness_mm=section_stress,
        regional_exclusion_span_mm=regional_exclusion_mm,
        regional_abs_sxx_pa=component_peak(2),
        regional_abs_syy_pa=component_peak(3),
        regional_abs_tau_xy_pa=component_peak(5),
        frequencies_hz=frequencies,
        equilibrium_error_n=balance,
        support_reaction_n=support_reaction,
        reported_support_nodal_force_n=reported_rf,
        applied_support_cload_n=support_cload,
    )
    if part is None:
        length = span * 0.001
        width = root * 0.001
        t = thickness * 0.001
        beam_young = float(orthotropic["E1_pa"]) if orthotropic else young_pa
        ei = beam_young * width * t**3 / 12
        mu = density_kg_m3 * width * t
        expected = force_n * length**3 / (8 * ei)
        f1 = 1.8751040687**2 / (2 * np.pi * length**2) * np.sqrt(ei / mu)
        result.update(
            analytic_deflection_m=expected,
            analytic_first_mode_hz=f1,
            known_case_passed=bool(
                abs(maxdef * 0.001 / expected - 1) < 0.05
                and balance < 1e-7
                and (orthotropic is not None or abs(frequencies[0] / f1 - 1) < 0.05)
            ),
        )
    (folder / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result
