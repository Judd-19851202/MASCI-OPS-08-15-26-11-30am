# MOTIVE IDENTITY RECONCILIATION CERTIFICATION

**Date:** 2026-02-10 (probe wall clock 2026-06-11T03:55–04:05Z)
**Mode:** READ-ONLY. No mappings created. No records modified. No auto-link executed. No DB writes.
**Auth:** `jaymn.judd@mascigc.com` admin token against `https://mascidocs.com`.

---

## PHASE 1 — ASSET ANALYSIS

### Motive side (from `asset_mappings.provider=motive`)

| Metric | Value |
|---|---|
| Total Motive assets | **190** |
| With VIN populated | **190** (100 %) |
| Vehicles (`asset_kind=vehicle`) | 90 |
| Equipment (`asset_kind=equipment`) | 100 |
| Currently linked (`masci_equipment_id` non-empty) | **0** |

First 25 Motive asset rows (id field = `vin` for all; `number` carries the MASCI-style unit code on vehicles; `name` carries it on equipment):

```
 #  asset_kind          motive.name        motive.number          motive.vin       asset_id
 1   equipment          RL-1786                                4SW56-501786        269020
 2   equipment          RL-0214                                    PWP00214        269019
 3   equipment          RL-0799                                       70799        269018
 …
16   equipment          PX026-0067                                 975.0067        268997
17   vehicle                              WT007-9109     3ALACXCY4EDFV9109       (vehicle_id=1451689)
18   vehicle                              WT006-9028     3ALACXDT3FDGA9028
19   vehicle                              WT005-6304     JALB4B14817016304
20   vehicle                              DPT002-6387    1M2AG11C36M036387
21   vehicle                              DPT007-8803    1M2AX07C2AM008803
…
```

### MASCI side (from `GET /api/equipment-master`)

| Metric | Value |
|---|---|
| Total equipment records | **596** |
| With `vin_serial_number` | 564 (95 %) |
| With `unit_number` | 349 (59 %) |
| Unique VINs | **559** |
| Unique unit_numbers | **349** |

Sample 10 EM rows (showing the join keys the auto-linker actually uses):

```
unit='EXC-8614'         vin='28614-24QC'          → EXC-8614 — 2017 Kubota KX040-4R1T
unit='BH004-3882'       vin='HLS03882'            → BH004-3882 — 2010 Caterpillar 420E
unit='BH005-0543'       vin='JWJ00543'            → BH005-0543 — 2013 Caterpillar 420 FIT
unit='DPT002-6387'      vin='1M2AG11C36M036387'   → DPT002-6387 — 2006 Mack CV713
unit='DPT007-8803'      vin='1M2AX07C2AM008803'   → DPT007-8803 — 2010 Mack GU713
```

### Match-rule simulation (per `routes/integrations/autolink.py`)

Rules: **(1) VIN exact** → **(2) `motive.number`/`name` ↔ `equipment_master.unit_number` exact**. All keys uppercased + whitespace-collapsed.

| Bucket | VIN hit | Unit hit | No-match |
|---|---|---|---|
| Vehicles (90) | **88** | 1 | 1 |
| Equipment (100) | **68** | 1 | 31 |
| **Total (190)** | **156** | **2** | **32** |

Coverage: **158 / 190 = 83.2 %** would auto-map at `high` confidence on the first run.

The 32 no-matches are dominated by equipment with custom internal serials (e.g., `BH002-7149 ↔ T0310GX957149`, `EXC011-0380 ↔ N6120380`) where Motive sees one number and MASCI tracks another — these need either a manual mapping pass or a serial-mapping table extension to close.

### Determination
**Matching CAN occur — and at high quality — using VIN (primary) and `unit_number` (secondary).** Other identifiers (asset name as a free-text label, asset_id which is Motive-internal) cannot be matched against MASCI because MASCI carries neither field.

---

## PHASE 2 — DRIVER ANALYSIS

### Motive side (from `employee_mappings.provider=motive`)

| Metric | Value |
|---|---|
| Total Motive drivers | **65** |
| With `email` | 2 (3 %) |
| With `username` (typically `first.last`) | 52 (80 %) |
| With first+last name | 65 (100 %) |
| Currently linked (`masci_employee_id` non-empty) | **0** |

First 25 Motive driver rows:

