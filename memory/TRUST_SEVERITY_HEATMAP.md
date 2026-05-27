# Trust Severity Heatmap
## Phase TRUST-1 · 2026-05-27

> Surfaces × categories × severity. One glance tells you where the
> heat is. Numbers in each cell are finding IDs from
> `TRUST_FINDINGS_MATRIX.json`.

---

## 1 · Heat scale

```
█ T5   operational integrity failure   (none open)
▓ T4   data survivability risk         (high blocker · gate Phase V)
▒ T3   operator trust degradation      (medium · should fix soon)
░ T2   workflow confusion              (low · queue surgically)
· T1   mild friction                   (backlog)
  T0   cosmetic                        (housekeeping)
```

---

## 2 · Master heatmap

Rows = audited surfaces. Cols = trust categories.
Cells = finding IDs at their severity.

```
                          DATA  CTX   OPS   MOB   AUTH  VIS   CALM
Daily Report (new)         ▓⁰¹  ─    ─    ▓⁰¹  ─    ▒⁰⁵  ─
Daily Report (autosave)    ▒⁰⁴  ─    ─    ▒⁰⁴  ─    ░¹²  ─
Daily Report (restore)     ░¹⁶  ─    ─    ─    ─    ─    ─
Sibling forms              ▒⁰²  ─    ─    ░⁰⁹  ─    ─    ─
ViewIncident (iter443)     ─    ✓    ─    ─    ─    ─    ─
ViewCAPA / others          ─    ░⁰³  ─    ─    ─    ─    ─
Crew Memory (iter442)      ▓⁰¹  ─    ─    ▓⁰¹  ─    ░⁰⁶  ·⁰⁷
Draft Telemetry            ─    ─    ─    ─    ─    ░¹⁸  ─
Draft Health tile (admin)  ─    ─    ─    ─    ─    ░¹²·¹⁹·²⁰ ─
Legacy redirects           ─    ░⁰⁸  ─    ─    ─    ─    ─
Multi-login flow           ─    ─    ─    ─    ▒¹⁰  ─    ─
Submit / queue path        ▒¹¹  ─    ─    ─    ─    ─    ─
MongoDB _id discipline     ░¹⁵  ─    ─    ─    ░¹⁵  ─    ─
Severity badge load        ─    ─    ─    ─    ─    ─    ·¹⁴
Operator self-triage       ─    ─    ─    ─    ─    ░²¹  ░²²
PRD doctrine sprawl        ─    ─    ─    ─    ─    ⁰²³  ─
```

Legend recap: `▓` T4 · `▒` T3 · `░` T2 · `·` T1 · `T0` plain
number · `✓` covered / no finding · `─` not in scope.

---

## 3 · Heat-by-surface (descending)

| Rank | Surface | Hottest | All finds |
|---|---|---|---|
| 1 | Daily Report (new) — autosave / lifecycle | T4 | TF-001 · TF-004 · TF-005 |
| 2 | Crew Memory (iter442 device memory) | T4 | TF-001 · TF-006 · TF-007 |
| 3 | Sibling forms (NewIncident/Inspection/etc.) | T3 | TF-002 · TF-009 |
| 4 | Submit / offline queue path | T3 | TF-011 |
| 5 | Multi-login token rotation | T3 | TF-010 |
| 6 | Draft Health tile (visibility) | T2 | TF-012 · TF-019 · TF-020 |
| 7 | Daily Report restore / archive | T2 | TF-016 |
| 8 | Operator self-triage workflows | T2 | TF-021 · TF-022 |
| 9 | Shared sibling surfaces (CAPA/Inspection/Meeting) | T2 | TF-003 · TF-017 |
| 10 | Backend MongoDB _id discipline | T2 | TF-015 |
| 11 | Pre-deploy doctrine gate | T2 | TF-018 |
| 12 | Legacy redirect paths | T2 | TF-008 |
| 13 | Severity badge visual load | T1 | TF-014 |
| 14 | PRD.md size | T0 | TF-023 |

---

## 4 · Heat-by-category

| Category | T4 | T3 | T2 | T1 | T0 | Total |
|---|---|---|---|---|---|---|
| DATA | 1 | 3 | 4 | 0 | 0 | 8 |
| CONTEXT | 0 | 0 | 4 | 0 | 0 | 4 |
| OPERATIONAL | 0 | 0 | 0 | 0 | 0 | 0 |
| MOBILE | 1 | 1 | 3 | 0 | 0 | 5 |
| ACCESS | 0 | 1 | 1 | 0 | 0 | 2 |
| VISIBILITY | 0 | 1 | 5 | 3 | 1 | 10 |
| CALMNESS | 0 | 0 | 0 | 2 | 1 | 3 |

**Observation:** VISIBILITY dominates. The platform has good
*data* and *context* hygiene (iter440-443 closed most of those);
the next trust frontier is **making invisible failures visible**.

---

## 5 · Distribution by status

| Status | Count |
|---|---|
| Open · next wave | 10 |
| Open · Phase TRUST-2 candidates | 6 |
| Open · documented only (no remediation planned) | 3 |
| Open · housekeeping | 1 |
| Closed by iter440 / 442 / 443 | (separate ledger) |

---

## 6 · Phase V gate

Phase V (RFI · Constraints · Schedule · P6 · Operational Records)
must NOT begin until:

| Finding | Severity | Why it gates Phase V |
|---|---|---|
| TF-001 | T4 | ITP-purged IDB is a real foreman scenario; net-new RFI surface would inherit the same risk |
| TF-002 | T3 | Sibling forms idempotency — RFI will be the next form to inherit; fix this pattern first |
| TF-004 | T3 | Quota probe / warning UI — RFI will add another large form payload to the same iOS quota budget |
| TF-011 | T3 | Submit-time commit() races — applies to every form, including future RFI |

Closing those four findings unlocks the green light for Phase V.

---

## 7 · Sign-off

- **Author:** E1 · Phase TRUST-1 audit lead
- **Status:** 🟢 Heat-map complete · 23 findings located
- **Next reading:** `TRUST_CRITICAL_SURFACES.md`
