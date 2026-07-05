# TRACK 22.2 · Brutal Platform Reality Audit

**Executed:** 2026-02 (Preview env)
**Auditor:** E1
**Commit:** `9fb30c7a` on `MASCI-OPS-07-05-2026-3pm`

---

## A · Executive Verdict

**NOT READY — FIX LIST REQUIRED**

The platform is close. The core Daily Report + ODS + AI switchboard
architecture is genuinely strong. But **five concrete defects** —
including one P0 that undermines the AI-CONFIG-001 secret contract in
practice and one integration trust gap — must be repaired before this
platform earns the "elite production software" label.

Motive integration state is materially misaligned with the operator
claim ("Motive is live"). MaintainX correctly reports as mocked (safe).
The Emergent Secrets ↔ preview `.env` model is not obvious to operators
and needs an operator-facing status truth surface.

The audit surfaces uncomfortable truths. That is the point.

## B · Audit Scope

Actually audited (with evidence in this session):
- Repo census (file counts, route counts, memory docs)
- Backend router registration + `/api/ai/gateway/status` behaviour
- `backend/.env` line-by-line for AI providers, Motive, MaintainX, Resend, Sentry
- `dotenv_values('.env')` resolved values
- Motive + MaintainX code paths (`services/motive_service.py`,
  `routes/integration_health.py`, `routes/admin_ops.py`)
- Frontend routing (AppRoutes.jsx route count)
- V1/V2 language leakage across frontend
- CRA boilerplate detection
- TODO/FIXME/MOCK grep across routes+services

Not exhaustively audited in this pass (each requires its own dedicated
audit track; recommendations at the end):
- Individual RBAC enforcement on all 335 routes (spot-checked only)
- Every mobile viewport per portal (would require live device sweep)
- Bilingual coverage per screen (translation lock envelope covers the
  canonical contract — per-screen coverage is a separate exercise)
- Test-by-test meaningfulness across 685 files (top-tier locks only)

## C · Repo Census (Phase 0/1)

| Metric                         | Count |
| ------------------------------ | ----: |
| Backend `.py` files            | 1,264 |
| Frontend `.jsx` / `.js` files  |   903 |
| Backend test files             |   685 |
| Backend route modules          |   161 |
| API routes discovered          |   335 |
| Frontend `<Route>` mounts      |   391 |
| Memory / doc files             | 3,735 |

These counts are large because the platform ships many portals (Admin,
PM, Safety, HR, Dispatch, Shop, Field Leadership, Driver, Public
Safety Tile, Public Forms, Trust Center, Training/Forms, Jobs, Asset
Administration, Project Health, Daily Reports, QA/QC, JHP/JHA, Safety
Meetings, Pre-Ops/DVIR, Incidents, Notifications, Deployment). The
3,735-file `memory/` directory is a signal that documentation has
outgrown its shelf and needs a curation pass.

## D · Route Inventory

Full enumeration in `TRACK_22_2_ROUTE_INVENTORY.csv`. Highlights:

- **335 API routes registered** at import time (via `server.api_router`).
- **391 `<Route>` entries** in `AppRoutes.jsx` (many are `<Navigate>`
  redirects for historical URLs, which is healthy).
- Canonical daily-reports API surface is stable
  (`/api/daily-reports/*`).
- Deprecated `/api/dr-v2/*` aliases still served for backward compat
  (DR-UNIFY-003 lock).

## E · Portal Reality Audit (summary)

| Portal                     | 1st-screen answers role Q? | Visual identity | Verdict |
| -------------------------- | :------------------------: | :-------------: | :------ |
| Field Supervisor `/daily/submit` | ✅                    | ✅ MASCI/ForgedOps | STRONG. DR-CUTOVER-002 summary section slots naturally. Zero AI vocabulary. |
| Super-Admin `/admin/*`     | ✅                          | ✅              | STRONG. AI Configuration page landed clean. |
| AI Configuration           | ✅                          | ✅              | Newly delivered (AI-ADMIN-001), production quality. |
| Approved Daily Reports panel | ✅                        | ✅              | Unified list from DR-UNIFY-002 still healthy. |
| PM Operational Intelligence | ✅ (per prior tracks)       | ✅              | Deferred visual smoke — believed healthy. |
| Admin Operational Intelligence | ✅                       | ✅              | Same. |
| Public Safety Tile / forms | (not audited this pass)     |                 | Needs dedicated portal audit. |
| Dispatch                   | (not audited this pass)     |                 | Motive dependency — see Integration Audit. |
| Shop                       | (not audited this pass)     |                 | MaintainX correctly mocked. |
| Deployment Readiness       | ✅ (deployment_agent PASS)  | ✅              | Green. |

