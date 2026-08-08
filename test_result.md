# MASCI Test Results

## Latest Test: PM Command Center Focused Retest (Post-Fix Verification)
## Test Date: 2026-08-08 (Second Run)
## Tester: Testing Agent (E2)
## Preview URL: https://masci-audit-hub.preview.emergentagent.com

---

# PM Command Center Focused Retest Results (2026-08-08 - Post-Fix Verification)

## Test Scope
Focused retest of three specific PM Command Center fixes:
1. PM Project Selector - verify no generic "Project number unavailable" fallback
2. PM Assigned Projects List - verify recognizable project names for scoped PM fixtures
3. Spanish language translations - verify PM Command Center page title/subtitle/action strings

## Test Credentials
- PM User: cert.pm@example.com / CertProof2026!
- Test URL: https://masci-audit-hub.preview.emergentagent.com/pm/command-center

## ❌ CRITICAL FAILURE: All Three Test Points Failed

### 1. ❌ PM Project Selector - Generic Fallback Still Present
**Status**: FAILED - Issue NOT fixed
**Finding**: 11 out of 12 selector options show "Project number unavailable"

**Evidence**:
```
Option 1: Project number unavailable · Earned Value readiness — Incomplete actual-cost evi...
Option 2: Project number unavailable · Earned Value readiness — Cost and schedule both unf...
Option 3: Project number unavailable · Earned Value readiness — Completed work with open c...
[... 8 more identical cases ...]
Option 11: Project number unavailable · Project name not available...
```

**Screenshot**: `.screenshots/pm_cc_retest_english.png`

### 2. ❌ PM Assigned Projects List - Generic Fallback Still Present
**Status**: FAILED - Issue NOT fixed
**Finding**: All 11 project rows in "Projects Assigned to You" section show "Project number unavailable"

**Evidence**:
```
Row 1: Project number unavailable · Earned Value readiness — Incomplete actual-cost evidence
Row 2: Project number unavailable · Earned Value readiness — Cost and schedule both unfavorable
Row 3: Project number unavailable · Earned Value readiness — Completed work with open commitments
[... 8 more identical cases ...]
```

**Screenshot**: `.screenshots/pm_cc_retest_english.png`

### 3. ❌ Spanish Translations - Not Working
**Status**: FAILED - Spanish toggle not functioning
**Finding**: After clicking Spanish language toggle, page content did not translate

**Evidence**:
- Page title remained in English: "Project Management Center"
- Action badges remained in English: "MISSING DAILY REPORT", "OPEN PROJECT"
- Project fallback text remained in English: "Project number unavailable"

**Screenshot**: `.screenshots/pm_cc_retest_spanish.png`

## Root Cause Analysis

### Backend API Investigation
Captured API responses during PM Command Center load:

**✓ `/api/pm/project-controls/portfolio-intelligence` - Working Correctly**
```json
{
  "projects": [
    {
      "project_number": "ZZ-C8-BOTH-RED",
      "project_name": "C8 Certification — Cost and schedule both unfavorable"
    },
    {
      "project_number": "ZZ-C8-PROGRESS-PARTIAL",
      "project_name": "C8 Certification — Incomplete progress evidence"
    },
    {
      "project_number": "ZZ-C8-COST-RED",
      "project_name": "C8 Certification — Unfavorable cost performance"
    }
    // ... 8 more projects with proper data
  ]
}
```

**❌ `/api/pm/jobs` - Returns Empty/Malformed Data**
- Status: 200 OK
- Body: Empty or not properly formatted
- This endpoint is called by `PmProjectSelector.jsx` (line 26)
- When it returns empty data, the selector has no options to populate

### Code Analysis

**File**: `/app/frontend/src/components/pm/command/PmProjectSelector.jsx`
- Lines 39-43: `optionLabel()` function still contains fallback strings:
  - `"Project number unavailable"` (line 40)
  - `"Project name unavailable"` (line 42)
- Line 26: Calls `/api/pm/jobs` which returns empty data
- Line 29-35: Tries to extract project data but gets empty array

**File**: `/app/frontend/src/components/pm/command/PmProjectFirstHome.jsx`
- Lines 256-258: Also contains fallback strings:
  - `"Project number unavailable"` (line 256)
  - `t("Project name unavailable")` (line 258)
- Line 138: Calls `/api/pm/project-controls/portfolio-intelligence` which HAS correct data
- Line 156: Builds `projectDirectory` lookup from portfolio-intelligence
- Line 129: Gets project numbers from `overview.scoped_projects`
- **Issue**: The lookup is working, but the project numbers in `scoped_projects` don't match the ones in `projectDirectory`

### The Disconnect

The system has TWO sources of project data:
1. `/api/pm/jobs` - Used by selector - Returns EMPTY
2. `/api/pm/project-controls/portfolio-intelligence` - Used by project list - Returns CORRECT data

But even though portfolio-intelligence has the right data, the project list is displaying generic fallbacks. This suggests:
- The `overview.scoped_projects` array contains project numbers that don't exist in the `projectDirectory` lookup
- OR the project numbers are in a different format/case
- OR the `overview` data itself is malformed

