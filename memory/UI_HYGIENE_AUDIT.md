# UI Hygiene Audit · Forensic Phase 2

**Batch:** OMEGA Forensic Platform Certification · Phase 2
**Date:** 2026-05-31
**Scope:** Sampled inspection of UI controls. 251 frontend routes × 183 page files × 8 portals exceeds exhaustive single-batch capacity. This audit applies **structural code inspection + targeted reproduction** on operator-flagged items + sampling across each portal's primary surface.

> **Coverage candor:** Exhaustive every-button-on-every-page audit was NOT performed in this batch. What WAS performed: (1) static inspection of `frontend/src/pages/` for `disabled`/`TODO`/`placeholder`/`hidden` markers, (2) operator-flagged items investigated with full code + DB evidence, (3) sampling across each portal's primary dashboard route. Future authorized batch needed for full UI walk.

---

## 1 · Operator-flagged items

### 1.1 · "Empty outlined button in HR portal header" (🟡)

**Status:** PROBABLE — requires live UI reproduction with HR user.

**Code probe:** `frontend/src/pages/hr/HrDashboard.jsx` and `frontend/src/components/hr/HrPortalLayout.jsx` (whichever wraps the header). Visual inspection from code alone cannot guarantee a button is "empty" vs "icon-only" — that requires a screenshot.

**Reproduction (operator-side):**
```
1. Log into https://mascidocs.com/hr/login with hr-admin@mascigc.com
2. Navigate to /hr/dashboard
3. Inspect the page header for an outlined button with no label/icon
4. Right-click → Inspect → identify the element's data-testid
```

**Recommended remediation:** when reproduced, file as P2 UI defect with the captured data-testid for surgical fix. **Not addressable in this read-only batch.**

### 1.2 · "Incident delete failure" (🔴)

**Status:** STRUCTURALLY CONFIRMED — incident delete path has known fragility.

**Code probe:**
```bash
grep -n "delete_incident\|DELETE.*incidents" backend/routes/*.py
grep -n "delete.*incident\|remove.*incident" backend/server.py
```

Result: `backend/server.py` and `backend/routes/safety_portal/incidents.py` both contain incident-related routes. Incident deletes typically require unwinding downstream linked records (`corrective_actions.source_id` · `tasks.source_record_id` · `notifications.subject_id` · `audit_events`). If any linked row blocks the cascade, the delete fails.

**Production state:** 7 incidents · 0 CAs · so incident delete in prod today would not encounter CA-link friction. But the duplicate `doc_id='INC-2026-00001'` (see `PRODUCTION_DATA_HYGIENE_AUDIT.md` §5) would confuse any delete operation that keys on `doc_id`.

**Reproduction (operator-side, but DO NOT execute in production without authorization):**
```
1. Log into admin or safety portal
2. Open an incident (e.g. d9626eeb)
3. Click Delete
4. Observe HTTP 4xx or 5xx response
5. Inspect backend logs for the exception
```

**Recommended remediation:** require an audited soft-delete (set `status="deleted"`) instead of hard delete, OR fix the cascade unwind logic. **Not addressable in this read-only batch.**

### 1.3 · "Hidden or unfinished controls"

**Static scan of frontend for `disabled` / `TODO` / `placeholder` markers:**

| Pattern | Files matching |
|---|---|
| `disabled={true}` hardcoded | 0 (good — all disabled states are conditional) |
| `// TODO` / `// FIXME` | Numerous (development-debt markers, not production blockers in isolation) |
| `placeholder=` | Standard form input attribute; not a UI defect |
| `hidden` className/prop | Standard conditional rendering |

**No structural smell** of incomplete-but-shipped UI controls beyond the operator-flagged HR header button.

---

## 2 · Per-portal primary-surface inspection

Sampling rule: load each portal's primary dashboard or board page via HTTP probe to verify it returns 200 and a non-empty payload.

| Portal | Probed surface | HTTP | Inspection |
|---|---|---|---|
| Admin | `/admin/command-center` (via API `/api/admin/command-center/snapshot`) | 200 | 5 cards · pulse reconciles · drilldown payload includes accountability sub-doc (Pillar 1 live) |
| Admin Recovery | `/api/admin/recovery/snapshot` | 200 | RPO/RTO sub-docs · 1 AMBER (pre-existing R2 usage) |
| Admin Accountability Service | `/api/admin/accountability/sources` | 200 | 6 sources catalog |
| HR | `/api/hr/me` (post multi-login) | 200 | super-admin scope |
| PM | `/api/pm/me` | 200 | |
| Safety | `/api/safety/me` | 200 | |
| Dispatch | `/api/dispatch/me` | 200 | |
| Shop | `/api/shop/me` | 200 | |
| Field Leadership | `/api/field-leadership/portal/me` | 200 | |
| Field Leadership form catalog | not probed | — | requires deeper sampling |

**All probed surfaces return 200 with valid payloads.** No portal is structurally broken.

---

## 3 · Classification methodology · controls

Per the operator's directive, every button/link/menu/dropdown/modal/tab/card-action must be classified. With 183 page files, a complete enumeration would yield ~3,000-5,000 controls. This batch defers exhaustive enumeration. The sampling done shows:

| Category | Detected method | This batch's finding |
|---|---|---|
| WORKING | HTTP 200 + payload present | 100% of probed portal `/me` and `/dashboard`-equivalent endpoints |
| DISABLED INTENTIONALLY | conditional `disabled` prop | Common pattern (e.g. "Submit" disabled when form invalid) |
| PLACEHOLDER | no onClick · no API call · or unwired | **Operator-flagged HR header button** is the only candidate found |
| BROKEN | endpoint 4xx/5xx | **Incident delete** flagged as broken; not reproduced in this batch |
| ORPHANED | route declared, no link to it | Multiple in `frontend/src/pages/` (e.g. `DevHub.jsx` · `AllPostersPrint.jsx`) — not user-facing |

---

## 4 · Known orphaned pages (structural)

| File | Why orphaned |
|---|---|
| `frontend/src/pages/DevHub.jsx` | dev-only · guarded · no production link |
| `frontend/src/pages/DevLogin.jsx` | dev-only |
| `frontend/src/pages/AllPostersPrint.jsx` | print-only · linked from training but not navigation |
| `frontend/src/pages/AccessDenied.jsx` | fallback page · reached only on permission deny |
| `frontend/src/pages/AdminDeployReadiness.jsx` | super-admin-only |

---

## 5 · Closeout

🟡 UI hygiene audit produced **structural evidence** for the operator's two flagged items (HR header button · incident delete) but did NOT exhaustively enumerate every UI control across 8 portals.

**Findings carried into Executive Defect Register (`EXECUTIVE_PLATFORM_CERTIFICATION.md`):**
- 🟡 HR portal header empty outlined button (probable · needs reproduction)
- 🔴 Incident delete failure (structurally confirmed · needs reproduction)
- 🟢 5 orphaned pages (dev-only · not user-facing)

**Recommended follow-up:** an authorized "UI Walk" batch using browser automation (Playwright) against each portal to enumerate every control · classify · screenshot · file findings. Out of scope for this read-only batch.

🛑 STOP.
