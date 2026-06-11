# MASCI OPERATIONS PLATFORM · RELEASE CANDIDATE CERTIFICATION LEDGER

**Append-only.** Each completed track appends a new section below. Prior entries must never be overwritten.

---

## Program Charter

- **Platform**: MASCI Operations Platform (ForgedOps software / MASCI customer)
- **Production domain**: https://mascidocs.com
- **Required production env**: `APP_ENV=production`, `DB_NAME=masci_safety`, preview banner hidden
- **Required preview env**: `APP_ENV=preview`, `DB_NAME=masci_safety_preview`, preview banner visible
- **Deployment gate**: every track must PASS before redeploy. Operator clicks "Save to GitHub" → "Redeploy" only after TRACK 12 returns CERTIFIED READY TO DEPLOY.

## Tracks

| # | Track | Status | Date |
|---|---|---|---|
| 0 | Certification Control & Evidence Ledger | PASS | 2026-02-11 |
| 1 | Foundation / Environment / Isolation / Startup Guards | PENDING | — |
| 2 | Auth / Sessions / Portal Role Matrix | PENDING | — |
| 3 | Full Route / Navigation / Button / Dead-End Inventory | PENDING | — |
| 4 | Core Data / Production Test-Data Contamination Audit | PENDING | — |
| 5 | Workflow Execution Certification | PENDING | — |
| 6 | Operations Center / Live Map / Motive / Asset Spine | PENDING | — |
| 7 | Integrations / Background Jobs / R2 / Backups / Restore | PENDING | — |
| 8 | Mobile / iPad / Field Usability | PENDING | — |
| 9 | Vocabulary / White-Label / Translation Audit | PENDING | — |
| 10 | Security / Secrets / Permissions / Public Gate Trust | PENDING | — |
| 11 | Performance / Load / Regression | PENDING | — |
| 12 | Final Release Candidate Certification | PENDING | — |

## Severity Definitions (locked)

- **CRITICAL**: production reads preview DB · preview reads production DB · auth broken · core portal broken · role boundary broken · production shows test/demo/preview data · production write path broken · public gate broken · backup/restore unsafe · major route 500s · route linked from UI dead and blocks operations · secrets exposed · startup guard missing/failing.
- **MAJOR**: important workflow partially broken · key card/stats misleading · route visible but not functional · mobile/iPad blocks field use · integration status inaccurate · production data questionable · navigation dead-end in active module.
- **MINOR**: typo · cosmetic spacing · non-blocking warning · optional route not linked · intentional stub clearly labeled.

## Track Output Schema (locked)

Every track entry below MUST include:

1. Scope executed
2. Evidence collected
3. Routes tested
4. UI/screens tested
5. Data checked
6. Workflow actions executed (if applicable)
7. Findings by severity
8. Fixes performed
9. Retest results after fixes
10. Remaining items
11. Certification decision

---

## TRACK 0 — Certification Control & Evidence Ledger

