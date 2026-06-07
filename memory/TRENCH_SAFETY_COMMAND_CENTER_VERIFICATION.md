# Safety Portal Command Center — Verification
**Date:** 2026-02-07
**Required directive:** Safety Portal must contain Asset Management, Tabulated Data Management, Inspection Management, Hold Management, Certification Management, Repair Management, QR Management, Photo Management, Report Review, Audit History.

---

## 1. Section-by-section verification

### 1.1 Asset Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Create Asset | ✅ `POST /trench-safety/assets` | ❌ No `+ New Asset` CTA | 🔴 MISSING |
| Edit Asset | ✅ `PUT /trench-safety/assets/{id}` | ❌ Detail is read-only by design comment | 🔴 MISSING |
| Asset Status change | ✅ `POST /…/status` | ❌ Only Assign/Return dialogs | 🔴 MISSING |
| List + Filter | ✅ `GET /trench-safety/assets` | ✅ `/safety/trench-safety/assets` | ✅ |
| View Asset Details | ✅ `GET /trench-safety/assets/{id}` | ✅ `/safety/trench-safety/assets/:id` | ✅ |

**Section verdict:** ⚠️ Partial (read-only). Write actions not exposed.

### 1.2 Tabulated Data Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Upload PDF | ✅ (currently `require_admin` — wrong gate) | ❌ Lives on `/admin/trench-boxes` | 🔴 DRIFT |
| Replace PDF | ✅ (admin gate) | ❌ Admin Console | 🔴 DRIFT |
| Link PDF | ✅ | ❌ Admin Console | 🔴 DRIFT |
| Manage Library | ✅ | ❌ Admin Console | 🔴 DRIFT |
| Verify Matching Assets | ❌ Not built | ❌ | ⏳ Future |
| View Library | ✅ public read | ✅ `/safety/trench-safety/tabulated-data` | ✅ |

**Section verdict:** 🔴 DRIFTED to Admin Console.

### 1.3 Inspection Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Create Inspection | ✅ `POST /…/inspections` | ❌ | 🔴 MISSING |
| Inspection History | ✅ `GET /…/inspections` | ❌ Not rendered on Asset Detail | 🔴 MISSING |
| Pass / Fail | ✅ field in payload | ❌ | 🔴 MISSING |
| Severity Assignment | ✅ field in payload | ❌ | 🔴 MISSING |

**Section verdict:** 🔴 Backend-only. No Safety Portal UI.

### 1.4 Hold Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Open Safety Hold | ✅ `POST /…/holds` | ❌ | 🔴 MISSING |
| Open Inspection Hold | ✅ same endpoint | ❌ | 🔴 MISSING |
| Open Maintenance Hold | ✅ same endpoint | ❌ | 🔴 MISSING |
| Certification Hold (auto) | ✅ engine `recompute_certification_hold` | ⚠️ Status visible on Hub alerts only | ⚠️ Partial |
| Release / Clear Hold | ✅ `POST /…/holds/{id}/clear` | ❌ | 🔴 MISSING |

**Section verdict:** 🔴 Backend-only.

### 1.5 Certification Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Upload Certification | ✅ `POST /…/certifications` | ❌ | 🔴 MISSING |
| Expiration Tracking | ✅ auto-expire sweep + alerts | ⚠️ count on Hub, no detail page | ⚠️ Partial |
| Certification Status | ✅ `certification_status_for` | ❌ Not displayed | 🔴 MISSING |
| Revoke / Patch | ✅ endpoints | ❌ | 🔴 MISSING |

**Section verdict:** 🔴 Backend-only.

### 1.6 Repair Management (Safety side)
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Review Repair Queue | ✅ `GET /trench-safety/shop/repairs` | ❌ Only on Shop Portal | 🔴 DRIFT |
| Safety Verification | ✅ `POST /…/repairs/{id}/verify` (safety_or_admin) | ❌ | 🔴 MISSING |
| Release Logic | ✅ verify endpoint clears Inspection Hold when `reinspection_passed` | ❌ No UI to call it | 🔴 MISSING |

