# Owner visual reference set — November 9, 2026

**Saved for now as local visual references.** The25 explicitly supplied Desktop PNGs are preserved unchanged in the [local gallery](../../output/frontend-reference-set-20261109/index.html). The [small manifest](reference-set-20261109.json) records every original/copied path, byte count, dimensions, SHA-256, attachment mapping, feature goal and evidence status. This records the owner's intended visual depth; it does not adopt the pictured hardware, mechanisms, controller or third-party CAD.

The originals total **30,785,675bytes**. All25 copied hashes, post-copy original hashes, PNG dimensions and gallery image links match. No image was cropped, resized, converted or annotated. The gallery displays responsive previews through HTML/CSS while linking directly to the full unchanged original files. It is a generated local artifact, with a local `.gitignore` marker excluding the gallery/images from Git. Only this note and the manifest are intended as small source records for a future separate publication; no existing plan/backlog, fin inspector or current PR was changed.

## Reference groups and feature targets

| References | Saved purpose | Project goal to retain |
|---|---|---|
|[REF01–05](../../output/frontend-reference-set-20261109/index.html#inspection-ui)|CAD inspection UI: measurement, tree, explode/section and context menu|A readable source tree, precise source-backed dimensions, useful section/explode controls, contextual selection and reusable inspection views. External native-format marketing is not a claim that the project supports every pictured CAD format.|
|[REF06–11](../../output/frontend-reference-set-20261109/index.html#rocket-assembly)|External rocket overall, transparent internals and motor/fin service|Move coherently between whole rocket, transparent/internal views and serviceable assemblies, preserving source IDs, frame and return context.|
|[REF12–15](../../output/frontend-reference-set-20261109/index.html#electronics-mounting)|Detailed PCB/avionics, threaded posts and carriers|Readable actual board features and source-defined mounting/carrier interfaces, with fasteners and heights only where documented.|
|[REF16–20](../../output/frontend-reference-set-20261109/index.html#mechanisms)|Motor/fin mechanisms, bearing and cutaway references|Understand shafts, bearings, actuators and moving-surface relationships through source-owned detail and honest motion/constraint status. No airbrake or external mechanism is adopted.|
|[REF21–22](../../output/frontend-reference-set-20261109/index.html#ring-pcb)|Ring PCB and layout detail|Cross-link recorded electrical features with corresponding mechanical geometry where real product identity and mounting data exist.|
|[REF23–24](../../output/frontend-reference-set-20261109/index.html#physical-context)|Physical rocket and transparent design|Keep overall proportions, hardware context and the connection between assembled and internal representations easy to understand.|
|[REF25](../../output/frontend-reference-set-20261109/index.html#system-map)|Physics / Predictive Guidance / PD Controller / Velocity Delta block diagram|A complete project-specific physics and control system map with visible signals, feedback, configuration identity and implementation status.|

**Attachment mapping is deliberate:** REF01–18 correspond to attached images1–18. **REF19 is `Screenshot 2026-11-09 at 4.04.40 AM.png`, supplied separately as a quoted local path; it is not attached image19.** REF20–25 correspond to attached images19–24. The manifest therefore contains25 files,24 attached-image indices and one explicit quoted-path entry.

External Sapphire, Lafayette and Kisters content remains reference material. Its appearance does not establish RP1 dimensions, supplier identity, rights to redistribute manufacturer CAD, installed suitability or engineering qualification. Photographs and screenshots are not dimensional sources. Future project geometry must come from admitted drawings/data/models with exact source, units, frame, maturity and applicable part/configuration identity; unsupported detail stays unavailable. Pictured gains, altitude targets, airbrakes and mechanical arrangements do not become requirements or hardware choices.

## Required system-diagram goal

At the end of this workbench, the owner should be able to inspect a **shared source-backed system map** alongside the mechanical/electrical views:

1. **Shared JAX physics core:** environment/gravity/wind, thrust and aerodynamic forces/moments, changing mass/CG/inertia, coordinate frames, integration and events. Expose the applicable model identity, units, timestep and model-domain limits.
2. **Feedback chain:** vehicle state → sensors with noise/bias/rate/latency → estimator → guidance/setpoint → PID or RL → command/position/rate/torque limits → servo/linkage/gimbal → vehicle forces/moments and feedback.
3. **Parallel system paths:** event/recovery logic, independent recovery power and switching, logger power, source-net/connector boundaries, telemetry/logging and recorded outputs. Link a block to exact source parts/code/results only where that correspondence exists.
4. **Configuration and status:** make implemented, planned, estimated, unsupported and unqualified states explicit per block and connection. Keep current conventional **G80 unguided** behavior distinct from **G12 later PID-to-RL** development. Frozen RP1 inspection geometry does not acquire missing complete flight/inertia inputs from a screenshot or an archived run.

The following is a read-only code/document status snapshot for planning the diagram, **not a new simulator or hardware test**:

| Block | Current source status and limits |
|---|---|
|Physics/environment/forces/mass/integration|Preliminary shared JAX6DOF/RK4 and environment/aero/motor models exist in `src/sim/dynamics.py`, `environment.py`, `aero.py` and `motor.py`. Their approximations and qualification limits remain.|
|Sensors/noise/latency|Estimated sampled observation models exist in `src/sim/sensors.py` and `env.py`; no calibrated incoming hardware is established here.|
|Estimator/guidance/setpoint|Estimator/controller deliverables remain in [WO-06](../work-orders/WO-06-avionics-pid-baseline.md). The external screenshot's predictive guidance is not an implemented project controller.|
|PID and RL|Later separate [WO-06](../work-orders/WO-06-avionics-pid-baseline.md)/[WO-07](../work-orders/WO-07-rl-ascent.md) scope. `src/sim/protocol.py` explicitly records `none; gimbal locked`; no gains, policy or control benchmark is adopted by this packet.|
|Limits/servo/gimbal|Preliminary actuator dynamics and thrust mapping exist in `src/sim/actuators.py` and `tvc.py`. Physical linkage, moving inertia, actuator calibration and control qualification retain their own requirements.|
|Events/recovery|Existing `env.py`/`dynamics.py` contain guide/apogee/landing events and simplified recovery drag/inflation. Installed deployment and suspended-body/canopy dynamics remain separate/unqualified.|
|Independent power/logging|Source power boundaries and hardware definitions coexist with simulated telemetry in `src/sim/telemetry.py`. Recovery-controller identity remains unresolved; firmware/HIL and physical deployment are later work. [Firmware scope](../../firmware/README.md) and [WO-10](../work-orders/WO-10-firmware-hil.md) remain unchanged.|

REF25 visibly organizes Physics, Predictive Guidance and PD Controller regions; its lower Velocity Delta Controller region is cropped in the original screenshot. Preserve that original image, but use project source to define the eventual map. Its3DOF/fixed-mass abstraction, numerical gains and240m example are external reference content, not a replacement for the project's model or accepted targets. **This packet implements no PID, predictive guidance, RL, airbrake or diagram feature; it saves the reference and required end goal.**
