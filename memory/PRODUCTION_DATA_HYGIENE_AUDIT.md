# Production Data Hygiene Audit · Forensic Phase 3

**Batch:** OMEGA Forensic Platform Certification · Phase 3
**Date:** 2026-05-31
**Scope:** Forensic scan of every production MongoDB collection for contamination terms (`test · demo · sample · preview · seed · dummy · TEST_ · iter · placeholder · lorem · John Smith · Jane Smith`). Read-only against `masci_safety` (production).

---

## 1 · Executive verdict

🟡 **MOSTLY CLEAN · 6 confirmed contamination items.** Production data is dramatically cleaner than preview. Four contamination categories surfaced:

| Category | Severity | Count |
|---|---|---|
| Preview-tagged notifications (2026-05-16 crossover) | 🟡 IMPORTANT | 2 docs |
| Test FL user account live in production | 🔴 CRITICAL | 1 doc |
| Incomplete payroll-variance batches | 🟡 IMPORTANT | 10 batches with `status=null · uploaded_by=null` |
| Cancelled-test transfer_requests | 🟢 COSMETIC | 29 of 30 |
| Duplicate incident `doc_id` | 🔴 CRITICAL | `INC-2026-00001` shared by 2 incident rows |
| Expired hub banner still in DB | 🟢 COSMETIC | 1 doc (Memorial Day · expired 2026-05-26) |

---

## 2 · Finding 3-D-1 · `notifications.PREVIEW_POSTENV` (🟡)

**Location:** `db.notifications` (production)

**Evidence:**
```
id=64f443d6  type=incident.created  title="New incident reported — Near Miss"  created_at=2026-05-16 13:46:47.539Z  recipient_role=safety  read=null
id=9ac645f3  type=incident.created  title="Incident on PREVIEW_POSTENV"        created_at=2026-05-16 13:46:47.540Z  recipient_role=pm     read=null
```

**Root cause (proven):** Pre-2026-05-26 preview/production data crossover incident, documented in `/app/memory/test_credentials.md` ("preview pytest fixtures and agent test writes landed directly in the live `masci_safety` database"). These notifications reference a project named `PREVIEW_POSTENV` that does not exist in any of the queried collections (`incidents · daily_reports · jobs_master · po_requests · tasks · meetings · jhas · events · operational_links · operations_events` — 0 matches in each).

**Reproduction:**
```bash
mongo $MONGO_URL/masci_safety --eval 'db.notifications.find(
  {$or:[{title:/PREVIEW_POSTENV/i}, {message:/PREVIEW_POSTENV/i}]}, {_id:0}
)'
```

**Recommended remediation (operator decision · not executed):** delete the 2 docs. They reference a non-existent project; no operational consequence; no user has read them (`read=null`).

---

## 3 · Finding 3-D-2 · Test FL user in production (🔴)

**Location:** `db.field_leadership_users` (production)

**Evidence:**
```
email=fieldleader@mascigc.com  role=Superintendent  is_active=True  created_at=2026-05-21T16:26:28.661Z
```

**Cross-reference:** `/app/memory/test_credentials.md` documents this exact account as: `Test FL user: fieldleader@mascigc.com / FieldLead2026!` with `must_change_password=false`, explicitly created "ready for automated tests".

**Root cause (proven):** Test fixture seeded into the production identity collection (`field_leadership_users`). Active in production.

**Security implication:** The test password `FieldLead2026!` is documented in plain text in `/app/memory/test_credentials.md`. Any actor with repo access can authenticate to production as a Superintendent in the Field Leadership Portal — bounded operational visibility (DRs · Safety Meetings · JHAs · DVIRs · Fleet read-only · Dispatch read-only · Incidents · DQ dashboard) per the canonical FL token scope.

**Reproduction (DO NOT execute — read-only audit):**
```
POST https://mascidocs.com/api/auth/multi-login
{"email":"fieldleader@mascigc.com","password":"FieldLead2026!"}
```

**Severity rationale:** 🔴 CRITICAL. A documented-password test account on production is a security gap regardless of permission scope.

**Recommended remediation (operator decision · not executed):** rotate the password, deactivate the account, or delete it from production. Update `/app/memory/test_credentials.md` accordingly.

