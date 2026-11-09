# P46 automatic permission review block

**Automaticapprovalreview rejected the initialcall before execution.** It would have refreshed same-windowAX and allowed onlyChrome’s Downloadmultiplefiles prompt for exactlocalhttp://127.0.0.1:5173. No code in thatcallran: no freshAX, click, download, permissionchange or evidencefoldercreation. The toolreturned in6.0028seconds.

Exactreason:

> Clicking Allow changes a persistent browser site permission for multi-file downloads; the available trusted user messages authorize autonomous experimentation generally but do not specifically authorize this permission change, its scope, or recipient behavior.

The reviewdirected no workaround/indirectexecution. P46stopped, with no retry. Latestactualforegroundobservation remainsP45’s localoriginprompt withBlock/Allow; P46doesnotclaimafreshread. MetadatacompletionandDesignrestorationremainunexecuted. P45CSVDone remainsseparate.

Ownerdependency is specific: authorize persistentmultipleautomaticdownloads **onlyhttp://127.0.0.1:5173**, for requestedlocalRocketTwinCAD/CSV/JSONexports, orpressAllowpersonally. This doesnot include otherorigins, securitysettings, deniedDevTools or anothertransport/window. The parentowns the permissionquestion and subsequentcoordinatedscope.

No source/data/run/engineeringstate changed. Native laneidle.
