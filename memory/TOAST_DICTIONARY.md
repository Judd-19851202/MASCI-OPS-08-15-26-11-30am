# MASCI Platform · TOAST_DICTIONARY.md

**Status:** v1.0 · authoritative · Track 14.0-BT (2026-06-13)
**Scope:** Every toast, inline message, validation message, and alert on the MASCI Operations Platform.
**Audience:** Developers · agents · designers · translators.

> Translate this dictionary, not 1 243 strings. Every new toast uses one of the patterns below.

---

## 1. Tone Doctrine

1. **Plain language.** No engineering terms. No env-var names. No raw API/endpoint/schema/migration/backend/frontend words. No raw HTTP codes in user-visible text.
2. **No blame.** Never tell the user "you did wrong." Tell them what to do next.
3. **Always include a next step where possible.** "Could not save. Try again." > "Could not save."
4. **Short.** One sentence preferred. Two sentences max.
5. **One concept per toast.** Don't stack multiple errors. Show the most actionable one first; queue the rest in a list view if needed.
6. **Operator-friendly fallback.** Where backend gives a vague error, surface "Try again, or contact your administrator if it keeps failing." rather than the technical detail.

---

## 2. Approved Patterns by Level

### `toast.success` (381 emissions today · target: every success ≤ 4 words where possible)

| Approved | Use when |
|---|---|
| **"Saved."** | Save completed |
| **"Changes saved."** | Edit completed |
| **"Submitted."** | Form submitted (Daily Report · Pre-Op · etc.) |
| **"Report submitted."** | When the entity is specifically a report |
| **"Uploaded."** | Single file uploaded |
| **"Document uploaded."** | When the entity is specifically a document |
| **"Photo uploaded."** | When the entity is a photo |
| **"Asset updated."** | Asset record updated |
| **"Asset added."** | New asset created |
| **"Removed."** | Generic remove success |
| **"Deleted."** | Generic delete success |
| **"Assigned."** | Assignment workflow complete |
| **"Approved."** | Approval workflow complete |
| **"Revision requested."** | Replaces "Rejected" — sends back for changes |
| **"Verified."** | Verification action complete |
| **"Acknowledged."** | Acknowledgment recorded |
| **"Export started."** | CSV/PDF export initiated (background) |
| **"PDF generated."** | PDF ready for download |
| **"Email sent."** | Email delivery successful |
| **"Signed in."** | Login success (often optional) |
| **"Signed out."** | Logout success (often optional) |
| **"Copied."** | Clipboard copy success |
| **"Ready."** | Asset/work transitioned to ready/available |

### `toast.warning` (12 emissions today · plain-language)

| Approved | Use when |
|---|---|
| **"Action required."** | User must do something to proceed |
| **"Review needed."** | Item is in review queue |
| **"This item needs attention."** | Generic warning state |
| **"Some information is missing."** | Form has incomplete fields |
| **"Integration not connected yet."** | Dormant integration surface |
| **"Email delivery is disabled in this environment. Contact your administrator if you need this emailed."** | Email send disabled (replaces the env-var leak fixed in A2) |
| **"This action could affect multiple records. Continue?"** | Bulk-action confirmation |

### `toast.error` (816 emissions today · always end with a next step)

| Approved | Use when |
|---|---|
| **"Could not save. Try again."** | Generic save failure |
| **"Could not save. Check required fields and try again."** | Validation-style save failure |
| **"Could not submit. Check required fields and try again."** | Generic submit failure |
| **"Upload failed. Try again."** | Single file upload failure |
| **"Upload failed. Check the file size or format and try again."** | Specific upload failure |
| **"Download failed. Try again."** | Single file download failure |
| **"Export failed. Try again, or contact your administrator if it keeps failing."** | CSV/PDF/export failure |
| **"PDF generation failed. Try again."** | PDF generation failure |
| **"Could not delete. Try again, or contact your administrator if it keeps failing."** | Delete failure |
| **"Could not approve this request. Try again, or contact your administrator if it keeps failing."** | Approval workflow failure |
| **"Could not record the revision request. Try again, or contact your administrator if it keeps failing."** | Needs-Revision workflow failure |
| **"Could not update right now. Try again."** | Generic update failure |
| **"You do not have access to this action."** | RBAC denied |
| **"Your role cannot perform this transition."** | Workflow transition denied by role |
| **"Sign-in required."** | Session expired / not authed |
| **"Session expired. Sign in again."** | 401 fallback |
| **"This action is not available yet."** | Feature gated/unreleased |
| **"Connection problem. Check your network and try again."** | Network/offline fallback |
| **"That email is already in use."** | Validation: duplicate |
| **"Valid email required."** | Validation: format |
| **"{Field} required."** | Validation: required (use `t("%{field} required", { field })`) |
| **"Reason must be at least 5 characters."** | Validation: minimum length |
| **"Choose a file first."** | Validation: missing file |
| **"Rework requires a written reason (5+ chars)."** | Domain-specific validation with helper |
| **"Cannot delete — linked corrective actions still reference this incident."** | Domain-specific guarded delete (rare; preserve specificity where it matters) |
| **"Copy failed — write it down by hand."** | Clipboard-API failure with operator-friendly fallback |