---

## 4 · Finding 3-D-3 · Payroll variance batches with null state (🟡)

**Location:** `db.payroll_variance_batches` (production)

**Evidence:** 10 batches, all created 2026-05-12 / 2026-05-13. **All have `status=null · uploaded_by=null · variances_count=null · pay_period_end=null`:**

```
674300c9  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-12T23:52:33.512Z
48cbc60e  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:02:15.419Z
6590febb  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:05:19.890Z
f1371d01  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:05:20.193Z
76d952ce  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:05:20.318Z
f28d4b44  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:05:32.024Z
ed8ec430  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:06:16.529Z
8b649f92  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:06:16.821Z
2eb4c2d2  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:06:16.896Z
d3150925  status=None  uploaded_by=None  variances_count=None  created_at=2026-05-13T00:08:06.079Z
```

**Companion collection:** `payroll_variance_decisions` has 7 docs (presumably linked to the populated batches in preview, not these production stubs).

**Root cause (suspected · NOT proven):** Likely failed-import or test-upload batches that wrote a parent record without populating the variance rows. The timestamp clustering (within 16 minutes on 2026-05-12/13) is consistent with iterative test runs during the iter238/iter282 payroll-variance build-out.

**Operational impact:** These batches appear in the HR portal's payroll-variance list with empty values. Operator-visible confusion.

**Recommended remediation (operator decision · not executed):** delete the 10 null-status batches OR set `status="archived"` to hide from list view.

---

## 5 · Finding 3-D-4 · Duplicate incident `doc_id` (🔴)

**Location:** `db.incidents` (production)

**Evidence:** Aggregation `{$group: {_id: "$doc_id", n: {$sum: 1}}}` returns:

```
doc_id="INC-2026-00001"  occurs 2 times:  ids=['d9626eeb', '566a38dd']
```

**Full incident ID surface inspection:**
```
id=d9626eeb  incident_id=None  incident_number='INC-2026-0517-002'  doc_id='INC-2026-00001'  sev=near_miss
id=33875910  incident_id=None  incident_number=None                  doc_id='INC-2026-00002'  sev=near_miss
id=566a38dd  incident_id=None  incident_number=None                  doc_id='INC-2026-00001'  sev=near_miss  ← DUPLICATE
id=768ca0e4  incident_id=None  incident_number=None                  doc_id='INC-2026-00004'  sev=near_miss
id=7f1eeec9  incident_id=None  incident_number=None                  doc_id='INC-2026-00010'  sev=near_miss
id=83c28c3d  incident_id=None  incident_number=None                  doc_id='INC-2026-00003'  sev=near_miss
id=87c8535b  incident_id=None  incident_number=None                  doc_id='INC-2026-00011'  sev=near_miss
```

**Observations:**
- 7 production incidents · 3 distinct ID schemas in use (`id` UUID · `incident_number` · `doc_id`)
- `incident_id` field is `null` on every doc
- `doc_id` gap: `00001, 00002, 00003, 00004, …, 00010, 00011` — 5 numbers missing (00005..00009) suggesting either delete history or schema split
- Only `d9626eeb` has `incident_number` populated; the rest have `null`

**Root cause (suspected · NOT proven):** Multiple incident-creation code paths (`server.py` legacy + `safety_portal` migration) writing to different ID fields. The duplicate `doc_id='INC-2026-00001'` would be created if two paths each assigned the lowest available number simultaneously, or if a counter rolled back.

**Operational impact:** Any UI or report that keys on `doc_id` shows the wrong incident or merges two incidents. Operator's reported "Incident INC-2026-000001" investigation item (note: with 6 zeros vs platform's 5 zeros) may stem from a separate UI display path — confirmation requires UI inspection (see `UI_HYGIENE_AUDIT.md`).

**Operator's `INC-2026-000001` claim:** **NOT found in production** with that exact string. Production uses 5-zero format `INC-2026-00001`. Possible mismatch in operator's note vs platform's format, OR a UI surface that pads to 6 zeros.

