# Safe Self-Healing Foundation

## What D7/D8 completes now
- Bounded runtime distress handling lives in `backend/lib/runtime_reliability.py`.
- Resource threshold crossings can now trigger:
  - incident capture,
  - bounded cleanup of `/tmp`, runtime incident files, and stale test reports,
  - admin-visible `safe_self_healing` state through `/api/admin-strict/diag/runtime-health`.
- The canonical machine-readable performance baseline is exposed through `/api/admin-strict/diag/performance-baseline`.

## What is explicitly forbidden
- No production mutation.
- No Atlas index mutation.
- No unbounded workspace deletion.
- No hidden auto-restart loop that erases forensic evidence.

## Why this is a D7/D8 foundation rather than a D9 deferral
- The platform already has a governed distress authority, release gate, and incident spine.
- D7/D8 extends those existing authorities with bounded cleanup and canonical baseline exposure.
- D9 can add richer orchestration, but it should build on this governed evidence-first foundation rather than reinvent it.