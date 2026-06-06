# TRENCH SAFETY · PHASE 4B — ARCHITECTURE

**Phase:** 4B — Inspections / Holds / Certifications / Alerts
**Date:** 2026-02 (preview pod)
**Status:** 🟢 Architecture locked by operator. Build in progress.

---

## 1. Operator-locked decisions

| # | Decision | Choice |
|---|----------|--------|
| 1 | Hold architecture | **A — Single enum extended.** `operational_status` is the authority. Add `Safety Hold`, `Certification Hold`, `Maintenance Hold` (renaming `Repair`). `trench_safety_holds` collection is **history/audit only**, never a parallel status. |
| 2 | Certification Hold default | **A — Explicit per-asset flag.** New asset field `requires_certification` (default `false`). Fleet is NOT auto-locked. |
| 3 | Severity matrix | **Approved.** Pass / Fail+Minor / Fail+Major / Fail+Critical map to existing+new holds + repair stubs. |
| 4 | Alert delivery | **A — In-app only.** No Resend / Twilio expansion. |
| 5 | Build scope | **Exactly the locked architecture. No new scope.** |

---

## 2. Single operational_status enum (authoritative)

```python
OPERATIONAL_STATUSES = (
    "Available",          # baseline
    "Assigned",           # on a project
    "In Transport",       # dispatch / transport in motion
    "Inspection Hold",    # failed inspection — must pass Monthly/Annual to clear
    "Maintenance Hold",   # open repair (renamed from "Repair")
    "Certification Hold", # required cert missing/expired
    "Safety Hold",        # critical damage / unsafe finding
    "Retired",            # terminal
)

HOLD_PRIORITY = {
    "Safety Hold":         100,
    "Certification Hold":   90,
    "Maintenance Hold":     80,
    "Inspection Hold":      70,
    "In Transport":         20,
    "Assigned":             10,
    "Available":             0,
    "Retired":              -1,  # terminal — never wins resolver
}
```

Backward compatibility: existing assets / mirror rows persisted with `"Repair"` are normalized to `"Maintenance Hold"` by an idempotent rewrite in `seed.py` on boot. The string `"Repair"` is removed from the enum entirely after migration.

## 3. Priority resolver

```python
def derive_operational_status(asset, open_holds) -> str:
    if asset.get("operational_status") == "Retired":
        return "Retired"
    # Pick the highest-priority active hold; fall back to assigned/in-transport/available.
    candidates = [h["kind"] for h in open_holds]  # e.g. ["Safety Hold", "Certification Hold"]
    # If asset is currently Assigned with no active holds, keep Assigned.
    base = asset.get("operational_status") or "Available"
    if not candidates:
        return base if base in ("Assigned", "In Transport", "Available") else "Available"
    return max(candidates, key=lambda k: HOLD_PRIORITY.get(k, 0))
```

Every write that touches a hold MUST recompute and persist `operational_status` from this resolver, then propagate via `upsert_equipment_master_mirror`. No write path bypasses the resolver.

## 4. Holds — history collection (audit only)

`db.trench_safety_holds` — every open/clear event recorded.

```jsonc
{
  "id": "uuid",
  "asset_id": "TB-01",
  "asset_uuid": "uuid",
  "kind": "Safety Hold",                       // one of HOLD_KINDS
  "reason": "Critical wall damage observed",   // free text
  "source": "inspection",                      // inspection | certification | manual | damage_report | repair
  "source_ref": "inspection:<id>",             // back-link
  "opened_at": "iso8601",
  "opened_by": "safety@masci.com",
  "cleared_at": null,
  "cleared_by": null,
  "clear_reason": null,
  "clear_source": null,                        // monthly_pass | cert_added | repair_completed | manual
  "is_active": true
}
```

**One asset can have multiple concurrent open holds** of different kinds. Only one row per (asset_id, kind) may be `is_active=true` at a time (idempotent open).

## 5. Inspections — extended

### New types added
- `"Special Inspection"`
- `"Damage Inspection"`
- `"Return Inspection"`

Final list:
```python
INSPECTION_TYPES = (
    "Daily Visual",
    "Monthly Competent Person",
    "Annual Review",
    "Special Inspection",
    "Damage Inspection",
    "Return Inspection",
)
```

