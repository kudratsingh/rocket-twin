# Elmer A known-case local-error audit

A read-only, independent reconstruction of the saved SIF reference reproduces the original A2/A4/A8 maximum field errors for both Vec and classic runs. The error is spatially varying and is not explained by a single fitted offset or slope. These observations narrow where to investigate; they do not establish a cause or qualify either solver for actual geometry.

For each saved SIF, the audit parsed literal SI values `k=0.04 W/(m·K)`, `h=36030.6 W/(m²·K)`, `Th=573.15 K` and `Tb=308.15 K`, and independently measured mesh dimensions `0.0002 × 0.001 × 0.187 m`. It derived, without calling the prior analytic-reference helper,

`q = (Th − Tb) / (Lx/k + 1/h)` and `T(x) = Th − (q/k)x`.

The resulting `q` is **52707.4296313 W/m²** and the x slope **−1,317,685.740783 K/m**. These inputs agree with the retained reference config and SI geometry; that check is independent of the earlier field-reference implementation, but does not independently prove the overall physical model.

The maximum-error coordinates below are in metres. Vec and classic select the same node on each level and differ only in the last few reported digits:

| Level | Maximum absolute error (K) | Location `(x, y, z)` m | Max hot-face error (K) | Max cold-face error (K) | Max strict volume-interior error (K) |
| --- | ---: | --- | ---: | ---: | ---: |
| A2 | 1.9335763e-5 | (0.00005, 0.00075, 0.04675) | 1.14e-13 | 1.386e-6 | 1.9335763e-5 |
| A4 | 1.1222336e-4 | (0.000175, 0.001, 0.187) | 2.27e-13 | 4.067e-6 | 9.5144e-6 |
| A8 | 3.7359859e-5 | (0.0001875, 0.001, 0.0935) | 2.27e-13 | 6.326e-6 | 1.9481e-5 |

Strict volume interior means a node lies away from **all six** box faces. A4's largest error lies on both y and z side faces; A8's lies on a y side face. The separate x-interior category in the full record includes side-face nodes and should not be confused with strict volume interior. Hot-face values match the imposed temperature to approximately floating-point output precision. The retained maximum-error values remain failures of the unchanged 1e-7 K criterion.

An unconstrained least-squares fit `a + b x + c y + d z` was solved using dimension-normalized coordinates for numerical conditioning. The following values are Vec; classic agrees at the scale shown. Slope values are K/m and intercept/residual values K.

| Level | `a − Th` | `b − analytic x slope` | `c` | `d` | Max absolute fit residual |
| --- | ---: | ---: | ---: | ---: | ---: |
| A2 | −9.63e-7 | +5.15e-4 | +3.74e-4 | +5.21e-7 | 1.875e-5 |
| A4 | +3.47e-6 | −1.315e-3 | −2.409e-3 | −4.653e-5 | 1.044e-4 |
| A8 | +1.07e-6 | −1.816e-3 | −6.19e-5 | −1.951e-5 | 3.620e-5 |

The large residual remaining after fitting rules out describing the saved nodewise error as just one globally affine offset/slope adjustment. It does not distinguish local assembly, conditioning, boundary interactions or another shared numerical/input issue. Classic's separately recorded density warnings also remain an unresolved qualification limit.

Native `mesh.nodes` coordinates were parsed as decimal text into Float64; the saved VTU coordinate arrays and temperature arrays were both **Float64** in all six fields. Matching nodes by their rounded coordinate keys and then comparing actual coordinates gave a maximum mapped difference of **0 m** at every level, with unique keys. This rules out a mismatch in this saved-node mapping at the recorded values; it does not establish full element topology, boundary integration or numerical conditioning.

The [proof script](../build/wo03-elmer-local-error-audit-v1/audit.py) and [full audit record](../build/wo03-elmer-local-error-audit-v1/record.json) preserve all six cases, source SIF/mesh/VTU/config/record hashes before and after, physical coordinates, signed errors, and fit results. Source hashes remained unchanged. Two successful read-only passes used **1.057726 + 1.269619 = 2.327345 CPU s**; the second used **1.551 s wall** and **200,032,256 bytes** peak RSS. An initial read-only attempt used a case-sensitive VTU field name and stopped before analysis; the correct saved field name is lowercase `temperature`, and that first attempt's CPU was not separately captured. No solver, new mesh, altered field, or new heat method was run.

The remaining decision is an unresolved numerical-field investigation on these high-aspect-ratio mixed-wall inputs, with input/reference and saved-coordinate-mapping mismatches less supported by this audit. It authorizes no new grid, parameter tuning or actual-baffle attempt, and the earlier independent tool, heat-balance and qualification limits remain in force.

The [compact decision packet](../runs/wo03-elmer-classic-decision-20261101T093000Z/record.json) includes this read-only proof and both successful audit records; source fields remain local and unchanged.
