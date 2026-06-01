# Incident Status · Data Model Audit

**Batch:** OMEGA · Forensic Audit · Incident Lifecycle Status · Data Model
**Mode:** READ-ONLY
**Companion:** `INCIDENT_LIFECYCLE_AUDIT.md` · `INCIDENT_STATUS_UI_AUDIT.md`
**Date:** 2026-06-01

---

## 1 · Pydantic schema

### 1.1 · `IncidentCreate` (input model · `routes/safety.py:202-254`)

```
model_config = ConfigDict(extra="allow")

DECLARED FIELDS (52)
─────────────────────────────────────────────────────────────────
project_name             str           required
project_number           str           "" default
location                 str           required
incident_date            str           required
incident_time            str           required
reported_date            str           required
reported_by              str           required
supervisor_name          str           "" default

incident_type            str           required
severity                 str           required
osha_recordable          str           "No" default
work_stopped             str           "No" default

person_name              str           "" default
person_role              str           "" default
person_employer          str           "" default
person_years_experience  str           "" default
body_part                str           "" default
injury_nature            str           "" default
treatment_provided       str           "" default
medical_facility         str           "" default
sent_home                str           "No" default

description              str           required
immediate_cause          str           "" default
contributing_factors     str           "" default
root_causes              dict          {} default
root_cause_notes         str           "" default

witnesses                list          [] default

immediate_actions_taken  str           "" default
corrective_actions       str           "" default
responsible_party        str           "" default
target_completion_date   str           "" default

notified_safety_manager  str           "No" default
notified_pm              str           "No" default
notified_gc              str           "No" default
notified_owner           str           "No" default
notified_osha            str           "No" default
notified_other           str           "" default

photos                   list          [] default

reporter_signature       str           "" default
supervisor_signature     str           "" default
distribution_list        list          None default (max 20)

NOT DECLARED (but allowed by extra="allow")
─────────────────────────────────────────────────────────────────
status                   (Sprint 1B backfill only)
resolution_status        (Sprint 1B backfill only)
_backfilled_status_at    (Sprint 1B marker)
_backfilled_status_reason (Sprint 1B marker)
corrected_on_site        (set by NewIncident form · drives derivation)
closed_at                NOT PRESENT
closed_by                NOT PRESENT
under_investigation      NOT PRESENT
corrective_action_required NOT PRESENT
pending_closure          NOT PRESENT
investigation_status     NOT PRESENT
lifecycle                NOT PRESENT
workflow_state           NOT PRESENT
```

### 1.2 · `Incident` (output model · `routes/safety.py:257-260`)

```
class Incident(IncidentCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""        # INC-YYYY-NNNNN
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
```

Adds three fields. No status, no lifecycle, no audit trail.

### 1.3 · `IncidentSummary` (list response · `routes/safety.py:263-275`)

```
id                  str
project_name        str
location            str
incident_date       str
incident_type       str
severity            str
person_name         str
reported_by         str
osha_recordable     str
photo_count         int
created_at          str
```

11 fields. **`status` is not projected into the list response.** Frontend filters by `i.status || "Open"` on the list page (`SafetyIncidents.jsx:72`) — meaning every incident in the list response shows status "Open" because the field is never returned.

---

## 2 · Actual DB state (production sample)

Probe: `GET https://mascidocs.com/api/incidents/87c8535b-ec64-4c06-aca0-01d5ebf9b3ec` (incident `INC-2026-00011` · created 2026-05-21).

