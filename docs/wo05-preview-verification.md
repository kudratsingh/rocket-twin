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
