# M1 Operator Review Guide · Option C

_Phase V.1 · M1 · 2026-05-29 · final pre-pilot review checkpoint._

> Read top-to-bottom in ~6 minutes. By the end of §10 you have
> everything needed to authorize (or hold) the pilot.

This guide supersedes `UPDATED_OPERATOR_REVIEW_GUIDE.md` for the
purposes of the **pilot authorization decision.** It folds in the
M1 (Option C) work and confirms the historical preservation
contract.

---

## 1 · State of the substrate

| Wave | Scope | Status |
|---|---|---|
| M0.0 | Hygiene closure | ✅ Closed |
| M0.1 | Substrate sealed | ✅ Sealed |
| M0.2 | Continuity Engine + Amendment Engine + PDF v1 | ✅ Live |
| M0.2A | OGC Catalog + Crew Readiness Matrix + Probes | ✅ Live |
| M0.3 | Operator surfaces (Foreman / FL Center / PM Panel / Public Viewer) | ✅ Live |
| M0.35 | Audience Projection Doctrine + Reality Validation + 2 Doctrine Locks | ✅ Closed |
| M0.4 | External PDF photo thumbnail embedding | ✅ Closed |
| **M1** | **Frozen Archive + Forward-Only ODR + Unified Read Experience** | ✅ **This wave** |

## 2 · M1 in 60 seconds

Six moves, no migration:

1. **Daily Report write freeze** — POST and DELETE return calm `410 Gone` directing operators to `/odr/new`. All read paths remain live forever.
2. **Unified records projector** — `GET /api/operational-records` merges ODR + frozen Daily Reports into one envelope with `record_kind` and `archive` flags. Counts are honest. Sort is newest-first across both substrates.
3. **Doc id router** — `GET /api/operational-records/resolve/{doc_id}` routes `DR-*` → legacy viewer, `ODR-*` → ODR viewer.
4. **Operational links bridge** — `legacy_daily_report` registered as a **target-only** artifact in `operational_links`. ODR rows can reference legacy ancestors; legacy rows can never become sources.
5. **Archive visual treatment** — calm, slate, single-source `<ArchiveBadge>` + `<ArchiveExplainerCard>` components. No alarm language. No warning colors.
6. **Read-only historical preservation** — verified by an explicit `count_documents` test that proves zero mutation across every freeze path.

**Zero lines of code mutate the legacy substrate.**

## 3 · What was explicitly NOT done (per directive)

| Prohibited | Status |
|---|---|
| Convert legacy reports | ❌ NOT DONE |
| Rewrite signatures | ❌ NOT DONE |
| Remap signed content | ❌ NOT DONE |
| Infer missing enums | ❌ NOT DONE |
| Alter historical PDFs | ❌ NOT DONE |
| Move historical photos | ❌ NOT DONE |
| Regenerate historical audit trails | ❌ NOT DONE |
| Create historical ODR records | ❌ NOT DONE |
| Migration script | ❌ NOT WRITTEN |
| Dual-write surface | ❌ NOT BUILT |

## 4 · Doctrine inheritance (no new doctrines added)

M1 ships entirely within the existing 50 ODR doctrines + 2
M0.35 Doctrine Locks (Simplicity Test, Platform Inheritance).
Specifically:

