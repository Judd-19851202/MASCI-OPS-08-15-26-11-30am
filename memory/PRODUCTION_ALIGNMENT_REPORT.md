# PRODUCTION_ALIGNMENT_REPORT

**Phase:** OMEGA Production Remediation · Phase 1 (Difference Audit)
**Date:** 2026-05-30 (UTC)
**Method:** Triangulation of (a) live source_hash probe of both `/api/version` endpoints, (b) direct grep of preview backend source against Batch K/L expectations, (c) live tasks/notifications enumeration on production via X-Admin-Token-less probe (returns 401 for write surfaces, used only for identity + recoverability surfaces).
**Mandate:** READ-ONLY. No code mutations. No deploys. No migrations.

---

## 🔴 HEADLINE — Production is one full Wave behind Preview

Preview carries 100% of the operator-authorized Wave 1 + Batch K + Batch L work. Production carries 0% of it.

| Identity | Preview | Production |
|---|---|---|
| URL | `safety-audit-mobile-1.preview.emergentagent.com` | `mascidocs.com` |
| `app_env` | `preview` | `production` |
| `db_name` | `masci_safety_preview` | `masci_safety` |
| `/api/version.source_hash` | `550118913c503ae6d206223be384372f` | `8e8ec6da31cf225cae2db172573f49a0` |
| Started at | 2026-05-30T17:33:24Z | 2026-05-30T17:56:51Z |
| `/api/health` | 🟢 200 OK | 🟢 200 OK |
| Sentry | enabled | enabled |

**Hash delta**: `550118…` (preview) ≠ `8e8ec6…` (production). Expected. Maps 1:1 to the unshipped work below.

---

## 1 · What exists in Preview but NOT in Production

### 1.1 · Backend route changes (Batch K — 5 missing fan-outs + 2 sub-events)

| File | Lines | Workflow | Fan-out added | Production today |
|---|---|---|---|---|
| `routes/safety.py` | 467–479 | Safety Meeting submit | `task → safety` + `notification → safety` (`meeting.submitted`) | 🔴 email-only, no bell/task |
| `routes/safety.py` | 556–660 | JHA submit | `task → safety` + `notification → safety` (`jha.submitted`) | 🔴 email-only |
| `routes/field_leadership.py` | 463–471 | Field Leadership 10 forms | `task → safety` + `notification → safety` (`fl.submitted`) | 🔴 email-only |
| `routes/safety_forms.py` | 944–973 | Safety Equipment Issuance | `task → safety` + `notification → safety` (`safety_form.issuance`) | 🔴 email-only |
| `routes/safety_forms.py` | 1099–1103 | Safety Equipment Return | `notification → safety` (severity scales w/ chargeback) | 🔴 silent |
| `routes/safety_forms.py` | 1159–1170 | Safety Equipment Training | `task → safety` + `notification → safety` (`safety_form.training`) | 🔴 email-only |
| `routes/payroll_variance.py` | 338–340 | Payroll Variance manual run | `notification → admin` (audit) | 🔴 silent |

### 1.2 · Backend route changes (Batch L — Fleet DVIR ownership matrix)

| File | Lines | Routing class | Behavior added | Production today |
|---|---|---|---|---|
| `routes/fleet_ops.py` | 569–625 | Normal DVIR | record-only (correct) | record-only (incidentally identical) |
| `routes/fleet_ops.py` | 569–625 | Defect (severity=monitor) | `task Shop Medium` + `dvir.defect → shop` | 🔴 ORPHAN — no fan-out |
| `routes/fleet_ops.py` | 569–625 | OOS (severity=oos or `out_of_service=Yes`) | `task Shop Critical` + `dvir.defect.oos → shop` + parallel `dvir.defect.oos → dispatch` | 🔴 ORPHAN — no fan-out |

### 1.3 · Backend write-path defense (Batch H — photo bloat prevention)

