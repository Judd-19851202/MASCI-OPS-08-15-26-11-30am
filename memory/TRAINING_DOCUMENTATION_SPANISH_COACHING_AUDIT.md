# TRAINING / DOCUMENTATION / SPANISH / COACHING AUDIT

**Authority**: FOCP MASTER PROGRAM · Phase 11
**Status**: 🟡 **DEFERRED IN PART — CANNOT BE DONE BY AI ALONE**
**TR IDs**: TR-D001 (training material), TR-D004 (Spanish translation reality match)

This single document covers all four sub-deliverables: training · documentation · Spanish translation · coaching/guidance.

---

## What I CAN audit from inside the repository (source-side)

### Coaching / Guidance / Help-Tip surfaces (source-direct)

Source inventory:

* `/app/frontend/src/components/HelpTip.jsx` — generic tooltip component
* `/app/frontend/src/components/LifecycleGuide.jsx` — per-workflow lifecycle explainer
* `/app/frontend/src/components/guidance/` — one file (`index.jsx`); appears minimal
* `/app/frontend/src/components/PortalContextBanner.jsx` — role-context banner
* `HelpTip` usage in pages: **33 files** import it (verified by grep)

**Source-side coaching audit verdict**:

* Coaching IS scaffolded across the platform (33 page-level integrations of HelpTip).
* Coverage is uneven: some pages have multiple HelpTips per major form field; others have none.
* The `LifecycleGuide` component provides per-workflow explainer modals — present on lifecycle-bearing pages.
* No central "platform tour" / "first-day walkthrough" surface exists in source.

### i18n / Spanish coverage (source-direct)

* `useTranslation` import found in 10+ component files (sampled).
* `t("...")` wrappers used pervasively on user-facing strings (visible in Rank #1 work).
* No standalone `i18n/` or `locales/` directory found at expected paths (`/app/frontend/src/i18n`, `/app/frontend/src/locales`). The translation backend may live in:
  * A library like `i18next` with backend-fetched translations, OR
  * Inline JSON elsewhere, OR
  * Server-rendered via the backend

**This is a source-evidence gap.** I cannot audit Spanish coverage without locating the translation source-of-truth. The operator should designate where translations are stored (file path or repository).

### Documentation / `/app/memory/` audit (source-direct)

* `/app/memory/` contains **1226 markdown files** (per `wc -l`).
* Inventory includes:
  * Doctrine docs (`OPERATIONAL_CONSTRAINT_FOUNDATION.md`, `ACCOUNTABILITY_LIFECYCLE_SPEC.md`, etc.)
  * Audit registers (ITER500_*, ITER501_*)
  * Certification reports (`POST_DEPLOY_CERTIFICATION.md`, etc.)
  * Sprint reports (Rank #1, Sprint 1 closeout, etc.)
* This is **engineering / governance documentation**, not **end-user training material**.
* End-user training material (videos, Skywork videos, knowledge-base entries, training PDFs) is NOT in `/app/`.

## What I CANNOT audit (operator must provide)

### Training videos · Skywork videos · Knowledge-base entries

* Not present in the repository.
* No mention of file paths to training assets in the codebase.
* Operator must designate:
  * Where the training videos live (URL, file store, learning-management-system)
  * Whether they want me to audit transcripts (provide them as text)
  * Whether they want me to validate video-to-workflow matching (requires video-to-text transcription tooling I do not have)

### Spanish translation reality match

* Cannot audit Spanish coverage without the translation source-of-truth path.
* Cannot validate Spanish copy quality without a native-Spanish reviewer.
* Operator must designate:
  * Path to translation files (or grant AI read access to a translation service)
  * A Spanish-language reviewer (human) to certify quality

### Documentation reality match

* Cannot validate whether `/app/memory/*` doctrine docs match actual current workflow behavior end-to-end without persona-driven testing (Phase 12).

---

## Partial findings (what I CAN report)

| Class | Finding | TR ID |
|---|---|---|
| Coaching coverage | Uneven · 33 files use HelpTip · no central new-user tour | (proposed) TR-0010 |
| In-app help center | Absent · users rely on HelpTip + LifecycleGuide piecemeal | (proposed) TR-0011 |
| Spanish source-of-truth location | Unknown to AI · needs operator pointer | TR-D004 |
| Training video inventory | Not in repo · needs operator inventory | TR-D001 |
| Knowledge base | Not in repo · needs operator pointer | TR-D001 sub |
| Skywork video inventory | Not in repo · needs operator inventory | TR-D001 sub |

## Required operator action to lift the DEFERRED status

| Action | Effort |
|---|---|
| Provide path / URL to translation files | 5 min |
| Provide list of training videos + URLs + topics | 30 min |
| Provide list of Skywork videos + URLs | 15 min |
| Provide knowledge-base URL / repo / wiki | 5 min |
| Designate a Spanish-language reviewer (human) | 1 hr (find a person) |
| Authorize tool extension if needed (e.g., video-to-text transcription) | one-time |

After these inputs, the audit can complete within 1–2 days of AI work.

---

End of Phase 11 partial audit · TR-D001 and TR-D004 remain DEFERRED.
