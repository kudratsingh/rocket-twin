"""One bounded saved-run read; independent scalar quaternion and matrix reference."""

import bisect
import hashlib
import json
import math
import os
import signal
import time
from pathlib import Path

os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["ARROW_NUM_THREADS"] = "1"
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "runs/exp-cf9e47a650074144856caf50775846d2"
OUT = ROOT / "docs/studies/replay-pose-20261107/reference.json"
signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("60 s wall limit")))
signal.alarm(60)
start, cpu = time.monotonic(), time.process_time()
pa.set_cpu_count(1)
pa.set_io_thread_count(1)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def normal(q):
    length = math.sqrt(sum(x * x for x in q))
    if not math.isfinite(length) or length == 0:
        raise ValueError("Invalid quaternion")
    return [x / length for x in q]


def slerp(a, b, f):
    a, b = normal(a), normal(b)
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0:
        b = [-x for x in b]
        dot = -dot
    dot = min(1.0, max(-1.0, dot))
    if dot > 0.9995:
        return normal([x + (y - x) * f for x, y in zip(a, b)])
    angle = math.acos(dot)
    scale = math.sin(angle)
    return [(math.sin((1 - f) * angle) * x + math.sin(f * angle) * y) / scale for x, y in zip(a, b)]


def matrix(q):
    w, x, y, z = q
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]


def mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


record = json.loads((RUN / "record.json").read_text())
resolved = json.loads((RUN / "resolved.json").read_text())
assert (
    record["run_id"] == "exp-cf9e47a650074144856caf50775846d2"
    and record["configuration"] == "modular-performance-v1"
)
cols = [
    "time_s",
    "north_m",
    "east_m",
    "down_m",
    "qw",
    "qx",
    "qy",
    "qz",
    "cg_station_m",
    "vn_mps",
    "ve_mps",
    "vd_mps",
]
table = pq.read_table(RUN / "telemetry.parquet", columns=cols, use_threads=False)
data = table.to_pydict()
times = data["time_s"]
n = len(times)
assert n == record["telemetry_samples"] and all(times[i] < times[i + 1] for i in range(n - 1))
indices = set(np.linspace(0, n - 1, min(n, 3000), dtype=int).tolist())
for event in record["events"].values():
    if event is not None:
        i = bisect.bisect_left(times, event)
        indices.update(max(0, min(n - 1, j)) for j in (i - 1, i))
indices = sorted(indices)
sampled = [times[i] for i in indices]
length = resolved["airframe"]["length_m"]
body = [[0, 1, 0], [1, 0, 0], [0, 0, -1]]
scene = [[0, 1, 0], [0, 0, -1], [-1, 0, 0]]


def sample(i):
    return {k: data[k][i] for k in cols}


def reference(t):
    hi = bisect.bisect_left(sampled, t)
    hi = min(hi, len(indices) - 1)
    if hi == 0 or sampled[hi] == t:
        lo = hi
        f = 0.0
    else:
        lo = hi - 1
        f = (t - sampled[lo]) / (sampled[hi] - sampled[lo])
    i, j = indices[lo], indices[hi]
    left, right = sample(i), sample(j)

    def interp(k):
        return left[k] * (1 - f) + right[k] * f

    q = slerp(
        [left[k] for k in ("qw", "qx", "qy", "qz")], [right[k] for k in ("qw", "qx", "qy", "qz")], f
    )
    rot = mul(mul(scene, matrix(q)), body)
    cg = interp("cg_station_m")
    return {
        "requested_time_s": t,
        "raw_indices": [i, j],
        "samples": [left, right],
        "fraction": f,
        "expected": {
            "position_scene_m": [interp("east_m"), -interp("down_m"), -interp("north_m")],
            "body_to_ned_wxyz": q,
            "cad_to_scene_matrix": rot,
            "pivot_cad_m": [0, -(length - cg), 0],
            "nose_scene": [rot[0][1], rot[1][1], rot[2][1]],
        },
    }


targets = {"descent": 11.15}
for name, t in record["events"].items():
    if t is not None and sampled[0] <= t <= sampled[-1]:
        targets[name] = t
cases = {name: reference(t) for name, t in targets.items()}
i = bisect.bisect_left(times, 11.15)
nearest = min((max(0, i - 1), min(n - 1, i)), key=lambda k: abs(times[k] - 11.15))
result = {
    "run_id": record["run_id"],
    "configuration": record["configuration"],
    "identity": {k: record[k] for k in ("resolved_sha256", "cad_revision_sha256", "code_sha256")},
    "artifact_sha256": {
        str(p.relative_to(ROOT)): digest(p)
        for p in [RUN / "record.json", RUN / "resolved.json", RUN / "telemetry.parquet"]
    },
    "source": "One read of selected columns from saved raw Parquet; API-like uniform and event-adjacent selection. Independent scalar quaternion/rotation calculations; no simulation, Three, browser or rendering.",
    "full_count": n,
    "playback_count": len(indices),
    "support_s": [sampled[0], sampled[-1]],
    "length_m": length,
    "events": record["events"],
    "raw_nearest_11_15": sample(nearest),
    "cases": cases,
    "timing": {
        "wall_seconds": time.monotonic() - start,
        "cpu_seconds": time.process_time() - cpu,
        "wall_limit_seconds": 60,
        "cpu_limit_seconds": 30,
    },
}
if result["timing"]["wall_seconds"] > 60 or result["timing"]["cpu_seconds"] > 30:
    raise TimeoutError("Resource budget exceeded")
OUT.write_text(json.dumps(result, indent=2) + "\n")
signal.alarm(0)
print(
    json.dumps(
        {
            "timing": result["timing"],
            "samples": n,
            "playback_samples": len(indices),
            "cases": list(cases),
            "hashes": result["artifact_sha256"],
        }
    )
)
