# Track 19.04 · Daily Report Residue Reproduction

## Field Report (2026-06-29)

> "A user opens Daily Reports on their own PC/laptop/office computer
> and sees residue from another user's report or another device/session."
>
> — Operator directive, Track 19.04

## Reproduction (verified in preview 2026-06-29)

### Setup

* Preview URL: `https://backup-forensics.preview.emergentagent.com`
* Preview DB: `masci_safety_preview`
* Two Chromium profiles simulating two office workstations.
* Actor A: Admin `jaymn.judd@mascigc.com`, Project `T5686`.
* Actor B: Foreman FSI submit (public) or Admin `jaymn.judd@mascigc.com` on a fresh device.

### Steps

1. Actor A opens `/daily/new` and picks Job `T5686`.
2. Actor A adds crew (`Alice`, `Bob`, `Charlie`) and equipment (`CAT 320`, `Roller`).
3. Actor A submits the report → visible in `/daily-reports`.
4. Later that day: Actor B opens `/daily/new` on a **different** device or browser profile.
5. Actor B picks the **same** Job `T5686`.
6. Actor B sees `Alice`, `Bob`, `Charlie` and both pieces of equipment silently populated in the crew + equipment sections — data Actor B never entered.

### Root Cause

Line-level:

```
backend/server.py  /api/jobs/{project_number}/recent-context   (silent, project-scoped baseline)
frontend/src/pages/NewDailyReport.jsx :: applyJob(job) → silently applies:
    setData(p => { next.masci_crews = priorCrews.map(...); next.equipment = priorEquipment.map(...); })
```

Actor B never opts in. The moment the job is picked, the previous DR's crew and equipment are copied into Actor B's form as if Actor B had typed them.

### Impact classification

| Vector | Cross-user | Cross-device | Cross-browser | Silent |
| --- | --- | --- | --- | --- |
| Silent Smart Prefill | ✓ | ✓ | ✓ | ✓ (P0) |

This is the primary P0. Every other candidate residue vector was audited (`TRACK_19_04_FORM_SESSION_AUTOSAVE_AUDIT.md`) and found either non-existent (`/api/daily-reports/latest` never existed) or already isolated (`crewMemory.js` is device-local + operator-confirmed).

### Additional secondary vector (shared office PC)

Even on the correctly-isolated Smart Prefill path, a shared office PC scenario existed where Admin A saved an autosave draft, then Foreman B signed in on the same PC and was OFFERED Admin A's draft via the "Resume Draft" prompt. This was a lower-severity vector (still required Foreman B to click Restore), but per operator directive was fixed by stamping `savedByActor` on every IDB draft write and gating restore on fingerprint match.

## Fix Verification

1. **Smart Prefill offer chip**: after `applyJob`, `smartPrefillOffer` state is set. NO write to `data.masci_crews` / `data.equipment` occurs until the operator clicks the yellow **Apply prefill** button. Dismiss cleanly discards.
2. **Draft actor gate**: `useFormDraft` refuses to surface `pendingDraft` when the draft's `savedByActor` fingerprint does not match `getAuthActorFingerprint()`. Cross-actor drafts are invisible and emit `draft.restore.blocked_cross_actor` telemetry.
3. **`/api/jobs/{pn}/recent-context` v19.04 contract**: response now includes `contract_version="19.04"`, `actor_scoped: bool`, and `source: "daily_reports.most-recent (project-scoped)"` so downstream renderers can label the offer accurately. Actor-scoped variant preferred when `foreman` / `superintendent` query params are supplied.

## Regression Guard

* `test_track_19_04_form_session_isolation.py` :: `test_smart_prefill_is_explicit_offer_not_auto_apply`
* `test_track_19_04_form_session_isolation.py` :: `test_cross_actor_draft_not_offered`
* `testing_agent_v3_fork` live UI verification: same-project new form for a different actor shows the offer chip, does NOT silently populate the crew rows.
