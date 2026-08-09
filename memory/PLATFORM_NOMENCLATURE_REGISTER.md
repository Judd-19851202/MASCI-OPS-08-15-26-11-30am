# PLATFORM_NOMENCLATURE_REGISTER

Status: OPEN — PRE-C10 blocking register

## Canonical runtime terminology

- Corrective Actions — preferred operator-facing term for corrective-action workflows.
- Incident — report, triage, investigation, verification, closure, archive.
- QA/QC — preserve exactly in tiles, sidebars, tables, breadcrumbs, and exports.
- Daily Reports — do not shorten to DR in primary operator labels.
- Project Management Center — PM command workspace label.
- Executive Overview — executive rollup, not diagnostics wording.
- Driver Link Review — HR-facing driver matching surface.
- Location Feed / Live Location — operator-facing wording for telematics/location status.

## Disallowed in normal operator UX

- CAPA as primary label where “Corrective Actions” is clearer.
- plumbing words such as Event Router, Materialize Events, Trust Audit, payload, collection, R2, Resend, Cloudflare, webhook, schema, fallback lane.
- transition wording such as “This page has moved” on production-facing routes.
- casual vendor-first wording where domain wording is clearer.

## Current explicit closure in runtime

- Dispatch live-location ribbon changed from vendor-first labels to Location Feed / live location wording.
- HR driver-matching surface renamed to Driver Link Review.
- PM / Executive / Operations surfaces updated to use Corrective Actions on key tiles and cards.

## Remaining open runtime checks

- Sweep remaining operator-visible CAPA references on PM, Safety, HR, Executive, Notifications, and training surfaces.
- Validate breadcrumb, search, tile, and sidebar naming parity after EN/ES pass.
- Close all user-observed wording findings in PRE_C10_MASTER_REMEDIATION_REGISTER with runtime evidence.