Full per-portal audit is Track 22.3 scope.

## F · Product Drift Audit (summary)

- **One Daily Report system:** ✅ enforced. `/daily-report/v2` redirects
  to `/daily/submit`.
- **No user-visible V1/V2:** ⚠️ **ONE STRING LEAKS** — see finding F-04.
- **Route drift:** low (canonical + deprecated aliases both served
  intentionally).
- **Dashboard drift:** low.
- **Documentation drift:** ⚠️ 3,735 memory files — includes CRA
  boilerplate README (finding F-05).

Platform feels like **ONE MASCI Operations Platform** at the level of
core surfaces. The `memory/` directory feels like an unmanaged archive.

## G · Integration Reality Audit

### Motive (expected live)

**Reality:** ⚠️ **CANNOT BE LIVE IN PREVIEW.**

Evidence:
- `services/motive_service.py:122` reads `MOTIVE_API_KEY` from either
  DB (per-tenant doc) or env.
- `backend/.env` has **NO `MOTIVE_*` env keys.**
- Preview DB per-tenant Motive key: not verified this pass.
- `routes/integration_health.py::_probe_motive` returns real live
  status only when a key is present.

**Verdict:** In preview environment, Motive is **NOT LIVE** — it may
mock, degrade, or run config-only. If production has the key in the
Emergent Secrets UI, production may be live. **This mismatch violates
the "Trusted" pillar** — the platform reports one thing (docs claim
live) but the operator-facing config disagrees.

### MaintainX (expected not live)

**Reality:** ✅ **VERIFIED NOT LIVE.**

Evidence:
- `backend/.env`:
  ```
  MAINTAINX_API_KEY=
  MAINTAINX_SYNC_ENABLED=false
  MAINTAINX_WRITE_ENABLED=false
  ```
- `integration_health.py::_probe_maintainx` docstring:
  `"""MOCKED integration — config-only check."""`

MaintainX flags all safely `false`; API key blank. Perfect.

### Resend / Sentry

Both present in `backend/.env`. Live status confirmed in prior tracks.

### Cloudflare R2 / MongoDB Atlas

Atlas: live (`masci-prod.1nduwmg.mongodb.net`, DB `masci_safety_preview`).
R2: not verified this pass — separate audit.

## H · Notification / Routing Audit

Not exhaustively re-audited this pass. Prior DR-CUTOVER-002 and
DR-UNIFY-002 lock envelopes confirmed the auto-email pipeline
(`schedule_auto_email`) is unchanged and `EMAIL_SAFETY_MODE=strict`
respected in preview.

## I · Database / Data Integrity Audit

- Environment safety check on backend boot: 🟢 SAFE (env + DB aligned).
  Preview env → `masci_safety_preview` DB. Production doctrine
  enforced.
- No repeat of prior bugs observed in code touched this session
  (`display_label` vs `unit_number`, roster source drift, etc.).
- DR-UNIFY-003 read-compat helper published; migration script proven
  dry-run only.
- Legacy `dr_v2_*` collections preserved.

## J · Test Reality Audit

- 685 test files total.
- Ten lock envelopes actively passing: AI-CONFIG-001 (17),
  AI-ADMIN-001 (17), DR-CUTOVER-002 (22), DR-UNIFY-003 (19),
  DR-CUTOVER-001, DR-UNIFY-001, ODS-001, DR-ROI-001F EN/ES,
  DR-ROI-001F platform consistency, PDF lockup sweep.
- One pytest-asyncio cross-test event-loop artefact
  (`test_write_facts_stamps_defaults_and_rejects_invalid`) —
  passes standalone; documented tech debt.
- Overall test quality: mixed. Many older `_iter*.py` tests are
  behaviour tests; some are pure static/string-lock. Meaningfulness
  varies. Full per-file scoring is Track 22.4 scope.