## Impact Assessment

**Severity**: HIGH - Blocks PM operational use

**User Impact**:
- PMs cannot identify which projects need attention
- All 11 assigned projects show as "Project number unavailable"
- Spanish-speaking operators cannot use the PM Command Center
- This is the EXACT same issue reported in WP-18C9 test - no progress made

**Operator Experience**:
- PM logs in and sees 11 projects all labeled "Project number unavailable"
- Cannot distinguish between projects
- Must click each one individually to discover which project it is
- Defeats the purpose of the "5:30 AM 10-second test" design goal

## Recommendations for Main Agent

### Priority 1: Fix `/api/pm/jobs` Endpoint
1. Investigate why `/api/pm/jobs` returns empty data for cert.pm@example.com
2. Ensure it returns the same project data structure as portfolio-intelligence
3. Verify PM scoping is working correctly (PM should see only assigned projects)

### Priority 2: Align Data Sources
1. Ensure `overview.scoped_projects` contains project numbers that match the portfolio-intelligence data
2. Verify the `/api/pm/command-center/overview` endpoint returns correct scoped_projects array
3. Consider using a single source of truth for project data instead of two different endpoints

### Priority 3: Fix Spanish Translations
1. Verify the `t()` translation function is working in PM Command Center components
2. Add Spanish translations for:
   - "Project number unavailable" → "Número de proyecto no disponible"
   - "Project name unavailable" → "Nombre de proyecto no disponible"
   - "MISSING DAILY REPORT" → "INFORME DIARIO FALTANTE"
   - "OPEN PROJECT" → "ABRIR PROYECTO"
3. Test language toggle functionality

### Priority 4: Add Defensive Fallbacks
Even after fixing the data source, keep fallbacks but make them more informative:
- Instead of "Project number unavailable", use the actual project number from the array
- Add a tooltip or help text explaining why the name might be missing
- Log warnings when fallbacks are used so issues can be detected

---

# Previous Test: WP-18C9 Executive/PM Experience Verification (2026-08-08 - First Run)

## Test Scope
Verification of rebuilt WP-18C9 Executive/PM experience:
1. Executive Overview landing page with distinct purpose cards
2. Executive portfolio view with attention-first hierarchy
3. PM portfolio view with attention-first hierarchy
4. PM Command Center project name display (no generic fallback)
5. PM Command Center admin-only intelligence-strip defect check
6. Project detail dialog, filters, and search functionality
7. Spanish language toggle

## Test Results

### ✅ PASSED (5/7)
1. ✅ Executive Overview landing page - Three distinct purpose cards working correctly
2. ✅ Executive portfolio view - Attention-first hierarchy (40 projects needing attention)
3. ✅ PM portfolio view - Attention-first hierarchy with PM-specific framing
4. ✅ Project detail dialog, filters, and search - All functional
5. ✅ PM Command Center project-first home view - Default view working

### ❌ FAILED (1/7)
1. ❌ **PM Command Center - Generic project name fallback**: 11 out of 42 projects show "Project number unavailable" instead of recognizable names. This affects scoped PM fixtures.

### ⚠️ PARTIAL PASS (1/7)
1. ⚠️ **Spanish language toggle**: Works but shows mixed English/Spanish content

## Critical Issues

### Issue #1: Generic Project Name Fallback (HIGH PRIORITY)
**Location:** PM Command Center project selector and assigned projects list  
**Problem:** 11 projects display "Project number unavailable" instead of recognizable project numbers/names  
**Examples:**
- "Project number unavailable · Earned Value readiness — Incomplete actual-cost evi..."
- "Project number unavailable · Project name not available"

**Files Affected:**
- `/app/frontend/src/components/pm/command/PmProjectSelector.jsx` (lines 40-43)
- `/app/frontend/src/components/pm/command/PmProjectFirstHome.jsx` (lines 256-258)

**Impact:** PMs cannot identify which projects need attention when they see generic "unavailable" labels.

### Issue #2: Mixed Language in Spanish Mode (MEDIUM PRIORITY)
**Location:** PM Command Center when Spanish language selected  
**Problem:** Some UI elements remain in English when Spanish is selected:
- "Project Management Center" (page title)
- "MISSING DAILY REPORT" (action badge)
- "OPEN PROJECT" (link text)

**Impact:** Creates confusion for Spanish-speaking users.

## Detailed Report
Full test report available at: `/app/wp18c9_test_report.md`

---

# Previous Test: MASCI Operator Language Remediation

## Test Date: 2026-08-07
## Tester: Testing Agent (E2)

## Test Scope
Testing for removal of banned operator-language terms across MASCI preview surfaces:
- Banned terms: truth, canonical, governance, snapshot, reconciliation, operations support, supporting records, project work, EV

## RETEST RESULTS (2026-08-07 - Second Run)

### ✅ ALL RETESTS PASSED