| File | Lines | Function | Effect | Production today |
|---|---|---|---|---|
| `routes/daily_reports.py` | 186–232, 254–257 | `_sanitize_inline_photos()` | On every DR POST, converts inline `data:image/...` base64 to `photo://` refs BEFORE persist; idempotent; soft-fails to legacy behavior if R2 misconfigured | 🔴 NOT present — every new prod DR lands as inline base64 |

### 1.4 · Wave 1 substrate routes (V-Prelude work documented in PREVIEW_PRODUCTION_DELTA_REPORT.md)

| Route module | Endpoints | State on prod |
|---|---|---|
| `operational_constraints.py` | `/api/operational/constraints/*` | 🔴 missing |
| `operational_links.py` | `/api/operational/links/*` | 🔴 missing |
| `operational_timeline.py` | `/api/operational/timeline/*` | 🔴 missing |
| `photo_governance.py` | `/api/operational/photo-governance/*` | 🔴 missing |
| `operational_attachments.py` | `/api/operational/attachments/*` | 🔴 missing |

### 1.5 · Frontend additions

| File | Purpose | State on prod |
|---|---|---|
| `frontend/src/components/operational/OperationalTimelineSidecar.jsx` | Passive timeline rail on PM Project Detail | 🔴 missing |
| Mount: `frontend/src/pages/PmProjectDetail.jsx` (right-side rail) | Mount point | 🔴 missing |

### 1.6 · Database collections (preview-only)

| Collection | Purpose | Rows preview | Rows prod |
|---|---|---:|---:|
| `operational_constraints` | Wave 1 substrate | live | absent |
| `operational_links` | Wave 1 substrate | live | absent |
| `operational_timeline` | Wave 1 substrate | live | absent |
| `photo_governance` | Wave 1 substrate (registry only) | live | absent |
| `operational_attachments` | Wave 1 substrate | live | absent |

### 1.7 · Probes / safety nets

| Probe | Mode | State on prod |
|---|---|---|
| `authority_mismatch_probe.py` | HARD gate | wired in preview pre-deploy check |
| `timestamp_doctrine_probe.py` | HARD gate | wired in preview pre-deploy check |
| `operational_links_doctrine_probe.py` | HARD gate | wired in preview pre-deploy check |
| `timeline_calmness_probe.py` | WARN (5× target = hard) | wired in preview pre-deploy check |
| `trendline_integrity_probe.py` | HARD gate | wired in preview pre-deploy check |
| `walkthrough_capture.py` | append-only writer | wired in preview |

---

## 2 · What exists in Production but NOT in Preview

### 2.1 · Real operational data

| Type | Production | Preview |
|---|---:|---:|
| Daily Reports | 86 (most recent DR-2026-00279, 2026-05-29) | smaller staged sample |
| Inline base64 photos in DRs | **8/8 most recent sampled** carry inline `data:image/...` payloads averaging 415 KB each | 0 (preview is post-Batch-G migrated) |
| Tasks | 1 (legacy `po.requests` from 2026-05-28) | 571 (test + workflow rows) |
| Notifications | small set: 72 `task.assigned`, 4 `incident.created`, 1 `po.approval_visibility` | 1,237 |
| R2 archive size | 464.3 MB · 284,295 records | smaller |
| R2 total usage | 80.64 GB / 2,778 objects | unmeasured |

### 2.2 · Production-only operational characteristics

