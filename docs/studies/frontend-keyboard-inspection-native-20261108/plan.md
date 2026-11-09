# P55 bounded desktop keyboard/search selection

Existing Q07/Q09 branch, no new implementation or source change. Sole designated
Chrome agent/samewindow, finalPR116c1adab runtime frozen. One150s native/210s
overall, inputs<=120s. No resize/mobile/performance work or physics.

Use exactRP1/spec811b and an actualselectedforward_ring. From ordinary non-input
focus, slash should open/focus Parts search; enter the stable partID and observe
matching source row. Escape while search owns focus must not clear the selected
part. Move focus through an actual normal button, then global Escape should
explicitly clear selection and its URL. Only claim keyboard/focus behavior if
actual focused state/route/pane is observed; do not infer Tab order from source.
If ordinary focus cannot be established through supported native actions, stop
that subcase unverified instead of injecting JS or forcing browser internals.

Clear the search and restore Whole if reserve. Capture actual focus/part/source
states. No download, Run, Play, permission/settings, different window or full
keyboard matrix claim. Stop guard/denial/source mismatch/ambiguous action. This
is one representative desktop branch, not all accessibility/layout acceptance.
