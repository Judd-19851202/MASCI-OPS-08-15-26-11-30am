# SAFETY SPANISH GAP REGISTER
## OCEP · Safety Training Completion Program (STCP) · Register 3 of 5

**Date**: 2026-06-03
**Authority**: OMEGA · STCP
**Mode**: READ-ONLY source-direct audit · NO translation work · NO engineering
**Evidence rule**: Spanish coverage of safety surfaces is measured separately at two layers — **UI strings (`i18n.js`)** and **coaching tip bodies (`tips.py`)**. Conflating the two produces misleading aggregate numbers (this is precisely how the inherited 52% figure was misleading for safety scope).

---

## 1 · The two-layer Spanish model on the platform

Safety surfaces deliver Spanish to the operator via two independent layers:

| Layer | Source file | Purpose | Coverage mechanism |
|---|---|---|---|
| **Layer A — UI string layer** | `frontend/src/lib/i18n.js` (4902 LOC · ~3218 ES entries) | Page titles, labels, buttons, validation strings, toast messages, navigation | `useT()` hook wraps every string; missing key falls back to EN |
| **Layer B — Coaching tip body layer** | `backend/guidance/tips.py` (6218 LOC · 157 form_keys · ~412 total tips) | Inline `HelpTip` blocks rendering the `why / who / when / mistake / example / next / escalate` content | Per-tip optional `title_es` and `body_es` fields; missing → renders EN body |
| **Layer C (auxiliary) — Safety topic library content** | `frontend/src/lib/topics/*.es.js` (23 trade-specific files · 1579 LOC) | Safety Meeting topic content (`incident_pattern`, `hazards_reviewed`, `discussion_notes`, `action_items`, `references_cited`) | Static ES dictionaries imported per trade |

---

## 2 · Layer A · UI string Spanish coverage (safety scope)

