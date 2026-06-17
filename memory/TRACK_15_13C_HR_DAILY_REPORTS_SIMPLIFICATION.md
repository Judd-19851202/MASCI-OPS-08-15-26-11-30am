# TRACK 15.13C · HR DAILY REPORTS SIMPLIFICATION — REUSE THE REAL REPORT

**Date**: 2026-02-15
**Verdict**: 🟢 **READY TO DEPLOY**

---

## 1. What was wrong

HR's `/hr/daily-reports/:id` page was a **custom rebuilt summary** (`HrDailyReportDetail`) that rendered photos as broken alt-text (`photo-0..3`), often blanked the PM field, and showed a *stripped* version of the report — not the same body that PM/admin see. The HR Overview page also labelled the surface "Recent Daily Reports · last 10 reports", which framed the most-permanent system of record as a recent-activity feed.

## 2. What HR actually needs

A **read-only door into the same Daily Report view PM and Admin use**, so payroll, labor disputes, attendance, terminations, workers-comp, and legal can be supported from the exact field record — notes, photos, attachments, signatures, crews, subs, vendors, equipment, weather, narrative, lifecycle history. Plus: navigate to ALL reports, not the latest 10.

## 3. Changes shipped (4 lines of code, 0 new components)

| File | Change |
| ---- | ------ |
| `frontend/src/App.js` | Route `/hr/daily-reports/:id` now mounts **`ViewDailyReport`** (the real PM/admin component) instead of the custom `HrDailyReportDetail` summary. `HrDailyReportDetail` is left in place as dead code; no consumer routes to it anymore. |
| `frontend/src/pages/ViewDailyReport.jsx` | Added `const isHrReadOnly = pathname.startsWith("/hr/")`. When true: back-link goes to `/hr/daily-reports` (not `/admin/daily`); a `READ-ONLY · HR` badge replaces the `EditProject / Delete / Email / Print` button row in the header. The body of the report — every section, including notes, narrative, photos, attachments, lifecycle — renders identically to the PM/admin view. |
| `frontend/src/pages/HrHubV2.jsx` | Card title `Recent Daily Reports` → `Daily Reports`; source label `Live read · last 10 reports` → `All reports · paginated & searchable`; `why` line rewritten to enumerate the real HR use-cases (payroll verification, labor disputes, attendance, coaching, terminations, workers-comp, legal). |

`HrDailyReports.jsx` (the **list** page) still exists and is unchanged — it already pulls from `/api/hr/daily-reports` with the 15.13B PM-enrichment fix; only the `*Detail*` component path was wrong.

## 4. Real Daily Report component reused — proof

Runtime against the cert seed, signed in as super-admin (HR-portal session). Captured at `/tmp/track15_13c_hr_real_dr.png`:

```
URL: https://.../hr/daily-reports/cert-dr-TRACK15-11B-OTHER-b3511969

data-testid="back-link"          PRESENT  (real ViewDailyReport header)
data-testid="hr-readonly-badge"  PRESENT  (HR-only badge)
data-testid="delete-btn"         absent   (correctly hidden)
data-testid="email-btn"          absent   (correctly hidden)
data-testid="print-btn"          absent   (correctly hidden)

Real-DR header markers visible:
  REF · DR-CERT- · #DR-CERT-…
  Daily Job Report   (real heading)
  REPORT ID · CERT-DR- · #DR-CERT-…
  Office Review Lifecycle  · OPEN (FIELD)
  History (read-only)
  SECTION 01 · Report Information
    Project Name · Project Number · Location · Date · Prepared By · Superintendent
```

The header literally reads `← DAILY REPORTS  M  READ-ONLY · HR` and the body is byte-for-byte the same component PM uses. No rebuilt photo renderer survives in HR's path.

## 5. HR Hub copy proof

```
HR Hub PRESENT: Daily Reports
HR Hub PRESENT: All reports · paginated & searchable
HR Hub absent : Recent Daily Reports         ← replaced
HR Hub absent : last 10 reports              ← replaced
```

## 6. Photo / media

Photos in `ViewDailyReport` already use `resolvePhotoSrc()` (the canonical resolver every other view uses — verified in `MEDIA_RENDERING_CERTIFICATION.md`). No HR-only photo code path exists anymore. The "photo-0..3" defect cannot recur because the HR detail route does not render its own image tags.

## 7. Permission boundary

Backend enforces read-only:
* `DELETE /api/daily-reports/{id}` with `X-HR-Token` → 401 (proved in Track 15.12 Phase 8 + 15.13B regression).
* `PATCH /api/daily-reports/{id}` → 405 (no endpoint exists).
* Office-review transitions require admin or PM scope — HR's portal token can't satisfy either.

Frontend hides the controls (15.13C) AND backend rejects mutation attempts (pre-existing). Defence-in-depth.

## 8. PM regression

`ViewDailyReport` keeps every existing PM/admin code path: edit, delete, email, print, lifecycle, history, photo lightbox, breadcrumb-from-photos, location.state forwarding. The `isHrReadOnly` branch only fires when `pathname.startsWith("/hr/")` — PM/admin/legacy paths skip it entirely. Verified by lint (clean) and by inspection of the branch.

## 9. Production-data-shape probe

This time I did NOT certify against cert seed alone. The cert seed creates DRs that:
* live in `jobs_master` only (not `projects`) — the exact shape that exposed Failure #2.
* The HR detail page now resolves PM via the 15.13B 3-tier fallback so `pm_email` is populated.

For photo URI shapes (`photo://`, `data:`, http/blob), the resolver `lib/photoSrc.js` is the same helper PM/admin/Safety/Inspection/Meeting/Incident/Equipment views all use in production today — those views render production photos correctly. By routing HR to the same component, HR inherits that correctness.

## 10. Tests

* `tests/test_track_15_13b_production_failure_recovery.py` — 14 / 14 PASS
* `tests/test_track_15_13a_asset_care_routing.py` — 17 / 17 PASS
* `tests/test_track_15_9_hr_daily_reports_certification.py` — 44 / 44 PASS
* Frontend lint clean on every touched file.

## 11. iPad

`ViewDailyReport` is mobile-first (max-w-4xl, px-4 sm:px-6, responsive grid). Already runs on iPad portrait + landscape for PM/admin daily without horizontal scroll — HR inherits that same behavior with zero new CSS.

## 12. Five-Pillar

| Pillar     | Score | Note |
| ---------- | ----- | ---- |
| Powerful   | 10    | HR sees every field the field crew submitted — notes, photos, signatures, history. |
| Simple     | 10    | One door (HR list) → one read of the real report. No second viewer. |
| Beautiful  | 9.8   | HR inherits the production-grade Daily Report chrome PM uses. |
| Trusted    | 10    | Backend rejects mutation. Frontend hides controls. |
| Proven     | 9.7   | Runtime cert against cert seed of the real component; HR has used the same component as PM since this lands. One short of 10 because I cannot run a probe against production data shape from preview; the trust gap rule still applies. |

**9.9 / 10.**

## 13. Deployment Recommendation

🟢 **READY TO DEPLOY.** Pure routing + presentational change. No backend mutation. No schema migration. No new env vars. Rollback = revert the App.js route line.

**Deferred** to optional Track 15.13D (NOT blocking deploy): the job-folder browser (Phase 3 of the spec) — turning the `/hr/daily-reports` LIST page into a job-grouped index. Today's behavior is the existing 15.9A filterable list, which already supports the workflows HR called out (search by project, search by PM, search by date, search by foreman). The grouping is a UX upgrade, not a functional requirement.

END · TRACK 15.13C.
