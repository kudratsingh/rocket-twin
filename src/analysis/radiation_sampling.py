"""Count-weighted reciprocal radiation reconciliation with fixed surface areas.

The independent ray likelihood is product Fij**nij. With Hij=Ai*Fij=Hji,
closure sum_j Hij=Ai, its Lagrange equations give
Fij=(nij+nji)*Aj/(lambda_j*Ai+lambda_i*Aj). Positive multipliers iterate
lambda_i <- lambda_i*sum_j Fij, with damping to avoid two-cycle oscillation.
This retains the sampling precision from unequal source areas/counts, unlike
unweighted averaging of reciprocal exchange-area observations. Union-of-hit
support is explicit: two zero counts never create a visibility edge here.

This is the fixed-stationary-population reversible MLE equation applied to
cosine ray destinations, where stationary populations are proportional to area.
Reference: reseeding-trajectory estimator paper, J. Chem. Phys. 152, 044110
(2020), section II.C equations3–4, https://pmc.ncbi.nlm.nih.gov/articles/PMC7047717/;
Trendelkamp-Schroer et al., Estimation and uncertainty of reversible Markov
models (2015), https://arxiv.org/abs/1507.05990 . This implementation derives
those scalar equations, with no new library or imported implementation.
Convergence and interval compatibility are mandatory independent checks; no
local geometry, spatial convergence or temperature uncertainty bound follows.
"""

from __future__ import annotations

from typing import Any

import numpy as np


def reciprocal_counts(
    hits: Any, areas_m2: Any, *, closure_tolerance: float = 1e-11, max_iterations: int = 20000
) -> tuple[Any, dict[str, Any]]:
    n = np.asarray(hits)
    area = np.asarray(areas_m2, dtype=float)
    if (
        n.ndim != 2
        or n.shape[0] != n.shape[1]
        or area.shape != (len(n),)
        or n.dtype.kind not in "iu"
        or np.any(n < 0)
        or not np.isfinite(area).all()
        or np.any(area <= 0)
        or np.any(n.sum(axis=1) <= 0)
        or not 0 < closure_tolerance < 1
        or max_iterations < 1
    ):
        raise ValueError("Nonnegative integer counts, positive areas and nonempty rows required")
    counts = np.asarray(n, dtype=float)
    sym = counts + counts.T
    ii, jj = np.nonzero(sym)
    weight = sym[ii, jj]
    multipliers = counts.sum(axis=1)
    for iteration in range(max_iterations + 1):
        denominator = multipliers[jj] * area[ii] + multipliers[ii] * area[jj]
        probability = weight * area[jj] / denominator
        row_sum = np.bincount(ii, weights=probability, minlength=len(area))
        error = float(np.max(np.abs(row_sum - 1)))
        if error <= closure_tolerance:
            break
        # Explicit fixed damping, not row renormalization of a returned F.
        multipliers *= (1 + row_sum) / 2
    else:
        raise RuntimeError("Count-weighted reciprocal likelihood did not reach closure")
    result = np.zeros(n.shape)
    result[ii, jj] = probability
    exchange = area[:, None] * result
    raw = counts / counts.sum(axis=1)[:, None]
    observed = counts > 0
    raw_log = float(np.sum(counts[observed] * np.log(raw[observed])))
    fitted_log = float(np.sum(counts[observed] * np.log(result[observed])))
    return result, {
        "method": "fixed-area reversible ray-count likelihood, positive Lagrange multipliers, damping0.5",
        "support": "union of observed directed pairs; no pair with zero counts in both directions",
        "iterations": iteration,
        "max_row_sum_error": error,
        "max_reciprocity_error_m2": float(np.max(np.abs(exchange - exchange.T))),
        "maximum_row_l1_adjustment": float(np.max(np.sum(np.abs(result - raw), axis=1))),
        "ray_likelihood_log_raw_unconstrained": raw_log,
        "ray_likelihood_log_reciprocal": fitted_log,
        "likelihood_deviance_vs_unconstrained": 2 * (raw_log - fitted_log),
        "minimum_multiplier": float(multipliers.min()),
        "maximum_multiplier": float(multipliers.max()),
        "local_geometry_or_temperature_convergence_established": False,
    }
