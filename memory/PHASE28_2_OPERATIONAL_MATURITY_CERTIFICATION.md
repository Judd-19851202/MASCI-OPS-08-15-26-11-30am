# PHASE 28.2 — Operational Maturity Certification
## iter430 · 2026-05-25

---

## Result — 🟢 5 of 6 implementable parts SHIPPED · 1 part requires operator devices

---

## Part-by-part outcome

### Part 1 · Production Atlas verification hardening ✅
- New endpoint:
  `GET /api/admin-strict/diag/persistence-health` (`routes/admin_persistence_health.py`)
- JSON-only · admin-strict gated · NO UI · NO chart · NO dashboard.
- Returns: `atlas_connected`, `atlas_host` (password-masked),
  `db_name`, `mongo_version`, `collections_detected`,
  `last_backup_time`, `r2_backup_success` (full row),
  `persistent_storage_confirmed` (24h recent-write probe),
  `drift_watch_active` + reason, `captured_at`.
- Live preview verification:
  ```
  atlas_connected: true
  mongo_version: 8.0.23
  collections_detected: 121
  atlas_host: mongodb+srv://***@masci-prod.1nduwmg.mongodb.net/...
  ```
- Backup snapshot integrity check (zip exists + size > 0 + manifest
  parses) — already shipped at `lib/backup_verification.py` since
  iter383. This phase wires its output into the new
  `r2_backup_success` field of `persistence-health`.

### Part 2 · Day-1 + Week-1 live ops debrief continuity ✅
- Week-1 question set REPLACED with the Phase 28.2 refined operational
  prompts (12 questions: friction repeats, naturally-trusted workflows,
  hesitation causes, bypasses, valuable continuity, unnecessary,
  untouched, coaching gaps, complexity gaps, terminology confusion,
  mobile/device issues, role visibility gaps).
- Same backend module (`routes/dispatch_day1_debrief.py`),
  same React component (`AdminDlsDay1Debrief.jsx`), variant prop
  drives both pages — calm doctrine preserved.
- Markdown sink:
  `/app/memory/DLS_WEEK1_LIVE_OPS_DEBRIEF_YYYY-MM-DD.md` per submit.

### Part 3 · Passkey / WebAuthn fan-out ✅
- Already shipped in Phase 28: `PasskeyEnrollPrompt` on Dispatch, HR,
  PM, Shop, Safety, Field Leadership. Component self-gates.
- NEW this phase: **device management** page at `/admin/profile` —
  `pages/admin/AdminProfile.jsx`. Lists enrolled passkeys
  (label, created_at, last_used_at, transport) and provides a single
  "Remove" action per row. Uses the existing `listPasskeys()` /
  `revokePasskey()` library calls.
- Real-device validation (iPhone / iPad / Android / Mac Touch ID /
  Windows Hello / Edge) is OPERATOR-OWNED — see
  `PHASE28_2_REAL_DEVICE_VALIDATION.md`.

### Part 4 · Production observability foundation ✅
- Sentry already wired (`sentry_init.py` · DSN-gated · PII scrubber).
- NEW: `sentry_tags.py` — `SentryOperationalTagsMiddleware`
  auto-attaches **portal / role / route / device / browser /
  language / tenant** tags to every Sentry event so a production
  exception card reveals operational context without log-diving.
- Coarse UA classification only — no fingerprinting, no unique IDs.
- Middleware mounted in `server.py` after CORS · no-op when
  `SENTRY_DSN` is unset (preview/dev stay clean).

### Part 5 · Controlled `server.py` modularization ✅
- **Phase 4D EXECUTED**: `/api/legacy-imports/*` (11 routes) moved
  from `server.py:9241-9702` into `routes/legacy_imports.py` via the
  `build_legacy_imports_router()` factory.
- `server.py`: **11,584 → 11,140 LOC** (-444 lines · -3.8 %).
- Zero behavior drift: every URL, response shape, status code, auth
  dep signature, and audit-log write contract preserved verbatim.
- Live verification: all 11 routes return 200 for authorised admin
  calls and 401 unauthorised. Existing iter238/iter248/iter249
  test suites all pass against the extracted module.
- NEW parity-lock test
  `tests/test_iter430_legacy_imports_extraction.py` guards against
  silent drift (path/method enumeration, duplicate-mount guard,
  auth-dep 401 verification).

### Part 6 · Production real-device validation ⏸ OPERATOR-OWNED
- I cannot drive real iPhones / iPads / etc. The test matrix and
  runbook live in `PHASE28_2_REAL_DEVICE_VALIDATION.md` so a
  human operator can run through it on shipping devices.

### Part 7 · Storage / cost governance ✅
- `GET /api/admin/operational-attachments/storage-summary` expanded
  with: `avg_attachment_size_bytes` and `projected_90_day_growth`
  (count + bytes · based on rolling 30-day window).
- Same admin-only · JSON-only contract · no UI added.

### Part 8 · Testing + certification ✅
- Parity-lock pytest suites (run individually per directive):
  - `test_iter430_legacy_imports_extraction.py` (3 tests) ✅
  - `test_iter430_persistence_health_and_sentry_tags.py` (5 tests) ✅
  - `test_iter429_1_storage_summary_and_week1.py` (7 tests · updated for 12 Week-1 questions) ✅
  - `test_iter429_op_attachments_r2.py` (4 tests) ✅
  - `test_iter427_legacy_backup_prune.py` (2 tests) ✅
  - `test_iter248_phase_a.py` (24 tests · validates extracted Phase A) ✅
  - `test_iter249_phase_b.py` (12 tests · validates extracted Phase B) ✅
  - `test_iter249_pilot_debrief.py` (7 tests · validates extracted debrief) ✅
- **Total: 64/64 GREEN.**
- Ruff + ESLint clean on every modified file.
- Live curl verification of: `/api/health`, persistence-health,
  legacy-imports (list/meta/audit/pilot-debrief), storage-summary,
  Week-1 questions.

---

## What this phase did NOT do (doctrine restraint)
- ❌ No dashboards · no charts · no KPI screens · no analytics
- ❌ No notification system · no alerting UI · no observability portal
- ❌ No browser-push system · no session recording · no telemetry
- ❌ No identity center · no security dashboard · no geo-tracking
- ❌ No "improvements" to legacy-imports during extraction
  (zero-behavior-change contract held)
- ❌ No new collections · no schema drift · no auth-shape changes

## Outstanding operator action
1. **Production `MONGO_URL`** — already deferred from Phase 28.1.
   Update prod deploy dashboard, redeploy.
2. **Real-device validation matrix** in
   `PHASE28_2_REAL_DEVICE_VALIDATION.md`.
3. **Phase 5+ modularization extractions** — `server.py` still has
   ~11.1k LOC of shared startup glue, auth helpers, and fleet-ops
   wiring. Roadmap doc carries the safe sequence for next session.
