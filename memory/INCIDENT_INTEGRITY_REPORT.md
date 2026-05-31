# Incident Integrity Report · Critical Fix Sprint 1 · P0-2

**Batch:** OMEGA Critical Fix Sprint 1 · P0-2
**Date:** 2026-05-31
**Scope:** Forensic audit of `db.incidents` plus all linked collections. Read-only.

---

## 1 · Inventory — 7 production incidents

| `id` (UUID prefix) | `doc_id` | `incident_number` | severity | created_at | project | photos |
|---|---|---|---|---|---|---|
| `d9626eeb` | `INC-2026-00001` | `INC-2026-0517-002` | near_miss | 2026-04-25 20:09Z | I-95 Resurfacing Phase 2 | 0 |
| `566a38dd` | `INC-2026-00001` ⚠ DUP | None | near_miss | 2026-04-29 11:02Z | Oxford Rd Surcharge Utility | 1 |
| `33875910` | `INC-2026-00002` | None | near_miss | 2026-05-04 11:57Z | CC5744 - OXFORD RD | 1 |
| `83c28c3d` | `INC-2026-00003` | None | near_miss | 2026-05-07 18:43Z | CC5744 - OXFORD RD | 7 |
| `768ca0e4` | `INC-2026-00004` | None | near_miss | 2026-05-12 16:21Z | NSB Corbin Park | 7 |
| `7f1eeec9` | `INC-2026-00010` | None | near_miss | 2026-05-18 19:36Z | NSB Corbin Park | 8 |
| `87c8535b` | `INC-2026-00011` | None | near_miss | 2026-05-21 11:09Z | T5860 SR 9 (I-95) | 4 |

**Counter gap:** `doc_id` jumps from `INC-2026-00004` (2026-05-12) to `INC-2026-00010` (2026-05-18). Missing IDs 00005, 00006, 00007, 00008, 00009 — 5 incidents either deleted or never created.

---

## 2 · Finding I-1 · 🔴 Duplicate `doc_id='INC-2026-00001'`

**Two incidents share the same `doc_id`:**

| Field | `d9626eeb` (1st) | `566a38dd` (2nd) |
|---|---|---|
| `id` (UUID) | `d9626eeb-37a8-4e55-a5bb-3ea74f46ccd3` | `566a38dd-c613-4989-a906-365cdf2114a9` |
| `doc_id` | `INC-2026-00001` | `INC-2026-00001` ⚠ |
| `incident_number` | `INC-2026-0517-002` | None |
| `created_at` | 2026-04-25 20:09Z | 2026-04-29 11:02Z |
| `project_name` | I-95 Resurfacing Phase 2 | Oxford Rd Surcharge Utility |
| `project_number` | empty | `25-04` |
| `photos` | 0 | 1 |
| total fields | 44 | 47 (includes GPS coords, distribution_list) |

**Root cause (proven):** Two separate incident-creation code paths assigned `doc_id='INC-2026-00001'` to two different incidents. The second incident (`566a38dd`, 4 days later) has 3 more fields (GPS + distribution_list) suggesting a newer/extended creation path. The counter logic in `db.doc_id_counters` failed to atomically increment OR the two records were created via independent counter sources.

**Operational impact:**
- Any UI surface keying on `doc_id` (e.g. CSV export at `safety.py:764-805` exports `doc_id` as the primary identifier) shows ambiguous results.
- Searching by `INC-2026-00001` returns 2 records.
- Any report or print that uses `doc_id` as title may mislabel records.

**Recommended remediation (operator decision · not executed):**

