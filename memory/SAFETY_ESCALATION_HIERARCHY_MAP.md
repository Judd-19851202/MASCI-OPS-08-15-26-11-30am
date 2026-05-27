# Safety Escalation Hierarchy Map

*Phase IV-BETA.4C · iter437 · 2026-02-27*
*Status: 🟢 HIERARCHY MAPPED · IMPLEMENTATION NOT STARTED*

> **Verification legend:** 🟢 VERIFIED · 🟡 ASSUMED · ⚪ UNTESTED

---

## I. Three-tier escalation contract (🟢 inherits from `COMMUNICATION_UNIFICATION_DOCTRINE.md §A.III`)

| Tier | When | Visual signal | Email subject prefix |
|---|---|---|---|
| **Routine** | Documentation, training, audits, ordinary inspections | Neutral chrome · doctrine-coloured stripe · no badge | `[MASCI · {TAG}] …` |
| **Action required** | Specific operator owes specific action by specific time | Amber stripe + amber badge on the row; no panel-wide colour | (TAG only — no prefix change) |
| **Severe / immediate** | Severe injury · OSHA-reportable · trench wall failure · live escalation · equipment fail with potential fatality risk | `🚨 SEVERE INCIDENT` / `⚠ EQUIPMENT FAIL` prefixed subjects · red severity pill · banner ONLY on the affected record | `🚨 SEVERE INCIDENT · …` / `⚠ EQUIPMENT FAIL · …` |

## II. Today's escalation surfaces (🟢 audited)

| Surface | Current escalation pattern | Verdict |
|---|---|---|
| `SafetyHub.jsx` | Mixed tile stripes (red/amber/cyan/etc.) communicate domain, not urgency. Eye reads "red tile" as "danger" even when the tile is just "Documents Library". | 🔴 false urgency |
| `SafetyIncidents.jsx` | `SEV_PILL` table column — colour bound to row's `severity` field. Correct. | 🟢 best-in-class |
| `SafetyCorrectiveActions.jsx` | Severity column present; needs verification against `SEV_PILL` discipline. | 🟡 needs audit |
| `SafetyAudits.jsx` | Pass/fail indicators colour-coded; doctrine compliance not yet verified. | 🟡 needs audit |
| Severe incident email | Already uses `🚨 SEVERE INCIDENT` prefix via PM auto-email gold standard (iter238). | 🟢 |

## III. Operationally critical surfaces — TRUE escalation (preserve)

These surfaces represent **real operational danger** and their
visual escalation must remain unmistakable:

1. **Active severe incident** — open incident with severity ∈ {severe,
   fatality, OSHA-reportable}. Surface today: `SafetyIncidents.jsx`
   table row + email subject `🚨 SEVERE INCIDENT · …`.
2. **Equipment failure with safety exposure** — pre-op/post-op failure
   on a unit with no replacement available. Surface: PM portal
   + Shop email. Prefix `⚠ EQUIPMENT FAIL · …`.
3. **Compliance blocker** — expired OSHA / TWIC / CDL on a worker
   currently dispatched to a job. Surface: `SafetyDocuments.jsx`
   expirations row.
4. **Trench / excavation violation** — JHA-tagged trench-box
   non-compliance. Surface: `JhaPlansAdmin` review interface.

## IV. False urgency — drop or demote (⚪ UNTESTED · plan only)

| Today | Why it's false urgency | Recommended demote |
|---|---|---|
| Red tile stripe on "Documents Library" | The library is reference; not urgent. | Slate or violet stripe. |
| Red tile stripe on "Training Certifications" | Reference list. | Violet stripe. |
| Red tile stripe on "Safety Audits" landing page | Most audits are routine. | Slate stripe. |
| Red `bg-red-100` empty-state panel | An empty list is not an emergency. | Slate-100 + leading info icon. |
| Per-tile red CTA button | Decorative. | Single neutral slate-800 CTA across all tiles. |

## V. Escalation ownership routing (🟢)

| Trigger | First responder | Then | Then |
|---|---|---|---|
| Severe incident | Site Safety officer (via Safety portal) | PM (alerted) | HR (24-hour reporting window) |
| Equipment fail | Shop Manager | PM (project context) | (no HR escalation unless injury) |
| OSHA expiration on dispatched worker | HR (Compliance & Records) | Dispatch (today's roster) | Field Leadership (foreman on-site) |
| Trench violation | Site Safety officer | PM | Admin if recurring across jobs |

## VI. Visual hierarchy plan for Safety V2 (⚪ UNTESTED · plan only)

When the implementation pass is authorised:

1. **Domain stripes** (analogous to HR's 5-domain palette):
   - `border-l-cyan-700` — Documents & Training (Safety brand)
   - `border-l-violet-600` — Compliance & Records
   - `border-l-red-700` — Incidents & Investigations (the ONE red domain)
   - `border-l-slate-600` — Audits & Guidance
2. **Severity pill discipline** stays exactly as `SafetyIncidents.jsx`
   has it today — colour bound to data, not theme.
3. **Severe-tier banner** (page-level, not chrome-level) only on
   the open severe-incident record itself; never on the Hub.
4. **CTA neutralisation** to slate-800 across the Hub, mirroring
   HR P1B trim and Admin/PM V2.

## VII. Doctrine reaffirmed

- ✅ True urgency preserved (severity pills + severe-tier prefixes)
- ✅ False urgency identified for demotion (decorative red, panel
  empty-states, hub-tile colour explosion)
- ✅ NO Safety workflow rewrites · NO incident logic changes
- ✅ Preview only · no production touches
