# TRACK 15.66 — Frontend Email Cleanup (Phase 1)

**Date:** 2026-06-22  
**Scope:** cosmetic `@mascigc` placeholders in login forms + component placeholders.

## 1. Cleaned this phase (16 occurrences → 0)

| File | Before | After |
|---|---|---|
| `pages/AdminLogin.jsx` | `placeholder="you@mascigc.com"` | `placeholder="you@yourcompany.com"` |
| `pages/PmLogin.jsx` | same | same |
| `pages/HrLogin.jsx` | same | same |
| `pages/SafetyLogin.jsx` | same | same |
| `pages/DispatchLogin.jsx` | same | same |
| `pages/FieldLeadershipPortalLogin.jsx` | same | same |
| `pages/SignIn.jsx` | same | same |
| `pages/ShopLogin.jsx` | `placeholder="shopmanager@mascigc.com"` | `placeholder="shop-manager@yourcompany.com"` |
| `components/JhaAcknowledgeButton.jsx` | `placeholder="you@mascigc.com"` | `placeholder="you@yourcompany.com"` |
| `components/AdminPMPanel.jsx` | mascigc placeholders | yourcompany |
| `components/EmployeeMasterPanel.jsx` | mascigc placeholders | yourcompany |
| `components/AdminAccessControlPanel.jsx` | mascigc placeholders | yourcompany |
| `pages/admin/AdminDigestConfig.jsx` | `placeholder="safety@mascigc.com, ops@mascigc.com"` | `placeholder="alerts@yourcompany.com, ops@yourcompany.com"` |

Verification:
```
grep -rEn 'placeholder=[\"\x27][^\"\x27]*@(mascigc|mascidocs)' frontend/src --include="*.jsx" --include="*.js" | wc -l
0
```

## 2. Remaining 35 frontend occurrences — fully classified

All remaining `@mascigc` / `@mascidocs` strings in the frontend are **content / branding display strings**, not routing decisions. They are not used as inputs to any email send. Phase 2 resolves them through the new `/api/admin/email-routing/v2/branding` endpoint so admin-changeable branding cascades into the UI.

| File | Count | Type | Phase 2 action |
|---|---:|---|---|
| `pages/AdminGuide.jsx` | 8 | Admin help guide example emails | Resolve via `branding.support_email` template |
| `data/training.js` | 6 | Training course content (employee-facing) | Resolve via branding template at render time |
| `lib/i18n.js` | 4 | i18n strings with example emails | Resolve via branding template |
| `data/training_es.js` | 3 | Spanish training content | Resolve via branding template |
| `pages/V2Compare.jsx` | 2 | Static comparison content | Resolve via branding template |
| `pages/SafetyDigest.jsx` | 2 | UI display of current default recipient | Pull from `/api/admin/email-routing/v2/routes/SAFETY_DIGEST_TO` |
| `components/AdminShopUsersPanel.jsx` | 2 | Empty-state copy | Pull from `/api/admin/email-routing/v2/routes/PRE_OP_FAIL_FALLBACK` |
| `components/TrenchBoxPosterCard.jsx` | 1 | Contact on printable poster | Pull from branding |
| `pages/SafetyFormsHub.jsx` | 1 | Static contact reference | Resolve via branding |
| `pages/HrPayrollVariance.jsx` | 1 | UI display of payroll variance default recipient | Pull from `/api/admin/email-routing/v2/routes/PAYROLL_VARIANCE_TO` |
| `pages/admin/AdminDigestConfig.jsx` | 1 | UI display of current default | Pull from `/api/admin/email-routing/v2/routes/SAFETY_DIGEST_TO` |
| `lib/companyInfo.js` | 1 | Company contact constant | Replace with `await getBranding()` lookup |
| Other (test/storybook/static comparison) | 3 | excluded from operational scope | n/a |

## 3. What was NOT cleaned in Phase 1 (and why)
* Training content + i18n strings — these are **localized content** that should pull the support email from a single source of truth. The right Phase 2 pattern is a `{{tenant.support_email}}` template placeholder evaluated at render time. Doing a sed-blind replace would break the Spanish translation alignment + would scatter the data dependency.
* UI display strings showing "current default" recipient — these are showing the configured default for that route. They become live once they read from `/api/admin/email-routing/v2/routes/...` (Phase 2 wiring).
* Admin guide — pulls from `/api/admin/email-routing/v2/branding.support_email` in Phase 2.

## 4. Hard-rule compliance (Phase 1 frontend)
* ✅ All cosmetic login + form placeholders genericized.
* ✅ No content / training / help-text edits made (Phase 2 will resolve through branding).
* ✅ No production user-visible behaviour change in Phase 1.
* ✅ Every remaining occurrence categorised.
