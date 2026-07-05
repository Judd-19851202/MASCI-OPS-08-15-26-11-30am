# ForgedOps · MASCI Operations Platform · Constitution

**Version:** 1.0 · Ratified 2026-02 (Track 22.2)
**Status:** Permanent. Amendments require a numbered track.

---

## Volume I · Platform Identity

**ForgedOps** is the platform. **MASCI Operations Platform** is its
first tenant. Product purpose: consolidate the field-crew day —
Daily Report, Safety, HR crew time, Equipment, Photos, Signatures —
into a single trusted operational spine, then surface intelligence
above that spine for PM/Admin without disrupting the field workflow.

Doctrine: **field-first · operations-first · one platform.**

## Volume II · Permanent Architecture Decisions

- **One platform.** One login. One nav paradigm per role.
- **One workflow per operational need.** No V1/V2 forks.
- **AI is additive only.** Never a dependency of a core workflow.
- **English is canonical storage.** Spanish is a supported UI mode.
- **Invisible Intelligence.** Field UI never surfaces AI vocabulary.
- **AI optional per tenant.** Five-link resolver gate.
- **No duplicate dashboards.** One PM OI. One Admin OI.
- **No duplicate status engines.**

## Volume III · Eight Pillars

Powerful · Simple · Beautiful · Trusted · Proven · Deployable ·
Durable · Relentless Ownership.

Every decision must satisfy every pillar simultaneously.

## Volume IV · Hard Rules (never violate)

1. Never remove a core workflow (Daily Report, HR export, ODS ingest,
   PDF, email, safety, photos, signature, EN/ES).
2. Never fork the Daily Report.
3. Never duplicate PM or Admin dashboards.
4. Never break historical records.
5. Never expose AI branding in the field UI.
6. Never make AI mandatory.
7. Never invent facts.
8. Never fake green.
9. Never leave a defect unowned.
10. Never weaken RBAC.
11. Never mutate production data without a documented, approved plan.
12. Never commit real provider API keys.

## Volume V · Product Constitution

- **UI consistency:** MASCI navy/red banner, shadcn cards, mono/caps
  kicker labels, calm palette, no purple gradients.
- **Route consistency:** every backend route prefixed `/api`;
  canonical + deprecated aliases coexist during transition windows.
- **Dropdown doctrine:** native `<select>` avoided where a
  shadcn/radix picker is available; native OK when the label maps 1:1
  to `unit_number` (never `display_label`).
- **Autosave doctrine:** the form's `data`/`set` pattern is the
  contract. New sections plug in; parent behaviour unchanged.
- **Validation doctrine:** validation lives in the form. AI never
  gates a submit.
- **Navigation doctrine:** admin nav for admins. Field nav for field.
  No cross-portal leakage.
- **Accessibility doctrine:** every interactive element carries a
  `data-testid`. Colour + shape both signal state.
- **Mobile/iPad doctrine:** ToughBook / iPad first for the field
  form.
- **Operator-first doctrine:** if a change requires operator
  retraining, it does not ship without an ADR.

## Volume VI · Daily Report System

- Single Daily Report: `/daily/submit` → `POST /api/daily-reports` →
  Mongo `daily_reports`.
- Preserved fields: `masci_crews[]`, `equipment[]`, `photos[]`,
  safety, materials, production, weather, GPS, signature.
- Email + PDF + HR + ODS + notifications untouched by AI presence.
- DR-CUTOVER-002 summary section is optional; disabled mode graceful.

## Volume VII · PM Operational Intelligence

PM sees: project health, RFIs, submittals, daily reports, photos,
risks, incidents, CAPAs, labor/equipment/material evidence — all
sourced from `operational_facts` + `operational_kpi_snapshots`.
No wrong-role clutter. No AI branding.

## Volume VIII · Admin Operational Intelligence

Admin sees: configuration, approvals, audit, exports, tenant control,
Trust Center, deployment readiness, AI Configuration, integration
truth surface.

## Volume IX · AI Architecture

- Single resolver: `resolve_ai_capabilities(db, tenant_id, module)`.
- Providers: Anthropic · OpenAI · Google (future providers pluggable
  via `MODULE_ENV_MAP` + `PROVIDER_KEY_MAP`).
- Every module: deployment flag AND tenant flag AND provider ready.
- Failover configurable.
- Disabled mode returns `enabled=false, reason_disabled=<code>`;
  never a 5xx.
- Secrets NEVER written to `.env` in the repo. Populated via
  Emergent Secrets UI at deploy time and surfaced only as booleans
  in admin responses.

## Volume X · ODS Architecture

- `operational_facts` collection holds every fact (labor, equipment,
  photo evidence, intelligence).
- `is_current` toggles supersede old facts idempotently.
- `operational_kpi_snapshots` pre-computed for dashboard reads.
- Backfill scripts non-destructive.

## Volume XI · Translation Architecture

- English canonical.
- Spanish UI mode via toggle.
- `translateUserInput` runs client-side on submit; canonical
  English lands on the server.