### Severity
```python
SEVERITIES = ("None", "Minor", "Major", "Critical")
```

### Extended `InspectionSubmit`
```python
class InspectionSubmit(BaseModel):
    inspection_type: str
    inspector_name: str
    inspector_role: str = ""
    competent_person_confirmed: bool = False
    checklist: List[InspectionChecklistItem] = []
    findings: str = ""
    corrective_actions: str = ""
    result: str = "Pass"
    severity: str = "None"          # NEW
    photo_refs: List[str] = []
    signature: Optional[str] = None # NEW (base64 / signature ref)
    project_id: Optional[str] = None      # NEW (auto-filled from asset.current_project_id if omitted)
    project_name: Optional[str] = None    # NEW
    location: Optional[str] = None        # NEW (auto-filled from asset.current_location)
    follow_up_action: Optional[str] = None # NEW
```

### Severity → consequence matrix (operator-locked)
| Result | Severity | Asset status delta | Auto Repair stub | Alert kind |
|--------|----------|---------------------|------------------|------------|
| Pass | * | If Inspection Hold + (Monthly/Annual + competent_person) → clear Inspection Hold; recompute. | No | hold_cleared (if cleared) |
| Fail | None / Minor | Open Inspection Hold | No | failed_inspection |
| Fail | Major | Open Inspection Hold | Yes (status=Open, kind="repair_recommendation") | failed_inspection |
| Fail | Critical | Open **Safety Hold** + Inspection Hold | Yes | critical_damage |

## 6. Certifications

`db.trench_safety_certifications`:
```jsonc
{
  "id": "uuid",
  "asset_id": "TB-01",
  "asset_uuid": "uuid",
  "kind": "Annual Inspection",          // one of CERTIFICATION_KINDS
  "issuer": "ProShoring Engineering, PE",
  "issued_at": "2026-01-15",
  "expires_at": "2027-01-15",
  "document_ref": "",                   // free-form ref (filename / blob)
  "notes": "",
  "status": "Active",                   // Active | Expired | Superseded | Revoked
  "created_at": "iso8601",
  "created_by": "safety@masci.com",
  "updated_at": "iso8601"
}
```

`CERTIFICATION_KINDS = ("Manufacturer", "Annual Inspection", "Engineering Letter", "Repair Certification", "Special")`.

### Effect on holds
- An asset with `requires_certification=true` AND zero **non-revoked active** certifications → opens `Certification Hold` (source="certification").
- An asset with `requires_certification=true` AND **all** active certifications expired → opens `Certification Hold`.
- Adding a fresh non-expired certification → clears the Certification Hold (if it was the only blocker).
- Setting `requires_certification=false` → clears any open Certification Hold immediately (operator decision).

`requires_certification` defaults to `false` per operator decision → Phase 4B does NOT auto-lock the fleet.

## 7. Alerts — derived (no new collection)

`GET /api/trench-safety/alerts` returns a snapshot:
```jsonc
{
  "alerts": [
    {
      "asset_id": "TB-01",
      "kind": "failed_inspection",   // see kinds below
      "severity": "Major",            // Minor | Major | Critical (mapped from source)
      "opened_at": "iso8601",
      "message": "Daily Visual failed (Major) — Inspection Hold applied",
      "link": "/safety/trench-safety/assets/TB-01",
      "source_ref": "inspection:<id>"
    }
  ],
  "counts": {"failed_inspection": 1, "expired_certification": 0, ...},
  "generated_at": "iso8601"
}
```

### Alert kinds
- `failed_inspection` — latest inspection result=Fail
- `critical_damage` — Safety Hold open with source=inspection severity=Critical
- `hold_applied` — any open hold (one per kind, includes Safety/Certification/Maintenance/Inspection)
- `hold_cleared` — only surfaced in the audit log (not in the live alerts endpoint)
- `expired_certification` — `requires_certification=true` + all certs expired
- `missing_certification` — `requires_certification=true` + zero non-revoked certs
- `due_soon_90` / `due_soon_60` / `due_soon_30` — earliest-expiring cert per asset hits the window
- `inspection_overdue` — `last_inspection_at` null OR older than 30 days for active asset
- `critical_damage` — covered above

