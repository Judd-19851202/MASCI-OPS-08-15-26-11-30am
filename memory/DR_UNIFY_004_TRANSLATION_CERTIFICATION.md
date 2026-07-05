# DR-UNIFY-004 · Translation Certification

## Doctrine

- **English is canonical.** Every submitted record is stored in
  English regardless of UI language.
- **Spanish is optional.** When the supervisor toggles ES, the form
  labels, dropdowns, and validation switch to Spanish.
- **On submit**, all text fields are translated back to canonical
  English by `translateUserInput` on the client before send.

## Verified end-to-end

- EN/ES toggle on `/daily/submit` renders both buttons; clicking ES
  switches at least one label into Spanish; clicking EN reverts.
  Verified live via Playwright (CERT-11).
- `translateUserInput` still imported and applied in
  `NewDailyReport.jsx` (unchanged).
- Daily Operational Summary section (DR-CUTOVER-002) accepts
  `language: "en" | "es"` on the accept endpoint; unknown values fall
  back to `"en"` per lock test
  `test_language_flag_accepts_es_and_falls_back_to_en`.
- Canonical English submitted record still writes to
  `daily_reports` unchanged. Spanish-only draft text (if any) may be
  stored in `daily_operational_summary_original_text`.

## Locks referenced

- `test_dr_roi_001f_en_es_lock.py` — 100% green.
- Frontend content test: rendered `/daily/submit` still shows the
  EN/ES toggle buttons and translated labels change on click.

## Edge cases

- If translation service is unavailable, submit falls back to the
  original user input (existing behaviour). No submit is blocked by
  translation failure.
- If tenant AI translation flag is off, the daily report submits
  identically to today.

**Verdict:** Translation subsystem certified.
