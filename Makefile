PYTHON ?= .venv/bin/python
UV_CACHE_DIR ?= $(CURDIR)/.cache/uv
MPLCONFIGDIR ?= $(CURDIR)/.cache/matplotlib
export UV_CACHE_DIR MPLCONFIGDIR

.PHONY: setup setup-reference check smoke tiny benchmark fetch-motors motor-study fetch-motor-study-sources f22-study fetch-f22-sources g-impulse-study

setup-cad: ## Install pinned CAD dependencies.
	uv pip install --python $(PYTHON) -r requirements-wo03.txt

setup-viewer: ## Install CAD and API dependencies before WO-04.
	uv pip install --python $(PYTHON) -r requirements-wo04.txt

setup-sim: ## Install pinned WO-02 CPU/reference/telemetry dependencies.
	uv pip install --python $(PYTHON) -r requirements-wo02.txt

setup: ## Install the implemented WO-01 CPU environment (requires network).
	uv venv --python 3.11 --allow-existing
	uv pip install --python $(PYTHON) -r requirements-wo01.txt

check:
	$(PYTHON) -m ruff check src tests scripts
	$(PYTHON) -m black --check src tests scripts
	$(PYTHON) -m mypy

smoke:
	$(PYTHON) -m pytest -q

tiny: ## Current CPU pipeline through WO-02.
	$(PYTHON) scripts/wo01_platform.py --preset tiny
	$(PYTHON) scripts/wo02_sim.py --preset tiny --compare rocketpy --require-benchmark

setup-reference: ## Install the pinned independent reference; needs network access.
	uv pip install --python $(PYTHON) -r requirements-wo01.txt rocketpy==1.13.0

benchmark: ## All modular modes; WO-01 preliminary design gates, never flight readiness.
	$(PYTHON) scripts/wo01_platform.py --preset sim --compare rocketpy --require-benchmark
	$(PYTHON) scripts/wo02_sim.py --preset tiny --compare rocketpy --require-benchmark

fetch-motors: ## Download unreviewed source curves and metadata; requires network.
	$(PYTHON) scripts/wo01_fetch_motors.py

motor-study: ## Local static screening; does not select a motor or change the baseline.
	$(PYTHON) scripts/wo01_motor_study.py --preset tiny --compare rocketpy

fetch-motor-study-sources: ## Collect primary PDFs and F25 curves for offline review.
	$(PYTHON) scripts/wo01_fetch_study_sources.py

f22-study: ## Historical and 2026 post-test comparisons; no selection.
	$(PYTHON) scripts/wo01_motor_study.py --preset tiny --config configs/studies/f22-selection.yaml --compare rocketpy

fetch-f22-sources: ## Fetch F22 source curve, certificates and correct hobby-case dimensions.
	$(PYTHON) scripts/wo01_fetch_study_sources.py --config configs/studies/f22-selection.yaml --output data/f22-study-sources

g-impulse-study: ## Published-summary G-motor screening with mass-growth allowance; no selection.
	$(PYTHON) scripts/wo01_motor_study.py --preset tiny --config configs/studies/g-impulse-selection.yaml

flight-study: ## Complete source-hypothesis trade, uncertainty and recovery study.
	$(PYTHON) scripts/wo02_sim.py --preset sim --study --compare rocketpy --require-benchmark

# WO-03 exports and engineering screens; expanded acceptance remains explicit.
cad:
	XDG_CACHE_HOME=$(CURDIR)/.cache $(PYTHON) scripts/wo03_cad.py --preset sim --require-benchmark

cad-reconcile:
	XDG_CACHE_HOME=$(CURDIR)/.cache $(PYTHON) scripts/wo03_cad.py --preset tiny --check-only --reconcile

engineering:
	$(PYTHON) scripts/wo03_engineering.py --preset sim

engineering-benchmark:
	$(PYTHON) scripts/wo03_engineering.py --preset sim --require-benchmark

revalidate: benchmark flight-study

vibration:
	XDG_CACHE_HOME=$(CURDIR)/.cache $(PYTHON) scripts/wo03_vibration.py --preset sim

traceability:
	$(PYTHON) scripts/wo03_traceability.py --preset tiny

service-diagrams:
	$(PYTHON) scripts/wo03_service_diagrams.py --preset tiny

thermal-study: ## Verified opaque-wall refinement; does not qualify hardware.
	$(PYTHON) scripts/wo03_thermal_topology.py --preset tiny

fin-study: ## Isolated fin construction/mass/stability trade; no adoption.
	$(PYTHON) scripts/wo03_fin_design.py --preset tiny

tolerance-study: ## Manufacturing/thermal-domain interval screens; failures stay open.
	$(PYTHON) scripts/wo03_tolerances.py --preset tiny

mount-study: motor-support ## Compatibility target; the old support-tube proposal remains historical.

motor-support: ## Check the active plate/cassette/retention load paths.
	$(PYTHON) scripts/wo03_motor_support.py --preset tiny

recovery-integration: ## Check actual recovery packing, demands and resolved independent power.
	$(PYTHON) scripts/wo03_recovery_integration.py --preset tiny

integration-report: ## Record complete mass/CG/full inertia and growth sensitivities.
	$(PYTHON) scripts/wo03_integrated_report.py --preset tiny

inspection-figures: ## Render existing CAD exports; run make cad first after changes.
	$(PYTHON) scripts/wo03_assembly_figures.py --preset tiny

correction-package: ## Rebuild isolated Package A copies and portable, hash-checked aliases.
	$(PYTHON) scripts/wo03_correction_package.py --preset tiny

recovery-budget: ## Exact G12 guide-limited recovery budget; retains full growth reserve.
	$(PYTHON) scripts/wo03_recovery_mass_budget.py --preset tiny

thermal-matrix: correction-package ## Required cases and exploratory cases remain distinct.
	$(PYTHON) scripts/wo03_thermal_matrix.py --preset tiny
