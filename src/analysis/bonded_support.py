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
        gmsh.model.mesh.generate(3)
        gmsh.model.mesh.optimize("HighOrder")
        types, element_tags, _ = gmsh.model.mesh.getElements(3)
        if set(types) != {11}:
            raise ValueError(f"Expected exclusively quadratic tetrahedra: {types}")
        local, _ = gmsh.model.mesh.getIntegrationPoints(11, "Gauss4")
        _, determinants, _ = gmsh.model.mesh.getJacobians(11, local)
        determinant_min = float(np.min(determinants))
        if determinant_min <= 0:
            raise ValueError(f"Nonpositive quadratic Jacobian: {determinant_min}")
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
                818.0
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
