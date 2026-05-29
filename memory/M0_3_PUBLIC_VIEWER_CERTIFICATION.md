# M0.3 · Public ODR Viewer · Certification

_Phase V.1 · 2026-05-29 · DOT / FAA / CEI / OWNER / CONSULTANT SURFACE._

## Mission

External stakeholders open a public link and see a **clean,
printable, professional, redaction-compliant** record. No internal
data leakage. Ever.

## Page

`/odr/public/:doc_id?link=<link_id>` ·
`/app/frontend/src/pages/odr/OdrPublicViewer.jsx`

## API surface

`GET /api/odr/public/{doc_id}?link_id=<link_id>`

- No portal token required (intentional — DOT inspectors do not have
  MASCI accounts).
- Gated by the Continuity Engine (`routes/odr/continuity.py`):
  - `doc_id` must resolve.
  - `link_id`, if supplied, must match the active link on the ODR.
  - Revoked links return 410 Gone.
  - Missing links return 403.
  - Every access (success or failure) appends a row to
    `odr_preload_attempts`.

## What's rendered (audience-safe)

| Section | Content |
|---|---|
| Header | doc_id · project number/name · report date · status |
| Crew | crew name · crew type · primary operation |
| Production | segments (count + crew_type + primary_operation) |
| Delays | any_delays flag · total hours lost · per-entry description |
| Safety | any_event flag only (NO per-event details) |
| Weather Impact | hours lost · description |
| Signature | foreman acknowledged · UTC timestamp · statement |
| Footer | one calm line · continuity tracked · independent verification on request |

## What is NEVER rendered (doctrine lock)

Per operator directive — External audience NEVER receives:

| Hidden | Reason |
|---|---|
| Coaching prompts | Internal operational guidance |
| Readiness | Internal QC signal |
| Internal comments | Author-only |
| Internal chronology notes | Author-only |
| Risk scoring | Internal lens |
| Internal guidance | Author-only |
| Future planning references | Internal forecast — NOT contractual record |
| Foreman raw `foreman_uid` | Privacy boundary |
| Superintendent raw uid | Privacy boundary |
| PM raw uid | Privacy boundary |
| Per-event safety details | Risk-redaction · safety details exit via the formal incident report, not the public ODR |
| Completion telemetry | Admin diagnostic |
| Device fingerprints | Privacy + security |
| Sync conflict telemetry | Operational noise |

Field projection enforced server-side in `continuity.py` and the
public response builder; the page consumes only what the API
returns.

## Continuity-safe identifier guarantee

The URL contains the **immutable** `doc_id` (year-scoped
`ODR-YYYY-NNNNN`). The `link_id` is the access token. Both are
preserved across:

- Active → Amended (URL stays valid; viewer shows amendments
  exposed in PDF + version-chain · NOT inline).
- Active → Superseded.
- Active → Archived.

No silent URL mutation. No broken historical links.

## Mobile + printable

| Constraint | How |
|---|---|
| Mobile friendly | `max-w-3xl` shell · single column · 16px base text |
| Printable | `print:py-0` on shell · monochrome palette · no interactive controls |
| Professional | No platform marketing · no MASCI logo at top (kept neutral on purpose) · simple slate hierarchy |
| Clean | No coaching tooltips · no "expand" / "details" widgets |

## Compliance posture

The page is designed to be acceptable as a print-out:

- ✅ DOT
- ✅ FAA
- ✅ CEI
- ✅ Owners
- ✅ Consultants

The official record SHA256 footer lives on the **PDF version**
(`/api/odr/{id}/pdf?audience=external`) which is the contractually
canonical artifact. The HTML viewer is the convenience access; the
PDF is the artifact of record. Both share the same backing data.

## Telemetry

The viewer does NOT post telemetry from the browser (it has no
portal token to do so). The server-side
`odr_preload_attempts` log captures every access — that's the
authoritative trail.

## Test surface

- `data-testid="public-odr-viewer"` · `public-odr-header` · `public-odr-crew` ·
  `public-odr-production` · `public-odr-delays` · `public-odr-safety` ·
  `public-odr-weather` · `public-odr-signature`
- Backend tests: `test_public_resolve_strips_internal_fields` +
  `test_public_resolve_revoked_link_410`.
- Browser smoke (M0.3 deploy run): renders ODR-2026-00003 cleanly.

## Verdict

🟢 **PUBLIC VIEWER LIVE.** Clean. Printable. Professional. Mobile
friendly. Redaction-compliant. Continuity-compliant. No internal
data ever leaks.
