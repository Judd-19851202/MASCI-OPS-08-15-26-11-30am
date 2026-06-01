# Sprint 1C/1D · Deployment Risk Report

**Batch:** OMEGA Pre-Deployment Certification Gate · Sprint 1C (Incident Delete) + 1D (UI Hygiene)
**Date:** 2026-02-27
**Mode:** Risk classification only · no code · no fixes · no deploy · no DB writes.

This report classifies the deployment risk for Sprint 1C/1D against four operational dimensions and documents the rollback procedure. Companion to `SPRINT1C1D_PRE_DEPLOY_CERTIFICATION.md` (evidence) and `SPRINT1C1D_GO_NO_GO_DECISION.md` (verdict).

---

## 1 · Risk classification summary

| # | Dimension | Risk |
|---|---|---|
| 1 | Incident workflow | 🟢 LOW |
| 2 | UI changes | 🟢 LOW |
| 3 | Platform stability | 🟢 LOW |
| 4 | Rollback complexity | 🟢 LOW |

🟢 **Aggregate deployment risk: LOW.**

---

## 2 · Dimension 1 · Incident workflow

### 2.1 · Risk factors evaluated

| Factor | Pre-Sprint | Post-Sprint | Risk |
|---|---|---|---|
| Auth gate | Admin or PM token (require_admin) | **Unchanged** — Admin or PM | 🟢 |
| Identifier resolver | UUID only; doc_id → 404 | UUID **or** doc_id; resolution exact-match | 🟢 |
| Behaviour on missing record | 404 | 404 | 🟢 |
| Behaviour on linked CAPAs | 200 silently (orphan-creating) | **409 + structured detail** (blocks orphan creation) | 🟢 (stricter; safer; cannot regress legitimate workflows) |
| Audit trail | None | `audit_events.kind=incident_deleted` row with actor/ip/ua/doc_id | 🟢 (additive — append-only) |
| Cascade to notifications / tasks / R2 blobs | None (orphans) | Still none (D-4 deferred) | 🟡 (no improvement, but no worsening either) |
| Sibling routes (`/inspections`, `/meetings`, `/jhas`, `/daily-reports`) | Identical 5-line legacy delete | **Unchanged** | 🟢 (zero spillover) |

### 2.2 · Caller analysis

| Known caller | Path argument | Risk under new contract |
|---|---|---|
| `IncidentsDashboard.jsx:50` (`api.delete('/incidents/' + it.id)`) | UUID | 🟢 unchanged success path |
| `ViewIncident.jsx:209` (`api.delete('/incidents/' + id)` from `useParams`) | UUID | 🟢 unchanged success path |
| Hypothetical CSV-driven admin batch passing doc_id | doc_id | 🟢 **previously 404 → now succeeds** (additive flexibility) |
| Hypothetical caller relying on 200-when-CAPA-linked | Either | 🟡 such a caller would now receive 409 — but no such caller has been identified in the codebase or in any operator workflow. Pre-Sprint behaviour was orphan-producing and would have left audit gaps; the new 409 is the right contract. |

### 2.3 · Verdict

🟢 **LOW.** The route is strictly safer (CAPA block prevents orphan creation; audit row prevents undocumented deletion) and strictly more flexible (doc_id acceptance) than before. The pytest battery (7/7) explicitly certifies the contract.

---

## 3 · Dimension 2 · UI changes

### 3.1 · Risk factors evaluated

| Factor | Risk |
|---|---|
| JSX-tree change in HrHub.jsx | 🟢 NONE — only className string mutated |
| JSX-tree change in IncidentsDashboard.jsx | 🟢 NONE — only catch-block body expanded (different branches inside an existing try/catch) |
| JSX-tree change in ViewIncident.jsx | 🟢 NONE — same shape as IncidentsDashboard |
| New dependencies | 🟢 NONE |
| New i18n keys | 🟡 5 new English toast strings; ES locale falls back to English (current behaviour for un-keyed strings in this codebase) |
| Accessibility regression | 🟢 IMPROVED — `aria-label="Sign out"` added to icon-only mobile button |
| Visual smoke (desktop / tablet / mobile) | 🟢 — captured in `sprint1c1d_cert_evidence/hr_hub_{desktop,tablet,mobile}_*.png` |
| ESLint clean | 🟢 |

### 3.2 · Verdict

🟢 **LOW.** Three small CSS/catch-block deltas. No JSX shape change. Lint clean. A11y improved. Visual cert clean across three viewports.

---

## 4 · Dimension 3 · Platform stability

### 4.1 · Regression test coverage

| Suite | Pass | Notes |
|---|---|---|
| Sprint 1C targeted (7 cases) | 7/7 | Direct contract for the new route |
| Accountability (Pillar 1 · phase 1a2 → 1a5) | 108/108 | Pillar 1 untouched; projection / service / owner-fidelity intact |
| Command Center + incident bundle | 71/71 | Includes `test_iter368_incident_capa_reverse_link.py` — closest neighbor of Sprint 1C CAPA-block logic |
| **TOTAL** | **186/186** | **0 failures · 0 errors** |

### 4.2 · Live health probes (preview)

