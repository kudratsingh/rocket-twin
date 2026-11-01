"""Bounded Elmer bridge diagnostic; default preparation, execution disabled."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import shutil
import sys
from decimal import Decimal
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build/wo03-elmer-bridge-diagnostic-v1"
CONFIG = ROOT / "configs/studies/wo03-elmer-bridge-diagnostic.yaml"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_vectors(deck):
    steps = deck.split("*STEP\n")[1:]
    if len(steps) != 2:
        raise ValueError("Unexpected source steps")
    result = []
    for step in steps:
        m = re.search(r"(?ms)^\*CLOAD,OP=NEW\n(.*?)(?=^\*)", step)
        if not m:
            raise ValueError("Missing original CLOAD")
        values = {}
        for line in m.group(1).splitlines():
            node, dof, token = line.split(",")
            node = int(node)
            if dof != "3" or node in values or not math.isfinite(float(token)):
                raise ValueError("Invalid CLOAD")
            values[node] = token
        result.append(values)
    return result


def load_mesh(prepared):
    mapping = {
        int(k): int(v) for k, v in json.loads((prepared / "node-map.json").read_text()).items()
    }
    nodes = {}
    for line in (prepared / "mesh/mesh.nodes").read_text().splitlines():
        x = line.split()
        n = int(x[0])
        nodes[n] = np.array([float(v) for v in x[2:]])
    if (
        len(mapping) != 42715
        or set(mapping.values()) != set(range(1, 42716))
        or set(nodes) != set(mapping.values())
    ):
        raise ValueError("Node map mismatch")
    xyz = np.asarray(list(nodes.values()))
    if not np.isfinite(xyz).all() or len({tuple(np.round(p, 12)) for p in xyz}) != len(xyz):
        raise ValueError("Nonfinite or ambiguous coordinates")
    return mapping, nodes


def analyze_arrays(ids, coords, displacements, reactions, support, loads):
    if len(ids) != len(set(ids)) or set(ids) != set(coords):
        raise ValueError("Output IDs missing or duplicate")
    if (
        set(displacements) != set(ids)
        or set(reactions) != set(ids)
        or not set(support) <= set(ids)
        or not set(loads) <= set(ids)
    ):
        raise ValueError("Node coverage mismatch")
    for arr in (displacements, reactions):
        if any(np.asarray(v).shape != (3,) or not np.isfinite(v).all() for v in arr.values()):
            raise ValueError("Malformed/nonfinite vector")
    applied = np.array([0.0, 0.0, math.fsum(float(x) for x in loads.values())])
    R = np.array([math.fsum(float(reactions[n][j]) for n in support) for j in range(3)])
    res = R + applied
    bound = np.array(
        [math.fsum(math.ulp(float(reactions[n][j])) / 2 for n in support) for j in range(3)]
    )
    # Account for conversion of every original decimal load token to binary64
    # and the accurately rounded summed applied force as well as output encoding.
    bound[2] += (
        math.fsum(math.ulp(float(v)) / 2 for v in loads.values()) + math.ulp(float(applied[2])) / 2
    )
    norm = float(np.linalg.norm(res))
    bnorm = float(np.linalg.norm(bound))
    status = (
        "pass"
        if norm + bnorm <= 1e-5
        else ("fail" if max(0.0, norm - bnorm) > 1e-5 else "unavailable_precision")
    )
    moment = np.sum([np.cross(coords[n], reactions[n]) for n in support], axis=0) + np.sum(
        [np.cross(coords[n], [0, 0, float(v)]) for n, v in loads.items()], axis=0
    )
    mb = np.sum(
        [
            [
                abs(coords[n][1]) * math.ulp(float(reactions[n][2])) / 2
                + abs(coords[n][2]) * math.ulp(float(reactions[n][1])) / 2,
                abs(coords[n][2]) * math.ulp(float(reactions[n][0])) / 2
                + abs(coords[n][0]) * math.ulp(float(reactions[n][2])) / 2,
                abs(coords[n][0]) * math.ulp(float(reactions[n][1])) / 2
                + abs(coords[n][1]) * math.ulp(float(reactions[n][0])) / 2,
            ]
            for n in support
        ],
        axis=0,
    )
    mb += np.array(
        [
            math.fsum(abs(float(coords[n][1])) * math.ulp(float(v)) / 2 for n, v in loads.items()),
            math.fsum(abs(float(coords[n][0])) * math.ulp(float(v)) / 2 for n, v in loads.items()),
            0.0,
        ]
    )
    return {
        "applied_force_N": applied.tolist(),
        "support_reaction_N": R.tolist(),
        "force_residual_N": res.tolist(),
        "force_encoding_bound_N": bound.tolist(),
        "strict_force_status": status,
        "moment_residual_Nm": moment.tolist(),
        "moment_encoding_bound_Nm": mb.tolist(),
        "moment_status": "reported_no_original_threshold",
        "max_displacement_norm_m": max(float(np.linalg.norm(v)) for v in displacements.values()),
    }


def read_vtu(path, nodes, support, loads):
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy

    vtk.vtkSMPTools.Initialize(1)
    vtk.vtkMultiThreader.SetGlobalMaximumNumberOfThreads(1)
    reader = vtk.vtkXMLUnstructuredGridReader()
    reader.SetFileName(str(path))
    reader.Update()
    grid = reader.GetOutput()
    pts = vtk_to_numpy(grid.GetPoints().GetData())
    pd = grid.GetPointData()
    names = [pd.GetArrayName(i) for i in range(pd.GetNumberOfArrays())]

    def field(name):
        choices = [n for n in names if n and n.lower() == name.lower()]
        if len(choices) != 1:
            raise ValueError("Missing or ambiguous " + name)
        a = vtk_to_numpy(pd.GetArray(choices[0]))
        if a.dtype != np.float64 or a.shape != (len(nodes), 3) or not np.isfinite(a).all():
            raise ValueError("Invalid field " + name)
        return a

    U = field("displacement")
    R = field("displacement loads")
    if pts.dtype != np.float64 or pts.shape != (len(nodes), 3) or not np.isfinite(pts).all():
        raise ValueError("Invalid coordinates")
    lookup = {tuple(np.round(x, 12)): i for i, x in enumerate(pts)}
    if len(lookup) != len(nodes):
        raise ValueError("Duplicate output coordinates")
    ids = sorted(nodes)
    order = [lookup[tuple(np.round(nodes[n], 12))] for n in ids]
    if np.max(np.abs(pts[order] - np.array([nodes[n] for n in ids]))) > 1e-12:
        raise ValueError("VTU coordinate mismatch")
    ud = {n: U[order[i]] for i, n in enumerate(ids)}
    rd = {n: R[order[i]] for i, n in enumerate(ids)}
    return analyze_arrays(ids, nodes, ud, rd, support, loads), ud


def decimal_token_half_width(token):
    """Prior reciprocal audit's half-last-printed-decimal-place bound."""
    value = Decimal(token)
    if not value.is_finite():
        raise ValueError("Nonfinite load token")
    return float(Decimal("0.5").scaleb(value.as_tuple().exponent))


