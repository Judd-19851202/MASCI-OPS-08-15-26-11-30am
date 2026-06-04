# MAINTAINX · DEFECT PIPELINE GAP REGISTER  (Phase 6)

**Date:** 2026-06-04 19:10 UTC
**Directive:** OMEGA — MaintainX Equipment Defect Pipeline Audit & Integration Plan
**Mode:** READ-ONLY (no writes)

Direct comparison of what the current P0-A/P0-B read-first MaintainX stack covers versus the complete Equipment Defect Pipeline described in Phases 1–5.

---

## 1 · Answer to the 10 required questions

| # | Question | State today | Verdict |
| --- | --- | --- | --- |
| 1 | Is Fleet DVIR included? | DVIR is fully implemented internally (`fleet_defects` lifecycle, severity, photos, RTS), but **NO** MaintainX WO is created from any DVIR row. `fleet_defects.external_refs.maintainx_work_order_id` field exists but is **never populated**. | **NOT COVERED at the MaintainX boundary** |
| 2 | Is Heavy Equipment Pre-Op included? | Pre-Op is fully implemented in `routes/equipment.py` with fan-out to `asset_holds` + `tasks` + `notifications`. There is **NO** MaintainX call. The service stubs `create_work_order_from_failed_preop()` return `{ok:false, status:"stub"}`. | **NOT COVERED at the MaintainX boundary** |
| 3 | Is Equipment Inspection (non-Pre-Op) included? | Shared `equipment_inspections` collection. No MaintainX wiring. | **NOT COVERED** |
| 4 | Is Shop issue included? | Shop can flip OOS via the Dispatch endpoint and can release asset_holds. No MaintainX wiring. | **NOT COVERED** |
| 5 | Is Dispatch breakdown included? | Same `manual_oos_flip` endpoint — no MaintainX wiring. | **NOT COVERED** |
| 6 | Is RTS return path included? | Dispatch `/clear` and `/release` exist; **no gate against MaintainX WO status**. RTS today is internal-only. | **NOT COVERED at the MaintainX boundary** |
| 7 | Are photos included? | DVIR / Pre-Op / Manual OOS all collect `photos[]` (R2 keys). No relay to MaintainX. | **READY in source rows · NOT PUSHED to MaintainX** |
| 8 | Are attachments included? | No `attachments[]` field exists on any source row today (photos only). No attachment relay. | **NOT COVERED** |
| 9 | Are source IDs preserved? | Inside ForgedOps yes; cross-system correlation (`correlation_id`/`externalId`) is **only defined on paper** in Phase 3/4 — no code stamps it yet. | **NOT IMPLEMENTED** |
| 10 | Are duplicate WO protections planned? | The P0 read-first sprint did **not** address WO duplicate protection. Duplicate-asset risk analyser exists. No WO de-dupe logic yet. | **PLANNED in Phase 8 · NOT BUILT** |

---

## 2 · Coverage matrix (capability × source)

For each defect source × capability cell:

`✅ live` · `🟡 internal-only (no MaintainX)` · `🚧 planned (Phase X)` · `❌ not started`

| Capability ↓ \ Source → | Fleet DVIR | Heavy Equipment Pre-Op | Equipment Inspection (non Pre-Op) | Shop issue | Dispatch breakdown | Manual maintenance request |
| --- | --- | --- | --- | --- | --- | --- |
| Defect intake row written | ✅ live | ✅ live | ✅ live | ✅ live | ✅ live | ✅ live |
| Severity classified | ✅ live | ✅ live | ✅ live | ✅ live (oos) | ✅ live (oos) | ✅ live |
| Photos collected | ✅ live | ✅ live | ✅ live | ✅ live | ✅ live | 🟡 partial |
| Asset resolved → equipment_master | ✅ live | ✅ live | ✅ live | ✅ live | ✅ live | ✅ live |
| Canonical defect payload built | ❌ (🚧 Phase 3) | ❌ | ❌ | ❌ | ❌ | ❌ |
| MaintainX `assetId` resolved | 🚧 (P0-A/P0-B mapping ready, but no consumer) | 🚧 | 🚧 | 🚧 | 🚧 | 🚧 |
| MaintainX WO push | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Photos pushed to WO | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `external_refs.maintainx_work_order_id` stamped | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| `external_refs.correlation_id` stamped | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Duplicate WO protection | ❌ (🚧 Phase 8) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Webhook status mirrored back to source | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| RTS gate against WO closure | ❌ (🚧 Phase 5) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Maintenance history visible on Asset Profile | 🚧 P0-G in roadmap | 🚧 P0-G | 🚧 P0-G | 🚧 P0-G | 🚧 P0-G | 🚧 P0-G |

---

## 3 · Net gap summary

| Theme | Open gap |
| --- | --- |
| **Canonical payload layer** | Not yet implemented in code. Phase 3 contract is documentation-only. |
| **WO push module** | Not yet implemented. Phase 4 mapping contract is documentation-only. |
| **Duplicate protection** | Not yet implemented; design in Phase 8. |
| **RTS gate against WO closure** | Not yet implemented; design in Phase 5. |
| **Webhook handler — real algorithm** | `services/maintainx_client.process_webhook(...)` is a stub. Signature verification uses placeholder HMAC-SHA256. |
| **Cross-source dedup keys** | No `correlation_id` or `externalId` is stamped anywhere yet. |
| **Photos relay** | No attachment relay code. |
| **Heavy Equipment Pre-Op parity** | The P0-A/P0-B sprint focused on Assets. Pre-Op is not even mentioned in the existing client. |

---

## 4 · What is OK / safe today

- Read-first asset matching (P0-A/P0-B) is **live and safe** — see `MAINTAINX_P0_GO_NO_GO.md`.
- Admin Integration Center surface is **live and safe** — see `MAINTAINX_ADMIN_INTEGRATION_GO_NO_GO.md`.
- All defect sources continue to operate exactly as before — no observable behaviour change.
- No defect row references an actual MaintainX WO; the `external_refs.maintainx_work_order_id` placeholder remains `null` everywhere.
- No deploy is required for any of the work in Phases 1–5; this is all planning.

---

## 5 · What must be true before any defect → WO push can be turned on

1. `MAINTAINX_API_KEY` populated and validated end-to-end via the existing Admin Integration Center "Test Connection" + "Run Dry-Run" flows.
2. Asset mapping count is high enough (≥ 90% of operational `equipment_master` rows have a `asset_mappings.maintainx.asset_id`).
3. Phase 3 canonical defect payload module is implemented and unit-tested.
4. Phase 8 duplicate-protection module is implemented and unit-tested.
5. Phase 5 RTS gate enforcement code is implemented behind a kill-switch.
6. Phase 6 dry-run preview is operator-reviewed against real DVIR + Pre-Op rows.
7. Operator authorisation is captured per source type — DVIR turned on first; Pre-Op second; Manual OOS third; etc.

— End of Phase 6 Gap Register —