| Domain | Status |
|---|---|
| `/api/health` · `/api/version` · `/api/admin/check` | 🟢 200 |
| `/api/admin/backups` (schedule + payload sane) | 🟢 200 |
| `/api/admin/command-center/snapshot` | 🟢 200 |
| `/api/admin/accountability/{sources,snapshot}` | 🟢 200 |
| `/api/auth/me-directory` (no token) | 🟢 401 (gate intact) |
| `/api/incidents` + `/api/incidents.csv` (admin) | 🟢 200 |
| Sibling DELETE routes (inspections/meetings/jhas/daily-reports/incidents · no token) | 🟢 401 ×5 |

### 4.3 · Production probes (read-only)

| Endpoint | Status |
|---|---|
| `https://mascidocs.com/api/health` | 🟢 200 |
| `https://mascidocs.com/api/version` | 🟢 200 |

### 4.4 · Verdict

🟢 **LOW.** 186/186 tests pass · 16/16 preview health probes 🟢 · production untouched + healthy.

---

## 5 · Dimension 4 · Rollback complexity

### 5.1 · Rollback procedure

```bash
# 1 · Backend route rollback (single revert restores 5-line legacy delete)
cd /app && git checkout HEAD~N -- backend/routes/safety.py
# supervisorctl restart NOT required (hot reload via uvicorn)
# expected: legacy DELETE behaviour restored within < 10 seconds

# 2 · Frontend rollback (three files; CRA hot reload picks up automatically)
cd /app && git checkout HEAD~N -- \
  frontend/src/pages/HrHub.jsx \
  frontend/src/pages/IncidentsDashboard.jsx \
  frontend/src/pages/ViewIncident.jsx
# expected: CRA dev server rebuilds within < 60 seconds in preview;
# production via supervisor restart of frontend service

# 3 · Test file removal (optional — pytest no longer references the new route's 409 path)
rm /app/backend/tests/test_sprint1c_incident_delete.py
# (only delete if rollback caller wants to remove all Sprint 1C artifacts)

# 4 · Verify rollback
URL=$(grep REACT_APP_BACKEND_URL /app/frontend/.env | cut -d= -f2)
curl -s -o /dev/null -w "%{http_code}\n" -X DELETE "$URL/api/incidents/cert-bogus"
# expected: 401 (auth gate intact)
```

### 5.2 · Rollback-impact analysis

| What persists if rolled back | Impact |
|---|---|
| `audit_events.kind=incident_deleted` rows written before rollback | 🟢 NONE — append-only metadata; orphan-safe; admin audit dashboard ignores unknown kinds gracefully |
| Synthetic test fixtures from `tests/test_sprint1c_incident_delete.py` | 🟢 NONE — tests reap fixtures in `finally` blocks; preview DB only |
| Memory reports (`SPRINT1C_*.md`, `SPRINT1D_*.md`, `CRITICAL_FIX_SPRINT1C1D_*.md`) | 🟢 NONE — historical record |
| Production DB state | 🟢 NONE — Sprint 1C/1D never wrote to production |

### 5.3 · Rollback duration

| Action | Wall-clock |
|---|---|
| Backend revert + hot-reload | < 60 seconds |
| Frontend revert + supervisor restart | < 2 minutes |
| Post-rollback health verification (4 curl probes) | < 30 seconds |
| **End-to-end rollback total** | **< 3 minutes** |

### 5.4 · Verdict

🟢 **LOW.** Single git revert per file. No DB migration. No env var. No new index. No schema change. No new collection. Audit rows from the new contract are append-only and harmless if the contract reverts.

---

## 6 · Aggregated risk × mitigation matrix

| Risk vector | Likelihood | Impact | Mitigation in place |
|---|---|---|---|
| New 409 surfaces on a previously-orphan-producing legitimate workflow | Vanishingly low — no such caller identified | Operator sees a clearer error message instead of silent orphan-creation | Pre-Sprint behaviour was strictly worse (silent orphans + no audit). Operator clears the blocking CAPA via existing Safety Portal CAPA panel. |
| doc_id branch accepts a doc_id that exists but the caller didn't intend | Vanishingly low — UUID and doc_id formats don't collide | Wrong incident deleted | Confirmation dialog already exists in both frontend callers (`window.confirm`). |
| Audit `insert_one` fails on Mongo transient error | Low | Delete still succeeds; audit row missing for that event | Try/except swallows the audit failure — by design, the delete contract is the priority. Operationally detectable via `audit_events.count_documents` drift over time. |
| HR Sign Out button visually regresses on an unanticipated viewport | None | Pure CSS-class delta; identical DOM tree | 3-viewport visual cert (desktop / tablet / mobile) clean |
| Sibling DELETE routes regress | None — not modified | n/a | 5/5 sibling-DELETE 401 probes confirm intact |
| Pillar 1 Accountability projection regresses on `kind=deleted` audit row | None — projection ignores `audit_events.kind` field | n/a | 108/108 Pillar 1 tests pass post-Sprint |

---

## 7 · Verdict

**Aggregate deployment risk classification:** 🟢 **LOW**

* Incident workflow: 🟢 LOW
* UI changes: 🟢 LOW
* Platform stability: 🟢 LOW
* Rollback complexity: 🟢 LOW

**Rollback procedure documented above.** End-to-end rollback wall-clock: < 3 minutes.

🛑 STOP. See `SPRINT1C1D_GO_NO_GO_DECISION.md` for the operator-facing verdict.
