# TRACK 16.04 · MASCI Transportation Foundation · Phase 1

**Date:** 2026-06-27
**Status:** ✅ GO
**Scope:** core data model + identity + eligibility skeleton only.
**MASCI Operations Platform.** Not ForgedOps Academy.

---

## Mission

Build the stable Phase 1 foundation for the MASCI Transportation &
Logistics module. Phase 1 = data model + identity + eligibility
skeleton. **No hauler packet uploads, orientation engine, quizzes,
certificates, carrier portal, public invite links, or intelligence
dashboards.** Those are explicitly deferred to later phases.

---

## What was built

### Backend (`/app/backend`)
| Path | Purpose |
|---|---|
| `lib/transport_eligibility.py` | Pure compute · status truth-table · HR-lifecycle override · returns one of `eligible / pending_review / needs_correction / expired / suspended / not_dispatchable`. |
| `lib/transport_identity.py` | Async resolvers: `find_existing_employee_projection`, `find_existing_leased_driver`, `display_name`. Prevents duplicate MASCI-employee projection and duplicate leased-driver-by-license. |
| `routes/transportation.py` | Carrier / Person / Truck / Eligibility router. Admin-strict CRUD + Dispatch read-only. Audit row on every create/update via `db.audit_events.insert_one`. Self-contained dispatch-or-admin gate (admin path uses `is_valid_directory_admin_token_async` — fixes the legacy sync-validator gap on Phase 1 dispatch endpoints). |
| `server.py` | Single new register call: `register_transportation_routes(app, db, require_admin_dep=require_admin_strict, require_dispatch_or_admin_dep=_shared_dispatch_or_admin)`. |

### Frontend (`/app/frontend`)
| Path | Purpose |
|---|---|
| `src/pages/AdminTransportation.jsx` | `/admin/transportation` page with 4 Tabs (Carriers · Drivers · Trucks · Eligibility). Full `data-testid` coverage. Uses existing `PortalShell` + `AdminSideNavV2`. No clickable buttons for un-implemented Phase 2/3 actions. |
| `src/App.js` | Lazy import + `<Route path="/admin/transportation" element={A(<AdminTransportation />)} />`. |

### Tests
| Path | Purpose |
|---|---|
| `backend/tests/test_track_16_04_transportation_foundation.py` | 24 regression tests covering all 22 directive scenarios + 2 bonus identity-resolver shape checks. All green in 0.08 s. |
| `scripts/deployment_gate.py` | New file appended to `REGRESSION_FILES`. |

### Documentation
| Path | Purpose |
|---|---|
| `memory/TRACK_16_04_TRANSPORTATION_FOUNDATION_PHASE_1.md` | This document. |
| `memory/PRD.md` | New track entry. |

---

## Data model (Phase 1 — additive collections)

### `carriers`
`id` · `tenant` · `legal_name` · `dba_name` · `carrier_type` ∈ {`leased_hauler`, `owner_operator`, `supplier`, `masci_internal`, `other`} · `dot_number` · `mc_number` · `contact_name/phone/email` · `status` ∈ Phase-1 status enum · `safety_hold` · `notes` · `created_at/by` · `updated_at/by`.
**Invariant:** no two active (`status ≠ inactive`) carriers in the same tenant may share a `legal_name`. Enforced at POST + PATCH.

### `transport_persons`
`id` · `tenant` · `kind` ∈ {`masci_employee`, `leased_driver`} · `employee_id` (nullable) · `carrier_id` (nullable) · `first_name` · `last_name` · `phone` · `email` · `license_number` · `cdl_class` · status enum · `safety_hold` · audit cols.
**Invariants:**
1. `kind=masci_employee` ⇒ `employee_id` required.
2. `kind=leased_driver` ⇒ `carrier_id` required (and must reference an existing carrier in the same tenant).
3. Active `(tenant, kind=masci_employee, employee_id)` is unique.
4. Active `(tenant, kind=leased_driver, carrier_id, license_number)` is unique when `license_number` is present.

### `transport_trucks`
`id` · `tenant` · `ownership` ∈ {`masci_owned`, `leased_carrier`, `owner_operator`, `unknown`} · `equipment_id` · `carrier_id` · `truck_number` · `vin` · `plate` · `truck_type` ∈ {`dump_truck`, `flow_boy`, `lowboy`, `tanker`, `roll_off`, `service_truck`, `other`} · status enum · `safety_hold` · audit cols.
**Invariants:**
1. `ownership ∈ {leased_carrier, owner_operator}` ⇒ `carrier_id` required.
2. `ownership = masci_owned` ⇒ `equipment_id` may link to Equipment Master (optional, advisory).

### `transport_eligibility_state` (derived read-model)
`id` · `tenant` · `target_type` ∈ {`carrier`, `person`, `truck`} · `target_id` · `state` ∈ Phase-1 eligibility enum · `reasons[]` · `computed_at` · `expires_at` · `stale` · `phase`.
Recomputed on every write to the underlying record AND on every read (Phase 1 keeps admin UI freshness simple).

