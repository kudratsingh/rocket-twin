"""CAD-property identity without importing the CAD kernel in the simulator.

Both source geometry and generator implementation invalidate cached properties.
The source revision is fixed for one process; run provenance separately checks
that no source or specification changes during an analysis/flight execution.
"""

import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any


@lru_cache(maxsize=1)
def generator_revision() -> str:
    root = Path(__file__).resolve().parents[1]
    return hashlib.sha256(
        b"".join(
            p.read_bytes()
            for p in [root / "cad/parts.py", root / "vehicle/geometry.py", Path(__file__)]
        )
    ).hexdigest()


def digest(geometry: dict[str, Any], cad: dict[str, Any] | None) -> str:
    return hashlib.sha256(
        json.dumps(
            {"geometry": geometry, "cad": cad, "generator_revision": generator_revision()},
            sort_keys=True,
        ).encode()
    ).hexdigest()