```
WILLIAM   MUNDT       william.masci        (active)
VINNY     MASSARO     vmassaro             (active)
TERRANCE  WILLIAMS    terrance.masci       (active)
TAMMY     SHNEIDER    tammy.masci          (active)
SHANE     MULLINS     —                    (deactivated)
SHAN      WILSON      swilson3             (active)
SANDRA    LOHREY      —                    (deactivated)
RONALD    HAFNER      —                    (deactivated)
ROBERT    CASTELLOW   robert.masci         (active)
ROBERT    ADAMS       roberta.masci        (active)
RICKY     AVERETT     raverett             (active)
RICHIE    SANCHEZ     richie.masci         (active)
RICHARD   VIELE       rviele               (active)
RICHARD   CLENDENIN   rclendenin           (active)
PATRICK   MCERLEAN    pmcerlean            (active)
NIGUEL    HERNANDEZ   —                    (deactivated)
MICHAEL   WEAVER      —                    (deactivated)
MARTY     MULLIN      —                    (deactivated)
MARGARET  ROTELLA     margaret.masci       (active)
KYLE      MCDANIEL    kyle.masci           (active)
KURT      POREDA      kporeda              (active)
KEVIN     HILL        kevin.masci          (active)
KENNETH   WIDRICK     —                    (deactivated)
JOSEPH    SZYMANEK    jszymanek            (active)
JOSEPH    PEREIRA     jpereira2            (active)
```

### MASCI side (from `GET /api/employees`)

| Metric | Value |
|---|---|
| Total employees | **238** |
| With `email` | **0** |
| With `name` | 238 |
| Active | 238 |

First 25 MASCI employees:

```
Alec Perkins         (GENERAL LAB)
Alejandro Escobedo   (GENERAL LAB)
Alex Stansbury       (MOT)
Alfonso Flores-rosas (GENERAL LAB)
Allen Smathers       (SUPERVISOR)
Allen Workman        (PROJECT MANAGER)
Alvaro Cia           (1ST MILL OP)
Amado Delfin         (LOADER OPERATOR)
Amanda Kapp          (ACCOUNTING)
Amanda Pitt          (NIGHT LOGISTICS)
…
```

### Match-rule simulation (per `routes/integrations/autolink.py`)

Rules: **(1) email exact** → **(2) `motive.username` ↔ `employees.email`** → **(3) full-name exact** (`first_name + last_name` upper-trim ↔ `employees.name` upper-trim).

| Path | Hits | Reason it's mostly empty |
|---|---|---|
| email exact | 0 | Motive carries email for only 2 drivers, employees carry **0** emails — intersection is empty by definition. |
| username → email | 0 | Employees carry **0** emails — intersection impossible. |
| full_name exact | **23** | The only path that lands matches. 23 / 65 = 35.4 %. |
| no_match | **42** | Mostly: middle initials in MASCI (e.g., `BRETT T HOFFMAN` vs Motive `BRETT HOFFMAN`), nicknames in Motive (e.g., `VINNY` vs MASCI `VINCEENZA`), spelling variants (`BROOK` vs `BROOKE`, `DARRELL` vs `DARREL`), and Motive drivers absent from MASCI roster. |

### Determination
**Matching CAN occur via full name only.** Email and phone paths are blocked because **MASCI employees collection contains zero emails** (the username→email fallback the linker ships is therefore inert today). Of the 42 no-matches, **19 have a strong fuzzy candidate** (one-edit, middle-initial, or nickname) and **23 likely correspond to Motive drivers who are not in the MASCI employee roster** (or are no-longer-employed):

| Sample no-match | Closest MASCI candidate |
|---|---|
| `VINNY MASSARO` | `VINCEENZA MASSARO` (nickname) |
| `TERRANCE WILLIAMS` | `TERRANCE J WILLIAMS` (middle initial) |
| `SANDRA LOHREY` | `SANDRA C LOHREY` (middle initial) |
| `RICHIE SANCHEZ` | `RICHARD SANCHEZ` (nickname) |
| `JERMIAH TINDLE` | `JEREMIAH L TINDLE` (spelling + middle initial) |
| `JEFFERY MARVEL` | `JEFFERY W. MARVEL` (middle initial) |
| `JAMES - TACO OLORTEGUI` | `JAMES OLORTEGUI` (nickname tag) |
| `JAMES BRISLIN` | `JAMES W. BRISLIN` (middle initial) |
| `JAMEL VICTORY` | `JAMEL G VICTORY` (middle initial) |
| `FRANK WURST` | `FRANCIS WURST` (formal/nickname) |
| `DAVID HOUT` | `DAVID J. HOUT` (middle initial) |
| `DARRELL AKINS` | `DARREL AKINS` (spelling) |
| `BROOK POWELL` | `BROOKE POWELL` (spelling) |
| `BRETT HOFFMAN` | `BRETT T HOFFMAN` (middle initial) |