```
Fields actually present in the document (49 keys, alphabetized):

_backfilled_status_at        str   "2026-06-01T00:10:54.210000+00:00"   ← Sprint 1B
_backfilled_status_reason    str   "Sprint 1B · OMEGA status backfill"  ← Sprint 1B
body_part                    str   ""
contributing_factors         str   "Contributing Factors:..."
corrective_actions           str   "* Reinforce dump truck departure procedures..."
created_at                   str   "2026-05-21T11:09:48.572061+00:00"
description                  str   "On the morning of the incident @ roughly 4:35 am..."
distribution_list            list  []
doc_id                       str   "INC-2026-00011"
employee_master_id           str   ""
equipment_master_id          str   ""
gps_accuracy                 None
gps_lat                      None
gps_lng                      None
id                           str   "87c8535b-ec64-4c06-aca0-01d5ebf9b3ec"
immediate_actions_taken      str   "* Incident was reported to MASCI safety/management..."
immediate_cause              str   "The driver failed to verify..."
incident_date                str   "2026-05-19"
incident_time                str   "04:35"
incident_type                str   "Property / Equipment Damage"
injury_nature                str   ""
location                     str   "I-95"
medical_facility             str   ""
notified_gc                  str   "No"
notified_osha                str   "No"
notified_other               str   ""
notified_owner               str   "Yes"
notified_pm                  str   "Yes"
notified_safety_manager      str   "Yes"
osha_recordable              str   "No"
person_employer              str   ""
person_name                  str   ""
person_role                  str   ""
person_years_experience      str   ""
photos                       list  ['data:image/jpeg;base64,...']
project_name                 str   "T5860 SR 9 (I-95)"
project_number               str   "25-22 - CP"
reported_by                  str   "Jaymn Judd"
reported_date                str   "2026-05-19"
reporter_signature           str   "data:image/png;base64,..."
resolution_status            str   "open"                                ← Sprint 1B
responsible_party            str   "MASCI Operations / Safety Department..."
root_cause_notes             str   "Root cause analysis indicates..."
root_causes                  dict  {procedure: True, communication: True, fatigue: True, ...}
sent_home                    str   "No"
severity                     str   "near_miss"
status                       str   "open"                                ← Sprint 1B
submit_language              str   "en"
supervisor_name              str   "Brian Harden"
supervisor_signature         str   ""
target_completion_date       str   "2026-06-26"
treatment_provided           str   ""
witnesses                    list  [{name:"", statement:"MASCI Paving Crew"}]
work_stopped                 str   "No"
```

### 2.1 · Status-related fields present

| Field | Value | Origin |
|---|---|---|
| `status` | `"open"` | Sprint 1B backfill 2026-06-01 |
| `resolution_status` | `"open"` | Sprint 1B backfill 2026-06-01 |
| `_backfilled_status_at` | timestamp | Sprint 1B marker |
| `_backfilled_status_reason` | "Sprint 1B · OMEGA status backfill" | Sprint 1B marker |

### 2.2 · Status-related fields ABSENT

| Operator-requested field | Present in any doc? |
|---|---|
| `lifecycle` | ❌ |
| `workflow_state` | ❌ |
| `closure_status` | ❌ |
| `closed_at` | ❌ |
| `closed_by` | ❌ |
| `under_investigation` | ❌ |
| `corrective_action_required` | ❌ |
| `pending_closure` | ❌ |
| `investigation_status` | ❌ |

---

## 3 · Sprint 1B backfill trace

### 3.1 · Origin

Source: `/app/memory/CLEANUP_EXECUTION_REPORT.md` (2026-06-01 00:09 UTC).

```
Step 6 · UPDATE_MANY · incidents (status=null backfill)
  Before:  6 docs with status=null
  After:   0 docs with status=null
  Modified: 6
```

The script that did this is `/tmp/sprint1b_phase3.py` (transient — no longer on disk). The rollback recipe in `CLEANUP_EXECUTION_REPORT.md:56` is:

```javascript
db.incidents.update_many(
  {_backfilled_status_reason: "Sprint 1B · OMEGA status backfill"},
  {$set: {status: null, resolution_status: null},
   $unset: {_backfilled_status_at: "", _backfilled_status_reason: ""}}
)
```

### 3.2 · What the backfill did

* Set `status = "open"` on 6 docs that had `status = null`.
* Set `resolution_status = "open"` on the same 6 docs.
* Stamped `_backfilled_status_at` + `_backfilled_status_reason` for audit traceability.
* **Did not** install any code path to change `status` afterward.

