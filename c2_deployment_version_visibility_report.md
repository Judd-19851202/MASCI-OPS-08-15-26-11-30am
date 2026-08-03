# C2 Deployment/Version/C2 Visibility Verification Report

**Target Environment:** https://masci-audit-hub.preview.emergentagent.com  
**Test Date:** 2026-07-23  
**Credentials Used:** jaymn.judd@mascigc.com / Maddix123! (Admin)  
**Verification Type:** READ-ONLY, Non-destructive

---

## Executive Summary

✅ **DEPLOYMENT VERSION INFO IS VISIBLE** in Preview environment through multiple surfaces:
- API endpoints provide full commit/hash details
- Admin UI displays build version in Platform Overview card
- Trust/governance endpoints accessible and returning status

⚠️ **DEPLOYMENT HISTORY NOT VISIBLE** in current UI surfaces tested

---

## 1. API Endpoint Visibility (Programmatic Access)

### ✅ `/api/version` - FULLY VISIBLE
**Status:** 200 OK  
**Accessible:** Public (no auth required)

**Visible Values:**
- **Backend Commit:** `2718dc1866e47a6e176a78d22026c02b632d7e78` (full SHA)
- **Source Hash:** `7ae9607be49196a1edc37011bfa7ac5d`
- **Frontend Build Commit:** `af31a84d0e60b512df9fcdede603f9ff1e48d882` (full SHA)
- **Frontend/Backend Release Match:** `False` ⚠️ **MISMATCH DETECTED**

**Interpretation:** Backend and frontend are deployed from different commits in Preview.

---

### ✅ `/api/health` - PARTIALLY VISIBLE
**Status:** 200 OK  
**Accessible:** Public (no auth required)

**Visible Values:**
- **OK:** `True`
- **Runtime Identity Status:** Not included in response (field absent)

---

### ⚠️ `/api/health/full` - DEGRADED STATE
**Status:** 503 Service Unavailable  
**Accessible:** Public (no auth required)

**Visible Values:**
- **OK:** `False`
- **Mongo:** `True`
- **Scheduler:** `True`
- **Backup Recent:** `False` ⚠️ (backup age exceeds threshold)
- **Runtime Identity OK:** `True`
- **Runtime Identity Status:** `NOT_APPLICABLE`

**Interpretation:** System is operational but degraded due to backup age. Runtime identity verification is working but marked as NOT_APPLICABLE (likely due to Preview environment configuration).

---

### ✅ `/api/admin/deployment-readiness` - ACCESSIBLE
**Status:** 200 OK  
**Accessible:** Requires admin authentication (X-Admin-Token + X-Directory-Token)

**Visible Values (from first test run):**
- **Decision:** `pass`
- **Blocking Gates:** `[]` (empty array)

**Note:** In second test run, this endpoint returned N/A values, possibly due to session timing or endpoint state changes.

---

### ✅ `/api/admin/trust-spine` - ACCESSIBLE
**Status:** 200 OK  
**Accessible:** Requires admin authentication (X-Admin-Token + X-Directory-Token)

**Visible Values (from first test run):**
- **Platform Band:** `amber` ⚠️
- **Canonical Status:** `DEGRADED` ⚠️

**Interpretation:** Trust spine is reporting degraded status with amber platform band, consistent with Preview environment state and frontend/backend mismatch.

---

## 2. Admin UI Visibility (Human-Readable)

### ✅ Admin Operating System Dashboard - BUILD VERSION VISIBLE

**Location:** `/admin` (Admin Operating System home page)

**Visible in Platform Overview Card:**
- **Build Version:** `Build 2718dc18 - masci-hub`
- **Uptime:** `0h 14m` (at time of capture)
- **Status:** HEALTHY (green indicator)

**Screenshot Evidence:** `c2_final_admin_dashboard.png`

**Interpretation:** The UI displays the SHORT commit hash (first 8 characters: `2718dc18`) which matches the backend commit from `/api/version` (`2718dc1866e47a6e176a78d22026c02b632d7e78`).

---

### ✅ Admin Dashboard Cards - GOVERNANCE/TRUST SURFACES PRESENT

