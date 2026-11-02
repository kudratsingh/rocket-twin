# Bounded integrated aft decision arithmetic

One read-only packet was declared before execution at one CPU, 2 CPU seconds
and 5 wall seconds. It reads saved S2/S1 results, does scalar algebra only and
runs no simulator, geometry integration, CAD, FEA or thermal solver. No stopped
S2 calculation was repeated. A 2-second CPU limit and 5-second alarm were active;
thread-count environment variables were set to one. The after-import timer is
recorded; setup/import/earlier hand-work CPU is unmeasured rather than zero.

The record rejects the additive sketch. Its named-stock mass is incomplete and
uncertain, not a complete installed mass or a conservative bound. Opening force,
point-contact and old-CP/balance sensitivities are conditional on that subtotal.
Full tensor and exact guide speed are unavailable. The fixed 15 m/s requirement,
separate 50 g growth, 15.5 m/s planning target, DF3 and thermal screens are retained.
No physical requirement, hardware selection or active geometry changed.

`executed-config.yaml` is the exact input. `arithmetic.py` is the executed source.
`record.json` retains before/after input hashes, scalar results and timing.
A successful process exit is not design acceptance. No further physical variant
or native analysis is admitted by this packet.