- Emails/PDFs/audit rendered in canonical English by default;
  bilingual variants are additive.

## Volume XII · Security

- `require_admin_strict` on every admin-write surface.
- Public field submit is rate-limited.
- Tenant isolation enforced by path parameter + Mongo scope.
- Provider keys never in responses. Locked by tests.

## Volume XIII · Deployment Doctrine

- Deployment gate = deployment_agent PASS + all lock envelopes green
  + Playwright role-by-role smoke.
- Preview `.env` distinct from production (Emergent Secrets UI).
- `EMAIL_SAFETY_MODE=strict` in preview.
- Rollback plan mandatory before every deploy.
- Post-deploy verification: canonical routes respond; new + deprecated
  aliases both respond; disabled-AI graceful path returns 200.

## Volume XIV · Lessons Learned

- Second Daily Report is forbidden. `/daily-report/v2` → redirect.
- AI must remain invisible in the field UI.
- Native dropdown breakage on iPad → prefer shadcn picker where safe.
- Dashboard identity drift kills trust — one PM OI, one Admin OI.
- V2 chasing kills momentum — enhance the production form instead.
- Executive dashboard was speculative — file exists but is not routed.
- ODS must be fed by production Daily Reports; V1→ODS hook is
  canonical.
- AI dependency risk → every core workflow must run with AI off.
- PM routing source mismatch — writes and reads must share one
  collection name.
- Async task weak-reference email failure — future queue should
  hold strong refs.
- `display_label` vs `unit_number` — pickers must emit the id, not
  the label.
- Backup false-red risk — status endpoints must read live state.
- Health alert spam — alert only on real regressions.
- Dispatch map admin-route bug — role guards must be on every
  admin-only surface.
- Certification reports beating screenshots — evidence hierarchy is
  screenshots > live behaviour > code > docs.

## Volume XV · Current Platform Status

- Repo: `MASCI-OPS-07-05-2026-3pm` @ commit `9fb30c7a`.
- 1,264 backend Python files. 903 frontend JSX/JS files.
- 685 backend test files. 3,735 memory docs (curation pending).
- Deployment status: **certified** (preview) per DR-UNIFY-004.
- Live integrations verified this pass: Resend, Sentry, Atlas.
- Live integrations mismatched with claim: Motive (see F-02).
- Mocked integrations: MaintainX (safely `false` flags).
- Not-yet-configured integrations: Gemini (safely absent).

## Volume XVI · Future Roadmap

- Provisioning CLI for tenants.
- Module gating / SKU tiering.
- Executive Portal (only when scoped).
- Live-LLM polish over the deterministic composer.
- Photo Intelligence production certification.
- Background queue for ODS ingestion.
- Telemetry for `/api/dr-v2/*` alias usage (feeds DR-UNIFY-005
  removal decision).

## Volume XVII · Non-Negotiable Standards

One platform. One workflow. Production-first. Field-first.
Operations-first. Invisible intelligence. Zero drift. Done means done.
No feature for feature's sake. Measurable operational value. Every
defect owned.

---

## Appendix A · Glossary

- **ODS** — Operational Data Spine (`operational_facts` +
  `operational_kpi_snapshots`).
- **Resolver** — `resolve_ai_capabilities(db, tenant_id, module)`.
- **Invisible Intelligence** — field UI never surfaces AI vocabulary.
- **Canonical route** — `/api/daily-reports/*`.
- **Deprecated alias** — `/api/dr-v2/*` served during transition.
- **DR-UNIFY-004** — deployment certification track.
- **Constitution** — this file. Permanent doctrine.

## Appendix B · Canonical naming

- Backend routes under `/api/*`.
- Mongo collections: canonical `daily_report_*`; legacy `dr_v2_*`
  served via read-compat helper.
- Frontend page files: `pages/<domain>/<PascalName>.jsx`.
- Test files: `tests/test_<track>_<subject>.py`.

## Appendix C · Standard workflow patterns

- Public form → rate-limited POST → Mongo write → ODS hook →
  auto-email schedule → 200 response.
- Admin surface → `require_admin_strict` gate → `X-Admin-Actor`
  audit tag → allow-list body → audit write → response.

## Appendix D · Architectural Decision Log

- ADR-001 (DR-UNIFY-001): One Daily Report.
- ADR-002 (DR-CUTOVER-001): V1 → ODS hook.
- ADR-003 (DR-CUTOVER-002): Optional Daily Operational Summary
  inside the existing form.
- ADR-004 (AI-CONFIG-001): Secret placeholders only in `.env`;
  real values via Emergent Secrets UI.
- ADR-005 (AI-ADMIN-001): Admin surface for tenant AI switchboard.
- ADR-006 (DR-UNIFY-003): Route/collection alias consolidation with
  read-compat helper.
- ADR-007 (DR-UNIFY-004): Deployment certification gate.
- ADR-008 (Track 22.2): Constitution ratified. Feature freeze pending
  Track 22.3.
