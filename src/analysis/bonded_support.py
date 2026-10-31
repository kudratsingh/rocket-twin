"""Geometry and conformal meshing probe for the WO-03 bonded load path.

Coordinates are millimetres in the vehicle body frame. This does not certify a
load path; only solids and material interfaces explicitly imported are included.
"""

from __future__ import annotations

import importlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


def fragment_and_mesh(
    step_paths: dict[str, Path],
    size_mm: float,
    output: Path,
    physical: dict[str, Any] | None = None,
) -> dict[str, Any]:
    gmsh = importlib.import_module("gmsh")
    gmsh.initialize()
    try:
        gmsh.option.setNumber("General.Terminal", 1)
        gmsh.model.add("bonded_support")
        inputs = []
        owners = []
        for owner, path in step_paths.items():
            entities = gmsh.model.occ.importShapes(str(path), highestDimOnly=True)
            for dim, tag in entities:
                if dim == 3:
                    inputs.append((dim, tag))
                    owners.append(owner)
        if len(inputs) < 3:
            raise ValueError("Missing imported material solids")
        _, mapping = gmsh.model.occ.fragment(inputs[:1], inputs[1:])
        gmsh.model.occ.synchronize()
        volume_owners: dict[int, set[str]] = {}
        for owner, result in zip(owners, mapping, strict=True):
            for dim, tag in result:
                if dim == 3:
                    volume_owners.setdefault(tag, set()).add(owner)
        overlap = {str(tag): sorted(v) for tag, v in volume_owners.items() if len(v) != 1}
        if overlap:
            raise ValueError(f"Overlapping material volumes: {overlap}")
        groups: dict[str, list[int]] = {}
        for tag, owner_set in volume_owners.items():
            groups.setdefault(next(iter(owner_set)), []).append(tag)
        for name, tags in groups.items():
            group = gmsh.model.addPhysicalGroup(3, tags)
            gmsh.model.setPhysicalName(3, group, name)
        # Verify common surfaces, not just geometric proximity.
        boundaries = {
            name: {
                abs(tag)
                for vol in tags
                for dim, tag in gmsh.model.getBoundary([(3, vol)], oriented=False)
                if dim == 2
            }
            for name, tags in groups.items()
        }
        adjacency = {
            name: {
                "mount": len(boundaries[name] & boundaries["motor_mount"]),
                "shell": len(boundaries[name] & boundaries["aft_shell"]),
            }
            for name in groups
            if name.startswith("mount_shell_bond_")
        }
        if "face_spreader" in groups:
            pairs = [
                ("upper_segment", "joint_flange"),
                ("joint_flange", "face_spreader"),
                ("face_spreader", "aft_shell"),
                *[("face_spreader", f"strip_{i}") for i in range(3)],
            ]
            missing = [(a, b) for a, b in pairs if not (boundaries[a] & boundaries[b])]
            if missing:
                raise ValueError(f"Finite shoulder missing shared faces: {missing}")
        strip_interfaces = {
            name: {
                "shell": len(boundaries[name] & boundaries["aft_shell"]),
                "strip": len(boundaries[name] & boundaries[name.replace("strip_bond_", "strip_")]),
            }
            for name in groups
            if name.startswith("strip_bond_")
        }
        if any(not a["shell"] or not a["strip"] for a in strip_interfaces.values()):
            raise ValueError(f"Strip bond not conformal: {strip_interfaces}")
        if any(not a["mount"] or not a["shell"] for a in adjacency.values()):
            raise ValueError(f"Bond does not share conformal surfaces at both ends: {adjacency}")
        gmsh.option.setNumber("Mesh.MeshSizeMin", 0.3)
        gmsh.option.setNumber("Mesh.MeshSizeMax", size_mm)
        gmsh.option.setNumber("Mesh.ElementOrder", 2)
        if physical is not None and physical.get("paper_doubler"):
            gmsh.option.setNumber("Mesh.Algorithm3D", 10)
            # Thin concentric surfaces need enough circumferential facets that
            # their chordal approximation does not cross the 0.1 mm film.
            gmsh.option.setNumber("Mesh.MeshSizeFromCurvature", 56)
            gmsh.option.setNumber("Mesh.MeshSizeMin", 0.05)
            gmsh.option.setNumber("Mesh.SecondOrderLinear", 1)
        gmsh.model.mesh.generate(3)
        generated_count = sum(len(ids) for ids in gmsh.model.mesh.getElements(3)[1])
        if generated_count > 150_000:
            raise RuntimeError(
                f"Bounded study refuses {generated_count} solid elements (>150000); "
                "no high-order optimization or structural solve is credited"
            )
        if physical is None or not physical.get("paper_doubler"):
            gmsh.model.mesh.optimize("HighOrder")
        types, element_tags, _ = gmsh.model.mesh.getElements(3)
        if set(types) != {11}:
            raise ValueError(f"Expected exclusively quadratic tetrahedra: {types}")
        local, integration_weights = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, local)
        determinant_min = float(np.min(determinants))
        if determinant_min <= 0:
            raise ValueError(f"Nonpositive quadratic Jacobian: {determinant_min}")
        mesh_volume_check = {}
        if physical is not None and physical.get("paper_doubler"):
            weights_arr = np.asarray(integration_weights, dtype=float)
            for name, group_volumes in groups.items():
                cad_volume = sum(float(gmsh.model.occ.getMass(3, tag)) for tag in group_volumes)
                mesh_volume = 0.0
                for tag in group_volumes:
                    _, det, _ = gmsh.model.mesh.getJacobians(11, local, tag)
                    det_arr = np.asarray(det, dtype=float).reshape(-1, len(weights_arr))
                    mesh_volume += float(np.sum(det_arr @ weights_arr))
                mesh_volume_check[name] = {
                    "cad_volume_mm3": cad_volume,
                    "mesh_volume_mm3": mesh_volume,
                    "relative_error": mesh_volume / cad_volume - 1.0,
                }
        gmsh.write(str(output / "mesh.msh"))
        solved = exploratory_solve(gmsh, groups, boundaries, output) if physical is None else None
        cases = {}
        if physical is not None:
            for case in physical["cases"]:
                case_dir = output / case["id"]
                case_dir.mkdir()
                cases[case["id"]] = exploratory_solve(
                    gmsh, groups, boundaries, case_dir, physical, case
                )
                (case_dir / "report.json").write_text(
                    json.dumps(cases[case["id"]], indent=2) + "\n"
                )
        return {
            "groups": groups,
            "interface_shared_surface_counts": adjacency,
            "strip_bond_shared_surface_counts": strip_interfaces,
            "element_count": sum(len(x) for x in element_tags),
            "minimum_gauss_jacobian_mm3": determinant_min,
            "mesh_volume_check": mesh_volume_check,
            "geometry_approximation": (
                "Straight-sided quadratic tetrahedra; 56-segment nominal circumference gives approximately 0.052 mm chord sag, comparable to 0.1 mm film thickness. No accuracy or local-gap guarantee."
                if physical is not None and physical.get("paper_doubler")
                else "Curved quadratic tetrahedra"
            ),
            "exploratory_139_97_n": solved,
            "physical_cases": cases,
        }

    finally:
        gmsh.finalize()


