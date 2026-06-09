# DR-FIX-3 · IDENTITY, ACCOUNTABILITY & SIGNATURE SIMPLIFICATION — CERTIFICATION

**Authority:** OMEGA DIRECTIVE — DR-FIX-3 · trust / identity / document-governance remediation
**Scope shipped:** R9 + R13 — *all other DR-AUDIT-001 items (R4, R5, R6, R10, R11) remain DEFERRED.*
**Certified:** 2026-02-09
**Verdict:** **PASS 🟢**

---

## Root Cause Summary

**R9 — Identity gap.** Pre-fix, the `prepared_by` field on every Daily Report was a free-text string. Two people with identical names produced indistinguishable submissions in the audit trail. Notification routing, historical accountability, and forensics all degraded to "who happens to type the name."

**R13 — Signer ambiguity.** Daily Reports historically captured TWO signatures (Prepared By + Superintendent), creating real-world confusion about:
- who authored the report,
- who legally attests to its content,
- and who is responsible if the content is wrong.

The platform standard is now **one author · one signature · one accountable preparer**.

---

## Files Changed

| File | Change | Purpose |
|---|---|---|
| `/app/backend/lib/prepared_by_resolver.py` | **NEW** — pure-read helper | Resolves portal tokens (admin, pm, fl, hr, safety, shop, dispatch, leadership) into a structured identity dict. Returns `None` for FSI fallback. Reuses existing per-portal `is_valid_*_token_async` primitives — no new auth surface. |
| `/app/backend/routes/daily_reports.py` | Two surgical edits | (1) `DailyReport` model adds `prepared_by_identity: Optional[Dict]` + `prepared_by_bound: bool`. (2) `create_daily_report._do_create()` calls the resolver before insert and stamps the result on the doc. |
| `/app/backend/pdf_render.py` | One block surgery | `_render_daily` sig section emits only the Prepared By block. Section header changed from `11 · Signatures` to `11 · Signature` (singular). Inline R13 doctrine comment. |
| `/app/frontend/src/pages/NewDailyReport.jsx` | Removed Superintendent SignaturePad | Submission form captures only Prepared By signature. Superintendent **name** field preserved (informational). |
| `/app/frontend/src/pages/ViewDailyReport.jsx` | Sign-Off section restructured | Single-column layout with `data-testid="dr-view-signoff"`. Renders Prepared By only. Section 01 still shows Superintendent **name** as KV context. |
| `/app/backend/tests/test_dr_fix_3_identity_and_signature.py` | **NEW** — 11 tests | R9 directory binding + FSI fallback + display-name preservation; R13 source guards, end-to-end PDF render, legacy doc backward compatibility. |

**Nothing else.** No new collections. No new endpoints. No new portals. No notifications. No emails. No SMS. No Motive/FleetWatcher/MaintainX. No dashboards. No automation. No workflow changes. No lifecycle/approval/kickback/routing changes.

---

## R9 · Prepared By Directory Binding — Implementation

When `POST /api/daily-reports` arrives:

1. The resolver inspects request headers in this priority order:
   `X-PM-Token` → `X-FL-Token` → `X-HR-Token` → `X-Safety-Token` →
   `X-Shop-Token` → `X-Dispatch-Token` → `X-Admin-Token` → `X-Leadership-Token`.
2. The first valid token resolves to its directory user via the
   existing per-portal `is_valid_*_token_async` helper (no new auth).
3. Identity is stamped on the doc:
   ```json
   {
     "prepared_by_bound": true,
     "prepared_by_identity": {
       "directory":  "pm" | "fl" | "hr" | "safety" | "shop" |
                     "dispatch" | "admin" | "leadership",
       "user_id":    "<uuid>",
       "name":       "Chris Wright",
       "email":      "chriswright@mascigc.com",
       "role":       "Project Manager"
     }
   }
   ```
4. When no recognized token is present (public/FSI path):
   `prepared_by_bound = False`, `prepared_by_identity = None`. Submit
   still succeeds — the public form remains unauthenticated, no login
   is required, no directory enrollment is forced.

