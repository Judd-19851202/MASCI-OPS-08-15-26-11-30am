# TRACK 19.60 · Vendor Health Certification

## Language mandate
**Qualitative only.** Four buckets. Never a score. Never a percentage. Never a compliance certification. Never a legal-defensibility claim.

| Bucket           | Trigger                                                                             |
|------------------|-------------------------------------------------------------------------------------|
| Excellent        | Vendor `is_active` = true · zero missing key documents · zero pending approvals     |
| Good             | Vendor `is_active` = true · at most 1 missing key document · zero pending approvals |
| Attention Needed | Vendor `is_active` = true · ≥ 2 missing key documents OR ≥ 1 pending approval       |
| Restricted       | Vendor `is_active` = false                                                          |

## Signals (all from certified data)
- `suppliers.is_active`
- Vendor-lane documents with `approval_status == "linked"` grouped by `record_type` (W-9 / COI / Contract check)
- Vendor-lane documents with `approval_status` starting with `pending`

## Language forbidden (lock-tested)
- `OSHA ready`
- `legally defensible`
- `court-ready`
- `approved for all work`
- `Chain of Custody`
- Any percentage
- Any numeric score

## Rendering rules
- Every bucket is paired with a plain-English **"Why: …"** narration (same pattern as Fleet / Employee / Project / Incident threads).
- "Restricted" carries the operational cue "Treat as restricted for new work." — HR/Admin decision.
- Preferred wording: "Documents on file · COI date recorded · Requires review".

## Pure function
`vendorHealth(vendor, docs)` in `AdminVendorThread.jsx` is a ~10-line pure function over 3 fields (`is_active`, document type set, pending count). Zero backend. Zero new score model.
