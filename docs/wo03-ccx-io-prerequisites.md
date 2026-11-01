# WO-03 CalculiX 2.23 I/O prerequisites

**Finding (2026-10-31): the installed CalculiX 2.23 path is not currently
qualified for the unchanged A/B/B_strong acceptance checks.** The installed
binary is `/opt/homebrew/bin/ccx` (Homebrew Cellar `calculix@2.23/2.23_1`;
`ccx -v` reports 2.23). It has already solved A and the cylindrical fixture,
but the retained packet records insufficient printed precision for the exact
`1e-7 K` field and `1e-10 W` balance checks. No precision option is documented.
In inspected upstream development source, `*NODE OUTPUT` selects the binary
FRD mode whose nodal scalar values are written as four-byte floats; the
separate eight-byte writer is not selected by that parser path. A later
declared A-2 diagnostic directly decoded the installed Homebrew binary's NT
and RFL records as four-byte node IDs plus float32 values; the three-grid
packet stopped after A-2 due to its first parser-format error, and A-4/A-8 were
not run. No existing input method was
found that supplies the continuously varying quadratic Robin law in B or
B_strong without either a linked user routine or a controlled boundary
discretization.

This is a bounded documentation/source inspection, not solver qualification.
The official manual and source links below are primary sources. Official
GitHub `master` currently identifies itself as `Version DEVELOPMENT`; no 2.23
source tag or commit was established in this inspection. Its code details
show conditional output encodings but are not proven byte-for-byte to be the
source used for the installed Homebrew binary. The initial source inspection did not run a solver. The later declared A-2
output diagnostic used the unchanged installed binary; no rebuild or modification
occurred. Its partial result is distinguished from the literature assessment.

## Option assessment