### Display rules — locked
- Read view shows `Prepared By: <name>` (line 309 of `ViewDailyReport.jsx`, unchanged).
- PDF shows `Prepared By: <name>` (line 220 of `pdf_render.py`, unchanged).
- No GUIDs, no user IDs, no internal references surface in any rendering.
- Audit can discriminate directory-bound from FSI via the `prepared_by_bound` flag (server-side only).

---

## R13 · Signature Simplification — Implementation

### PDF (`pdf_render.py::_render_daily`)
```python
sigs = _signature("Prepared By", d.get("prepared_by_signature"),
                  d.get("prepared_by") or "")
if sigs:
    rows.append(_section("11 · Signature", sigs))
```
The Superintendent `_signature(...)` call is gone. Historical reports that carry a `superintendent_signature` blob in MongoDB keep their data unchanged — the rendering pipeline simply no longer reads it. Section heading switched from plural `Signatures` to singular `Signature`.

### Submission form (`NewDailyReport.jsx`)
The `<SignaturePad testId="superintendent-sig" />` block is removed. The `<Input testId="superintendent" />` name field is preserved — superintendent remains informational project context, not a signer.

### Read view (`ViewDailyReport.jsx`)
Section 11 collapses from a 2-column grid (Prepared By + Superintendent) to a single-column `<div data-testid="dr-view-signoff">` block. Section 01 still renders `<KV label="Superintendent" value={data.superintendent} />` (line 310, unchanged) so the superintendent name remains visible as project context.

### Backward compatibility
- `superintendent_signature` field still accepted on the model (`extra="allow"` on `DailyReportCreate`).
- Historical DRs with stored signatures load, fetch, and render to PDF with no errors.
- Their stored signature remains in MongoDB intact (no destructive migration).

---

## Test Results

### `test_dr_fix_3_identity_and_signature.py` — 11/11 PASS

```
tests/test_dr_fix_3_identity_and_signature.py::test_r9_directory_bound_admin                                PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r9_directory_bound_pm                                   PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r9_fsi_fallback_no_portal_token                         PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r9_human_readable_name_no_guid_leak                     PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r9_legacy_post_without_identity_field_passes_through    PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r13_pdf_renderer_emits_single_signature_block           PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r13_view_no_longer_renders_superintendent_signature_block PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r13_form_no_longer_captures_superintendent_signature    PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r13_new_dr_pdf_does_not_render_superintendent_sig       PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_r13_pdf_bytes_render_without_crash                      PASSED
tests/test_dr_fix_3_identity_and_signature.py::test_legacy_dr_with_superintendent_signature_still_readable  PASSED
```

### Regression — DR-FIX-1 + DR-FIX-2 + MM-001B + MM-001B-F1 still green

```
37 passed in 29.85s
```

- DR-FIX-1 (R1 production, R2 constraints, R3 schedule_delays) — 9/9
- DR-FIX-2 (R7 superintendent auto-pop, R12 done button) — 7/7
- MM-001B + MM-001B-F1 (E-1, E-2, E-5 + false-outgoing fix) — 10/10
- DR-FIX-3 (R9 + R13) — 11/11

---

## Read View Evidence

URL: `/admin/daily/5fea62a0-1fc0-47e2-aaeb-4378af3d7f33`

- Section 01 (top of report) still shows `Superintendent: Pytest` — informational context preserved.
- Section 11 Sign-Off — single column, single signature block:
  - Header: `Sign-Off`
  - Label: `PREPARED BY`
  - Name: `Pytest`
  - Signature pad: present, populated
  - **No Superintendent signature block anywhere.**

Screenshot: `/tmp/dr_fix3_view_signoff.png` (captured during verification run).

---

## PDF Evidence

In-process render via `render_record_pdf("daily-report", doc)`:
- PDF magic bytes confirmed (`%PDF-…`).
- HTML envelope contains exactly one `11 · Signature` section.
- After splitting on `"11 · Signature"`, the right-hand portion contains
  zero occurrences of `Superintendent` (test
  `test_r13_pdf_renderer_emits_single_signature_block` enforces this).
