# MASCI Command Center Target State

**Track 13.5C · Definitive Command Center specification**
**Mode:** Architecture only — no rename, no collapse, no implementation.
**Generated:** 2026-06-12 (UTC)

> Settles the meaning of "Command Center" once. Future tracks (R-05 collapse, naming hygiene) measure themselves against this document.

---

## 1. What a Command Center IS

A **Command Center** in MASCI is **the primary role landing for a portal**. It must satisfy all of:

1. **Owns the first-screen objective** of the portal (see `MASCI_PORTAL_TARGET_STATE_MATRIX.md`).
2. **Aggregates "what needs me now?"** for one role audience, drawn from real APIs of that portal's engines.
3. **Calm above-the-fold** — max one map, max 4 KPI cards, max 2 primary actions.
4. **Lets the operator drill** from any KPI to the underlying engine record in ≤ 2 clicks.
5. **Renders only canonical objects** — `PortalShell` · `StatusChip` · `Card` · `DataTable` · `EmptyState`.
6. **Always answers "is the data fresh?"** — every metric carries a refresh timestamp + chip flips to `stale_position` / `offline_feed` on SLA breach.

There is **exactly one** Command Center per role-portal. Super-admin gets one additional cross-portal aggregator. That is the full universe.

---

## 2. What a Command Center IS NOT

- **Not an authoring tool.** Authoring belongs to its own surface with a non-"Center" name.
- **Not a settings page.** Settings live under `/admin/settings/*` or `/me/settings`.
- **Not a domain ops view.** A domain's own ops view (trench-safety ops, ODR ops, training ops) is a *module landing*, not a Command Center.
- **Not a multi-role surface.** One role, one Command Center.
- **Not a marketing dashboard.** No vanity metrics. Every card must answer an operator question.
- **Not the only place a KPI appears.** KPIs may appear inside engine surfaces as well, but the canonical authoritative value is rendered here.

---

## 3. The five legitimate Command Centers (target state)

| # | Command Center | Role audience | First-screen objective | Backing APIs |
| --- | --- | --- | --- | --- |
| 1 | **Admin Command Center** (`/admin/command-center`) | Super-admin · Admin | "Is the platform healthy and is anyone locked out who shouldn't be?" | `/api/admin/health/*` · `/api/admin/recovery` · `/api/admin/scheduler` |
| 2 | **Dispatch Command Center** (`/dispatch-portal/command`) | Dispatcher | "Where is every crew right now, and what needs me in the next hour?" | `/api/operations-map/snapshot` · `/api/dispatch/*` · `/api/dispatch-lifecycle/*` |
| 3 | **PM Command Center** (`/pm/command-center`) | PM | "What's at risk on my projects today, and what needs my signature?" | `/api/pm/command-center/{overview,resources,hauls,materials,shop-impact,safety-impact,timeline}` · `/api/pm/jobs` · `/api/pm/crew/capas` |
| 4 | **Safety Command Center** (`/safety/command-center` — does not yet exist; planned, target state only) | Safety Manager | "What unsafe conditions are open right now, and what training/forms are due?" | `/api/safety/*` · `/api/trench-safety/*` · `/api/incidents/*` · `/api/qaqc/*` |
| 5 | **Field Leadership Command Center** (`/field-leadership/portal` — exists as portal home; promote to "Command Center" semantics) | Superintendent · General Foreman | "What is my crew submitting today, what needs my verify, and is there a safety flag?" | `/api/field-leadership/portal/*` · `/api/daily-reports*` · `/api/incidents/*` |

Plus the **single cross-portal aggregator**:

| # | Aggregator | Role audience | Purpose |
| --- | --- | --- | --- |
| 6 | **Operations Center** (`/operations-center`) | Super-admin · Operations Director | Cross-portal glance: every role's Command Center signal in one place. Read-only. |

That is **6 total** surfaces using "Command Center" or "Operations Center" semantics. Everything else loses the suffix.

---

## 4. Alignment audit — current vs target

Cited from `MASCI_COMMAND_CENTER_REALITY_MATRIX.md`.

| Current surface | Current verdict | Target verdict | Action (deferred — analysis only) |
| --- | --- | --- | --- |
| `AdminCommandCenter` (`/admin/command-center`) | Aligned | **Aligned · keep as Admin Command Center** | None |
| `OperationsCenterCommand` (`/operations-center`) | Aligned but overlaps AdminCommandCenter | **Promote to `OperationsCenter`** (the single cross-portal aggregator). Remove the word "Command" from the URL/title to differentiate from the role landings | Awaits R-05 authorization |
| `DispatchCommandCenter` (`/dispatch-portal/command`) | Aligned | **Aligned · keep** | None |
| `PmCommandCenter` (`/pm/command-center`) | Aligned | **Aligned · keep** | None |
| `OdrCenter` (`/odr/center`) | Misaligned (domain ops view) | **Rename to `OdrConsole` or `OdrOpsView`** — drop the "Center" suffix | Awaits R-05 authorization |
| `TrenchSafetyOpsCenter` (`/trench-safety/ops-center`) | Misaligned (domain ops view) | **Rename to `TrenchSafetyOps`** | Awaits R-05 authorization |
| `OperationalGuidanceCenter` (`/guidance/center`) | Misaligned (authoring tool) | **Rename to `GuidanceAuthoring` or `GuidanceLibrary`** | Awaits R-05 authorization |
| `OpsTrainingCenter` (`/ops-training/center`) | Misaligned (catalog/authoring) | **Rename to `OpsTrainingHub`** | Awaits R-05 authorization |
| `AdminIntegrationCenter` (`/admin/integrations`) | Misaligned (settings page) | **Rename to `AdminIntegrations`** | Awaits R-05 authorization |
| (planned) Safety Command Center | Missing | **Build during Safety pillar work** — uses the target-state shell from Track 13.5C | Future |
| (planned promotion) Field Leadership Command Center | Implicit only | **Re-label the FL portal home as Field Leadership Command Center** | Future |

---

## 5. Why this matters to the Five Pillars

| Pillar | Impact of correct CC architecture |
| --- | --- |
| Powerful | Every role has exactly one place that answers "what needs me?" with cited data |
| Simple | The word "Command Center" stops meaning four different things. Operators can navigate the platform by inference |
| Beautiful | All 5 (+1) Centers share `PortalShell` chrome; visually indistinguishable in structure |
| Trusted | All metrics show provenance + freshness chips; no derived numbers |
| Proven | Each Center has its own visual guardrail (the Dispatch canvas guardrail is the reference) |

---

## 6. What this document does NOT do

- Does not rename anything.
- Does not collapse anything.
- Does not specify any code change.
- Does not authorize any merge.

It is the **definitive specification** against which any future R-05 / R-03 collapse work will be measured.

Standing rules: No deploy. No GitHub save. No merge.
