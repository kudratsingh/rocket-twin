"""Bounded native offline SVG image-document rendering, never browser/UI automation.

Uses only installed documented AppKit NSImage/NSBitmapImageRep APIs. No
NSApplication, window, WebView, install, private CoreSVG API or physics solver.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUN = ROOT / "runs/wo04-offline-render-feasibility-20261102-v4"
OUTPUT = ROOT / "output/engineering-walkthrough-rendered"
SOURCE = ROOT / "output/engineering-walkthrough"
SWIFT = r"""
import AppKit
import Foundation
let args = CommandLine.arguments
print("SVG_registered=" + String(NSImage.imageTypes.contains("public.svg-image")))
guard args.count == 3 else { fputs("Expected SVG input and PNG output\n", stderr); exit(2) }
guard let image = NSImage(contentsOfFile: args[1]) else {
    fputs("NSImage could not create a supported representation from this SVG document\n", stderr)
    exit(3)
}
var bounds = NSRect(origin: .zero, size: image.size)
guard let cgImage = image.cgImage(forProposedRect: &bounds, context: nil, hints: nil) else {
    fputs("NSImage representation did not produce a CGImage snapshot\n", stderr)
    exit(4)
}
let bitmap = NSBitmapImageRep(cgImage: cgImage)
guard let png = bitmap.representation(using: .png, properties: [:]) else { exit(5) }
do {
    try png.write(to: URL(fileURLWithPath: args[2]))
    print("PNG_dimensions=" + String(cgImage.width) + "x" + String(cgImage.height))
} catch { fputs("PNG write failed: \(error)\n", stderr); exit(6) }
"""


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    started = time.monotonic()
    RUN.mkdir(parents=True, exist_ok=True)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    swift_path = RUN / "native_image_document.swift"
    swift_path.write_text(SWIFT)
    manifest = json.loads((SOURCE / "source-manifest.json").read_text())
    for artifact in manifest["artifacts"]:
        assert digest(ROOT / artifact["path"]) == artifact["sha256"]
    # A new AppKit document-snapshot path, materially different from sips/QuickLook.
    source = SOURCE / "01-arrangement-side.svg"
    destination = OUTPUT / "01-arrangement-side.png"
    command = [
        "/usr/bin/swift",
        "-module-cache-path",
        str(RUN / "swift-module-cache"),
        str(swift_path),
        str(source),
        str(destination),
    ]
    attempt: dict = {
        "candidate": "documented_AppKit_NSImage_document_snapshot",
        "command": command,
        "timeout_seconds": 120,
    }
    try:
        completed = subprocess.run(
            command, cwd=ROOT, text=True, capture_output=True, timeout=120, check=False
        )
        attempt.update(
            exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr
        )
    except subprocess.TimeoutExpired as error:
        attempt.update(
            exit_code=None,
            timed_out=True,
            stdout=str(error.stdout or ""),
            stderr=str(error.stderr or ""),
        )
    success = attempt.get("exit_code") == 0 and destination.exists()
    rendered = []
    if success:
        # The same proven installed renderer handles the remaining saved documents.
        # Each run stays bounded to120s and the whole campaign to10min.
        for artifact in manifest["artifacts"]:
            if time.monotonic() - started > 115:
                break
            svg = ROOT / artifact["path"]
            png = OUTPUT / f"{artifact['id']}.png"
            sidecar_path = png.with_suffix(".metadata.json")
            cached_matches = (
                png.exists()
                and sidecar_path.exists()
                and json.loads(sidecar_path.read_text()).get("source_svg_sha256")
                == artifact["sha256"]
            )
            if not cached_matches:
                result = subprocess.run(
                    command[:-2] + [str(svg), str(png)],
                    cwd=ROOT,
                    capture_output=True,
                    text=True,
                    timeout=min(120, 120 - (time.monotonic() - started)),
                    check=False,
                )
                if result.returncode:
                    attempt.setdefault("later_failures", []).append(
                        {
                            "artifact": artifact["id"],
                            "exit_code": result.returncode,
                            "stderr": result.stderr,
                        }
                    )
                    break
            # Keep provenance with every raster without claiming native SVG geometry.
            sidecar = {
                "source_svg": artifact["path"],
                "source_svg_sha256": artifact["sha256"],
                "png_sha256": digest(png),
                "identity": manifest["identity"],
                "sources": manifest["sources"],
                "renderer": "AppKit NSImage snapshot",
                "browser_verified": False,
                "physical_acceptance": False,
            }
            png.with_suffix(".metadata.json").write_text(json.dumps(sidecar, indent=2) + "\n")
            rendered.append(
                {"id": artifact["id"], "path": str(png.relative_to(ROOT)), "sha256": digest(png)}
            )
        if rendered:
            from PIL import Image, ImageDraw

            thumbs = []
            for item in rendered:
                image = Image.open(ROOT / item["path"]).convert("RGB")
                image.thumbnail((390, 430))
                tile = Image.new("RGB", (420, 475), "#101e29")
                tile.paste(image, ((420 - image.width) // 2, 32))
                ImageDraw.Draw(tile).text((12, 8), item["id"], fill="#dcebf5")
                thumbs.append(tile)
            sheet = Image.new("RGB", (420 * 4, 475 * ((len(thumbs) + 3) // 4)), "#101e29")
            for index, tile in enumerate(thumbs):
                sheet.paste(tile, ((index % 4) * 420, (index // 4) * 475))
            sheet.save(OUTPUT / "contact-sheet.png")
    record = {
        "schema_version": "1.0.0",
        "result": (
            "native_offline_render_succeeded_pending_visual_inspection"
            if success
            else "native_offline_renderer_unavailable"
        ),
        "elapsed_seconds": time.monotonic() - started,
        "attempts": [attempt],
        "candidate_count": 1,
        "budget": {
            "maximum_discovery_minutes": 10,
            "maximum_full_render_seconds": 120,
            "maximum_distinct_candidates": 2,
            "maximum_seconds_per_attempt": 120,
        },
        "documented_api_sources": [
            "https://developer.apple.com/documentation/appkit/nsimage/init(contentsoffile:)",
            "https://developer.apple.com/documentation/appkit/nsimagerep/cgimage(forproposedrect:context:hints:)",
            "https://developer.apple.com/documentation/appkit/nsbitmapimagerep",
        ],
        "historical_diagnosis": {
            "sips13": "Advertised SVG UTI did not establish a decodable SVG representation; cannot extract image. Not repeated.",
            "QuickLook255": "QuickLook sandbox-extension/path-filter initialization failed before image generation. Not repeated.",
        },
        "excluded_options": [
            "Private CoreSVG/OTSVG APIs are undocumented and not an authorized supported renderer path",
            "WebKit/WebView is excluded because it would establish a browser document context",
            "No installed CairoSVG/resvg/ImageMagick was found in the prior dependency record; none installed or upgraded",
        ],
        "rendered": rendered,
        "input_manifest_sha256": digest(SOURCE / "source-manifest.json"),
        "visual_inspection": [],
        "browser_used": False,
        "ui_window_created": False,
        "new_dependencies": False,
        "physics_or_cad_run": False,
        "limits": "Native image-document rasterization, even if successful, is not browser acceptance or engineering qualification. No automatic repeat of an unsupported method.",
    }
    (RUN / "record.json").write_text(json.dumps(record, indent=2) + "\n")
    print(
        json.dumps(
            {
                "result": record["result"],
                "elapsed_seconds": round(record["elapsed_seconds"], 2),
                "rendered": len(rendered),
                "record": str((RUN / "record.json").relative_to(ROOT)),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