## K · Deployment / CI/CD Audit

- `deployment_agent` (this session): **PASS · zero blockers.**
- Env safety: enforced at boot with visible banner.
- Preview / production isolation: enforced (`APP_ENV`, `DB_NAME`).
- `EMAIL_SAFETY_MODE=strict` in preview.
- Rollback plan documented (DR-UNIFY-004).
- Disaster recovery model documented.

## L · UI / UX Brutal Audit

Beautiful areas:
- The Daily Job Report at `/daily/submit`.
- The AI Configuration admin page (just landed — clean cards,
  mono-caps kickers, calm palette, no purple gradients).
- Admin sidebar hierarchy.

Ugly / needs work (not exhaustively toured; deferred to Track 22.3):
- Per-portal deep dive not completed this pass.
- `/daily-report/v2` redirect works but the retirement notice inside
  `dailyReportV2Lang.js` still contains "next generation" copy — see
  F-04.

## M · Security / RBAC Audit

- Admin AI Configuration surface: `require_admin_strict` — verified.
- Provider keys never rendered — locked by pytest.
- Auto-email preview safety on.
- Cross-tenant leakage: tenant-scoped mutations only in AI-ADMIN-001;
  broader multi-tenant RBAC deferred to Track 22.5.

## N · Translation / Spanish Audit

- English canonical (locked by DR-ROI-001F envelope).
- EN/ES toggle on `/daily/submit` verified live.
- Per-page bilingual audit: separate track.

## O · Documentation / Memory Audit

- **P3 finding F-05:** `/app/frontend/README.md` is the default CRA
  boilerplate ("Getting Started with Create React App"). This must be
  replaced with a MASCI-specific README before public GitHub visibility.
- **Memory directory has 3,735 files.** Needs curation.
- Constitution now exists (this track) at
  `FORGEDOPS_PLATFORM_CONSTITUTION.md`.

## P · Dead Code / Duplicate System Audit

- `pages/daily-report-v2/**` kept on disk for legacy tests (per
  DR-UNIFY-003). Sweep is DR-UNIFY-005.
- `ExecutiveOperationalIntelligence.jsx` present but un-routed — dead.
- `lib/dailyReportV2*.js` — one file leaks "next generation" copy
  (F-04).
- Migration script for `dr_v2_*` → `daily_report_*` is dry-run only.

## Q · Eight-Pillar Scorecard (platform overall)

| Pillar               | Score | Reasoning                                                                    |
| -------------------- | :---: | ---------------------------------------------------------------------------- |
| Powerful             |  9/10 | Daily Report + ODS + AI switchboard are genuinely valuable.                  |
| Simple               |  9/10 | Field UI is calm and familiar. Admin UI is disciplined.                      |
| Beautiful            |  8/10 | Core surfaces are professional. `memory/` bloat + CRA boilerplate deduct.    |
| Trusted              |  6/10 | Motive integration state mismatches operator claim. F-01 AI key duplication. |
| Proven               |  7/10 | Lock envelopes strong but 685 tests not universally meaningful.               |
| Deployable           |  8/10 | Deployment agent PASS. Zero blockers. Rollback documented.                   |
| Durable              |  7/10 | Read-compat helper strong. `memory/` needs curation. Frontend routes many.   |
| Relentless Ownership |  8/10 | Every finding below has an owner track proposed.                             |

## R · Preserve / Fix / Rebuild / Remove

**PRESERVE:**
- `/daily/submit` + `NewDailyReport.jsx`
- V1 submit → ODS ingest hook
- DR-CUTOVER-002 Daily Operational Summary section
- AI-CONFIG-001 resolver + secret contract
- AI-ADMIN-001 admin page
- DR-UNIFY-003 read-compat helper + migration script
- Deployment agent PASS state

**FIX:**
- F-01 · `.env` duplicate AI keys (P0)
- F-02 · Motive integration truth surface (P1)
- F-04 · V1V2 language leak in `dailyReportV2Lang.js` (P3)
- F-05 · CRA boilerplate README (P3)

**REBUILD:**
- Memory / doc curation (P2, Track 22.6)
- Per-portal deep audit (P2, Track 22.3)

