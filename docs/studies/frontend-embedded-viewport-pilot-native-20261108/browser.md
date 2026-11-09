# P28 embedded unscaled actual-app viewport — partial pilot

One normal same-tab DEV fixture navigation loaded the real RP1 AD1v2 app with exactspec811b…:55 records,26/26 meshes visible and actual rendered rocket. The parent separately reported requested1440×900CSS, actualinner1440×900, documentclient1440×900, framerect1440×900,DPR2,size matchyes. `ready-1440.jpg` visibly contains the entire magenta unscaled frame outline. This is an **embedded actual-app CSS viewport**, not a top-level Chrome size claim.

One actual inner-app Nose control click succeeded. Native AX reports Nose pressed1 and the child URL gained `part=nose` while retaining exactRP1/spec; `nose-selected-1440.jpg` captures the selected model/readout. The parent did not automate that interaction.

The first parent1280×720 preset action returned:

> The user changed '/Applications/Google Chrome.app'. Re-query the latest state with `get_app_state` before sending more actions.

The packet stopped immediately, without re-query, retry, another preset, screenshot or restoration. Resize completion and child-state retention at1280 are **unconfirmed**. Last successful state was1440embedded/Nose selected; finalstateafterguard is unobserved. No fixture-method approval rejection or CSP block occurred, but the pilot remains partial pending primary acceptance; no full responsive matrix credit follows from dimensions alone.

Last successful timer28.191 s; interrupted action began39.520 s with4.0694 s tool wall, below90 s. No later native call. No top-level bounds/zoom/DevTools/CDP/otherwindow,Play,simulation,export orperformance action. Source manifest and actual size/pixel observations are separate. Prior blocked methods/packets remain unchanged.
