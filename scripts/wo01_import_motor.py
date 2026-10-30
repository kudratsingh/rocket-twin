"""Import one upstream RASP file byte-for-byte and write a provenance sidecar.

Accepts a local download or a HTTPS ThrustCurve URL. Certification metadata
must be checked against the cited certificate; parsing alone is not certification.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from datetime import UTC, date, datetime
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import urlopen

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.motors import parse_rasp


def import_motor(
    raw: bytes, output: Path, source: str, certificate: str, cert_body: str, cert_date: date
) -> dict[str, object]:
    curve = parse_rasp(raw.decode("utf-8-sig"))
    sidecar: dict[str, object] = {
        "source_url": source,
        "certificate_url": certificate,
        "certification_body": cert_body,
        "certification_date": cert_date.isoformat(),
        "fetched_at": datetime.now(UTC).isoformat(),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "designation": curve.designation,
        "diameter_m": curve.diameter_m,
        "length_m": curve.length_m,
        "propellant_mass_kg": curve.propellant_mass_kg,
        "casing_mass_kg": curve.loaded_mass_kg - curve.propellant_mass_kg,
        "loaded_mass_kg": curve.loaded_mass_kg,
        "total_impulse_ns": curve.total_impulse_ns,
        "burn_time_s": curve.burn_time_s,
        "average_thrust_n": curve.average_thrust_n,
        "validation_status": "imported; certificate correspondence not independently verified",
    }
    if output.exists() or output.with_suffix(".yaml").exists():
        raise FileExistsError("refusing to overwrite an existing curve or provenance sidecar")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Keep all original comments, precision, whitespace and line endings.
    output.write_bytes(raw)
    output.with_suffix(".yaml").write_text(yaml.safe_dump(sidecar, sort_keys=False))
    return sidecar


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", type=Path)
    source.add_argument("--url")
    parser.add_argument("--source-url", required=True, help="upstream provenance page")
    parser.add_argument("--certificate-url", required=True)
    parser.add_argument("--certification-body", choices=["NAR", "TRA", "CAR"], required=True)
    parser.add_argument("--certification-date", type=date.fromisoformat, required=True)
    parser.add_argument("--name", required=True, help="local filename stem, e.g. Estes_F15")
    args = parser.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.name):
        parser.error("--name must be a simple filename stem")
    if args.url:
        parsed = urlparse(args.url)
        if parsed.scheme != "https" or parsed.hostname not in {
            "www.thrustcurve.org",
            "thrustcurve.org",
        }:
            parser.error("--url must use HTTPS on thrustcurve.org")
        with urlopen(args.url, timeout=20) as response:
            raw = response.read(2_000_001)
    else:
        raw = args.file.read_bytes()
    if len(raw) > 2_000_000:
        parser.error("motor file exceeds 2 MB")
    dest = Path("configs/vehicle/motors") / (args.name + ".eng")
    try:
        metadata = import_motor(
            raw,
            dest,
            args.source_url,
            args.certificate_url,
            args.certification_body,
            args.certification_date,
        )
    except (ValueError, FileExistsError) as exc:
        parser.error(str(exc))
    print(f"Imported {dest}: {metadata['total_impulse_ns']:.3f} N s; source bytes preserved")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
