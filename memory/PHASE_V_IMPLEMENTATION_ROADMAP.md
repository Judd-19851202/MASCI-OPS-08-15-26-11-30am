# Phase V · Implementation Roadmap
## Phase V.0 · Architecture & Governance · 2026-05-27

> Sequencing, gates, and exit criteria for every sub-phase of the RFI +
> Schedule Intelligence rollout. Doctrine-locked.

---

## 1 · Headline

| Sub-phase | Focus | Build? | Gate |
|---|---|---|---|
| **V.0** *(this pass)* | Doctrine + architecture + governance docs | **NO** | Operator review of 16 deliverables |
| V.1 | RFI MVP (internal PM/Superintendent flow + PDF + audit) | Yes (preview) | Operator review |
| V.2 | External RFI collaboration (tokenized links + external respond) | Yes (preview) | Operator review |
| V.3 | Schedule shell + external P6 link + `.xer` upload (storage only) | Yes (preview) | Operator review |
| V.4 | P6 import MVP (parse + diff + activate) | Yes (preview) | Operator review |
| V.5 | RFI ↔ Schedule linkage (constraint engine + impact view) | Yes (preview) | Operator review |
| V.6 | Operational schedule intelligence (exposure dashboards + dispute package extension + optional external schedule access) | Yes (preview) | Operator review |
| Production | Deploy V.6 to production when operator declares readiness | Yes (production) | Operator-explicit |

**No skip-ahead.** Each sub-phase ships, stabilizes, regression-locks,
operator-reviews, and only then enables the next.

---

## 2 · V.0 Exit Criteria (this pass)

- [x] 16 deliverable docs in `/app/memory/`
- [x] No code changes
- [x] No DB migrations
- [x] No production deploy
- [x] Doctrine inherits visibly from existing platform memory
- [ ] **OPERATOR REVIEW** — pending

---

## 3 · V.1 — RFI MVP

### Scope
- New collections: `rfis`, `rfi_revisions`, `rfi_audit`, `rfi_distributions`
- Backend routers: `routes/rfi/*` (no code in `server.py`)
- PM portal routes: `/pm/rfi`, `/pm/rfi/new`, `/pm/rfi/:id`, `/pm/rfi/:id/edit`, `/pm/rfi/:id/pdf`
- Field Leadership portal routes: `/field-leadership/portal/rfi/new`, `/field-leadership/portal/rfi/:id`
- PDF renderer using existing `pdf_render.py`
- RFI templates: FDOT + Generic (first two)
- State machine implementation matching `RFI_WORKFLOW_LIFECYCLE.md` (no external states yet)
- Sidebar V2 amendment: add "Operational Records" domain (RFI Center entry only)
- Permission matrix enforcement (every cell in `RFI_PERMISSION_MODEL.md §3`)
- Audit-trail append-only enforcement
- Governance Health Chip integration (no external signals yet)
- `restore_drill.py` extended to new collections

### Tests required for V.1 sign-off
- Pytest: every state transition in `RFI_WORKFLOW_LIFECYCLE.md §3` (positive + negative role)
- Pytest: PDF render produces expected sections in expected order
- Pytest: audit trail captures every transition
- Playwright: PM happy path (draft → review → submit → PDF download)
- Playwright: Superintendent mobile draft path
- Playwright: voiding requires dual control
- Playwright: visual doctrine baseline includes `/pm/rfi`
- Playwright: governance chip surfaces RFI-related signals when applicable
- Playwright: no `/api/admin/*` leakage from Superintendent surface

### V.1 exit gate
- All tests green in preview.
- Trendline shows `direction=stable` for the new PM Operational Records pages across at least 14 records.
- Operator runs ≥ 3 real RFIs end-to-end in preview.
- Doctrine inheritance checklist passes.
- Operator authorizes V.2.

---

## 4 · V.2 — External RFI Collaboration

### Scope
- New collections: `rfi_external_tokens`, `rfi_external_audit`
- New backend routers: `routes/rfi/external.py`, `routes/rfi/distribute.py`
- New surface: `/rfi/ext/:token_id/:token_slug` (no portal chrome, mobile-first)
- Email integration: Resend (existing transport · new templates)
- Token issuance + revocation UI (`/pm/rfi/:id/distribute`)
- Per-token rate limiting + abuse discipline
- External response capture
- Clarification-required loop
- PDF download from external surface

### Tests required for V.2 sign-off
- Pytest: token issuance + expiration + revocation lifecycle
- Pytest: external action audit trail fan-out
- Pytest: external response cannot escalate scope beyond assigned RFI
- Playwright: external landing page renders cleanly on mobile
- Playwright: external response flow end-to-end (mock email)
- Pytest: no PII leakage beyond approved fields
- Pytest: rate-limit caps enforced

### V.2 exit gate
- All tests green in preview.
- Operator runs ≥ 2 RFIs that touch a real external party (preview-mode email).
- No security findings (token guessing, scope escalation).
- Operator authorizes V.3.

---

## 5 · V.3 — Schedule Shell + External P6 Link + `.xer` Upload

### Scope
- New collections: `schedule_imports`, `schedules`, `schedule_revisions` (placeholders only — no parsing yet)
- New backend routers: `routes/schedule/import_xer.py` (upload-only, no parse), `routes/schedule/revisions.py`
- New PM routes: `/pm/schedule`, `/pm/schedule/upload`, `/pm/schedule/imports`
- R2 storage layout (`schedules/{project}/raw/{sha256}.xer`)
- "Open Primavera P6" sidebar link (configurable per project)
- Sidebar V2: full Operational Records domain (RFI Center + Schedule Intelligence + P6 link)

