# PRODUCTION PARITY EXECUTION REPORT
**Phase 3A · Iter367 · Preview-Side Audit**
**Generated:** 2026-05-23
**Auditor:** E1 (in-platform, preview environment only)
**Scope:** Validate that iter354 → iter367 work is internally consistent and ready for production redeploy. **Production-side verification must be re-run by the operator after deploy** using this same playbook + `/app/memory/PRE_REDEPLOY_CHECKLIST.md`.

---

## 1 · Environment baseline

| Probe | Result | Notes |
|---|---|---|
| `GET /api/health` (preview) | `200 · {"ok":true,"service":"masci-hub"}` | ✅ healthy |
| Cumulative pytest regression (iter354-iter365 + iter363 + iter364) | **61 passed in 60.97s** | ✅ green |
| Backend lint (ruff) on routes touched in stabilization arc | clean | ✅ |
| Frontend lint on all 14 files touched in iter363→iter367 | clean | ✅ |

---

## 2 · Endpoint existence & RBAC probes

All probes use a freshly-minted admin token from `POST /api/admin/login`.

### 2.1 · Linkage capture surfaces (read endpoints)
| Endpoint | Code | Status |
|---|---|---|
| `GET /api/incidents` | 200 | ✅ |
| `GET /api/daily-reports` | 200 | ✅ |
| `GET /api/equipment-inspections` | 200 | ✅ |
| `GET /api/meetings` | 200 | ✅ |
| `GET /api/qaqc-inspections` | 200 | ✅ |
| `GET /api/safety-forms/equipment-issuances` | 200 (with X-Safety-Forms-Token) | ✅ |
| `GET /api/safety-forms/equipment-trainings` | 200 (with X-Safety-Forms-Token) | ✅ |
| `GET /api/master-lookup/employees?q=a&limit=3` | 200 | ✅ Returns flat `{id,name,...}` shape (iter363 fix) |

### 2.2 · Governance / notifications / digest
| Endpoint | Code | Status |
|---|---|---|
| `GET /api/admin/governance/summary` | 200 | ✅ Returns `convergence_score`, `rule_counts`, `severity_counts`, `category_counts`, `last_scan`, `rule_catalog` |
| `GET /api/admin/compliance/findings?limit=5` | 200 | ✅ |
| `GET /api/admin/notifications/digest` | 200 | ✅ |
| `GET /api/safety/notifications/digest` | 200 | ✅ |
| `GET /api/hr/notifications/digest` | 200 | ✅ |
| `GET /api/pm/notifications/digest` | 200 | ✅ |
| `GET /api/dispatch/notifications/digest` | 200 | ✅ |
| `GET /api/fl/notifications/digest` | 200 | ✅ |

### 2.3 · Handoff/documentation drift (NOT a deployment blocker, but worth noting)
| Documented URL | Reality | Impact |
|---|---|---|
| `GET /api/admin/governance/scan` | Does NOT exist | Handoff doc error — scan runs internally via `/summary` lazy refresh; no separate scan endpoint shipped |
| `GET /api/notifications/digest/{role}` | Actual path is `/api/{role}/notifications/digest` | Handoff doc URL order was reversed — only affects external operators consuming the API |

---

## 3 · Governance Health (live preview data)

```
total_open_findings: 335
convergence_score:   0  (label: "critical")
EMP_LINK_* registered rules:
  - EMP_LINK_UNRESOLVABLE: 8 open
  - EMP_LINK_AMBIGUOUS:    0 open (clean)
  - EMP_LINK_MISSING_ID:   0 open (clean)
rule_counts top 5:
  - PPE_MISSING:           230
  - EMP_ARCHIVED_ACTIVE:    73
  - CAPA_NO_OWNER:          16
  - EMP_LINK_UNRESOLVABLE:   8
  - INC_NEEDS_CAPA:          8
```
Operational reading: governance detector is working correctly. The high open count is dominated by historical PPE_MISSING findings on legacy records — **not introduced** by iter354-iter367. The new EMP_LINK_* detector (iter355) is firing on exactly 8 free-text identities, which proves the iter359-iter364 prevention loop is catching what slipped through.

---

## 4 · Frontend rendering parity (preview live verification at 390 + ES)