**Section verdict:** 🔴 DRIFTED to Shop / Backend-only.

### 1.7 QR Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Generate QR | ✅ `GET /…/qr-label.png` (safety_or_admin) | ❌ Phase 7 frontend pending | ⏳ |
| Reprint QR | ✅ `POST /…/qr-label/audit` | ❌ Phase 7 frontend pending | ⏳ |
| Download QR | ✅ PNG endpoint | ❌ Phase 7 frontend pending | ⏳ |

**Section verdict:** ⏳ Awaiting Phase 7 frontend.

### 1.8 Photo Management
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Upload Photos | ✅ but gated `require_shop_or_admin` — DRIFT | ❌ Phase 7 frontend pending | 🔴 DRIFT (auth) + ⏳ UI |
| Internal vs Public Visibility | ✅ `visibility` field exists | ❌ No UI | ⏳ |
| Asset Photo Library | ✅ `GET /…/photos` | ❌ No UI | ⏳ |
| Delete Photo | ✅ `DELETE /trench-safety/photos/{id}` (safety_or_admin) | ❌ No UI | ⏳ |

**Section verdict:** 🔴 + ⏳ Auth drift plus no UI.

### 1.9 Report Review
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Review Field Reports | Public POSTs land in `trench_safety_repairs` | ❌ Only visible inside Shop queue | 🔴 DRIFT |
| Resolve Reports | ✅ repair lifecycle | ❌ Shop only | 🔴 DRIFT |
| Assign Follow-Up | ✅ PATCH endpoint | ❌ | 🔴 MISSING |

**Section verdict:** 🔴 DRIFTED to Shop.

### 1.10 Audit
| Required | Backend | Safety Portal UI | Verdict |
|---|---|---|---|
| Complete Asset Timeline | ✅ `GET /trench-safety/assets/{id}/audit` | ❌ Not surfaced on Asset Detail | 🔴 MISSING |
| Inspection Timeline | ✅ same source filtered | ❌ | 🔴 MISSING |
| Hold Timeline | ✅ holds + audit | ❌ | 🔴 MISSING |
| Cert Timeline | ✅ certs + audit | ❌ | 🔴 MISSING |
| Repair Timeline | ✅ repairs + audit | ❌ | 🔴 MISSING |

**Section verdict:** 🔴 Backend-only.

---

## 2. Section-level Roll-up

| Section | Verdict |
|---|---|
| Asset Management | ⚠️ Partial |
| Tabulated Data Management | 🔴 DRIFT |
| Inspection Management | 🔴 MISSING |
| Hold Management | 🔴 MISSING |
| Certification Management | 🔴 MISSING |
| Repair Management | 🔴 DRIFT + MISSING |
| QR Management | ⏳ Awaiting Phase 7 FE |
| Photo Management | 🔴 DRIFT + ⏳ |
| Report Review | 🔴 DRIFT |
| Audit History | 🔴 MISSING |

---

## 3. Verdict

🟡 **PARTIAL — COMMAND CENTER INCOMPLETE.**

The Safety Portal exists and renders a calm read-only dashboard, but it does not yet function as the Trench Safety Command Center the directive requires. Every write workflow except Assign/Return is either drifted to another surface or has no UI.

Blockers (in priority order):
1. Tabulated Data CRUD must move to Safety Portal (DRIFT-1).
2. Photo Upload backend gate must move to `safety_or_admin` (DRIFT-2).
3. Repair Review + Field Report Review must be added to Safety Portal (DRIFT-3).
4. Asset write actions (create / edit / status / audit timeline) must be added to Safety Portal UI.
5. Inspection / Hold / Certification UIs must be added.
6. Phase 7 frontend (QR + Photo) lands on the corrected Safety Portal.