---

## Eligibility truth table (Phase 1)

| Input | Resulting state |
|---|---|
| `status = inactive` | `not_dispatchable` |
| `safety_hold = true` | `suspended` |
| `status = suspended` | `suspended` |
| `status = expired` | `expired` |
| `status = needs_correction` | `needs_correction` |
| `status = pending_review` | `pending_review` |
| `status = active` (no override) | `eligible` |
| `kind = masci_employee` AND `hr_lifecycle_active = false` | `not_dispatchable` (overrides everything else) |

HR lifecycle is resolved against the canonical `employees` collection
via `_hr_lifecycle_active(db, employee_id)`. Missing employee → `None`
(no eligibility flip; admin can resolve).

---

## API surface

### Admin (require admin-strict)
| Method | Path |
|---|---|
| GET / POST | `/api/admin/transportation/carriers` |
| GET / PATCH | `/api/admin/transportation/carriers/{id}` |
| GET / POST | `/api/admin/transportation/persons` |
| GET / PATCH | `/api/admin/transportation/persons/{id}` |
| GET / POST | `/api/admin/transportation/trucks` |
| GET / PATCH | `/api/admin/transportation/trucks/{id}` |
| GET | `/api/admin/transportation/eligibility/{target_type}/{target_id}` |

### Dispatch (require dispatch or admin · READ-ONLY)
| Method | Path |
|---|---|
| GET | `/api/dispatch/transportation/eligible-drivers` |
| GET | `/api/dispatch/transportation/eligible-trucks` |
| GET | `/api/dispatch/transportation/status/{target_type}/{target_id}` |

No public routes. No write endpoints exposed to dispatch in Phase 1.

---

## Audit

Every create / update writes one row into `db.audit_events`:

```
{ id, kind, entity_type, entity_id, actor, old, new, ts, tenant, route, ip, ua }
```

Audit kinds in this track: `transport_carrier_create`,
`transport_carrier_update`, `transport_person_create`,
`transport_person_update`, `transport_truck_create`,
`transport_truck_update`. (Eligibility recompute is logged only via
the `transport_eligibility_state` row, not a separate audit entry —
status changes that drive eligibility shifts are themselves captured
under the per-entity update audit.)

---

## RBAC

* Admin routes: `require_admin_strict` (Track 15.32 per-user admin
  validator). PM / Shop / HR / Safety / Dispatch tokens are rejected.
* Dispatch routes: self-contained gate that accepts the canonical
  per-user admin token (via `is_valid_directory_admin_token_async`)
  OR the dispatch portal token (via `is_valid_dispatch_user_token_async`).
* No public surface. No external carrier surface. No unauthenticated
  invite tokens.

---

## MASCI Hauler Pack baseline map

The existing MASCI hauler agreement and packet remain the legal
baseline. Phase 1 prepares the data model so Phase 2 can convert
that packet into a digital onboarding workflow without losing any
current requirement.

### Carrier (entity-level requirements → `carriers` + future packet sections)

| Current packet item | Phase 1 lands at | Phase 2 docs/section |
|---|---|---|
| Company information / legal name / DBA | `carriers.legal_name` · `carriers.dba_name` | — |
| FEIN | _deferred_ (Phase 2: `carrier_documents.fein`) | W-9 packet |
| FDOT / DOT / MC numbers | `carriers.dot_number` · `carriers.mc_number` (FDOT in Phase 2 `carrier_compliance.fdot_number`) | Carrier compliance section |
| Company address / contact / contact method | `carriers.contact_*` | Carrier identity section |
| Certificate of Corporation / Sunbiz active entity proof | _deferred_ | Carrier docs · `sunbiz_proof` |
| MCS company snapshot / FMCSA proof | _deferred_ | Carrier docs · `fmcsa_snapshot` |
| W-9 | _deferred_ | Carrier docs · `w9` |
| Signed Subcontractor Hauling Agreement | _deferred_ | Agreement section · digital signature in P2 |
| Insurance certificate · minimum $300k coverage · additional-insured language · waiver of subrogation · cancellation notice | _deferred_ | Carrier docs · `insurance.coi` + `insurance.policy_attrs` |
| Independent contractor language · attorney fees / indemnification | _deferred_ | Agreement section |
| Workers comp responsibility | _deferred_ | Agreement section |
| Lien release authorization · payment pickup authorization | _deferred_ | Agreement section |
| Licensing certification page | _deferred_ | Agreement section |
| Signature blocks | _deferred_ | Digital signature in P2 |

### Truck (`transport_trucks`)

| Current packet item | Phase 1 lands at | Phase 2 |
|---|---|---|
| Current truck numbers | `transport_trucks.truck_number` | — |
| Vehicle registration | _deferred_ | `truck_documents.registration` |
| Truck numbering / stickers | `transport_trucks.truck_number` + future `sticker_status` | Phase 2 truck checklist |
| Tarp system requirement | _deferred_ | Truck inspection / acknowledgement |
| Backup warning device / CB radio | _deferred_ | Truck inspection / acknowledgement |
| FleetWatcher / GPS verification | _deferred_ | Truck integration field · `fleetwatcher_asset_id` |

