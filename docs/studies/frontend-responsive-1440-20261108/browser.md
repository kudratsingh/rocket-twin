# P5 entry observation — actual size mismatch

**Stopped before responsive cases.** After the owner said Ready, the fresh supported native Chrome state still reported **1965×1074 CSS pixels, DPR 2**, with “Target 1440×900 CSS px not reached.” The packet used 21.928 active seconds against the 480-second cap. No zoom reset, resize, reload, panel/camera interaction or other UI mutation occurred.

The observed window is “Rocket Twin · Vehicle inspection” in Google Chrome, at `127.0.0.1:5173/?workspace=design&design=G80-F2-RP1-AD1-definition-v2&verifyViewport=1`. The requested-size selector says 1440×900, while the actual Content area value remains 1965×1074. This observation does not establish what happened in the owner's view; it records this authorized native runtime's actual readout.

The agreed stop condition was an initial size mismatch or a size change after ordinary Cmd0. Because the initial value already mismatched, Cmd0 and every dependent responsive case stayed unexecuted. No guess, alternate method, DevTools retry or window-border gesture followed. Existing RP1/UI state is unchanged; the measurement panel remains visible.

The primary-declared frozen local source head was `285298f8d70def083d1bf98e3774e6cfce8accc7`; remote checks were ongoing, not claimed passed/merged. No source acceptance tuple or new responsive screenshot acceptance follows from this entry-only packet. Screenshot raster dimensions are recorded separately from the actual CSS helper values and are never substituted for content dimensions.

Required dependency: the owner/provider must establish **actual Content area 1440×900 CSS pixels** in the same authorized Chrome window and coordinate a fresh Ready. Selecting the 1440×900 requested target alone does not resize. Future ownership/attempt handling remains with primary; this stopped packet and inventory are frozen. See the [session record](../../../runs/frontend-responsive-1440-20261108/record.json).