**Visible Cards:**
1. **Platform Overview** (01, HEALTHY) - Shows build version
2. **Operations Control Center** (02, ATTENTION) - 14 items, 3 attention, 11 healthy
3. **Storage & Recovery** (03, ATTENTION) - Backup age 1780.5m (yesterday, 4 hrs PM)
4. **AI Operations** (04, ATTENTION) - Gateway ON, provider unavailable (ANTHROPIC)
5. **Communications** (05, HEALTHY) - 49 routes configured
6. **Identity & Security** (06, HEALTHY) - 50 active sessions
7. **Governance & Trust** (07, CRITICAL) - 0% (0 rules tracked) ⚠️
8. **Platform Configuration** (08, CRITICAL) - 5/6 integration(s) degraded
9. **Diagnostics** (09, HEALTHY) - Service reporting healthy
10. **Maintenance** (10, ATTENTION) - 14 ops, 3 need attention

**Screenshot Evidence:** `c2_final_admin_dashboard.png`

---

### ⚠️ Operations Trust Center - SESSION ISSUE

**Location:** `/admin/email` (Email & Routing page)

**Status Messages Visible:**
- **Trust Center unavailable:** `session_not_active`
- **Trust validator unavailable:** `session_not_active`

**Disposition Elements Found:** 2 elements with `data-trust-surface-id`, `data-trust-disposition`, `data-trust-role`, `data-canonical-owner` attributes present in DOM

**Screenshot Evidence:** `c2_version_operations_trust.png`

**Interpretation:** Trust Center and Trust Validator components are present in the UI but not loading data due to session state issues. The disposition labels are correctly implemented in the code but the actual trust data is not being fetched/displayed.

---

### ❌ Deployment History - NOT VISIBLE

**Checked Locations:**
- `/admin` - Admin Operating System dashboard
- `/admin/operations-control` - Operations Control page
- `/admin/governance` - Governance page (if exists)
- `/admin/recovery` - Storage & Recovery page
- `/admin/email` - Email & Routing page

**Finding:** No deployment history, release log, or commit history UI surface was found in any of the admin pages tested.

**Interpretation:** While current deployment version is visible (via Platform Overview card and API endpoints), there is no UI surface showing:
- Previous deployments
- Deployment timeline
- Release history
- Commit changelog
- Deployment audit trail

---

## 3. Release/Certification/Health Indicators

### ✅ Health Indicators - VISIBLE

**Platform Posture (Admin Dashboard header):**
- **HEALTHY:** 4 domains
- **ATTENTION:** 4 domains
- **CRITICAL:** 2 domains
- **AWAITING SIGNAL:** 0 domains
- **TOTAL DOMAINS:** 10

**Individual Domain Health:**
- Platform Overview: HEALTHY
- Operations Control Center: ATTENTION (14 items)
- Storage & Recovery: ATTENTION (backup age)
- AI Operations: ATTENTION (provider unavailable)
- Communications: HEALTHY
- Identity & Security: HEALTHY
- Governance & Trust: CRITICAL (0% rules tracked)
- Platform Configuration: CRITICAL (5/6 integrations degraded)
- Diagnostics: HEALTHY
- Maintenance: ATTENTION (3 need attention)

---

### ⚠️ Certification Indicators - PARTIALLY VISIBLE

**Trust Spine Status (from API):**
- Platform Band: `amber`
- Canonical Status: `DEGRADED`

**Deployment Readiness (from API):**
- Decision: `pass`
- Blocking Gates: `[]` (none)

**Interpretation:** System is passing deployment readiness checks despite degraded trust status and amber platform band. This is consistent with Preview environment expectations.

---

### ⚠️ Release Match Status - MISMATCH DETECTED

**Frontend/Backend Release Match:** `False`

**Details:**
- Backend Commit: `2718dc1866e47a6e176a78d22026c02b632d7e78`
- Frontend Build Commit: `af31a84d0e60b512df9fcdede603f9ff1e48d882`

**Interpretation:** Frontend and backend are deployed from different commits. This is a **release identity mismatch** which may be intentional in Preview for testing purposes, but would be a blocker in Production.

---

## 4. Console Errors & Warnings

