# MOBILE DEPLOYMENT CERTIFICATION

_Phase V-Prelude · Deployment Readiness · Track 6 · 2026-05-29T00:23Z_

Mobile readiness audit for iPhone and iPad across PM, Safety,
Dispatch, Field-Leadership; with explicit focus on the Wave 1.1
Operational Timeline Sidecar, uploads, drawers, navigation, and photo
flows.

---

## 1 · Doctrine references

- `MOBILE_UX_REFINEMENT_AUDIT.md` (V-Prelude planning, mobile polish backlog)
- `MOBILE_CHRONOLOGY_CERTIFICATION.md` (Wave 1.1 mobile contract for the timeline sidecar)
- `MOBILE_RHYTHM_REPORT.md` (iPhone scenarios · stop-the-line conditions)
- `FIELD_WALK_CHECKLISTS/MobileSafari.md` (iOS Safari checklist)
- `DAILY_REPORT_DEVICE_MEMORY_MODEL.md` ⛔ (crew memory + preload doctrine)
- `DATA_SURVIVABILITY_AUDIT.md` ⛔ (TRUST-1 root: offline drafts, IDB queue)
- `touch_target_audit.py` (CI tool; emits a touch-target report)

---

## 2 · Coverage statistics (static)

| Measurement | Count |
|---|---|
| Files in `frontend/src/**` using mobile primitives (`useMobile` / `isMobile` / `md:` / `sm:` / `@media`) | 263 |
| Files using Drawer / `sm:hidden` / `lg:hidden` | 161 |
| Pages with explicit mobile path | every PM / HR / Safety / Dispatch / FL surface |

---

## 3 · Per-surface readiness

| Surface | iPhone | iPad | Notes |
|---|---|---|---|
| PM Hub (`/pm/hub`) | ✅ | ✅ | hub cards stack on `<md`, two-column on `≥md` |
| PM Project Detail (`/pm/projects/:projectNumber`) | ✅ | ✅ | content + Timeline Sidecar; sidecar stacks below content on `<md` (per `MOBILE_CHRONOLOGY_CERTIFICATION.md`) |
| PM Daily Reports | ✅ | ✅ | full mobile path, offline-draft via IDB |
| Safety Hub | ✅ | ✅ | iter318 safety hub calm pass |
| Safety Incidents (write) | ✅ | ✅ | photo upload, signature pad, drawer-style fields |
| Safety CAPAs / Forms | ✅ | ✅ | iter319/320/321 cross-portal calm pass |
| Safety Cards (Field Safety Cards) | ✅ | ✅ | text-first, no badges |
| Dispatch Board | ✅ | ✅ | iter321 dispatch calm pass; bounded mobile read |
| Dispatch Driver Day-1 Debrief | ✅ | ✅ | magic-link iter437; chunked upload |
| Field-Leadership Hub | ✅ | ✅ | iter314 mobile path certified |
| Field-Leadership Daily Reports (author) | ✅ | ✅ | full author flow + offline draft + queue |
| HR Hub / People | ✅ | ✅ | iter317c grouped cards |
| HR Time-Off | ✅ | ✅ | iter222 helptips |
| Admin Hub | ✅ | ✅ | secondary surface; not field-critical |
| **Operational Timeline Sidecar** (NEW · Wave 1.1) | ✅ | ✅ | calmness probe score 0.0 across 2 mobile viewports; certified by `MOBILE_CHRONOLOGY_CERTIFICATION.md` |

---

## 4 · Upload flows

Doctrine: **chunked uploads** to bypass proxy limits + IDB-backed retry
queue + R2 destination with inline fallback (degraded mode).

| Flow | Path | Storage | Resilience | Status |
|---|---|---|---|---|
| Daily Report photos | `/api/daily-reports/.../photos` (or job-photos route) | R2 | IDB queue · chunked · retry | ✅ |
| Safety Incident photos | `/api/safety/incidents/.../photos` | R2 | IDB queue · chunked · retry | ✅ |
| Pre-Op / DVIR photos | `/api/preops/...` · `/api/dvirs/...` | R2 | IDB queue · chunked · retry | ✅ |
| Photo Governance registry (Wave 1) | `/api/operational/photo-governance/*` | metadata only · no binary | n/a | ✅ |
| Operational Attachments substrate | `/api/operational/attachments/*` | R2 (binary off-path) | inherits Daily-Report resilience | ✅ |

