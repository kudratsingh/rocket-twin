# P47 independent inspection after a denied download permission

Scope: one <=120s native /180s overall packet, stop inputs at90s; sole
browser_access_sol in the existing authorized Chrome window. Source is combined
PR116head eedfabfe08f2cfdee82e1f927a69f4d06b2641e4, current frozenRP1/spec811b/core238.

The permission change rejected inP46 remains unexecuted. This packet neither
grants permission nor retries/substitutes the metadata download. It may dismiss
an actually observed exact127.0.0.1:5173 multiple-download prompt once using Escape
(no Allow/Block/settings button). If that cannot return ordinary app context, stop.
A denial/context ambiguity stops immediately; no alternate transport or workaround.

Then native navigation to normal exact-source RP1 Design/forward_ring may exercise
only the new fin/recovery source links: confirm both exist; choose Recovery,
confirm same part/spec and recovery evidence; return to Design retaining exact
part/context. Capture real native states/images. No download, simulator run,
performance/viewport campaign, other window or engineering change is admitted.
Metadata export stays unconfirmed. Preserve prior pending owner decision; no
permission resolution, complete frontend or physical acceptance is claimed.
