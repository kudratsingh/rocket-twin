# Preview verification notes

The parts explorer search accepts the recorded part ID as well as the existing
display name, type and material. Matching is case-insensitive. This makes it
possible to locate a part using an exact identifier from its source record.
The search does not change the configuration, geometry, or analysis evidence.

The search behavior has a frontend unit test. Browser verification of this
change is pending resolution of designated-window runtime ownership; it is not
a new visual acceptance result.

Run comparison lists unavailable required wind settings and unavailable case or
input-hash records even if both runs omit the same information. The match message
is limited to available recorded fields; unrecorded fields cannot be compared. Synthetic
frontend tests cover missing data, equal zeros and changed wind settings; this
later change has not been browser verified.

Replay graph vertical scales use the displayed samples rather than forcing zero
into every range. Constant-valued samples receive a display-only margin, and
the scale labels retain enough precision to distinguish close bounds. Synthetic
frontend tests cover small variations and constant data; this change has not
been browser verified.
