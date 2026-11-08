# Adafruit 5374 source PCB drawing

The separately admitted follow-up retrieves and parses the official Eagle board as XML data. It adds a read-only, selectable 2D footprint view for `high_g_accel`. It does not change the core 55-part source, engineering geometry, optional internal-detail manifest, physical configuration or vehicle placement.

The exact source is the [official Adafruit ADXL375 PCB repository](https://github.com/adafruit/Adafruit_ADXL375_PCB), whose README associates it with [PID5374](https://www.adafruit.com/product/5374). The board artifact is pinned by [immutable Git blob](https://api.github.com/repos/adafruit/Adafruit_ADXL375_PCB/git/blobs/4a768fc9f113ba6f95c6e930a3fac436d066f82a):

| Field | Recorded value |
| --- | --- |
| Git blob | `4a768fc9f113ba6f95c6e930a3fac436d066f82a` |
| SHA-256 | `7c089eb8cc0756b7dc5e30abd240978dc272113d93f602b497f8f442d532d68c` |
| Size / format | 269,123 bytes / Eagle XML 9.6.2 |
| RP1 specification | `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660` |
| Drawing ID | `adafruit-5374-pcb-2d-4a768fc9-v1` |
| Manufacturer drawing frame | Original PCB XY coordinates, millimetres, +Y up; no vehicle registration |
| Coverage | 26 listed placements, 200 top-side primitives; four Ø2.5 mm mounting drills |
| License | CC BY-SA 3.0 Unported, Adafruit Industries / Limor Fried (Ladyada) |

The board outline is **25.4 × 17.78 mm**. The current nominal product envelope is **25.6 × 17.7 × 4.6 mm**, a PCB-minus-envelope XY difference of **−0.20 / +0.08 mm**. Datums, tolerance and incoming hardware revision are unavailable, so these values do not establish a fit pass. The SVG preserves millimetre coordinates without scaling the board into the current envelope.

The source contains an `ADXL343` value at U1 despite being the official ADXL375/PID5374 file. The drawing retains that value and explains the inconsistency; it does not infer installed silicon identity. All component/package heights remain null. Connector population, incoming revision, full three-dimensional bodies and vehicle orientation remain unavailable.

Top-side package silk/documentation, rectangular SMD footprints and explicit drill circles are projected using source placements and rotations. Curved outline wires are sampled at at most five-degree steps. SMD corner roundness remains in the data but is displayed as a rectangle. Copper diameter/annulus is not invented when absent. Bottom mirrored footprints are listed with a note, rather than transformed by an assumed convention. Routing, decorative logos, font contours and artwork are omitted. These are PCB footprints, not fabricated parts or package solids.

`HighGBoardDetail` accepts `{ partId, configurationId, specificationSha256 }` and returns no view unless all three match the pinned RP1 record. Its larger native dialog exposes footprint selection, source values/positions/rotations and missing details. Exported SVG embeds the full upstream attribution notice, source blob/SHA, units, frame and limitations, alongside visible Adafruit/CC BY-SA attribution. The upstream README license notice is preserved in the JSON and dialog. This derived drawing is distributed under the same CC BY-SA 3.0 terms.

Reproduce with `.venv/bin/python scripts/wo04_high_g_board_export.py` after placing the exact official XML and upstream README in `.cache/hardware-detail-sources/` as documented by the script defaults. The exporter rejects changed bytes before XML parsing. The cache is not a required tracked dependency; the derived JSON is source-owned. Tests always verify the tracked data and rejection guard, and verify complete regeneration when the optional source cache exists.

Validation: three Python tests pass; the frontend SSR test confirms exact-source admission, refusal of wrong IDs/hashes, dimensions, hole coverage, license and full SHA preservation. TypeScript typecheck and component ESLint pass. Ruff and Black checks pass in the primary project environment (the research worker lacked Black). The separately recorded live check opened this graphic, but Escape failed; the native-dialog key-ownership correction has source tests and awaits browser recheck. No 3D-detail acceptance, purchased-hardware check, manufacturing tolerance or physical/flight qualification is claimed.

The initial six-page research packet remains a historical record of its earlier read-only scope. This follow-up supersedes its “not downloaded/parsed” status only for the explicitly pinned Adafruit board. Eggtimer/AeroTech source availability and generic board identity gaps remain unresolved.
