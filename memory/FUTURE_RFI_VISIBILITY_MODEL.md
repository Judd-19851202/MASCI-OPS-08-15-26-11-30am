# FUTURE RFI VISIBILITY MODEL

_Phase ODR-Governance Extension · Future-RFI Per-FLL Contract · 2026-05-29_

This document locks the per-FLL visibility model for the future
RFI system **before** RFI implementation begins. The future
implementation must respect this contract; deviation requires a
doctrine revision (V20).

**Architecture only. No implementation.**

---

## 1 · RFI lifecycle (canonical)

```
   draft   →   submitted   →   in_review   →   responded
       ↓           ↓              ↓                ↓
   (rare)    (the act that      (PM / designer  (linked back
              starts the         / owner has     to ODR / extra-
              question)          it)             work / cost)
```

Authoring of an RFI typically begins **from an ODR Extra Work
event** (Section 8) where the foreman flagged a question. The RFI
then lifts into the PM-owned lifecycle.

---

## 2 · Per-FLL visibility · RFI

| RFI capability | FLL-1 Foreman | FLL-2 GF | FLL-3 Super | FLL-4 Sr Super | FLL-5 PM | FLL-6 Ops Leader |
|---|---|---|---|---|---|---|
| See RFIs were *created* | NONE | LIMITED (related to own work) | FULL (project) | LIMITED (regional · cross-project conflicts) | FULL | SUMMARY (count / age / cycle-time trends) |
| Author / create an RFI | NONE (foreman flags via Extra Work → Super lifts into RFI) | LIMITED (rare · usually escalates to Super) | FULL | LIMITED (regional escalation) | FULL | NONE |
| See RFI body / attachments | NONE | LIMITED | FULL | LIMITED | FULL | NONE |
| Review RFI status (`in_review` queue) | NONE | LIMITED (own work) | FULL | LIMITED | FULL | SUMMARY |
| Respond to an RFI | NONE | NONE | LIMITED (escalates to PM) | NONE | FULL (owns response) | NONE |
| See RFI response | NONE | LIMITED (impact on own work) | FULL | LIMITED (regional impact) | FULL | SUMMARY |
| Link RFI to constraint | LIMITED (via own Extra Work seed) | LIMITED | FULL | LIMITED | FULL | NONE |
| See RFI cost impact | NONE | NONE | LIMITED (operational impact only) | NONE | FULL | SUMMARY |
| See RFI schedule impact | LIMITED (today/tomorrow only) | LIMITED (3-day) | FULL | FULL (regional) | FULL | SUMMARY |
| See RFI cycle time (age) | LIMITED (own seeded) | LIMITED (own crews') | FULL | FULL | FULL | SUMMARY |

---

## 3 · Three RFI doctrine rules

| # | Rule |
|---|---|
| RFI-V1 | **Foreman does not see RFIs by default.** The foreman seeds the question via an ODR Extra Work entry; the RFI lifecycle is owned upstream (Super lifts, PM responds). |
| RFI-V2 | **PM owns response · Super manages project-side lifecycle · Sr Super sees regional impact.** Each tier has a clear lane; no role's surfaces show RFI affordances outside its lane. |
| RFI-V3 | **Cost impact is FLL-5 only.** Even Super does not see RFI cost figures by default — Super sees the *operational* impact (schedule shift · work-area block); cost is reserved for FLL-5. |

---

## 4 · Cross-system anchors

- **ODR → RFI link** — every ODR Extra Work entry carries an
  optional `rfi_link_id`. When populated, the Super sees the linked
  RFI from the ODR Inbox surface; the foreman sees only "RFI in
  progress" status — never the body.
- **Constraint → RFI link** — recurring constraints may seed an
  RFI; visibility follows RFI rules above.
- **Schedule → RFI** — RFI schedule impacts cross-reference into
  the schedule system (see `FUTURE_SCHEDULE_VISIBILITY_MODEL.md`).

---

## 5 · Public-link surface

Public link (foreman's anonymous data-collection surface) **never**
exposes RFI data. Authority is FLL-1 NONE; the public link is
even more restricted (no auth) and therefore inherits NONE.

---

## 6 · Doctrine anchors

| Doctrine | Anchor |
|---|---|
| V13 RFI tracks the work | § 2 matrix · author + project team see, FLL-3 manages, FLL-5 owns response |
| V5 no cross-role leakage | § 4 ODR → RFI rule: foreman sees status, never body |
| V6 PM ≠ MORE | § 3 RFI-V3 cost impact is FLL-5-only |

_End of Future RFI Visibility Model._
