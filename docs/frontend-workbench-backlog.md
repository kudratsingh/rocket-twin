# Frontend workbench backlog

Latest bounded FT-001/016/017 slice: [VP1 programme workbench](wo04-vp1-validation-workbench-20261106.md). Selectable stage/part SVG, dated material costs, unavailable all-in cost and five UNSENT copy/download previews are implemented; browser/physical acceptance remains open. No contact or test execution is inferred.

Latest bounded FT-016/evidence increment: [separate FP1/FR1 source-relationship comparison](wo04-rp1-studies-20261104.md), selectable graphics, source hashes and honest unaccepted status. Actual exported React graphs were inspected offline;85 integrated web tests/type/lint/format/build pass. Browser observation fields remain false; this does not complete the43-task plan.

The [machine-readable backlog](frontend-workbench-backlog.json) preserves all 43 planning-kit tasks, their dependencies, owner roles, acceptance criteria and evidence fields. This is a conservative snapshot: `partial` identifies bounded evidence, not task completion. A `planned` entry may have earlier work; it has not been established here against the full task criteria. All browser-observed and accepted fields are false for this increment. Source/build checks do not establish usability or acceptance.

Planning source: `output/frontend-planning-kit-20261103/` — manifest SHA-256 `4e2c647017b36ed5368ac757e873fe30d9f314f5e02fc01cf98943432ce93010`; backlog JSON SHA-256 `e0a717dabaf59794841861fd6febd8999e4bbec23464e1cd6e7e247840c0d20c`. These hashes bind the named files; the manifest lists individual kit files and excludes itself. The source snapshot has no Git metadata, so no commit identity is asserted.

Independent F2 engineering context: [decision](wo03-g80-f2-decision.md), [coupled accounting](wo03-g80-f2-coupled-accounting.md), [cost and placement](wo03-g80-f2-cost-and-placement.md), and [construction walkthrough](wo04-f2-construction-walkthrough.md). These are source context, not evidence of frontend task completion or engineering acceptance.

Browser observations belong to the established designated owner in the authorized window. No browser, download, performance or visual acceptance is claimed by this ledger. Phase P7 remains a continuous acceptance lane; later fidelity work in P8 requires its own scope.

