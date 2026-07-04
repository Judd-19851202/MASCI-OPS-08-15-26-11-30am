# TRACK 19.62 · Asset Thread — Fire Protection Branch

## Trigger
When `asset.asset_class` (case-insensitively) contains `"Fire Protection"`.

## Mission section (Section 1)
Facts panel replaced with:
- Extinguisher label (unit_id or asset_id)
- Type (canonical from taxonomy or legacy string)
- Serial
- Assignment (target label or fallback chain: facility → room → unit → location detail)
- Assignment kind (target kind or legacy `location_kind`)
- Location detail
- Last inspection date
- Next due
- Last inspection status
- Timeline events count
- Documents linked count

## Attention section (Section 2 · max 5)
Rules, in order:
1. **CRITICAL — Failed Inspection** if `last_status.toLowerCase() === "fail"`.
2. **HIGH — Inspection Overdue** if `next_due_date < today`.
3. **MEDIUM — Assignment Missing** if no `assigned_target_ref` / `_kind` / `_unit_number` / `_facility_name`.
4. **MEDIUM — Record Missing** if both `serial_number` and `asset_tag` are empty.
5. **MEDIUM — N fire documents awaiting HR/Admin approval** if any pending historical records exist.

Wording is deliberately non-compliance:
- ✅ "Needs Attention"
- ✅ "Inspection Overdue"
- ✅ "Assignment Missing"
- ✅ "Record Missing"
- ❌ NOT "OSHA compliant"
- ❌ NOT "legally compliant"
- ❌ NOT "certified safe"
- ❌ NOT "fire-code compliant"

Lock test asserts the forbidden phrases do not appear in the page.

## Relationships section (Section 5)
Edges emitted for Fire Protection subjects:
- Parent asset (via `assigned_unit_number` / `equipment_master_id`) with deep-link back into `/admin/assets/<parent>/thread`.
- Facility + optional room.
- Project (when `assigned_project_number` present).
- Safety Portal · Fire Extinguishers (always — inspection authoritative surface).
- Historical Records asset lane (when linked docs exist).

## Timeline (Section 4)
Reads Historical Records linked docs into timeline events (same
mapping used for other asset entities). Live extinguisher inspection
history remains in the Safety Portal in Phase A; Phase B projects
those events into the backbone.

## Header cross-links
- **Manage in Safety Portal** — always shown for Fire Protection class.
- **Add asset document** — routes to Historical Records intake pre-populated with `entity_kind=asset` + `asset_id`.
- **Fleet lens** — routes to the Fleet Unit Thread pilot when the extinguisher has a parent unit.
- **Asset master** — routes to `/admin/equipment`.

## Non-goals for Phase A
- No write path from the thread into `db.fire_extinguishers`.
- No embedded inspection form on the thread page.
- No new PDF export from the thread.
- No new OI product.
