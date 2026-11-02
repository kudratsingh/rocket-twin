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
.venv/bin/python scripts/wo04_workbench_export.py --output web/public/engineering-workbench/g80-c1.json
.venv/bin/python scripts/wo04_workbench_extended_export.py --output web/public/engineering-workbench/g80-extended.json
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
