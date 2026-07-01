# TRACK 19.08 · Inspection Engine Specification

Reverse-engineered inspection engine that powers Equipment Pre-Op, DVIR, QA-QC, generic Inspection, and JHA subtype.

---

## 1 · High-level architecture

```
┌───────────────────────────────────────────┐
│           TEMPLATE STORE                  │
│   pm_templates + equipment_master +       │
│   fleet_defect_severity                   │
└──────────────┬────────────────────────────┘
               │  loaded at form open
               ▼
┌───────────────────────────────────────────┐
│         SECTIONS BUILDER                  │
│  CanonicalInspectionSections.jsx          │
│  → array of { title, items[] }            │
└──────────────┬────────────────────────────┘
               │  hydrates React state
               ▼
┌───────────────────────────────────────────┐
│      NEW<FORM>.JSX SHELL                  │
│  Header · Body · Photos · Sign-off        │
│  · Sticky submit                          │
└──────────────┬────────────────────────────┘
               │  submit
               ▼
┌───────────────────────────────────────────┐
│   BACKEND SUBTYPE HANDLER                 │
│   (routes/{equipment,fleet_ops,           │
│    qaqc,inspections}.py)                  │
│  · schema-validate                        │
│  · derive overall_status                  │
│  · fan-out defects[]                      │
│  · fire PDF + email                       │
│  · emit audit events                      │
└──────────────┬────────────────────────────┘
               ▼
    fleet_defects · corrective_actions
    · fleet_status.oos · audit_events
```

---

## 2 · Template contract

Every inspection template is a JSON object:

```json
{
  "id": "template-slug",
  "kind": "equipment_preop | dvir | qaqc | jha | generic",
  "asset_type_match": "excavator | dozer | truck | crane | ...",
  "sections": [
    {
      "title": "Engine / Fluids",
      "items": [
        {"id": "engine.oil", "label": "Oil level & condition", "critical": false, "required": true},
        {"id": "engine.coolant", "label": "Coolant", "critical": false, "required": true}
      ]
    },
    ...
  ]
}
```

`critical=true` items propagate to `fleet_status.status=out_of_service` on FAIL. `required=true` items must have a Pass/Fail/N-A selection (cannot be blank).

Templates live in:
* `pm_templates` (QA-QC + PM inspection templates)
* Hardcoded template lists in `components/CanonicalInspectionSections.jsx` (equipment / DVIR)
* `equipment_master` document may carry an `inspection_template_id` override
* `fleet_defect_severity` maps defect labels → severity → OOS threshold

---

## 3 · PASS / FAIL / N-A logic

Per item — three states via `<YesNo>`-style pill:
* **PASS** — item is compliant.
* **FAIL** — item is non-compliant. Requires `notes` (client-side) and *should* require a photo (industry standard; not currently enforced — see §5).
* **N-A** — item does not apply to this asset today.

Aggregate at section level:
* Section is `pass` if all `required` items are PASS or N-A.
* Section is `fail` if any `required` item is FAIL.
* Section is `partial` if any `required` item has no selection.

Aggregate at form level (`overall_status`):
* `safe_to_operate` (DVIR) / `pass` (Equipment/QA-QC) if all sections pass.
* `unsafe_out_of_service` / `fail` if any section fails.
* `partial` / `pending_review` if any section is partial.

---

## 4 · Conditional visibility

Rare — most sections are always visible. Two exceptions:
* **Weekly Lead / Weekly Emergency** DVIR — extra sections load only when `dvir_type` matches.
* **Excavation-adjacent items** on Equipment Pre-Op — skipped when `equipment_type` is not an excavator/loader/dozer.

There is **no** field-level `visible_when` DSL — all conditional visibility is hardcoded.

---

## 5 · Photo requirement at defect level (industry gap)

Currently **not enforced**. Operators can mark FAIL and submit without a photo. Compare to Samsara / MaintainX where submit is disabled until photo attached. Preserved as a P1 opportunity in `16_EXECUTIVE_RECOMMENDATIONS.md`.

---

## 6 · Autosave / resume / offline

* Client-side autosave via `useFormDraft` (Track 19.04 actor-scoped).
* IndexedDB draft is committed on 2xx submit; discarded on Discard.
* Offline: `enqueueUpload` retries × 5.
* Resume: on remount, the draft-restore banner appears if a draft exists for `formKey + savedByActor`.

---

## 7 · Progress calculation

Progress = `(sum of selected items) / (sum of required items)` — Daily Report exposes this as `0/9 · Needs work` (Track 19.06). Other forms do not surface aggregated progress.

---

## 8 · Submission flow

```
Client (submit btn)
  ├─ validate() — client-side
  ├─ mintIdempotencyKey() → persist
  ├─ language check → translateUserInput if ES
  ├─ enqueueUpload({method:POST, url, body, idempotencyKey})
  │   ├─ 2xx → commit draft, clear key, saveCrewSetup, toast success
  │   ├─ 4xx → toast failure, keep draft, no idempotency clear
  │   └─ queued (offline) → toast "Saved · will upload when reconnected"
  └─ trigger downstream fanout (see §2 above)
```

---

## 9 · The `inspections` collection is polymorphic

Same physical collection stores:
* QA-QC (`inspection_type=qaqc`)
* Generic (`inspection_type=generic`)
* JHA (`inspection_type=jha` — some records; JHA also has dedicated `jhas` collection)
* Legacy imports (`inspection_type=legacy`)

Read layer filters by `inspection_type`. Powerful but fragile — see `11_DUPLICATE_LOGIC_REPORT.md`.

---

## 10 · Where the "feels like multiple inspections" comes from

Two forces stacked:
1. **Section count grew with each machine type** — every new machine type added new template sections to `CanonicalInspectionSections.jsx`. No UX consolidation.
2. **Coaching-panel stacking** — three helper systems render simultaneously on Equipment Pre-Op (see §11).

Both preserved in `15_ROOT_CAUSE_ANALYSIS.md`. Neither is broken; both are drift.