### `toast.info` (34 emissions today · use sparingly)

| Approved | Use when |
|---|---|
| **"Loading…"** | Long-running load (prefer skeleton/spinner over toast) |
| **"Preparing your download…"** | Multi-step prepare-then-download |
| **"This may take a moment."** | Generic patience message |
| **"No changes to save."** | Save attempted on unchanged form |

### `toast.loading` (0 emissions today · use sparingly)

Prefer inline spinners and disabled-button states over `toast.loading`.

---

## 3. Integration / Dormant-State Patterns

These pair with the A2 "no fake integration claims" finding and 14.0-I1 honesty banners.

| Approved | Use when |
|---|---|
| **"MaintainX is not connected yet. Contact your administrator to enable."** | Dormant MaintainX action surfaced |
| **"FleetWatcher is not connected yet. Contact your administrator to enable."** | Dormant FleetWatcher action surfaced |
| **"Email delivery is disabled in this environment. Contact your administrator if you need this emailed."** | Resend disabled |
| **"Awaiting integration credentials."** | Generic integration-pending pattern |

---

## 4. Forbidden Patterns

| Forbidden | Replace with |
|---|---|
| `toast.error("HTTP 500")` / `(HTTP ${code})` | "Could not {verb} right now. Try again, or contact your administrator if it keeps failing." |
| `toast.error(\`${e.message}\`)` exposing raw exception | "Could not {verb}. Try again." |
| `toast.error("API failed")` | "Could not {verb}. Try again." |
| `toast.warning("(RESEND_API_KEY / AUTO_EMAIL_REPORTS)")` | Use the approved "Email delivery is disabled..." pattern |
| `toast.error("Rejected")` (as button-action confirmation) | "Revision requested." |
| `toast.success("Created")` for a user-facing add | "Asset added." / "Document uploaded." / etc. (specify entity) |
| `toast.error("Invalid")` | "{Field} is not valid." or "Check required fields and try again." |
| `toast.error("Failed")` (standalone) | "Could not {verb}. Try again." |
| `toast.error("Permission denied")` | "You do not have access to this action." |
| `toast.error("Server is down")` | "Connection problem. Check your network and try again." |

---

## 5. Implementation Rules

- All toasts use `sonner` via `import { toast } from "sonner"` (already platform-standard).
- All user-visible strings route through `useT()` / `t("...")` for translation readiness.
- HTTP-code branching may still exist internally (e.g., 401 vs 403 vs 500) — but the *displayed text* must come from this dictionary, not from the response code.
- Backend error details may be logged to console for support — but **must not** appear in the toast text on operator/field surfaces.
- Admin/Dev surfaces (`/admin/*`, `/dev/*`) may show one additional line with a support-ID or correlation key when one exists in the platform — but never raw stack traces or env-var names.

---

## 6. Spanish Readiness Notes (for 14.0-S1)

The ~50 patterns above cover ≈ 95 % of the platform's 1 243 toast emissions by frequency. Translating those 50 keys first delivers the bulk of the Spanish coverage.

| Toast key | Priority |
|---|---|
| Saved · Submitted · Uploaded · Approved · Verified · Acknowledged · Assigned · Removed · Deleted · Ready | P0 (very high frequency) |
| Could not save · Could not submit · Upload failed · Download failed · Export failed · Could not delete · Could not update | P0 |
| You do not have access to this action · Sign-in required · Session expired | P0 |
| Action required · Review needed · This item needs attention · Some information is missing | P0 |
| Integration not connected yet · MaintainX is not connected yet · FleetWatcher is not connected yet · Email delivery is disabled | P1 |
| Domain-specific (Cannot delete — linked corrective actions...) | P1 |
| Validation specifics | P1 |

---

**End of TOAST_DICTIONARY.md v1.0.**
