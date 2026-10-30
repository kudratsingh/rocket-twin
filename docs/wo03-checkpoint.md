> This is the saved pre-resume snapshot, retained for provenance. The owner has
> resumed work; current status is in STATUS.md and scope in ADR-0007/WO-03.

# Historical WO-03 checkpoint — superseded after owner resume

Owner explicitly requested save and stop. Resume WO-03, then WO-04 only after its
CAD benchmark passes. No physical work, purchases, paid runs or WO-10 gate changes.

## Saved state

- WO-02 is complete. PR #2 and #3 merged; main merge commit:
  dc24bd8f94f4d8c4e0acabfc90bdaccda41ddf23.
- Private repository: kudratsingh/rocket-twin. Remote branch `wo-03-cad` exists,
  created from main. No WO-03 commits or PRs have been published yet.
- Local Git metadata creation remains restricted; authenticated GitHub connector
  is available for branches/trees/commits/PRs. Do not claim a local Git commit.
- Added requirements-wo03.txt (CadQuery 2.8.0, trimesh 4.11.5, existing WO-02 pins).
- Added requirements-wo04.txt (above plus FastAPI 0.162.0, uvicorn 0.41.0,
  httpx 0.28.1). Added `make setup-cad` and `make setup-viewer` targets.
- The owner ran `make setup-viewer`; imports and a real CadQuery solid volume/
  inertia check succeeded. Installed: CadQuery 2.8.0, cadquery-ocp 7.9.3.1.1,
  trimesh 4.11.5, FastAPI 0.162.0, uvicorn 0.41.0, httpx 0.28.1.
  ezdxf reported an unwritable global cache; configure a workspace cache on resume.
- No CAD generators, CAD exports, sensor additions or vehicle geometry changes
  have been implemented. Existing vehicle/simulation configuration remains intact.
- Read AGENTS.md, CLAUDE.md, PLAN, ENVIRONMENT, WO-03, WO-04, UI and EXTENSIONS.
  Follow focused PRs and merge after checks; routine owner review is not required.

## Resume work

1. Verify CadQuery/trimesh/API imports. Read current spec and work-order files.
2. Implement spec-driven CadQuery parts and all three actual assemblies, plus
   separate conditional G54 fit study. Keep G80 reference and distinct PID-to-RL
   trainer. Preserve source archives and G25W quarantine.
3. Replace envelope overlaps with a real layout. Current parts largely share the
   centreline; avionics, battery, recovery bulkhead and servo placements overlap.
   Resolve these before claiming collision-free CAD. Include joints, mounts,
   retaining hardware, liners, fin attachments and every part's learn/build metadata.
4. Model a two-axis gimbal with real nested rings, pivots, links and mechanical
   stops; verify combined pitch/yaw sweep, motor/case/liner/nozzle keep-outs,
   servo/link motion and manufacturing tolerances. Do not retain linkage_ratio=1
   without deriving it from actual horn/link geometry. Earlier reasoning explored
   different arrangements; none is an accepted or implemented design.
5. Reconcile actual CAD volume, centroid and inertia with the YAML/simulation.
   Distinguish bulk-density custom solids from purchased/flexible envelopes with
   supplied or estimated mass. Do not tune density merely to fit old estimates or
   call commercial bounding-box volume a verified physical mass.
6. Address high-g sensing with a real additional sensor, retaining the low-g IMU
   for gyro/attitude. Candidate investigated: Adafruit ADXL375 breakout PID 5374,
   +/-200 g, published board envelope 25.6 x 17.7 x 4.6 mm, mass 1.0 g, $24.95.
   These are manufacturer facts, not a purchase or final component selection.
   Add mounting, harness, netlist, mass and realistic sensor-model consequences.
7. Re-run affected static/flight comparisons and CAD mass/interface/sweep checks.
   Deliver STEP/STL/GLB plus manifests and part-function documentation. No physical
   fit, structural, thermal or flight release from numerical checks alone.
8. Once CAD benchmark passes, proceed into the existing WO-04 FastAPI/React/
   react-three-fiber viewer contract. Node 22.23.2 and npm 10.9.8 are available;
   npm cache contains React/Vite packages, so check offline install before asking
   owner for any further network setup.

## Sources already checked

- https://cadquery.readthedocs.io/en/latest/installation.html
- https://cadquery.readthedocs.io/en/latest/assy.html
- https://cadquery.readthedocs.io/en/latest/importexport.html
- https://pypi.org/project/cadquery/ (2.8.0 published June 2026)
- https://www.analog.com/en/products/adxl375.html
- https://www.adafruit.com/product/5374
- https://learn.adafruit.com/adafruit-adxl375/downloads
- https://github.com/adafruit/Adafruit_ADXL375_PCB

Terminal PyPI DNS remains restricted in the agent session. The owner can install
from their normal terminal; do not repeatedly attempt identical blocked downloads.
Do not start further work until the owner resumes after the computer update.