def reciprocal(load1, u1, load2, u2):
    def dot(load, u):
        terms = [float(value) * float(u[node][2]) for node, value in load.items()]
        result = math.fsum(terms)
        bound = (
            math.fsum(
                abs(float(value)) * math.ulp(float(u[node][2])) / 2
                + abs(float(u[node][2]))
                * (decimal_token_half_width(value) + math.ulp(float(value)) / 2)
                + (decimal_token_half_width(value) + math.ulp(float(value)) / 2)
                * math.ulp(float(u[node][2]))
                / 2
                for node, value in load.items()
            )
            + math.ulp(result) / 2
        )
        return result, bound

    w11, b11 = dot(load1, u1)
    w22, b22 = dot(load2, u2)
    w12, b12 = dot(load1, u2)
    w21, b21 = dot(load2, u1)
    difference = abs(w12 - w21)
    bound = b12 + b21 + math.ulp(difference) / 2
    return {
        "equal_half_F_dot_U_Nm": 0.5 * w11,
        "single_half_F_dot_U_Nm": 0.5 * w22,
        "equal_half_work_encoding_bound_Nm": 0.5 * b11,
        "single_half_work_encoding_bound_Nm": 0.5 * b22,
        "F_equal_dot_U_single_Nm": w12,
        "F_single_dot_U_equal_Nm": w21,
        "absolute_difference_Nm": difference,
        "combined_encoding_bound_Nm": bound,
        "status": (
            "consistent_with_output_encoding"
            if difference <= bound
            else "outside_output_encoding_bound"
        ),
        "criterion_basis": "prior audit compares reciprocal difference with propagated output/token precision; no added engineering tolerance",
    }