| ID | Phase | Task | Owner | Dependencies | Status |
| --- | --- | --- | --- | --- | --- |
| FT-001 | P0 | Record source and configuration identity baseline | `primary_integrator` | — | partial |
| FT-002 | P0 | Define focused page and selection contracts | `primary_integrator` | FT-001 | partial |
| FT-003 | P0 | Specify telemetry phase and presentation validity | `data_analysis_owner` | FT-001 | partial |
| FT-004 | P0 | Resolve designated browser runtime prerequisite | `designated_terra_browser_owner` | FT-001 | blocked |
| FT-005 | P0 | Define recorded analysis and batch extension contracts | `primary_integrator` | FT-001, FT-003 | planned |
| FT-006 | P1 | Replace oversized universal shell with focused page frame | `primary_integrator` | FT-002 | partial |
| FT-007 | P1 | Synchronize deep links URL history and navigation | `primary_integrator` | FT-002, FT-006 | partial |
| FT-008 | P1 | Load independent candidate resources independently | `primary_integrator` | FT-001, FT-002, FT-006 | partial |
| FT-009 | P1 | Make scrolling focus and contextual drawers usable | `inspection_owner` | FT-006, FT-007 | partial |
| FT-010 | P1 | Package navigation rescue regression scenarios | `primary_integrator` | FT-007, FT-008, FT-009 | partial |
| FT-011 | P2 | Make CAD viewport dominant with contextual tools | `inspection_owner` | FT-002, FT-006, FT-008 | partial |
| FT-012 | P2 | Expose zoom fit reset and selected-part focus | `inspection_owner` | FT-011 | partial |
| FT-013 | P2 | Build source-derived OpenRocket-style 2D view | `inspection_owner` | FT-001, FT-011 | partial |
| FT-014 | P2 | Link part search selection and 2D/3D inspection | `inspection_owner` | FT-012, FT-013 | partial |
| FT-015 | P2 | Expose section explode and dimensional inspection | `inspection_owner` | FT-012, FT-014 | planned |
| FT-016 | P2 | Create focused construction and load-path views | `inspection_owner` | FT-013, FT-014 | partial |
| FT-017 | P2 | Deliver mass launch and inspection export slice | `inspection_owner` | FT-015, FT-016 | partial |
| FT-018 | P3 | Audit replay pose events and recovery model behavior | `data_analysis_owner` | FT-003 | partial |
| FT-019 | P3 | Implement reusable validity and provenance adapters | `data_analysis_owner` | FT-005, FT-018 | partial |
| FT-020 | P3 | Build concise complete-configuration experiment setup | `experiment_replay_owner` | FT-002, FT-005, FT-019 | partial |
| FT-021 | P3 | Implement reproducible run lifecycle and errors | `data_analysis_owner` | FT-005, FT-019 | planned |
| FT-022 | P3 | Add bounded local batch backend orchestration | `data_analysis_owner` | FT-021 | planned |
| FT-023 | P3 | Build batch setup progress and run library | `experiment_replay_owner` | FT-020, FT-021, FT-022 | planned |
| FT-024 | P3 | Implement synchronized scientific run comparison | `experiment_replay_owner` | FT-019, FT-021 | partial |
| FT-025 | P3 | Correct replay clock scrubbing and phase disclosures | `experiment_replay_owner` | FT-018, FT-019, FT-021 | partial |
| FT-026 | P4 | Improve camera scale lighting and trajectory context | `experiment_replay_owner` | FT-012, FT-025 | planned |
| FT-027 | P4 | Add honest event-linked schematic recovery illustration | `experiment_replay_owner` | FT-003, FT-018, FT-025 | planned |
| FT-028 | P4 | Surface telemetry evidence and validity during playback | `experiment_replay_owner` | FT-019, FT-025 | partial |
| FT-029 | P4 | Bound replay data transfer and rendering cost | `experiment_replay_owner` | FT-025, FT-026 | planned |
| FT-030 | P5 | Inventory compatible structural thermal and aero artifacts | `data_analysis_owner` | FT-001, FT-005 | planned |
| FT-031 | P5 | Implement analysis identity and registration adapters | `data_analysis_owner` | FT-019, FT-030 | planned |
| FT-032 | P5 | Build focused analysis selection and unavailable states | `data_analysis_owner` | FT-002, FT-014, FT-031 | planned |
| FT-033 | P5 | Display true structural fields and margins | `data_analysis_owner` | FT-031, FT-032 | planned |
| FT-034 | P5 | Display thermal histories and supported aero results | `data_analysis_owner` | FT-031, FT-032 | planned |
| FT-035 | P5 | Compare compatible analysis cases with stable scales | `data_analysis_owner` | FT-024, FT-033, FT-034 | planned |
| FT-036 | P6 | Integrate focused pages and end-to-end identity flow | `primary_integrator` | FT-010, FT-017, FT-023, FT-025, FT-028, FT-029, FT-035 | partial |
| FT-037 | P6 | Optionally compose one dense Mission Control page | `primary_integrator` | FT-036 | planned |
| FT-038 | P7 | Continuously observe first inspection slice in permitted Chrome | `designated_terra_browser_owner` | FT-004, FT-010, FT-017 | planned |
| FT-039 | P7 | Observe experiments batches replay comparison and analysis | `designated_terra_browser_owner` | FT-036, FT-038 | planned |
| FT-040 | P7 | Measure representative long-run browser performance | `designated_terra_browser_owner` | FT-029, FT-039 | planned |
| FT-041 | P7 | Close observed defects and publish bounded acceptance | `primary_integrator` | FT-038, FT-039, FT-040 | planned |
| FT-042 | P8 | Scope future validated recovery CFD and controls fidelity separately | `primary_integrator` | FT-018, FT-030 | planned |
| FT-043 | P8 | Scope controlled parametric design editing with regenerated candidates | `primary_integrator` | FT-001, FT-005, FT-013 | planned |