### 3.3 · What the backfill did NOT do

* Did not declare the field in the Pydantic schema.
* Did not add a PATCH/PUT endpoint.
* Did not add a frontend editor.
* Did not add a state-machine.
* Did not add an audit collection (`incident_status_changes` does not exist — verified by grep across `/app/backend`).
* Did not normalize the vocabulary across consumers.

---

## 4 · Indexes on `incidents`

Cannot probe without exfil access to production Mongo. From the code path:
* No `db.incidents.create_index("status")` exists in `/app/backend/server.py` startup hooks.
* No `db.incidents.create_index("resolution_status")` exists.
* The Sprint 1B backfill marker fields are not indexed.

This means any future query on `status` will table-scan. Acceptable today because no query meaningfully uses it.

---

## 5 · Read paths that DO consult `status` / `resolution_status`

| File | Line | Field | Purpose |
|---|---|---|---|
| `routes/project_health.py` | 184 | `resolution_status` | count unresolved incidents (uses `!= "Closed"`) |
| `routes/project_health.py` | 188-189 | `resolution_status` + `severity` | count unresolved high/critical |
| `routes/operations_center.py` | 180 | `resolution_status` | filter active issues |
| `routes/governance.py` | 336 | `status` | integrity rule `INC_CLOSED_CAPA_OPEN` |
| `routes/governance.py` | 824 | `status` | second pass on same integrity rule |
| `routes/governance.py` | 361, 867 | `status` | embed in rule payload |
| Frontend `SafetyIncidents.jsx` | 72 | `status` | client-side filter |
| Frontend `SafetyIncidents.jsx` | 169 | `status` | render status pill |

Note: every one of these is a **read** path. There are **zero write paths.**

---

## 6 · Read paths that IGNORE `status` and derive their own

| File | Function | Derivation |
|---|---|---|
| `lib/accountability_projection.py:596` | `_status_for_incident` | `corrected_on_site == "yes"` → "resolved"; linked CAPA resolved → "resolved"; linked CAPA open → "in_progress"; else → "open" |
| `routes/command_center.py:484` | `_incident_is_resolved` | same derivation as above (cited via helper) |
| `frontend/src/pages/ViewIncident.jsx:68` | `computeFollowUpStatus` | `severity ∈ {medical, restricted, lost_time, fatality}` OR `osha_recordable=="Yes"` × CAPA open/closed counts |
| `routes/hr_portal.py:1561` | open-count probe | uses `corrected_on_site != "Yes"` + age filter |

---

## 7 · Audit trail / history

**No audit collection exists for incident status changes.**

* No `incident_status_changes` collection — verified via grep across `/app/backend`.
* No `audit_events.kind == "incident_status_changed"` entry pattern — verified via grep.
* The only incident-related audit is `audit_events.kind == "incident_deleted"` (set by the DELETE handler at `routes/safety.py:880`).

If the operator authorizes a closure workflow in a future batch, an audit trail must be designed alongside it — there is no infrastructure to build on.

---

## 8 · Summary verdict (data model only)

* ✅ A `status` field exists, with `resolution_status` parallel field.
* ✅ Sprint 1B backfilled values from null → "open".
* ❌ Field is not declared in the Pydantic schema.
* ❌ Field is not projected into the list response.
* ❌ No write endpoint exists.
* ❌ No closure-state vocab is canonized (5 vocabularies fragment the concept).
* ❌ No audit trail exists.
* ❌ No indexes exist for status-bound queries.

🟡 **Data model state: latent.** The field exists; the model does not.

---

## 9 · OMEGA discipline

| Rule | Observed |
|---|---|
| Read-only audit | ✅ |
| Evidence-first | ✅ |
| No code changes | ✅ |
| No remediation proposed | ✅ |
| Stop after schema assessment | ✅ |

🛑 Data-model audit complete. Continue to `INCIDENT_STATUS_UI_AUDIT.md` for the UI inventory.