### Tests required for V.3 sign-off
- Pytest: upload chunking handles up to 100 MB
- Pytest: file persisted in R2 with sha256 key
- Pytest: empty/non-`.xer` rejected
- Pytest: P6 link config round-trip
- Playwright: upload UX feels native
- Visual doctrine baseline includes `/pm/schedule`
- Trendline stable for new pages

### V.3 exit gate
- All tests green.
- Operator uploads ≥ 2 real `.xer` files (parsing TBD).
- Operator authorizes V.4.

---

## 6 · V.4 — P6 Import MVP (Parse + Diff + Activate)

### Scope
- Vendor parser via `backend/services/schedule_parser.py`
- New collections: `schedule_activities`, `schedule_relationships`, `schedule_milestones`, `schedule_calendars`, `schedule_constraints_native`, `schedule_audit`
- Validation pipeline (per `P6_IMPORT_ARCHITECTURE §4`)
- Diff engine (per `P6_IMPORT_ARCHITECTURE §5`)
- Activation transaction (per `SCHEDULE_BACKUP_RETENTION §7`)
- Schedule views: Activity List · Lookahead · Critical Path Risk (read-only)
- Field-readable lookahead PDF
- Backup integration (`schedule_*` collections in `restore_drill.py`)

### Tests required for V.4 sign-off
- Pytest: parser handles real-world `.xer` files (fixtures from operator-supplied samples)
- Pytest: validation flags fire correctly
- Pytest: diff engine returns expected structure
- Pytest: activation is atomic (rollback on failure)
- Pytest: parser performance envelope met (50 MB ≤ 30s)
- Playwright: upload → preview → accept → activate flow
- Visual doctrine baseline includes new views
- Trendline stable

### V.4 exit gate
- ≥ 3 real-world `.xer` files processed cleanly.
- ≥ 1 schedule activation completed in preview.
- Operator authorizes V.5.

---

## 7 · V.5 — RFI ↔ Schedule Linkage (Constraint Engine)

### Scope
- New collection: `rfi_constraints` (per `SCHEDULE_CONSTRAINT_MODEL`)
- New backend router: `routes/constraints/*`
- "Schedule impact" toggle on RFI draft / review form
- Activity picker UX
- Constraint list / detail views
- Operational Impact View under `/pm/schedule/operational-impact`
- Critical-path exposure calculation
- Rebind pass on schedule activation
- Chip integration for exposure signals

### Tests required for V.5 sign-off
- Pytest: every constraint lifecycle transition
- Pytest: RFI → constraint → activity proposal + confirmation flow
- Pytest: critical-path exposure computation correctness (fixture-based)
- Pytest: rebind pass on revision activation
- Pytest: orphaned-link surface
- Playwright: full triangle (RFI submits → constraint activates → activity reflects)
- Visual doctrine baseline + trendline stable

### V.5 exit gate
- ≥ 5 real RFIs with schedule links closed end-to-end.
- ≥ 1 schedule revision with rebind pass executed.
- Operator authorizes V.6.

---

## 8 · V.6 — Operational Schedule Intelligence

### Scope
- Executive read-only exposure dashboards
- Dispute Package extension (RFI + schedule artifacts bundle)
- Optional external schedule access (tokenized lookahead read-only)
- Aging-exposure email digests (PM + Executive)
- Trend instrumentation of exposure metrics in the doctrine trendline

### Tests required for V.6 sign-off
- Pytest: dispute package generation produces stable sha256 manifest
- Pytest: external schedule token cannot read `.xer` raw file
- Pytest: exposure trend records appended on the trendline
- Playwright: executive view renders calmly
- Trendline stable across all surfaces

### V.6 exit gate
- ≥ 1 dispute package generated for a real RFI.
- ≥ 1 external lookahead tokenized read used in preview.
- Operator authorizes production deploy planning.

---

## 9 · Production Deploy Gate

Before ANY production deploy of any V.x phase:

- [ ] Preview has been stable for ≥ 14 consecutive days post-phase
- [ ] Doctrine trendline `direction=stable` for the new surfaces
- [ ] Operator checkpoint declared for the phase
- [ ] Auto-deploy checkpoint pipeline includes the new surfaces
- [ ] `pre_deploy_check.sh` extended
- [ ] `restore_drill.py` covers new collections
- [ ] No open P0/P1 issues
- [ ] Operator gives explicit written authorization

**No production deploy without explicit operator sign-off, every time.**

---

## 10 · Out-of-Scope (entire Phase V)

The following are **forbidden** anywhere in V.0–V.6 unless explicitly
re-authorized:

- CPM engine implementation
- Two-way P6 sync
- Live Oracle Primavera Cloud API
- Resource leveling
- Cost loading / earned value
- Gantt chart "hero feature"
- Generic ticketing
- Replacing existing workflows (daily reports, safety meetings, JHA)
- Destructive schema migrations
- Auth playbook bypass
- Notification engine rewrite

---

## 11 · Cross-Cutting Discipline

Every V.x phase MUST:

- Live in `routes/*` modules (no new endpoints in `server.py`)
- Use existing token / portal / scope helpers
- Honour the existing rate-limit and lockout infrastructure
- Honour the existing CORS / preview-vs-prod env identity guards
- Register in the visual doctrine baseline probe
- Append to the doctrine trendline
- Participate in auto-deploy checkpoint pipeline
- Pass the visual governance inheritance checklist

---

## 12 · Sign-off

- **Author:** E1 · Phase V.0 architecture authoring pass
- **Status:** 🟢 Roadmap doctrine-grade
- **Next step:** Operator review of the 16 Phase V.0 deliverables before any V.1 build begins.
- **Implementation:** Awaiting operator green-light.
