"""Actual assemblies reproduce cached mass properties and printable orientations."""

from pathlib import Path

import numpy as np
import pytest
from pydantic import ValidationError

pytest.importorskip("cadquery")
from src.cad.assembly import export_vehicle, print_layout, rigid_intersections
from src.vehicle.schema import Part, load_vehicle


@pytest.mark.parametrize("name", ["performance", "tvc-finned", "tvc-finless"])
def test_actual_assembly_cache_solids_and_print_bed(name: str, tmp_path: Path) -> None:
    v = load_vehicle("configs/vehicle/platform/" + name + ".yaml")
    report, solids = export_vehicle(v, tmp_path / v.id, False)
    assert report["mass_benchmark_passed"] and report["print_volume_passed"]
    assert all(p["valid_solid"] for p in report["parts"])
    assert not rigid_intersections(v, solids)
    for p, row in zip(v.parts, report["parts"]):
        assert p.cad_mass
        np.testing.assert_allclose(
            p.cad_mass.cg_local_body_m, row["properties"]["cg_local_body_m"], atol=1e-10
        )
        np.testing.assert_allclose(
            p.cad_mass.inertia_per_kg_m2, row["properties"]["inertia_per_kg_m2"], atol=1e-12
        )
        assert np.linalg.eigvalsh(p.inertia_per_kg_m2).min() > 0
    nose = next(p for p in v.parts if p.id == "nose_cone")
    assert nose.print_settings
    from src.cad.parts import local_shape

    oriented, _ = print_layout(local_shape(nose), nose.print_settings.rotation_deg)
    assert abs(oriented.BoundingBox().zmin) < 1e-5
    # Stale geometry must not silently reuse old CAD inertia in flight or Analysis.
    part = next(p for p in v.parts if p.id == "aft_shell")
    data = part.model_dump(by_alias=True)
    data["geometry"]["length_m"] += 0.001
    with pytest.raises(ValidationError, match="stale CAD"):
        Part.model_validate(data)
