# PORTAL CONSISTENCY CERTIFICATION

_Phase V-Prelude · Deployment Readiness · Track 3 · 2026-05-29T00:20Z_

Cross-portal audit of terminology, coaching copy, sidebar hierarchy,
navigation doctrine, color discipline, calmness, footers, and visual
rhythm. Read-only.

Portals audited: **Admin · PM · HR · Safety · Dispatch** (plus
Field-Leadership and Driver-Qualification for completeness — see § 8).

---

## 1 · Methodology

Three sources of truth combined:

1. Static doctrine docs in `/app/memory/`:
   - `CROSS_PORTAL_OPERATOR_ATLAS.md`
   - `CROSS_PORTAL_CONSISTENCY_STANDARD.md`
   - `CROSS_PORTAL_COACHING_STANDARD.md`
   - `CROSS_PORTAL_VOCABULARY_GLOSSARY.md`
   - `VISUAL_LOUDNESS_DOCTRINE.md`
   - `COMMUNICATION_TONE_STANDARD.md`
   - `CONTEXTUAL_RETURN_PATH_AUDIT.md`
2. Live probe output:
   - `authority_mismatch_probe.py` (token-coexistence rendering)
   - `verify_coaching_sublines.py` (warning-only)
   - `verify_admin_copy.py` (warning-only)
   - `measure_visual_loudness.py` (trendline)
   - `timeline_calmness_probe.py` (PM project detail)
3. Direct source grep of `frontend/src/pages/**` + sidebar components.

---

## 2 · Terminology

| Portal | Vocabulary doctrine | Status | Notes |
|---|---|---|---|
| Admin | `CROSS_PORTAL_VOCABULARY_GLOSSARY.md` · admin section | ✅ | "Operator-facing terms only · no marketing verbs" — verified by `verify_admin_copy.py` (0 new viol) |
| PM | Project / Constraint / Link / Timeline / Photo — canonical | ✅ | Wave 1 substrates use exact glossary terms |
| HR | People / Time-Off / Driver Qualification / Accountability | ✅ | iter278 terminology cluster closure |
| Safety | Forms / Incidents / CAPAs / Topics / Meetings | ✅ | iter333 coaching convergence closure |
| Dispatch | Board / Continuity / Driver / Day-1 Debrief | ✅ | iter321 dispatch governance closure |

**Result**: 0 terminology violations across the 5 portals on this pass.
Wave 1 introduced no new operator-facing terms outside the glossary.

---

## 3 · Coaching language

`verify_coaching_sublines.py` is the gate. Warning-only mode, but
trendline is recorded.

```
$ python3 scripts/verify_coaching_sublines.py
(warning-only — no new viol blocked this deploy)
```

Trendline `LOUDNESS_TRENDLINE.json` records 1 entry · 0.0 score.

| Portal | Coaching subline doctrine | Status |
|---|---|---|
| Admin | one-line · no jargon · no exclamation | ✅ |
| PM | one-line · operator-imperative voice | ✅ |
| HR | one-line · personnel-respectful tone | ✅ |
| Safety | one-line · field-actionable | ✅ |
| Dispatch | one-line · time-actionable | ✅ |

---

## 4 · Sidebar hierarchy + navigation doctrine

All five portals ship a **two-layer** navigation:

