# M0.2 + M0.2A · Operator Review Guide

_Phase V.1 · 2026-05-29 · pre-pilot review checkpoint._

The operator directive after M0.1 was unambiguous:

> "After M0.2 + M0.2A: **STOP.** Do NOT begin M0.3, Migration,
> Dual-write, Pilot rollout. Await operator review."

This guide is the briefing for that review. It is intentionally
short. Read it top-to-bottom in ~5 minutes. Then decide whether to
authorize M0.3.

---

## 1 · What shipped in this wave

| Component | Module | Status |
|---|---|---|
| Public Link Continuity Engine | `routes/odr/continuity.py` | 🟢 LIVE |
| Amendment Engine | `routes/odr/amendments.py` | 🟢 LIVE |
| PDF Rendering Framework | `routes/odr/pdf.py` | 🟢 LIVE |
| OGC Catalog Seed | `routes/odr/guidance_catalog.py` | 🟢 14 prompt_keys · ≥4 EN/ES |
| Crew Readiness Matrix | `routes/odr/crew_readiness_matrix.py` | 🟢 21 crews |
| Guidance Intelligence Foundation | `routes/odr/guidance_routes.py` | 🟢 deterministic |
| Public-Link Continuity Probe | `scripts/odr_public_link_continuity_probe.py` | 🟢 8 invariants |
| Bilingual Probe | `scripts/odr_bilingual_probe.py` | 🟢 7 invariants |

All wired into `pre_deploy_check.sh` as hard-blocking stages.

## 2 · What I would test myself first

1. **Pull `GET /api/odr/guidance/prompts`** — confirm you see 14 keys.
2. **Pull `GET /api/odr/guidance/resolve?prompt_key=production.add_first_segment&crew_type=pipe&lang=en`** — confirm 4 pipe-specific EN bullets render in a tone you'd accept on a foreman tooltip.
3. **Pull `GET /api/odr/guidance/resolve?prompt_key=safety.report_every_event&crew_type=any&lang=es`** — confirm the Spanish is field-usable.
4. **Open a PDF** via `GET /api/odr/{id}/pdf?audience=external` and read it like a CEI rep would. If you see anything you wouldn't want to hand to FDOT, flag it.
5. **Mint then revoke a public link**:
   - `POST /api/odr/{id}/link` → record `link_id`
   - `GET /api/odr/public/{doc_id}?link_id={link_id}` → 200
   - `PATCH /api/odr/public-links/{link_id}` with `{"revoke": true}`
   - `GET /api/odr/public/{doc_id}?link_id={link_id}` → 410 (Gone)

## 3 · What this wave does NOT do (intentional)

- ❌ NO frontend. No UI changes. No new pages. M0.3 is the UI wave.
- ❌ NO RFI. NO Schedule. NO P6. NO AI copilot. NO new role models.
- ❌ NO dashboard expansion. NO migration. NO dual-write. NO pilot.
- ❌ NO production deploy. Preview only.

## 4 · What is still required before pilot

| Item | Owner | Wave |
|---|---|---|
| `/odr/new` foreman entry UI | Frontend agent | M0.3 |
| FL ODR Center (inbox + amendment route + diff viewer) | Frontend agent | M0.3 |
| PM consumption panel (cost+contract lens) | Frontend agent | M0.3 |
| Public link rendering page (`/odr/public/:doc_id`) | Frontend agent | M0.3 |
| Migration plan execution (legacy `daily_reports` → ODR) | Migration agent | M1 |
| Dual-write pilot | Migration agent | M1 |

## 5 · Doctrine compliance audit

| Doctrine | Inherited? | Evidence |
|---|---|---|
| FIELD_LEADERSHIP_VISIBILITY_DOCTRINE | ✅ | PDF audience projection · public envelope strip · guidance lookups respect resolve_fll |
| OPERATIONAL_LINKING_RULES | ✅ | M0.1 carried over · M0.2 adds no new artifact_type writes (uses existing types) |
| TIMELINE_DOCTRINE | ✅ | M0.1 carried over · no timeline writes in M0.2 (continuity ≠ chronology) |
| ODR_COACHING_GUIDANCE_ADDENDUM | ✅ | OGC catalog is the source-of-truth for coaching content; readiness emits prompt_key references only |
| ROLE_AWARE_VISIBILITY_MODEL | ✅ | PDF endpoint enforces portal-role for external/executive/pm; public resolver never returns telemetry / consumer_dispatch / device fingerprint |

## 6 · Test surface

| Suite | Pass |
|---|---|
| `tests/odr/test_odr_substrate.py` | 12/12 |
| `tests/odr/test_odr_m02.py` | 24/24 |
| `tests/test_v_prelude_wave1_substrate.py` + `tests/test_v_prelude_wave1_1_sidecar.py` (regression) | 27/27 |
| `scripts/odr_public_link_continuity_probe.py --gate` | ✅ 0 failures |
| `scripts/odr_bilingual_probe.py --gate` | ✅ 0 failures |
| `ruff check backend/routes/odr/ scripts/odr_*.py` | ✅ clean |

**Total ODR + regression coverage: 63 tests + 2 probes · 0 failures.**

## 7 · What I want approval on before M0.3

- [ ] Tone of the OGC catalog (sample bullets in §2 above).
- [ ] PDF external-audience field redaction (open the actual PDF).
- [ ] Amendment authority matrix (foreman in-window vs Super+ post-window).
- [ ] Public-link mint authority (Admin + PM only — not FL by default).

If anything in the above feels off, the catalog and authority gates
are the cheapest things to change in the entire wave. The frontend
agent will inherit whatever you bless here.

## 8 · Stop condition acknowledged

🛑 **HALTED at end of M0.2 + M0.2A as directed.**

Awaiting operator instruction to authorize M0.3.

_End of M0.2A Operator Review Guide._
