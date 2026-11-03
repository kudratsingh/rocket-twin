"""Read-only local preview diagnostics; never starts a service or runs a simulation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
F2_PATH = "web/public/engineering-workbench/preparedg80-fixed-f2.json"
ROUTES = (
    "/api/health",
    "/api/vehicles",
    "/api/engineering/workbench-g80-fixed",
    "/api/engineering/workbench-g80-f2",
)
FILES = (
    "Makefile",
    "scripts/wo04_preview.sh",
    "scripts/wo04_api.py",
    "web/package.json",
    "web/package-lock.json",
    "web/src/App.tsx",
    "docs/CURRENT.md",
    "docs/wo03-g80-f2-decision.md",
    "configs/vehicle/candidates/g80-f2-ballast.yaml",
)


def command(*args: str) -> str:
    try:
        result = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=5,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"},
            check=False,
        )
        return (
            result.stdout.strip()
            if result.returncode == 0
            else f"unavailable: {result.stderr.strip()}"
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return f"unavailable: {error}"


def response_status(code: int, body: bytes) -> str:
    try:
        detail = json.loads(body).get("detail")
    except (ValueError, AttributeError):
        detail = None
    if code == 404 and detail == "Not Found":
        return "missing-route (exact 404 Not Found)"
    if code == 404:
        return f"source/resource missing (404; detail={detail!r})"
    if code == 409:
        return f"source-error or mismatch (409; detail={detail!r})"
    if code >= 400:
        return f"HTTP error {code} (detail={detail!r})"
    return f"HTTP {code}"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def probe(port: int, path: str) -> tuple[str, bytes | None]:
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", method="GET")
    try:
        with opener.open(request, timeout=2) as response:
            body = response.read(2_000_001)
            if len(body) > 2_000_000:
                return "response too large to inspect", None
            return response_status(response.status, body), body
    except urllib.error.HTTPError as error:
        return response_status(error.code, error.read(4096)), None
    except (urllib.error.URLError, OSError) as error:
        return f"unreachable from this process: {error}", None


def source_status(document: object, root: Path = ROOT) -> list[str]:
    if not isinstance(document, dict):
        return ["source-error: response is not a JSON object"]
    identity, sources = document.get("identity"), document.get("generated_from")
    if not isinstance(identity, dict) or identity.get("candidate_id") != "G80-F2":
        return [f"identity mismatch: expected G80-F2; got {identity!r}"]
    if not isinstance(sources, list) or not sources:
        return ["source-error: no generated_from source list"]
    result = [
        f"identity: {identity.get('source_identity')!r}; spec SHA-256: {identity.get('specification_sha256')!r}; CAD revision: {identity.get('cad_revision')!r}"
    ]
    if not identity.get("source_identity") or identity.get("cad_revision") is not None:
        result.append("identity mismatch: F2 requires a source identity and no full CAD revision")
    spec_sources = [s for s in sources if isinstance(s, dict) and s.get("id") == "spec"]
    if len(spec_sources) != 1 or spec_sources[0].get("sha256") != identity.get(
        "specification_sha256"
    ):
        result.append("identity mismatch: F2 specification hash does not match its source record")
    for source in sources:
        if not isinstance(source, dict):
            result.append("source-error: malformed source record")
            continue
        path, expected = source.get("path"), source.get("sha256")
        if (
            not isinstance(path, str)
            or not isinstance(expected, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
        ):
            result.append(f"source-error: malformed source path/hash: {source!r}")
            continue
        target = (root / path).resolve()
        if not target.is_relative_to(root.resolve()):
            result.append(f"source-error: path outside repository: {path}")
            continue
        try:
            actual = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError as error:
            result.append(f"source-error: {path}: {error}")
            continue
        status = "matching current source" if actual == expected else "mismatch"
        result.append(f"{status}: {path}; expected={expected}; actual={actual}")
    return result


def parse_json(body: bytes | None) -> object | None:
    if body is None:
        return None
    try:
        return json.loads(body)
    except (ValueError, UnicodeDecodeError):
        return None


def main() -> None:
    print("READ-ONLY PREFLIGHT — browser interaction, build and engineering acceptance NOT checked")
    print(f"Repository: {ROOT}")
    print(f"Git HEAD: {command('git', 'rev-parse', 'HEAD')}")
    print(
        f"Git working tree (porcelain; untracked files included):\n{command('git', 'status', '--short') or '(clean)'}"
    )
    node = command("node", "--version")
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", node)
    node_ok = bool(match and int(match[1]) == 22 and int(match[2]) >= 12)
    print(
        f"Node: {node} — {'within project range' if node_ok else 'missing or outside >=22.12.0 <23'}"
    )
    python = ROOT / ".venv/bin/python"
    version = command(str(python), "--version") if python.is_file() else "missing .venv/bin/python"
    print(
        f"Project Python: {version} — {'expected 3.11' if version.startswith('Python 3.11.') else 'missing or outside expected 3.11'}"
    )
    print(
        f"web/node_modules: {'present (dependency correctness not checked)' if (ROOT / 'web/node_modules').is_dir() else 'missing'}"
    )
    for path in FILES:
        print(f"{'present' if (ROOT / path).is_file() else 'missing'}: {path}")
    print("Prepared F2 snapshot (source hashes at inspection time, not a browser or build check):")
    try:
        prepared = json.loads((ROOT / F2_PATH).read_bytes())
        for line in source_status(prepared):
            print(f"  {line}")
    except (OSError, ValueError) as error:
        prepared = None
        print(f"  unavailable or invalid: {error}")
    print(
        "Loopback HTTP probes (from this process only; unreachable does not prove no host listener):"
    )
    status, _ = probe(5173, "/")
    print(f"  127.0.0.1:5173/: {status}; response alone does not identify the running build")
    for route in ROUTES:
        status, body = probe(8000, route)
        print(f"  127.0.0.1:8000{route}: {status}")
        if route == "/api/health" and body is not None:
            health = parse_json(body)
            if (
                not isinstance(health, dict)
                or health.get("status") != "ok"
                or health.get("flight_ready") is not False
            ):
                print("    response mismatch: expected Rocket Twin preview health contract")
            else:
                print("    preview health contract matches; server revision is not established")
        if route == "/api/vehicles" and body is not None:
            catalog = parse_json(body)
            if not isinstance(catalog, dict) or not isinstance(catalog.get("vehicles"), list):
                print("    response mismatch: expected vehicle catalog")
            else:
                for item in catalog["vehicles"]:
                    if isinstance(item, dict):
                        print(
                            f"    {item.get('id')}: available={item.get('available')!r}; reason={item.get('unavailable_reason')!r}; identity={item.get('identity')!r}"
                        )
        if route.endswith("g80-f2") and body is not None:
            api = parse_json(body)
            for line in source_status(api):
                print(f"    {line}")
            if isinstance(api, dict) and isinstance(prepared, dict):
                equal = api.get("identity") == prepared.get("identity") and api.get(
                    "generated_from"
                ) == prepared.get("generated_from")
                print(
                    f"    API vs prepared identity/source list: {'matching' if equal else 'mismatch'}"
                )
    print(
        "Build: not run. Browser/WebGL/interaction: not observed. No service was started or stopped."
    )
    print(
        "Owner commands from repository root: .venv/bin/python scripts/wo04_preview_preflight.py ; make preview"
    )
    print(
        "make preview prepares snapshots and starts services; run it separately in a normal terminal when intended."
    )


if __name__ == "__main__":
    main()
