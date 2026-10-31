# Common-surface gas and radiation verification

The offline coupling now solves gas conduction, finite solid half walls and
radiation at the same surface temperatures. It does not add a legacy air-gap
path in parallel. Opening gas temperature and radiative surroundings are
independent inputs. No active vehicle geometry, material limit or requirement
changed.

The method uses the verified Robin finite-element gas reduction. Its area-mean
surface temperatures satisfy `s = G θ + R q`, while material and prescribed-gas
heat is `H = −K θ + J q`. The diffuse-gray operator supplies the radiative load
`q(s)`. A damped Newton solve, with analytic derivatives, closes this common
surface system. A missing interface classification stops assembly.

The current radiation projection uses group area-mean temperature to the fourth
power and distributes each group's heat uniformly by area. This is an explicit
approximation: the fourth power of a mean is generally different from the mean
of fourth powers. Full gas/surface field reconstruction reports both and a
changed integrated-radiation diagnostic. Neither a gas mesh node nor a part mean
is automatically a qualified local solid hot spot. Raw finite-element couplings
are not clipped into a positive pairwise network.

Executed record:
`runs/wo03-gas-radiation-20261031T051417456778Z/record.json`.
Three conforming slab meshes contain 6 / 48 / 384 tetrahedra. An independent
scalar energy balance combines Fourier air conduction and gray parallel-plate
radiation, with both finite wall resistances. Expected transfer is
0.233288210840920 W. Maximum solver error is 3.86e-15 W; maximum energy imbalance
is below 3e-15 W. The affine fixture is exactly representable on each mesh;
its agreement checks implementation, not convergence of the rocket's irregular
fields. Central-difference heat-derivative comparisons also pass.

A separate black-opening fixture keeps all gas opening nodes at 300 K while its
radiative brightness is 500 K. Its heat entering, leaving and reservoir transfer
balances to 1.11e-16 W. This prevents an aperture brightness assumption from
silently heating the gas boundary by the same amount.

Run from the repository root:

```sh
.venv/bin/python scripts/wo03_gas_radiation.py --preset tiny
.venv/bin/python -m pytest tests/test_gas_radiation.py -q
```

The recorded input/source snapshot is authoritative for these numbers. Later
Robin API development retains backward-compatible simple fixtures but requires
a fresh record before claiming exact-current reproducibility. These checks cost
$0 on local CPU. Actual fitting-baffle gas meshing, complete material paths,
spatial/projection uncertainty and required burn/soak matrix results remain
WO-03 design acceptance items. No physical-build or flight gate is cleared.
