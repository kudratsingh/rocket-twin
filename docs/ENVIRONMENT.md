# Environment spec

Verified local Apple Silicon environment (2026-10-30): Python 3.11.16, uv 0.12.17,
NumPy 2.4.6, PyYAML 6.0.3, Pydantic 2.13.4, pytest 9.1.1, Ruff 0.16.3,
Black 26.5.1, mypy 2.3.0, JAX/jaxlib 0.4.38, RocketPy 1.13.0, SciPy 1.17.1,
PyArrow 23.0.1, CadQuery 2.8.0/cadquery-ocp 7.9.3.1.1, trimesh 4.11.5,
Gmsh 4.15.2, FastAPI 0.162.0, uvicorn 0.41.0, httpx 0.28.1 and Matplotlib
3.11.2. CalculiX `ccx` 2.23 is installed and was executed in recorded WO-03 runs.
The `cairosvg` Python package is absent; the service diagram generator uses Pillow
for PNG and also emits source SVG. These are installed-environment facts, not a
claim that every dependency is reproducibly locked; a complete `uv.lock` and fresh
Mac/full-stack install verification remain pending.

Initial setup could not reach PyPI due to shell DNS restrictions. Local Python 3.11
packages were copied into this repository's `.venv` for checks; no packages in other
projects were changed. A complete `uv.lock` and fresh Mac/full-stack install
verification remain pending. The private GitHub CPU workflow now installs the
WO-01 pins plus RocketPy 1.13.0/SciPy 1.17.1 on a clean Linux runner; its hosted
check results are linked from PR #1. Use `make setup` on a network-enabled machine for the minimal WO-01 setup;
use `make check smoke tiny` in the existing local environment. The owner subsequently
installed RocketPy 1.13.0 (`make setup-reference`), and the static reference comparison
has passed. SciPy resolved to 1.17.1. JAX is CPU-tested in WO-02; CadQuery/CAD and
the local FastAPI stack are installed and exercised for WO-03. Web runtime/build
and firmware toolchain remain unverified; later work orders resolve their pins.
Matplotlib's cache is kept in ignored
`.cache/matplotlib/` by Make, avoiding writes outside the workspace.

## Pin table (installed versions verified 2026-10-30; other stacks remain pending)

| Component | Verified pin / state | Why |
|---|---|---|
| Python | 3.11.x | CadQuery/OCP 8.x needs ≥ 3.11; JAX, RocketPy, cvxpy all fine on 3.11 |
| uv | 0.12.17 (Homebrew, arm64) | Environment and dependency management |
| JAX / jaxlib | 0.4.38 / 0.4.38; CPU tested; GPU only on approved runs | Physics core + PPO (ADR-0001) |
| NumPy | 2.4.6 | RocketPy ≥ 1.4 supports NumPy 2 |
| RocketPy | 1.13.0 (installed and tested) | Reference for mass/CG/CP and unguided flight validation |
| CadQuery / cadquery-ocp | 2.8.0 / 7.9.3.1.1 | Parametric parts; STEP/STL/GLB exports |
| trimesh | 4.11.5 | Mesh processing and GLB conversion |
| pydantic | 2.13.4 | Vehicle spec schema and validation |
| cvxpy + Clarabel | not installed/pinned | G-FOLD convex solve (ADR-0004) |
| FastAPI + uvicorn | 0.162.0 / 0.41.0 (installed) | API |
| pyarrow | 23.0.1 | Parquet telemetry |
| Node | 22 LTS | Frontend |
| Vite / React / TypeScript | see `web/package-lock.json`; not Python packages | Frontend |
| three / @react-three/fiber / @react-three/drei | record exact | 3D viewer |
| uPlot | record exact | Telemetry plots (fast at 500 Hz × many channels) |
| zustand | record exact | Frontend state |
| PlatformIO / Teensyduino / sensor libraries | not installed/pinned in Python env | Firmware build (WO-10) |

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

## WO-02 CPU environment

`make setup-sim` installs `requirements-wo02.txt`: JAX/jaxlib 0.4.38 (the planned
0.4 line), PyArrow 23.0.1, existing RocketPy/SciPy pins and WO-01 requirements.
Physics comparison uses float64; embedded policies remain float32. No GPU or paid
run is needed. Host PyPI DNS is restricted; the owner was given the terminal install
command and installed it successfully. Local arm64 CPU validation passes: 65 tests,
actual-mode flight benchmarks and a 4,096-env step. Hosted CI installs the same pins
on clean Linux. Full project lock/CAD/web stacks remain separate.

## WO-03 engineering expansion (ADR-0007)

Gmsh 4.15.2 and CalculiX 2.23 are now installed and actually executed in local
WO-03 runs. `runs/wo03-vibration-20261030T174152408940Z/record.json` records
analytical fixtures, mesh levels, solver version, reactions/equilibrium and a
three-level fin-shell convergence check. These verify solver operation and those
calculations only; they do not qualify rocket materials or attachment/load paths.
SciPy 1.17.1/NumPy 2.4.6 support hand and transient-model calculations. Keep display
tessellation separate from analysis discretization; record solver, mesh, material
and input identities. No paid compute or OpenFOAM was used.

## WO-03 execution host, verified 2026-10-30

Installed versions: Gmsh 4.15.2; CalculiX `ccx` 2.23 at `/opt/homebrew/bin/ccx`;
CadQuery 2.8.0; cadquery-ocp 7.9.3.1.1; trimesh 4.11.5. The axial-bar known case
matches expected displacement/stress to about 2.5e-7 relative and balances support
reactions within 6e-9 N. A fin-shell model run at 10/7/5 mm mesh targets changed
0.25% in displacement and 5.57% in regional stress between the final two meshes,
meeting numerical convergence criteria for that idealized model only. Its ideal
clamp and estimated properties do not prove actual fin/root strength. Vibration and
flutter acceptance remains false.

Use `XDG_CACHE_HOME="$PWD/.cache"` for CAD/Gmsh and
`MPLCONFIGDIR="$PWD/.cache/matplotlib"` for plots. `make cad-reconcile` explicitly
adopts new unmeasured CAD mass/centroid/inertia estimates; run `make cad` afterward
to regenerate and verify exports. `make engineering` records preliminary screens
and fields; `make engineering-benchmark` remains nonzero while expanded criteria
are open. The current bounded thermal model uses an estimated external-case boundary
and lumped part means; liner conduction uses simplified gap/contact links and
approximate radiation, without resolved interfaces, bond-line conduction or spatial
gradients. Hot-soak results exceed several part screening
limits; these are open design findings, not qualification. Structural/thermal
calculations do not authorize physical work.