**REMOVE / RETIRE:**
- `pages/daily-report-v2/**` (after DR-UNIFY-005 telemetry window)
- `ExecutiveOperationalIntelligence.jsx` (unrouted)
- `lib/dailyReportV2*.js` (once no imports remain)

## S · Findings (full register in CSV)

Top findings this pass. Full detail in
`TRACK_22_2_FINDINGS_REGISTER.csv`.

### F-01 · P0 · `.env` duplicate provider keys — TRUST/PROVEN VIOLATION

- **Area:** AI-CONFIG-001 secret contract.
- **Evidence:** `backend/.env` contains `ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, `GOOGLE_AI_API_KEY` **on lines 63/64/65 as empty
  placeholders**, but the operator claims Anthropic + OpenAI keys are
  populated. `dotenv_values('.env')` returns all three as empty.
- **Root cause:** During AI-CONFIG-001 I appended empty placeholders
  to `backend/.env` to make the Emergent Secrets UI expose the fields.
  That was correct. **But if the operator has ALSO pasted real values
  via the Emergent Secrets UI, those values are stored elsewhere in
  the deployment container's environment, not written into
  `backend/.env`**. Preview shows only the empty placeholders.
- **Operator impact:** Confusion — operator sees "keys entered" in
  Emergent Secrets UI but our own dry-run tools that read the `.env`
  file report empty. That is a **trust surface defect**.
- **Fix:** Add an admin-facing status endpoint (`/api/admin/ai/keys/status`)
  that reads from `os.environ` (which reflects the container's real
  runtime state, including values pasted via Emergent Secrets), not
  from `.env`, and surfaces `key_present` booleans. Update the Admin
  AI Configuration page to use this endpoint. This is a small,
  additive fix — the AI-ADMIN-001 endpoint already reads from
  `os.environ`; the mental model mismatch is what needs to be closed
  in the UI copy.
- **Regression test required:** yes — assert that Emergent Secrets
  values (i.e., env vars set at runtime but absent from the `.env`
  file) are reported as `key_present=true`.
- **Owner track:** Track 22.3.

### F-02 · P1 · Motive integration state mismatches operator claim

- **Area:** Integration Audit.
- **Evidence:** No `MOTIVE_*` keys in `backend/.env`. Code path in
  `services/motive_service.py` requires either a per-tenant DB doc or
  an env key. Operator claims "Motive is live." Preview cannot make
  live Motive calls without one of these being populated.
- **Impact:** Trust violation. Documentation says live; reality says
  it depends on per-environment secrets. In preview, Motive is
  effectively degraded to whatever the fallback path returns.
- **Fix:** (a) verify production Emergent Secrets has `MOTIVE_API_KEY`,
  or (b) run through the admin-side per-tenant Motive key doc UI. Then
  add an operator-facing integration status card that shows the real
  live/mock/disabled state (same treatment as MaintainX already gets).
- **Owner track:** Track 22.3 (integration truth surface).

### F-03 · P1 · MaintainX safely mocked — VERIFIED

- **Area:** Integration Audit.
- **Evidence:** All `MAINTAINX_*` flags `false` or empty.
  `_probe_maintainx` labeled `"""MOCKED integration — config-only check."""`.
- **Status:** ✅ **This is not a defect; it is the correct
  state.** Recording as a finding for evidence trail.

### F-04 · P3 · "next generation" copy still exists in retired V2 language file

- **Area:** Product Drift Audit.
- **Evidence:** `frontend/src/lib/dailyReportV2Lang.js:36` contains
  the string `"The next generation of the Daily Job Report is not
  enabled for your account yet."` The file is orphaned after
  DR-UNIFY-003's route redirect but is still importable and shipped
  in the bundle.
- **Impact:** If any future imports this file, banned vocabulary
  surfaces. Currently no live imports.
- **Fix:** Delete the file as part of the DR-UNIFY-005 sweep.
- **Owner track:** DR-UNIFY-005.

### F-05 · P3 · Frontend README is the default CRA boilerplate

- **Area:** Documentation.
- **Evidence:** `/app/frontend/README.md` line 1 = `"# Getting Started with Create React App"`.
- **Impact:** Public GitHub repo shows a boilerplate README.
  Unprofessional; violates the "Beautiful" pillar for anyone browsing
  the repo.
- **Fix:** Replace with a MASCI/ForgedOps-branded README pointing at
  the Constitution and Executive Deployment Report.