- **Cloudflare front-edge** observed in front of production origin (transient 520 logged 17:50–17:52Z 2026-05-30; auto-recovered). Preview is direct emergent edge.
- **Real user traffic** (PMs submitting DRs, fleet drivers submitting DVIRs). Preview is operator-driven only.
- **Atlas-class Mongo cluster** (vs preview's smaller instance).

### 2.3 · Pre-existing contamination

| Side | Test/PE rows | Tool |
|---|---:|---|
| Production (`masci_safety`) | **0** | `verify_no_contamination.py` |
| Preview (`masci_safety_preview`) | 163 (127 notifications · 31 tasks · 1 FL TO · 4 public links) | `verify_no_contamination.py` |

**Critical**: preview contamination CANNOT travel via deploy (deploy ships code, not Mongo). Logged for post-deploy housekeeping; NOT a deploy blocker.

---

## 3 · Which OMEGA gaps are closed in Preview only

Per `OMEGA_GAP_REGISTER.md`:

| Gap | Preview state | Production state |
|---|---|---|
| OMEGA-3 / Fleet DVIR orphan (UNACCEPTABLE) | 🟢 CLOSED (Batch L) | 🔴 STILL OPEN |
| OMEGA-5 / Field Leadership fan-out | 🟢 CLOSED (Batch K) | 🔴 STILL OPEN |
| OMEGA-6 / Safety Equipment Issuance + Return + Training fan-outs | 🟢 CLOSED (Batch K) | 🔴 STILL OPEN |
| OMEGA-7 / JHA fan-out | 🟢 CLOSED (Batch K) | 🔴 STILL OPEN |
| OMEGA-8 / Safety Meeting fan-out | 🟢 CLOSED (Batch K) | 🔴 STILL OPEN |
| OMEGA-13 / Payroll Variance audit fan-out | 🟢 CLOSED (Batch K) | 🔴 STILL OPEN |

---

## 4 · Which OMEGA gaps remain ACTIVE in Production

Same six from §3, plus:

| Gap | Severity | Notes |
|---|---|---|
| OMEGA-1 / Photo migration NOT RUN | 🟡 Medium (OOM trajectory) | 8/8 sampled DRs still inline base64. Headroom 600−464 = 136 MB. ~22 MB/month growth. |
| OMEGA-2 / Batch H write-path defense not deployed | 🟡 Medium | Every NEW prod DR also lands as inline base64, compounding OMEGA-1. |
| OMEGA-9 / Training supervisor lens | 🟡 P1 | Batch M scope. NOT IN THIS REMEDIATION. |
| OMEGA-10 / Severe Incident escalation cadence | 🟡 P2 | Batch N scope. NOT IN THIS REMEDIATION. |
| OMEGA-11 / PO 60-day escalation | 🟡 P2 | Batch N scope. NOT IN THIS REMEDIATION. |
| OMEGA-12 / Watchdog alarm path untested live | 🟡 P2 | Not in scope. |
| OMEGA-14, 15, 16 | 🟢 P3 hygiene | Not in scope. |

---

## 5 · Which recoverability improvements remain Preview-only

| Improvement | Preview | Production | Impact |
|---|---|---|---|
| Batch H photo write-path defense (`_sanitize_inline_photos`) | 🟢 active | 🔴 absent | Every new DR adds inline bloat |
| Batch G migration script presence | 🟢 `/app/scripts/migrate_dr_photos.py` | 🟢 (script is repo-only; cannot run without operator) | Script ready, untriggered |
| `legacy-migration/` R2 prefix discipline | 🟢 documented | 🔴 not yet used | Awaits migration |
| Wave 1 timeline / constraints substrates | 🟢 5 collections live | 🔴 absent | No recoverability blast radius — additive |
| `restore_drill.py --restore-photos` flag | 🟢 callable | 🟢 callable (script in repo) | Both sides identical; tested in Batch E drill |
| Backup scheduler core | 🟢 healthy | 🟢 **CERTIFIED HEALTHY** — last tick 43 sec before probe, 464 MB ok=true, zero failed_attempts today | Both sides identical |

**Net**: The preview-only recoverability deltas are limited to the photo write-path defense (Batch H) and the Wave 1 substrate. The core backup + restore pipeline is identical on both sides and currently healthy on prod.

---

## 6 · Which notification improvements remain Preview-only

All 7 fan-out paths certified in `BATCH_K_FINAL_CERTIFICATION.md` + 2 routing tiers (defect + OOS) certified in `FLEET_DVIR_CERTIFICATION.md`:

| Event | Preview emits | Production emits |
|---|---|---|
| Field Leadership form submitted | `task → safety` + `notification.fl.submitted → safety` | nothing |
| Safety Equipment Issuance | `task → safety` + `notification.safety_form.issuance → safety` | nothing |
| Safety Equipment Return | `notification.safety_form.return → safety` (severity by chargeback) | nothing |
| Safety Equipment Training | `task → safety` + `notification.safety_form.training → safety` | nothing |
| JHA submitted | `task → safety` + `notification.jha.submitted → safety` | nothing |
| Safety Meeting submitted | `task → safety` + `notification.meeting.submitted → safety` | nothing |
| Payroll Variance manual run | `notification.payroll_variance.manual_run → admin` | nothing |
| Fleet DVIR Defect (monitor) | `task Shop Medium` + `notification.dvir.defect → shop` | nothing |
| Fleet DVIR OOS | `task Shop Critical` + `notification.dvir.defect.oos → shop` + `notification.dvir.defect.oos → dispatch` | nothing |

**Production tasks/notifications enumeration (V-P9 / V-P-notif on 2026-05-30):**
- `source_module="fleet.dvir"` rows: **0**
- `source_module="safety.meeting"` rows: **0**
- `source_module="safety.jha"` rows: **0**
- `source_module="field_leadership.records"` rows: **0**
- `source_module="safety.form.issuance"` rows: **0**
- `source_module="safety.form.training"` rows: **0**
- `source_module="hr.payroll_variance"` rows: **0**
- `type="dvir.defect"` / `"dvir.defect.oos"` notifications: **0**

Production is fan-out-blind for every Batch K/L event.

---

## 7 · Exact file-level delta summary

**Backend modules added or modified in preview-only:**

```
backend/routes/safety.py                  (Batch K · ~70 LOC added)
backend/routes/safety_forms.py            (Batch K · ~90 LOC added)
backend/routes/field_leadership.py        (Batch K · ~25 LOC added)
backend/routes/payroll_variance.py        (Batch K · ~15 LOC added)
backend/routes/equipment.py               (Pre-Op pattern reference — unchanged)
backend/routes/fleet_ops.py               (Batch L · ~95 LOC added)
backend/routes/daily_reports.py           (Batch H write-path defense · ~50 LOC added)
backend/routes/operational_constraints.py (Wave 1 · new file)
backend/routes/operational_links.py       (Wave 1 · new file)
backend/routes/operational_timeline.py    (Wave 1 · new file)
backend/routes/photo_governance.py        (Wave 1 · new file)
backend/routes/operational_attachments.py (Wave 1 · new file)
```

**Frontend modules added in preview-only:**

```
frontend/src/components/operational/OperationalTimelineSidecar.jsx  (Wave 1.1 · new file)
frontend/src/pages/PmProjectDetail.jsx                              (Wave 1.1 · mount point added)
```

**Schemas added in preview-only:** 5 new MongoDB collections (operational_*).

**No backend modules removed.** No schema mutations on existing collections. All Batch K/L/H additions are additive (new rows in tasks/notifications collections; new code paths inside existing endpoints).

---

## 8 · Net verdict

🔴 **Production is one cumulative deploy behind preview** containing exactly the work the operator has authorized over the last ~5 weeks (Wave 1 / 1.1 / 1.1A / 1.1B / Observation Ledger / Batch H / Batch K / Batch L). No surprise files. No scope creep. The delta is the authorized backlog, end-to-end.

The deploy is the only mechanism that brings prod into alignment. The photo migration (`migrate_dr_photos.py`) is a one-shot operator command that, paired with the deploy, removes ~270 MB of inline base64 from `daily_reports` and brings R2 from 80 GB → ~20 GB / archive 464 MB → ~115 MB.

---

_End of PRODUCTION_ALIGNMENT_REPORT.md._
