# TRACK 15.73 SLICE 1 · Remediation

**Date**: 2026-02-11
**Status**: SHIPPED to preview · ready for production deploy.

## What was changed (3 files · ~30 LOC additive)

### Backend (1 file)

**`backend/routes/asset_spine.py`** — `taxonomy_by_unit` endpoint hardened with a graceful display-label-strip fallback.

```diff
@router.get("/taxonomy/by-unit/{unit_or_id}")
async def taxonomy_by_unit(...):
+   import re as _re
    doc = await db.equipment_master.find_one({"id": unit_or_id}, {"_id": 0})
+   resolution_source = "id" if doc else None
    if not doc:
        doc = await db.equipment_master.find_one(
-           {"unit_number": {"$regex": f"^{unit_or_id}$", "$options": "i"}}, {"_id": 0}
+           {"unit_number": {"$regex": f"^{_re.escape(unit_or_id)}$", "$options": "i"}}, {"_id": 0}
        )
+       if doc: resolution_source = "unit_number"
+   # Track 15.73 Slice 1 · graceful fallback: extract leading token
+   # before em-dash / hyphen separator (rescues display_label payloads).
+   if not doc:
+       leading = unit_or_id
+       for sep in (" \u2014 ", " - ", "\u2014", "\u2013"):
+           if sep in leading:
+               leading = leading.split(sep, 1)[0].strip()
+               break
+       if leading and leading != unit_or_id:
+           doc = await db.equipment_master.find_one(
+               {"unit_number": {"$regex": f"^{_re.escape(leading)}$", "$options": "i"}},
+               {"_id": 0},
+           )
+           if doc: resolution_source = "display_label_strip"
    if not doc:
        return {"found": False, "unit_number": unit_or_id,
+               "resolution_source": "not_found",
                **resolve_classification(None)}
    return {"found": True, "id": doc.get("id"),
            "unit_number": doc.get("unit_number") or "",
            "display_label": doc.get("display_label") or doc.get("label") or "",
+           "resolution_source": resolution_source,
            **resolve_classification(doc)}
```

**Side-benefit**: `re.escape()` on the user-controlled `unit_or_id` closes a
latent regex-injection issue in the case-insensitive lookup (the user could
have passed `.*` or `(?!)` and broken the match semantics).

### Frontend (2 files)

**`frontend/src/components/EquipmentCombo.jsx`** — picker now emits canonical
`unit_number` instead of display_label:

```diff
const pick = (it) => {
-  const label = it.display_label || it.make_model || "";
+  // Track 15.73 Slice 1 · trust fix · emit canonical unit_number first.
+  const label = it.unit_number || it.display_label || it.make_model || "";
   onChange?.(label);
   onPick?.(it);
   setOpen(false);
};
```

**`frontend/src/pages/NewEquipmentInspection.jsx`** — Pre-Op `onPick` now stores
`unit_number` in `equipment_unit` and captures the FK `equipment_master_id`:

```diff
<EquipmentCombo
   value={data.equipment_unit}
   onChange={(v) => set("equipment_unit", v)}
   onPick={(it) => setData((p) => ({
     ...p,
-    equipment_unit: it.display_label || it.make_model || "",
+    equipment_unit: it.unit_number || it.display_label || it.make_model || "",
+    equipment_master_id: it.id || p.equipment_master_id,
     equipment_make: it.make_model || p.equipment_make,
     equipment_serial: it.vin_serial_number || p.equipment_serial,
   }))}
/>
```

## Why this is the right fix

1. **Backend fallback is additive**. Existing callers that already pass a
   correct `unit_number` are unaffected; only the previously-failing
   display_label payloads change outcome (now resolve correctly).
2. **Frontend fix prevents new drift**. Future submissions store
   `equipment_unit="EXC-0364"` instead of `"EXC-0364 — 2022 HYUNDAI HX210A"`.
3. **Both are reversible** with `git revert` in under five minutes per file.
4. **No DB migration needed**. Historical inspection rows stay exactly as the
   field captured them — the resolver does the rescue work at read time.
5. **Resolution source telemetry** (`unit_number` / `display_label_strip` /
   `id` / `not_found`) is now observable from the API response, enabling
   future drift monitoring without DB access.

## Validation evidence

- `/app/test_reports/track_15_73_slice1_equipment_audit.json` — full collection inventory + RG007-0869 forensics
- `/app/test_reports/track_15_73_slice1_real_field_gap.json` — gap classification (rescuable vs synthetic vs unresolvable)
- `/app/test_reports/track_15_73_slice1_resolver_regression.json` — live API regression: **overall_pass=true**

Key numbers from the live regression run:

| Metric | Result |
|---|---|
| RG007-0869 literal lookup | ✅ resolved (source=unit_number) |
| RG007-0869 display_label lookup | ✅ resolved (source=display_label_strip) |
| Real field units rescued via fallback | **13 unique** (60 inspection rows) |
| Synthetic test fixtures incorrectly resolved | **0** (zero false positives) |
| Genuinely missing catalog entries | 281 (all `D52-*-<hash>` / `iter*` test fixtures) |

## What this fix does NOT do

- Does **NOT** seed missing equipment into `equipment_master`. The 281
  unresolvable units are all auto-generated test fixtures from legacy
  regression suites; they have no business representation.
- Does **NOT** migrate historical `equipment_inspections.equipment_unit`
  values. The resolver rescues them at read time; the rows themselves stay
  faithful to the field-captured original.
- Does **NOT** alter the Pre-Op UI states. The honest "Unit not cataloged
  yet" banner still fires for genuinely unknown unit numbers — exactly the
  copy approved in Track 15.72C.
- Does **NOT** change any other resolver (`taxonomy/review-needed`,
  `taxonomy/by-id`, `inspection-templates/by-asset-type`, etc.).

## Deployment instructions for operator

Standard backend + frontend redeploy. No env changes. No DB writes.

After deploy, verify:

```bash
# 1. Literal lookup (sanity)
curl -s "$URL/api/asset-spine/taxonomy/by-unit/RG007-0869" -H "X-Admin-Token: $TOKEN" | jq .

# 2. Display-label lookup (the fix)
curl -s --get "$URL/api/asset-spine/taxonomy/by-unit/RG007-0869 — 2025 JOHN DEERE 672G" \
     -H "X-Admin-Token: $TOKEN" --data-urlencode . | jq .
# expect: found=true, resolution_source=display_label_strip

# 3. Bogus (negative control)
curl -s "$URL/api/asset-spine/taxonomy/by-unit/U-9999" -H "X-Admin-Token: $TOKEN" | jq .
# expect: found=false, resolution_source=not_found
```

## Rollback

```bash
git revert <SLICE-1 commit>
sudo supervisorctl restart backend frontend
```

Rollback time: < 2 minutes. Worst case: caller sees pre-fix behaviour (display_label payload → "Unit not cataloged"). No data corruption possible — the change is read-side only.
