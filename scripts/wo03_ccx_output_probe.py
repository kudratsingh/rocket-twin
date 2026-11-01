"""One declared, output-only CalculiX diagnostic on the retained A decks.

The only input edit is a *NODE OUTPUT request for NT and RFL. No mesh,
boundary, material, or numerical method is generated or changed here.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import resource
import struct
import subprocess
import time
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "configs/studies/wo03-ccx-output-probe.yaml"
SOURCE_CONFIG = ROOT / "configs/studies/wo03-thermal-error-isolation.yaml"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_nodes(inp: str) -> dict[int, tuple[float, float, float]]:
    lines = inp.splitlines()
    start = next((i for i, line in enumerate(lines) if line.upper().startswith("*NODE")), None)
    if start is None:
        raise ValueError("Input has no node block")
    nodes: dict[int, tuple[float, float, float]] = {}
    for line in lines[start + 1 :]:
        if line.startswith("*"):
            break
        if not line.strip():
            continue
        fields = [part.strip() for part in line.split(",")]
        if len(fields) < 4:
            raise ValueError("Malformed node record in retained deck")
        nodes[int(fields[0])] = (float(fields[1]), float(fields[2]), float(fields[3]))
    if not nodes:
        raise ValueError("Empty node block")
    return nodes


def add_output_request(original: str) -> str:
    endings = [
        i for i, line in enumerate(original.splitlines()) if line.strip().upper() == "*END STEP"
    ]
    if len(endings) != 1:
        raise ValueError("Expected one *END STEP in retained A input")
    lines = original.splitlines()
    idx = endings[0]
    if any(line.strip().upper().startswith("*NODE OUTPUT") for line in lines):
        raise ValueError("Retained source already has NODE OUTPUT; refusing to alter it")
    lines[idx:idx] = ["*NODE OUTPUT", "NT,RFL"]
    return "\n".join(lines) + "\n"


def parse_dat_temperatures(text: str) -> dict[int, float]:
    parts = text.lower().split("temperatures", 1)
    if len(parts) != 2:
        raise ValueError("No DAT temperatures block")
    values: dict[int, float] = {}
    for line in parts[1].splitlines()[1:]:
        fields = line.split()
        if len(fields) == 2 and fields[0].isdigit():
            values[int(fields[0])] = float(fields[1])
        elif values:
            break
    if not values:
        raise ValueError("DAT temperatures block has no values")
    return values


def parse_binary_scalar_field(frd: bytes, field: bytes, node_ids: list[int]) -> dict[int, float]:
    """Decode a scalar mixed-FRD field after checking framing and all node IDs.

    Mapping follows upstream frdselect.c: 4-byte integer node ID followed by
    one 4-byte float per scalar node. Binary frdselect records have no ASCII
    -3 field terminator; fixed node count determines the next record boundary.
    Fail closed unless the component header, every node ID, and following
    structural marker agree with the observed CalculiX 2.23 file.
    """
    marker = re.compile(rb"(?m)^[ \t]*-4[ \t]+" + re.escape(field) + rb"[ \t]+[^\n]*\n")
    matches = list(marker.finditer(frd))
    if len(matches) != 1:
        raise ValueError(f"Expected one FRD {field.decode()} field header, got {len(matches)}")
    pos = matches[0].end()
    if pos < 2:
        raise ValueError("Truncated FRD field header")
    metadata_end = frd.find(b"\n", pos)
    if metadata_end < 0:
        raise ValueError("Truncated FRD component header")
    component = frd[pos:metadata_end]
    parts = component.split()
    expected_component = b"T" if field == b"NDTEMP" else field
    if len(parts) < 2 or parts[0] != b"-5" or parts[1] != expected_component:
        raise ValueError("Unexpected FRD component header")
    start = metadata_end + 1
    end = start + 8 * len(node_ids)
    if end > len(frd):
        raise ValueError("Truncated binary FRD scalar records")
    following = frd[end : end + 32]
    # These exact fixed-column prefixes are observed in the pinned 2.23 file.
    # Accepting arbitrary whitespace here could hide a truncated binary value
    # by consuming a byte from the following ASCII header.
    if field == b"NDTEMP":
        if not re.match(rb"    1PSTEP\b", following):
            raise ValueError(f"Unexpected bytes after NT records: {following!r}")
    elif field == b"RFL" and not following.startswith(b" 9999\n"):
        raise ValueError(f"Unexpected bytes after RFL records: {following!r}")
    result: dict[int, float] = {}
    for i, expected_id in enumerate(node_ids):
        node, value = struct.unpack_from("<if", frd, start + i * 8)
        if node != expected_id or not math.isfinite(value):
            raise ValueError(
                f"Unexpected binary field record at index {i}: id={node}, value={value}"
            )
        result[node] = value
    return result


def parse_dat_rfl(text: str) -> tuple[dict[int, float], float]:
    lower = text.lower()
    key = "heat generation for set hot"
    if key not in lower:
        raise ValueError("No DAT hot-set RFL block")
    block = text[lower.index(key) + len(key) :]
    values: dict[int, float] = {}
    for line in block.splitlines()[1:]:
        fields = line.split()
        if len(fields) == 2 and fields[0].isdigit():
            values[int(fields[0])] = float(fields[1])
        elif values:
            break
    total_key = "total heat generation for set hot"
    if total_key not in lower:
        raise ValueError("No DAT hot-set RFL total")
    total_block = text[lower.index(total_key) + len(total_key) :]
    total = next(
        (float(line.split()[0]) for line in total_block.splitlines()[1:] if line.split()), None
    )
    if not values or total is None:
        raise ValueError("Incomplete DAT hot-set RFL block")
    return values, total


def exact_temperature(x: float, cfg: dict) -> float:
    a = cfg["case_a"]
    dx, _width, _length = cfg["dimensions_m"]
    k = cfg["conductivity_w_m_k"]
    q = (a["hot_prescribed_k"] - a["cold_bulk_k"]) / (dx / k + 1.0 / a["h_w_m2_k"])
    return a["hot_prescribed_k"] - q * x / k


def float32_spacing(value: float) -> float:
    """ULP for a positive finite binary32 value, using adjacent IEEE bits."""
    bits = int.from_bytes(struct.pack("<f", value), "little")
    here = struct.unpack("<f", bits.to_bytes(4, "little"))[0]
    following = struct.unpack("<f", (bits + 1).to_bytes(4, "little"))[0]
    return following - here


def run(outdir: Path) -> None:
    if outdir.exists():
        raise FileExistsError(f"Fresh output path required: {outdir}")
    outdir.mkdir(parents=True, exist_ok=False)
    setup_start = time.monotonic()
    proc_cpu_total = 0.0
    env = os.environ.copy()
    for key in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "BLIS_NUM_THREADS",
        "CCX_NPROC_EQUATION_SOLVER",
        "CCX_NPROC_RESULTS",
        "CCX_NPROC_CFD",
    ):
        env[key] = "1"
    cfg = yaml.safe_load(CONFIG.read_text())
    source_cfg = yaml.safe_load(SOURCE_CONFIG.read_text())
    binary = Path(cfg["binary"])
    records: dict = {
        "packet": cfg["id"],
        "config_sha256": sha256(CONFIG),
        "binary_path": str(binary),
        "binary_realpath": str(binary.resolve()),
        "binary_sha256": sha256(binary),
        "threads_requested": 1,
        "environment_threads": {
            key: env[key]
            for key in (
                "OMP_NUM_THREADS",
                "OPENBLAS_NUM_THREADS",
                "MKL_NUM_THREADS",
                "VECLIB_MAXIMUM_THREADS",
                "BLIS_NUM_THREADS",
                "CCX_NPROC_EQUATION_SOLVER",
                "CCX_NPROC_RESULTS",
                "CCX_NPROC_CFD",
            )
        },
        "case_wall_limit_seconds_all_grids": cfg["limits"]["case_wall_seconds_all_grids"],
        "packet_cpu_limit_seconds": cfg["limits"]["packet_cpu_seconds"],
        "grids": [],
        "status": "preflight",
    }
    record_path = outdir / "record.json"
    try:
        if records["binary_sha256"] != cfg["binary_sha256"]:
            raise ValueError("Installed CalculiX hash differs from declared packet")
        original_sources: dict[str, str] = {}
        for item in cfg["grids"]:
            src = ROOT / item["input"]
            actual = sha256(src)
            if actual != item["input_sha256"]:
                raise ValueError(f"Retained source hash mismatch: {item['input']}")
            original_sources[str(src.relative_to(ROOT))] = actual
        records["source_inputs"] = original_sources
        records["source_config_sha256"] = sha256(SOURCE_CONFIG)
        records["setup_wall_seconds"] = time.monotonic() - setup_start
        if records["setup_wall_seconds"] > 120:
            raise TimeoutError("Declared setup wall limit reached before solve")
        case_start = time.monotonic()
        records["status"] = "running"
        record_path.write_text(json.dumps(records, indent=2) + "\n")
        for item in cfg["grids"]:
            elapsed = time.monotonic() - case_start
            remaining = cfg["limits"]["case_wall_seconds_all_grids"] - elapsed
            if remaining <= 0 or proc_cpu_total >= cfg["limits"]["packet_cpu_seconds"]:
                raise TimeoutError("Declared A-case or packet limit reached; no retry")
            src = ROOT / item["input"]
            original = src.read_text()
            nodes = parse_nodes(original)
            expected_node_count = (int(item["divisions"]) + 1) ** 3
            if len(nodes) != expected_node_count or list(nodes) != list(
                range(1, expected_node_count + 1)
            ):
                raise ValueError(
                    "Retained deck node topology is not the expected structured A grid"
                )
            folder = outdir / f"A-{item['divisions']}"
            folder.mkdir()
            modified = add_output_request(original)
            inp = folder / "case.inp"
            inp.write_text(modified)
            check = modified.replace("*NODE OUTPUT\nNT,RFL\n", "", 1)
            if check != original:
                raise ValueError("Input edit exceeded the output-only card insertion")
            (folder / "source_input.sha256").write_text(
                item["input_sha256"] + "  " + item["input"] + "\n"
            )
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            begin = time.monotonic()
            proc = subprocess.run(
                [str(binary), "-i", "case"],
                cwd=folder,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                timeout=remaining,
                check=False,
            )
            usage = resource.getrusage(resource.RUSAGE_CHILDREN)
            cpu = (usage.ru_utime + usage.ru_stime) - (before.ru_utime + before.ru_stime)
            proc_cpu_total += cpu
            wall = time.monotonic() - begin
            (folder / "stdout.txt").write_text(proc.stdout)
            row = {
                "divisions": item["divisions"],
                "source_input": item["input"],
                "source_input_sha256": item["input_sha256"],
                "probe_input_sha256": sha256(inp),
                "returncode": proc.returncode,
                "wall_seconds": wall,
                "child_cpu_seconds": cpu,
                "child_peak_rss_bytes_cumulative_max": usage.ru_maxrss,
                "completed_marker": "Job finished" in proc.stdout,
                "status": (
                    "solved"
                    if proc.returncode == 0 and "Job finished" in proc.stdout
                    else "invalid_solve"
                ),
            }
            records["grids"].append(row)
            record_path.write_text(json.dumps(records, indent=2) + "\n")
            if row["status"] != "solved":
                raise RuntimeError("Invalid solve; preserve outputs and stop without retry")
            frd_path = folder / "case.frd"
            frd = frd_path.read_bytes()
            ids = list(nodes)
            fields = {
                name: parse_binary_scalar_field(frd, field, ids)
                for name, field in (("NT", b"NDTEMP"), ("RFL", b"RFL"))
            }
            dat_t = parse_dat_temperatures((folder / "case.dat").read_text())
            if set(dat_t) != set(ids):
                raise ValueError("DAT field node IDs differ from retained source nodes")
            nt = fields["NT"]
            exact = {
                node_id: exact_temperature(xyz[0], source_cfg) for node_id, xyz in nodes.items()
            }
            errors = [abs(nt[node_id] - exact[node_id]) for node_id in ids]
            max_pair = max(abs(nt[node_id] - dat_t[node_id]) for node_id in ids)
            vals = list(nt.values())
            row.update(
                {
                    "node_count": len(nodes),
                    "frd_size_bytes": len(frd),
                    "frd_field_record_mapping": "4-byte LE node ID + 4-byte LE float32 value, fixed node count, followed by ASCII ` -3\\n`; NT and RFL component headers verified",
                    "nt_min_k": min(vals),
                    "nt_max_k": max(vals),
                    "nt_max_abs_error_from_exact_a_k": max(errors),
                    "nt_max_abs_difference_from_dat_print_k": max_pair,
                    "nt_float32_spacing_min_k": min(float32_spacing(v) for v in vals),
                    "nt_float32_spacing_max_k": max(float32_spacing(v) for v in vals),
                    "raw_output_meets_1e-7_k": max(errors) <= 1e-7,
                    "rfl_min": min(fields["RFL"].values()),
                    "rfl_max": max(fields["RFL"].values()),
                    "rfl_semantics": "manual: external concentrated heat sources; not a film-integrated heat total",
                }
            )
            records["status"] = "running"
            record_path.write_text(json.dumps(records, indent=2) + "\n")
            if proc_cpu_total > cfg["limits"]["packet_cpu_seconds"]:
                raise TimeoutError("CPU limit exceeded; no retry")
        records["status"] = "complete_diagnostic_not_qualification"
    except BaseException as exc:
        records["status"] = "incomplete_preserved"
        records["stop_reason"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        records["setup_wall_seconds"] = records.get(
            "setup_wall_seconds", time.monotonic() - setup_start
        )
        records["case_wall_seconds_all_grids"] = time.monotonic() - locals().get(
            "case_start", setup_start
        )
        records["packet_child_cpu_seconds"] = proc_cpu_total
        records["setup_wall_limit_seconds"] = 120
        records["setup_included_in_case_wall"] = False
        records["source_inputs_unchanged_after"] = {
            rel: (ROOT / rel).exists() and sha256(ROOT / rel) == expected
            for rel, expected in records.get("source_inputs", {}).items()
        }
        record_path.write_text(json.dumps(records, indent=2) + "\n")


def decode_preserved(outdir: Path) -> None:
    """Read the preserved A-2 artifacts only; never invoke CalculiX."""
    record_path = outdir / "record.json"
    original_record = json.loads(record_path.read_text())
    if (
        original_record.get("status") != "incomplete_preserved"
        or len(original_record.get("grids", [])) != 1
    ):
        raise ValueError(
            "Read-only decode is limited to the single preserved A-2 diagnostic result"
        )
    cfg = yaml.safe_load(CONFIG.read_text())
    source_cfg = yaml.safe_load(SOURCE_CONFIG.read_text())
    item = cfg["grids"][0]
    source = ROOT / item["input"]
    if sha256(source) != item["input_sha256"]:
        raise ValueError("A-2 retained source changed since run")
    folder = outdir / "A-2"
    input_text = source.read_text()
    nodes = parse_nodes(input_text)
    frd = (folder / "case.frd").read_bytes()
    ids = list(nodes)
    nt = parse_binary_scalar_field(frd, b"NDTEMP", ids)
    rfl = parse_binary_scalar_field(frd, b"RFL", ids)
    dat = (folder / "case.dat").read_text()
    dat_nt = parse_dat_temperatures(dat)
    dat_rfl, dat_rfl_total = parse_dat_rfl(dat)
    exact = {node_id: exact_temperature(xyz[0], source_cfg) for node_id, xyz in nodes.items()}
    nt_values = list(nt.values())
    hot_ids = [node_id for node_id, xyz in nodes.items() if xyz[0] == 0.0]
    observed = {
        "source_packet_record_sha256_before_decode": sha256(record_path),
        "probe_config_sha256": sha256(CONFIG),
        "source_config_sha256": sha256(SOURCE_CONFIG),
        "binary_sha256": original_record["binary_sha256"],
        "as_run_manifest": json.loads((outdir / "as-run-manifest.json").read_text()),
        "preserved_run_record_status": original_record["status"],
        "preserved_run_stop_reason": original_record.get("stop_reason"),
        "solver_returncode": original_record["grids"][0]["returncode"],
        "solver_wall_seconds": original_record["grids"][0]["wall_seconds"],
        "solver_child_cpu_seconds": original_record["grids"][0]["child_cpu_seconds"],
        "solver_child_peak_rss_bytes_cumulative_max": original_record["grids"][0][
            "child_peak_rss_bytes_cumulative_max"
        ],
        "packet_wall_seconds_at_parser_stop": original_record["case_wall_seconds_all_grids"],
        "packet_child_cpu_seconds_at_parser_stop": original_record["packet_child_cpu_seconds"],
        "setup_wall_seconds": original_record["setup_wall_seconds"],
        "raw_frd_sha256": sha256(folder / "case.frd"),
        "probe_input_sha256": sha256(folder / "case.inp"),
        "source_input_sha256_after": sha256(source),
        "divisions": 2,
        "node_count": len(nodes),
        "frd_header_lines": [
            " -4  NDTEMP 1 1",
            " -5  T 1 1 0 0",
            " -4  RFL 1 1",
            " -5  RFL 1 1 0 0",
        ],
        "frd_record_layout": "source-based four-byte native int node IDs followed by four-byte native float32 scalar values; fixed all-node count; NT block followed by ASCII 1PSTEP header and RFL block followed by ASCII 9999 file footer",
        "field_framing_checks": "all node IDs decoded in order 1..27; component labels and following structural headers matched",
        "nt_min_k": min(nt_values),
        "nt_max_k": max(nt_values),
        "nt_max_abs_error_from_exact_a_k": max(
            abs(nt[node_id] - exact[node_id]) for node_id in ids
        ),
        "nt_max_abs_difference_from_dat_print_k": max(
            abs(nt[node_id] - dat_nt[node_id]) for node_id in ids
        ),
        "nt_float32_spacing_min_k": min(float32_spacing(v) for v in nt_values),
        "nt_float32_spacing_max_k": max(float32_spacing(v) for v in nt_values),
        "unchanged_1e-7_k_field_check": "not demonstrated by this float32 field encoding; no tolerance was relaxed",
        "rfl_min": min(rfl.values()),
        "rfl_max": max(rfl.values()),
        "rfl_hot_sum": sum(rfl[node_id] for node_id in hot_ids),
        "rfl_hot_node_float32_spacing_min_w": min(
            float32_spacing(abs(rfl[node_id])) for node_id in hot_ids
        ),
        "rfl_hot_node_float32_spacing_max_w": max(
            float32_spacing(abs(rfl[node_id])) for node_id in hot_ids
        ),
        "rfl_hot_sum_dat_total": dat_rfl_total,
        "rfl_hot_node_max_difference_from_dat": max(
            abs(rfl[node_id] - dat_rfl[node_id]) for node_id in hot_ids
        ),
        "rfl_semantics": "manual identifies external concentrated heat sources; the output does not by itself establish integrated *FILM heat",
        "grid_4_and_8": "not run: preserved A-2 parser-format stop rule; no reruns or additional grids",
        "packet_status": "partial_diagnostic; three-grid packet incomplete; solver acceptance not established",
    }
    decode_path = outdir / "read-only-decode.json"
    decode_path.write_text(json.dumps(observed, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build/wo03-ccx-output-probe-v1")
    parser.add_argument("--decode-preserved-only", action="store_true")
    args = parser.parse_args()
    outdir = Path(args.output)
    if not outdir.is_absolute():
        outdir = ROOT / outdir
    if args.decode_preserved_only:
        decode_preserved(outdir)
    else:
        run(outdir)


if __name__ == "__main__":
    main()
