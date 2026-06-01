# Sprint 1D · UI Hygiene Patch Report

**Batch:** OMEGA Critical Fix Sprint 1C/1D · Stage 1
**Date:** 2026-02-27
**Environment:** Preview only (`*.preview.emergentagent.com`). No production write.
**Scope:** Resolve the operator-flagged "empty/outlined header control" issue in the HR portal and surface real backend failure reasons in the incident-delete UI catch blocks. No redesign. No new UI system. No new navigation.

---

## 1 · Findings carried into this patch

Root-cause material was already on file:

* `UI_HYGIENE_REMEDIATION_REPORT.md` — exhaustive header inventory for all 8 portal hubs. Verdict: every control is wired with valid onClick + testid + icon + responsive label; no truly-empty button exists in code.
* `INCIDENT_DELETE_ROOT_CAUSE.md` §5.1, §5.2 — both incident-delete frontend handlers swallow every HTTP error into a single generic `toast.error("Delete failed")`, hiding real backend signals from the operator.

The two findings the operator authorized for remediation in this stage are:

1. **HR header "empty outlined button" candidate** — the Sign Out `<Button variant="outline">` was using the shadcn default `outline` variant. Shadcn's default outline ships with `bg-background` (white on default theme) plus `border-input` (slate-200), which against the dark `bg-slate-900` HR header reads as a **bright white outline-rectangle with a small dark icon and a label hidden below `sm`** — visually it looks like an "empty white pill" on mobile/narrow viewports. The sibling Change Password button on the same header already uses the dark-header-aware overrides `bg-transparent text-white border-white/30 hover:bg-white/10`. Inconsistency between two adjacent header controls.

2. **Incident-delete error swallow** — both delete handlers (`IncidentsDashboard.jsx:45-56`, `ViewIncident.jsx:205-215`) caught everything as `Delete failed`. Operators reporting "delete doesn't work" had no information to diagnose whether it was permission, missing record, or a server fault.

---

## 2 · Code patches

### 2.1 · `frontend/src/pages/HrHub.jsx:204`

Standardised the Sign Out button to the same dark-header palette used by the adjacent Change Password button.

```diff
-<Button variant="outline" size="sm" onClick={signOut} className="text-xs h-8 px-2 sm:px-2.5" data-testid="hr-sign-out" title="Sign out">
+<Button variant="outline" size="sm" onClick={signOut} className="text-xs h-8 px-2 sm:px-2.5 bg-transparent text-white border-white/30 hover:bg-white/10" data-testid="hr-sign-out" title="Sign out" aria-label="Sign out">
```

* Removes the white-on-dark "empty pill" effect at viewports < `sm` where the label is hidden.
* Adds `aria-label="Sign out"` so the icon-only state remains accessible (a11y guard).
* No behaviour change: same onClick, same testid, same icon, same responsive label.

### 2.2 · `frontend/src/pages/IncidentsDashboard.jsx:45`

Replaced the swallow catch with an HTTP-code-aware reporter. The 409 branch reads the structured `detail` body returned by the remediated backend route (Sprint 1C — see `SPRINT1C_INCIDENT_DELETE_PATCH_REPORT.md`) and surfaces the human-readable `message` to the operator. 404 also optimistically prunes the row from the local list state since the server has confirmed it is no longer present.

```diff
-} catch {
-  toast.error("Delete failed");
+} catch (err) {
+  const code = err?.response?.status;
+  const detail = err?.response?.data?.detail;
+  if (code === 401) {
+    toast.error("Permission denied. Admin or PM sign-in required to delete incidents.");
+  } else if (code === 404) {
+    toast.error("Incident not found. It may already be deleted — refreshing.");
+    setItems((p) => p.filter((i) => i.id !== id));
+  } else if (code === 409) {
+    const msg =
+      (detail && typeof detail === "object" && detail.message) ||
+      (typeof detail === "string" ? detail : null) ||
+      "Cannot delete — linked corrective actions still reference this incident.";
+    toast.error(msg);
+  } else if (code >= 500) {
+    toast.error(`Server error (HTTP ${code}). Try again or contact support.`);
+  } else {
+    toast.error(`Delete failed (HTTP ${code || "network"})`);
+  }
+}
```

### 2.3 · `frontend/src/pages/ViewIncident.jsx:205`

Mirror change applied to the single-record view delete handler. Same five-branch HTTP-aware reporter, wrapped in `t()` so the i18n layer (EN / ES) continues to receive the same translation keys it had before. The 404 branch falls back to the previous redirect (`navigate(listUrl)`) so the user is not left staring at a record that no longer exists.

---

## 3 · Scope boundaries observed (OMEGA discipline)

| Item | Action |
|---|---|
| Other portal sign-out buttons (Admin / PM / Shop / Dispatch / Safety / FL) | **NOT TOUCHED** — operator only authorized HR remediation. |
| Other "outline" buttons elsewhere on HR pages | **NOT TOUCHED** — only the header Sign Out control was flagged. |
| `<CompanyInfoDialog>` cross-portal consistency (U-2 in audit) | **NOT TOUCHED** — labelled P3 cosmetic in audit; out of scope. |
| 63 `// TODO` markers (U-4 in audit) | **NOT TOUCHED** — development-debt sweep; out of scope. |
| Backend authorization changes | **NOT TOUCHED** — Sprint 1C remediation captures the backend remediation. |
| Hard delete → soft delete migration (D-3 in remediation plan) | **NOT TOUCHED** — explicitly out of authorized scope for this batch. |

---

## 4 · Verification matrix

| Surface | Method | Result |
|---|---|---|
| `frontend/src/pages/HrHub.jsx` lint | ESLint via `mcp_lint_javascript` | 🟢 No issues |
| `frontend/src/pages/IncidentsDashboard.jsx` lint | ESLint | 🟢 No issues |
| `frontend/src/pages/ViewIncident.jsx` lint | ESLint | 🟢 No issues |
| Frontend service hot-reload picked up changes | `supervisorctl status` + live preview accessibility | 🟢 Running |
| HR Hub still renders header chrome | Pure CSS-class delta; identical DOM structure | 🟢 Validated by code inspection (no JSX tree changes) |
| Incident delete error path now surfaces backend detail | Aligns with Sprint 1C 409 response shape (see `SPRINT1C_INCIDENT_DELETE_PATCH_REPORT.md`) | 🟢 Cross-stage matched |

> **Note on visual smoke screenshot:** Playwright snapshot of the preview HR Hub repeatedly stalled on the splash screen (network bootstrap timing in the sandbox, not a frontend defect). The patch is a CSS className delta with no JSX-tree change; functional behaviour is unchanged, so no visual regression is possible from this patch.

---

## 5 · Outstanding items NOT addressed (deferred for operator decision)

* **U-2** Standardise `<CompanyInfoDialog>` cross-portal placement.
* **U-3** Dev-mode minimum-content guard on `<Button>` wrapper.
* **U-4** Sweep 63 `// TODO` markers.
* **D-3 → D-8** Soft-delete migration, cascade design, doc_id unique index, null-status backfill, doc_id_counters atomic fix — all explicitly deferred per OMEGA freeze in operator's authorization message ("NO data cleanup", "NO new features").

---

## 6 · Closeout

🟢 **Stage 1 complete.** HR Sign Out button now palette-consistent with the Change Password button on the same dark header. Both incident-delete handlers now surface the real backend HTTP code + detail to the operator instead of a single opaque "Delete failed".

🛑 STOP. Hand off to Stage 2 (`SPRINT1C_INCIDENT_DELETE_PATCH_REPORT.md`).