### Driver (`transport_persons`)

| Current packet item | Phase 1 lands at | Phase 2 |
|---|---|---|
| DOT-certified drivers · driver roster | `kind` · `license_number` · `cdl_class` | Driver docs + Clearinghouse |
| FMCSA Clearinghouse documentation | _deferred_ | Driver docs · `clearinghouse` |
| CDL copy / class / expiration | `cdl_class` (free-text), expiration deferred | Driver docs · `cdl` |
| Medical card | _deferred_ | Driver docs · `medical_card` |
| Orientation completion · no-skip orientation video · quizzes · certificates | _deferred_ | Phase 3 Orientation Engine |
| Critical safety acknowledgements · driver digital signature | _deferred_ | Phase 2 packet signature flow |

### Dispatch / Safety / Payment / Tickets (operational rules → preserved doctrine, surfaced in later phases)

`Firearms prohibition` · `unlawful roadway discharge prohibition` ·
`accident / injury reporting` · `damage documentation requirements` ·
`hourly rate / payment rules` · `ticket submission deadline` ·
`ticket completion requirements` · `unauthorized stop deductions` ·
`hot asphalt stop deduction` · `GPS clock-in / clock-out` ·
`dispatch notification requirements` · `rain delay / check-in rules` ·
`afternoon dispatch check-in` → **all preserved verbatim in the legacy
packet**; digitized as acknowledgement checkboxes + audit during
Phase 2 packet build. Phase 1 introduces no new copy here.

### What Phase 1 prepares now
1. Stable `carriers / transport_persons / transport_trucks` identity
   layer (no duplication of HR or equipment master).
2. Eligibility skeleton ready to absorb document-expiration logic
   (Phase 2) and orientation completion (Phase 3) without breaking
   contract — `compute_transport_eligibility` accepts a `context`
   bag that future phases extend.
3. Audit trail ready for legal/insurance review without new plumbing.

### What Phase 2 (Hauler Packet) must build next
1. `carrier_documents` collection with R2-backed uploads (W-9,
   COI, sunbiz, MCS, signed agreement) — reuses the existing
   `photo_storage` engine; introduces no new storage system.
2. Per-driver document subcollection (CDL, medical, Clearinghouse).
3. Invite link / packet workflow (admin-issued · expiring · signed
   acknowledgements · digital signature).
4. Document-expiration tracking → wired into eligibility via the
   `context` extension hook already in `compute_transport_eligibility`.
5. Carrier-portal acknowledgement surface (read-only for now).

---

## Deferrals (explicit · do NOT ship in Phase 1)

* Remote invite links · hauler packet uploads · digital signature.
* Clearinghouse document intake · CDL / medical expiration logic.
* No-skip orientation video engine · quizzes · certificates.
* Dispatch hard-block enforcement (eligibility is computed but does
  not yet gate the assignment workflow).
* Carrier portal · public onboarding links.
* Intelligence / scorecards · driver / carrier ratings.
* Email notification routes for transportation events.
* Bulk migration / auto-import of existing employees & trucks.

---

## Tests (24 / 24 green · 0.08 s)

All 22 directive scenarios + 2 bonus identity-resolver checks.
Wired into `scripts/deployment_gate.py` under `REGRESSION_FILES`.

Live happy-path verified end-to-end against the local backend:
* Carrier POST → 201 + audit row
* Leased driver POST under that carrier → 201
* Duplicate-license POST under same carrier → 409
* Truck POST (leased) → 201
* Eligibility GET on carrier → `pending_review` with correct reason
* Dispatch read endpoint with `X-Admin-Token` → 200
* Dispatch read endpoint with `X-Dispatch-Token` → 200
* Anonymous dispatch read → 401
* Dispatch token attempting admin POST → 401

---

## Risks / unknowns

* **HR lifecycle resolver** consults `employees`. Field-name
  heuristics cover `is_active`, `terminated`, `lifecycle_status`,
  `status`. If a future HR migration renames these, the override
  silently degrades to "unknown" (no false `not_dispatchable`) but
  may also miss real terminations. Lock a clearer HR-lifecycle
  contract in Phase 5 (HR / Safety Integration).
* **Pre-existing `_require_dispatch_or_admin` wrapper bug** (server.py
  line 11781) — the wrapper calls the shared factory's inner without
  `request`. Track 16.04 sidesteps this by building its own gate inline.
  A separate cleanup track should fix the global wrapper or migrate
  fleet_ops to the canonical shared factory.

## Next recommended track

**Track 16.05 — Phase 2 Hauler Packet (intake)**:
`carrier_documents` collection + invite/upload workflow, reusing
R2 storage. Extends eligibility via the `context` hook already
provided in `compute_transport_eligibility`. No orientation /
quizzes / certificates yet (Phase 3).
