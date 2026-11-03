# Inspection refinement — source labels, selection and read-only preflight

Continues the first usable inspection slice after PR67. Astra MEDIUM refined
2D drawing readability and shared visibility; Terra HIGH added the read-only
normal-terminal preflight/checklist. The primary inspected actual offline images.
No engineering geometry, flight physics, dependencies or graphics engine changed.

The source2D drawing/export now includes a color/count legend, selected-part
annotation, source-role versus simplified-representation labels, a component
picker, hidden-layer versus globally-hidden explanations, Reveal&focus and
selection-only/context views. Existing hiddenIDs are respected across2D/3D;
local drawing keys do not reset the retained hidden3D camera. Pointer/keyboard
and actual browser downloads still require designated-agent observation.

Actual in-process API source is the recorded modular-performance-v1 reference,
resolvedspecc18abfee2444307e...,CAD1193713d0f4a7ad8... . It is not F2 or its new
connection proposal. The fin-set and high-g sensor selected views were rendered
through the installed nativeAppKit helper into1200x560PNGs,74.418/0.627seconds
(75.045seconds aggregate, below120). Their legend, identifiers, units, selected
callouts and maturity statements were inspected at original resolution without
clipping. Old520px exports remain historical; no browser screenshot is claimed.

Artifacts: `output/focused-design-2d-v2/fin_set/` and
`output/focused-design-2d-v2/high_g_accel/`; compact records in
`runs/wo04-focused-2d-refinement-20261103-v1/`.

Read-only normal-terminal preparation:

```sh
.venv/bin/python scripts/wo04_preview_preflight.py
make preview
```

The first command starts/stops nothing and performs no physics/CAD/build/install.
It distinguishes versions, missingGit metadata, source fingerprint mismatch,
missing API route, missing source, unreachable listener and a running-build identity.
An unreachable sandbox probe cannot prove that an owner-host server is stopped.
Current sandbox probes remainEPERM; source hashes match, and build/browser
acceptance remains separate. Node22/Python3.11/environment policy is retained.
The second command is the existing preview launcher and needs normal host
permission to bind5173/8000. See `frontend-owner-verification-20261103.md` for the
pending exact interaction matrix and evidence attribution.

Only the existing designated agent/window may verify after supported runtime
ownership is established. Prior automatic ownership rejection was not retried or
bypassed by these code/data tasks. Full43-task completion, all work-order and
physical/purchase/paid/firmware/flight gates remain open.
