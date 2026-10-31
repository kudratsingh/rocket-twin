"""Actual through-openings and separate panels must survive CAD postprocessing."""

import math
from pathlib import Path

import cadquery as cq
import yaml

from scripts.wo03_baffle_fit import baffle_shape
from src.vehicle.schema import Part


def test_export_geometry_has_real_notches_seams_and_support_bearing() -> None:
    cfg = yaml.safe_load(Path("configs/studies/wo03-baffle-fit.yaml").read_text())["geometry"]
    part = Part.model_validate(
        {
            "estimate": True,
            "id": "test_baffle",
            "type": "commercial",
            "parent": None,
            "position_m": 0,
            "mass_kg": 0.001,
            "material": "aluminum",
            "learn": "Synthetic geometry fixture; not a candidate or measured hardware.",
            "geometry": {
                "length_m": cfg["foil_wall_m"],
                "radius_m": cfg["baffle_outer_radius_m"],
                "inner_radius_m": cfg["baffle_clearance_opening_radius_m"],
            },
            "cad": {
                "generator": "liner",
                "mass_basis": "volume_density",
                "role": "manufactured",
                "notes": "Synthetic baffle fixture",
            },
        }
    )
    mount = part.model_copy(deep=True)
    mount.id = "fixture_mount"
    mount.cad.parameters = {
        "rail_depth_mm": 7,
        "rail_width_mm": 12,
        "rail_radius_mm": 28.5,
        "retainer_blocks": [
            {"size_mm": [12, 12, 20], "position_mm": [25.5, 0, 190], "angle_deg": a}
            for a in (60, 180, 300)
        ],
    }
    shape = baffle_shape(part, mount, cfg)
    assert shape.isValid()
    assert len(shape.Solids()) == 3

    def inside(radius_mm: float, angle_deg: float) -> bool:
        a = math.radians(angle_deg)
        return shape.isInside(
            cq.Vector(radius_mm * math.cos(a), radius_mm * math.sin(a), 0.010), 1e-7
        )

    assert not inside(24.5, 0)  # rail keep-out
    assert not inside(22, 60)  # actual integral-block clearance opening
    assert not inside(20, 90)  # real through seam
    assert inside(24.15, 30)  # retained material under the mica support
