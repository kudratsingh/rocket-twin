# Portable system-map SVG — final evidence state

In **Engineering → system map**, select a current G80 or future G12 block and
choose **Download source SVG**. The source sheet contains the visible graph,
every E1… flow-key entry and the selected block's status, explanation, signal
units/frame and source paths. It carries the exact RP1 configuration/specification
and repository source checkpoint `07552bd1425dce4cf0b47af56c70b44a9500625e`;
SVG metadata retains the complete node/edge set and selected record. It contains
no external image/font request, script or new simulation result.

The source guard accepts only `G80-F2-RP1-AD1-definition-v2`, specification
SHA-256 `811b3bed631fe2ce30a6b0211beecb739d40ebbbcb10e063f6beba0854631660`.
Filenames identify mode and source, for example
`rp1-system-map-g12-811b3bed631f.svg`. Current G80 remains unguided with complete
RP1 flight/inertia inputs unavailable. Future G12 guidance/PID/RL and physical
control remain planned and unqualified; independent recovery stays separate.

The exporter clones the visible SVG, inlines computed vector/text styles and
adds native SVG text/shapes on a standalone source sheet. It rejects foreign
source identity, a missing selected node and external image/script payloads.
Downloading reports a filename or error without changing the selection, camera,
graph layout or underlying source. Source tests/type/lint/format/build evidence
remains separate from the executed artifact evidence below.

## Executed download and XML readback — P74

P74 selected **Future G12 / PID → later RL** and performed one actual browser
**Download source SVG** action. Chrome reported the download complete. Primary
read only the expected downloaded file and verified its actual bytes and XML,
including current RP1/specification, source checkpoint, mode `g12`, selected block
`control`, and absence of external resources, scripts or `foreignObject`. An
identical-byte local verification copy was made.

| Artifact | Recorded identity |
| --- | --- |
| Actual downloaded filename | `rp1-system-map-g12-811b3bed631f.svg` |
| Source SVG size | **47,779 bytes** |
| Source SVG SHA-256 | `4b982729c490b4baceed6a72e20aeae80fd99e754f8af53ca41211bf206fb1c2` |
| Offline AppKit PNG | **1600 × 980** |
| Offline PNG SHA-256 | `3e5f64206da91f6859f041c2b530ae49e46b6ad9b049aaa6252f9889d3b5c072` |

The verified reopen URL was observed by the verifier at 78.637 seconds, after
its declared 60-second readiness deadline. P74 therefore stopped before browser
navigation. This preserves the successful download/XML result; it does not
establish standalone browser rendering or an application failure.
[Native packet outcome](browser-export.md),
[portable XML/readback receipt](export-readback.json).

## Offline rendering and readability

The established AppKit `NSImage` image-document renderer successfully rasterized
those exact SVG bytes in **35.62349758297205 seconds**, exit code 0, with no browser,
window or WebView. The resulting offline image was inspected for readable graph,
flow key, selected-block detail, units and source information. This establishes
readability in that offline rendering path, separately from Chrome.
[Offline PNG](../../../output/frontend-system-map-export-20261109/P74-offline.png),
[render receipt and matching source/PNG hashes](../../../output/frontend-system-map-export-20261109/P74-offline-render.json).

## Browser standalone reopening — unexecuted after P75 focus stop

P75 began with the exact verified artifact URL ready and sent one documented
address-bar shortcut. Native state exposed the editable address/search field,
but focused-element confirmation was unavailable. The required focus assertion
stopped the packet with **P75 addressfocus unavailable**. No URL paste, Return,
navigation, screenshot, alternate input or retry followed. This was a verifier
focus-confirmation stop, not a demonstrated missing/illegible SVG, rendering
failure or permission rejection.

**Standalone SVG reopening in the browser remains unexecuted. No further attempt
is planned or authorized by this record.** Offline AppKit readability and XML
validity do not substitute for that browser evidence. Neither this export nor
these observations close full FW2-020/A15, engineering, physical or flight
acceptance. Frozen sources and all five UNSENT inquiries remain unchanged.
