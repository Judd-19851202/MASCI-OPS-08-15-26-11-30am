# MASCI Platform — Preserve List (Track 13.4C · Deliverable #3)

**Mandatory before any future fix work begins.**  
**Lens:** "What is good today and MUST NOT be destroyed by the recovery process?"  
**Mode:** documentation only · no implementation · no design.

The audit found drift and gaps, but it also found strengths. Recovery
must protect these.

---

## PRESERVE AT ALL COSTS

### 1. Trench Safety architecture
- **Why it works:** Trench Safety is the most fully-realized module on the
  platform. 23 dedicated pages, 15+ trench-specific Mongo collections,
  bilingual wallet cards (Phase 2B noted), QR landings, public excavation
  forms, dedicated leadership digest, repair-review workflow, asset
  detail with rated-depth governance, public references and tabulated
  data.
- **Why it should stay:** It is the platform's exemplar of role-first,
  field-first design. Other modules should *grow toward this pattern*,
  not away from it.
- **What must not change:** the role-first separation
  (`TrenchSafetyOpsCenter` vs `PublicTrenchSafetyDashboard`),
  the QR landing flow (`TrenchSafetyQrLanding`), and the
  rated-depth acknowledgement (V-09 / R-06 cross-portal language fix
  must not bleed in and "simplify" this module).

### 2. PM portal rebuild improvements (Track 13.4A baseline)
- **Why it works:** PM Command Center now answers the "what requires
  PM attention today?" question with PM-scoped data — verified end-to-end
  via the new `pm.demo@mascigc.com` fixture (Track 13.4A §9). `compute_pm_scope` correctly partitions by `pm_email` + `co_pm_emails`.
- **Why it should stay:** It is the working prototype for the
  role-first portal pattern.
- **What must not change:** the scoping function
  (`pm_auth.compute_pm_scope`), the `/api/admin/jobs` 401-for-PM
  hardening (iter180), and the PM fixture seeder
  (`/app/backend/scripts/seed_pm_demo_fixture.py`).

### 3. Dispatch Map recovery (Track 13.4A)
- **Why it works:** Real tiles render, real markers cluster, the
  filter symmetry bug was found and fixed, and a pixel-level visual
  guardrail now prevents the failure class from recurring.
- **Why it should stay:** Dispatch is the platform's operational
  truth surface.
- **What must not change:** `preserveDrawingBuffer: true`, the scoped
  CSS override block on `[data-testid="dispatch-map-canvas-wrap"]`,
  the empty-status-array fallback to `ALL_BANDS`, and Phase 4 of
  `predeploy_certify.sh` that runs the guardrail.

### 4. Cross-portal Operations Map consistency (D-09)
- **Why it works:** `DispatchMapHero` and `/operations-map` consume
  the same hook (`useMapSnapshot`) and the same endpoint. There is
  no second source of truth for fleet position.
- **Why it should stay:** Single-source-of-truth is the only way
  Dispatch and Operations remain coherent as the platform grows.
- **What must not change:** `useMapSnapshot.js` must remain the
  single client-side fetcher; the operations-map snapshot endpoint
  must remain the single API.

### 5. Per-portal authentication isolation (iter180 hardening)
- **Why it works:** Every per-portal `/api/admin/*` route rejects
  per-portal tokens (PM, HR, Dispatch, etc.) with 401. Phase 1 §B
  documented the per-portal token storage keys.
- **Why it should stay:** Privilege separation. PM cannot read admin
  surfaces even if a PM token leaks.
- **What must not change:** the `require_admin` rejection of PM /
  HR / Dispatch / Shop / Safety tokens.

### 6. Append-only RC Certification Ledger discipline
- **Why it works:** `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md`
  is the auditable history of every track. Tracks 13.4A, 13.4B Phase
  1, 13.4B Phase 2, 13.4B Phase 3 all left a trace.
- **Why it should stay:** It is the only single document a future
  engineer can read to understand "what happened here?"
- **What must not change:** the append-only contract.

### 7. Operational Guidance Center as the cross-portal coaching hub
- **Why it works:** Every portal links to `/guidance?from=portal`.
  `guidance_search_misses` already captures what operators tried to
  look up but couldn't find.
- **Why it should stay:** Centralised coaching with a feedback loop.
- **What must not change:** the `?from=` query convention and the
  single `OperationalGuidanceCenter` entry point.

### 8. Strong operator-native language inside each portal's tile labels
- **Why it works:** Phase 2B §I.2 noted "Daily Report", "Pre-Op",
  "JHA", "Crew", "Project Risk", "Field Truth" all read field-first,
  not engineering-first.
- **Why it should stay:** Verbiage drift is one of the easiest ways
  for a platform to degrade.
- **What must not change:** Operator-native verbs in tile labels
  during any future standardisation pass.

### 9. Safety Forms · Equipment Issuance/Training inline EN+ES legal text
- **Why it works:** The lone form family that ships truly bilingual
  acknowledgement text (Phase 2B §H.1).
- **Why it should stay:** Sets the *floor* for bilingual safety forms.
- **What must not change:** Legal text remains in both languages
  inline (even if it is also moved into a per-tenant config later).

### 10. Track 13.4A Visual Render Guardrail (`test_track_13_4a_dispatch_map_visual_guardrail.py`)
- **Why it works:** Pixel-level canvas inspection, not DOM-only;
  catches the original "DOM-OK / human-blank" failure class with
  precise error messages.
- **Why it should stay:** Operator screenshot wins. This guardrail
  enforces that rule mechanically.
- **What must not change:** The `canvas.toDataURL()` approach, the
  thresholds (`mean ≥ 15 · variance ≥ 5 · unique ≥ 8 · box > 0`),
  and Phase 4 of `predeploy_certify.sh`.

### 11. Working integrations baseline
- **Why it works:** Resend (email), Cloudflare R2 (backups), Motive
  (telematics) integrations are live and instrumented (`integration_health.py`, `IntegrationHealthCard`, `IntegrationEventsCard`,
  `resend_webhook_events`).
- **Why it should stay:** Replacing these is months of work.
- **What must not change:** The integration plumbing
  (`integrations/` route subdir, `integration_settings`,
  `integration_sync_logs`).

### 12. Existing positive tenant-config plumbing (W-17 · W-18)
- **Why it works:** `training_guides`, `training_videos`,
  `digest_settings` are admin-editable today.
- **Why it should stay:** This is the baseline pattern the rest of
  the platform should grow into.
- **What must not change:** The admin-editable surfaces for these
  collections must continue to function.

---

## PRESERVE GUIDANCE FOR DESIGN/REBUILD DECISIONS

Whenever a future track proposes to "simplify", "standardise" or
"rebuild" anything, it MUST first answer:

1. Does this change touch any item on the Preserve List?
2. If yes — does it strictly improve the preserved item, or does it
   change behaviour?
3. If behaviour changes, the change requires explicit operator approval
   before implementation.

This list is the bright line.