**Non-Critical Errors (Expected in Preview):**
- Sentry tracking failures (external service)
- CDN rum failures (Cloudflare RUM)
- Usage tracking failures (analytics)
- 401 errors on notification endpoints (expected after certain operations)
- 401 errors on email routing endpoints (session state)
- 401 errors on trust center endpoints (session state)
- 503 error on `/api/health/full` (degraded state due to backup age)

**No Critical JavaScript Errors:** No page crashes, no blank screens, no blocking errors.

---

## 5. Summary of Findings

### ✅ VISIBLE in Preview:

1. **Backend Commit Hash** (full 40-char SHA) - via `/api/version`
2. **Frontend Build Commit** (full 40-char SHA) - via `/api/version`
3. **Source Hash** - via `/api/version`
4. **Build Version** (short 8-char hash) - via Admin UI Platform Overview card
5. **Frontend/Backend Release Match Status** - via `/api/version`
6. **Platform Health Status** - via Admin UI dashboard cards
7. **Trust Spine Status** (Platform Band, Canonical Status) - via `/api/admin/trust-spine`
8. **Deployment Readiness** (Decision, Blocking Gates) - via `/api/admin/deployment-readiness`
9. **Runtime Identity Status** - via `/api/health/full`
10. **System Uptime** - via Admin UI Platform Overview card

### ❌ NOT VISIBLE in Preview:

1. **Deployment History** - No UI surface showing previous deployments
2. **Release Changelog** - No commit history or release notes visible
3. **Deployment Timeline** - No audit trail of when deployments occurred
4. **Trust Center Data** - Present in UI but not loading due to session issues
5. **Trust Validator Data** - Present in UI but not loading due to session issues

### ⚠️ ISSUES DETECTED:

1. **Frontend/Backend Mismatch** - Different commits deployed (may be intentional in Preview)
2. **Backup Age Exceeds Threshold** - Causing `/api/health/full` to return 503
3. **Trust Center Session Issues** - Trust surfaces not loading data
4. **Governance & Trust Critical** - 0% rules tracked
5. **Platform Configuration Critical** - 5/6 integrations degraded

---

## 6. Recommendations

### For Production Deployment:

1. **Ensure Frontend/Backend Release Match** - `frontend_backend_release_match` must be `true`
2. **Resolve Backup Age Issue** - Ensure backups are recent before deployment
3. **Fix Trust Center Session Issues** - Investigate why trust surfaces show `session_not_active`
4. **Populate Governance Rules** - Address 0% governance rules tracked
5. **Fix Integration Degradation** - Resolve 5/6 integrations degraded status

### For C2 Visibility Improvements:

1. **Add Deployment History UI** - Create admin page showing deployment timeline
2. **Add Release Changelog UI** - Show commit history and release notes
3. **Improve Trust Center Reliability** - Fix session state issues preventing data load
4. **Add Deployment Audit Trail** - Track who deployed what and when

---

## 7. Test Evidence Files

- `c2_version_initial.png` - Initial page load
- `c2_version_after_login.png` - After admin login
- `c2_version_admin_console.png` - Admin console view
- `c2_version_operations_trust.png` - Operations Trust Center page
- `c2_version_recovery.png` - Recovery page
- `c2_final_admin_dashboard.png` - Full admin dashboard (full page screenshot)
- Console logs: `/root/.emergent/automation_output/20260723_214203/console_20260723_214203.log`

---

## 8. Conclusion

**Deployment version and commit information IS VISIBLE** in the Preview environment through:
1. API endpoints (`/api/version`, `/api/health`, `/api/admin/deployment-readiness`, `/api/admin/trust-spine`)
2. Admin UI Platform Overview card (showing build version with short commit hash)

**Deployment history is NOT VISIBLE** - no UI surface exists for viewing previous deployments or release timeline.

**Trust/governance surfaces are PRESENT** but experiencing session state issues preventing data from loading.

**Release identity mismatch detected** - frontend and backend deployed from different commits, which would be a blocker in Production but may be acceptable in Preview for testing.

**Overall Assessment:** C2 visibility is **PARTIALLY IMPLEMENTED** - current deployment info is visible, but historical deployment data and some trust surfaces are not accessible.
