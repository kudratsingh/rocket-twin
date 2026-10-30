"""Collect primary source PDFs and F25 candidate data for offline WO-01 review.

Downloads are archival only: they do not approve a motor or change the baseline.
No automatic retries after access denials; preserve source bytes and provenance.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.wo01_fetch_motors import main as collect_curves


def fetch_pdf(url: str) -> bytes:
    request = Request(
        url,
        headers={
            "User-Agent": "rocket-twin/0.0.1 (motor-data research client)",
            "Accept": "application/pdf",
        },
    )
    with urlopen(request, timeout=20) as response:
        raw = response.read(20_000_001)
    if len(raw) > 20_000_000 or not raw.startswith(b"%PDF-"):
        raise ValueError("response is not a PDF or exceeds 20 MB")
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/studies/motor-selection.yaml"))
    parser.add_argument("--output", type=Path, default=Path("data/motor-study-sources"))
    args = parser.parse_args()
    collection = yaml.safe_load(args.config.read_text())
    sources = collection["sources"]
    args.output.mkdir(parents=True, exist_ok=True)
    results = []
    denied = False
    names = collection.get(
        "pdf_sources",
        ["matrix", "rms_dimensions", "rms_certificate", "old_g25_certificate", "f25_certificate"],
    )
    for name in names:
        path = args.output / (name + ".pdf")
        url = sources[name]
        try:
            if path.exists():
                raw = path.read_bytes()
                if not raw.startswith(b"%PDF-"):
                    raise ValueError(f"invalid existing PDF: {path}")
                status = "cached"
            else:
                if denied:
                    results.append(
                        {"source": name, "url": url, "status": "not_requested_after_denial"}
                    )
                    continue
                raw = fetch_pdf(url)
                path.write_bytes(raw)
                status = "downloaded"
            results.append(
                {
                    "source": name,
                    "url": url,
                    "file": str(path),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                    "status": status,
                    "review_status": "not_yet_reviewed",
                }
            )
            print(f"{name}: {status}, {path}")
        except (OSError, ValueError) as exc:
            results.append({"source": name, "url": url, "status": "failed", "error": str(exc)})
            print(f"{name}: {exc}", file=sys.stderr)
            if isinstance(exc, HTTPError) and exc.code in {401, 403, 429}:
                denied = True
    (args.output / "manifest.json").write_text(
        json.dumps({"updated_at": datetime.now(UTC).isoformat(), "sources": results}, indent=2)
        + "\n"
    )
    # Independent source-curve collection; no certificate/mass acceptance follows.
    curve_args = []
    for candidate in collection.get("curve_candidates", ["AeroTech:F25"]):
        curve_args.extend(["--candidate", candidate])
    curves_code = collect_curves(curve_args) if curve_args else 0
    return int(
        curves_code != 0 or any(r["status"] not in {"cached", "downloaded"} for r in results)
    )


if __name__ == "__main__":
    raise SystemExit(main())
