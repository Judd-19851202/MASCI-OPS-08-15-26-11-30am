# SAFETY HELP CONTENT REGISTER
## OCEP · Safety Training Completion Program (STCP) · Register 4 of 5

**Date**: 2026-06-03
**Authority**: OMEGA · STCP
**Mode**: READ-ONLY source-direct audit · NO new help content authored
**Evidence rule**: "Help content" means the **content actually rendered to the operator inside the platform**: tips, lifecycle guides, glossary entries, page tooltips, validation messages, sticky-footer hints, and topic library prose. Documentation in `/app/memory/` is governance content and is OUT of scope for in-app help.

---

## 1 · Help-content delivery mechanisms (single inventory)

The platform delivers in-app safety help through five mechanisms. Each is verified source-direct.

| # | Mechanism | Implementation | Used by safety workflows? | Bilingual? |
|---|---|---|:-:|:-:|
| H1 | `HelpTip` registry block | `frontend/src/components/HelpTip.jsx` reads from `backend/guidance/tips.py` via `/api/guidance/tips` | ✅ 14 of 14 | Labels ES yes; bodies almost entirely EN-only (Layer B gap — see `SAFETY_SPANISH_GAP_REGISTER.md` §3) |
| H2 | `LifecycleGuide` component | `frontend/src/components/LifecycleGuide.jsx` — workflow stage explainer | ✅ on incident, QA/QC, site inspection lifecycle panels | Wraps strings via `useT()` — ES via i18n.js |
| H3 | `HelpTip` static body inline | Component accepts caller-supplied content | ✅ scattered usage in `HrEmployees.jsx`, `FleetRepairDrawer.jsx`, `AdminFieldLeadershipUsersPanel.jsx`, `FieldLeadershipPortalChangePassword.jsx` | Yes via `useT()` |
| H4 | Admin Operational Language Glossary | `frontend/src/pages/admin/AdminOperationalLanguage.jsx` (509 LOC, ~50 EN+ES vocabulary entries) | Admin-only read-side; not in flow | Yes — every entry has explicit `en` + `es` |
| H5 | Safety Topic Library prose | `frontend/src/pages/SafetyTopicLibrary.jsx` reads `topics/*.es.js` + `*.en.js` | ✅ Safety Meeting + Incident reference | Yes — 23 trade-specific ES files |

---

## 2 · Per-safety-workflow help content map

For each safety workflow, the rendered help-content sources:

| # | Workflow | H1 tips (count) | H2 lifecycle guide | H3 static helps | H4 glossary entries cited | H5 topic library | Total help-density verdict |
|---|---|:-:|:-:|:-:|:-:|:-:|:-:|
| 1 | JHP + ack | 8 (jha + jha.poster) | ❌ (no lifecycle guide on JHP) | ❌ | "JHP" glossary entry (check) | 23 topic files relevant | 🟡 |
| 2 | Safety Meeting | 22 | ❌ (no lifecycle for meetings) | ❌ | "Safety Meeting" entry | ✅ (topic library is core to meetings) | 🟡 |
| 3 | Incident Report | 18 | ✅ `IncidentLifecyclePanel` | ❌ | "Incident", "OSHA Recordable" entries | indirect | 🟢 |
| 4 | Site Inspection | 17 | ✅ `SiteInspectionLifecyclePanel` | ❌ | "FINDINGS_RAISED" pattern | indirect | 🟢 |
| 5 | QA/QC Inspection | 18 | ✅ `QaqcLifecyclePanel` | ❌ | "DEFICIENCY_RAISED", "Amendment 001" closure | indirect | 🟢 |
| 6 | CAPA | 11 | ❌ (pipeline implicit on detail page) | ❌ | ✅ "CAPA" entry (full 5-section) | indirect | 🟡 |
| 7 | Equipment Pre-op | 13 | ❌ | ❌ | "Pre-shift" entry | n/a | 🟡 |
| 8 | Equipment Issuance | 12 | ❌ | ✅ scattered | "Equipment Issuance" entry | n/a | 🟡 |
| 9 | Equipment Training | 11 | ❌ | ❌ | "Training Record" entry | n/a | 🟡 |
| 10 | Fleet Repair / RTS | 14 | ❌ | ✅ `FleetRepairDrawer.jsx` uses HelpTip inline | "Return to Service" entry | n/a | 🔴 (RTS form_key only 2 tips) |
| 11 | Fire Extinguisher | 8 | ❌ | ❌ | ❌ | n/a | 🟡 |
| 12 | Safety Topic Library | 4 (topic-library form_key) | ❌ | ❌ | n/a | ✅ (this IS the library) | 🟡 |
| 13 | Safety Document | 6 | ❌ | ❌ | ❌ | n/a | 🟡 |
| 14 | Safety Training record | 8 | ❌ | ❌ | ❌ | indirect | 🟡 |

**Density verdict**: 🟢 3 (the three workflows with formal lifecycle guides — Incident, Site, QA/QC) · 🟡 10 · 🔴 1 (Fleet RTS — covered in detail in Coaching Gap Register §4 row 1).

---

## 3 · Where help content is missing entirely (audit by mechanism)

