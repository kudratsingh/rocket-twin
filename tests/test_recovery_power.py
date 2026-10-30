"""Resolved modes must not override the dedicated recovery supply with main VBAT."""

from pathlib import Path

from src.vehicle.schema import load_vehicle


def test_resolved_recovery_supply_and_return_are_independent() -> None:
    paths = [
        Path("configs/vehicle/platform") / name
        for name in ["performance.yaml", "tvc-finned.yaml", "tvc-finless.yaml"]
    ] + list(Path("configs/vehicle/wo02").glob("*.yaml"))
    expected = {
        "RECOVERY_BAT_POS": ("recovery_battery", "recovery_power_switch"),
        "RECOVERY_ARMED_POS": ("recovery_power_switch", "independent_recovery"),
        "RECOVERY_RETURN": ("recovery_battery", "independent_recovery"),
        "RECOVERY_OUTPUT_BUNDLE": ("independent_recovery", "recovery_output_harness"),
    }
    for path in paths:
        vehicle = load_vehicle(path)
        nets = {net.net: (net.source, net.to) for net in vehicle.netlist}
        assert "RECOVERY_INDEPENDENT" not in nets
        assert {name: nets[name] for name in expected} == expected
        graph: dict[str, set[str]] = {}
        for net in vehicle.netlist:
            for target in [net.to] if isinstance(net.to, str) else net.to:
                graph.setdefault(net.source, set()).add(target)
                graph.setdefault(target, set()).add(net.source)
        reached = {"independent_recovery"}
        frontier = list(reached)
        while frontier:
            node = frontier.pop()
            for target in graph.get(node, set()) - reached:
                reached.add(target)
                frontier.append(target)
        assert not reached & {
            "battery",
            "regulator_5v",
            "flight_computer",
            "servo_pitch",
            "servo_yaw",
        }