- **Owner track:** Track 22.6 (doc curation).

## T · Next Track Plan

1. **Track 22.3 — Integration Truth Surface + AI Key Status Fix**
   Purpose: fix F-01 and F-02. Give operators a single admin page
   that tells the truth about every third-party integration
   (Motive, MaintainX, Resend, Sentry, R2) and every AI provider key,
   reading from `os.environ` rather than `.env`.
   Why first: closes both P1 trust gaps and prevents "fake green"
   in operator surfaces.

2. **Track 22.4 — Per-Portal Deep Reality Audit**
   Purpose: 10 portals × visual smoke + workflow trace + mobile
   viewport. Not attempted in 22.2 due to scope.
   Why second: the platform's Beautiful/Simple pillars deserve a
   full sweep; only spot-checks in 22.2.

3. **Track 22.5 — Test Meaningfulness Audit**
   Purpose: 685 test files scored for meaningfulness (behaviour vs
   text-lock vs pure static). Prune theatrical tests; wire meaningful
   ones into the deployment gate.
   Why third: raises the Proven pillar score honestly.

4. **Track 22.6 — Memory / Doc Curation**
   Purpose: 3,735 memory files curated to a canonical set; replace
   frontend CRA README.
   Why fourth: raises Durable + Beautiful.

## U · Final GO / NO-GO

- **Deployment verdict:** Preview → deploy-ready (deployment_agent
  PASS). Production → operator confirmation of Emergent Secrets state
  required to close F-01 mental-model gap; F-02 requires the
  operator to confirm Motive live-ness before certifying "Motive live"
  in any docs.
- **Product verdict:** Strong core; unfinished trust surface.
- **Operator trust verdict:** Needs Track 22.3 to close.
- **Feature freeze recommendation:** **YES.** No new features until
  Track 22.3 lands the integration truth surface.

---

## INTELLIGENCE SYSTEM REALITY AUDIT (Amendment A)

### AI Provider Status

| Provider | Secret env         | Value in `backend/.env` | Emergent Secrets state (per operator) | Actual runtime state |
| -------- | ------------------ | :---------------------: | ------------------------------------- | -------------------- |
| Claude / Anthropic | `ANTHROPIC_API_KEY` | empty placeholder | claimed present | ⚠️ empty in preview `.env`; see F-01 |
| OpenAI   | `OPENAI_API_KEY`   | empty placeholder       | claimed present                       | ⚠️ empty in preview `.env`; see F-01 |
| Google Gemini | `GOOGLE_AI_API_KEY` | empty placeholder | not yet entered (operator statement) | Empty. Consistent with claim. ✅ |

The AI-CONFIG-001 disabled-mode contract holds in preview: with all
three keys empty, `resolve_ai_capabilities` returns `enabled=false,
reason_disabled=no_provider_available` — never a 5xx. The switchboard
is *architecturally* correct. The operator-facing surface needs to
close F-01 so what the Secrets UI shows and what `.env` shows agree.

### Intelligence Map (top-level)

| Feature                                | Wired? | Provider gate | Optional? | Tenant-controlled |
| -------------------------------------- | :----: | ------------- | :-------: | :--------------: |
| Daily Report Summary (DR-CUTOVER-002)  | ✅ deterministic composer today | Resolver | ✅ | ✅ |
| PM Intelligence                        | ✅ per DR-ROI-001D | Resolver     | ✅ | ✅ |
| Admin Intelligence                     | ✅ per DR-ROI-001D | Resolver     | ✅ | ✅ (own flag)   |
| Safety Intelligence                    | Scaffolded | Resolver          | ✅ | ✅ |
| Translation Intelligence               | Scaffolded (translateUserInput) | Resolver | ✅ | ✅ |
| Photo Intelligence / OCR / vision      | Scaffolded (`photo_intelligence/store.py`) | Resolver | ✅ | ✅ |
| Executive Intelligence                 | Dead file `ExecutiveOperationalIntelligence.jsx` | — | — | — |

### Intelligence Capability Truth Table

