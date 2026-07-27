# PRODUCTION VERIFICATION CHECKLIST

Environment: Production  
Live URL: `https://mascidocs.com`  
Purpose: Verify the live platform after deployment, capture every defect, and classify root cause before any fix/redeploy cycle.

---

## 1. Rules of execution

- Run this checklist against **Production only**.
- Record **PASS / FAIL / N.A.** for every line.
- Capture screenshots, exact URLs, timestamps, and console/network notes for every failure.
- Do **not** classify truthful RED/AMBER operational posture as a deploy failure unless the surface is broken, inaccessible, blank, misleading, or contradictory.
- If a failure is found, continue the sweep unless the issue is a true platform blocker (site down, auth dead, data authority wrong, or admin control plane inaccessible).

---

## 2. Critical production gate checks

### 2.1 Runtime / identity / health

| Check | Expected result | Evidence to capture |
|---|---|---|
| `GET /api/health` | HTTP `200`, `ok=true` | response body |
| `GET /api/ready` | HTTP `200`, production DB/runtime healthy | response body |
| `GET /api/health/full` | HTTP `200`, no gross startup/runtime failure | response body |
| `GET /api/version` | production runtime identity present, frontend/backend release identity coherent | response body |
| `GET /api/platform/data-truth` | response loads and reflects production truth surfaces | response body |

### 2.2 Super admin continuity

Use real production super-admin credentials.

| Check | Route | Expected result |
|---|---|---|
| Admin sign-in page loads | `/admin/login` | form renders, no blank screen |
| Admin login succeeds | `/admin/login` | lands in Admin, no loop |
| Master sign-in route loads | `/sign-in` | form renders correctly |
| Admin root loads | `/admin` | dashboard renders |
| Session persists across admin routes | multiple | no unexpected logout or 401 loop |

### 2.3 Admin operational surfaces

| Route | Expected result |
|---|---|
| `/admin/system` | page loads with live production system state |
| `/admin/deploy-readiness` | loads and renders truthful deployment posture |
| `/admin/system-health` | loads, not blank |
| `/admin/trust-spine` | loads, truthful trust posture visible |
| `/admin/recovery` | loads, recovery snapshot visible |
| `/admin/scheduler-runs` | loads, scheduler history visible |
| `/admin/integration-truth` | loads, integration truth visible |
| `/admin/governance-trust` | loads |
| `/admin/storage-recovery` | loads |

---

## 3. Portal verification matrix

Use **real production credentials** for each portal. Confirm login, session persistence, landing route, and fail-closed behavior.

| Portal | Login route | Pass criteria |
|---|---|---|
| Admin | `/admin/login` | login works, admin routes accessible |
| PM | `/pm/login` | login works, PM dashboard/hub accessible |
| HR | `/hr/login` | login works, HR dashboard accessible |
| Safety | `/safety-portal/login` | login works, Safety hub accessible |
| Dispatch | `/dispatch-portal/login` | login works, Dispatch hub accessible |
| Shop | `/shop/login` | login works, Shop hub accessible |
| Field Leadership | `/field-leadership/portal/login` and `/leadership/login` | login works, FL dashboard accessible |

### Portal-specific checks

For each successful portal login, verify:

- no redirect loop
- no blank screen
- no stale session-expired overlay
- no console-fatal error
- at least one representative dashboard page loads with meaningful content
- unauthorized admin route access fails closed, not broken-open

---

## 4. Public workflow verification

These routes must remain public where designed.

| Route | Expected result |
|---|---|
| `/daily/submit` | loads anonymously; form usable |
| `/incidents/report` | loads anonymously if intended public; otherwise expected guard behavior |
| `/meetings/submit` | loads correctly |
| `/jha` | loads correctly |
| `/trench-safety` | loads correctly |
| `/trench-safety/excavation/new` | loads correctly |
| `/equipment/submit` | loads correctly if intended public |
| `/fleet/dvir/submit` | loads correctly |

For public workflows, verify:

- no auth gate where public access is expected
- no broken submit form shell
- no missing required assets/scripts
- if a submit smoke is authorized, capture resulting record ID

---

## 5. PM schedule / cost-code / planning verification

This lane validates what exists on the live platform for the rolling schedule system.

### Admin cost-code verification

| Route | Expected result |
|---|---|
| `/admin/cost-registry` | registry loads, table visible, no blank/error state |

### PM planning verification

| Route | Expected result |
|---|---|
| `/pm/project-schedule` | page loads |
| `/pm/jobs` | loads PM jobs |
| `/pm/project/:projectNumber` | representative project page loads |
| `/pm/project-staffing` | loads |

### What to verify on `/pm/project-schedule`

- project selector works
- project schedule loads for an assigned project
- projected finish visible
- critical path count visible
- overall progress visible
- rolling 14-day board visible
- save button present
- DOT schedule report export works
- Monday Look-Behind indicator visible

### Important interpretation rule

This verification proves whether the built surfaces are alive in Production. It does **not** by itself prove that the full closed-loop “why it failed / feed into next two-week plan” process is fully implemented.

---

## 6. Trust / recovery / survivability verification

These surfaces were part of recent critical work and must be checked live.

| Route / API | Expected result |
|---|---|
| `/admin/trust-spine` | page loads; no payload/render break |
| `/admin/recovery` | page loads |
| `/admin/deploy-readiness` | page loads |
| `/admin/system-health` | page loads |
| `/api/admin/deployment-readiness` | returns coherent payload |
| `/api/admin/platform-trust/validate` | returns coherent payload; no secret leakage |
| `/api/admin/recovery/snapshot` | returns coherent payload |
| `/api/admin/backup-verification/state` | reachable |
| `/api/admin/integrations/truth-status` | reachable |
| `/api/admin/scheduler-runs` | reachable |

### Expected nuance

- RED / AMBER status may be truthful and acceptable if operational posture is degraded.
- Fail only if the surface is broken, missing, contradictory, inaccessible, or misleading.

---

## 7. Storage / files / PDFs / photo surfaces

| Surface | Expected result |
|---|---|
| photo upload endpoint | reachable / working |
| job photo libraries | load correctly |
| PDF export pages | export/download works |
| file attachment reads | succeed |
| trench/document/photo references | render or download correctly |

---

## 8. Notifications / integrations / scheduler sanity

| Surface | Expected result |
|---|---|
| integration truth | shows coherent production provider posture |
| notifications surfaces | load |
| scheduler runs | visible |
| backup verification state | coherent |
| payroll variance weekly surfaces | no obvious breakage |

---

## 9. Responsive / UX sweep

Check at minimum:

- Desktop
- Tablet landscape
- Tablet portrait
- Mobile

Pages:

- `/admin/login`
- one admin dashboard route
- one PM dashboard route
- one Safety route
- one public workflow route

Check for:

- horizontal overflow
- clipped forms
- missing primary actions
- broken nav
- blank panels
- unusable tables

---

## 10. Pass/fail record template

| ID | Route / API | Area | Expected | Actual | Pass/Fail | Severity | Screenshot / Evidence | Notes |
|---|---|---|---|---|---|---|---|---|

---

## 11. Severity guide

- **P0** — site down, admin auth dead, wrong environment identity, data authority wrong, protected/public boundary broken, blank shell on core route, critical submission blocked
- **P1** — major portal/dashboard broken, storage/PDF/upload broken, trust/recovery surfaces inaccessible, widespread responsive break
- **P2** — degraded but usable flow, route-level defect, non-critical export issue, warning/UX defect with workaround
- **P3** — cosmetic or minor polish issue
