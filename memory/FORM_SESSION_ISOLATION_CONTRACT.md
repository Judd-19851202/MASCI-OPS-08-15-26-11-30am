# Form Session Isolation Contract (Platform-wide)

## Purpose

Every long-form editor on the MASCI Operations Platform must obey a
single Form Session Contract so a shared PC, shared iPad, or
individual workstation NEVER surfaces one operator's work to another
operator by accident. The contract preserves productivity features
(autosave, active-draft recovery, Smart Prefill) while eliminating
cross-actor, cross-device, and cross-session residue.

## Identities

| Identity | Purpose | Lifetime | Rotates on |
| --- | --- | --- | --- |
| **Device ID** (`getDeviceId()`) | Device recognition, banner targeting, operational analytics | Persistent — reset only by hard local-storage clear | never (except explicit reset) |
| **Auth Actor Fingerprint** (`getAuthActorFingerprint()`) | Discriminate signed-in portal actors on the same device | For the life of the portal token | login / logout / passkey re-auth |
| **Draft ID (IDB key)** | Locate an in-progress form draft on this device | Until submitted or discarded | never (device-scoped for token-rotation safety) |
| **Report ID / doc_id** | Identify a completed record | Permanent | never |
| **Form Session** | One blank instance of a form | The mount lifetime | on remount |

## Rules

1. **Device ID identifies the device only.** It never scopes form content by itself.
2. **Draft IDs are stored under the device ID (for token-rotation safety) BUT every draft entry carries a `savedByActor` fingerprint.**
3. **A draft is only offered for restore when `entry.savedByActor === currentAuthFingerprint`.** Cross-actor drafts are silently hidden — they still exist on disk (in case the original actor returns) but are invisible to a different actor on the same device.
4. **Legacy drafts (no `savedByActor`) are offered with `isCrossToken=true`.** The UI must render a calm "unknown-author, confirm before applying" affordance. This is a one-shot compat window; every new write since 19.04 stamps the fingerprint.
5. **New form session → blank data.** No implicit hydration from prior submitted records, prior device state, prior localStorage residue, prior React state, or another actor's draft.
6. **Explicit resume is required.** Autosave restoration is offered as a prompt (`DraftRestorePrompt`). Silent auto-hydration is forbidden.
7. **Smart Prefill is opt-in.** Prior-report crew + equipment (`/api/jobs/{pn}/recent-context`) is presented as an OFFER CHIP that requires operator Apply. Silent auto-apply is forbidden.
8. **Successful submit clears the draft** (via `useFormDraft.commit()`).
9. **Successful submit clears the idempotency key.**
10. **Discard soft-deletes to a 24 h archive** so a mis-tap can be recovered.
11. **No backend endpoint may return "latest draft" globally.** Drafts live client-side, scoped to the actor + device pair.
12. **Submitted records must never hydrate a new draft.** Downstream views read from the submitted record; the new-form editor starts blank.
13. **Offline queue items are per-idempotency-key.** They never hydrate an unrelated new form.
14. **Public/anonymous form flow** (no portal token): `getAuthActorFingerprint()` returns `"anon"`. Two anonymous foremen on the same public form on the same device DO see each other's drafts via the restore prompt — this is the calm compat behavior for kiosk/public field flows. The prompt makes the offer explicit; there is no silent hydration.
15. **Historical Daily Reports on the reporting surface are immutable.** No mutation via HR changes, no re-linkage of employee identities. Names captured at submit remain the historical record (Track 19.03 doctrine).

## Applies to (form types)

* Daily Reports (`daily-report-new`)
* Safety Meetings (`meeting-new`)
* Incident Reports (`incident-new`)
* Equipment / Fleet Inspections (`inspection-new`, `dvir-new`, `fleet-dvir-new`)
* JHP / JHA (`jha-new`)
* Pre-Ops (uses same `useFormDraft` pattern when introduced)
* HR Payroll Variance / DLS Debrief / Recovery Action — inherit via `useFormDraft`

All the above already use `useFormDraft(formKey, data, actorId)`. The Track 19.04 upgrade to `useFormDraft` propagates the actor gate to every consumer automatically.

## Attachments

Photos and documents (PDF, XLSX, XLS, CSV) share one unified attachment envelope:

```
{ attachment_ref, mime_type, extension, category, filename, file_size, uploaded_at }
```

* Storage: SAME R2 bucket used by photos.
* Photo prefix: `photos/YYYY/MM/<source>/<uuid>.<ext>`.
* Document prefix: `documents/YYYY/MM/<source>/<uuid>.<ext>`.
* Filename sanitised server-side.
* Extension allow-list: `pdf`, `xls`, `xlsx`, `csv`, plus existing photo types.
* Dangerous extensions blocked: `exe, bat, cmd, com, cpl, dll, jar, js, jse, msi, ps1, psm1, sh, vbe, vbs, wsf, wsh, scr, app, action, workflow, hta`.
* Size cap: 25 MiB per attachment.
* Attachments are linked to a specific report at submit time — no cross-report attachment leakage possible.

## Violations (regression tests will catch)

* Silent auto-apply from `/api/jobs/{pn}/recent-context` — banned.
* Draft written without `savedByActor` field — banned (guarded by `saveDraft` signature).
* Draft surfaced when `entry.savedByActor` mismatches current actor — banned (guarded by `useFormDraft`).
* Backend endpoint returning any operator's draft to a different actor — banned (none exist).
* Attachment upload of dangerous extension — 400 with clear message.
* Attachment upload > 25 MiB — 400 with clear size hint.
