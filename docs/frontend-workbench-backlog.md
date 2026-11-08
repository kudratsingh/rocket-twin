# Frontend workbench backlog

Current source: dedicated G80 RP1/AD1 v2; archived CAD/runs remain separate. G54 and G12 PID-to-RL remain committed tracks. No inquiry/contact, purchase, physical test or engineering/flight release is implied.

**November8 reconciliation:** the43-task ledger is synchronized with the28-task RV map and merged PR101–104 evidence. Six source-contract/audit/ownership tasks are complete at their limited scope;33 tasks remain partial, three optional/future tasks are deferred, and FT027 schematic recovery illustration remains planned. These are task states, not a completion percentage. No new acceptance check was passed by updating this document.

Use [the current release worklist](frontend-release-worklist.md), [machine-readable FT tasks](frontend-workbench-backlog.json), [RV tasks](frontend-revamp-backlog.json) and [acceptance checks](frontend-revamp-acceptance.csv). The supported sole native owner is `/root/browser_access_sol` in the authorized current Chrome window. Earlier ownership/extension blockers are historical; the separate rejected DevTools/viewport setup is still blocked. No headless/CDP, other-window or denied-method retry.

Source and live evidence: [RP1 source release](frontend-release-20261107.md), [interior workflow](studies/frontend-interiors-20261108/report.md), [PCB source reference](studies/frontend-hardware-detail-sources-20261108/integration.md), [Move/Rotate and Whole rocket correction](studies/frontend-pan-20261108/report.md). Browser checks are attributed to their actual code/data/window; earlier captures do not accept later changes.

The original planning kit remains in `output/frontend-planning-kit-20261103/`, manifest SHA-256 `4e2c647017b36ed5368ac757e873fe30d9f314f5e02fc01cf98943432ce93010`. Its frozen intake and prior execution records remain historical. Current public GitHub publication uses focused PRs and required checks; engineering/build/WO10/flight gates stay separate.