---

## PHASE 3 — AUTO-LINK PREVIEW (live `GET /api/admin/integrations/motive/auto-link/preview`)

### Assets (`?kind=assets`)

```
counts: { link: 158, skip_manual_link: 0, skip_already_linked_same: 0, no_match: 32 }
methods: { vin: 156, unit_number: 2 }
confidence: { high: 158 }
```

First 10 proposed asset LINKs (decision = "link"):

```
vehicle  | DPT002-6387 | vin=1M2AG11C36M036387 | vin  (high) → DPT002-6387 · 2006 Mack CV713
vehicle  | DPT007-8803 | vin=1M2AX07C2AM008803 | vin  (high) → DPT007-8803 · 2010 Mack GU713
vehicle  | DPT014-7057 | vin=1M2AX04CX9M007057 | vin  (high) → DPT014-7057 · 2009 Mack GU713
vehicle  | DPT015-6201 | vin=1M2AX04C89M006201 | vin  (high) → DPT015-6201 · 2009 Mack GU713
vehicle  | DPT021-8147 | vin=1M2AX04CXAM008147 | vin  (high) → DPT021-8147 · 2010 Mack GU713
vehicle  | DPT024-4764 | vin=1M2AT04C87M004764 | vin  (high) → DPT024-4764 · 2007 Mack CTP713
vehicle  | DPT025-4762 | vin=1M2AT04C47M004762 | vin  (high) → DPT025-4762 · 2007 Mack CTP713
vehicle  | DPT027-7238 | vin=1M2AX09C29M007238 | vin  (high) → DPT027-7238 · 2009 Mack GU713
vehicle  | DPT029-7236 | vin=1M2AX09C99M007236 | vin  (high) → DPT029-7236 · 2009 Mack GU713
vehicle  | DPT030-7237 | vin=1M2AX09C09M007237 | vin  (high) → DPT030-7237 · 2009 Mack GU713
```

First 10 proposed asset NO_MATCH:

```
vehicle    | PKU-8234     | vin=5TFKB5AB0TX058234   (Toyota pickup, VIN not in equipment_master)
equipment  | BH002-7149   | vin=T0310GX957149       (MASCI tracks BH-style with diff serial)
equipment  | DZ004-9851   | vin=JX169851
equipment  | EXC007-0616  | vin=NA0110616
equipment  | EXC008-7704  | vin=KMTPC094T05007704
equipment  | EXC009-0074  | vin=NB0310074
equipment  | EXC011-0380  | vin=N6120380
equipment  | EXC015-0413  | vin=TTN00413
equipment  | EXC-1680     | vin=21680
equipment  | EXC-0117     | vin=HHIHQB01LB0000117
```

### Drivers (`?kind=drivers`)

```
counts: { link: 23, skip_manual_link: 0, skip_already_linked_same: 0, no_match: 42 }
methods: { full_name: 23 }
confidence: (medium for all 23 — full_name matches are graded "medium")
```

All 23 proposed driver LINKs:

```
BRIAN HARDING             (brian.masci)        → 'Brian Harding'
CODY RAGAN                (cragan)             → 'Cody Ragan'
Corey Anderson            (no username)        → 'Corey Anderson'
DANIEL VALES              (daniel.masci)       → 'Daniel Vales'
DANNY KRAMMER             (dann.masci)         → 'Danny Krammer'
DEDORIUS VARNES           (dvarnes)            → 'Dedorius Varnes'
GREGORY BATROSS           (gregb.masci)        → 'Gregory Batross'
HARRY OLSON               (harry.masci)        → 'Harry Olson'
JACQUELINE BLOODWORTH     (jacqb.masci)        → 'Jacqueline Bloodworth'
JARED SARGENT             (jared.masci)        → 'Jared Sargent'
JERRY METELUS             (jerry.masci)        → 'Jerry Metelus'
JOHN THOENNES             (jthoennes)          → 'John Thoennes'
JONATHAN BLAIR            (jonathanb.masci)    → 'Jonathan Blair'
JONATHAN MOLERO           (jonathanm.masci)    → 'Jonathan Molero'
JOSEPH SZYMANEK           (jszymanek)          → 'Joseph Szymanek'
KEVIN HILL                (kevin.masci)        → 'Kevin Hill'
KURT POREDA               (kporeda)            → 'KURT POREDA'
KYLE MCDANIEL             (kyle.masci)         → 'Kyle Mcdaniel'
MARGARET ROTELLA          (margaret.masci)     → 'Margaret Rotella'
RICHARD VIELE             (rviele)             → 'Richard Viele'
ROBERT ADAMS              (roberta.masci)      → 'Robert Adams'
SHAN WILSON               (swilson3)           → 'Shan Wilson'
WILLIAM MUNDT             (william.masci)      → 'William Mundt'
```

---

## PHASE 4 — FAILURE ANALYSIS

**Why 0 / 0 today:** **A. Auto-link has never been executed on production.**

Evidence:
1. `mapping_notes` / `mapping_confidence` / `motive.mapping_status` are empty on every row in `asset_mappings` and `employee_mappings` (the auto-linker stamps these fields whenever it touches a row).
2. The sync-log history (`/api/admin/integrations/sync-logs?integration=motive&limit=20`) shows only ingestion sync types: `sync_events`, `sync_assets`, `sync_users`, `sync_geofences`. **No `autolink_assets` or `autolink_drivers` entries exist.**
3. The preview endpoint reports `skip_already_linked_same=0` for both kinds — meaning zero rows have a prior link to skip over.
4. Running the preview NOW produces 158 asset link proposals and 23 driver link proposals — the engine works; nothing has consumed it.

**Why even after auto-link runs the remaining gaps stay:**

| Secondary cause | Affected | Detail |
|---|---|---|
| **B. Matching rules too strict (drivers)** | ~19 drivers | Driver linker has no middle-initial collapse and no nickname/fuzzy resolution. `BRETT HOFFMAN` ≠ `BRETT T HOFFMAN` under the current exact-match rule. |
| **C. Field mismatch (drivers via email)** | 65 drivers | Linker tries `motive.email` and `motive.username` against `employees.email`. MASCI's employees collection carries **0 emails**, so both paths are inert. Full-name is the only working path today. |
| **E. Missing identifiers (equipment)** | ~31 equipment | MASCI's `equipment_master.vin_serial_number` does not contain the Motive vin for these rows (the small-equipment serial in Motive is a manufacturer code Motive captured, while MASCI tracks an internal RL/EXC/BH-style serial). Resolution requires a one-time human serial mapping. |
| **D. Data normalization** | minimal | The linker already uppercases + whitespace-collapses both sides. No casing/space drift detected in the sample. |
| **F. Motive driver not on MASCI roster** | ~23 drivers | Several Motive drivers (e.g., `JAMES VANDEGAAF`, `JOHN PAUL`, `ANDREW GRANT`, `AVIS ADKINS`) have no last-name match in `employees` at all — likely contract drivers or recently-terminated rosters. |

**Verdict on Phase 4:** **A. Auto-link never executed.** Once it runs, secondary blockers B/C/E account for the residual no-matches.

---

## PHASE 5 — EXECUTION RISK PROJECTION

If `POST /api/admin/integrations/motive/auto-link?kind=assets` is fired now:

| Outcome | Count | Confidence |
|---|---|---|
| Newly mapped assets | **158** (88 vehicles + 70 equipment) | HIGH — 156 are exact-VIN matches (17-char VINs collide with probability ~0); 2 are exact unit_number matches. 1:1 guard in the apply path will refuse any duplicate-target collision. |
| Unmatched assets | **32** (1 vehicle + 31 equipment) | Awaits manual serial alias table. |
| Manual override conflicts | 0 | No `masci_equipment_id` is non-empty anywhere — nothing to preserve. |
| 1:1 target collisions | Expected 0 | Each VIN/unit_number is unique on both sides; preview did not surface duplicates. |