def exploratory_solve(
    gmsh: Any,
    groups: dict[str, list[int]],
    boundaries: dict[str, set[int]],
    output: Path,
    physical: dict[str, Any] | None = None,
    case: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Static exploratory load; not an accelerating-vehicle case."""
    from src.analysis.fea import solver_path
    from src.analysis.support_fea import _clipped_quadratic_triangle_weights, _quadratic_tets

    coords, elements = _quadratic_tets(gmsh)
    mat_elements: dict[str, list[int]] = {"PLY": [], "PAPER": [], "EPOXY": []}
    if any(name.startswith("strip_") and not name.startswith("strip_bond_") for name in groups):
        mat_elements["CARBON"] = []
        mat_elements["STRIP_BOND"] = []
    if "joint_flange" in groups:
        mat_elements["ASA_STOP"] = []
        mat_elements["G11_FACE"] = []
    for name, volumes in groups.items():
        material = (
            "PLY"
            if name == "motor_mount"
            else (
                "PAPER"
                if name in ("aft_shell", "upper_segment")
                or (
                    name == "upper_doubler"
                    and physical is not None
                    and physical.get("paper_doubler")
                )
                else (
                    "ASA_STOP"
                    if name == "joint_flange"
                    else (
                        "G11_FACE"
                        if name in ("face_spreader", "upper_doubler")
                        else (
                            "STRIP_BOND"
                            if name.startswith("strip_bond_") or name == "upper_wrap_bond"
                            else "CARBON" if name.startswith("strip_") else "EPOXY"
                        )
                    )
                )
            )
        )
        for volume in volumes:
            types, tags, _ = gmsh.model.mesh.getElements(3, volume)
            for typ, ids in zip(types, tags):
                if typ != 11:
                    raise ValueError("Nonquadratic element")
                mat_elements[material].extend(int(x) for x in ids)
    if set(elements) != {eid for ids in mat_elements.values() for eid in ids} or sum(
        len(v) for v in mat_elements.values()
    ) != len(elements):
        raise ValueError("Material mapping incomplete or overlapping")
    support = sorted(
        n
        for n, x in coords.items()
        if abs(
            x[2]
            - (
                float(physical.get("support_station_mm", 818.0))
                if physical is not None and physical.get("joint_model") == "finite_shoulder_bonded"
                else 922.0
            )
        )
        < 1e-5
        and 32.49
        <= np.linalg.norm(x[:2])
        <= (
            34.01
            if "CARBON" in mat_elements
            and physical is not None
            and physical.get("joint_model") == "ideal_strip_projection"
            else 33.01
        )
    )
    if len(support) < 3:
        raise ValueError("No front joint nodes")
    weights: dict[int, float] = {}
    area = 0.0
    faces = 0
    for face in boundaries["motor_mount"]:
        bb = gmsh.model.getBoundingBox(2, face)
        if bb[5] - bb[2] <= 5:
            continue
        centre = np.asarray(gmsh.model.occ.getCenterOfMass(2, face))
        matching = False
        for angle in (0.0, 120.0, 240.0):
            angle = np.deg2rad(angle)
            radial = np.array([np.cos(angle), np.sin(angle)])
            tangent = np.array([-np.sin(angle), np.cos(angle)])
            planar = centre[:2] - 28.5 * radial
            if abs(np.dot(planar, radial)) < 0.75 and abs(abs(np.dot(planar, tangent)) - 6.0) < 0.2:
                matching = True
                break
        if not matching:
            continue
        face_area = 0.0
        types, _, conns = gmsh.model.mesh.getElements(2, face)
        for typ, conn in zip(types, conns):
            if typ != 9:
                raise ValueError("Expected quadratic face")
            for tri in np.asarray(conn).reshape(-1, 6):
                w, a = _clipped_quadratic_triangle_weights(tri, coords, 1001.0, 1019.0)
                area += a
                face_area += a
                for n, value in w.items():
                    weights[n] = weights.get(n, 0.0) + value
        if face_area > 1e-10:
            faces += 1
    weights = {n: w for n, w in weights.items() if abs(w) > 1e-12}
    if not weights or not 5 <= faces <= 6:
        raise ValueError(f"Unexpected thrust engagement: {faces} faces, {area} mm2")
    total = sum(weights.values())
    # Body-coordinate noseward is negative z. Accelerating-frame inertial loads
    # are aftward (+z); gravity is included in T/m specific acceleration.
    load = (
        139.97
        if physical is None
        else physical["thrust_n"]
        - physical["motor_mass_kg"] * physical["specific_acceleration_m_s2"]
    )
    forces = {n: -load * w / total for n, w in weights.items()}
    mass_details = []
    if physical is not None:
        assert case is not None
        # Lump each tetrahedron's volume onto its four corner nodes. The total
        # of each part is exactly reconciled to its CAD mass. This is a mesh
        # approximation of distributed body force, not point grounding.
        part_elements = {}
        for name, volumes in groups.items():
            part_elements[name] = [
                int(e)
                for vol in volumes
                for ids in gmsh.model.mesh.getElements(3, vol)[1]
                for e in ids
            ]

        def element_volume(eid: int) -> float:
            a, b, c, d = [coords[n] for n in elements[eid][:4]]
            return abs(float(np.linalg.det(np.array([b - a, c - a, d - a])))) / 6

        def add_mass(name: str, mass: float, ids: list[int]) -> None:
            vol = sum(element_volume(e) for e in ids)
            if vol <= 0:
                raise ValueError(f"No attachment volume for {name}")
            for e in ids:
                nodal = mass * physical["specific_acceleration_m_s2"] * element_volume(e) / vol / 4
                for n in elements[e][:4]:
                    forces[n] = forces.get(n, 0.0) + nodal
            mass_details.append(
                {
                    "id": name,
                    "mass_kg": mass,
                    "inertial_force_n": mass * physical["specific_acceleration_m_s2"],
                    "elements": len(ids),
                }
            )

        for name, ids in part_elements.items():
            add_mass(name, physical["mass_kg"][name], ids)
        # Other aft components are approximated by volume-weighted load patches
        # on their named substrate, near the specified physical attachment z.
        # Their attachments need physical modeling before qualification.
        for attachment in physical["attachments"]:
            ids = part_elements[attachment["substrate"]]
            z = attachment["station_mm"]
            distances = {
                e: abs(float(np.mean([coords[n][2] for n in elements[e][:4]])) - z) for e in ids
            }
            nearest = min(distances.values())
            selected = [e for e in ids if distances[e] <= max(nearest + 0.01, 5.0)]
            add_mass(attachment["id"], attachment["mass_kg"], selected)
        if case["growth_location"] == "aft":
            ids = part_elements["aft_shell"]
            selected = [
                e for e in ids if 1095 <= np.mean([coords[n][2] for n in elements[e][:4]]) <= 1105
            ]
            add_mass("growth_aft_1p100m", 0.05, selected)
        expected = (
            physical["forward_mass_kg"] + (0.05 if case["growth_location"] == "forward" else 0.0)
        ) * physical["specific_acceleration_m_s2"]
        if abs(sum(forces.values()) + expected) > 1e-6:
            raise ValueError(
                f"Inertial accounting failed: {sum(forces.values())}, expected reaction {expected}"
            )
    anchor = min(support, key=lambda n: coords[n][0])
    anchor2 = max(support, key=lambda n: abs(coords[n][0] - coords[anchor][0]))
    lines = ["*HEADING", "Exploratory full thrust, restrained upper joint, N mm MPa", "*NODE"]
    lines += [f"{n},{x[0]:.12g},{x[1]:.12g},{x[2]:.12g}" for n, x in coords.items()]
    lines += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"]
    lines += [f"{n}," + ",".join(map(str, con)) for n, con in elements.items()]
    for name, ids in mat_elements.items():
        lines.append(f"*ELSET,ELSET={name}")
        lines += [",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)]
    for name, ids in [("SUPPORT", support), ("ALL", sorted(coords))]:
        lines.append(f"*NSET,NSET={name}")
        lines += [",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)]
    materials = [
        ("PLY", 2000 if case is None else case["ply_mpa"], 0.25),
        ("PAPER", 500 if case is None else case["paper_mpa"], 0.3),
        ("EPOXY", 2000 if case is None else case["epoxy_mpa"], 0.3),
    ]
    if "CARBON" in mat_elements:
        assert case is not None
        materials.append(("CARBON", case["carbon_mpa"], 0.3))
        materials.append(("STRIP_BOND", case["epoxy_mpa"], 0.3))
    if "ASA_STOP" in mat_elements:
        stop_modulus = 5000.0 if physical is not None and physical.get("g11_stop") else 1000.0
        materials.extend([("ASA_STOP", stop_modulus, 0.35), ("G11_FACE", 10000.0, 0.3)])
    for name, young, poisson in materials:
        lines += [
            f"*MATERIAL,NAME={name}",
            "*ELASTIC",
            f"{young},{poisson}",
            f"*SOLID SECTION,ELSET={name},MATERIAL={name}",
        ]
    lines += [
        "*BOUNDARY",
        "SUPPORT,3,3,0",
        f"{anchor},1,2,0",
        f"{anchor2},2,2,0",
        "*STEP",
        "*STATIC",
        "*CLOAD",
    ]
    lines += [f"{n},3,{f:.12g}" for n, f in forces.items()]
    lines += ["*NODE PRINT,NSET=SUPPORT", "RF", "*NODE PRINT,NSET=ALL", "U"]
    for name in mat_elements:
        lines += [f"*EL PRINT,ELSET={name}", "S"]
    lines += ["*END STEP"]
    (output / "case.inp").write_text("\n".join(lines) + "\n")
    ccx = solver_path()
    if ccx is None:
        raise RuntimeError("CalculiX executable unavailable")
    proc = subprocess.run(
        [ccx, "-i", "case"],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
        env={**os.environ, "OMP_NUM_THREADS": "1"},
    )
    (output / "solver.log").write_text(proc.stdout + proc.stderr)
    if proc.returncode or "*ERROR" in (proc.stdout + proc.stderr).upper():
        raise RuntimeError("CalculiX solve failed; inspect solver.log")
    sections: dict[str, list[list[float]]] = {"U": [], "RF": [], "S": []}
    section = None
    for line in (output / "case.dat").read_text().splitlines():
        low = line.lower()
        if "displacements (" in low:
            section = "U"
            continue
        if "forces (" in low:
            section = "RF"
            continue
        if "stresses (" in low:
            section = "S"
            continue
        fields = line.split()
        if section and fields:
            try:
                int(fields[0])
                sections[section].append([float(x) for x in fields])
            except ValueError:
                pass
    if not all(sections.values()):
        raise RuntimeError("Missing solver output sections")
    raw_reaction = sum(row[3] for row in sections["RF"])
    constrained_applied = sum(forces.get(n, 0.0) for n in support)
    reaction = raw_reaction - constrained_applied
    disp = np.array(sections["U"])
    stress_by_material = {}
    for name, ids in mat_elements.items():
        wanted = set(ids)
        rows = [row for row in sections["S"] if int(row[0]) in wanted]
        radial_stresses = []
        shear = []
        axial = []
        mises = []
        for row in rows:
            eid = int(row[0])
            x = np.mean([coords[n] for n in elements[eid][:4]], axis=0)
            r = np.linalg.norm(x[:2])
            c = x[0] / r if r else 1.0
            s = x[1] / r if r else 0.0
            xx, yy, zz, xy, xz, yz = row[2:8]
            radial_stresses.append(c * c * xx + s * s * yy + 2 * c * s * xy)
            shear.append(c * xz + s * yz)
            axial.append(zz)
            mises.append(
                np.sqrt(
                    ((xx - yy) ** 2 + (yy - zz) ** 2 + (zz - xx) ** 2) / 2
                    + 3 * (xy * xy + xz * xz + yz * yz)
                )
            )
        if not rows:
            raise RuntimeError(f"No stress output for {name}")
        stress_by_material[name] = {
            "points": len(rows),
            "max_radial_tension_mpa": max(radial_stresses),
            "max_radial_compression_mpa": min(radial_stresses),
            "max_abs_axial_shear_mpa": max(map(abs, shear)),
            "max_abs_axial_stress_mpa": max(map(abs, axial)),
            "max_von_mises_mpa": max(mises),
            "p95_abs_radial_mpa": float(np.percentile(np.abs(radial_stresses), 95)),
            "p95_abs_axial_shear_mpa": float(np.percentile(np.abs(shear), 95)),
            "p95_von_mises_mpa": float(np.percentile(mises, 95)),
        }
    regions = {}
    if physical is not None:
        # Fixed axial regions, weighted by linearized tetrahedron volume. Values
        # average signed integration-point stresses; no percentile substitution.
        for region, material, region_low, region_high in [
            ("shell_forward", "PAPER", 940, 980),
            *[
                (f"bond_{i}_middle", "EPOXY", z + 1, z + 2)
                for i, z in enumerate([990, 1045, 1100, 1138.5, 1177])
            ],
        ]:
            ids = set(mat_elements[material])
            sums = np.zeros(3)
            absolute_sums = np.zeros(3)
            absolute_max = np.zeros(3)
            denominator = 0.0
            for row in sections["S"]:
                eid = int(row[0])
                if eid not in ids:
                    continue
                x = np.mean([coords[n] for n in elements[eid][:4]], axis=0)
                if not region_low <= x[2] <= region_high:
                    continue
                r = np.linalg.norm(x[:2])
                c = x[0] / r if r else 1.0
                ss = x[1] / r if r else 0.0
                xx, yy, zz, xy, xz, yz = row[2:8]
                volume_weight = element_volume(eid) / 4
                values = np.array(
                    [c * c * xx + ss * ss * yy + 2 * c * ss * xy, c * xz + ss * yz, zz]
                )
                sums += volume_weight * values
                absolute_sums += volume_weight * np.abs(values)
                absolute_max = np.maximum(absolute_max, np.abs(values))
                denominator += volume_weight
            if denominator:
                means = sums / denominator
                regions[region] = {
                    "volume_mm3": denominator,
                    "signed_mean_radial_mpa": float(means[0]),
                    "signed_mean_axial_radial_shear_mpa": float(means[1]),
                    "signed_mean_axial_mpa": float(means[2]),
                    "volume_weighted_mean_abs_radial_mpa": float(absolute_sums[0] / denominator),
                    "volume_weighted_mean_abs_axial_shear_mpa": float(
                        absolute_sums[1] / denominator
                    ),
                    "volume_weighted_mean_abs_axial_mpa": float(absolute_sums[2] / denominator),
                    "regional_peak_abs_radial_mpa": float(absolute_max[0]),
                    "regional_peak_abs_axial_shear_mpa": float(absolute_max[1]),
                    "regional_peak_abs_axial_mpa": float(absolute_max[2]),
                }
        if "shell_forward" in regions:
            regions["shell_forward"]["estimated_section_force_n"] = (
                regions["shell_forward"]["signed_mean_axial_mpa"] * np.pi * (33**2 - 32.5**2)
            )
    return {
        "physical": physical is not None,
        "mass_details": mass_details,
        "expected_front_reaction_n": expected if physical is not None else None,
        "thrust_flank_load_n": load,
        "fixed_regions": regions,
        "applied_n": sum(forces.values()),
        "raw_calculix_constrained_node_force_n": raw_reaction,
        "applied_force_at_constrained_nodes_n": constrained_applied,
        "reaction_n": reaction,
        "equilibrium_residual_n": reaction + sum(forces.values()),
        "load_faces": faces,
        "load_area_mm2": area,
        "max_displacement_mm": float(np.linalg.norm(disp[:, 1:4], axis=1).max()),
        "stress": stress_by_material,
        "scope": (
            "Accelerating-frame approximation with assumed distributed attachment patches; no attachment or flight qualification."
            if physical is not None
            else "Full 139.97 N exploratory static case; not a flight inertia model."
        ),
    }


def bonded_bar_fixture(out: Path) -> dict[str, Any]:
    """Check two conformally joined, serial elastic solids against PL/EA."""
    gmsh = importlib.import_module("gmsh")

    from src.analysis.support_fea import (
        _clipped_quadratic_triangle_weights,
        _quadratic_tets,
        _run_ccx,
    )

    out.mkdir(parents=True, exist_ok=False)
    gmsh.initialize()
    gmsh.option.setNumber("General.Terminal", 0)
    gmsh.model.add("fixture")
    a = gmsh.model.occ.addBox(0, 0, 0, 10, 10, 10)
    b = gmsh.model.occ.addBox(0, 0, 10, 10, 10, 20)
    _, mp = gmsh.model.occ.fragment([(3, a)], [(3, b)])
    gmsh.model.occ.synchronize()
    gmsh.option.setNumber("Mesh.MeshSizeMax", 3)
    gmsh.option.setNumber("Mesh.ElementOrder", 2)
    gmsh.model.mesh.generate(3)
    gmsh.model.mesh.optimize("HighOrder")
    coords, elements = _quadratic_tets(gmsh)
    groups = []
    for entity in mp:
        ids = []
        for dim, tag in entity:
            for typ, tags in zip(*gmsh.model.mesh.getElements(3, tag)[:2]):
                assert typ == 11
                ids += list(map(int, tags))
        groups.append(ids)
    support = sorted(n for n, x in coords.items() if abs(x[2]) < 1e-8)
    weights: dict[int, float] = {}
    for _, face in gmsh.model.getEntities(2):
        bb = gmsh.model.getBoundingBox(2, face)
        if abs(bb[2] - 30) > 1e-5 or abs(bb[5] - 30) > 1e-5:
            continue
        for typ, conn in zip(
            gmsh.model.mesh.getElements(2, face)[0], gmsh.model.mesh.getElements(2, face)[2]
        ):
            assert typ == 9
            for tri in np.array(conn).reshape(-1, 6):
                w, _ = _clipped_quadratic_triangle_weights(tri, coords, 29, 31)
                for n, x in w.items():
                    weights[n] = weights.get(n, 0.0) + x
    assert abs(sum(weights.values()) - 100) < 1e-5
    a = min(support, key=lambda n: coords[n][0] + coords[n][1])
    b = max(support, key=lambda n: abs(coords[n][0] - coords[a][0]))
    d = ["*HEADING", "Two material axial bar: N mm MPa", "*NODE"] + [
        f"{n},{x[0]},{x[1]},{x[2]}" for n, x in coords.items()
    ]
    d += ["*ELEMENT,TYPE=C3D10,ELSET=ALL"] + [
        f"{n}," + ",".join(map(str, c)) for n, c in elements.items()
    ]
    for name, ids in [("A", groups[0]), ("B", groups[1])]:
        d += [f"*ELSET,ELSET={name}"] + [
            ",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)
        ]
    for name, ids in [("SUP", support), ("ALL", sorted(coords))]:
        d += [f"*NSET,NSET={name}"] + [
            ",".join(map(str, ids[i : i + 16])) for i in range(0, len(ids), 16)
        ]
    for name, e in [("A", 2000), ("B", 100)]:
        d += [
            f"*MATERIAL,NAME={name}",
            "*ELASTIC",
            f"{e},0",
            f"*SOLID SECTION,ELSET={name},MATERIAL={name}",
        ]
    d += (
        ["*BOUNDARY", "SUP,3,3,0", f"{a},1,2,0", f"{b},2,2,0", "*STEP", "*STATIC", "*CLOAD"]
        + [f"{n},3,{w:.12g}" for n, w in weights.items() if abs(w) > 1e-12]
        + ["*NODE PRINT,NSET=ALL", "U", "*NODE PRINT,NSET=SUP", "RF", "*END STEP"]
    )
    (out / "case.inp").write_text("\n".join(d) + "\n")
    gmsh.finalize()
    _run_ccx(out)
    sec = ""
    data: dict[str, list[list[float]]] = {"U": [], "RF": []}
    for line in (out / "case.dat").read_text().splitlines():
        if "displacements (" in line.lower():
            sec = "U"
            continue
        if "forces (" in line.lower():
            sec = "RF"
            continue
        try:
            fields = line.split()
            int(fields[0])
            data[sec].append([float(x) for x in fields])
        except (ValueError, IndexError, KeyError):
            pass
    u = [row[3] for row in data["U"] if abs(coords[int(row[0])][2] - 30) < 1e-6]
    reaction = sum(row[3] for row in data["RF"])
    expected = 100 / 100 * (10 / 2000 + 20 / 100)
    report = {
        "fixture": "two conformal serial solids, nu=0, E=2000 and 100 MPa, L=10 and 20 mm, area 100 mm2, 100 N",
        "expected_mm": expected,
        "mean_top_displacement_mm": float(np.mean(u)),
        "relative_error": abs(float(np.mean(u)) / expected - 1),
        "reaction_n": reaction,
        "residual_n": reaction + 100,
        "element_counts": [len(x) for x in groups],
    }
    (out / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def _beam_shapes(xi: float, length: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Hermite transverse shapes and their first/second x derivatives.

    xi lies in [0, 1]. Rotation is dv/dx. See Gere, Mechanics of Materials,
    Euler-Bernoulli beam interpolation; N, mm, MPa throughout this module.
    """
    s = xi
    n = np.array(
        [
            1 - 3 * s * s + 2 * s**3,
            length * (s - 2 * s * s + s**3),
            3 * s * s - 2 * s**3,
            length * (-s * s + s**3),
        ]
    )
    dn = np.array(
        [
            (-6 * s + 6 * s * s) / length,
            1 - 4 * s + 3 * s * s,
            (6 * s - 6 * s * s) / length,
            -2 * s + 3 * s * s,
        ]
    )
    ddn = np.array(
        [
            (-6 + 12 * s) / length**2,
            (-4 + 6 * s) / length,
            (6 - 12 * s) / length**2,
            (-2 + 6 * s) / length,
        ]
    )
    return n, dn, ddn


def overlap_beam_spring(
    *,
    divisions: int,
    length_mm: float,
    overlap_mm: float,
    width_mm: float,
    thickness_mm: tuple[float, float],
    young_mpa: tuple[float, float],
    adhesive_thickness_mm: float,
    adhesive_young_mpa: float,
    adhesive_poisson: float,
    force_n: float,
    outer_load_fraction: float,
    radius_mm: float | None = None,
    hoop_young_mpa: tuple[float, float] | None = None,
    eccentric_interface: bool = True,
    retain_fields: bool = False,
    opening_force_n: float = 0.0,
) -> dict[str, Any]:
    """Finite-overlap, linear elastic two-adherend beam/adhesive reduction.

    Each adherend has independent axial, transverse and rotational degrees of
    freedom. Adhesive shear and normal springs are integrated along the *finite*
    overlap with three-point Gauss quadrature. They connect displacements at the
    actual adherend surfaces, retaining the eccentricity that generates peel.
    No outer-adherend end is grounded or projected onto an ideal joint.

    Derivation: minimization of int[EA u'^2 + EI v''^2 + k_s delta_u^2 +
    k_n delta_v^2]/2 dx - external work. This is a small-displacement version of
    the beam/adhesive formulation in Goland and Reissner, J. Applied Mechanics
    11 (1944), A17-A27; it does not implement their finite-rotation correction.
    For a complete cylindrical sleeve the optional Eh*t*b/R^2 radial foundation
    follows circumferential membrane strain v/R (Timoshenko & Woinowsky-Krieger,
    Theory of Plates and Shells, axisymmetric cylindrical shell equations).
    Orthotropy, contact, crushing, fracture, defects and thermal eigenstrains are
    excluded. Hoop properties and the end-load split must be explicit inputs.
    """
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve

    positive = (
        length_mm,
        overlap_mm,
        width_mm,
        *thickness_mm,
        *young_mpa,
        adhesive_thickness_mm,
        adhesive_young_mpa,
    )
    if (
        divisions < 2
        or any(x <= 0 or not np.isfinite(x) for x in positive)
        or overlap_mm > length_mm
        or not 0 <= outer_load_fraction <= 1
        or not -1 < adhesive_poisson < 0.5
        or force_n <= 0
    ):
        raise ValueError("Invalid finite-overlap input")
    h = length_mm / divisions
    first = round((length_mm - overlap_mm) / h)
    if abs(first * h - (length_mm - overlap_mm)) > 1e-8:
        raise ValueError("Mesh must put a node at the exact overlap start")
    node_counts = (divisions + 1, divisions - first + 1)
    offsets = (0, 3 * node_counts[0])
    ndof = 3 * sum(node_counts)
    entries: list[tuple[int, int, float]] = []
    force = np.zeros(ndof)
    gauss_x, gauss_w = np.polynomial.legendre.leggauss(3)
    points = [(float((x + 1) / 2), float(w * h / 2)) for x, w in zip(gauss_x, gauss_w)]

    def add(ids: list[int], local: np.ndarray) -> None:
        entries.extend(
            (i, j, float(local[a, b]))
            for a, i in enumerate(ids)
            for b, j in enumerate(ids)
            if local[a, b] != 0
        )

    def ids(layer: int, element: int) -> list[int]:
        start = offsets[layer] + 3 * (element if layer == 0 else element - first)
        return list(range(start, start + 6))

    for layer in (0, 1):
        t, e = thickness_mm[layer], young_mpa[layer]
        ea = e * width_mm * t
        ei = e * width_mm * t**3 / 12
        for element in range(0 if layer == 0 else first, divisions):
            axial = ea / h * np.array([[1.0, -1.0], [-1.0, 1.0]])
            local = np.zeros((6, 6))
            local[np.ix_([0, 3], [0, 3])] = axial
            for s, weight in points:
                n, _, ddn = _beam_shapes(s, h)
                bending = ei * np.outer(ddn, ddn)
                if radius_mm is not None and hoop_young_mpa is not None:
                    bending += hoop_young_mpa[layer] * t * width_mm / radius_mm**2 * np.outer(n, n)
                local[np.ix_([1, 2, 4, 5], [1, 2, 4, 5])] += weight * bending
            add(ids(layer, element), local)
    g = adhesive_young_mpa / (2 * (1 + adhesive_poisson))
    ks = g * width_mm / adhesive_thickness_mm
    kn = adhesive_young_mpa * width_mm / adhesive_thickness_mm
    for element in range(first, divisions):
        local = np.zeros((12, 12))
        for s, weight in points:
            n, dn, _ = _beam_shapes(s, h)
            shear_shape = np.zeros(12)
            normal_shape = np.zeros(12)
            shear_shape[[0, 3]] = -np.array([1 - s, s])
            shear_shape[[6, 9]] = np.array([1 - s, s])
            normal_shape[[1, 2, 4, 5]] = -n
            normal_shape[[7, 8, 10, 11]] = n
            if eccentric_interface:
                # gamma_xy includes dv/dx across the finite film. The h/2
                # terms make a uniform rigid rotation strain-free; omitting
                # them creates a spurious adhesive shear under that motion.
                shear_shape[[1, 2, 4, 5]] = (thickness_mm[0] + adhesive_thickness_mm) / 2 * dn
                shear_shape[[7, 8, 10, 11]] = (thickness_mm[1] + adhesive_thickness_mm) / 2 * dn
            local += weight * (
                ks * np.outer(shear_shape, shear_shape) + kn * np.outer(normal_shape, normal_shape)
            )
        add(ids(0, element) + ids(1, element), local)
    rows, cols, values = zip(*entries)
    stiffness = coo_matrix((values, (rows, cols)), shape=(ndof, ndof)).tocsr()
    # Only the base shell is supported, at its finite forward end. Its extension
    # ahead of the overlap stays elastic. No extra outer sleeve endpoint support.
    constrained = [0, 1, 2]
    if not eccentric_interface and radius_mm is None:
        # Exact axial-only Volkersen fixture: transverse rigid modes are removed
        # without altering any axial stiffness or adding an axial tie.
        constrained += [offsets[1] + 1, offsets[1] + 2]
    force[3 * divisions] = -force_n * (1 - outer_load_fraction)
    force[offsets[1] + 3 * (node_counts[1] - 1)] = -force_n * outer_load_fraction
    force[3 * divisions + 1] = -opening_force_n
    force[offsets[1] + 3 * (node_counts[1] - 1) + 1] = opening_force_n
    free = np.setdiff1d(np.arange(ndof), constrained)
    displacement = np.zeros(ndof)
    displacement[free] = spsolve(stiffness[free][:, free], force[free])
    residual = stiffness @ displacement - force
    rigid_rotation_residual = None
    if eccentric_interface and (hoop_young_mpa is None or max(hoop_young_mpa) == 0):
        rotation = np.zeros(ndof)
        separation = sum(thickness_mm) / 2 + adhesive_thickness_mm
        for layer in (0, 1):
            for node in range(node_counts[layer]):
                start = offsets[layer] + 3 * node
                rotation[start] = -separation if layer else 0.0
                rotation[start + 1] = (node + (first if layer else 0)) * h
                rotation[start + 2] = 1.0
        rigid_rotation_residual = float(
            np.max(np.abs(stiffness @ rotation)) / (abs(stiffness).sum(axis=1).max() * length_mm)
        )
    fields = []
    peak_stress = np.zeros(2)
    peak_shear = 0.0
    peak_peel = 0.0
    max_abs_normal = 0.0
    for element in range(divisions):
        a = displacement[ids(0, element)]
        b = displacement[ids(1, element)] if element >= first else None
        for s, _ in points:
            n, dn, ddn = _beam_shapes(s, h)
            row: dict[str, Any] = {"x_mm": (element + s) * h}
            for layer, d in enumerate([a] if b is None else [a, b]):
                strain = (d[3] - d[0]) / h
                curvature = float(ddn @ d[[1, 2, 4, 5]])
                surface = young_mpa[layer] * np.array(
                    [
                        strain - thickness_mm[layer] / 2 * curvature,
                        strain + thickness_mm[layer] / 2 * curvature,
                    ]
                )
                peak_stress[layer] = max(peak_stress[layer], float(np.max(np.abs(surface))))
                row[f"layer_{layer}_surface_axial_stress_mpa"] = surface.tolist()
            if b is not None:
                slip = float(np.array([1 - s, s]) @ (b[[0, 3]] - a[[0, 3]]))
                if eccentric_interface:
                    slip += float(
                        (thickness_mm[0] + adhesive_thickness_mm) / 2 * (dn @ a[[1, 2, 4, 5]])
                        + (thickness_mm[1] + adhesive_thickness_mm) / 2 * (dn @ b[[1, 2, 4, 5]])
                    )
                normal = float(n @ (b[[1, 2, 4, 5]] - a[[1, 2, 4, 5]]))
                shear = g / adhesive_thickness_mm * slip
                peel = adhesive_young_mpa / adhesive_thickness_mm * normal
                row.update(shear_mpa=shear, peel_mpa=peel)
                peak_shear = max(peak_shear, abs(shear))
                peak_peel = max(peak_peel, peel)
                max_abs_normal = max(max_abs_normal, abs(peel))
            fields.append(row)
    result: dict[str, Any] = {
        "method": "finite-overlap Euler-Bernoulli adherends with shear and normal springs",
        "divisions": divisions,
        "dof_count": ndof,
        "spring_quadrature_points": 3 * (divisions - first),
        "force_n": force_n,
        "outer_load_fraction": outer_load_fraction,
        "forward_extension_mm": length_mm - overlap_mm,
        "max_axial_displacement_mm": float(np.max(np.abs(displacement[::3]))),
        "max_radial_displacement_mm": float(np.max(np.abs(displacement[1::3]))),
        "max_rotation_rad": float(np.max(np.abs(displacement[2::3]))),
        "end_relative_opening_mm": float(
            displacement[offsets[1] + 3 * (node_counts[1] - 1) + 1]
            - displacement[3 * divisions + 1]
        ),
        "flat_beam_rigid_rotation_relative_residual": rigid_rotation_residual,
        "small_rotation_screen_passed": float(np.max(np.abs(displacement[2::3]))) < 0.1,
        "base_peak_abs_surface_axial_mpa": float(peak_stress[0]),
        "outer_peak_abs_surface_axial_mpa": float(peak_stress[1]),
        "peak_abs_adhesive_shear_mpa": peak_shear,
        "peak_tensile_peel_mpa": max(0.0, peak_peel),
        "peak_abs_adhesive_normal_mpa": max_abs_normal,
        "axial_reaction_n": float(residual[0]),
        "axial_equilibrium_residual_n": float(residual[0] - force_n),
        "free_residual_n_or_nmm": float(np.max(np.abs(residual[free]))),
        "strain_energy_nmm": float(displacement @ (stiffness @ displacement) / 2),
        "external_work_nmm": float(displacement @ force),
        "radius_mm": radius_mm,
        "hoop_young_mpa": hoop_young_mpa,
        "contact_or_failure_model": False,
        "estimated_inputs": True,
        "measured_data_used": False,
        "physical_qualification": False,
    }
    if retain_fields:
        result["gauss_fields"] = fields
    return result


def overlap_known_case(divisions: int = 120) -> dict[str, Any]:
    """Check spring shear lag against the exact equal-EA Volkersen solution.

    Two equal 1 mm adherends, E=1000 MPa, b=10 mm, L=100 mm, G=0.1 MPa,
    h=0.5 mm, F=10 N. One left endpoint is fixed and force is applied at the
    opposite end of the other adherend. Surface eccentricity is disabled only
    in this analytical axial-only verification case, never in candidate runs.
    """
    length, width, young, thick, force, shear, gap = 100.0, 10.0, 1000.0, 1.0, 10.0, 0.1, 0.5
    result = overlap_beam_spring(
        divisions=divisions,
        length_mm=length,
        overlap_mm=length,
        width_mm=width,
        thickness_mm=(thick, thick),
        young_mpa=(young, young),
        adhesive_thickness_mm=gap,
        adhesive_young_mpa=shear * 2.6,
        adhesive_poisson=0.3,
        force_n=force,
        outer_load_fraction=1.0,
        eccentric_interface=False,
        retain_fields=True,
    )
    lam = np.sqrt(2 * shear / (gap * young * thick))
    errors, expected = [], []
    for row in result.pop("gauss_fields"):
        x = row["x_mm"]
        tau = (
            force * lam * np.cosh(lam * (x - length / 2)) / (2 * width * np.sinh(lam * length / 2))
        )
        expected.append(float(tau))
        errors.append(abs(abs(row["shear_mpa"]) - tau))
    result.update(
        fixture="equal-EA Volkersen axial shear lag, exact solution at every quadrature point",
        analytical_peak_end_shear_mpa=float(
            force * lam / (2 * width) * np.cosh(lam * length / 2) / np.sinh(lam * length / 2)
        ),
        max_point_relative_error=float(max(errors) / max(expected)),
        verified=max(errors) / max(expected) < 0.01
        and abs(result["axial_equilibrium_residual_n"]) < 1e-7
        and abs(result["external_work_nmm"] / (2 * result["strain_energy_nmm"]) - 1) < 1e-8,
    )
    return result


def bonded_path_hand_budget(
    *,
    force_n: float,
    ring_bond_areas_mm2: list[float],
    ring_stations_mm: list[float],
    rail_area_mm2: float,
    rail_weak_i_mm4: float,
    paper_hot_mpa: float,
    plywood_hot_mpa: float,
    adhesive_hot_mpa: float,
    bond_gap_mm: float,
    upper_wall_mm: float,
    aft_wall_mm: float,
    joint_stiffness_n_mm: float,
    design_factor: float = 3.0,
    rail_force_n: float | None = None,
    aft_path_length_mm: float = 255.0,
    upper_path_length_mm: float = 778.0,
    ring_arm_mm: float = 3.5,
    ring_width_mm: float = 12.0,
    ring_thickness_mm: float = 3.0,
) -> dict[str, Any]:
    """Trace serial stiffness and lower-bound strengths without inventing a pass.

    Newton force balance, PL/EA, GA/h, cantilever bending + Timoshenko shear,
    Euler pinned column (Gere, Mechanics of Materials). The sector-arm ring
    model uses a deliberately restrictive 12 mm strip and 3.5 mm radial arm;
    the actual ring has plate continuity and direct rail-to-OD paths. Its
    compliance is an assumed sensitivity, not a derived assembled stiffness.
    All-ring sharing and a single-ring worst placement are retained separately.
    The full path cannot be accepted from mean shear, ring arm or gross paper.
    """
    from itertools import pairwise

    rail_load = force_n if rail_force_n is None else rail_force_n
    vals = [
        force_n,
        rail_area_mm2,
        rail_weak_i_mm4,
        paper_hot_mpa,
        plywood_hot_mpa,
        adhesive_hot_mpa,
        bond_gap_mm,
        upper_wall_mm,
        aft_wall_mm,
        joint_stiffness_n_mm,
        design_factor,
        rail_load,
        aft_path_length_mm,
        upper_path_length_mm,
        ring_arm_mm,
        ring_width_mm,
        ring_thickness_mm,
        *ring_bond_areas_mm2,
    ]
    if any(v <= 0 or not np.isfinite(v) for v in vals) or len(ring_bond_areas_mm2) != 5:
        raise ValueError("Invalid hand-budget inputs")
    base_bore = 32.5
    upper_area = np.pi * ((base_bore + upper_wall_mm) ** 2 - base_bore**2)
    aft_area = np.pi * ((base_bore + aft_wall_mm) ** 2 - base_bore**2)
    g = adhesive_hot_mpa / 2.6
    bond_k = [g * a / bond_gap_mm for a in ring_bond_areas_mm2]
    ring_arm = ring_arm_mm
    width, thick = ring_width_mm, ring_thickness_mm
    inertia = width * thick**3 / 12
    ring_bending_k = 3 * plywood_hot_mpa * inertia / ring_arm**3
    ring_shear_k = (5 / 6) * (plywood_hot_mpa / 2.5) * (width * thick) / ring_arm
    per_ring_k = 3 / (1 / ring_bending_k + 1 / ring_shear_k)
    connections = [1 / (1 / k + 1 / per_ring_k) for k in bond_k]
    paper_k = paper_hot_mpa * aft_area / aft_path_length_mm
    upper_k = paper_hot_mpa * upper_area / upper_path_length_mm
    bound_shortening = (
        rail_load / sum(connections)
        + rail_load / paper_k
        + force_n / upper_k
        + force_n / joint_stiffness_n_mm
    )
    overall_optimistic_k = force_n / bound_shortening
    max_clear = max(b - a - 3 for a, b in pairwise(ring_stations_mm))
    unbraced_length = ring_stations_mm[-1] - ring_stations_mm[0] - 3.0
    full_pcr = 3 * np.pi**2 * plywood_hot_mpa * rail_weak_i_mm4 / unbraced_length**2
    brace_pcr = 3 * np.pi**2 * plywood_hot_mpa * rail_weak_i_mm4 / max_clear**2
    return {
        "load_n": force_n,
        "motor_flank_load_bound_n": rail_load,
        "design_factor": design_factor,
        "ring_positions_mm": ring_stations_mm,
        "ring_bond_contact_areas_mm2": ring_bond_areas_mm2,
        "ring_bond_shear_stiffness_n_mm": bond_k,
        "assumed_finite_ring_axial_stiffness_n_mm": per_ring_k,
        "finite_ring_plus_bond_stiffness_n_mm": connections,
        "aft_shell_gross_area_mm2": float(aft_area),
        "upper_shell_gross_area_mm2": float(upper_area),
        "aft_shell_gross_stiffness_n_mm": float(paper_k),
        "aft_path_length_mm": aft_path_length_mm,
        "entire_upper_tube_axial_stiffness_n_mm": float(upper_k),
        "upper_path_length_mm": upper_path_length_mm,
        "assumed_joint_stiffness_n_mm": joint_stiffness_n_mm,
        "optimistic_serial_path_stiffness_n_mm": float(overall_optimistic_k),
        "optimistic_axial_shortening_mm": float(bound_shortening),
        "required_minimum_hot_upper_axial_strength_mpa_gross": float(
            design_factor * force_n / upper_area
        ),
        "required_minimum_hot_aft_axial_strength_mpa_gross": float(
            design_factor * rail_load / aft_area
        ),
        "maximum_permissible_upper_local_stress_multiplier_at_2mpa": float(
            2 * upper_area / (design_factor * force_n)
        ),
        "maximum_permissible_aft_local_stress_multiplier_at_2mpa": float(
            2 * aft_area / (design_factor * rail_load)
        ),
        "required_hot_bond_shear_mpa_if_uniform_all_rings": design_factor
        * rail_load
        / sum(ring_bond_areas_mm2),
        "required_hot_bond_shear_mpa_if_one_smallest_ring": design_factor
        * rail_load
        / min(ring_bond_areas_mm2),
        "required_hot_plywood_axial_mpa_equal_rails": design_factor
        * rail_load
        / (3 * rail_area_mm2),
        "unbraced_full_length_euler_n": float(full_pcr),
        "ideally_braced_euler_n": float(brace_pcr),
        "effective_unbraced_length_mm": unbraced_length,
        "ideal_maximum_clear_braced_length_mm": max_clear,
        "required_hot_rail_modulus_mpa_unbraced": float(
            design_factor * rail_load * unbraced_length**2 / (3 * np.pi**2 * rail_weak_i_mm4)
        ),
        "required_hot_rail_modulus_mpa_ideal_braces": float(
            design_factor * rail_load * max_clear**2 / (3 * np.pi**2 * rail_weak_i_mm4)
        ),
        "ring_bond_peel_strength_required_mpa": None,
        "retention_capacity_required_n_at_least": design_factor * force_n,
        "numerical_assembly_acceptance": False,
        "limitations": [
            "No physical ring is grounded: bond/ring, aft shell, whole upper tube and finite joint compliances are serial.",
            "The scalar path is optimistic parallel sharing; it does not predict actual individual ring reactions, bending, shell ovalization, peel or local crushing.",
            "The larger motor-flank load bounds rail/ring/bond and aft-paper demands; the forward-body reaction is used only for upper tube and joint. This avoids using the smaller joint reaction to clear the mount.",
            "The assumed ring-sector arm is not a verified plate stiffness; actual 3D structure includes direct rail-to-OD transfer and slots.",
            "Upper shortening uses all path force over the whole 778 mm tube and is a bound; actual upstream mass inertia reduces force toward the nose.",
            "Euler values bracket zero and ideal brace support and are not assembled-shell buckling factors.",
            "The retention number is only a same-magnitude reverse-load minimum; recovery opening, extraction, TVC and handling can govern separately.",
            "No peel or mixed-mode allowable is inferred from manufacturer tensile, lap-shear, tear or service-temperature data.",
        ],
    }


def peel_foundation_known_case(divisions: int = 120) -> dict[str, Any]:
    """Verify the retained normal springs against a semi-infinite DCB solution.

    Two identical Euler-Bernoulli beams on a continuous normal elastic foundation,
    equal/opposite 1 N end forces. Relative opening w satisfies D w'''' + k w=0,
    D=(1/EI1+1/EI2)^-1 and beta=(k/4D)^1/4. For a moment-free loaded end,
    w(0)=P/(2 D beta^3). See Hetenyi, Beams on Elastic Foundation (1946),
    semi-infinite beam under end force. The fixture extends over 13 decay lengths;
    its remote clamp differs negligibly from the semi-infinite boundary.
    Surface eccentricity is disabled to isolate and verify the normal operator.
    """
    young, width, thickness, length = 1000.0, 10.0, 1.0, 100.0
    gap, adhesive_e, force = 0.5, 0.026, 1.0
    bending = young * width * thickness**3 / 12
    relative_bending = bending / 2
    foundation = adhesive_e * width / gap
    beta = (foundation / (4 * relative_bending)) ** 0.25
    expected = force / (2 * relative_bending * beta**3)
    result = overlap_beam_spring(
        divisions=divisions,
        length_mm=length,
        overlap_mm=length,
        width_mm=width,
        thickness_mm=(thickness, thickness),
        young_mpa=(young, young),
        adhesive_thickness_mm=gap,
        adhesive_young_mpa=adhesive_e,
        adhesive_poisson=0.3,
        force_n=1e-20,
        outer_load_fraction=0.5,
        eccentric_interface=False,
        opening_force_n=force,
    )
    error = abs(result["end_relative_opening_mm"] / expected - 1)
    result.update(
        fixture="double-cantilever normal foundation, semi-infinite end-opening solution",
        expected_end_opening_mm=expected,
        beta_per_mm=beta,
        length_over_decay_length=length * beta,
        relative_error=error,
        verified=error < 0.001
        and abs(result["external_work_nmm"] / (2 * result["strain_energy_nmm"]) - 1) < 1e-8,
    )
    return result


def annular_brace_sensitivity(
    outer_radius_mm: float,
    inner_radius_mm: float,
    axial_thickness_mm: float,
    young_mpa: float,
    channel_inner_radius_mm: float | None = None,
) -> dict[str, Any]:
    """Elementary circumferential-brace sensitivity, never a support acceptance.

    For diametrically opposed radial forces on a slender, unperforated circular
    ring: delta=(pi/4-2/pi) P R^3/(EI). This follows Castigliano integration of
    ring bending energy (Roark's Formulas for Stress and Strain, circular rings).
    The section is I=t*w^3/12. Actual wide, slotted, rail-connected rings and the
    shell/bond boundary do not match that idealization. The guaranteed continuous
    inner band is reported separately where a fin channel crosses the ring.
    """
    if not 0 < inner_radius_mm < outer_radius_mm or min(axial_thickness_mm, young_mpa) <= 0:
        raise ValueError("Invalid annular brace geometry")
    width = outer_radius_mm - inner_radius_mm
    radius = (outer_radius_mm + inner_radius_mm) / 2
    inertia = axial_thickness_mm * width**3 / 12
    result: dict[str, Any] = {
        "outer_radius_mm": outer_radius_mm,
        "inner_radius_mm": inner_radius_mm,
        "radial_width_mm": width,
        "mean_radius_mm": radius,
        "unperforated_section_inplane_i_mm4": inertia,
        "ideal_diametric_stiffness_n_mm": young_mpa
        * inertia
        / ((np.pi / 4 - 2 / np.pi) * radius**3),
        "width_over_mean_radius": width / radius,
        "slender_ring_assumption_demonstrated": width / radius <= 0.1,
        "actual_assembled_support_stiffness_available": False,
        "slots_bonds_shell_and_rail_junctions_included": False,
        "numerical_assembly_acceptance": False,
    }
    if channel_inner_radius_mm is not None:
        band_outer = min(outer_radius_mm, channel_inner_radius_mm)
        if band_outer <= inner_radius_mm:
            result["continuous_inner_band"] = None
        else:
            result["continuous_inner_band"] = annular_brace_sensitivity(
                band_outer, inner_radius_mm, axial_thickness_mm, young_mpa
            )
    return result