def inputs(cfg):
    prepared = ROOT / cfg["input_root"]
    review = json.loads((ROOT / cfg["input_review"]).read_text())
    irec = json.loads((prepared / "record.json").read_text())
    for key, cfgkey in (
        ("source_deck", "source_deck"),
        ("source_metadata", "source_metadata"),
        ("elmer_solver", "solver"),
        ("stress_module", "module"),
    ):
        if sha(ROOT / cfg[cfgkey]) != irec["source_sha256_before"][key]:
            raise ValueError("Original bridge input differs: " + key)
    deck = (ROOT / cfg["source_deck"]).read_text()
    meta = json.loads((ROOT / cfg["source_metadata"]).read_text())
    nodal = json.loads((ROOT / cfg["nodal_fixture_result"]).read_text())
    if nodal["status"] != "single_nodal_rhs_known_answer_pass_not_qualified" or not all(
        nodal[k]
        for k in ("source_unchanged", "prefix_unchanged", "generated_unchanged", "ledger_unchanged")
    ):
        raise ValueError("Nodal known-case gate absent")
    for k in ("solver", "module"):
        if sha(ROOT / cfg[k]) != cfg[k + "_sha256"]:
            raise ValueError("Solver/module hash mismatch")
    for p, h in review["source_ledger"].items():
        if sha(p) != h:
            raise ValueError("Input converter source changed")
    for p, h in irec["output_hashes"].items():
        if sha(ROOT / p) != h:
            raise ValueError("Prepared input changed")
    prefix = ROOT / ".cache/elmer-evaluation/setup-v1/prefix"
    pi = {str(p): sha(p) for p in prefix.rglob("*") if p.is_file()}
    if pi != review["prefix_sha256"]:
        raise ValueError("Prefix changed")
    probe = json.loads(
        (
            ROOT / ".cache/elmer-evaluation/structural-module-v1/build-attempt/record.json"
        ).read_text()
    )
    runtime = {p: v["sha256"] for p, v in probe["runtime_dependencies"].items() if v.get("sha256")}
    if any(sha(p) != h for p, h in runtime.items()):
        raise ValueError("Runtime dependency changed")
    mapping, nodes = load_mesh(prepared)
    source = load_vectors(deck)
    mapped = []
    if len(meta["support_node_ids"]) != 1574:
        raise ValueError("Support count")
    support = [mapping[int(n)] for n in meta["support_node_ids"]]
    for name, loads in zip(("equal", "single"), source, strict=True):
        sif = (prepared / name / "case.sif").read_text()
        found = re.findall(
            r"Target Nodes\(1\) = (\d+)\n  Displacement 3 Load = Real ([^\n]+)\n", sif
        )
        expected = {str(mapping[n]): v for n, v in loads.items()}
        if len(found) != len(loads) or dict(found) != expected:
            raise ValueError("Exact source-to-SIF load mismatch")
        mapped.append({mapping[n]: v for n, v in loads.items()})
        force = math.fsum(float(x) for x in loads.values())
        moment = np.sum(
            [np.cross(nodes[mapping[n]], [0, 0, float(v)]) for n, v in loads.items()], axis=0
        )
        baseline = irec["load_resultants"][len(mapped) - 1]
        if abs(force - baseline["force_N"][2]) > 1e-8 or not np.allclose(
            moment * 1000, baseline["moment_Nmm"], rtol=1e-10, atol=1e-6
        ):
            raise ValueError("Load resultant mismatch")
    return {
        "prepared": prepared,
        "review": review,
        "irec": irec,
        "deck": deck,
        "meta": meta,
        "mapping": mapping,
        "nodes": nodes,
        "support": support,
        "loads": mapped,
        "prefix": prefix,
        "prefix_hash": pi,
        "runtime_hash": runtime,
    }