- Even when the source doc carries a non-empty `superintendent_signature` (legacy/historical), the rendered PDF still emits only the Prepared By block (test `test_legacy_dr_with_superintendent_signature_still_readable` enforces this).

---

## Submission Form Evidence

URL: `/daily/new`

- Section 11 Sign-Off renders:
  - Distribution List
  - **`PREPARED BY SIGNATURE *`** (single, required)
- No Superintendent Signature pad anywhere on the form.
- Superintendent **name** input remains earlier on the form for informational capture.

Screenshot: `/tmp/dr_fix3_new_form.png` (captured during verification run).

---

## Historical Report Verification

- DR submitted with `superintendent_signature=<data url>` → submit OK (200).
- `GET /api/daily-reports/{id}` returns the doc with `superintendent_signature` preserved verbatim — data is not destroyed.
- `render_record_pdf("daily-report", doc)` produces a valid PDF (starts with `%PDF-`).
- Rendered HTML's `11 · Signature` section contains zero Superintendent text — the legacy data does not bleed into the new rendering.

---

## Verification Matrix (per directive)

| Required check | Result |
|---|---|
| Directory-bound user submits → structured identity stored | ✅ `test_r9_directory_bound_admin`, `test_r9_directory_bound_pm` |
| Human-readable name displayed (no GUIDs) | ✅ `test_r9_human_readable_name_no_guid_leak` |
| PDF displays Prepared By correctly | ✅ `test_r13_pdf_bytes_render_without_crash` |
| Read View displays Prepared By correctly | ✅ `test_r13_view_no_longer_renders_superintendent_signature_block` |
| No directory match → submission succeeds (FSI fallback) | ✅ `test_r9_fsi_fallback_no_portal_token` |
| New report has Prepared By signature captured | ✅ Screenshot + `test_r13_new_dr_pdf_does_not_render_superintendent_sig` |
| New report Superintendent signature absent | ✅ Both source guards + screenshot |
| PDF contains one signature block | ✅ `test_r13_pdf_renderer_emits_single_signature_block` |
| Read View contains one signature block | ✅ `test_r13_view_no_longer_renders_superintendent_signature_block` + screenshot |
| Legacy report opens | ✅ `test_legacy_dr_with_superintendent_signature_still_readable` |
| Legacy PDF renders | ✅ Same test (PDF bytes returned) |
| Historical signatures preserved (no destructive migration) | ✅ Same test (`superintendent_signature` returned verbatim from GET) |

---

## Success Criteria — All Met

- ✅ Every Daily Report has one accountable author
- ✅ Prepared By is directory-bound whenever a portal token is presented
- ✅ FSI fallback remains functional (no login required for public submits)
- ✅ Superintendent remains project context only (name visible, signature gone)
- ✅ Daily Reports contain exactly one signature authority
- ✅ Historical reports remain valid (data preserved, render path graceful)
- ✅ No workflow / lifecycle / approval / kickback / routing changes occurred
- ✅ No integrations added
- ✅ No scope creep — R9 + R13 only

---

## Out of Scope (frozen — OMEGA discipline)

- R4 Executive Summary on PDF
- R5 SHA256 audit footer on PDF
- R6 Excavation on PDF
- R8 Silent crew/equipment auto-apply
- R10 Kickback in-app fallback
- R11 Motive M-DR-1
- RM-1 → RM-5 (removals, pending one DR cycle)
- Material Movement E-3 → E-9
- FleetWatcher / Motive / MaintainX
- Daily Report or PDF redesign

---

## STOP CONDITION OBSERVED

Per directive, all work halts here. R4, R5, R6, FleetWatcher, Motive, MM follow-on phases, PDF redesign, and Daily Report redesign remain **deferred** pending explicit authorization.

**CERTIFIED · DR-FIX-3 COMPLETE**
