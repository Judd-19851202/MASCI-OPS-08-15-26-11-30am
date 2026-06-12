# MASCI Proven-Pillar Validation (Track 13.4F)

**Mode:** validation only · NO implementation · NO design.  
**Generated:** 2026-02 (Track 13.4F).  
**Source:** every finding catalogued through Tracks 13.4A → 13.4E that violated the *Proven* pillar in `MASCI_PLATFORM_FIVE_PILLAR_MATRIX.md`.

---

## A. Proven-pillar finding inventory (pre-closure)

10 of 12 Tier-1 findings violated *Proven*, per Track 13.4C Five-Pillar matrix. The full list:

| ID | Description | Pre-closure status |
|---|---|---|
| D-01 | Production Motive webhook unverified | Unverified |
| D-03 | 100/190 motive-mapped assets without GPS | Observed in preview · production-side not verified |
| D-04 | 157 stale assets | Observed in preview · production-side not verified |
| T-01 | Safety-Critical UI Spanish 75.8 % | Measured but Spanish-real-path not verified |
| T-08 | Outbound emails 0 % Spanish | Measured |
| T-09 | Server-rendered PDFs 0 % Spanish | Measured |
| V-04 | `tokens.css` PROPOSAL — not wired | Self-declared in file header |
| V-13 | Mobile evidence gap | Partially closed in 13.4E (5 of 9 portals) |
| V-15 / R-13 | Driver portal landing "missing" | **TO BE RE-VALIDATED in 13.4F** |
| W-01 | No tenant model | Verified true |
| W-02 | No tenant scoping in routes | Verified true |
| W-09 | Hardcoded MASCI legal text | Verified true |

---

## B. Per-finding closure verdicts

### B.1 D-01 Production Motive webhook unverified — **Cannot Verify**
- Reason: Track 13.4F is executed against the preview environment (`APP_ENV=preview` · `DB_NAME=masci_safety_preview`).
- Action required: production-side execution of Track 13.4D §3 7-point checklist. None can be performed from preview.
- Verdict: **Still Unverified · Evidence Required · Cannot Verify from preview.**

### B.2 D-03 / D-04 GPS coverage and staleness — **Cannot Verify (production)**
- Preview shows 90/190 with GPS, 33 attention, 157 stale. These numbers are real for preview but cannot be assumed identical in production.
- Verdict: **Still Unverified · production rerun required.**

### B.3 T-01 Safety-Critical Spanish 75.8 % — **Verified (measured)**
- Track 13.4B Phase 3 measured the orphan count precisely: 100 Safety-Critical orphans out of 413.
- Real-Spanish-path UI walkthrough (i.e., setting `lang=es` and visually confirming each safety surface) **not** performed.
- Verdict: **Verified at measurement level · still unverified at user-walkthrough level.**

### B.4 T-08 Outbound emails 0 % Spanish — **Verified**
- Source review of `branded_portal_emails.py`, `outage_alerts.py`, `pm_routes.py`, `pm_admin.py`, `safety_forms.py` confirms: no Spanish template exists.
- Verdict: **Verified.**

### B.5 T-09 Server-rendered PDFs 0 % Spanish — **Verified**
- Source review of `pm_welcome_pdf.py`, `field_leadership_pdf.py`, `training_pdf.py`, `hub_banners_pdf.py`, ODR PDF builders, Trench Safety PDF builders confirms: no Spanish layer. (`safety_forms.py` Equipment Issuance is the lone exception with inline EN+ES legal text.)
- Verdict: **Verified.**

### B.6 V-04 `tokens.css` not wired — **Verified**
- The file's own header declares "STATUS: PROPOSAL — NOT YET WIRED into any component."
- Components hardcode Tailwind color literals (per `tokens.css` header: ~690 red-700, ~605 slate-900, ~105 cyan-700 occurrences).
- Verdict: **Verified.**

### B.7 V-13 Mobile evidence gap — **Resolved**
- Track 13.4E: 30 captures for Admin · Dispatch · PM · Shop · HR at iPad-landscape · iPad-portrait · phone.
- Track 13.4F: 48 captures for Safety · Leadership · Field Leadership · Driver-landing-attempt · Dispatch-driver-login · Driver-pre-trip-public at desktop + iPad LS + iPad PT + phone.
- All 9 operator portals + driver session entry points + key public surfaces now have mobile evidence.
- Verdict: **Resolved.**

