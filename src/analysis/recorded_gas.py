"""Hash-checked offline reduced gas response, without pretending to store a field.

The original factorization owns the geometry/physics checks and field probes.
This reader permits repeated transient calculations using its exact reduced
matrices and ordered identities. A reduced operator cannot reconstruct an
arbitrary new spatial field; that operation remains unavailable. No arrays are
clipped, symmetrized or repaired here. Units/signs follow robin_gas.py.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

import numpy as np


class GasResponse(Protocol):
    @property
    def group_ids(self) -> tuple[int, ...]: ...

    @property
    def bulk_ids(self) -> tuple[str, ...]: ...

    @property
    def prescribed_ids(self) -> tuple[str, ...]: ...

    @property
    def group_areas_m2(self) -> Any: ...

    @property
    def mean_by_reservoir_temperature(self) -> Any: ...

    @property
    def mean_by_group_neumann_k_w(self) -> Any: ...

    @property
    def reservoir_conductance_raw_w_k(self) -> Any: ...

    @property
    def reservoir_heat_by_group_neumann(self) -> Any: ...

    @property
    def diagnostics(self) -> dict[str, Any]: ...

    def evaluate(
        self, bulk_temperature_k: Any, prescribed_temperature_k: Any, group_neumann_w: Any
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class RecordedGasResponse:
    group_ids: tuple[int, ...]
    bulk_ids: tuple[str, ...]
    prescribed_ids: tuple[str, ...]
    group_areas_m2: Any
    mean_by_reservoir_temperature: Any
    mean_by_group_neumann_k_w: Any
    reservoir_conductance_raw_w_k: Any
    reservoir_heat_by_group_neumann: Any
    diagnostics: dict[str, Any]
    provenance: dict[str, Any]

    @classmethod
    def load(
        cls, operator: Path, state_metadata: Path, *, operator_sha256: str, metadata_sha256: str
    ) -> RecordedGasResponse:
        for path, expected in ((operator, operator_sha256), (state_metadata, metadata_sha256)):
            if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
                raise ValueError("Recorded gas response or state metadata hash changed")
        meta = json.loads(state_metadata.read_bytes())
        gids = tuple(int(i) for i in meta["group_ids"])
        bulk = tuple(str(i) for i in meta["bulk_ids"])
        prescribed = tuple(str(i) for i in meta["prescribed_ids"])
        if (
            not gids
            or len(set(gids)) != len(gids)
            or sorted(gids) != list(gids)
            or len(set(bulk)) != len(bulk)
            or len(set(prescribed)) != len(prescribed)
            or not bulk
            or not prescribed
        ):
            raise ValueError(
                "Unique, ordered recorded surface/material/reservoir identities required"
            )
        ng, nr = len(gids), len(bulk) + len(prescribed)
        shapes = {
            "group_areas_m2": (ng,),
            "mean_by_reservoir_temperature": (ng, nr),
            "mean_by_group_neumann_k_w": (ng, ng),
            "reservoir_conductance_raw_w_k": (nr, nr),
            "reservoir_heat_by_group_neumann": (nr, ng),
        }
        arrays = {}
        with np.load(operator, allow_pickle=False) as data:
            for name, shape in shapes.items():
                value = np.asarray(data[name], dtype=float).copy()
                if value.shape != shape or not np.isfinite(value).all():
                    raise ValueError(
                        "Recorded gas matrix is missing, nonfinite or has wrong state shape"
                    )
                value.flags.writeable = False
                arrays[name] = value
        if np.any(arrays["group_areas_m2"] <= 0):
            raise ValueError("Every recorded gas surface needs positive area")
        diagnostics = dict(meta["diagnostics"])
        if not diagnostics.get("algebra_checks_pass"):
            raise ValueError("Source factorization algebra checks did not pass")
        diagnostics["spatial_field_reconstruction_from_reduced_cache"] = "unavailable"
        return cls(
            gids,
            bulk,
            prescribed,
            **arrays,
            diagnostics=diagnostics,
            provenance={
                "source_metadata": meta,
                "operator_sha256": operator_sha256,
                "metadata_sha256": metadata_sha256,
                "raw_matrices_repaired_or_clipped": False,
            },
        )

    def evaluate(
        self, bulk_temperature_k: Any, prescribed_temperature_k: Any, group_neumann_w: Any
    ) -> dict[str, Any]:
        raise ValueError(
            "Spatial gas/surface reconstruction is unavailable from reduced matrices alone; "
            "reload the original mesh/factor and exact boundary conditions."
        )
