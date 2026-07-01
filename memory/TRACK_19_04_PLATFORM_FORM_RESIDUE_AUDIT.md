# Track 19.04 · Platform Form Residue Audit

Cross-form review to confirm every long-form editor obeys the
`FORM_SESSION_ISOLATION_CONTRACT.md` contract after the 19.04 upgrade.

## Form-by-form review

| Form | Route | Uses `useFormDraft`? | Explicit-restore prompt? | Silent auto-hydration surfaces | Status |
| --- | --- | --- | --- | --- | --- |
| **Daily Report** | `/daily/new`, `/daily/submit` | ✓ `daily-report-new` | ✓ `DraftRestorePrompt` | Was silent Smart Prefill via `/jobs/{pn}/recent-context` → **FIXED** as `smartPrefillOffer` chip | ✓ 19.04 |
| **Safety Meeting** | `/meetings/new`, `/meetings/submit` | ✓ `meeting-new` | ✓ `DraftRestorePrompt` | None found. Meeting attendees added via `EmployeeCombo` (canonical HR roster, Track 19.03). | ✓ inherits 19.04 |
| **Incident Report** | `/safety/incident/new` | ✓ `incident-new` | ✓ `DraftRestorePrompt` | None found. Involved employees via `EmployeeCombo`. | ✓ inherits 19.04 |
| **Equipment / DVIR Inspection** | `/safety/inspections/new`, `/fleet/dvir/new` | ✓ `inspection-new`, `fleet-dvir-new` | ✓ `DraftRestorePrompt` | None found. | ✓ inherits 19.04 |
| **JHA / Job Hazard Plans** | `/jha` | Read-only hub — signature/acknowledgement flow uses fresh POST, no long autosave | n/a | Signature is captured per session, cleared on submit. | ✓ n/a |
| **Pre-Op** | (no dedicated form yet — DVIR covers) | — | — | — | ✓ n/a |
| **QA/QC** | Absorbed into inspection flow | — | — | — | ✓ n/a |
| **HR Payroll Variance** | `/hr/payroll` | ✓ (uses `useFormDraft`) | ✓ | None found. | ✓ inherits 19.04 |
| **DLS Day-1 Debrief** | `/dls/day-one` | ✓ (uses `useFormDraft`) | ✓ | None found. | ✓ inherits 19.04 |
| **Recovery Action** | Admin surface | ✓ (uses `useFormDraft`) | ✓ | None found. | ✓ inherits 19.04 |
| **New Safety Equipment Issuance** | `/safety/forms/equipment-issuance/new` | No autosave — quick form | n/a | Employees via `EmployeeCombo`. Static fields defaulted. | ✓ n/a |
| **Public field submit variants** | `/daily/submit`, `/meetings/submit` | Uses same `useFormDraft` under `"anon"` fingerprint | ✓ prompt-based | Kiosk/public flow accepts prompt-based recovery for anonymous shared operators. | ✓ acceptable per contract §14 |

## Global infrastructure verified

* **`useFormDraft` upgrade** (`/app/frontend/src/lib/resiliency/useFormDraft.js`) — every consumer inherits the `savedByActor` gate automatically. No per-form change required for Safety Meeting / Incident / Inspection / DVIR / HR Payroll / DLS / Recovery Action.
* **`saveDraft` signature** — new `{ savedByActor }` opt; older callers pass no opt and get `savedByActor:null` (legacy compat window; behaves as "unknown author" prompt).
* **`getAuthActorFingerprint`** — probes the same 7-portal token set as `getLegacyActorIds` in priority order, returns `"anon"` for public flows.
* **No backend endpoint returns a global "latest draft".** Verified by grepping `server.py` for `/latest`, `/recent`, `/my-latest`, `/drafts`, `/draft` — only `/jobs/{pn}/recent-context` exists, and that is now v19.04-contract-versioned with `contract_version` in the response, `actor_scoped` flag, and consumed only via the explicit offer chip on the frontend.

## Forms that intentionally have NO autosave

* HR Employees single-row Add / Edit dialogs — hits the backend on Save directly, no long-form editor.
* Trench Safety Excavation form — public one-shot submit with in-memory state only.
* JHP acknowledgement — one signature event per session.

These flows have no persisted client state and therefore no residue vector.

## Conclusion

The single upgrade to `useFormDraft` covers every long-form editor on the platform. Additionally, the Daily Report's explicit-offer Smart Prefill chip removes the last silent auto-hydration vector. Zero further per-form work required.