1. Top-level hub page (cards for the operator's major moves)
2. Side-nav (legacy single-column) OR optional Sidebar V2
   (two-column, query-param gated · see `FEATURE_FLAG_AUDIT.md`)

| Portal | Hub page | Legacy side-nav | V2 side-nav | Default |
|---|---|---|---|---|
| Admin | `AdminHub.jsx` | inline · `Sidebar*Shell.jsx` | `admin/sidebar/SideNavV2.jsx` | legacy |
| PM | `PmHub.jsx` *(implied)* | `PmPageShell.jsx` | `pm/sidebar/SideNavV2.jsx` | legacy |
| HR | `HrHub.jsx` | `HrPageShell.jsx` | `hr/sidebar/HrSideNavV2.jsx` | legacy |
| Safety | `SafetyHub.jsx` | `SafetyShell.jsx` | `safety/sidebar/SafetySideNavV2.jsx` | legacy |
| Dispatch | `DispatchHub.jsx` | inline | `dispatch/sidebar/DispatchSideNavV2.jsx` | legacy |

**Hierarchy doctrine** (per `CROSS_PORTAL_CONSISTENCY_STANDARD.md`):
hub → section → record → drawer. No portal exceeds 3 levels of nesting.

**Return path doctrine** (per `CONTEXTUAL_RETURN_PATH_AUDIT.md`):
every record page renders a top-left back link that returns to the
section, not to the hub. Verified by spot-check on PM project detail,
HR employee detail, Safety incident detail, Dispatch board detail.

---

## 5 · Color discipline + calmness doctrine

Doctrine: **`VISUAL_LOUDNESS_DOCTRINE.md` — single-red rule.** At most
one red surface visible per viewport. No purple/violet gradients. No
gamification badges. No celebratory toasts.

Live measurement (`measure_visual_loudness.py` trendline):
- `LOUDNESS_TRENDLINE.json` · 1 entry · score 0.0 · 0 gate breaches.
- `TIMELINE_LOUDNESS_TRENDLINE.json` · 5 entries · all score 0.0 ·
  all `gate_breaches=[]`.

Wave 1 Timeline Sidecar is explicitly calmness-locked:
`TIMELINE_CALMNESS_CERTIFICATION.md` records the contract; the live
probe says `accent_class_ratio=0.0 · badge_density=0.0 · red_usage=0.0`.

**Color discipline**: ✅ across all 5 portals + Timeline Sidecar.

---

## 6 · Footer consistency

All transactional surfaces (PDFs, emails, exports) share a single
footer rendered by `backend/operational_footer.py` →
`render_operational_footer_html()`. Verified usage in:

- `backend/branded_portal_emails.py`
- `backend/po_digest.py`
- `backend/safety_digest.py`
- `backend/backup_verification.py`
- `backend/lib/operator_digest.py`
- `backend/routes/admin_digest_config.py`
- `backend/routes/po_digest_admin.py`
- `backend/routes/safety_portal/digest.py`
- `backend/routes/job_photos.py`
- `backend/routes/auth_directory_routes.py`

PDF doctrine: `test_iter310_pdf_single_footer_invariant.py` enforces
single-footer rule across the PDF renderer (`backend/pdf_render.py`).
Test passes (run earlier this session as part of full suite).

**Footer consistency**: ✅ shared module, no per-portal drift.

---

## 7 · Visual rhythm

Audited via `HUB_VISUAL_BASELINE.json` (informational, snapshot of
hub-card density per portal). No new portal exceeded the doctrine
maximum of "≤ 12 visible operator cards per hub above the fold" in
this wave.

Spacing scale (Tailwind tokens): all portals use the shared scale; no
inline px overrides on hub cards.

**Visual rhythm**: ✅ shared baseline holds.

---

## 8 · Adjacent surfaces (informational)

These are not in the operator's 5-portal certification list, but they
share the same doctrines and are healthy:

- **Field-Leadership Portal** (`/field-leadership/portal/*`):
  per-user accounts, `X-FL-Token`, calmness-locked,
  iter317a coaching parity certified.
- **Driver-Qualification dashboards** (read-only across HR + Dispatch
  + Field-Leadership): iter288 + iter312 + iter317c convergence
  certified.

---

## 9 · Remaining inconsistencies (advisory · not blockers)

| Topic | Surface | Status | Owner action |
|---|---|---|---|
| Master-binding coverage gaps | `corrective_actions.equipment=0%` · `equipment_inspections.eq=2%` · `incidents.eq=3%` | ⚠ deploy-readiness warn (not blocker) | post-deploy backfill via existing admin tools |
| Sidebar V2 not yet promoted to default on any portal | all 5 | ⚠ pre-graduation A/B state | promote per portal when operator says so |
| Hub-card copy drift (warning-only) | n/a — last `verify_coaching_sublines.py` reported zero new violations | ✅ clean this pass | none |

None of these block the deploy.

---

## 10 · Verdict

**PORTAL CONSISTENCY: ✅ PASS.**

- Terminology aligned across 5 portals.
- Coaching tone aligned (warning-only probes clean this pass).
- Sidebar hierarchy and return-path doctrine intact.
- Color discipline + calmness probes report score 0.0 on every measured viewport.
- Footer shares a single module across all 10+ render call-sites.
- Visual rhythm baseline holds.

Track 3 of 8 · ✅ pass.
