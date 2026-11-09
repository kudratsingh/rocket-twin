#!/usr/bin/env bash
# Local-only inspection/experiment preview. No paid service or flight controller.
set -euo pipefail
cd "$(dirname "$0")/.."
if [[ ! -x .venv/bin/python ]]; then
  echo "Missing project Python environment. Run make setup-viewer first." >&2
  exit 1
fi
node_major="$(node -p 'process.versions.node.split(".")[0]')"
if [[ "$node_major" != 22 ]]; then
  echo "This preview uses the project's Node 22 pin; found $(node --version)." >&2
  exit 1
fi
if [[ ! -d web/node_modules ]]; then
  echo "Missing locked web dependencies. In a normal terminal run npm --prefix web ci, then retry." >&2
  exit 1
fi
prepare_snapshot() {
  local producer="$1"
  local target="$2"
  if ! .venv/bin/python "$producer" --output "$target"; then
    echo "Unavailable prepared snapshot: $target (other workspaces remain available)." >&2
    # Only an ignored generated export is removed; never retain it as current.
    rm -f -- "$target"
  fi
}
# Explicit offline display preparation; requests never generate geometry.
if ! .venv/bin/python scripts/wo04_rp1_geometry_export.py; then
  echo "RP1 3D inspection unavailable; source drawings remain usable." >&2
fi
# Optional source-defined detail assets; core geometry remains the reference.
if ! .venv/bin/python scripts/wo04_rp1_detail_export.py; then
  echo "Optional RP1 detail unavailable; core inspection remains available." >&2
fi
# Only recorded existing triangles are prepared; unavailable optional assets do not block Design.
if ! .venv/bin/python scripts/wo04_prepare_component_detail.py --prepare; then
  echo "Optional mechanical component detail unavailable; the base model remains usable." >&2
fi
prepare_snapshot scripts/wo04_workbench_export.py web/public/engineering-workbench/g80-c1.json
prepare_snapshot scripts/wo04_workbench_extended_export.py web/public/engineering-workbench/g80-extended.json
prepare_snapshot scripts/wo04_workbench_a1_export.py web/public/engineering-workbench/g80-a1.json
prepare_snapshot scripts/wo04_g80_fixed_export.py web/public/engineering-workbench/preparedg80-fixed-f1.json
prepare_snapshot scripts/wo04_f2_export.py web/public/engineering-workbench/preparedg80-fixed-f2.json
prepare_snapshot scripts/wo04_f2_c1_export.py web/public/engineering-workbench/f2-c1.json
prepare_snapshot scripts/wo04_rp1_studies_export.py web/public/engineering-workbench/rp1-studies.json
prepare_snapshot scripts/wo04_vp1_validation_export.py web/public/engineering-workbench/rp1-validation.json
prepare_snapshot scripts/wo04_rp1_inspection_export.py web/public/engineering-workbench/rp1-ad1-inspection.json
prepare_snapshot scripts/wo04_rp1_connections_export.py web/public/engineering-workbench/rp1-connections.json
.venv/bin/python scripts/wo04_api.py --host 127.0.0.1 --port 8000 &
preview_api_pid=$!
cleanup() {
  kill "$preview_api_pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM
echo "Rocket Twin preview: http://127.0.0.1:5173"
echo "Local API: http://127.0.0.1:8000/docs"
echo "Preliminary design — engineering acceptance remains open. Ctrl-C stops this launcher."
npm --prefix web run dev -- --host 127.0.0.1 --port 5173 --strictPort
