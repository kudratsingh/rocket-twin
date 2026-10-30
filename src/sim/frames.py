"""Shared convention: body +x noseward, +z down, +y completes right-handed triad.

Model world: north-east-down (NED). Full scale world: ECI (ADR-0005).
Quaternions: scalar-first (w, x, y, z), body to world rotation.
Spec stations are metres aft from nose tip: body x = CG station - part station.
"""

BODY_FORWARD = "+x"
BODY_DOWN = "+z"
QUATERNION_ORDER = "wxyz"
WORLD_BY_SCALE = {"model": "NED", "full": "ECI"}
STANDARD_GRAVITY_M_S2 = 9.80665
