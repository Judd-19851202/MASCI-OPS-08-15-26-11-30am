# TRACK 21.3 · Phase D · Singleton Mongo Collection Retention Review

**Date:** 2026-07-04
**Baseline:** 68 collection-name candidates referenced exactly once across `backend/**/*.py`.

## Method

Static regex scan (`db[<name>]` / `db.<name>`) with a method-noise filter. **The scanner cannot distinguish between real Mongo collection names and Python attribute lookups against a `db`-named variable in an unrelated helper.** Manual review of the 68 candidates is required to separate signal from noise.

## Findings

| Bucket | Count | Classification |
|---|---|---|
| Actual audit collections (referenced once by design) | ~5 (`mfa_audit_events`, `daily_reports_audit`, `hub_banner_audit`, `odr_translation_events`, `driver_qualification_audit`) | **KEEP** — single-writer audit collections; no reader necessary. Verified as legitimate collections in production. |
| Legacy / dormant collections | ~3 candidates (`doc_id_counters`, `_record_holds_doc_ref_not_base64`, `transportation_*` fragments) | **RETIRE-LATER** — need production data lookup to prove absence of live writers before deletion. Ownership: Backend team. Target: Track 21.2z. |
| **Scanner false positives** (Python attributes / substring matches / helper variable names beginning with `_`) | **~60** (`_unused`, `_source`, `_client`, template placeholders, etc.) | **CLASS-D FALSE POSITIVE** — not Mongo collections. Regex over-matched. |

## Deletion decisions

**None taken.** Per the Zero-Drift mandate and the user's explicit rule ("Do not delete collections blindly"), no collection is dropped in this track. Every candidate flagged for deletion would first require:

1. A grep across production audit logs to prove zero writes in the last 30 days.
2. A backup snapshot with rollback plan.
3. Explicit Ops sign-off.

These steps are Ops-owned and out of scope for this remediation track.

## Class-C status

**TD-21.2-C04 → RECLASSIFIED.**
- ~60 false positives → **Class-D** (scanner artifact).
- ~5 audit collections → **Class-E** (intentional single-write design).
- ~3 potentially dormant → **Class-C RETIRE-LATER** (target Track 21.2z with Ops).

Net: **0 immediate remediation. 3 items queued with owner + target track.**
