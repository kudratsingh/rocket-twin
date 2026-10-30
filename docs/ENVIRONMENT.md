# Environment spec

WO-01 local environment is runnable. Planned later stacks in the table below are
not yet resolved pins. `requirements-wo01.txt` pins the direct dependencies used
now: Python 3.11.16, NumPy 2.4.6, PyYAML 6.0.3, Pydantic 2.13.4, pytest 9.1.1,
ruff 0.16.3, black 26.5.1 and mypy 2.3.0. Python itself is installed separately.

Initial setup could not reach PyPI due to shell DNS restrictions. Local Python 3.11
packages were copied into this repository's `.venv` for checks; no packages in other
projects were changed. A complete `uv.lock` and a fresh-install verification remain
pending. Use `make setup` on a network-enabled machine for the minimal WO-01 setup;
use `make check smoke tiny` in the existing local environment. The owner subsequently
installed RocketPy 1.13.0 (`make setup-reference`), and the static reference comparison
has passed. SciPy resolved to 1.17.1. CAD, JAX, web and firmware remain untested;
later work orders resolve their pins. Matplotlib's cache is kept in ignored
`.cache/matplotlib/` by Make, avoiding writes outside the workspace.

## Pin table (agent fills exact values in WO-01/03/04 and records them here)

| Component | Pin | Why |
|---|---|---|
| Python | 3.11.x | CadQuery/OCP 8.x needs ≥ 3.11; JAX, RocketPy, cvxpy all fine on 3.11 |
| uv | record exact | Full lock pending network-enabled resolution |
| JAX / jaxlib | 0.4.x line (record exact); CPU on Mac, `jax[cuda12]` on the GPU box | Physics core + PPO (ADR-0001) |
| NumPy | 2.4.6 | RocketPy ≥ 1.4 supports NumPy 2 |
| RocketPy | 1.13.0 (installed and tested) | Reference for mass/CG/CP and unguided flight validation |
| CadQuery | latest release with OCP 7.9/8.x (record exact) | Parametric parts; `cadquery-ocp` wheel |
| trimesh | record exact | STL → GLB conversion for the viewer |
| pydantic | 2.13.4 | Vehicle spec schema and validation |
| cvxpy + Clarabel | record exact | G-FOLD convex solve (ADR-0004) |
| FastAPI + uvicorn | record exact | API |
| pyarrow | record exact | Parquet telemetry |
| Node | 22 LTS | Frontend |
| Vite / React / TypeScript | record exact | Frontend |
| three / @react-three/fiber / @react-three/drei | record exact | 3D viewer |
| uPlot | record exact | Telemetry plots (fast at 500 Hz × many channels) |
| zustand | record exact | Frontend state |
| PlatformIO | record exact | Firmware build (WO-10) |
| Teensyduino core | record exact | Teensy 4.1 target |
| Sensor libraries (ICM-42688 / BMI088, BMP390) | record exact | Firmware drivers |

Record resolved pins in `uv.lock`, `web/package-lock.json`, `firmware/platformio.ini` and in
this table.

## GPU tier (RunPod, Oct 2026 list price)

| Tier | Card | $/h | Used for |
|---|---|---|---|
| dev | RTX 4090 24 GB | 0.89 | WO-07/08 PPO training and 1,000-episode Monte-Carlo evals |

Presets map to tiers: `tiny` (CPU, any machine, < 2 min), `sim` (Mac CPU, single runs and
small batches), `rl` (dev GPU), `real` (Mac + flight computer over USB serial).

No other tier is expected. If a PPO run exceeds 30 minutes on a 4090, re-price and ask before
the second run.

## Install — Mac (CAD, API, frontend, firmware)

```zsh
brew install uv node@22 platformio
git clone <repo> && cd rocket-twin
uv sync --extra dev --extra cad
uv run python -c "import jax, rocketpy, cadquery; print(jax.__version__)"
uv run scripts/wo01_platform.py --preset tiny      # CPU smoke must pass before anything else
cd web && npm ci && npm run dev                   # http://localhost:5173
```

CadQuery on Apple Silicon: use the `cadquery-ocp` wheel from PyPI; if it fails, the fallback
is `conda-forge`, recorded as a blocker in STATUS.md, not silently switched.

## Install — GPU box (Linux, RL only)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
git clone <repo> && cd rocket-twin
uv sync --extra gpu                               # jax[cuda12], pyarrow, no cadquery
uv run python -c "import jax; print(jax.devices())"
uv run scripts/wo07_rl.py --preset tiny           # CPU smoke before any GPU time
```

## Hardware (ordered in WO-09; agent writes the BOM, owner buys)

- Flight computer: Teensy 4.1 (600 MHz Cortex-M7, FPU, microSD slot).
- IMU: ICM-42688-P or BMI088 breakout (SPI). Barometer: BMP390 (SPI or I²C).
- Servos: two metal-gear micro servos with published stall torque and speed (e.g. MG90S class
  or better); the spec records torque, speed, deadband, supply voltage.
- Power: 2S LiPo 300–500 mAh, 5 V regulator for servos, arming switch, buzzer, status LEDs.
- Recovery: independent electronic recovery for every mode, especially plugged G12ST-P;
  controller pyro channel is reserved. Exact controller, power isolation, deployment
  hardware and ground tests are WO-09/10 release gates.
- Airframe: preliminary 66 mm hybrid kraft/plywood/printed ASA platform, custom
  keyed coupler and interchangeable fixed/finned-TVC/finless-TVC aft modules.
  Every cut, bonded, printed and purchased part has its own spec/inventory entry.
- Motors: preliminary G80-10T SU performance and reformulated G12ST-P DMS TVC
  families; 29 mm nominal bore retained by trade, not fixed requirement. Exact
  source/variant/California and delay verification remain open; F15 is historical.
- Ground: launch pad with rail/rod, electrical launch controller with interlock, test stand
  (optional) for TVC range tests.

## Data locations

| What | Where |
|---|---|
| Mode specs/common assembly | `configs/vehicle/platform/`, `configs/platform.yaml` (git) |
| Motor curves and source sidecars | `configs/vehicle/motors/`, `configs/studies/` (git) |
| Generated meshes | `build/` (ignored; `make cad` regenerates) |
| Sim runs | `runs/<id>/` (record.json committed; telemetry.parquet ignored) |
| RL checkpoints | HF Hub private model repo `KudratSingh22/rocket-twin-policies` |
| Flight logs | `data/flights/` on the owner's Mac; private HF dataset `KudratSingh22/rocket-twin-flights` |

## Known time sinks (avoid)

- CadQuery/OCP install problems on macOS — use the PyPI wheel first; record the exact wheel.
- Frame and sign conventions — one `frames.py`, imported everywhere; a wrong sign in the TVC
  moment arm shows up as a controller that "works" with inverted gains. The WO-02 validation
  must include a known-answer test for a gimbal deflection producing the expected pitch moment.
- Re-implementing physics in TypeScript "just for preview" — forbidden by rule 2.
- Unbounded frontend scope — `docs/UI.md` is the contract.
- Servo models that ignore latency and rate limits — they make RL look better than reality.
- PPO reward shaping toward a sim artefact (e.g. rewarding zero gimbal motion) — check the
  policy's gimbal traces, not just the return.

## Rebaselined WO-01 commands

`make tiny` resolves all three modes and writes complete spec/inventory previews.
`make benchmark` adds independent RocketPy comparisons and enforces preliminary
model gates. `scripts/wo01_vehicle.py` and the old motor-study targets preserve the
historical F15/three-second/TWR-3 studies; their selection gates are not the active
platform benchmark. No dependency upgrade or new paid environment is implied.