### B.8 V-15 / R-13 Driver portal landing missing — **INVALIDATED**
- Track 13.4B Phase 1 inventory could not locate a driver landing page in `pages/`. This was incorrect.
- **The Driver portal DOES exist:**
  - `/app/frontend/src/pages/driver/DriverShift.jsx` — mounted at `/driver` in `App.js`.
  - `/app/frontend/src/pages/driver/DriverMagicLanding.jsx` — magic-link landing.
  - `/app/frontend/src/pages/driver/ShiftStart.jsx` — shift start surface.
  - Backend routes in `/app/backend/routes/dispatch_driver.py` provide `/start-shift`, `/shift-lookups`, `/assignment-lookups`, `/magic-link`, `/session/exchange`, `/me`, `/my-assignment`, `/assignments/{id}/transition`, `/assignments/{id}/acknowledge`, `/sessions`, `/sessions/{id}/revoke`.
  - Backend `/app/backend/routes/driver_profile.py` carries the driver profile API.
- The earlier inventory pattern matched `*Hub.jsx` and `*Home.jsx`; the Driver portal does not use those suffixes (uses `DriverShift`), so the regex missed it. Today's source confirmation re-locates it.
- Verdict: **INVALIDATED. The finding was wrong.** Track 13.4E's "Needs Rebuild" verdict for Driver Portal is downgraded to "exists, requires further role audit" (see `MASCI_DISCOVERY_CLOSURE_REPORT.md` §3).

### B.9 W-01 No tenant model — **Verified**
- Mongo collections audit confirmed no `tenants`, `customers`, `workspaces`, `organizations`, `tenant_settings`, or `branding` collections.
- Verdict: **Verified.**

### B.10 W-02 No tenant scoping in routes — **Verified**
- `grep -rln "tenant_id|customer_id|workspace_id|organization_id" /app/backend --include="*.py"` returns matches only in test fixture files.
- Verdict: **Verified.**

### B.11 W-09 Hardcoded MASCI legal text — **Verified**
- `safety_forms.py` lines 189, 195, 493, 498 contain `"MASCI General Contractors Inc."` baked into equipment acknowledgement text (EN + ES).
- Verdict: **Verified.**

---

## C. Final Proven-pillar score

| Status | Count | Findings |
|---|---|---|
| **Verified** (proven via evidence) | 7 | T-01 · T-08 · T-09 · V-04 · W-01 · W-02 · W-09 |
| **Resolved** (gap now closed) | 1 | V-13 |
| **Invalidated** (finding was incorrect) | 1 | V-15 / R-13 |
| **Still Unverified · Cannot Verify from preview** | 3 | D-01 · D-03 · D-04 |

→ **Production Motive validation remains the single open Proven-pillar gap.**

---

## D. Closure of production Motive validation

Per Section 1 directive: audit actual production.

**This audit cannot meet that directive from preview.** The honest categorisation:

| Domain | Verdict |
|---|---|
| Webhook activity (production) | Cannot Verify · Evidence Required |
| GPS updates (production) | Cannot Verify · Evidence Required |
| Asset counts (production) | Cannot Verify · Evidence Required |
| Marker counts (production) | Cannot Verify · Evidence Required |
| Marker types (production) | Cannot Verify · Evidence Required |
| Feed health (production) | Cannot Verify · Evidence Required |
| Operational summary accuracy (production) | Cannot Verify · Evidence Required |
| Geofence behaviour (production) | Cannot Verify · Evidence Required · circle conversion gap documented |
| Dispatch homepage map behaviour (production) | Cannot Verify · Evidence Required · preview verified in 13.4A |
| Operations Map behaviour (production) | Cannot Verify · Evidence Required · preview verified in 13.4A |

**Reason:** preview environment is intentionally isolated. To validate production, an audit must be re-run against `https://mascidocs.com/api/...` with admin/dispatch tokens issued from the production identity store. Track 13.4F cannot perform that from the current container.

**Action required:** the operator must either grant production access or accept that the Proven-pillar production gap stays open until a production-side audit is executed by someone with that access.

---

## E. What this validation did NOT do
- Did not connect to production.
- Did not walk through Spanish UI flows manually.
- Did not redesign the Driver portal (now confirmed to exist).
- Did not modify any source.
- Did not author a production-validation script (the 7-point checklist exists in Track 13.4D §3 ready for production execution).
