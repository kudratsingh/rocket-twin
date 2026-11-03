"""Export frozen CCX diagnostic fields; no solving, interpolation or acceptance."""

from __future__ import annotations

import hashlib
import json
import re
import resource
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
CASE = ROOT / "build/wo03-f2-c1-pressure-footprint-v1/2.0"
OUTPUT = ROOT / "build/wo03-f2-c1-diagnostic-fields-v1/fields.npz"
METADATA = ROOT / "runs/wo03-g80-f2-c1-field-export-20261103-v1/metadata.json"
INPUTS = {
    "spec": (
        ROOT / "configs/vehicle/candidates/g80-f2-ballast.yaml",
        "7b188941de7fd4061800936c957b962d2165a5965c5cd9e46476d86242ed5a78",
    ),
    "local_step": (
        ROOT / "build/wo03-g80-f2-local-cad-v2/notched_forward_ring.step",
        "7de1c2cbd7ecbad28f1a10aa3f80ca5be5ab3a330c4cbacc5e427a32ddce786c",
    ),
    "mesh": (CASE / "mesh.msh", "b5f6d3e994ca43aa9990128e6e892999a4d3eb35e8c445d5d58bf2417fe4a862"),
    "deck": (CASE / "case.inp", "4f6e35cf7dc06f7b991f9ace1cfe4ef3de21331f6686563bb6de647190730655"),
    "dat": (CASE / "case.dat", "c006eef6769871b51b5bd02137b2807da8eef9335593904be5658430be3dc5dd"),
    "grid_report": (
        CASE / "report.json",
        "6eb2d2cd57db35919934c27513ff885fe488fd7a350279b1d5ad0f0824ea4a59",
    ),
    "campaign_record": (
        ROOT / "runs/wo03-g80-f2-c1-method-20261103-v1/record.json",
        "525c38ad3897f0b7b54ecb15f36e83f6ad15916a4cbc91ac1fcbb1a4151f91bc",
    ),
}


