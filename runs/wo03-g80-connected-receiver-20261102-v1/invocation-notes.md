# Preserved v1 invocation notes

- Initial system `python3` invocation stopped before the script entered `main`: NumPy was unavailable. No run artifacts were created by that invocation.
- The project `.venv/bin/python` invocation entered `main` and stopped at the recorded `KeyError: 'ring_outer_inner_radius_mm'` in the first body-area diagnostic. The original v1 record, executed config, executed script, and manifest are preserved unchanged.
- The owner authorized one targeted input-wiring correction and one retry in a new v2 run folder. v1 has no available CPU timing for its failed attempt; the shell wall time was 0.532 seconds.
