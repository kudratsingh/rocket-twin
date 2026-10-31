"""Exercise the wrench reference-point transform independently of CAD."""

from scripts.wo03_fin_load_routing import known_case, move


def test_force_moment_transport_and_round_trip():
    assert known_case()["passed"]
    force = [0.0, 10.0, 0.0]
    tangent = [0.033, 0.0, 1.115]
    axis = [0.0, 0.0, 1.115]
    moment = move(force, [0.0, 0.0, 2.0], tangent, axis)
    assert abs(moment[2] - 2.33) < 1e-12
    assert abs(move(force, moment, axis, tangent)[2] - 2.0) < 1e-12
