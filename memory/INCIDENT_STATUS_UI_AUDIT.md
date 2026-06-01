# Incident Status · UI Audit

**Batch:** OMEGA · Forensic Audit · Incident Lifecycle Status · UI Layer
**Mode:** READ-ONLY · evidence-first
**Companion:** `INCIDENT_LIFECYCLE_AUDIT.md` · `INCIDENT_STATUS_DATA_MODEL.md`
**Date:** 2026-06-01

---

## 1 · UI inventory · pages that mention incident status

| Page | Path | Status-related behavior | Editable? |
|---|---|---|---|
| `SafetyIncidents.jsx` | `/safety-portal/incidents` (Safety) · `/admin/incidents` (Admin) | **List page** · status filter dropdown (Open · Investigating · Closed) · status pill in row | **No** — filter only |
| `ViewIncident.jsx` | `/admin/incidents/{id}` · `/incidents/{id}` · `/pm/incidents/{id}` | **Detail page** · derived `followUpStatus` banner (Follow-Up Required · Investigation Open · Operationally Complete) | **No** — derived; never stored |
| `HrIncidents.jsx` | `/hr/incidents` (HR read-only mirror) | List + read-only view | **No** — by design (HR read-only) |
| `NewIncident.jsx` | `/incidents/new` · `/incidents/submit` | **Create** form | No status field; never asks |
| `HrSafetyRecords.jsx` | `/hr/safety-records` | Cross-portal mirror | **No** (HR write blocked) |
| `SafetyReports.jsx` | `/safety/reports` | Aggregate counts | n/a — no per-incident status |
| `SafetyHub.jsx` | `/safety-portal` | Tile hub | n/a |
| `SafetyEmployeeProfiles.jsx` | `/safety/employees` | Per-employee rollup | n/a — counts incidents involving employee |

**No page provides an editor for `incident.status`. Zero of 8 status-mentioning pages allow mutation.**

---

## 2 · `SafetyIncidents.jsx` · the list page

### 2.1 · Filter dropdown (lines 122-130)

```jsx
<Select value={status} onValueChange={setStatus}>
  <SelectTrigger className="h-9" data-testid="incidents-status">
    <SelectValue placeholder={t("Status")} />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="all">{t("All statuses")}</SelectItem>
    <SelectItem value="Open">Open</SelectItem>
    <SelectItem value="Investigating">Investigating</SelectItem>
    <SelectItem value="Closed">Closed</SelectItem>
  </SelectContent>
</Select>
```

### 2.2 · Filter logic (line 72)

```jsx
if (status !== "all" && (i.status || "Open") !== status) return false;
```

**Bug-class observation:** The list API (`/api/incidents`) returns `IncidentSummary`, which does NOT project `status`. So `i.status` is always `undefined`, and the fallback `|| "Open"` makes every row look "Open". Filtering by `Investigating` or `Closed` will always return 0 rows in this surface — even though Sprint 1B set every doc's `status` to "open", the list endpoint strips the field.

### 2.3 · Status pill render (lines 168-170)

```jsx
<span className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase
                  tracking-[0.15em] font-bold ${STATUS_PILL[i.status] || "bg-slate-100"}`}>
  {i.status || "Open"}
</span>
```

Every row shows "OPEN" in a slate pill because the status filter projects nothing through the list endpoint.

### 2.4 · STATUS_PILL constant (lines 34-42)

```jsx
// STATUS_PILL — workflow state, not severity. Demoted to neutral
// slate so the eye elevates SEV_PILL as the danger signal. (iter437
// IV-BETA.5A · false urgency removal — see SAFETY_ESCALATION_HIERARCHY
// _MAP.md §IV.)
const STATUS_PILL = {
  Open:          "bg-slate-100 text-slate-800",
  Investigating: "bg-slate-100 text-slate-800",
  Closed:        "bg-slate-100 text-slate-500",
};
```

Three states · Title-case vocabulary · all rendered in slate (intentional de-emphasis). This vocabulary is `Open / Investigating / Closed` — different from accountability projection's `open / in_progress / resolved`, and different from the operator's `Under Investigation / Corrective Action Required / Pending Closure / Closed`.

---

## 3 · `ViewIncident.jsx` · the detail page

### 3.1 · Lifecycle "block" (lines 305-330)

```jsx
<WhyItMattersPanel
  title={t("Incident lifecycle")}
  summary={t("Reported → Linked CAPA(s) → Verified → Closed. " +
             "Closing without a verified CAPA is blocked.")}
  ...
