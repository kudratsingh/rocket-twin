# Export provenance adapter verification

The check executed from `.cache/wo04-export-provenance-check.mjs`; the archived
`executed-check.mjs` must be copied to that path before reproducing its relative
imports. It uses React server rendering only, never a browser or physical solver.

The initial check stopped because the full CSS hash included a new HTML-only
glossary. The actual SVG-affecting CSS is unchanged: the maintained CSS has the
rendered CSS as an exact prefix, and every extra selector is scoped to the
glossary section, which has no SVG descendants. All11actual SVG strings match
between archived rendered and maintained components. The current metadata
adapter carries all33sources; base15sources are unchanged. Actual browser
click/download behavior remains unverified. No temperature/strength criterion
was changed and no raster or engineering calculation repeated.
