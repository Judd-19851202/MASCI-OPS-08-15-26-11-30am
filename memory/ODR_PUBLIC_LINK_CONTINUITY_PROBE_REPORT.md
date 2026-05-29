# ODR Public-Link Continuity Probe Report

_Generated 2026-05-29T13:05:09Z · env=preview · db=masci_safety_preview_

## Counts
- ODRs: **56**
- Public links issued: **29**
- ODRs with public_access.link_id: **27**
- Preload attempts logged: **65**

## Checks
- ✅ **C1** · Unique public link_id
- ✅ **C2** · ODR public_access.link_id resolves to registry
- ✅ **C3** · Registry rows reference existing ODR id
- ✅ **C4** · doc_id format `ODR-YYYY-NNNNN`
- ✅ **C5** · doc_id uniqueness across ODRs
- ✅ **C6** · No two ODRs share an active link_id
- ✅ **C7** · preload_attempts.outcome ∈ closed enum
- ✅ **C8** · preload_attempts append-only (count never shrinks)