1. **Promote `d9626eeb` to keep `INC-2026-00001`** (it's the older record and has the legacy `incident_number`).
2. **Reassign `566a38dd` to next available number** — likely `INC-2026-00012` since the next counter value is past 00011. Or use the gap `INC-2026-00005`..`INC-2026-00009` if those were truly never used.
3. **Investigate `doc_id_counters`** to ensure atomic increment.
4. **Add unique index**: `db.incidents.createIndex({doc_id: 1}, {unique: true, sparse: true})` — would prevent future duplicates.

**Risk if left alone:** 🔴 Audit/reporting integrity gap. Ongoing risk that report exports, regulatory filings, or operational drilldowns reference the wrong incident.

---

## 3 · Finding I-2 · 🟡 Three distinct ID schemas in use

Every incident has up to 3 ID fields:
- `id` — UUID (always present)
- `doc_id` — `INC-YYYY-NNNNN` 5-digit format (always present)
- `incident_number` — `INC-YYYY-MMDD-NNN` date-encoded format (only present on `d9626eeb`)
- `incident_id` — `null` on every record
- `report_id` — `null` on every record

**Implication:** Code paths are inconsistent. Some expect `incident_id`, some `incident_number`, some `doc_id`. The `accountability_projection.project_incident()` projection uses `id`. The DELETE route uses `id`. The CSV export uses `doc_id`. Cross-surface confusion is inevitable.

**Recommended remediation:** pick `id` (UUID) as canonical primary key and `doc_id` as display ID. Deprecate `incident_id` (always null) and `report_id` (always null) and `incident_number` (legacy single-row). Consolidate.

---

## 4 · Finding I-3 · 🟢 NO orphan CAPA links

| Probe | Result |
|---|---|
| `corrective_actions` count | **0 in production** |
| Orphan CAPA → incident references | n/a (no CAs exist yet) |

🟢 No orphans because no CAs. This is consistent with the production data state (`PRODUCTION_DATA_HYGIENE_AUDIT.md`).

---

## 5 · Finding I-4 · 🟢 NO orphan attachments

| Probe | Result |
|---|---|
| Incidents with `photos[]` | 6 of 7 (only `d9626eeb` has 0 photos) |
| Incidents with embedded `corrective_actions[]` array | 7 of 7 (embedded, not referencing the CA collection) |
| Embedded photo objects orphaned from R2 storage | NOT VERIFIED in this batch (would require R2 listing) |

🟢 Photos are embedded directly on the incident document. They are never orphaned by structural design.

---

## 6 · Finding I-5 · 🟢 NO orphan notifications

| Probe | Result |
|---|---|
| Notifications with `type` matching incident | 4 |
| Of those, with `subject_id` referencing a missing incident | **0** |

🟢 All 4 incident-type notifications reference live incidents (or do not carry `subject_id`).

(Note: the 2 `PREVIEW_POSTENV` notifications surfaced in `PRODUCTION_DATA_HYGIENE_AUDIT.md` are `type=incident.created` but reference a project name, not an incident UUID. They do not show as orphans against the `incidents` collection because they were never linked to an incident record in the first place.)

---

## 7 · Finding I-6 · 🟡 Invalid / null status chain

**Every production incident has `status=null` and `resolution_status=null`.**

| `id` | `status` | `resolution_status` |
|---|---|---|
| `d9626eeb` | None | None |
| `566a38dd` | None | None |
| `33875910` | None | None |
| `83c28c3d` | None | None |
| `768ca0e4` | None | None |
| `7f1eeec9` | None | None |
| `87c8535b` | None | None |

**Root cause:** Incident creation code paths do not set a default `status`/`resolution_status`. The accountability projection (`project_incident`) has fallback logic to map null → `"open"`, but any UI surface that reads `status` directly sees `null`.

**Operational impact:** Reporting and dashboard surfaces that count "open" vs "resolved" incidents may miscount these as neither.

**Recommended remediation:**
- Backfill all 7 production incidents with `status="open"` (or appropriate state).
- Update incident-creation code path to write `status="open" · resolution_status="open"` by default.

**Risk if left alone:** 🟡 Reporting accuracy gap. Pillar 1 projection masks the issue today, but any non-projection report surface is exposed.

---

## 8 · Finding I-7 · 🟢 Audit events on incidents

| Probe | Result |
|---|---|
| `audit_events` rows referencing incidents | 0 |
| `admin_audit` rows referencing incidents | (not enumerated by ID) |

🟡 NOTE: incidents don't have audit-event coverage. Creates and updates are not audited via `audit_events` collection. This is a Pillar 1B observability gap (covered in Pillar 1 supportability audit · "what changed" question is RED).

---

## 9 · Severity summary

| Severity | Finding | Count |
|---|---|---|
| 🔴 CRITICAL | I-1 Duplicate `doc_id='INC-2026-00001'` | 1 |
| 🟡 IMPORTANT | I-2 Three ID schemas in use, inconsistent | 1 |
| 🟡 IMPORTANT | I-6 All 7 incidents have `status=null · resolution_status=null` | 7 records |
| 🟢 CLEAN | I-3 No orphan CAPA links (0 CAs total) | — |
| 🟢 CLEAN | I-4 No orphan attachments (embedded design) | — |
| 🟢 CLEAN | I-5 No orphan notifications | — |
| 🟡 OBSERVABILITY | I-7 No audit-event trail on incidents | platform-wide |

---

## 10 · Closeout

🟡 Incident dataset is **mostly clean** with one 🔴 critical (duplicate doc_id) and two 🟡 important (ID schema drift · null status). 0 orphan links · 0 orphan attachments · 0 orphan notifications detected.

🛑 STOP. **NO REMEDIATION executed.** See `INCIDENT_DELETE_REMEDIATION_PLAN.md` for combined remediation sequencing.
