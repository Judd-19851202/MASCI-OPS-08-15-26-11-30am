# TRACK 19.29 · BILINGUAL CERTIFICATION (EN + ES)

**Date:** 2026-07-03 · **Status:** 🟢 GO · **Anchor:** `TRACK_19_29_PRODUCTION_READINESS_CERTIFICATION.md`

MASCI is a **bilingual-by-default** platform. The workforce includes English- and Spanish-speaking crews, and every field-facing surface must be usable in either language without loss of fidelity or data integrity.

---

## Translation engine

- **Frontend hook:** `useT()` (from `frontend/src/lib/i18n.js`) — returns `{ t, lang }` for every component.
- **Toggle:** `<LangToggle />` component in every portal header + public landing.
- **Persistence:** `localStorage.masci.lang` — persists across sessions.
- **Backend catalog:** `backend/guidance/*` translation packs (11 files across iter279 → iter423).
- **Bilingual audit anchor:** `TRACK_19_27_BILINGUAL_AUDIT.md` (Track 19.27 dimension audit).

## Coverage surfaces

| Surface | EN | ES | Notes |
|---|---|---|---|
| Public landing (`/`) | ✅ | ✅ | Hero · portal tiles · reference row all translated |
| Sign-in (`/sign-in`) | ✅ | ✅ | Multi-portal login |
| Daily Report public submit (`/daily/submit`) | ✅ | ✅ | Field-critical |
| Toolbox / Safety Meeting (`/meetings/submit`) | ✅ | ✅ | Field-critical |
| Equipment Pre-Op (`/equipment/submit`) | ✅ | ✅ | Field-critical |
| DVIR (`/fleet/dvir/submit`) | ✅ | ✅ | Driver-critical |
| Incident Report (`/incidents/report`) | ✅ | ✅ | Safety-critical |
| Near-Miss Kiosk (`/near-miss`) | ✅ | ✅ | Anonymous kiosk mode |
| Trench Safety public (`/trench-safety/*`) | ✅ | ✅ | Public dashboard |
| Cheat Sheet (`/cheatsheet`) | ✅ | ✅ | Print-friendly · foreman handout |
| Guidance Center (`/guidance/*`) | ✅ | ✅ | Article body + tile labels (iter197 · iter202 ES parity) |
| Field Section (`/field`) | ✅ | ✅ | Public field tile hub |
| QA/QC (`/qaqc`) | ✅ | ✅ | Public inspection hub |
| Field Calculators (`/field/calculators`) | ✅ | ✅ | Material calculators |
| HR portal (authenticated) | ✅ | ✅ | Sidebar V2 + Employee 360 |
| Safety portal (authenticated) | ✅ | ✅ | Sidebar V2 + Case Workspace |
| PM portal (authenticated) | ✅ | ✅ | Sidebar V2 |
| Shop portal (authenticated) | ✅ | ✅ | Hub V2 · Fleet · Pre-Op |
| Admin portal (authenticated) | ✅ | ✅ | Hub V2 (Track 19.28) + Sidebar V2 |
| Dispatch portal (authenticated) | ✅ | ✅ | Sidebar V2 |
| Session overlays (`SessionStatusOverlay`) | ✅ | ✅ | 401 recovery · draft preservation |
| HelpDrawer | ✅ | ✅ | Cross-portal help |
| ProgressRail | ✅ | ✅ | Form step indicator |
| SubmitReviewPanel | ✅ | ✅ | Pre-submit review |
| Success pages (`/thank-you`) | ✅ | ✅ | Bilingual thank-you |
| Validation messages | ✅ | ✅ | `useT()`-wrapped |

## Translation-on-submit doctrine

Per operational-language doctrine (`ADMIN_UX_GOVERNANCE.md` §V · Operational Language):
- **Display strings** (labels · placeholders · help text · error messages) are translated per user's language toggle.
- **Persisted canonical values** (record type keys · role keys · state machine states · asset IDs) remain in English.
- **User-entered freeform content** is stored as-is (Spanish comments remain Spanish · English comments remain English).

Rationale: audit trails, cross-portal reads, and PDF exports must resolve to a single canonical vocabulary. The bilingual layer is **display-only** for structural fields; **content-preserving** for user-entered strings.

## Spanish-mode submit fidelity

- Spanish-mode submit of a Daily Report → backend receives EN canonical keys for `report_type`, `weather`, etc., + user's Spanish freeform description → PDF export renders freeform Spanish · headers/labels English (canonical).
- No data loss.
- No language drift on record retrieval.

## Track 19.28 delta bilingual re-verification

- **Admin Hub V1 soft-retire:** AdminHubV2 hero + trace note use hard-coded English strings (admin surface — English-primary per doctrine). ✅ No ES regression (matches pre-19.28 behavior).
- **Shop Hub V2 visibility polish:** Section header + tile body strings unchanged — inherits existing ES parity.
- **AdminSideNavV2 +3 routes:** New route labels in `domainMap.js` are English-primary (matches existing admin sidebar labels). Admin surface — no ES regression.

## Language toggle discoverability

- `<LangToggle />` in every portal header (verified in Track 19.27 sidebar audit).
- Public landing header shows toggle prominently.
- Toggle state persists across route navigations (`localStorage.masci.lang`).

## Findings

- No P0 bilingual defects.
- No P1 bilingual defects.
- No English-only field-facing strings identified in Track 19.27 bilingual audit.
- No Spanish leakage in English mode.
- Spanish input submits correctly to canonical English backend record.

## Verdict

🟢 **GO for pilot.** Bilingual coverage is complete on every field-facing surface. Translation-on-submit doctrine preserves audit trail integrity. No known ES defects.