| ID | Phase | Task | Owner | Dependencies | Status |
| --- | --- | --- | --- | --- | --- |
| FT-001 | P0 | Record source and configuration identity baseline | `primary_integrator` | — | complete |
| FT-002 | P0 | Define focused page and selection contracts | `primary_integrator` | FT-001 | complete |
| FT-003 | P0 | Specify telemetry phase and presentation validity | `data_analysis_owner` | FT-001 | complete |
| FT-004 | P0 | Resolve designated browser runtime prerequisite | `designated_sol_browser_owner` | FT-001 | complete |
| FT-005 | P0 | Define recorded analysis and batch extension contracts | `primary_integrator` | FT-001, FT-003 | complete |
| FT-006 | P1 | Replace oversized universal shell with focused page frame | `primary_integrator` | FT-002 | partial |
| FT-007 | P1 | Synchronize deep links URL history and navigation | `primary_integrator` | FT-002, FT-006 | partial |
| FT-008 | P1 | Load independent candidate resources independently | `primary_integrator` | FT-001, FT-002, FT-006 | partial |
| FT-009 | P1 | Make scrolling focus and contextual drawers usable | `inspection_owner` | FT-006, FT-007 | partial |
| FT-010 | P1 | Package navigation rescue regression scenarios | `primary_integrator` | FT-007, FT-008, FT-009 | partial |
| FT-011 | P2 | Make CAD viewport dominant with contextual tools | `inspection_owner` | FT-002, FT-006, FT-008 | partial |
| FT-012 | P2 | Expose zoom fit reset and selected-part focus | `inspection_owner` | FT-011 | partial |
| FT-013 | P2 | Build source-derived OpenRocket-style 2D view | `inspection_owner` | FT-001, FT-011 | partial |
| FT-014 | P2 | Link part search selection and 2D/3D inspection | `inspection_owner` | FT-012, FT-013 | partial |
| FT-015 | P2 | Expose section explode and dimensional inspection | `inspection_owner` | FT-012, FT-014 | partial |
| FT-016 | P2 | Create focused construction and load-path views | `inspection_owner` | FT-013, FT-014 | partial |
| FT-017 | P2 | Deliver mass launch and inspection export slice | `inspection_owner` | FT-015, FT-016 | partial |
| FT-018 | P3 | Audit replay pose events and recovery model behavior | `data_analysis_owner` | FT-003 | complete |
| FT-019 | P3 | Implement reusable validity and provenance adapters | `data_analysis_owner` | FT-005, FT-018 | partial |
| FT-020 | P3 | Build concise complete-configuration experiment setup | `experiment_replay_owner` | FT-002, FT-005, FT-019 | partial |
| FT-021 | P3 | Implement reproducible run lifecycle and errors | `data_analysis_owner` | FT-005, FT-019 | partial |
| FT-022 | P3 | Add bounded local batch backend orchestration | `data_analysis_owner` | FT-021 | partial |
| FT-023 | P3 | Build batch setup progress and run library | `experiment_replay_owner` | FT-020, FT-021, FT-022 | partial |
| FT-024 | P3 | Implement synchronized scientific run comparison | `experiment_replay_owner` | FT-019, FT-021 | partial |
| FT-025 | P3 | Correct replay clock scrubbing and phase disclosures | `experiment_replay_owner` | FT-018, FT-019, FT-021 | partial |
| FT-026 | P4 | Improve camera scale lighting and trajectory context | `experiment_replay_owner` | FT-012, FT-025 | partial |
| FT-027 | P4 | Add honest event-linked schematic recovery illustration | `experiment_replay_owner` | FT-003, FT-018, FT-025 | planned |
| FT-028 | P4 | Surface telemetry evidence and validity during playback | `experiment_replay_owner` | FT-019, FT-025 | partial |
| FT-029 | P4 | Bound replay data transfer and rendering cost | `experiment_replay_owner` | FT-025, FT-026 | partial |
| FT-030 | P5 | Inventory compatible structural thermal and aero artifacts | `data_analysis_owner` | FT-001, FT-005 | partial |
| FT-031 | P5 | Implement analysis identity and registration adapters | `data_analysis_owner` | FT-019, FT-030 | partial |
| FT-032 | P5 | Build focused analysis selection and unavailable states | `data_analysis_owner` | FT-002, FT-014, FT-031 | partial |
| FT-033 | P5 | Display true structural fields and margins | `data_analysis_owner` | FT-031, FT-032 | partial |
| FT-034 | P5 | Display thermal histories and supported aero results | `data_analysis_owner` | FT-031, FT-032 | partial |
| FT-035 | P5 | Compare compatible analysis cases with stable scales | `data_analysis_owner` | FT-024, FT-033, FT-034 | partial |
| FT-036 | P6 | Integrate focused pages and end-to-end identity flow | `primary_integrator` | FT-010, FT-017, FT-023, FT-025, FT-028, FT-029, FT-035 | partial |
| FT-037 | P6 | Optionally compose one dense Mission Control page | `primary_integrator` | FT-036 | deferred |
| FT-038 | P7 | Continuously observe first inspection slice in permitted Chrome | `designated_sol_browser_owner` | FT-004, FT-010, FT-017 | partial |
| FT-039 | P7 | Observe experiments batches replay comparison and analysis | `designated_sol_browser_owner` | FT-036, FT-038 | partial |
| FT-040 | P7 | Measure representative long-run browser performance | `designated_sol_browser_owner` | FT-029, FT-039 | partial |
| FT-041 | P7 | Close observed defects and publish bounded acceptance | `primary_integrator` | FT-038, FT-039, FT-040 | partial |
| FT-042 | P8 | Scope future validated recovery CFD and controls fidelity separately | `primary_integrator` | FT-018, FT-030 | deferred |
| FT-043 | P8 | Scope controlled parametric design editing with regenerated candidates | `primary_integrator` | FT-001, FT-005, FT-013 | deferred |