def prepare(cfg):
    if cfg["native_execution_authorized"] or cfg["required_ci_confirmed"]:
        raise ValueError("Prepare-only flags must be false")
    d = inputs(cfg)
    OUT.mkdir(parents=True, exist_ok=True)
    record = OUT / "preflight.json"
    if record.exists():
        raise FileExistsError(record)
    import vtkmodules.vtkCommonCore as vtkcore
    import vtkmodules.vtkIOXML as vtkio

    paths = [
        Path(__file__).resolve(),
        Path(vtkio.__file__),
        Path(vtkcore.__file__),
        ROOT / "tests/test_elmer_bridge_diagnostic.py",
        CONFIG,
        ROOT / cfg["input_review"],
        ROOT / cfg["source_deck"],
        ROOT / cfg["source_metadata"],
        ROOT / cfg["nodal_fixture_result"],
        ROOT / cfg["solver"],
        ROOT / cfg["module"],
        ROOT / "scripts/wo03_owned_process.py",
    ]
    before = {str(p): sha(p) for p in paths}
    (OUT / "config-disabled.yaml").write_bytes(CONFIG.read_bytes())
    after = {str(p): sha(p) for p in paths}
    if before != after:
        raise ValueError("Preflight inputs changed")
    result = {
        "status": "prepared_no_native",
        "source_before": before,
        "source_after": after,
        "input_output_sha256": d["irec"]["output_hashes"],
        "prefix_sha256": d["prefix_hash"],
        "runtime_sha256": d["runtime_hash"],
        "nodes_used": len(d["nodes"]),
        "support_nodes": len(d["support"]),
        "load_nodes": [len(x) for x in d["loads"]],
        "reader": "Float64 U and displacement loads; coordinate-to-node uniqueness; no sign flip",
        "reciprocity_criterion": "difference vs propagated binary/token rounding bounds only; no extra tolerance",
        "nodal_B_status": "single known-answer strict force/displacement passed",
        "required_ci_confirmed": False,
        "native_execution_authorized": False,
        "native_execution_performed": False,
        "packet_planned_cpu_s": 420,
    }
    record.write_text(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "status": result["status"],
                "nodes": result["nodes_used"],
                "loads": result["load_nodes"],
            }
        )
    )