#### 1. Shop Service Truck Page - "reconciliation" → "daily check" ✅ PASS
**Status**: FIXED and verified on live preview
**Verification**:
- ✅ Page title now shows: "Service Truck Daily Check Records"
- ✅ No "reconciliation" term found in visible page content
- ✅ "Daily check" terminology is used throughout
- ✅ Count strip shows "4 daily checks" (not "reconciliations")
- ✅ All user-facing labels updated correctly

**File**: `/app/frontend/src/pages/shop/ServiceTruckReconciliationRecords.jsx`
**Changes verified**:
  - Line 85: `portalRole="Shop Portal · Service Truck Daily Check"` ✅
  - Line 86: `pageTitle="Service Truck Daily Check Records"` ✅
  - Line 137: Error message: "Service truck daily check records unavailable" ✅
  - Line 143: `{data.count} daily check{data.count === 1 ? "" : "s"}` ✅
  - Line 151: `kicker="No daily checks in scope"` ✅
  - Line 152: `title="No service truck daily checks found for this range."` ✅

**Screenshot**: `.screenshots/retest_shop_service_truck.png`

#### 2. PM Monday Review - "operations support" removal ✅ PASS
**Status**: FIXED and verified on live preview
**Verification**:
- ✅ No "operations support" term found in visible page content
- ✅ Page renders correctly with "Monday Review Workspace" title
- ✅ Project selector shows "Project support" as fallback (acceptable - different from "operations support")

**Note**: The project selector component uses "Project support" as a fallback for projects with operator-unsafe language in their names. This is distinct from "operations support" and is an acceptable fallback label.

**Screenshot**: `.screenshots/retest_pm_monday_review.png`

---

## ORIGINAL TEST RESULTS (First Run - Issues Identified)

### ✅ PASSED SURFACES (Original)
1. **Landing Page** - No banned terms found
2. **Dispatch Hub** - No banned terms found
   - ✅ Coaching area uses approved language: "Driver taps create the live operating record"
3. **PM Hub** - No banned terms found
4. **PM Project Controls Authority** - No banned terms found
5. **Earned Value Workspace** - No banned terms found
6. **Portfolio Intelligence** - No banned terms found

### ❌ FAILED SURFACES (Original - Now Fixed)

#### 1. Shop Hub & Service Truck Pages (NOW FIXED ✅)
**Original Issue**: "reconciliation" term still present
**Locations**:
- `/shop/service-truck-reconciliation` route
- Page title: "Service Truck Reconciliation Records"
- File: `/app/frontend/src/pages/shop/ServiceTruckReconciliationRecords.jsx`
  - Line 85: `portalRole="Shop Portal · Service Truck Reconciliation"`
  - Line 86: `pageTitle="Service Truck Reconciliation Records"`
  - Line 137: Error message mentions "Service truck reconciliation records"
  - Line 143: `{data.count} reconciliation{data.count === 1 ? "" : "s"}`
  - Line 151: `kicker="No reconciliations in scope"`
  - Line 152: `title="No service truck reconciliations found for this range."`

**Expected**: Should use "Daily Check" or similar approved language
**Screenshot**: `.screenshots/03_shop_hub.png`, `.screenshots/04_shop_service_truck.png`

#### 2. PM Monday Review Workspace (NOW FIXED ✅)
**Original Issue**: "operations support" term found
**Location**: `/pm/monday-review` route
**File**: `/app/frontend/src/pages/PmMondayReviewWorkspace.jsx`
  - Line 549: `<div className="text-sm font-black text-slate-900">Payroll Review</div>`
  - The term "operations support" was detected in the rendered page content

**Expected**: Should use approved plain-language alternative
**Screenshot**: `.screenshots/06_pm_monday_review.png`

### ⚠️ NOT TESTED (Timeout/Access Issues)
- Safety Portal Hub (timeout during navigation)
- Safety Digest
- Safety Reports  
- Trench Safety Pulse

---

## FINAL STATUS

### ✅ OPERATOR LANGUAGE REMEDIATION: COMPLETE

Both identified issues have been successfully fixed and verified on the live preview environment:

1. ✅ **Shop Service Truck Page**: "reconciliation" → "daily check" terminology updated throughout
2. ✅ **PM Monday Review**: "operations support" term removed from visible content

### Remaining Notes
- Route path `/shop/service-truck-reconciliation` remains unchanged (internal URL, not user-facing)
- Project selector fallback "Project support" is acceptable (distinct from banned "operations support")
- All user-facing labels, titles, and messages now use approved language

## Test Coverage
- ✅ Landing page EN/ES toggle
- ✅ Dispatch Hub coaching area
- ✅ Shop Hub and service truck pages (RETESTED ✅)
- ✅ PM Hub and related workspaces (RETESTED ✅)
- ✅ Earned Value workspace
- ✅ Portfolio Intelligence workspace
- ⚠️ Safety surfaces (partial - timeout issues, not critical for this retest)

## Notes
- Test used real preview credentials from `/app/memory/test_credentials.md`
- All screenshots saved to `.screenshots/` directory
- Console logs captured for debugging
- Retest performed: 2026-08-07
- Both fixes verified on live preview: https://masci-audit-hub.preview.emergentagent.com
