#!/usr/bin/env python3
"""Read one existing trajectory; calculate four raw-sample axis/velocity comparisons."""
import hashlib
import json
import math
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
RUN = ROOT / 'runs/exp-cf9e47a650074144856caf50775846d2'
OUTPUT = Path(__file__).with_name('record.json')
TARGETS = (0.17, 10.395, 11.15, 116.029)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def current_code_digest():
    h = hashlib.sha256()
    for folder in ('src/sim', 'src/vehicle', 'src/cad'):
        for path in sorted((ROOT / folder).glob('*.py')):
            h.update(path.read_bytes())
    h.update((ROOT / 'scripts/wo02_sim.py').read_bytes())
    return h.hexdigest()


def angle(a, b):
    norm = math.sqrt(sum(x*x for x in a) * sum(x*x for x in b))
    if norm == 0:
        return None
    return math.degrees(math.acos(max(-1, min(1, sum(x*y for x, y in zip(a, b)) / norm))))


def main():
    files = [RUN / x for x in ('record.json', 'resolved.json', 'telemetry.parquet')]
    for path in files:
        if not path.is_file():
            raise FileNotFoundError(path)
    record = json.loads(files[0].read_text())
    cols = ['time_s', 'down_m', 'vn_mps', 've_mps', 'vd_mps', 'qw', 'qx', 'qy', 'qz', 'landed']
    table = pq.read_table(files[2], columns=cols).to_pydict()
    times = table['time_s']
    samples = []
    for target in TARGETS:
        i = min(range(len(times)), key=lambda j: abs(times[j] - target))
        w, x, y, z = (table[key][i] for key in ('qw', 'qx', 'qy', 'qz'))
        norm = math.sqrt(w*w + x*x + y*y + z*z)
        if not math.isfinite(norm) or norm == 0:
            raise ValueError(f'invalid quaternion at sample {i}')
        w, x, y, z = (v / norm for v in (w, x, y, z))
        # First column of the scalar-first body-to-NED rotation matrix: body +x.
        nose = [1 - 2*(y*y + z*z), 2*(x*y + w*z), 2*(x*z - w*y)]
        velocity = [table[k][i] for k in ('vn_mps', 've_mps', 'vd_mps')]
        samples.append({'target_s': target, 'row_index_zero_based': i, 'recorded_time_s': times[i],
                        'height_agl_m': -table['down_m'][i], 'velocity_ned_mps': velocity,
                        'recorded_quaternion_wxyz': [table[k][i] for k in ('qw','qx','qy','qz')],
                        'nose_axis_ned': nose, 'nose_to_velocity_deg': angle(nose, velocity),
                        'nose_from_up_deg': angle(nose, [0, 0, -1]), 'landed': table['landed'][i]})
    result = {'schema_version': 1, 'method': 'One existing Parquet; nearest raw rows, normalized recorded quaternion and body +x rotated into NED; no rollout or resampling.',
              'run_id': record['run_id'], 'configuration': record['configuration'], 'controller': record['controller'],
              'flight_ready': record['flight_ready'], 'trajectory_complete': record['trajectory_complete'],
              'telemetry_rows': len(times), 'events_s': record['events'],
              'artifact_sha256': {str(p.relative_to(ROOT)): digest(p) for p in files},
              'source_sha256': {p: digest(ROOT / p) for p in ('src/sim/frames.py','src/sim/dynamics.py','scripts/wo02_sim.py')},
              'saved_code_sha256': record['code_sha256'], 'current_code_digest_sha256': current_code_digest(),
              'resolved_spec_sha256': record['resolved_sha256'], 'cad_revision_sha256': record['cad_revision_sha256'],
              'samples': samples}
    OUTPUT.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
