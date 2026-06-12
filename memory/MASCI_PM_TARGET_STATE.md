# MASCI PM Portal Target State

**Track 13.5C · Definitive PM target state per surface**
**Mode:** Architecture only — no migration, no code.
**Generated:** 2026-06-12 (UTC)

> Closes the operator decisions left open in `MASCI_PM_REALITY_MATRIX.md`. Each PM surface is classified into **Must Exist · Nice To Have · Does Not Belong** with the explicit definition of "complete" at the end.

---

## 1. Surface-by-surface classification

| PM surface | Reality classification (13.5B) | Target classification | Why · what "complete" means |
| --- | --- | --- | --- |
| **Active Projects** | Real | **Must Exist** | Complete = pulse card bound to `/api/pm/jobs` count + `last_refresh` timestamp + drill to project list. |
| **Project Health** | Real | **Must Exist** | Complete = per-project Card grid driven by `/api/pm/command-center/{overview,resources,hauls,materials,shop-impact,safety-impact,timeline}`. All 7 Phase-4A endpoints surface canonical chips. |
| **Risks** | Planned (no engine) | **Nice To Have** | Decision required: **either** the existing Constraints engine is renamed/relabelled as Risks (zero new code) **or** a new domain object is authorized. Complete = one engine, one list view, one chip. **Operator must choose.** |
| **RFIs** | Missing | **Nice To Have** | Out of MASCI scope today. Complete = a future RFI engine with lifecycle (`submitted → pending_verification → verified` or `needs_revision`). **Operator decision required: in scope or out?** |
| **Submittals** | Missing | **Nice To Have** | Same as RFIs — out of scope today; pending operator decision. |
| **Daily Reports** | Real | **Must Exist** | Complete = canonical chips on `/pm/daily`, verification chain unchanged, no copy regression, no ES regression. |
| **Incidents** | Real | **Must Exist** | Same shape as Daily Reports. |
| **CAPAs** | Real but Partial (U-01) | **Must Exist** | Complete = PM-scoped CAPA list view at `/pm/capas` (closes U-01) using existing `/api/pm/crew/capas`. No new engine; only a list view. |
| **Photos** | Real | **Must Exist** | Complete = `/pm/photos` keeps `JobPhotosLibrary` behavior, gains canonical Card grid + tokenized empty state. Production verification (D-01-class) lifts Trusted score. |
| **Holds (Open Holds)** | Real but Partial | **Must Exist** | Complete = unified holds view (Safety · Maintenance · Certification · Inspection) — either a materialized `holds_view` or a dedicated `/api/pm/holds` endpoint. **This is the single highest-impact PM engine gap.** |
| **Due Today** | Real but Partial | **Must Exist** | Complete = pulse card driven by a cross-engine aggregation (`due_at <= now() + 24h`) across Daily / Incident / CAPA / (future) RFI / Submittal. |
| **Crews In Field Today** | Real but Partial | **Must Exist** | Complete = pulse card driven by `/api/pm/command-center/resources` (already exists) — only presentation work. |

Summary: **8 Must Exist · 3 Nice To Have · 0 Does Not Belong.**

There are no PM surfaces that do not belong; every concept in PM V2 maps to a real operator question. The work is engine-completion (Holds, Due Today), engine-decision (Risks/RFIs/Submittals = in or out), and presentation alignment (chips, cards, density).

---

## 2. What does NOT belong in PM

Cross-referenced against `MASCI_PORTAL_TARGET_STATE_MATRIX.md` §3:

- **Job CRUD** → Admin
- **Dispatcher live map** → Dispatch (PM may read, may not own)
- **HR termination flow** → HR
- **Safety form authoring** → Safety
- **ODR issuance** → Operator role
- **Admin scheduler / backup health** → Admin

PM's role is **verify, escalate, and drill** — not author or operate.

---

## 3. The "complete PM" definition

A PM portal is **complete** when all of the following are true:

1. **All 8 Must-Exist surfaces are bound to real APIs** (Holds + Due Today + Crews still need aggregation; CAPA list view is the only new screen needed).
2. **Every PM surface renders through Phase B1 primitives** (`PortalShell`, `StatusChip`, `Card`, `DataTable`, `EmptyState`) — no ad-hoc HubCards survive.
3. **Every PM status uses one of the 18 canonical keys** from `statusRegistry.js`.
4. **Every PM number carries an API provenance tooltip** + last-refresh chip.
5. **`co_pm_emails` scoping is preserved** byte-for-byte (test_iter437 must continue to pass).
6. **PM V2's "Open Holds" pulse card renders a real, unified value** drawn from the Holds engine — not derived per-render.
7. **PM iPad portrait (820×1180) is operator-verified** via a screenshot baseline that survives release-to-release.
8. **One Playwright visual guardrail per PM surface** (similar to the Dispatch canvas guardrail).
9. **PM CAPA list view ships** (closes U-01).
10. **Risks / RFIs / Submittals decisions are recorded** — either authorized as scope and engine-built, or explicitly deferred with a written timestamp.

---

## 4. Five-Pillar PM target

| Pillar | Today (13.5B) | Target | Why the gap closes |
| --- | :-: | :-: | --- |
| Powerful | 9 | 10 | Unified Holds + PM CAPA list + Risks decision = 1 point |
| Simple | 6 | 9 | Primitives + canonical chips + drop ad-hoc cards = 3 points |
| Beautiful | 7 | 9 | Same primitive migration = 2 points |
| Trusted | 7 | 10 | API provenance + refresh chips + production data verification = 3 points |
| Proven | 7 | 9 | Per-surface guardrails + baseline screenshots × 3 viewports = 2 points |
| **Avg** | **7.2** | **9.4** | — |

PM cannot honestly target a 10/10 average because Risks/RFIs/Submittals are still subject to operator decision; the target reflects that honesty.

---

## 5. Minimum implementation steps to reach complete PM (sequenced)

Each is a future track to be authorized **one at a time**. None of them happen in 13.5C.

1. **PM-1:** Build PM-scoped CAPA list view (closes U-01) — uses existing API.
2. **PM-2:** Unified Holds aggregation — author a `/api/pm/holds` (or `/api/holds`) endpoint or materialize a `holds_view`.
3. **PM-3:** Due-Today cross-engine aggregation endpoint.
4. **PM-4:** Phase B3 pilot migration of one PM surface to Phase B1 primitives (visual reskin only — no engine change).
5. **PM-5:** Decision recording for Risks / RFIs / Submittals — written operator answer captured in an audit ledger entry.
6. **PM-6:** Production data verification for PM photo + Motive feed.
7. **PM-7:** Three-viewport screenshot baseline for `/pm/{hub, command-center, jobs, daily, incidents, photos, capas}`.
8. **PM-8:** Per-surface Playwright visual guardrail.

Each PM-N step earns a measurable score improvement against §4.

---

## 6. Standing rules

No deploy. No GitHub save. No merge. No code in this track. The PM portal continues to serve operators as-is.