| Safety surface | Spanish in `i18n.js`? | Evidence |
|---|:-:|---|
| Daily Report form labels & sticky footer | 🟢 | iter437/438 section (lines 85–151) |
| JHP / `/jha` public hub | 🟢 | JHP section (multiple iter# blocks) |
| Admin JHP Acknowledgements | 🟢 | FOCP R2 section (post-2026-05 iter blocks) |
| Incident Report | 🟢 | Incident section + iter402+ blocks |
| Site Inspection | 🟢 | Inspection section |
| QA/QC Inspection | 🟢 | QA/QC section + Amendment 001 strings |
| CAPA / Corrective Action | 🟢 | Corrective section |
| Equipment (pre-op, issuance, training) | 🟢 | Equipment section |
| Fleet (DVIR, repair, RTS, visibility) | 🟢 | Fleet section |
| Fire Extinguisher | 🟢 | iter293 fire-extinguisher block |
| Safety Topic Library | 🟢 | iter202/203/204 Operational Guidance Center |
| Safety Document upload | 🟢 | Safety document section |
| Safety Training records | 🟢 | iter200 LeadershipLogin + training_es.js (1093 LOC) |

**Layer A verdict**: 🟢 GREEN. Spanish UI coverage of safety workflows is broad and well-anchored in i18n.js. NO RED at this layer.

---

## 3 · Layer B · Coaching tip body Spanish coverage (safety scope)

This is the source-direct gap that was previously conflated with Layer A.

### 3.1 · Aggregate count

| Metric | Value |
|---|---:|
| Total safety-relevant tips in `tips.py` | ~137 |
| Tips with `body_es` populated | **≈ 1** (sole instance is on `jha.poster`) |
| Tips with `title_es` populated | ≈ 0 |
| Coverage % | **< 1%** |

### 3.2 · Per safety form_key body_es coverage

For every safety form_key in `tips.py`, every tip was inspected for a `body_es` field. The result is uniform:

| Workflow group | Form_keys audited | Tips with body_es | Verdict |
|---|---:|---:|:-:|
| JHP (jha, jha.poster) | 8 tips | 1 (jha.poster only) | 🔴 |
| Safety Meeting (6 form_keys) | 22 tips | 0 | 🔴 |
| Incident Report (6 form_keys) | 18 tips | 0 | 🔴 |
| Site Inspection (5 form_keys) | 17 tips | 0 | 🔴 |
| QA/QC Inspection (6 form_keys) | 18 tips | 0 | 🔴 |
| CAPA / Corrective (3 form_keys) | 11 tips | 0 | 🔴 |
| Equipment Pre-op (preop + 4 sub) | 13 tips | 0 | 🔴 |
| Equipment Issuance (parent + 4 sub) | 12 tips | 0 | 🔴 |
| Equipment Training (parent + 3 sub) | 11 tips | 0 | 🔴 |
| Fleet (DVIR/Repair/RTS/Visibility + weeklys) | 14 tips | 0 | 🔴 |
| Fire Extinguisher (3 form_keys) | 8 tips | 0 | 🔴 |
| Safety Topic Library | 4 tips | 0 | 🔴 |
| Safety Document (3 form_keys) | 6 tips | 0 | 🔴 |
| Safety Training (3 form_keys) | 8 tips | 0 | 🔴 |

**Layer B verdict**: 🔴 RED. Across 14 safety workflows, the coaching surface delivers virtually zero Spanish body text.

### 3.3 · Runtime impact

The `HelpTip.jsx` component (line 22–23 docstring) renders ES labels (`label_es: "Por qué importa"`, `"Errores comunes"`, etc., hardcoded in the component) but falls back to EN tip `body` when `body_es` is absent. A Spanish operator therefore sees the **label** in Spanish but the **content** in English. This is functional (no crash, no blank) but **defeats the coaching purpose** for Spanish-primary operators.

This is exactly the failure mode SOCP §P-ES-2 anticipated:

> "The platform is English-canonical by doctrine. Submitted prose round-trips to English. The operational risk is therefore in the Spanish READ surface, not the Spanish WRITE surface."

The Spanish READ surface of the **coaching layer** is empty.

---

## 4 · Layer C · Safety topic library Spanish content (auxiliary)

This is the bright spot. The 23 trade-specific topic dictionaries (`frontend/src/lib/topics/*.es.js`) contain professionally-authored Spanish safety content:

| Layer C metric | Value | Verdict |
|---|---|:-:|
| Trade-specific ES topic dictionaries | 23 files | 🟢 |
| Total ES content LOC | 1579 | 🟢 |
| Sampled-verified for quality (decision-grade prose) | `excavation.es.js` end-to-end inspected; SOCP Phase 3 §2.3 + §7.2 found exemplary safety prose | 🟢 |
| Field-reviewer walk-through completed | ❌ (SOCP Phase 4 packet hands this to the operator) | n/a |

**Layer C verdict**: 🟢 GREEN content quality; field review pending.

---

## 5 · Composite Spanish readiness per safety workflow

For each workflow, the composite Spanish verdict is the WORST of Layer A and Layer B (Layer C is auxiliary):

| # | Workflow | Layer A (UI) | Layer B (coaching) | Layer C (topics) | Composite |
|---|---|:-:|:-:|:-:|:-:|
| 1 | JHP + ack | 🟢 | 🟡 (1 of 8 tips body_es) | n/a | 🟡 |
| 2 | Safety Meeting | 🟢 | 🔴 | 🟢 | 🔴 |
| 3 | Incident Report | 🟢 | 🔴 | n/a | 🔴 |
| 4 | Site Inspection | 🟢 | 🔴 | n/a | 🔴 |
| 5 | QA/QC Inspection | 🟢 | 🔴 | n/a | 🔴 |
| 6 | CAPA | 🟢 | 🔴 | n/a | 🔴 |
| 7 | Equipment Pre-op | 🟢 | 🔴 | n/a | 🔴 |
| 8 | Equipment Issuance | 🟢 | 🔴 | n/a | 🔴 |
| 9 | Equipment Training | 🟢 | 🔴 | n/a | 🔴 |
| 10 | Fleet Repair / RTS | 🟢 | 🔴 | n/a | 🔴 |
| 11 | Fire Extinguisher | 🟢 | 🔴 | n/a | 🔴 |
| 12 | Safety Topic Library | 🟢 | 🔴 | 🟢 (topic content) | 🟡 (library tips empty in ES but content rich) |
| 13 | Safety Document | 🟢 | 🔴 | n/a | 🔴 |
| 14 | Safety Training record | 🟢 | 🔴 | n/a | 🔴 |

**Composite verdict count**: 🟢 0 · 🟡 2 · 🔴 12.

---

## 6 · Retired false findings (Spanish-specific)

| Inherited claim | Source-direct verification | Disposition |
|---|---|---|
| "Spanish coverage is ~52%" (composite Phase 2 figure) | Layer A: ~comprehensive. Layer B: < 1%. Layer C: 23 dictionaries · 1579 LOC. | **REFINED — the 52% was a composite of incompatible layers.** Replace with two layer-specific scores. |
| "Spanish content is broadly machine-translated" | `excavation.es.js` sampling shows idiomatic field prose with specific weights (3,000 lb/yd³), OSHA citations preserved, regional idioms ("nomás un minuto"). Not machine-translated. | **RETIRED** (per Layer C content). |
| "Every safety tip needs translation" | A subset of tips already has English body that, once translated, will fall through cleanly via the `body_es` mechanism. The infrastructure exists; only content is missing. | **REFINED**: the gap is content, not infrastructure. |

---

## 7 · Operator priorities (informational, not authorizing)

Layer B remediation, if authorized via FOCP, can be sequenced by safety-leverage:

| Rank | Form_key | Why |
|---|---|---|
| 1 | fleet.rts (body_es) | Highest single-decision risk. |
| 2 | jha + jha.poster (body_es) | Legal attestation chain. |
| 3 | incident.severity, incident.narrative (body_es) | OSHA-recordable record integrity. |
| 4 | qaqc.signoff (body_es) + Amendment 001 closure path coaching | Per Phase 2 P4. |
| 5 | preop.controls + preop.signoff (body_es) | Pre-shift defect surfacing. |
| 6 | safety-training.expiration (body_es) | Unqualified-operator-in-service prevention. |

Each row above is a tip-body content addition, NOT a new workflow. Per Rule 2 (reuse existing content), the EN bodies already exist; Layer B is a content-translation task gated by FOCP 7-test + 4-proof.

---

**End of SAFETY SPANISH GAP REGISTER · STCP 3 of 5**