def execute(cfg):
    if not cfg["native_execution_authorized"] or not cfg["required_ci_confirmed"]:
        raise ValueError("Native execution not admitted or required CI not confirmed")
    frozen = yaml.safe_load((OUT / "config-disabled.yaml").read_text())
    norm = dict(cfg)
    norm["native_execution_authorized"] = False
    norm["required_ci_confirmed"] = False
    if norm != frozen:
        raise ValueError("Configuration changed beyond explicit admission")
    from scripts.wo03_owned_process import darwin_process_callbacks, run_owned

    pre = json.loads((OUT / "preflight-reviewed.json").read_text())
    for p, h in pre["source_before"].items():
        if p != str(CONFIG) and sha(p) != h:
            raise ValueError("Frozen source changed")
    d = inputs(cfg)
    native = OUT / "native"
    native.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    env = dict(os.environ)
    for n in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        env[n] = "1"
    env["ELMER_HOME"] = str(d["prefix"].resolve())
    env["ELMER_LIB"] = str((d["prefix"] / "share/elmersolver/lib").resolve())
    rss, desc = darwin_process_callbacks()
    rec = {
        "status": "started",
        "cases": [],
        "qualification": False,
        "rss_scope": "supervised root process only",
        "source_before": {
            str(p): sha(p)
            for p in [
                Path(__file__).resolve(),
                CONFIG,
                ROOT / cfg["input_review"],
                ROOT / cfg["source_deck"],
                ROOT / cfg["source_metadata"],
                ROOT / cfg["nodal_fixture_result"],
                ROOT / cfg["solver"],
                ROOT / cfg["module"],
            ]
        },
    }

    def persist():
        u = resource.getrusage(resource.RUSAGE_SELF)
        rec["parent_cpu_s"] = u.ru_utime + u.ru_stime
        rec["parent_peak_rss_bytes"] = u.ru_maxrss
        (native / "record.json").write_text(json.dumps(rec, indent=2) + "\n")

    persist()
    solutions = []
    try:
        for index, name in enumerate(("equal", "single")):
            case_root = native / name
            case_root.mkdir()
            shutil.copytree(d["prepared"] / "mesh", case_root / "mesh")
            folder = case_root / "case"
            folder.mkdir()
            shutil.copyfile(d["prepared"] / name / "case.sif", folder / "case.sif")
            for p in (d["prepared"] / "mesh").iterdir():
                if sha(p) != sha(case_root / "mesh" / p.name):
                    raise ValueError("Mesh copy differs")
            if sha(folder / "case.sif") != sha(d["prepared"] / name / "case.sif"):
                raise ValueError("SIF copy differs")
            solver = ROOT / cfg["solver"]
            cmd = (
                "import os,resource;resource.setrlimit(resource.RLIMIT_CPU,(120,120));os.execv("
                + repr(str(solver))
                + ",["
                + repr(str(solver))
                + ',"case.sif"])'
            )
            st = run_owned(
                [sys.executable, "-c", cmd],
                log_path=folder / "solver.log",
                status_path=folder / "status.json",
                wall_limit_s=120,
                rss_callback=rss,
                descendants_callback=desc,
                rss_limit_bytes=2147483648,
                cwd=folder,
                env=env,
            )
            lines = (folder / "solver.log").read_text(errors="replace").splitlines()
            unused = "solver 1              linear system abort not converged"
            count = sum(x.strip().lower() == unused for x in lines)
            for line in lines:
                x = line.strip().lower()
                if x == unused:
                    continue
                if "fatal:" in x or "error:" in x or "not converged" in x:
                    raise ValueError("Native failure text: " + line)
            log = "\n".join(lines).lower()
            if (
                "directsolver: using direct method: umfpack" not in log
                or "elmer solver: all done" not in log
            ):
                raise ValueError("Direct solver completion missing")
            found = [
                p
                for p in (folder / "field_t0001.vtu", case_root / "mesh/field_t0001.vtu")
                if p.is_file()
            ]
            if len(found) != 1:
                raise ValueError("VTU missing or ambiguous")
            result, u = read_vtu(found[0], d["nodes"], d["support"], d["loads"][index])
            rec["cases"].append(
                {
                    "case": name,
                    "result": result,
                    "native_status": st,
                    "vtu_sha256": sha(found[0]),
                    "ignored_exact_unused_keyword_count": count,
                }
            )
            persist()
            if result["strict_force_status"] != "pass":
                raise ValueError("Strict force unavailable or failed")
            solutions.append(u)
            # No next case after any changed source, prefix or input.
            _ = inputs(cfg)
        rec["reciprocity"] = reciprocal(d["loads"][0], solutions[0], d["loads"][1], solutions[1])
        rec["status"] = (
            "diagnostic_complete_not_qualified"
            if rec["reciprocity"]["status"] == "consistent_with_output_encoding"
            else "stopped_reciprocity_outside_encoding_bound"
        )
    except Exception as exc:
        rec.update(status="stopped", error=repr(exc))
        raise
    finally:
        try:
            rec["source_after"] = {p: sha(p) for p in rec["source_before"]}
            rec["source_unchanged"] = rec["source_after"] == rec["source_before"]
            _ = inputs(cfg)
            rec["inputs_unchanged"] = True
        except (OSError, ValueError, KeyError, TypeError) as exc:
            rec.update(status="stopped", inputs_unchanged=False, postcheck_error=repr(exc))
        persist()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("prepare", "execute"), default="prepare")
    args = parser.parse_args()
    cfg = yaml.safe_load(CONFIG.read_text())
    sys.path.insert(0, str(ROOT))
    if args.phase == "prepare":
        prepare(cfg)
    else:
        execute(cfg)


if __name__ == "__main__":
    main()