### Alert destinations (all in-app)
- Safety Portal Trench Hub: aggregate banner + count tile
- Asset Detail: per-asset card listing every active alert
- Project Panel (`TrenchSafetyOnProjectPanel`): condensed badge per asset row
- Public field view (read-only): "DO NOT USE" banner extended to Safety Hold + Certification Hold

## 8. Shop integration (no Phase-6 work)

On Fail + Major or Critical inspections, the inspections handler creates a Repair row with:
```jsonc
{
  "status": "Open",
  "kind": "repair_recommendation",
  "source": "inspection:<inspection_id>",
  "severity_at_creation": "Major" | "Critical",
  "issue_description": "<inspection findings or 'Critical damage observed'>",
  "requires_reinspection": true,
  ...
}
```

This row is automatically surfaced by the existing `GET /api/trench-safety/assets/{id}/repairs?status=Open` endpoint that Shop's UI consumes in Phase 6. **No new shop UI** in Phase 4B.

## 9. Equipment Master mirror (Phase 4A — extended)

`upsert_equipment_master_mirror` continues to be the **only** write path into `equipment_master` for trench rows. It now also carries:
- `requires_certification`
- `active_holds` — list of `{kind, opened_at}` for the open holds
- `certification_status` — `OK | Due Soon | Expired | Missing | Not Required`
- `last_inspection_result` / `last_inspection_severity`

These flow through to Dispatch / Project Dashboards / Global Search **for free** because every consumer reads from `equipment_master`.

## 10. Routes added (all `/api` prefixed)

| Method | Path | Auth |
|--------|------|------|
| GET | `/api/trench-safety/assets/{id}/holds` | any_portal |
| POST | `/api/trench-safety/assets/{id}/holds` | safety_or_admin |
| POST | `/api/trench-safety/holds/{hold_id}/clear` | safety_or_admin |
| GET | `/api/trench-safety/assets/{id}/certifications` | any_portal |
| POST | `/api/trench-safety/assets/{id}/certifications` | safety_or_admin |
| PATCH | `/api/trench-safety/certifications/{cert_id}` | safety_or_admin |
| POST | `/api/trench-safety/certifications/{cert_id}/revoke` | safety_or_admin |
| GET | `/api/trench-safety/alerts` | any_portal |

Modified (extended payloads, no new paths):
- `POST /api/trench-safety/assets/{id}/inspections` — accepts `severity`, signature, project/location.
- `GET /api/trench-safety/by-project` — enriched per-asset with `holds`, `certification_status`, `last_inspection`.
- `PUT /api/trench-safety/assets/{id}` — accepts `requires_certification`.
- `GET /api/trench-safety/dashboard` — surfaces new alert counts.

## 11. Frontend surfaces

| File | Add / Modify |
|------|--------------|
| `pages/trench_safety/TrenchSafetyAssetDetail.jsx` | Active Holds card, Certifications card, "Log Inspection" CTA opens the new severity-aware modal |
| `pages/trench_safety/TrenchSafetyInspectionModal.jsx` (NEW) | Full 6-type + severity submission |
| `pages/trench_safety/TrenchSafetyCertificationsCard.jsx` (NEW) | List + Add + Revoke; toggles `requires_certification` |
| `pages/trench_safety/TrenchSafetyHoldsCard.jsx` (NEW) | List open holds + Manual Open / Clear (safety/admin) |
| `pages/trench_safety/TrenchSafetyAlerts.jsx` (NEW) | Alerts inbox tab on the Safety Portal |
| `pages/trench_safety/TrenchSafetyShell.jsx` | Add "Alerts" tab |
| `pages/trench_safety/TrenchSafetyHub.jsx` | Alert tile |
| `components/trench/TrenchSafetyOnProjectPanel.jsx` | Add per-row hold / cert / inspection-status badges |
| `pages/trench_safety/TrenchSafetyQrLanding.jsx` + `PublicTrenchSafetyDashboard.jsx` | Extend "DO NOT USE" banner |
| `lib/i18n.js` | Spanish translations |

## 12. Tests

`tests/test_trench_safety_phase4b.py` — covers every acceptance row from the forensic audit § 4.

## 13. Migration

Single idempotent function at boot (`seed.py`): rewrite `operational_status="Repair"` → `"Maintenance Hold"` on both `trench_safety_assets` and `equipment_master`. Safe to run repeatedly.

---

**Architecture confirmed. Build begins now.**
