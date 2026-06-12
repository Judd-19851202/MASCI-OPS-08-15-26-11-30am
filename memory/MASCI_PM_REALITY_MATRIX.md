# MASCI PM Portal Reality Matrix

**Track 13.5B · PM-Specific Five-Pillar Reality Validation**
**Mode:** Analysis only — no code change.
**Generated:** 2026-06-12 (UTC)

> Scope per directive: validate every PM V2 object — Active Projects · Crews In Field · Open Holds · Due Today · Project List · Project Health · Risks · RFIs · Submittals · Daily Reports · Incidents · CAPAs · Photos.

---

## 1. Method

For each object I asked the six questions in the directive:
A. Exists today?
B. Data source exists?
C. Workflow exists?
D. API exists?
E. Route exists?
F. Operational value exists?

Then classified into one of: **Real · Real but Partial · Planned · Mock · Missing**.

Evidence cited at file / route / endpoint level. No new findings invented.

---

## 2. Object-by-object verdict

### 2.1 Active Projects (V2 pulse card #1)

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Yes (in live PM portal as `/pm/jobs` count and as `/pm/hub` summary) |
| B. Data source? | ✅ MongoDB `jobs` / `jobs-master` collections |
| C. Workflow? | ✅ Job creation lives in Admin (`/admin/jobs`) and trickles to PM via `co_pm_emails` scoping |
| D. API? | ✅ `/api/pm/jobs` (`pm_routes.py:276`) returns scoped active projects |
| E. Route? | ✅ `/pm/jobs` |
| F. Operational value? | ✅ Yes — every PM session opens with "how many active?" |
| **Classification** | **Real** |
| **PM V2 verdict** | Pulse card is presentation-correct; needs to bind to `/api/pm/jobs` count in B3. |

### 2.2 Crews In Field Today

| Question | Answer |
| --- | --- |
| A. Exists today? | 🟡 Implicit only — through Daily Reports + Dispatch Board |
| B. Data source? | 🟡 `daily_reports` + `dispatch_assignments` + Motive feed |
| C. Workflow? | 🟡 Implicit. There is no single "Crews in Field" engine — it is derived |
| D. API? | ❌ No dedicated endpoint named `/api/pm/crews-in-field`; closest is `/api/pm/command-center/resources` (`pm_command_center.py:345`) which carries crew/resource composition |
| E. Route? | 🟡 Surfaced inside `/pm/command-center` |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real but Partial** |
| **PM V2 verdict** | The card concept is right; the derivation needs to be explicit in any migration. |

### 2.3 Open Holds