| Route | Documented behavior and source | Sufficient in principle? | Executable with current installed binary? | Same physical problem? |
|---|---|---:|---:|---|
| `*NODE PRINT` for `NT` and `RFL`/reaction output in `.dat` | Manual §7.99 (PDF pp. 568–570) describes the requested nodal output. Upstream [`src/printoutnode.f`](https://github.com/Dhondtguido/CalculiX/blob/master/src/printoutnode.f#L646-L730) writes temperatures and nodal thermal reactions with `(i10,1x,1p,e13.6)` / `(i10,1p,3(1x,e13.6))`. This is seven significant digits; around 300–573 K, displayed temperature increments are about `1e-4 K`, insufficient to resolve `1e-7 K`. ASCII FRD uses `%12.5E` (six significant digits), with about `1e-3 K` increments in this range. Reaction/heat output at DAT width cannot prove a `1e-10 W` cancellation either. | No | Yes, but precision is fixed by the output implementation; manual exposes no precision selector. | Yes, but fails acceptance evidence precision. |
| `*NODE FILE` → ASCII `.frd` | Manual §7.97 (PDF pp. 565–566) calls this ASCII FRD. Upstream `src/frdselect.c` writes ASCII scalar field values using `%12.5E` after float conversion (around lines 854–873; see [source](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdselect.c)). The field path is not suitable for the `1e-7 K` criterion. Coordinate formatting in `frd.c` is separate evidence and is not used to infer this field precision. | No | Yes, with documented output selection. | Same selected fields, insufficient output resolution. |
| `*NODE OUTPUT` → mixed binary/ASCII `.frd` | Manual §7.98 (PDF p. 566) says the file is a mixture of binary and ASCII and its options match `*NODE FILE`. Upstream `src/frd.c` routes nodal `NT` through `frdselect` (around lines 3761–3786). The parser in [`src/calinput.f`](https://github.com/Dhondtguido/CalculiX/blob/master/src/calinput.f#L3908-L3932) sets `output='bin '` for `*NODE OUTPUT` and `output='asc '` for `*NODE FILE`. In [`src/frdselect.c`](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdselect.c#L804-L839), the `bin` scalar-value branch casts to `float` and writes `sizeof(float)`; subsequent component blocks repeat the same branches ([lines 854–885](https://github.com/Dhondtguido/CalculiX/blob/master/src/frdselect.c#L854-L885)). A separate non-ASCII/non-`bin` branch writes `sizeof(double)`, but the inspected parser does not select it for `*NODE OUTPUT`. The declared installed-binary A-2 probe directly decoded all 27 NT and RFL records using that four-byte layout; its preserved output and parser correction are documented in [`wo03-ccx-output-probe.md`](wo03-ccx-output-probe.md). A-4/A-8 were not run after the initial parser-format stop. The official master source is DEVELOPMENT and not matched to the installed Homebrew 2.23 source archive. | No for the inspected and A-2-confirmed `*NODE OUTPUT` path | Keyword works for the tested A-2 field; three-grid packet is incomplete | Same selected fields; observed float32 output is too coarse for `1e-7 K`. RFL does not establish integrated film heat. |
| `RFL` as a thermal boundary reaction | Manual §7.99 describes `RFL` as external concentrated heat sources, not as the integrated heat flux from a film/Robin boundary. Do not treat `RFL` as total film heat without separate source/semantics proof. | Not established as film reaction output | Keyword exists for its stated quantity | Not shown equivalent to integrated surface film heat. |
| Explicit `*FILM` element-face entries (`Fx`) | Manual §7.59 (PDF pp. 510–512) accepts sink temperature and film coefficient for uniform film data. Subdividing the surface and assigning constants is a numerical approximation to the same continuous Robin law, not a different continuum-physics model. It is not qualified as the unchanged B/B_strong case without a quantified bound on the resulting boundary-input error. | Potentially, if boundary-input error is controlled | Yes | Continuum law can match; finite patch input error must be quantified and included in acceptance. |
| Nonuniform film label `FxNUy` + `film.f` | Manual §7.59 and §8.4.5 (PDF pp. 510–512, 643–644) define nonuniform convection via a user routine. The routine receives integration-point coordinates, current temperature, element, face, and area and returns film coefficient `h` and sink temperature; it can therefore represent the continuous quadratic spatial law without replacing it with centroids or surface patches. The manual §8 (PDF p. 633) says user routines must replace the dummy routine and be recompiled. Official interface and coordinates: [manual §8.4.5](https://www.dhondt.de/ccx_2.23.pdf), [upstream `src/film.f`](https://github.com/Dhondtguido/CalculiX/blob/master/src/film.f). | Yes in a compatible linked build; not a proved capability of the installed binary as shipped | No evidence of runtime user-routine loading. Existing binary is not documented to accept an external `film.f`; a custom linked executable/rebuild is required and explicitly outside this reconnaissance. | Yes when coded from the exact coordinates/formula and validated; requires a future declared build and qualification packet. |
| Nonuniform `*DFLUX` + `dflux.f` | Manual §8.4.3 (PDF pp. 639–641) exposes current solution temperature `sol`, integration-point coordinates `coords`, element/face identity, and returned flux. A function `q=h(x)(Tbulk(x)-T)` can in principle encode the same Robin heat law as a temperature-dependent surface flux, provided sign, units, and solver iteration/tangent behavior are qualified. Upstream requires a user routine; manual §8 again says replace the dummy and recompile. [Manual](https://www.dhondt.de/ccx_2.23.pdf). | Plausible but unverified; `film.f` is the direct documented convection interface | No documented runtime route; custom link/rebuild required | Potentially yes if the exact law and sign are used; not execution-ready. This is not a way to silently substitute a fixed flux. |
| `*NETWORK MPC` | Manual §7.86 (PDF pp. 559–560) requires custom `networkmpc_lhs.f` and `networkmpc_rhs.f`; the listed network degrees of freedom are total temperature/pressure/mass flow in network elements. It is not a boundary condition for a continuum heat-transfer face and does not create a distributed quadratic Robin field on the 3-D wall. | No | No as an unmodified existing binary feature requiring custom routines; no surface mapping | No; different network model/problem. |

## Output precision conclusion

The manual distinguishes `.dat` `*NODE PRINT`, ASCII `.frd` `*NODE FILE`,
and mixed binary/ASCII `.frd` `*NODE OUTPUT` (manual §6.13, PDF p. 402;
§§7.97–7.99, PDF pp. 565–570). It documents no precision flag on these output
keywords. Upstream `printoutnode.f` shows `E13.6` for `.dat` nodal
temperatures and thermal reactions: seven significant digits, with about
`1e-4 K` increments near 300–573 K. ASCII FRD scalar values use `%12.5E`
(about `1e-3 K` increments in this range) after float conversion. In the
inspected upstream parser, `*NODE OUTPUT` sets
`output='bin '`, and `frdselect.c` writes those nodal scalar results as
four-byte floats; its separate eight-byte `double` branch is not reached by
that keyword. This establishes the source path, but not the exact path in the
installed Homebrew binary because the source identifies as DEVELOPMENT and is
not pinned to the 2.23 package. The declared A-2 probe has now directly
confirmed that this installed binary emits NT as float32: 27 ordered node
records decoded, with `3.0518e-5` to `6.1035e-5 K` spacing across the field.
This does not meet `1e-7 K`, and the three-grid packet stopped after A-2. No
documented existing output route has demonstrated enough precision.
`RFL` is described as
concentrated heat sources and does not close the thermal film-integral output
question.

This agrees with the existing packet: A's largest displayed nodal error is
`4.816e-5 K`; the existing result reader could not establish the `1e-7 K`
criterion, and rounded hot/cold heat cannot establish `1e-10 W` balance. The
existing packet explicitly did not execute B/B_strong. See
[`wo03-ccx-thermal-comparison.md`](wo03-ccx-thermal-comparison.md) for the
run identity, observations and retained limitation.

## B and B_strong boundary-input conclusion

The exact required boundary is a continuously varying quadratic Robin law.
Explicit uniform `*FILM` records are constants on assigned element faces;
finite subdivision approximates the continuous law. This can approximate the
same physical boundary condition, but the packet must quantify and budget the
input approximation error before treating it as the unchanged acceptance case.
`FxNUy`/`film.f` is the official CalculiX hook that supplies `h(x)` and
`Tbulk(x)` at each face integration point. `dflux.f` sees the current
temperature and position and may encode the Robin law as a temperature-
dependent flux, but that alternate assembly/iteration route is not verified
here. Both custom hooks require replacing dummy routines and compiling/linking
per the official manual. No source-only plugin or user-routine flag for the
already installed binary is documented.

## Decision for the next packet

**Current executable: the tested `*NODE OUTPUT` temperature path is float32
and inadequate for the unchanged `1e-7 K` criterion; the declared three-grid
probe is incomplete. Custom-film input remains a build prerequisite.** Do not
infer solver qualification from A's successful exit. The A-2 raw output and
framing evidence are in [`wo03-ccx-output-probe.md`](wo03-ccx-output-probe.md).
In parallel, any patchwise film approximation needs an explicit boundary-input
error bound. This note selects no production tool and authorizes no new solve
or actual-baffle attempt.

The installed Homebrew receipt identifies its source as the official
`ccx_2.23.src.tar.bz2` archive and records the formula hash; the formula installs
the archive-built executable but does not retain its source tree. The A-2
probe establishes the actual installed binary's float32 NT/RFL layout from the
preserved FRD records; it does not source-pin every 2.23 selector path. The manual
documents no numeric precision selector. The inspected development main only
parses job-name `-i` and version `-v`; it has no output-precision option, while
the input parser maps `*NODE FILE` to ASCII and `*NODE OUTPUT` to `bin`. This
does not prove the 2.23 archive has identical parser code: the exact 2.23
archive's `frdselect` and main source were not inspected, so the 2.23 double
branch reachability remains unresolved as a source-code question. No CLI or
input selector for that branch was found in the inspected development source
or documented in the manual. No raw solver-state API or runtime
user-subroutine loader was found in the inspected official paths.