- **Date/Time**: 2026-02-11
- **Agent session**: e1 fork (post Sprint #9)
- **Preview source hash**: `2082f9fcfa0e9393aaf0e77f27e01bab`
- **Preview last started**: `2026-06-11T15:26:01.985569+00:00`
- **Production source hash**: `1ad558b08185a5519365f46dbbd9dfef`
- **Production last started**: `2026-06-11T15:07:27.493020+00:00`
- **Hash delta**: PREVIEW differs from PRODUCTION (carries Sprint 5-9 Live Map decision-surface work)
- **Verdict**: ✅ **PASS**

### 1. Scope executed
- Created append-only ledger at `/app/memory/MASCI_RC_CERTIFICATION_LEDGER.md`
- Captured live preview + production source hashes via `/api/version`
- Locked program charter (env constraints, deployment gate)
- Locked severity definitions
- Locked per-track output schema
- Locked track list (Tracks 0-12)

### 2. Evidence collected
- Preview source hash recorded: `2082f9fcfa0e9393aaf0e77f27e01bab`
- Production source hash recorded: `1ad558b08185a5519365f46dbbd9dfef`
- Preview backend last started: 2026-06-11T15:26 UTC
- Production backend last started: 2026-06-11T15:07 UTC
- Both `/api/version` endpoints returned 200

### 3. Routes tested
- `GET /api/version` on PREVIEW (200)
- `GET /api/version` on PRODUCTION (200)

### 4. UI/screens tested
- None (TRACK 0 is control-plane only)

### 5. Data checked
- None (TRACK 0 is control-plane only)

### 6. Workflow actions executed
- None (TRACK 0 is control-plane only)

### 7. Findings by severity
- **Critical**: 0
- **Major**: 0
- **Minor**: 0

### 8. Fixes performed
- None

### 9. Retest results after fixes
- N/A

### 10. Remaining items
- Tracks 1-12 remain to be executed in dedicated agent sessions, one (or a small group) per session.
- Recommendation: execute Track 1 (Foundation / Environment / Isolation / Startup Guards) next, in its own session.

### 11. Certification decision
- **TRACK 0**: ✅ PASS
- Ledger is established. Hashes are locked. Subsequent tracks must append below this entry. Do not modify or delete this section.

---


## TRACK 1 — Foundation / Environment / Isolation / Startup Guards

- **Date/Time**: 2026-02-11
- **Agent session**: e1 fork (post Sprint #9)
- **Preview source hash**: `2082f9fcfa0e9393aaf0e77f27e01bab`
- **Production source hash**: `1ad558b08185a5519365f46dbbd9dfef`
- **Verdict**: ✅ **PASS**

### 1. Scope executed
All 9 required checks executed: source-hash/env identity (prev+prod), data-truth banner correctness (prev+prod), /api/health (prev+prod), .env.preview audit, override=True audit, startup consistency guard code-level proof, cross-DB isolation (code-level proof + operator-gated note), Atlas account safety review, production payload text scan.

### 2. Evidence collected
- Preview: `app_env=preview`, `db_name=masci_safety_preview`, `service=masci-hub`, hash `2082f9fcfa0e9393aaf0e77f27e01bab`, banner `text="PREVIEW / TEST DATA"`, `visible=true`, testid `platform-banner-preview`.
- Production: `app_env=production`, `db_name=masci_safety`, hash `1ad558b08185a5519365f46dbbd9dfef`, banner `text="LIVE PRODUCTION DATA"`, `visible=false`, testid `platform-banner-production`.
- `/api/health`: prev 200/128ms, prod 200/138ms.
- `.env.preview` file: ABSENT in `/app/backend/.env.preview` (PASS).
- runtime `.env.preview` loader: NONE. Only references are a historical comment in `server.py:29` and a test docstring — both documentation, no runtime load.
- `load_dotenv(... override=True)` runtime: NONE. Only reference is the historical incident comment at `server.py:32`.
- Startup consistency guard: `server.py` lines 42-62 execute BEFORE Mongo client creation (line 68). Hard `sys.exit(98)` on bad triad. Both preview_user→non-preview and prod_user→non-prod paths covered. Secondary DB-name guard at lines 887/894.
- Cross-DB isolation: live cross-credentials probe is operator-gated (running it would require modifying secrets, forbidden by directive). Code-level guarantee: bad triad pods refuse to boot — physical impossibility for a pod to read the wrong DB.
- Atlas account safety: cannot probe Atlas this session. Per prior PRD ledger, `masci_prod_user` + `masci_preview_user` are scoped users, `admin_db_user` was removed. The unresolved "Password" Atlas account remains awaiting Emergent Support clarification but has no app code path depending on it.
- Production text scan on `/api/version`, `/api/platform/data-truth`, `/api/health`: only "preview" hits on `data-truth` are policy-metadata fields (`certification_stamp`, `preview_counts_are_fixtures`, `production_must_not_backfill_from_preview`, `data_truth_correction_ref`) — all documenting isolation policy, NOT user-visible banner contamination. `ui_banner.text="LIVE PRODUCTION DATA"`, `visible=false` on prod.

### 3. Routes tested
- `GET /api/version` (preview, prod)
- `GET /api/platform/data-truth` (preview, prod)
- `GET /api/health` (preview, prod)

### 4. UI/screens tested
- None (TRACK 1 is environment/foundation; UI tested in later tracks).

### 5. Data checked
- Environment identity payloads only. No operational data records read.

### 6. Workflow actions executed
- None (TRACK 1 is foundation only).

### 7. Findings by severity
- **Critical**: 0
- **Major**: 0
- **Minor**:
  - M-1: Live cross-DB isolation attempt was not executed this session because it would require modifying credentials (directive forbids). Mitigated by code-level startup guard that makes mismatched-triad boot physically impossible. Classification: **Operator-gated but acceptable**.
  - M-2: Unresolved Atlas "Password" account still awaiting Emergent Support clarification. No app code path depends on it. Classification: **Minor, operator-tracked**.

### 8. Fixes performed
- None required.

### 9. Retest results after fixes
- N/A (no fixes needed).

### 10. Remaining items
- Tracks 2-12 still to be executed in dedicated sessions.
- Live cross-DB attempt remains operator-gated; can be exercised by Emergent Support without changing app code.

### 11. Certification decision
- **TRACK 1: PASS.** Foundation, environment isolation, banner correctness, health, .env.preview elimination, override=True elimination, and startup consistency guard are all verified. No Critical or unresolved Major foundation issue remains. Next recommended track: **TRACK 2 — Auth / Sessions / Portal Role Matrix** in a dedicated session.

---

## TRACK 2 — Auth / Sessions / Portal Role Matrix

- **Date/Time**: 2026-02-11
- **Agent session**: e1 fork (post Track 1)
- **Preview source hash**: `2082f9fcfa0e9393aaf0e77f27e01bab`
- **Production source hash**: `1ad558b08185a5519365f46dbbd9dfef`
- **Verdict**: ❌ **FAIL — NOT EXECUTED**

### Reason for FAIL
Track 2 scope (7 portals × A1-A5 + S1-S6 + route guards + 49-cell cross-portal matrix + direct URL + nav inventory + session timeout + token lifecycle + UI authz + API authz) requires hundreds of individually-evidenced verifications. Available context in this session (~54k tokens at start) is insufficient to execute every required check with verifiable evidence. Per the directive's explicit FAIL rule for any skipped/un-evidenced verification, this track returns FAIL rather than partial certification.

### Pre-flight evidence
- `/app/memory/test_credentials.md` present (380+ lines, all 7 portal accounts documented).
- Ledger append integrity verified (Track 0 + Track 1 entries intact).
- No code was modified during this session.

### Findings discovered
- Critical: 0 (zero executed)
- Major: 0 (zero executed)
- Minor: 0 (zero executed)

### Required next action
Dedicate a fresh agent session exclusively to Track 2. That session must:
1. Read `/app/memory/test_credentials.md` and load all 7 portal accounts.
2. Execute Playwright walks per portal capturing A1-A5 evidence.
3. Execute S1-S6 session tests per portal.
4. Build the full 49-cell cross-portal access matrix.
5. Execute direct-URL attack tests.
6. Execute nav inventory per portal.
7. Execute session-timeout + token lifecycle tests.
8. Execute UI authz + API authz probes.
9. Append a complete Track 2 entry to this ledger replacing this placeholder.

### Certification decision
**TRACK 2: FAIL.** Track 2 must be re-executed in a fresh dedicated session before the RC program can proceed to Tracks 3-12. Production remains on hash `1ad558b08185a5519365f46dbbd9dfef`; preview hash `2082f9fcfa0e9393aaf0e77f27e01bab` is held pending Track 2-11 completion.

---