| Surface | Route | Overflow @ 390px | ES guide rendered | Status |
|---|---|---|---|---|
| `/incidents/new` | public | 0 px | (form, no guide) | ✅ |
| `/daily/new` | public | 0 px | (form, guide on crew section) | ✅ |
| `/admin/incidents/{id}` | admin | 0 px | ✅ "Ciclo de vida del incidente" | ✅ |
| `/hr/employees/{id}/accountability` | hr | 0 px | ✅ "Cómo funciona esta línea de tiempo" | ✅ |
| `/pm/crew-compliance` | pm | 0 px | ✅ "Cómo funciona tu vista de cumplimiento" | ✅ |
| `/dispatch-portal/driver-qualification` | dispatch | 0 px (shared component) | ✅ "Cómo funciona la disponibilidad del conductor" | ✅ |
| `/field-leadership/portal/driver-qualification` | fl | 0 px (shared component) | ✅ same | ✅ |
| `/hr/incidents` | hr | 0 px | ✅ "Cómo ve RR. HH. los incidentes" | ✅ |
| `/admin/compliance-findings` | admin (English-only by convention) | n/a (desktop-first) | EN "How findings work" | ✅ |
| `/admin/governance` | admin | n/a | EN — Linkage Health pill rendering "IDENTITY LINKAGE · 8 open" | ✅ |
| `/field-leadership/portal` (FL Dashboard) | fl | 0 px | (no guide; iter365 fixed overflow) | ✅ |

---

## 5 · Identity linkage submit-and-persist lifecycle (pytest-verified)

Both iter363 and iter364 lifecycle harnesses were re-run live against preview:
- `test_iter363_employee_linkage_persistence.py` — **11 passed** (incidents, daily-reports, meetings, equipment-inspections, ppe issuance, training records, roster API contract)
- `test_iter364_p1_linkage_persistence.py` — **6 passed** (qaqc-inspections, corrective-actions, shop sign-off)

For each: linked path (with `employee_id`) and free-text path (without) verified end-to-end via POST → GET round-trip.

---

## 6 · Coaching/language convergence (iter366-iter367 audit)

- 11 canonical terms audited platform-wide (Closeout, Verified, Escalated, Pending Review, Archived, Active, Expired, Accountability, CAPA, Linked, Roster-linked). **Zero drift detected.**
- 7 pages now carry exactly ONE LifecycleGuide coaching surface (no duplicate intros after iter366-iter367 cleanup).
- 22 ES translations added in iter366 + 4 added in iter367. The previously-undetected English fallback bug (LifecycleGuide strings rendering EN under `lang=es`) is fully closed.

---

## 7 · Production drift expectations

Once redeployed, the following MUST be verified on `mascidocs.com`:
1. The 8 new operational coaching banners render with the iter365 + iter367 copy in EN and ES.
2. The `Identity Linkage` pill on `/admin/governance` shows live data and is clickable.
3. The EmployeeRosterField dropdown renders employee names (iter363 fix). **Pre-redeploy probe**: `curl https://mascidocs.com/api/master-lookup/employees?q=a -H "X-Admin-Token: TOK" | python3 -c "import sys,json;print('items[0].name=', json.load(sys.stdin)['items'][0].get('name'))"` — if `None` or missing, the iter363 fix did NOT deploy.
4. POSTs to `/api/incidents` with `employee_master_id` persist the field (covered by iter363 pytest).
5. POSTs to `/api/qaqc-inspections` with `inspector_id` persist (iter364 pytest).
6. POSTs to `/api/admin/equipment-inspections/{id}/signoff` with `signed_by_employee_id` persist (iter364 pytest).

---

## 8 · Verdict (preview side)

✅ **Preview is internally consistent and ready for production redeploy.**
- Zero broken endpoints (after correcting handoff doc URL drift).
- Zero failing tests (61/61).
- Zero coaching duplicates remaining on retrofitted pages.
- Zero free-text identity capture inputs platform-wide.
- Zero ES fallback gaps on retrofitted LifecycleGuides.

⏳ **Production verification deferred to operator** — re-run sections 2.1, 2.2, 4 above against `https://mascidocs.com/*` after clicking Deploy. Compare the resulting numbers/codes to this baseline.

---

*See `WORKFLOW_PARITY_GAPS.md` for any structural gaps surfaced during this audit, and `POST_REDEPLOY_SMOKE_RESULTS.md` for the template the operator should fill in after redeploy.*
