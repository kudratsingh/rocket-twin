# Motors

Certified thrust curves in RASP `.eng` format from thrustcurve.org, one per motor, each with a
sidecar `<name>.yaml` recording: source URL, certification body and date, propellant mass,
casing mass, total impulse, burn time, and the date fetched.

Default (ADR-0003): `Estes_F15.eng`. Two alternatives fetched in WO-01 for the motor panel and
the thrust-to-weight check. Never edit a `.eng` file by hand; the scale factor used for
randomisation lives in the vehicle spec.

## Import without editing the source

The source files are now archived here with reviewed sidecars. The importer
validates one RASP entry, preserves its exact original bytes, and records its hash,
source/certificate URLs, date and derived impulse/masses. Import does not establish
certification: check the certificate and exact motor variant separately.

The selected historical F15 dataset is John Coker's 2013 certification-derived record:
https://www.thrustcurve.org/simfiles/5f4294d20002e900000007e5/ .
With network access, import it using:

```sh
.venv/bin/python scripts/wo01_import_motor.py \
  --url https://www.thrustcurve.org/simfiles/5f4294d20002e900000007e5/download/Estes_F15.eng \
  --source-url https://www.thrustcurve.org/simfiles/5f4294d20002e900000007e5/ \
  --certificate-url https://www.thrustcurve.org/motors/cert/60c63bfcb5bc370004713e7f/F15.pdf \
  --certification-body NAR --certification-date 2012-11-25 --name Estes_F15
```

For a manual browser download, replace `--url ...` with `--file /path/to/Estes_F15.eng`.
Existing files are never overwritten. The command writes `.eng` and `.yaml` side by
side. It does not change the vehicle specification; reconcile geometry, masses and
curve-derived figures before setting `motor.curve` in the spec.

RASP parsing rules: https://www.thrustcurve.org/info/raspformat.html .
The numerical parser tests use a synthetic TEST motor, stored only in test code;
those samples are not a substitute for certified data.

## Collect all candidates for review

`make fetch-motors` queries the official API for Estes F15, AeroTech F10 and G25.
It retains search responses, download responses, original decoded RASP bytes and
SHA-256 inventories in ignored `data/motor-downloads/`. API output is unreviewed;
multiple motor variants are retained, not automatically selected. Reconcile the
certificate date, source, geometry and masses before importing any candidate here.
The API path is based on the official documentation and the installed RocketPy
1.13.0 client. Local tests check byte preservation and review labelling; successful
live API execution is still pending network access.

The collector sends JSON POST requests with explicit content/accept headers and
identifies itself as `rocket-twin/0.0.1`. If an HTTP/API rejection occurs, its
bounded diagnostics are written to `<candidate>/error.json` under the download
folder. It stops on 401/403/429; there are no automatic access-denial retries.
The outgoing request format and error handling are locally tested. Live server
acceptance remains to be verified from a network-enabled terminal.

## Current review

- `Estes_F15.eng`: selected historical certification-derived dataset, accepted for
  the digital F15 model. SHA-256 and historical certificate date are in its sidecar.
- `AeroTech_F10_historical.eng`: excluded from selection pending variant reconciliation;
  source listing is out of production. Certification date is unknown.
- `AeroTech_G25_152mm.eng`: quarantined despite its API `cert` label, because its
  geometry/propellant mass disagree with the motor summary. Certification date unknown.
- `AeroTech_G25_124mm_derived.eng`: retained for comparison only. API labels it `user`,
  while internal comments say NAR-derived. Certificate/date reconciliation is pending.

Dates of submission and file creation are not certification dates. These files
are historical engineering inputs, not confirmation of current motor certification
or hardware suitability. Original `.eng` bytes have not been edited.