If `POST /api/admin/integrations/motive/auto-link?kind=drivers` is fired now:

| Outcome | Count | Confidence |
|---|---|---|
| Newly mapped drivers | **23** | MEDIUM — full-name exact across two systems is not surname-collision-free in principle, but every proposed match is between a single Motive driver and a single same-cased employee; no two-target ambiguities surfaced. |
| Unmatched drivers | **42** | Needs (a) fuzzy/middle-initial/nickname rule extension in `_propose_driver_links`, **or** (b) a one-time manual pairing for the ~19 obvious near-matches. The remaining ~23 likely require roster reconciliation outside MASCI. |
| Manual override conflicts | 0 | No `masci_employee_id` is non-empty anywhere. |

### Composite expected post-run state

- Asset Spine coverage: 31.9 % → **~58 %** (158 newly linked / 596 total).
- Trust score (assets): 0 → **83.2 %** band `green`.
- Trust score (drivers): 0 → **35.4 %** band `amber`.
- Operations Center Command · Telematics tile: 0 mapped trucks → ~88 mapped trucks; `rows=[]` → ~88 live rows.

---

## FINAL QUESTION — CAN WE SAFELY EXECUTE AUTO-LINK NOW?

# **YES.**

**Why it is safe:**

1. **Idempotent writes.** The apply code (`asset_mappings.update_one(... "$or": [{masci_equipment_id: ""}, {masci_equipment_id: {"$exists": false}}])`) writes only when the target field is empty. It refuses to overwrite manual links.
2. **1:1 collision guard.** Before writing, the code checks `db.asset_mappings.find_one({masci_equipment_id: candidate})` and skips if another row already owns the target. Zero such rows exist today.
3. **Audit trail.** Every link stamps `mapping_notes`, `mapping_confidence`, `motive.mapping_status="Mapped"`, and writes a `sync_log` row (`sync_type=autolink_assets|autolink_drivers`).
4. **Reversibility.** Since this is the first run, undoing it is a single Mongo update setting `masci_equipment_id=""` on auto-stamped rows (identifiable by `mapping_notes LIKE "Auto-linked%"`).
5. **Preview matches expectation.** The dry-run output (`counts={link:158, skip_manual_link:0, skip_already_linked_same:0, no_match:32}`) has zero `skip_manual_link` and zero `skip_already_linked_same` — nothing pre-existing to disturb.

### Exact execution sequence

```bash
# 0. Confirm preview totals (already captured above; rerun if more than ~10 min has passed)
curl -s -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/motive/auto-link/preview?kind=assets"  | jq '.counts'
curl -s -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/motive/auto-link/preview?kind=drivers" | jq '.counts'

# 1. Execute assets first (the bigger / higher-confidence batch).
curl -s -X POST -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/motive/auto-link?kind=assets" | jq

# 2. Execute drivers.
curl -s -X POST -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/motive/auto-link?kind=drivers" | jq

# 3. Post-run verification (read-only).
curl -s -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/cleanup/trust-score" | jq
curl -s -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/admin/integrations/sync-logs?integration=motive&limit=5" | jq
curl -s -H "X-Admin-Token: $TOK" \
  "https://mascidocs.com/api/operations-center/command/telematics" \
  | jq '{mapped_trucks, unmapped_trucks, integration_readiness}'
```

**Expected response from step 1:** `{"ok": true, "kind": "assets", "linked": 158, "skipped_manual": 0, "noop": 32, "conflicts": 0}`.
**Expected response from step 2:** `{"ok": true, "kind": "drivers", "linked": 23, "skipped_manual": 0, "noop": 42, "conflicts": 0}`.

### What this run will NOT solve (follow-up backlog)

1. **31 small-equipment serial gaps** — need a one-time alias table or hand-curated mapping pass.
2. **42 driver no-matches** — need either (a) a fuzzy/middle-initial extension to `_propose_driver_links`, or (b) a manual review of the 19 obvious near-matches and ~23 likely off-roster names.
3. **MASCI employees collection has no emails** — once that data lands, the linker's primary (high-confidence) email/username paths will automatically light up and increase driver coverage.

### What this run also does NOT change (mandate compliance)

- MONGO_URL, DB_NAME, APP_ENV, JWT_SECRET, Atlas users, authentication, sessions, Motive Dashboard, env vars, secrets — all untouched.