- The dashboard inherits the platform sidebar / card / dialog shells
  from the shared ui/ kit (Lock #2).
- The freeze adds zero foreman steps (Lock #1).
- The archive badge is one component, not a per-page invention
  (Lock #2).

## 5 · Cumulative test surface · 67 pytest · 0 fails

| Suite | Result |
|---|---|
| M0.1 substrate | 🟢 12 / 12 |
| M0.2 + M0.2A engines | 🟢 24 / 24 |
| M0.3 operator surfaces | 🟢 7 / 7 |
| M0.4 photo embedding | 🟢 9 / 9 |
| **M1 Option C (this wave)** | 🟢 **15 / 15** |
| Public link continuity probe `--gate` | 🟢 0 fail · 0 warn |
| Bilingual probe `--gate` | 🟢 0 fail |
| 4 advisory probes (M1-prep) | 🟢 GREEN at install |

## 6 · M1 spot-check checklist (~3 minutes of operator hands-on)

- [ ] Open `/operational-records` — confirm one unified list with archive badges on legacy rows
- [ ] Filter `kind=All` — both substrates appear; counts honest
- [ ] Filter `kind=ODR only` — only ODR rows visible, no archive badges
- [ ] Filter `kind=Archive only` — only legacy rows visible, all carry archive badges
- [ ] Click a legacy doc_id — routes to the legacy viewer (`/daily-reports/<id>`)
- [ ] Click an ODR doc_id — routes to the ODR detail viewer (`/odr/<id>`)
- [ ] `curl -X POST /api/daily-reports … → 410 Gone with redirect copy`
- [ ] `curl -X DELETE /api/daily-reports/<id> → 410 Gone with preservation copy`
- [ ] `GET /api/daily-reports` still returns the historical list (read paths live)
- [ ] `daily_reports` row count before vs after spot-check is identical (already proved by test 15)

## 7 · Approval items · what we want operator sign-off on before pilot

- [ ] **M1 Option C acceptance** — read `M1_OPTION_C_IMPLEMENTATION_PLAN.md` + `LEGACY_RECORD_FREEZE_CERTIFICATION.md`. Confirm the freeze contract matches MASCI policy.
- [ ] **Archive visual treatment acceptance** — read `ARCHIVE_VISUAL_TREATMENT_STANDARD.md`. Confirm tone (calm, slate, no alarm) is appropriate for distribution-facing surfaces.
- [ ] **Operational links bridge acceptance** — read `OPERATIONAL_LINKS_BRIDGE_CERTIFICATION.md`. Confirm `legacy_daily_report` as target-only is the right semantic.
- [ ] **Pilot rollout authorization** — explicit go/no-go on first-crew pilot.
- [ ] **OR · M2 authorization** — RFI + Schedule integration on the ODR substrate before pilot.

## 8 · Pilot authorization gate (every row must be ✅)

| Condition | Status |
|---|---|
| M0.0 hygiene | ✅ |
| M0.1 substrate sealed | ✅ |
| M0.2 / M0.2A engines + probes | ✅ |
| M0.3 operator surfaces live | ✅ |
| M0.35 reality validation passed (4/4) | ✅ |
| Doctrine Lock #1 (Simplicity Test) acknowledged | ✅ |
| Doctrine Lock #2 (Platform Inheritance) acknowledged | ✅ |
| M0.4 external PDF photo embedding | ✅ |
| **M1 Option C (freeze + projector + bridge + archive UI)** | ✅ |
| Pytest sweep complete (67 / 67) | ✅ |
| Continuity + bilingual probes green | ✅ |
| Advisory probes installed (M1-prep) | ✅ 4 / 4 GREEN |
| Zero-mutation invariant verified | ✅ test 15 |
| **Operator final review** | ⏳ awaiting |

Until the final row turns ✅: **No pilot. No M2. Await
authorization.**

## 9 · What stays NOT happening (per directive)

- ❌ NO pilot rollout
- ❌ NO RFI / Schedule / P6 work
- ❌ NO migration of any kind
- ❌ NO mutation of any legacy row
- ❌ NO production deploy beyond preview cutover
- ❌ NO new architecture or governance layers added

## 10 · Stop condition

🛑 **HALTED at end of M1 closure as directed.**

The substrate now presents **one operational history while
maintaining two record substrates.** Reality validation has proved
the operational shape (M0.35). Audience projection is locked
(M0.35). Photos travel with the document (M0.4). Doctrine locks
protect simplicity and inheritance from drift (M0.35). The audit
trail knows what was shipped to whom and when. **Historical truth
is preserved byte-identical.**

> _Field truth beats developer assumptions._
> _Operator adoption beats feature count._
> _Reality validation beats rework._
> _Photo evidence beats narrative dispute._
> _Historical truth beats forced conversion._

When you are ready, issue **pilot authorization** (or **M2
authorization** if you prefer to land RFI + Schedule integration
before the first crew goes live). Until then, the system stays
here — calmly, deterministically, audit-defensibly complete
through M1.

---

_End of M1_OPERATOR_REVIEW_GUIDE.md · supersedes the M0.4 review guide for the pilot decision._
