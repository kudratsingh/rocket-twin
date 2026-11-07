# VP1 inquiry response and first-test decision template

**Current state: five drafts unsent; no replies or service quote received; no clock has started.** This is a blank decision aid, not an authorization or a recommendation to purchase, fabricate or load. The latest owner workflow is the [VP1 response decision](../../wo03-vp1-response-decision-20261106.md); the frozen [protocol](protocol.md), [package summary](package-summary.md), [D1 decision](../../wo03-rp1-load-attachment-decision.md) and the five existing drafts govern technical scope.

## Record and date convention

The public [response-tracker.json](response-tracker.json) is a blank template. Put raw replies, quotes, and actual dates in the ignored local directory `.cache/vp1-correspondence/`; publish only a sanitized decision. Create a local copy without overwriting any existing record:

```sh
mkdir -p .cache/vp1-correspondence
cp -n docs/validation/rp1-vp1/response-tracker.json .cache/vp1-correspondence/response-tracker.json
.venv/bin/python scripts/wo03_vp1_inquiry_tracker.py --input .cache/vp1-correspondence/response-tracker.json
```

Record each **actual** owner-supplied send date and its IANA timezone separately in that copy; retain the original draft, date, and all received replies, including negative or incomplete replies. Record at most one actual `follow_up_date` per inquiry, only after a send. Never infer a send or contact approval. The helper validates and previews dates without changing the file or contacting anyone. The default input is the blank tracker. It makes no scheduler or notification.

The send day is day zero, even if it falls on a weekend. Count the next Monday–Friday days independently for each inquiry; the only follow-up is on business day 5 and documentation closes on business day 10. Set `holiday_calendar.choice` to `provided` with a description including coverage and actual `dates` in `YYYY-MM-DD`, or explicitly to `none` to count all weekdays including holidays. `unspecified` produces provisional weekday dates and flags holiday ambiguity. A supplied calendar excludes only its listed dates; verify coverage through each due date. The single actual follow-up date is separate from its calculated due date. All actual sends, follow-ups, and replies are recorded by the owner; a calculated due date never sends or schedules anything.

| Draft | Actual send date and timezone | Reply/date and retained reference | Follow-up due day 5 / actual | Close day 10 | Remaining question |
| --- | --- | --- | --- | --- | --- |
| Aircraft Spruce 02-20850 | Pending | None | Pending | Pending | Lot, grain, thickness, density, available typical data |
| LOC BT-2.56 | Pending | None | Pending | Pending | Dimensions, paper surface and preparation |
| AeroTech 12912 | Pending | None | Pending | Pending | Dimensions, substrate, finish and bonding preparation |
| WEST 105/206/406 | Pending | None | Pending | Pending | Wood/paper preparation, wet-out, mix and cure |
| Laboratory RFQ | Pending | None | Pending | Pending | Scope, method and itemized written quote |

## Evidence and gaps

- Supplier stock/product or process facts, exact source, date, lot and limitations: **pending**. These facts do not qualify the custom assembled root or establish installed properties.
- Laboratory written acceptance of substrates, process, specimen preparation, cure, fixtures and scope: **pending**.
- Calibration certificates, uncertainty budget, independent displacement reference and force/contact controls: **pending**. Check S1 U95 displacement ≤0.01 mm and fitted effective compliance uncertainty ≤10%, including held-out predictions as specified in the protocol.
- Replication, directions, conditioning, load caps, sacrificial phases and invalid/censored outcomes: **pending**. S1 specifies ten strips (five per grain direction, three calibration and two held out) and six actual curved-substrate joint witnesses (three per route).
- D1 comparison and pass/fail method: **pending**. Preserve the once-factored 331.125 N / 8.83 N·m and 1 mm total-tip limit, retained strength screens, uncertainty, and distinct root-input and distributed-panel interpretation. S1 alone cannot establish an installed fin pass. Bare AD1 fails its estimated screen; the stock is not adopted.
- Written itemized **all-in S1 total** including stock, preparation, fabrication, fixtures, calibrated channels, setup, test, report, shipping and tax, with exclusions, payment and quote validity: **unavailable**. A stock snapshot or affordability reservation is not a total quote; unresolved components remain unknown rather than zero.

## One first-test decision

When the written method, complete itemized total quote, calibration/uncertainty, replication, fixture details and D1 pass/fail interpretation are available, make **one** room-temperature S1 recommendation: **proceed to owner authorization** or **hold/replan**, with the supporting evidence, amount and unresolved exclusions recorded below. Missing, unsuitable or contradictory evidence means hold; do not infer a pass from silence or a capability page.

- Recommendation and reason: **pending**.
- Exact laboratory/method and source references: **pending**.
- Itemized all-in total and quote validity: **pending**.
- Failed, unquoted or ambiguous requirements and stop conditions: **pending**.
- Owner decision for purchase, paid service, specimen fabrication and testing: **not authorized**; separate explicit approval is required before any such action.

S2a conditioned samples require their own decision and authorization. **S2b independent root articles remain separately held** until S2a and a supported construction/material decision, valid method and written quote, and separate authorization. Coupon results, product claims or an S1 quote do not admit root construction, installed fin acceptance, thermal/recovery/flutter or flight release.