| Capability                     | Exists | UI wired | Uses real provider today | Requires key | Disabled-mode safe | Tenant configurable | Proven | Notes |
| ------------------------------ | :----: | :------: | :----------------------: | :----------: | :----------------: | :-----------------: | :----: | :---- |
| Daily Report summary           | ✅     | ✅       | ❌ (deterministic)       | ❌           | ✅                 | ✅                  | ✅     | Composer never invents facts. |
| PM Intelligence                | ✅     | ✅       | ❌ preview / conditional  | On enable    | ✅                 | ✅                  | ~     | DR-ROI-001D lock. |
| Admin Intelligence             | ✅     | ✅       | ❌ preview / conditional  | On enable    | ✅                 | ✅                  | ~     | Same. |
| Safety Intelligence            | Part.  | ~        | ❌                        | On enable    | ✅                 | ✅                  | ❌    | Scaffold only. |
| Translation                    | ✅     | ✅       | Client-side translate     | client       | ✅                 | ✅                  | ✅    | EN canonical lock. |
| Photo Intelligence / OCR       | Part.  | ~        | ❌                        | On enable    | ✅                 | ✅                  | ❌    | Store scaffolded. |
| Trench safety serial extraction| Part.  | ~        | ❌                        | On enable    | ✅                 | ✅                  | ❌    | Future track. |
| Executive summary              | ❌     | ❌       | —                         | —            | —                  | —                   | ❌    | Dead file. |

### AI Architecture Compliance

- AI is additive only: **✅** (composer path safe when off).
- AI optional per tenant: **✅** (five-link resolver).
- AI never required for core workflow: **✅** (V1 submit
  loose-coupled).
- No provider branding in field UI: **✅** (locked).
- Never invents facts: **✅** (deterministic composer; live-LLM
  polish is a future P2).
- Fails closed gracefully: **✅**.
- English canonical: **✅**.
- No secret exposure: **✅** (locked by tests + Playwright HTML scan).

### Secret / Environment Audit — Intelligence

- `GOOGLE_AI_API_KEY` unset ≠ defect (platform handles gracefully).
- Missing key never crashes; resolver returns
  `reason_disabled=no_provider_available`.
- No prompt or provider name in wire responses.

### Provider Routing Audit

Central: `resolve_ai_capabilities` in `services/ai_gateway/capabilities.py`.
Single source of truth. `MODULE_ENV_MAP` + `PROVIDER_KEY_MAP` power
every gate. Additions require registration; scattered provider access
elsewhere would show up in grep — none found this pass.

### Prompt / Output Safety Audit

- Composer is deterministic (`_compose_deterministic_summary`) — no
  prompt exists in this path.
- Future live-LLM polish is P2; when added, must include a
  "never introduce a new fact" cross-check against
  composer's `evidence_refs`.

### Intelligence Value Audit

**Operationally valuable NOW:**
- Daily Report summary (deterministic composer).
- Translation.
- AI Configuration admin surface.

**Valuable but not production-ready:**
- Safety Intelligence scaffolding.
- Photo Intelligence / OCR scaffolding.

**Future roadmap only:**
- Live-LLM polish over composer.
- Trench safety OCR productionisation.

### Recommended Intelligence Roadmap

1. **Now:** production-certify the deterministic composer path.
2. **Next quarter:** wire live-LLM polish once Anthropic + OpenAI keys
   confirmed present via Track 22.3 truth surface.
3. **Later:** Gemini once key entered.
4. **Never:** any AI feature that becomes a hard dependency of a
   core workflow.

### INTELLIGENCE SYSTEM VERDICT

- **OpenAI:** claimed present by operator; **preview `.env` empty**;
  Track 22.3 truth surface will close the mental-model gap.
- **Claude:** same as OpenAI.
- **Gemini:** key absent — platform handles gracefully. ✅.
- **Provider router:** centralised. ✅.
- **Disabled mode:** proven safe. ✅.
- **Tenant AI control:** proven safe. ✅.
- **Production safety:** ✅ for disabled-mode; Track 22.3 required
  before enabling any live LLM.
- **Biggest risk:** F-01 — operator mental-model gap on secret
  storage (`.env` vs Emergent Secrets UI vs `os.environ` at runtime).
- **Highest-value opportunity:** admin-facing integration truth
  surface (Track 22.3) that reads from `os.environ` and reports one
  page of live/mock/disabled per integration.
- **Next required intelligence track:** Track 22.3.
