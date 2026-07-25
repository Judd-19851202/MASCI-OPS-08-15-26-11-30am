# BCSS Release 2 · Program 2 · Checkpoint 5
## Starter Adoption

The Operational Truth Spine is a MASCI OPS platform architecture.  
BCSS is Domain 01 and the first implementation domain.  
The artifact does not establish a separate BCSS-only truth architecture.

Date: 2026-07-25

Status: IMPLEMENTATION COMPLETE — READY FOR FORMAL ADOPTION RECORD

---

## Scope
- Wave 1 + Wave 3 starter adoption only
- exactly five selected surface families
- one canonical OTS evaluation pipeline
- one canonical projection layer
- additive compatibility only

## Canonical architecture used
- Canonical evaluation helper: `backend/lib/ots_truth.py`
- Canonical truth card object: shared internal OTS result
- Canonical public projection: `public_ots_projection()`
- Canonical relationship projection: `projected_truth_relationship()`

## Adoption coverage metric

| Metric | Count |
|---|---:|
| Selected surface families | 5 |
| Total API/UI/report/email consumers updated | 15 |
| Truth Subjects bound | 6 |
| Canonical evaluation calls | 9 |
| Legacy evaluation paths remaining | 0 within adopted families |
| Duplicate claim paths removed | 0 |
| Claim ceilings enforced | 9 |
| Prohibited wording guards | 6 |
| Projection adapters created | 3 |
| Compatibility aliases retained | 4 |

## Implementation SHA
- `d55dfaca132655c6a4c429f0f22c41a0aaed90c2`

## Future domain rule
Future domains shall adopt the Operational Truth Spine by consuming the canonical evaluation and projection architecture. No domain may implement an independent truth, claim, confidence, certification, or evidence engine.

## Selected surface families
1. Platform Data Truth
2. Recovery Snapshot
3. Backup Verification
4. Backup Trust
5. Deployment Readiness
