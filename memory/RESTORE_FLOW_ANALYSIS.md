# Restore Flow Analysis
## P0 Field Incident · 2026-05-27

> Why "Restore" returns stale work. Doctrine-locked.

---

## 1 · The Current Restore Contract

```js
// useFormDraft.js · simplified
useEffect(() => {
  const draft = await getDraft(actorId, formKey);
  if (draft) setPendingDraft(draft);   // only the latest write
}, [formKey, actorId]);

const restore = () => {
  const d = pendingDraft;
  setPendingDraft(null);
  return d;
};
```

```js
// draftStore.js
export async function getDraft(actorId, formKey) {
  const entry = await get(`masci.draft.${actorId}.${formKey}`);
  if (!entry || !entry.form) return null;
  if (Date.now() - (entry.savedAt || 0) > 14 days) {
    await del(...);   // stale → discard
    return null;
  }
  return entry.form;
}
```

The restore surface offers **one** draft per (actorId, formKey).
There is no draft history, no chooser, no preview, no timestamp shown
to the user, no version vector.

---

## 2 · Why "Restore Loads Stale Work"

Three confirmed mechanisms · any one of them produces the symptom:

### 2.1 — Restore returns the LAST SUCCESSFUL save

If the most recent N save attempts failed silently (see
`AUTOSAVE_FAILURE_ANALYSIS §2.1`), the restored draft is whatever was
written on the last successful save — possibly hours older than the
current work. The operator sees their morning work returned instead of
their afternoon work.

### 2.2 — Restore returns a draft from a PRIOR token

If the user's token rotated between the original save and the
restore attempt:

- The current `actorId` reads draft from key `masci.draft.p.NEW.daily-report-new`.
- The OLD work lives at `masci.draft.p.OLD.daily-report-new` — invisible.
- The "Restore" prompt may not appear at all, or may appear with a
  pre-token-rotation draft that's even older than the morning's work.

### 2.3 — Restore returns the LAST DRAFT BEFORE A SUBMIT

The `commit()` path runs on **successful submit** AND on **queued
submit**. If a queued submit was discarded (some upload error · or
the queue dropped on a clean restart), the draft was already erased
**before** the submit confirmed. On the next mount, `getDraft()`
finds a still-older draft (the one before the discarded one) — looking
ancient to the operator.

---

## 3 · Missing UX Affordances

To even diagnose which draft is being returned, the operator needs
information the UI does not provide:

| Missing affordance | What the operator should see |
|---|---|
| Last-saved timestamp | "Saved 14 minutes ago at 11:42 AM" |
| Last-saved source | "From this device · this morning at 06:32" |
| Multi-draft picker | "3 unsent drafts found · pick one to restore" |
| Cross-token discovery | "We found a draft under a previous login · restore?" |
| Field-diff summary | "12 fields changed since this draft" |
| Confidence chip | "✓ Auto-saved" vs "⚠ Save failed — out of space" |

Today: just a single amber prompt with the word "Restore". The
operator must trust the system blindly. **That trust is broken.**

---

## 4 · The "Restore Then Resume" Hazard

Even if the operator gets the right draft on restore, a subsequent
autosave failure overwrites it within minutes (see `AUTOSAVE_FAILURE
_ANALYSIS §2.6`). The operator restarts the report → restore returns
the same stale draft again → the cycle continues.

This is precisely what the foreman reported: **"operator must restart
report repeatedly"**.

---

## 5 · The "Discard" Footgun

The "Discard" button on the restore prompt calls `discardDraft()`
which deletes the IDB entry for the **current** (actorId, formKey). If
the user has multiple orphaned drafts (token rotation), discarding the
visible one does NOT clean up the invisible orphans. They linger for
14 days.

More dangerously: if the operator hits Discard intending to ignore an
old draft and start fresh, but the autosave loop has been silently
failing all morning, **they have just deleted the only copy of their
morning work**. There is no undo.

---

## 6 · The 14-Day Stale Threshold Is Both Too Long And Too Short

- **Too long** for the active-work case: a 14-day-old draft is almost
  certainly not what the operator wants — but it's offered as
  restore-eligible.
- **Too short** for the dormant-actor case: an operator on vacation
  for 3 weeks loses their pre-vacation drafts forever.

The threshold also has no UI surface — operators can't see it, can't
adjust it, can't know it.

---

## 7 · Required Restore Contract (target)

After remediation, "Restore" should:

1. Surface the **timestamp** of the draft offered.
2. Offer a **chooser** when multiple drafts exist for this formKey
   (including across actorIds for the same logical user).
3. Show a **field-diff preview** ("12 fields differ from the empty form").
4. Refuse to delete a draft that has not been **acknowledged-stale**
   (require a second tap for the discard path).
5. Distinguish **truly idle drafts** from **recently-written drafts
   the user just hasn't seen**.

These changes are in `P0_REMEDIATION_PLAN.md`.

---

## 8 · Sign-off

- **Author:** E1 · P0 incident investigation pass
- **Status:** 🟢 Restore failure modes characterized
- **Next reading:** `ROOT_CAUSE_HYPOTHESIS_MATRIX.md`
