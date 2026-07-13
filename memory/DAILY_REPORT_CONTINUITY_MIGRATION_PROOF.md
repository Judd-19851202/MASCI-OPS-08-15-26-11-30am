# Daily Report Continuity — Migration Proof

- Source file: `frontend/src/lib/resiliency/draftStore.js`
- Verified behavior now:
  1. Enumerate candidate legacy entries.
  2. Ignore invalid / empty envelopes.
  3. Choose newest valid candidate by `savedAt`.
  4. Write target.
  5. Read target back.
  6. Delete legacy source only after successful verified promotion.
  7. Leave legacy source intact on failed promotion/readback.
