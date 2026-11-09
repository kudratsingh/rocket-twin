# One real desktop experiment and saved-result follow-up

Primary admits exactly one existing local-CPU Tiny request using the
[completed source preflight](../frontend-desktop-detail-20261108/experiment-desktop-preflight.md):
archived G80 modular-performance-v1, Tiny dt0.005s/9000steps/45s, wind1m/s toward0°,
gust0, seed20261107, no sweep. No RP1 flight, batch, physical source edit, paid run,
new model or full-duration benchmark is admitted.

Use two sequential UI packets declared before execution: P44 launch/save at most
180s native/240s overall, with no new input after150s and a90s computation-observation
limit; P45 saved replay/comparison/export at most150s native/210s overall. P45 may
reuse the single accepted ID only and cannot submit a second run. Splitting the
UI observations gives each a real closeout reserve; it does not enlarge the9000-step
computation or claim a hard worker deadline. Existing API cancellation is cooperative
and there is no guaranteed90s worker termination. At timeout report state/ID,
stop new actions and do not retry the computation.

Start from normal RP1 Design and record its identity; choose archived G80 only in
Experiments. An acceptedID comes from the actual response. Record only queued,
running/terminal states actually observed; fast completion may omit an intermediate
state. Save/reload exactID, verify settings/source/profile and expected partial
trajectory. Compare to exp-d0baf4168f7f41e687a1b5f12e14cc3e only after actual A/B
identities/settings match the preflight; otherwise show/refuse the mismatch.

No mandatory magic copy strings or fabricated pass, events or field data. Preserve
actual errors, missing landing, partial trajectories, differences and downloaded
bytes. Optional playback in P45 is bounded to5wallseconds, not a new whole-flight
performance qualification. Return to original RP1 source if reserve permits.

Stop private/changed context, wrong source/settings, ambiguous/multiple acceptance,
failed/missing attempt, incompatible baseline, export-coverage rejection, guard,
automatic denial or deadline. No automatic retake/resource increase/cancellation
campaign follows. Only the designated browser agent uses the existing Chrome
window. Other agents may inspect project metadata and publish source changes.
All supplier/lab inquiries remain UNSENT and engineering/build/flight gates remain.
