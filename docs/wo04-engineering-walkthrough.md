# First engineering walkthrough

This increment implements a read-only C1 engineering explanation alongside the
saved preview. It adds arrangement/projection/section SVGs, selectable construction
details and assembly illustrations, load-transfer/free-body diagrams, mass/CG/CP
plots, and recorded launch comparisons. Shared selection links drawings to part
functions, materials, mass bases, sources and open findings. SVG downloads include
identity/source metadata; JSON has a separate source manifest. No current C1
detailed CAD, spatial stress/temperature field or installed acceptance is supplied.

## Open locally

From the repository root:

```sh
.venv/bin/python scripts/wo04_workbench_export.py --output web/public/engineering-workbench/g80-c1.json
make preview
```

Open <http://127.0.0.1:5173/?workspace=engineering>. The live endpoint is
`/api/engineering/workbench`; the prepared JSON is the same versioned export,
not a new analysis. Its source identity must remain visible when used offline.
The default CLI destination is `build/engineering-workbench/g80-c1.json`.

New graphics are **browser-unverified**: code/SSR checks do not establish owner
visual acceptance, click behavior or successful download. No new screenshots are
verified. At this documentation checkpoint the designated browser agent reported
unresolved runtime ownership; restricted probes refused ports5173/8000. Actual
host availability and a supported runtime handoff remain unverified. The subsequent
primary startup returned `listen EPERM` on5173. After the owner reported starting
the preview in normal Terminal, one new restricted-shell endpoint probe still
refused5173/8000; that is not proof of host-browser failure. Consult the
latest [status](STATUS.md) for any subsequent startup evidence; owner/operator
action is required only if that handoff remains unavailable.

## Identity and interpretation

Schema1.0.0 exports135 sourced components and136 distribution rows. Configuration
`C1_closed_receiver_mass_balance` remains preliminary, with `cad_revision:null`.
Full hashes are included for every source. Key SHA-256 identities:

| Input | SHA-256 |
| --- | --- |
| C1 specification | `d76c34c69c64b9281d0e945643b95d79385393ab7d40156c7cdbc6a601f15228` |
| Source lock | `b90ced9757330494f593867cd8fc88be58c68a77619c2e1e00cc717fc19c4100` |
| Attachment record | `0af4cc8a52bf68feb5a7e69f3af2f39333894272389c6b28d47e1f5b76b7bd5b` |
| Corrected connection audit | `7ae31e129db12a049150be84c05b446851bb8ec7396db328f890a5cf783586bf` |

Axial stations increase aft from the nose; radius is measured from the centreline.
Source body+X points toward the nose, so station=−bodyX. Units are mm, g, N, N·m
and m/s; other quantities carry explicit units. Geometry maturity distinguishes
concept, envelope, detailed CAD and undefined. Evidence states distinguish
calculated, estimated, measured, unavailable, failed, historical and superseded;
this increment adds no measured installed result. Undefined geometry is listed
rather than invented.

The complete distribution reconciles1079.806750976539g nominal plus separate50g
at1227mm, including retained fin residual/tabs once. Additional20g/motor-CG probes
and stopped R1 cases remain separate. Body-root8.83035, socket-centre10.75095 and
rocket-axis16.11538N·m are different recorded moment datums. Baseline1.5m usable,
formal15m/s and separate15.5 planning remain;1.8m C1 departure14.975m/s fails15.
Illustrative1.971m equipment and rail buttons are unconfirmed.

Missing/hash-changed inputs fail explicitly. Eight backend tests cover source,
identity, ledger, corrected loads and CLI contracts; engineering gates remain open.

## Tailored references

The presentation adopts traceable technical-data identities from the
[NASA SE Handbook §6.6](https://www.nasa.gov/reference/6-0-crosscutting-technical-management/)
and separates verification evidence from intended-use validation under
[§5.3](https://www.nasa.gov/reference/5-0-product-realization/).
[NASA-STD-7009B](https://standards.nasa.gov/node/263) motivates explicit intended
use, credibility limits and project acceptance criteria.
[Glenn's stability explanation](https://www1.grc.nasa.gov/beginners-guide-to-aeronautics/conditions-for-rocket-stability/)
supports explaining CG ahead of CP; it does not validate C1 aerodynamics.
The thermal increment will identify property sources and interfaces, then
build/check/run/verify, following
[Building Thermal Models](https://ntrs.nasa.gov/api/citations/20170010293/downloads/20170010293.pdf).
These are tailored references, not NASA compliance claims.
