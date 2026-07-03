# TRACK 20.4 · Final Recommendation

## Decision
🟢 **PROMOTE + EXTEND (small).**

## Proposed Track 19.60 scope
### Route
`/admin/vendors/:vendorId/thread` (HR/Admin owner portal) — with cross-links from:
- Admin `SupplierMasterPanel` row → thread
- PM `PmSuppliers` row → thread (role-lensed view)
- Safety cases → vendor thread if vendor is a linked party

### Owner portal
- **Admin / HR** owns the route.
- **PM / Safety / Shop / Fleet / Dispatch / Ops / Executive** consume via role-lensed URL params (e.g. `?lens=pm|safety|shop|fleet|dispatch|exec`) OR via role-inferring guards.
- **Zero permission widening.**

### Adapters (all pure functions)
1. `missionAdapter({ vendor, docs, po_summary })` — name, kind, status, do-not-use, health chip + "Why:" narration.
2. `attentionAdapter({ vendor, docs, po_summary, incidents })` — max 5, sourced from COI expiration, PO overdue, safety flags, missing W-9.
3. `actionQueueAdapter({ vendor, docs, po_summary })` — up to 5 specific verbs (Upload W-9 · Renew COI · Approve contract · Resolve overdue PO · Verify prequalification).
4. `timelineAdapter({ documents, po_events })` — union of PO events + document upload events + status change events.
5. `relationshipAdapter({ vendor, pos, incidents })` — POs, PMs, projects, incidents, carrier compliance (deep-link if applicable).
6. `documentsAdapter({ vendor_docs })` — reads from vendor lane of Historical Records.
7. `photosAdapter` → shell empty.
8. `oiAdapter` → honest empty (no `vendor_intelligence` OI product).
9. `historyAdapter({ pos, docs, status_events })` — chronological composite.
10. `auditAdapter({ vendor_audit })` — reads from `historical_records_audit` filtered by entity.

### Required endpoints
- `GET /api/suppliers` + `GET /api/admin/suppliers/{id}` (**enrich response with a few flags — small backend LOC**).
- `GET /api/po-requests?supplier=<n>` (already exists — filter param supported client-side today; may need explicit server-side filter — small LOC).
- `GET /api/historical-records?entity_kind=vendor&entity_id=<vendor_id>` (**vendor lane extension**).
- `GET /api/historical-records/audit?entity_kind=vendor&entity_id=<vendor_id>` (**vendor lane extension**).
- Existing dispatch / material / shop endpoints — used verbatim.

### Estimated LOC
- **Backend LOC: ≤ 350** — vendor lane discriminator on Historical Records + a handful of new fields on `suppliers` + a small server-side `supplier` filter on `/api/po-requests`.
- **Frontend LOC: ≈ 500** — new `AdminVendorThread.jsx` + adapters + entry point on `SupplierMasterPanel` and `PmSuppliers`.
- **Lock test LOC: ≈ 150**.

### Permission model
- Admin / HR: full.
- Accounting: full financial-adjacent read (payments deferred).
- PM: scoped read + no tax / no full contract value / no cross-project.
- Safety: scoped read + no financials.
- Shop / Fleet / Dispatch / Trans: relevant subset only.
- Executive: summary only.
- Field / Public: no thread access.

### Document model
- Vendor lane of Historical Records Intake. HR/Admin approves; PM/Safety/Shop may submit.

### Upload model
- Reuse existing multipart intake. No new pipeline.

### Contract future path
- Contracts stored as vendor-lane documents in Track 19.60.
- Signing / renewal automation deferred to a later dedicated track.

### Audit model
- Reuse `historical_records_audit` with `entity_kind` discriminator.

### Deployment risk
🟢 **LOW** — additive frontend + a small, backwards-compatible schema discriminator. No env, no migration blocker.

### Build sequence
1. Track 19.59 — **audit-follow-through**: land the vendor lane on Historical Records (small backend + frontend).
2. Track 19.60 — **PROMOTE**: `AdminVendorThread.jsx` + adapters + cross-links.
3. Track 19.61 — **health chip flags**: add do-not-use / prequalification fields to `suppliers`.
4. Later — contract signing / AP integration.

## Justification for `PROMOTE + EXTEND` over `PROMOTE + ADAPTERS`
Adapters-only would force us to fabricate a Documents section (W-9 / COI / contracts don't exist as first-class records today). The mandate forbids fabrication. The smallest honest path is to formalise the vendor lane in Historical Records — an extension small enough to keep this a "promotion" rather than a rebuild.