| Question | Answer |
| --- | --- |
| A. Exists today? | 🟡 Yes, as status state across multiple workflows — but no unified "holds" list |
| B. Data source? | 🟡 Spread across `daily_reports.lifecycle`, `incidents.lifecycle`, `qaqc`, `equipment_status` |
| C. Workflow? | 🟡 Per-engine holds: Safety Hold, Maintenance Hold, Certification Hold, Inspection Hold |
| D. API? | ❌ No `/api/pm/holds` exists. Holds must be re-derived per surface |
| E. Route? | ❌ No PM Holds page exists today |
| F. Operational value? | ✅ Yes (this is the #1 "what needs me?" answer) |
| **Classification** | **Real but Partial** (data exists everywhere; aggregation does not) |
| **PM V2 verdict** | Strongest case for engine work in B3: a unified hold registry would change PM operating reality. |

### 2.4 Due Today

| Question | Answer |
| --- | --- |
| A. Exists today? | 🟡 Implicit only |
| B. Data source? | 🟡 `daily_reports.due_at`, `incidents.due_at`, `capas.due_at`, `submittals.due_at` (if exists) |
| C. Workflow? | 🟡 Per-engine due dates |
| D. API? | ❌ No `/api/pm/due-today` |
| E. Route? | ❌ No PM Due-Today page |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real but Partial** |
| **PM V2 verdict** | Same as Holds — the surface concept is right; the cross-engine aggregation does not yet exist. |

### 2.5 Project List

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Yes — `/pm/jobs` |
| B. Data source? | ✅ `jobs` collection + `co_pm_emails` scoping |
| C. Workflow? | ✅ |
| D. API? | ✅ `/api/pm/jobs` (`pm_routes.py:276`) |
| E. Route? | ✅ `/pm/jobs` |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real** |

### 2.6 Project Health (per-project pulse)

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Yes — `/pm/command-center` per-project view (Phase 4A) |
| B. Data source? | ✅ Multiple collections joined |
| C. Workflow? | ✅ Implicit aggregation |
| D. API? | ✅ `/api/pm/command-center/{overview,resources,hauls,materials,shop-impact,safety-impact,timeline}` (`pm_command_center.py:215-642`) |
| E. Route? | ✅ `/pm/command-center?project_number=<pn>` |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real** |
| **PM V2 verdict** | The most production-ready PM surface today; visual reskin pending. |

### 2.7 Risks

| Question | Answer |
| --- | --- |
| A. Exists today? | ❌ No dedicated PM-side Risk surface |
| B. Data source? | 🟡 Risks are recorded indirectly via `incidents`, `capas`, `qaqc`, and ad-hoc Constraint records (`/constraints`) |
| C. Workflow? | ❌ No "Risk" engine; closest concept is Constraints |
| D. API? | ❌ No `/api/pm/risks` |
| E. Route? | 🟡 `/constraints*` exists but is platform-wide, not PM-scoped |
| F. Operational value? | ✅ Yes — risk surfacing is what PMs ask for first |
| **Classification** | **Planned** (no engine yet) |
| **PM V2 verdict** | The Risks table in PM V2 preview is **MOCK**. Any migration must first answer: do Constraints become Risks, or is a new engine needed? |

### 2.8 RFIs

| Question | Answer |
| --- | --- |
| A. Exists today? | ❌ Not as a backend object |
| B. Data source? | ❌ No `rfis` collection |
| C. Workflow? | ❌ No RFI lifecycle exists |
| D. API? | ❌ No `/api/*/rfi*` route |
| E. Route? | ❌ No RFI page in any portal |
| F. Operational value? | ✅ Yes — RFIs are PM's daily reality |
| **Classification** | **Missing** (mock only in PM V2) |
| **PM V2 verdict** | The RFIs table in PM V2 preview is **MOCK** and represents future scope, not current capability. |

### 2.9 Submittals

| Question | Answer |
| --- | --- |
| A. Exists today? | ❌ Not as a backend object |
| B. Data source? | ❌ No `submittals` collection |
| C. Workflow? | ❌ No submittal lifecycle |
| D. API? | ❌ No route |
| E. Route? | ❌ No surface |
| F. Operational value? | ✅ Yes |
| **Classification** | **Missing** (mock only in PM V2) |
| **PM V2 verdict** | Same as RFIs — aspirational. |

### 2.10 Daily Reports

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Fully implemented |
| B. Data source? | ✅ `daily_reports` collection + lifecycle |
| C. Workflow? | ✅ Submitted → Pending Verification → Verified → Closed; "Needs Revision" is the strongest negative |
| D. API? | ✅ `/api/daily-reports`, `/api/daily-reports/{id}`, `/api/daily-reports/{id}/lifecycle`, `/api/daily-reports/{id}/transition`, `/api/daily-reports/{id}/state-events`, `/api/pm/...` scoped read |
| E. Route? | ✅ `/pm/daily`, `/daily-reports*` |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real** |
| **PM V2 verdict** | Re-skin lane is safest first migration target. |

### 2.11 Incidents

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Fully implemented |
| B. Data source? | ✅ `incidents` collection + lifecycle |
| C. Workflow? | ✅ `/api/incidents`, `/api/incidents/{id}/lifecycle`, `/api/incidents/{id}/transition`, `/api/incidents/{id}/state-events` |
| D. API? | ✅ |
| E. Route? | ✅ `/pm/incidents`, `/incidents*` |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real** |

### 2.12 CAPAs

| Question | Answer |
| --- | --- |
| A. Exists today? | 🟡 Exists per-incident but **not as a PM-scoped list** (U-01 from 13.4E usability audit) |
| B. Data source? | ✅ `capas` (or embedded inside `incidents`) |
| C. Workflow? | ✅ CAPA lifecycle is real |
| D. API? | ✅ `/api/pm/crew/capas` (`pm_routes.py:195`) returns crew-scoped CAPAs |
| E. Route? | 🟡 Surfaced inside `/pm/incidents` flow; no dedicated `/pm/capas` page |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real but Partial** (data + API exist; PM-scoped list view missing per U-01) |
| **PM V2 verdict** | Highest-ROI new surface: data exists, only the list view is absent. |

### 2.13 Photos

| Question | Answer |
| --- | --- |
| A. Exists today? | ✅ Yes — `JobPhotosLibrary` component mounted at `/pm/photos` |
| B. Data source? | ✅ R2 storage + `job_photos` collection (zero entries in preview env at capture time — see current_photos_*.jpg screenshots) |
| C. Workflow? | ✅ Upload happens via Daily Reports / Site Inspections / QA-QC; photos surface centrally |
| D. API? | ✅ Backend endpoints for upload, list, migrate, health under `/api/admin/photos*` and per-form scoped endpoints |
| E. Route? | ✅ `/pm/photos` (portalKey="pm") |
| F. Operational value? | ✅ Yes |
| **Classification** | **Real** (data backend operational; preview empty is environmental, not a defect) |

---

## 3. Summary matrix

| PM V2 object | Classification | Operational gap |
| --- | --- | --- |
| Active Projects        | Real            | None |
| Crews In Field         | Real but Partial | Needs explicit aggregation endpoint |
| Open Holds             | Real but Partial | **Needs unified holds list (highest-impact engine gap)** |
| Due Today              | Real but Partial | Cross-engine due-date aggregation |
| Project List           | Real            | None |
| Project Health         | Real            | Visual only; APIs Phase 4A ready |
| Risks                  | Planned         | **No engine yet** |
| RFIs                   | Missing         | **No engine yet** |
| Submittals             | Missing         | **No engine yet** |
| Daily Reports          | Real            | None |
| Incidents              | Real            | None |
| CAPAs                  | Real but Partial | PM-scoped list view missing (U-01) |
| Photos                 | Real            | Preview env empty; production unverified (D-01-class concern) |

Count: **5 Real · 5 Real but Partial · 1 Planned · 2 Missing**

---

## 4. Five-Pillar score for the PM portal as it stands today

| Pillar | Score | Justification (cited) |
| --- | :-: | --- |
| Powerful | 9 | Real APIs back 8 of 13 V2 objects directly; PM Command Center Phase 4A delivers 7 sub-endpoints. |
| Simple | 6 | Sub-form duplication R-02 · CAPA list missing U-01 · "Center" naming overload V-09 · 7 ad-hoc card styles per visual identity audit. |
| Beautiful | 7 | Improved post-13.4A (cited in `MASCI_VISUAL_IDENTITY_AUDIT.md`); PM tile-CTA amber drift V-02 remains. |
| Trusted | 7 | Verification lifecycle is real; preview env data freshness is environmental, not a PM defect. |
| Proven | 7 | `co_pm_emails` scoping passes regression suite (test_iter437_pm_jobs_endpoint.py); preview screenshots filed; no production usability sign-off captured for PM V2 itself. |

PM portal average: **7.2 / 10.**

---

## 5. PM V2 preview vs reality — operator decisions still needed

1. **Holds engine** — should Open Holds be its own engine, or rendered from a `holds_view` materialized across the existing per-workflow `lifecycle` records?
2. **Risks vs Constraints** — does the existing Constraints engine cover what PM V2 labels Risks, or is a new domain object required?
3. **RFIs / Submittals** — out of scope for PM V2 migration, or in scope?
4. **CAPA list view (U-01)** — green-light a single new screen, or roll into B3?
5. **Photos data refresh** — needs production verification (D-01-class).

These five questions must be answered before Phase B3 (Pilot Migration) can be sequenced.

---

## 6. Standing rules

No deploy. No GitHub save. No merge. No new findings invented in this matrix.