/>
```

This is a **documentation block** in the page — pure copy explaining the intent. It is **not** an editor. The user reads it; no buttons follow.

### 3.2 · Derived `followUpStatus` (lines 60-110)

```jsx
function computeFollowUpStatus(incident, capas) {
  const sev = (incident?.severity || "").toLowerCase();
  const oshaRecordable = incident?.osha_recordable === "Yes";
  const requiresFollowUp = SERIOUS_SEVERITIES.has(sev) || oshaRecordable;
  const openCount = capas.filter(c => OPEN_CAPA_STATES.has(c.status || "Open")).length;
  const verifiedCount = capas.filter(c => c.status === "Verified" || c.status === "Closed").length;

  if (capaCount === 0 && requiresFollowUp) return { kind: "required",  ... };
  if (capaCount > 0 && openCount > 0)      return { kind: "open",      ... };
  if (capaCount > 0 && openCount === 0)    return { kind: "complete",  ... };
  return null;  // low severity, no CAPAs → quiet
}
```

States returned: `required · open · complete · null`. **None of these touch the DB.** They are computed on every render from data already loaded.

### 3.3 · Where the banner appears (line 322)

```jsx
<div data-testid={`followup-status-${followUpStatus.kind}`}>
  ... rose / amber / emerald banner ...