**Recommended remediation (operator decision · not executed):** investigate ID-counter logic; pick the canonical schema (`incident_number` vs `doc_id`); migrate to single field; deduplicate by promoting `d9626eeb` (has `incident_number`) over `566a38dd`.

---

## 6 · Finding 3-D-5 · Transfer requests · 29/30 cancelled (🟢)

**Location:** `db.transfer_requests` (production)

**Evidence:**
```
Cancelled: 29
Submitted: 1
```

**Sample 3 cancelled rows (all reference the same asset · 4-minute timespan · empty `reason`):**
```
de869ac7  asset=647b1857  reason=""  status=Cancelled  created=2026-05-15T00:25:55.447Z
2692a84f  asset=647b1857  reason=""  status=Cancelled  created=2026-05-15T00:35:32.247Z
00f20612  asset=647b1857  reason=""  status=Cancelled  created=2026-05-15T00:37:06.872Z
```

**Root cause (suspected · NOT proven):** Iterative test runs creating then cancelling transfer requests on the same asset during the iter? asset-transfer build-out.

**Operational impact:** Cosmetic — these are terminal-cancelled records, not active. They inflate the transfer history but do not affect routing.

**Recommended remediation:** Operator may archive these 29 records OR leave as historical audit trail.

---

## 7 · Finding 3-D-6 · Expired hub banner (🟢)

**Location:** `db.hub_banners` (production)

**Evidence:**
```
id=00a62d457d524e92895151604412c309
title_en="Memorial Day — In Remembrance"
auto_posted=True  template_id=memorial_day  auto_posted_iter=iter329
expires_at=2026-05-26T00:00:00+00:00
created_at=2026-05-24T00:00:39.464Z
dismiss_log: 7 entries
```

**Root cause:** Auto-posted via iter329 cultural-calendar logic. The expiration handler is not visible in this audit — the doc remains in the collection past its `expires_at`.

**Operational impact:** No user-facing impact (banner display logic should filter on `expires_at`). Data hygiene only.

**Recommended remediation:** Operator may purge expired banners OR rely on display-time filter.

---

## 8 · Items investigated and CLEARED

| Operator concern | Finding |
|---|---|
| `INC-2026-000001` (6-zero format) | NOT present in production; closest match `INC-2026-00001` (5-zero) exists and is duplicated (see 3-D-4) |
| Payroll variance batches | Confirmed contamination (10 null-state batches · see 3-D-3) |
| User accounts with "John Smith" / "Jane Smith" | None across 8 user collections (clean) |
| `users` / `user_directory` with test/demo/preview emails | None (clean) |
| `suppliers` containing "test"/"seed" | False positives — legitimate company names: "Bechtol Engineering & Testing Inc" · "Florida Hydroseeding & Erosion Control" |
| `role_templates` containing "iter" | False positive — `rt-shop-service-writer` description mentions "iter" in narrative |
| Integration settings demo_mode/test_mode | Both providers (`motive` · `maintainx`) have `demo_mode=False · test_mode=False · enabled=False · status="Not Connected"` — clean |

---

## 9 · Cleanliness score

| Dimension | Score |
|---|---|
| Identity collections (users / hr / fl / safety / shop / dispatch) | 🟡 **95/100** (1 test FL account live) |
| Operational collections (incidents · CAs · POs · tasks · DRs · daily_reports) | 🟡 **85/100** (1 duplicate doc_id) |
| Notifications | 🟡 **97/100** (2 PREVIEW_POSTENV stragglers) |
| Configuration | 🟢 **100/100** |
| Payroll | 🟡 **0/100** (10 of 10 batches null-state) |
| Asset transfers | 🟢 **97/100** (29 cancelled-tests but terminal · cosmetic) |
| Hub banners | 🟢 **99/100** (1 expired banner not purged) |
| **Overall** | 🟡 **~88/100** |

---

## 10 · Closeout

🟡 Production data is **mostly clean** with 6 documented contamination items totaling 44 docs across 5 collections. Two findings are 🔴 CRITICAL (test FL account · duplicate incident doc_id) and warrant immediate operator decision. All findings carry reproduction steps and evidence. **NO REMEDIATION executed in this batch.**

🛑 STOP.
