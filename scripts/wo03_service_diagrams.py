"""Render preliminary service/station diagrams from a resolved vehicle YAML."""

from __future__ import annotations

import argparse
import html
import sys
from pathlib import Path

import yaml
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.schema import load_vehicle


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/platform.yaml"))
    parser.add_argument("--preset", choices=["tiny", "sim"], default="tiny")
    parser.add_argument("--vehicle", help="resolved vehicle id; defaults to first platform mode")
    args = parser.parse_args()
    platform = yaml.safe_load(args.config.read_text())
    paths = platform["vehicles"]
    selected = None
    for path in paths:
        vehicle = load_vehicle(path)
        if args.vehicle is None or vehicle.id == args.vehicle:
            selected = vehicle
            break
    if selected is None:
        parser.error(f"Unknown vehicle: {args.vehicle}")

    parts = {part.id: part for part in selected.parts}
    x0, scale = 100, 1300 / selected.airframe["length_m"]

    def x(station: float) -> float:
        return x0 + station * scale

    def label(text: str, px: float, py: float, size: int = 18, anchor: str = "middle") -> str:
        return f'<text x="{px:.1f}" y="{py:.1f}" font-size="{size}" text-anchor="{anchor}">{html.escape(text)}</text>'

    elements = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="740" viewBox="0 0 1500 740">',
        '<rect width="100%" height="100%" fill="#fbfcfe"/>',
        "<style>text{font-family:Arial,sans-serif;fill:#172b3a}.small{font-size:14px}.thin{stroke:#526b7b;stroke-width:2;fill:none}.dash{stroke-dasharray:8 6}</style>",
        label(f"Preliminary service stations | {selected.id}", 750, 42, 26),
        label(
            "Station values from resolved YAML; schematic envelopes, not measured fit or packing",
            750,
            70,
            16,
        ),
    ]

    def extent(part_id: str) -> tuple[float, float]:
        p = parts[part_id]
        length = p.geometry.get("length_m", 0.0)
        return p.position_m, p.position_m + length

    separation = float(platform["interface"]["aft_separation_station_m"])
    end = selected.airframe["length_m"]
    elements.append(
        f'<rect x="{x(separation):.1f}" y="260" width="{x(end) - x(separation):.1f}" height="80" fill="#dce4ed" stroke="#334e5c" stroke-width="2"/>'
    )

    # Airframe silhouette is derived from named spec parts where present.
    for pid, caption, color in [
        ("nose_cone", "Nose / recovery", "#dce6ee"),
        ("body_upper", "Upper bay", "#e9d8b5"),
        ("interface_coupler", "Keyed coupler", "#a9c7c9"),
    ]:
        if pid not in parts:
            continue
        a, b = extent(pid)
        px, pw = x(a), max(3, x(b) - x(a))
        elements.append(
            f'<rect x="{px:.1f}" y="260" width="{pw:.1f}" height="80" rx="4" fill="{color}" stroke="#334e5c" stroke-width="2"/>'
        )
        elements.append(label(caption, px + pw / 2, 250, 15))
    for pid, caption, color in [
        ("motor_mount", "Aft mount envelope", "#b6c7da"),
        ("motor", "Motor envelope", "#e3a17e"),
    ]:
        if pid not in parts:
            continue
        a, b = extent(pid)
        elements.append(
            f'<rect x="{x(a):.1f}" y="274" width="{x(b) - x(a):.1f}" height="52" fill="{color}" stroke="#334e5c"/>'
        )
        elements.append(label(caption, (x(a) + x(b)) / 2, 392 if pid == "motor" else 410, 15))
    for pid, caption, color in [
        ("recovery_bulkhead", "Recovery barrier (station)", "#a15b45"),
        ("avionics_bay", "Avionics bay / removable sled access", "#51828b"),
        ("battery", "Battery envelope", "#c89c39"),
    ]:
        if pid not in parts:
            continue
        p = parts[pid]
        length = p.geometry.get("length_m", 0.012)
        if "bbox_m" in p.geometry:
            length = p.geometry["bbox_m"][0]
        a, b = p.position_m, p.position_m + length
        yy = 185 if pid == "recovery_bulkhead" else (210 if pid == "avionics_bay" else 225)
        elements.append(
            f'<line x1="{x(a):.1f}" y1="{yy}" x2="{x(b):.1f}" y2="{yy}" stroke="{color}" stroke-width="8"/>'
        )
        elements.append(
            f'<line x1="{x(a):.1f}" y1="{yy}" x2="{x(a):.1f}" y2="340" stroke="{color}" stroke-dasharray="4 4"/>'
        )
        elements.append(label(caption, (x(a) + x(b)) / 2, yy - 12, 14))
    # Station ruler sourced from all resolved physical part positions.
    elements += [f'<line x1="{x(0):.1f}" y1="465" x2="{x(end):.1f}" y2="465" class="thin"/>']
    major = {
        0.0,
        parts["nose_cone"].geometry["length_m"],
        separation,
        parts["interface_coupler"].position_m,
        parts["motor_mount"].position_m,
        end,
    }
    for value in sorted(major):
        elements.append(
            f'<line x1="{x(value):.1f}" y1="457" x2="{x(value):.1f}" y2="473" class="thin"/>'
        )
        elements.append(label(f"{value:.3f}", x(value), 494, 12))
    elements.append(
        label(
            "Station from nose datum (m); part starts shown, interval labels are nominal spec envelopes",
            750,
            522,
            14,
        )
    )
    # Service actions and direction arrows.
    elements += [
        '<defs><marker id="arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#244f68"/></marker></defs>',
        f'<line x1="{x(0) - 20:.1f}" y1="560" x2="{x(end) + 30:.1f}" y2="560" stroke="#244f68" stroke-width="3" marker-end="url(#arrow)"/>',
        label(
            "Motor insert / withdraw toward aft (right); verify retention and actual clearance",
            750,
            550,
            14,
        ),
        f'<line x1="{x(separation):.1f}" y1="620" x2="{x(end):.1f}" y2="620" stroke="#744f91" stroke-width="3" marker-end="url(#arrow)"/>',
        label(
            "Aft module exchange: separate at keyed joint; hardware, access and proof load unresolved",
            750,
            610,
            14,
        ),
        f'<line x1="{x(0.45):.1f}" y1="690" x2="{x(0.25):.1f}" y2="690" stroke="#16836b" stroke-width="3" marker-end="url(#arrow)"/>',
        label(
            "Sled / battery service access direction is preliminary; withdraw after adjacent modules open",
            750,
            680,
            14,
        ),
        label(
            "Recovery repack: access through nose end; direction and packed envelope require physical mock-up",
            750,
            720,
            13,
        ),
        "</svg>",
    ]
    svg = "\n".join(elements) + "\n"
    out = Path("build") / selected.id / "service"
    out.mkdir(parents=True, exist_ok=True)
    (out / "stations.svg").write_text(svg)
    # Render a matching PNG using Pillow so this output has no optional SVG runtime.
    image = Image.new("RGB", (1500, 740), "#fbfcfe")
    draw = ImageDraw.Draw(image)
    draw.text(
        (750, 24), f"Preliminary service stations | {selected.id}", fill="#172b3a", anchor="mm"
    )
    draw.text(
        (750, 52),
        "Resolved YAML envelopes; schematic only, no measured fit or recovery packing",
        fill="#172b3a",
        anchor="mm",
    )
    colors = {"nose_cone": "#dce6ee", "body_upper": "#e9d8b5", "interface_coupler": "#a9c7c9"}
    for pid, caption, color in [
        ("nose_cone", "Nose / recovery", colors["nose_cone"]),
        ("body_upper", "Upper bay", colors["body_upper"]),
        ("interface_coupler", "Keyed coupler", colors["interface_coupler"]),
    ]:
        if pid in parts:
            a, b = extent(pid)
            draw.rectangle((x(a), 260, x(b), 340), fill=color, outline="#334e5c", width=2)
            draw.text(((x(a) + x(b)) / 2, 245), caption, fill="#172b3a", anchor="mm")
    separation = float(platform["interface"]["aft_separation_station_m"])
    aft_end = max(p.position_m + p.geometry.get("length_m", 0.0) for p in selected.parts)
    draw.rectangle(
        (x(separation), 260, x(aft_end), 340), fill="#dce4ed", outline="#334e5c", width=2
    )
    draw.text(
        ((x(separation) + x(aft_end)) / 2, 245),
        "Exchangeable aft module envelope",
        fill="#172b3a",
        anchor="mm",
    )
    for pid, caption, color in [
        ("motor_mount", "Aft mount envelope", "#b6c7da"),
        ("motor", "Motor envelope", "#e3a17e"),
    ]:
        if pid in parts:
            a, b = extent(pid)
            draw.rectangle((x(a), 274, x(b), 326), fill=color, outline="#334e5c")
            draw.text(
                ((x(a) + x(b)) / 2, 395 if pid == "motor" else 410),
                caption,
                fill="#172b3a",
                anchor="mm",
            )
    for pid, caption, color, yy in [
        ("recovery_bulkhead", "Recovery barrier", "#a15b45", 185),
        ("avionics_bay", "Sled / avionics bay", "#51828b", 210),
        ("battery", "Battery envelope", "#c89c39", 230),
    ]:
        if pid in parts:
            p = parts[pid]
            length = p.geometry.get("length_m", p.geometry.get("bbox_m", (0.012,))[0])
            draw.line((x(p.position_m), yy, x(p.position_m + length), yy), fill=color, width=8)
            draw.line((x(p.position_m), yy, x(p.position_m), 340), fill=color, width=1)
            draw.text(
                ((x(p.position_m) + x(p.position_m + length)) / 2, yy - 12),
                caption,
                fill="#172b3a",
                anchor="mm",
            )
    draw.line((x(0), 465, x(end), 465), fill="#526b7b", width=2)
    major = {
        0.0,
        parts["nose_cone"].geometry["length_m"],
        separation,
        parts["interface_coupler"].position_m,
        parts["motor_mount"].position_m,
        aft_end,
    }
    for value in sorted(major):
        draw.line((x(value), 457, x(value), 473), fill="#526b7b", width=2)
        draw.text((x(value), 486), f"{value:.3f}", fill="#172b3a", anchor="mm")
    draw.text(
        (750, 515),
        "Station from nose datum (m); start positions and nominal envelopes",
        fill="#172b3a",
        anchor="mm",
    )
    for yy, txt, color, direction in [
        (
            560,
            "Motor insert / withdraw toward aft (right); retention and clearance unverified",
            "#244f68",
            "right",
        ),
        (
            620,
            "Aft module exchange at keyed joint; hardware/access/proof load unresolved",
            "#744f91",
            "right",
        ),
        (
            675,
            "Sled service access after adjacent modules open; direction preliminary",
            "#16836b",
            "left",
        ),
    ]:
        draw.line((x(0.25), yy, x(0.72), yy), fill=color, width=3)
        tip = x(0.72) if direction == "right" else x(0.25)
        sign = 1 if direction == "right" else -1
        draw.polygon(((tip, yy), (tip - sign * 10, yy - 6), (tip - sign * 10, yy + 6)), fill=color)
        draw.text((750, yy - 13), txt, fill="#172b3a", anchor="mm")
    draw.text(
        (750, 720),
        "Recovery access from nose end; packed envelope and repack path require mock-up",
        fill="#172b3a",
        anchor="mm",
    )
    image.save(out / "stations.png")
    print(out / "stations.svg")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