| Workflow | H1 | H2 | H3 | H4 | H5 | Concrete missing |
|---|:-:|:-:|:-:|:-:|:-:|---|
| JHP | ✅ | ❌ | ❌ | partial | indirect | No JHP lifecycle guide; no JHP-specific static helps |
| Safety Meeting | ✅ | ❌ | ❌ | partial | ✅ | No meeting lifecycle guide |
| CAPA | ✅ | ❌ | ❌ | ✅ | n/a | No CAPA pipeline lifecycle guide despite 5-stage pipeline documented in glossary |
| Equipment Pre-op | ✅ | ❌ | ❌ | partial | n/a | No pre-op lifecycle guide |
| Equipment Issuance | ✅ | ❌ | ✅ | partial | n/a | No issuance lifecycle guide |
| Equipment Training | ✅ | ❌ | ❌ | partial | n/a | No training-record lifecycle guide |
| Fleet | ✅ | ❌ | ✅ | partial | n/a | **No RTS attestation help content** beyond 2 tips |
| Fire Extinguisher | ✅ | ❌ | ❌ | ❌ | n/a | No glossary entry; no lifecycle |
| Safety Document | ✅ | ❌ | ❌ | ❌ | n/a | No classification-decision help |
| Safety Training | ✅ | ❌ | ❌ | ❌ | n/a | No expiration-warning help inline |

---

## 4 · Help content QUALITY assessment (spot-sampled)

Where help content exists, sample-verification was performed against actual file content (`tips.py` body strings + topic file prose):

| Sample | Source | Quality | Note |
|---|---|---|---|
| `daily-report` why tip body | `tips.py` lines 41–46 | 🟢 | Direct, operational. |
| `incident.severity` tips | `tips.py` (verified count = 2) | 🟡 | Mistake + why present; depth on severity classification is concise |
| `excavation.es.js` `trenching_shoring.incident_pattern` | `topics/excavation.es.js` line 7 | 🟢 | Decision-grade ("una yarda cúbica pesa ~3,000 lb. Compresión del pecho mata en menos de 5 minutos.") |
| `excavation.es.js` `excavation_spoil_placement.discussion_notes` | line 33 | 🟢 | Sourced 18-inch setback, vibration causality. |
| `AdminOperationalLanguage.jsx` "CAPA" glossary entry | lines 53–59 | 🟢 | 5-section structure (operational/lifecycle/accountability/downstream/etc) |
| `AdminOperationalLanguage.jsx` "Accountability Timeline" entry | lines 33–41 | 🟢 | "Auto-assembled on every read. Never stored as a denormalized table" — doctrine-quality |

**Quality verdict**: 🟢. Where help content exists, it is professionally written and operational. The gap is **coverage breadth**, not **content quality**.

---

## 5 · Cross-cutting help-content findings

### 5.1 · Inconsistent lifecycle-guide coverage
Three workflows (Incident, Site, QA/QC) have first-class `LifecycleGuide` integration. Five workflows (JHP, Meeting, CAPA, Equipment Pre-op, Fleet) have similarly complex state-progression but no inline lifecycle guide. **This is the largest structural help-content gap.**

### 5.2 · The glossary is underused as a help source
`AdminOperationalLanguage.jsx` contains ~50 EN+ES vocabulary entries with 5-section depth each. Currently:
- Visible only to admin users at a dedicated admin route
- NOT linked from any in-flow page (per AdminOperationalLanguage.jsx line 5: "Every LifecycleGuide should eventually link here for term definitions" — operator-intent declared but not yet wired)

Operators looking up a term in-flow have to leave their current workflow. Doctrine intent is unwired. **This is a high-leverage opportunity for content reuse.**

### 5.3 · Help content does NOT eliminate Jaymn dependency for two workflows
The directive specifies "Training must eliminate tribal knowledge and reduce dependency on Jaymn." Two workflows continue to require external coaching even with current help content:

| Workflow | Why help content is insufficient |
|---|---|
| Fleet RTS | 2 tips, no lifecycle guide, no glossary cross-link. Operator must call Jaymn or other senior for RTS attestation guidance. |
| Safety Meeting | No lifecycle guide. New foreman must guess at what makes a meeting record valid for audit (signoff completeness, attendee verification, topic specificity). |

---

## 6 · Retired false findings (help content scope)

| Inherited claim | Source-direct verification | Disposition |
|---|---|---|
| "All safety workflows have HelpTip content" | True for parent form_keys; false at the leaf/decision-form level on some workflows (Fleet RTS, qaqc.signoff, preop.controls — see Coaching Gap Register). | **REFINED**: presence ≠ adequacy. |
| "Glossary is in-flow" | `AdminOperationalLanguage.jsx` is admin-only, not linked from in-flow pages. Wiring is operator-intended (`line 5`) but not implemented. | **CONFIRMED gap**. |
| "LifecycleGuide is on every state-machine workflow" | Implemented on Incident, Site, QA/QC, Payroll Variance. NOT on JHP, Meeting, CAPA, Equipment, Fleet despite multi-state lifecycles. | **CONFIRMED gap**. |

---

## 7 · What this register does NOT do

- Does **not** author new help content.
- Does **not** modify the glossary, lifecycle guides, or topic library.
- Does **not** authorize the implementation of glossary in-flow linking.
- Does **not** rank operator priorities — Section 5 is informational.
- Does **not** claim help-content gaps are blockers; only the operator can decide that.

---

**End of SAFETY HELP CONTENT REGISTER · STCP 4 of 5**