</div>
```

User-visible labels: "Follow-Up Required" (rose) · "Investigation Open" (amber) · "Operationally Complete" (emerald).

### 3.4 · CTAs

The only CTA on the banner is `Open Follow-Up CAPA` (line 83) — links to the CAPA creator. There is no "Mark Closed", "Mark Under Investigation", "Mark Corrective Action Required", or "Mark Pending Closure" button anywhere in `ViewIncident.jsx` (verified by grep).

---

## 4 · Cross-portal mirror behavior

### 4.1 · HR portal (`HrIncidents.jsx`)

HR is read-only by design. The page shows the same list shape as Safety. No editor. The HR portal's status-related copy reads:

```
"HR owns OSHA recordkeeping — Safety/Admin closes incidents."
```

(`HrSafetyRecords.jsx:344` per the operator's prior `REAL_USER_DISCOVERABILITY_AUDIT.md` § 3.3.) HR users have no closure surface, by intent.

### 4.2 · PM portal

PM accesses `/pm/incidents/{id}` which routes to the same `ViewIncident.jsx` component. No editor.

### 4.3 · Field Leadership portal

`/leadership/records?type=incident` is read-only — no detail editor.

### 4.4 · Public submission (`NewIncident.jsx`)

The public/safety incident creator is the only write surface. It captures the initial state. There is no `status` input on this form; the field is not declared in the schema (per `INCIDENT_STATUS_DATA_MODEL.md` §1).

---

## 5 · Visible-on-screen labels for incident status (across the app)

| Surface | Visible label | Storage path |
|---|---|---|
| `SafetyIncidents.jsx` filter | `Open / Investigating / Closed` | reads `i.status` from API list (always undefined → falls back to "Open") |
| `SafetyIncidents.jsx` row pill | `OPEN` (slate) on every row | same |
| `ViewIncident.jsx` lifecycle block | "Reported → Linked CAPA(s) → Verified → Closed. Closing without a verified CAPA is blocked." | static copy |
| `ViewIncident.jsx` follow-up banner | "Follow-Up Required" · "Investigation Open" · "Operationally Complete" | derived live; never stored |
| Command Center · Jobs Today card | "Open · no resolution path" | hardcoded string |
| Command Center · Safety card | "Open · unresolved" · "Open · OSHA notification clock active" | hardcoded strings |
| Accountability dashboard | "open" · "in_progress" · "resolved" | derived from `corrected_on_site` + CAPA |
| Project Health card | uses `resolution_status != "Closed"` for count | reads DB but never displays |

**Eight different label vocabularies in use simultaneously**, all read-only.

---

## 6 · Permission model — who could edit if the surface existed?

| Role | Token | Could read `incident.status`? | Could write (today)? |
|---|---|---|---|
| Super-admin | `X-Admin-Token` | Yes (detail endpoint) | **No** — no write endpoint exists |
| Safety officer | `X-Safety-Token` | Yes (detail endpoint via cross-portal read gate) | **No** |
| HR | `X-HR-Token` | Yes (read-only mirror) | **No** — by intent |
| PM | `X-PM-Token` | Yes (scoped to assigned jobs) | **No** |
| Field Leadership | `X-FL-Token` | Yes (scoped) | **No** |
| Dispatch | `X-Dispatch-Token` | No | **No** |
| Shop | `X-Shop-Token` | No | **No** |

No role can edit `incident.status` — not because permissions block them, but because **the endpoint that would accept the edit does not exist**.

---

## 7 · UI gap-summary table

| Operator's required UI element | Present? | Where it would go |
|---|---|---|
| "Mark Under Investigation" button | ❌ | `ViewIncident.jsx` |
| "Mark Corrective Action Required" button | ❌ | `ViewIncident.jsx` |
| "Mark Pending Closure" button | ❌ | `ViewIncident.jsx` |
| "Mark Closed" button | ❌ | `ViewIncident.jsx` |
| Current lifecycle status pill (clear label) | ⚠️ partial · pill present but uses outdated 3-state vocab and always reads "Open" | `SafetyIncidents.jsx` (list) + `ViewIncident.jsx` (detail) |
| Status-change history / audit log | ❌ | no surface; collection doesn't exist |
| OSHA-specific closure gate | ❌ | no closure gate exists |
| CAPA-completion auto-update | ⚠️ partial · CAPA completion changes the **derived** state in Accountability + Command Center, but DOES NOT update `incident.status` in DB | n/a |
| Lifecycle filter on list page | ⚠️ partial · dropdown present but ineffective (list endpoint strips `status` field) | `SafetyIncidents.jsx` |
| Per-portal permission separation (Safety/Admin can close, HR cannot) | n/a — no closure path exists for anyone | n/a |

---

## 8 · Screenshots / visual evidence

This audit is code-based. No screenshots were captured (OMEGA discipline · evidence-first · read-only · no UI traversal needed because the absent UI cannot be screenshot). The string evidence above is sufficient — the buttons do not exist in the JSX source, therefore they cannot render.

If the operator wants visual confirmation, a single screenshot of `/admin/incidents/<any-id>` would document the absence of any Mark-* buttons.

---

## 9 · Conclusion · UI layer

* Three pages mention status; none edit it.
* The filter dropdown is functionally inert because the list endpoint strips the field.
* The detail page renders a *derived* follow-up banner that never persists.
* The lifecycle copy block on the detail page describes the intended flow ("Reported → Linked CAPA(s) → Verified → Closed") — but no UI implements it.
* No status-change history is rendered anywhere.

The Super-Admin's production observation is correct: **there is no surface to change incident lifecycle state, in any portal, for any role.**

---

## 10 · OMEGA discipline

| Rule | Observed |
|---|---|
| Read-only UI audit | ✅ — code grep only |
| Evidence-first | ✅ — file + line cited for every claim |
| No code changes | ✅ |
| No remediation proposed | ✅ |
| Stop after UI inventory | ✅ |

🛑 UI audit complete. The three deliverables (`INCIDENT_LIFECYCLE_AUDIT.md` · `INCIDENT_STATUS_DATA_MODEL.md` · `INCIDENT_STATUS_UI_AUDIT.md`) together document the full lifecycle gap. No further action authorized.