def digest(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def read_deck(path: Path) -> tuple[dict[int, list[float]], dict[int, list[int]]]:
    nodes: dict[int, list[float]] = {}
    elements: dict[int, list[int]] = {}
    mode = ""
    with path.open() as lines:
        for line in lines:
            line = line.strip()
            if line.startswith("*"):
                mode = (
                    "node"
                    if line.upper() == "*NODE"
                    else "element" if line.upper().startswith("*ELEMENT,TYPE=C3D10,") else ""
                )
                continue
            if mode and line:
                fields = [s.strip() for s in line.split(",")]
                if len(fields) != (4 if mode == "node" else 11):
                    raise ValueError(f"malformed {mode} record")
                ident = int(fields[0])
                target = nodes if mode == "node" else elements
                if ident <= 0 or ident in target:
                    raise ValueError(f"duplicate or invalid {mode} ID {ident}")
                if mode == "node":
                    values = [float(x) for x in fields[1:]]
                    if not np.isfinite(values).all():
                        raise ValueError("nonfinite coordinates")
                    nodes[ident] = values
                else:
                    elements[ident] = [int(x) for x in fields[1:]]
    if not nodes or not elements or any(n not in nodes for row in elements.values() for n in row):
        raise ValueError("empty mesh or missing connectivity node")
    return nodes, elements


def read_fields(
    path: Path, nodes: dict[int, list[float]], elements: dict[int, list[int]]
) -> tuple[np.ndarray, np.ndarray]:
    node_index = {ident: i for i, ident in enumerate(nodes)}
    element_index = {ident: i for i, ident in enumerate(elements)}
    u = np.full((2, len(nodes), 3), np.nan)
    stress = np.full((2, len(elements), 4, 6), np.nan)
    seen = set()
    step, mode = 0, ""
    with path.open() as lines:
        for raw in lines:
            line = raw.strip()
            match = re.fullmatch(r"S T E P\s+(\d+)", line)
            if match:
                step = int(match.group(1))
                mode = ""
                if step not in (1, 2):
                    raise ValueError(f"unexpected step {step}")
                continue
            if line.startswith(("displacements (", "stresses (")):
                mode = "u" if line.startswith("displacements (") else "stress"
                expected = (
                    "displacements (vx,vy,vz) for set ALLN"
                    if mode == "u"
                    else "stresses (elem, integ.pnt.,sxx,syy,szz,sxy,sxz,syz) for set WOOD"
                )
                if step not in (1, 2) or not line.startswith(expected) or (step, mode) in seen:
                    raise ValueError("unexpected or duplicate field section")
                if not re.search(r"time\s+([\d.E+\-]+)$", line) or float(line.split()[-1]) != step:
                    raise ValueError("field time does not match step")
                seen.add((step, mode))
                continue
            if not line or not mode:
                continue
            fields = line.split()
            if mode == "u":
                if len(fields) != 4 or int(fields[0]) not in node_index:
                    raise ValueError("unexpected displacement record")
                index = node_index[int(fields[0])]
                if np.isfinite(u[step - 1, index]).any():
                    raise ValueError("duplicate displacement ID")
                u[step - 1, index] = [float(x) for x in fields[1:]]
            else:
                if (
                    len(fields) != 8
                    or int(fields[0]) not in element_index
                    or int(fields[1]) not in (1, 2, 3, 4)
                ):
                    raise ValueError("unexpected stress element/IP record")
                index, ip = element_index[int(fields[0])], int(fields[1]) - 1
                if np.isfinite(stress[step - 1, index, ip]).any():
                    raise ValueError("duplicate stress element/IP")
                stress[step - 1, index, ip] = [float(x) for x in fields[2:]]
    if (
        seen != {(1, "u"), (1, "stress"), (2, "u"), (2, "stress")}
        or not np.isfinite(u).all()
        or not np.isfinite(stress).all()
    ):
        raise ValueError("missing phase, node, element, IP or nonfinite field")
    return u, stress


def main() -> None:
    resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
    started = time.monotonic()
    if OUTPUT.exists() or METADATA.exists():
        raise FileExistsError("preserve existing field export; remove nothing automatically")
    for name, (path, expected) in INPUTS.items():
        if digest(path) != expected:
            raise ValueError(f"{name} source hash mismatch")
    report = json.loads(INPUTS["grid_report"][0].read_text())
    record = json.loads(INPUTS["campaign_record"][0].read_text())
    if (
        report not in record["reports"]
        or report["h_mm"] != 2.0
        or report["installed_strength_accepted"]
        or record["installed_strength_accepted"]
    ):
        raise ValueError("grid/report identity mismatch")
    nodes, elements = read_deck(INPUTS["deck"][0])
    if len(nodes) != report["quality"]["nodes"] or len(elements) != report["quality"]["elements"]:
        raise ValueError("mesh counts mismatch report")
    u, stress = read_fields(INPUTS["dat"][0], nodes, elements)
    if time.monotonic() - started > 20:
        raise TimeoutError("20-second wall budget reached before output")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    np.savez(
        OUTPUT,
        node_ids=np.array(list(nodes), dtype=np.int64),
        coordinates_mm=np.array(list(nodes.values())),
        element_ids=np.array(list(elements), dtype=np.int64),
        connectivity_node_ids=np.array(list(elements.values()), dtype=np.int64),
        displacement_mm=u,
        stress_mpa=stress,
    )
    if time.monotonic() - started > 20:
        OUTPUT.unlink()
        raise TimeoutError("20-second wall budget reached during output")
    metadata = {
        "schema_version": "1.0.0",
        "identity": "G80-F2-C1-pressure-footprint-v1",
        "component_fixture": "hypothetical finite-support notched forward ring; 2.0 mm pressure-footprint grid",
        "status": "diagnostic; required three-grid convergence unavailable",
        "active_vehicle_compatible": False,
        "installed_strength_accepted": False,
        "geometry": "Frozen F2 ring from local STEP (32.3 mm outer radius), not proposed F2-C1-fit 32.2 mm radius.",
        "frame": "local X/Y transverse, Z positive aft; station_m = 1.075 + Z_mm/1000",
        "units": {"coordinates": "mm", "displacement": "mm", "stress": "MPa"},
        "phases": ["seventy_thirty", "single_anchor"],
        "stress_components": ["sxx", "syy", "szz", "sxy", "sxz", "syz"],
        "integration_points": [1, 2, 3, 4],
        "array_shapes": {
            "node_ids": [len(nodes)],
            "coordinates_mm": [len(nodes), 3],
            "element_ids": [len(elements)],
            "connectivity_node_ids": [len(elements), 10],
            "displacement_mm": list(u.shape),
            "stress_mpa": list(stress.shape),
        },
        "connectivity": "C3D10 node IDs as stored in CalculiX deck; no reordering",
        "stress_location": "per-element four solver integration points; no averaging or interpolation",
        "inputs": {
            name: {"path": str(path.relative_to(ROOT)), "sha256": expected}
            for name, (path, expected) in INPUTS.items()
        },
        "output": {"path": str(OUTPUT.relative_to(ROOT)), "sha256": digest(OUTPUT)},
        "export_wall_s": time.monotonic() - started,
    }
    METADATA.parent.mkdir(parents=True, exist_ok=True)
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n")
    print(
        json.dumps(
            {"output": str(OUTPUT), "metadata": str(METADATA), "wall_s": metadata["export_wall_s"]}
        )
    )


if __name__ == "__main__":
    main()
