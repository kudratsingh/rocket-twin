# Actual adhesive-interface occupancy

Executed `wo03-interface-occupancy-20261031T040905840132Z`; candidate `69df790ec9bcba1465be4fa9861a7ad5fbc467091cbf58f44dee069e56e00bac`, CAD `1193713d0f4a7ad8393a00a0a03e7aaa04e9aa9393d2034691ef7126ae3cdd3b`.

Nominal geometry partitions one physical space. These areas do not replace the visibility model or establish bond quality. The prior full-annulus gas path is invalid wherever glue or another solid occupies it. Actual openings remain available for gas transfer and geometry-resolved radiation.

| Region | Start, mm | Thickness, mm | Glue area, mm² | Other solid, mm² | Open area, mm² | Mechanism and correction |
|---|---:|---:|---:|---:|---:|---|
| mount_shell_bond_0 | 990.000 | 0.680 | 606.201718 | 0.000000 | 0.000000 | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |
| mount_shell_bond_1 | 1045.000 | 0.680 | 606.201718 | 0.000000 | 0.000000 | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |
| mount_shell_bond_2 | 1100.000 | 0.680 | 540.359846 | 57.243246 | 8.598626 | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |
| mount_shell_bond_3 | 1138.500 | 0.680 | 540.359846 | 57.243246 | 8.598626 | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |
| mount_shell_bond_4 | 1177.000 | 0.680 | 540.359846 | 57.243246 | 8.598626 | Glue: solid conduction plus bounded contacts. Other solid: its own material path. Open: air and visible-surface radiation only; remove duplicate full-area gas path. |

The record retains full volume balance and three area-probe refinements (0.1/0.01/0.001 mm). Full wetting is nominal CAD, not a process guarantee. Preserve the existing 0.32–0.68 mm gap variants and 2/10/50 W/K per-ring contact sensitivities; each requires its own geometry. Missing potting/meniscus cannot be assumed. Bond and air areas are disjoint; temperatures and radiation visibility remain separate calculations.

Part-average transient temperatures cannot establish local interface hot spots. Later owner stages retain bond sectioning/wetting, hot-load and instrumented soak measurements. No candidate adoption, thermal acceptance or flight release.

Evidence: `/Users/kudratsingh/Machine-Learning-Projects/rocket-twin/runs/wo03-interface-occupancy-20261031T040905840132Z/record.json`. Regenerate with `.venv/bin/python scripts/wo03_interface_occupancy.py`.
