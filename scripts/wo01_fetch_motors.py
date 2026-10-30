"""Download candidate motor records for offline review; does not approve a motor.

Uses the official ThrustCurve search/download JSON APIs, also exercised by
RocketPy 1.13.0's GenericMotor._call_thrustcurve_api. Raw RASP bytes are decoded
from the response, saved unchanged, and hashed. All results are retained to avoid
silently choosing the wrong motor variant. Data stays in ignored data/ until review.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.vehicle.motors import parse_rasp

API = "https://www.thrustcurve.org/api/v1"
CANDIDATES = [("Estes", "F15"), ("AeroTech", "F10"), ("AeroTech", "G25")]


class APIRequestError(RuntimeError):
    def __init__(self, message: str, diagnostic: dict[str, Any]):
        super().__init__(message)
        self.diagnostic = diagnostic


def request_json(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Use the documented JSON POST interface; never retry access denials.

    Record a bounded error-body excerpt and selected nonsensitive response headers.
    Do not store cookies or bypass authentication/bot challenges.
    """
    request = Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "User-Agent": "rocket-twin/0.0.1 (motor-data research client)",
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read(5_000_001)
    except HTTPError as exc:
        with exc:
            excerpt = exc.read(4096).decode("utf-8", errors="replace")
        diagnostic = {
            "url": url,
            "method": "POST",
            "request_body": payload,
            "http_status": exc.code,
            "reason": str(exc.reason),
            "response_headers": {
                key: exc.headers[key]
                for key in ["Server", "Content-Type", "CF-Ray", "Retry-After", "X-Cache"]
                if exc.headers is not None and exc.headers.get(key) is not None
            },
            "response_body_excerpt": excerpt,
            "note": "Bounded diagnostic only. No cookies or auth tokens recorded.",
        }
        raise APIRequestError(f"HTTP {exc.code} {exc.reason} from {url}", diagnostic) from exc
    if len(raw) > 5_000_000:
        raise ValueError("API response exceeds 5 MB")
    try:
        result = json.loads(raw)
    except (ValueError, UnicodeError) as exc:
        raise APIRequestError(
            "API returned a non-JSON response",
            {
                "url": url,
                "method": "POST",
                "request_body": payload,
                "response_body_excerpt": raw[:4096].decode("utf-8", errors="replace"),
            },
        ) from exc
    if not isinstance(result, dict):
        raise TypeError("API response must be an object")
    if result.get("errors"):
        raise APIRequestError(
            "API reported an error",
            {
                "url": url,
                "method": "POST",
                "request_body": payload,
                "api_errors": result["errors"],
            },
        )
    return result


def save_downloads(
    directory: Path, source_url: str, response: dict[str, Any]
) -> list[dict[str, Any]]:
    """Retain every valid RASP response with explicit unreviewed provenance."""
    directory.mkdir(parents=True, exist_ok=True)
    inventory = []
    for result in response.get("results", []):
        encoded = result.get("data")
        if not encoded:
            continue
        raw = base64.b64decode(encoded, validate=True)
        curve = parse_rasp(raw.decode("utf-8-sig"))
        digest = hashlib.sha256(raw).hexdigest()
        dest = directory / (digest + ".eng")
        dest.write_bytes(raw)
        inventory.append(
            {
                "file": str(dest),
                "sha256": digest,
                "designation": curve.designation,
                "length_m": curve.length_m,
                "loaded_mass_kg": curve.loaded_mass_kg,
                "propellant_mass_kg": curve.propellant_mass_kg,
                "average_thrust_n": curve.average_thrust_n,
                "burn_time_s": curve.burn_time_s,
                "total_impulse_ns": curve.total_impulse_ns,
                "source_url": source_url,
                "api_metadata": {k: v for k, v in result.items() if k != "data"},
                "review_status": "unreviewed; not approved for the vehicle spec",
            }
        )
    if not inventory:
        raise ValueError("API returned no usable RASP files")
    (directory / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n")
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/motor-downloads"))
    parser.add_argument(
        "--candidate",
        action="append",
        choices=["Estes:F15", "AeroTech:F10", "AeroTech:G25", "AeroTech:F25", "AeroTech:F22"],
        help="fetch only these manufacturer:name records; repeat as needed",
    )
    args = parser.parse_args(argv)
    candidates = (
        [tuple(value.split(":")) for value in args.candidate] if args.candidate else CANDIDATES
    )
    failed = False
    for manufacturer, name in candidates:
        destination = args.output / (manufacturer + "_" + name)
        destination.mkdir(parents=True, exist_ok=True)
        try:
            search_url = API + "/search.json"
            search_request = {"manufacturer": manufacturer, "commonName": name}
            search = request_json(search_url, search_request)
            (destination / "search.json").write_text(json.dumps(search, indent=2) + "\n")
            motors = search.get("results", [])
            if not motors:
                raise ValueError("no matching motor records")
            # The search response is retained for certification dates, dimensions,
            # manufacturer and variant reconciliation during offline review.
            ids = [str(m["motorId"]) for m in motors]
            download_url = API + "/download.json"
            download_request = {"motorIds": ids, "format": "RASP", "data": "file"}
            response = request_json(download_url, download_request)
            (destination / "download.json").write_text(json.dumps(response, indent=2) + "\n")
            inventory = save_downloads(destination, download_url, response)
            (destination / "request.json").write_text(
                json.dumps(
                    {
                        "fetched_at": datetime.now(UTC).isoformat(),
                        "search_url": search_url,
                        "search_request": search_request,
                        "method": "POST",
                        "download_url": download_url,
                        "download_request": download_request,
                    },
                    indent=2,
                )
                + "\n"
            )
            print(f"{manufacturer} {name}: {len(inventory)} source file(s) saved for review")
        except APIRequestError as exc:
            diagnostic = destination / "error.json"
            diagnostic.write_text(json.dumps(exc.diagnostic, indent=2) + "\n")
            print(f"{manufacturer} {name}: {exc}. Diagnostic: {diagnostic}", file=sys.stderr)
            failed = True
            if exc.diagnostic.get("http_status") in {401, 403, 429}:
                print(
                    "Stopping requests to this host after access denial or rate limiting.",
                    file=sys.stderr,
                )
                break
        except (OSError, URLError, ValueError, TypeError, KeyError) as exc:
            print(f"{manufacturer} {name}: download failed: {exc}", file=sys.stderr)
            failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