Deploy-readiness probe confirms:
- `r2` ✅ uploads will land in R2
- `r2_degraded_24h` ✅ 0 fallback-to-inline events in last 24h

---

## 5 · Drawer + navigation rhythm

| Pattern | Doctrine | Status |
|---|---|---|
| Sheet-style drawer for record details on `<md` | `CROSS_PORTAL_CONSISTENCY_STANDARD.md` | ✅ enforced |
| Top-left back link on every record page | `CONTEXTUAL_RETURN_PATH_AUDIT.md` | ✅ enforced |
| Bottom-of-viewport primary action on `<md` | per-page (PM Daily Reports, Safety Incidents) | ✅ |
| Sidebar V2 collapses to top-nav on `<md` | five sidebar V2 components | ✅ when flag on |
| Photo carousel scroll behavior | `useMobile` + touch swipe | ✅ |

---

## 6 · Touch-target audit

`scripts/touch_target_audit.py` exists as the CI tool for ≥ 44×44 pt
touch targets. Spot-check during this audit:

- Hub-page primary cards ≥ 64×64 — ✅
- Form-field submit buttons ≥ 44×44 — ✅
- Timeline Sidecar interactive elements: **none** (passive, read-only —
  no touch targets at all). ✅

---

## 7 · Offline / data survivability (TRUST-1)

| Capability | Path | Status |
|---|---|---|
| IDB draft persistence (Daily Reports, Safety Incidents) | `frontend/src/lib/idbDraft.js` | ✅ green pill on field walks |
| Outbox / retry queue | inline in idbDraft | ✅ |
| Draft telemetry visibility | `/api/draft-telemetry/*` · `TRUST-1 TF-018` gate | ✅ route live · 0 events recently |
| Archive-on-delete (soft-delete + 90d retention) | Mongo + idbDraft | ✅ |

Per `MOBILE_RHYTHM_REPORT.md`, no stop-the-line conditions observed in
the iPhone scenarios documented during Wave 1.1.

---

## 8 · Timeline Sidecar mobile contract (Wave 1.1)

Quoting `MOBILE_CHRONOLOGY_CERTIFICATION.md`:

- Stacks below project content on `<md` (no horizontal squeeze).
- Read-only — zero buttons, zero touch targets, zero badges.
- No more than 12 visible rows above the fold; the rest scrolls.
- Z-suffixed UTC timestamps; render-local via `lib/dateUtils.js`.
- Calmness probe score on 2 mobile viewports: 0.0 with 0 gate breaches.

✅ Contract upheld in the latest `fork-stability-sweep` trendline entry.

---

## 9 · Known limitations (advisory · not blockers)

| Limitation | Surface | Workaround |
|---|---|---|
| Sidebar V2 not promoted to mobile default on any portal | all 5 portals | legacy single-column ships by default; operator can opt in per URL |
| Wave 2 Discovery surfaces (Operational Search, Field Memory rich UI) not yet built | n/a — Wave 2 LOCKED | none needed; Wave 2 itself is locked |
| Mobile polish backlog items in `MOBILE_UX_REFINEMENT_AUDIT.md` | spot polish (spacing, tap rhythm) | scheduled for V-Prelude Wave 3 (Resilience + Mobile polish) — LOCKED |
| Master-binding coverage warning (corrective_actions / incidents) | indirect mobile impact (sparser surface filters) | post-deploy backfill via admin tools |

None of these block the deploy.

---

## 10 · Verdict

**MOBILE DEPLOYMENT: ✅ PASS.**

- All operator-critical surfaces have certified iPhone + iPad paths.
- Wave 1.1 Timeline Sidecar mobile contract upheld and probe-verified.
- Upload resilience: 0 R2 fallback events in last 24h; chunked + IDB
  queue + retry intact.
- Drawer / navigation / return-path doctrine consistent across surfaces.
- Touch-target audit tool exists in CI; no field violations observed.
- TRUST-1 offline survivability still green.

Track 6 of 8 · ✅ pass.
