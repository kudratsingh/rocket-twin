"""Download-only isolated Elmer prerequisites; never install or execute them.

Run from the owner's normal terminal when the agent sandbox cannot resolve the
official hosts. CMake's digest is from the official GitHub release metadata.
The Elmer archive is addressed by a full official commit; its downloaded digest
is recorded, not claimed to be an independently supplied checksum.
"""

from __future__ import annotations

import hashlib
import json
import signal
import time
from datetime import UTC, datetime
from pathlib import Path
from types import FrameType
from urllib.parse import urlsplit, urlunsplit
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / ".cache/elmer-evaluation/downloads"
COMMIT = "a19504ac53ec222e3355e182b08f2ff280c2203a"
FILES = (
    (
        "cmake-3.31.8-macos-universal.tar.gz",
        (
            "https://github.com/Kitware/CMake/releases/download/v3.31.8/"
            "cmake-3.31.8-macos-universal.tar.gz"
        ),
        "d1449f969c54d5c00886d5b643340d493dfb3c81cb39ee29b35453395c11ebf7",
    ),
    (
        f"elmerfem-{COMMIT}.tar.gz",
        f"https://github.com/ElmerCSC/elmerfem/archive/{COMMIT}.tar.gz",
        None,
    ),
)


def timeout(_signum: int, _frame: FrameType | None) -> None:
    raise TimeoutError("Acquisition time cap; partial files preserved")


def main() -> None:
    DEST.mkdir(parents=True, exist_ok=True)
    manifest_path = DEST / "acquisition.json"
    if manifest_path.exists():
        raise SystemExit(f"Existing acquisition retained: {manifest_path}. No automatic retry.")
    start = time.monotonic()
    previous_handler = signal.signal(signal.SIGALRM, timeout)
    record: dict = {
        "started_utc": datetime.now(UTC).isoformat(),
        "scope": "download only; no extraction, installation, build or solver execution",
        "elmer_release": "26.2.1",
        "elmer_commit": COMMIT,
        "per_file_wall_limit_s": 120,
        "total_wall_limit_s": 300,
        "maximum_bytes_per_file": 100 * 1024 * 1024,
        "files": [],
        "status": "running",
    }
    try:
        for name, url, expected in FILES:
            target = DEST / name
            partial = target.with_name(name + ".partial")
            if target.exists() or partial.exists():
                raise FileExistsError(f"Preserving existing {name}; no overwrite or retry")
            attempt_start = time.monotonic()
            item = {
                "name": name,
                "url": url,
                "expected_sha256": expected,
                "status": "started",
            }
            record["files"].append(item)
            manifest_path.write_text(json.dumps(record, indent=2) + "\n")
            digest, count = hashlib.sha256(), 0
            print(f"Downloading {name}", flush=True)
            signal.setitimer(signal.ITIMER_REAL, min(120.0, 300.0 - (attempt_start - start)))
            with urlopen(url, timeout=15) as response, partial.open("xb") as output:
                # Release redirects can carry temporary credentials. Preserve
                # the public origin/path without persisting its signed query.
                resolved = urlsplit(response.url)
                item["resolved_url"] = urlunsplit(
                    (resolved.scheme, resolved.netloc, resolved.path, "", "")
                )
                while chunk := response.read(1024 * 1024):
                    elapsed = time.monotonic()
                    if elapsed - attempt_start > 120 or elapsed - start > 300:
                        raise TimeoutError("Acquisition time cap; partial files preserved")
                    if count == 0 and chunk[:2] != b"\x1f\x8b":
                        raise ValueError("Response is not a gzip archive")
                    count += len(chunk)
                    if count > record["maximum_bytes_per_file"]:
                        raise ValueError("Archive exceeds declared size cap")
                    output.write(chunk)
                    digest.update(chunk)
            actual = digest.hexdigest()
            item.update(bytes=count, sha256=actual, wall_seconds=time.monotonic() - attempt_start)
            if count == 0 or (expected is not None and actual != expected):
                raise ValueError("Empty archive or checksum mismatch; partial file preserved")
            partial.rename(target)
            item["status"] = (
                "official_checksum_verified" if expected else "commit_addressed_digest_recorded"
            )
            signal.setitimer(signal.ITIMER_REAL, 0)
        record["status"] = "downloaded_not_installed_or_qualified"
    except Exception as error:
        record.update(status="failed_preserved", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
        record["wall_seconds"] = time.monotonic() - start
        manifest_path.write_text(json.dumps(record, indent=2) + "\n")
    print(f"Saved {manifest_path}. No archives were extracted or executed.")


if __name__ == "__main__":
    main()
