"""Read-only one-step guide-event bound for the three saved calm-air cases."""
import hashlib
import json
import resource
import time
from pathlib import Path

resource.setrlimit(resource.RLIMIT_CPU, (10, 10))
start = time.process_time()
root = Path.cwd()
packet = root / 'runs/wo03-g80-guide-clock-bound-20261101-v1'
flight = root / 'runs/wo03-g80-canopy-stage3-20261101-v1/flight-result.json'
curve = root / 'configs/studies/rebaseline/motors/AeroTech_G80_2007_published.eng'
files = [flight, curve, root / 'src/sim/env.py', root / 'src/sim/dynamics.py', root / 'src/sim/inputs.py', Path(__file__)]
def hashes():
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
before = hashes()
points = []
for line in curve.read_text().splitlines():
    text = line.strip()
    if not text or text.startswith(';'):
        continue
    cols = text.split()
    if len(cols) == 2:
        points.append(tuple(map(float, cols)))
assert points and all(t >= 0 and f >= 0 for t, f in points)
peak = max(f for t, f in points)
rows = []
for r in json.loads(flight.read_text())['result']:
    c = r['case']
    if any(c.get(k, 0) != 0 for k in ('wind_north_mps', 'wind_east_mps', 'gust_amplitude_mps')):
        rows.append({'case': r['name'], 'status': 'unavailable_for_this_calm_air_bound'})
        continue
    m = r['metrics']
    lower_mass = m['effective_burnout_mass_kg']
    assert lower_mass > 0 and c['dt_s'] == 0.005 and c['thrust_scale'] > 0
    accel_upper = peak * c['thrust_scale'] / lower_mass + 9.80665
    allowance = c['dt_s'] * accel_upper
    lower_speed = m['guide_exit_mps'] - allowance
    rows.append({'case': r['name'], 'status': 'conditional_recorded_model_clock_bound',
        'source_curve_peak_n': peak, 'thrust_scale': c['thrust_scale'],
        'mass_lower_bound_kg': lower_mass, 'dt_s': c['dt_s'],
        'accel_upper_mps2': accel_upper, 'speed_allowance_mps': allowance,
        'recorded_guide_speed_mps': m['guide_exit_mps'],
        'conditional_guide_crossing_speed_lower_mps': lower_speed,
        'unchanged_target_mps': 15.0, 'conditional_screen_pass': lower_speed >= 15.0})
after = hashes()
assert before == after
record = {'status': 'completed_readonly_no_new_flight', 'source_before': before,
    'source_after': after, 'source_unchanged': True, 'cases': rows,
    'basis': 'For the saved fixed-motor zero-wind guide model, on-guide speed is axial and drag/friction oppose forward motion. Piecewise-linear thrust cannot exceed its endpoint maximum. Instantaneous mass is no smaller than effective full-depletion mass. Use Fmax/mmin + g, conservatively allowing gravity to aid acceleration. RK4 increments cannot exceed dt times this acceleration upper bound while the guide constraint applies. Exit is detected on the first step ending beyond the guide, so the clock offset is at most one dt. Subtract this speed bound without reconstructing an unsaved row.',
    'limitations': ['Conditional on existing rigid fixed-guide model and physical sign assumptions; no real guide qualification.', 'No reconstruction of missing telemetry or independent accuracy validation of integration/force/aerodynamic models.', 'Windy cases unavailable under this narrowly scoped calm-air proof.', 'Full trajectories, guide-row audit, manufacturing and site evidence remain unavailable.', 'Not a replacement for static/reference/uncertainty or recovery checks.'],
    'cpu_s': time.process_time() - start, 'solver_or_mesh_or_flight_invoked': False,
    'flight_ready': False}
(packet / 'record.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'peak_n': peak, 'cases': rows, 'cpu_s': record['cpu_s']}, indent=2))
