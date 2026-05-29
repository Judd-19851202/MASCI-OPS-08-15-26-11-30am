# ODR · PUBLIC LINK DEVICE CONTINUITY ADDENDUM

_Phase V.1 · Operational Daily Record · Pre-Lock Hard Requirement · 2026-05-29_

The ODR ships with **public-link access** (not full portal gate-kept).
This doctrine establishes the **device continuity contract** that
prevents one crew's prior-day report data from leaking into another
crew's blank slate via the public link.

**Mandatory before spec lock. No implementation. Architecture only.**

---

## 1 · Doctrine statements (O11–O20 · new)

These extend the locked operator doctrine (O1–O10) and are anchored
in every relevant artifact.

| # | Statement |
|---|---|
| O11 | Public ODR links may create or submit current-day reports only within their authorized project/report context. |
| O12 | "Start from yesterday" / "duplicate previous report" / "continue previous report" / any auto-preload of prior ODR data is allowed **only** if device continuity is verified. |
| O13 | Device continuity must compare device fingerprint, local device token, prior submitter/session identity (where available), project/job context, report link context, date continuity, and (optional) GPS/project proximity. |
| O14 | If continuity passes → allow prior-report preload. If continuity fails → **never** load prior report details; show a calm message and offer a blank report. |
| O15 | Never expose prior employees, equipment, production entries, notes, photos, delay records, safety answers, or vendor/sub lists from a previous report to an **unverified** device. |
| O16 | Manual blank entry is always allowed. |
| O17 | Authorized admin/PM override is allowed **only** inside the authenticated portal, never from a public ODR link. |
| O18 | All preload attempts (allowed · denied · mismatch · missing token · expired · override) are append-only logged. |
| O19 | The continuity rule applies to every preload surface: auto-preload, duplicate-yesterday, repeat crew, repeat equipment, repeat production segments, repeat materials, repeat subs/vendors, repeat tomorrow-plan carryover. |
| O20 | When in doubt, the system **chooses a blank slate** over an unverified preload. Field trust is the asymmetric value. |

---

## 2 · The seven continuity signals

The continuity engine compares the **incoming preload request** to
the **prior report's submission envelope**. A request passes when
**at least the four mandatory signals match** AND **no signal
explicitly conflicts**.

| # | Signal | Mandatory? | Source on request | Source on prior |
|---|---|---|---|---|
| 1 | **Device fingerprint** (UA + OS + OS version + app version + is_pwa + is_secure_context) | ✅ mandatory | `DeviceFingerprint` rendered at request time | `reliability.device_fingerprint` stored on the prior ODR |
| 2 | **Local device token** (opaque · cryptographically random · long-lived in browser localStorage / IDB · scoped to project + crew) | ✅ mandatory | client-presented token | stored on prior ODR `public_access.device_tokens[]` |
| 3 | **Project / job context** (`project_id` + optional `crew_id`) | ✅ mandatory | URL path of public link | `project.project_id` (+ `crew_profile.crew_id`) on prior |
| 4 | **Report link context** (the opaque public link id that grants access; per-project + per-crew) | ✅ mandatory | link slug used for navigation | matching `public_access.link_id` on prior |
| 5 | **Date continuity** (today = prior `report_date` + 1 calendar day in site-TZ, OR within an operator-configurable window default 1–3 days for weekends/holidays) | optional but strongly preferred | server clock + site-TZ | `project.report_date` on prior |
| 6 | **GPS / project proximity** (current GPS fix within an operator-configurable radius of `work_areas[*].gps_centroid` or `project.gps`) | optional · failure does **not** block when 1–4 pass | browser geolocation | `project.gps` + work_areas centroids |
| 7 | **Prior submitter / session identity** (foreman UID or session id, when the prior ODR was authored from this device) | optional · used as a tie-breaker | last-author UID stored locally | `submitted_by_uid` + `device_session_id` on prior |

**Passing rule (minimum bar)**: signals 1 + 2 + 3 + 4 all match,
AND signal 5 is within the configured window (or N/A on a holiday),
AND no signal **explicitly conflicts** (e.g., GPS evidence places
the device 400 miles away).

**Conflict rule**: if any signal explicitly conflicts (not merely
"unknown"), the request is denied regardless of how many other
signals pass. This is the asymmetric default — better to start
blank than to leak.

---

## 3 · Public link trust boundary

```
                  ┌──────────────────────────────────┐
                  │   Public ODR Link Boundary       │
                  │   (anonymous · public web)        │
                  │                                  │
                  │   ✅ may: create today's ODR     │
                  │   ✅ may: submit today's ODR     │
                  │   ✅ may: read today's own ODR   │
                  │   ❌ may NOT: preload prior ODR  │
                  │           without continuity      │
                  │   ❌ may NOT: enumerate prior    │
                  │           ODRs for project        │
                  │   ❌ may NOT: trigger admin/PM   │
                  │           override                │
                  └──────────────────────────────────┘
                              │
                              │ (continuity-checked)
                              ▼
              ┌──────────────────────────────────────┐
              │   ODR (private collection · server)   │
              │   prior ODRs · device tokens · logs   │
              └──────────────────────────────────────┘
                              ▲
                              │ (authenticated portal token only)
              ┌──────────────────────────────────────┐
              │   Admin / PM Portal Boundary          │
              │   ✅ may: override preload denial     │
              │   ✅ may: rotate device tokens        │
              │   ✅ may: read preload logs           │
              │   ✅ may: read continuity audit       │
              └──────────────────────────────────────┘
```

The public link surface **never** sees:

- Other crews' prior reports (different `crew_id` / `link_id`).
- Any ODR data when continuity fails (only "start blank" is offered).
- Admin override mechanics (an admin override happens server-side,
  initiated from the authenticated portal; the public surface only
  sees its result if and when the admin grants it).

---

## 4 · Allowed vs forbidden preload data classes

When continuity **passes**, the preload may seed today's blank with:

- Crew roster from prior `manpower.rows[]` (still editable today).
- Equipment list from prior `equipment.rows[]`.
- Subcontractor / vendor list from prior `subcontractors.entries[]`.
- Work area list from prior `work_areas[]`.
- Tomorrow's plan from prior `tomorrow.planned_work` → today's
  "yesterday context" header.
- Production-segment shells (crew_type + primary_operation) — never
  the *values* of LF / tons / structures (today is a new day).

When continuity **fails**, the preload may seed today's blank with:

- **Nothing.** The form opens blank. Sections 1 (Project Snapshot)
  still auto-fills its public, link-scoped fields (project name,
  date, weather) because those come from the link itself, not from
  any prior ODR.

Note: project / weather / date / sunrise-sunset are **not** prior-
ODR data; they come from the link's project metadata and external
weather APIs. They are safe to render regardless of continuity.

---

## 5 · Failure UX (calm copy doctrine)

When continuity fails, the foreman sees a **single calm sentence**
(neutral chrome, not red, not alarming):

```
┌─────────────────────────────────────────────┐
│  We could not verify this is the same       │
│  device that created yesterday's report.    │
│  Start a blank report for today.            │
│                                              │
│  [Start blank report]                       │
└─────────────────────────────────────────────┘
```

No mention of "security", "denied", "unauthorized", or "error".
Per O20 — calm asymmetric default. Foremen who lost their device
or switched browsers simply start blank; PM Review can stitch
context back later from the authenticated portal.

---

## 6 · Admin / PM override (authenticated only)

Override flow:

1. Foreman in the field hits the continuity denial screen and
   contacts PM / Admin (out-of-band).
2. PM / Admin opens the authenticated portal (`/pm/...` or
   `/admin/...`), navigates to the project's ODR list, finds the
   prior ODR.
3. PM / Admin selects "Trust this device for preload" — server
   appends the new device token to the prior ODR's
   `public_access.device_tokens[]` and logs an override row to
   `odr_preload_attempts`.
4. Foreman reloads the public link; continuity now passes; preload
   proceeds.

Override **never** happens from the public link surface. The public
link cannot trigger or simulate an override.

---

## 7 · Preload attempt log (append-only)

Every preload request — successful or not — appends one row to
`odr_preload_attempts`:

```python
class PreloadAttempt(BaseModel):
    attempt_id: str                          # uuid4
    requested_at_utc: str
    public_link_id: str                       # the link the request came through
    project_id: str
    target_report_date: str                   # YYYY-MM-DD
    prior_odr_id: Optional[str]               # the candidate prior ODR (or null)

    # Result
    outcome: Literal[
        "allowed",
        "denied_device_mismatch",
        "denied_missing_token",
        "denied_expired_context",
        "denied_wrong_project",
        "denied_wrong_link",
        "denied_date_out_of_window",
        "denied_gps_conflict",
        "denied_no_prior",
        "override_used",
    ]
    signals_matched: List[str]                # e.g. ["fingerprint","token","project"]
    signals_failed: List[str]
    override_actor_uid: Optional[str]         # when outcome="override_used"
    override_portal: Optional[Literal["pm","admin"]]
    notes: Optional[str]                      # admin-authored when override

    # Forensic
    device_fingerprint_at_request: DeviceFingerprint
    gps_at_request: Optional[GeoFix]
```

Append-only · protected by extended `trendline_integrity_probe.py` ·
read-only from any non-admin surface.

---

## 8 · Operator-configurable knobs (admin-strict only)

| Knob | Default | Range | Effect |
|---|---|---|---|
| `continuity.date_window_days` | `1` | `1..7` | Prior ODR must be within N calendar days of today |
| `continuity.gps_radius_m` | `5000` | `100..50000` | Allowed GPS deviation from project centroid |
| `continuity.gps_required` | `false` | bool | When `true`, signal 6 (GPS) becomes mandatory |
| `continuity.token_ttl_days` | `90` | `7..365` | Device tokens older than this expire |
| `continuity.max_tokens_per_link` | `8` | `1..32` | Cap on the number of trusted devices per project+crew link |

All knobs are admin-strict; the public link surface cannot read or
modify them.

---

## 9 · Probe specification · `odr_public_link_continuity_probe.py` (PLANNED ONLY · no code yet)

Probe scope (when implemented in M0):

1. Asserts every public ODR link route declares the continuity gate
   dependency.
2. Asserts no preload response body returns prior-ODR data unless
   the request carries a valid device token AND the continuity
   engine returned `allowed`.
3. Asserts `odr_preload_attempts` row is written for every preload
   request (success or denial).
4. Asserts `override_actor_uid` is non-null when `outcome="override_used"`.
5. Synthetic test: simulates the same project/link from two
   different fake fingerprints; second one must fail.
6. Synthetic test: simulates a request with the right fingerprint
   but expired token; must fail.
7. Asserts no admin-strict knob is readable from any public route.
8. Cross-checks `LocalizedString` blocks: failure UX copy must
   render in both EN and ES (i18n string table coverage).

Mode: **HARD gate** in `pre_deploy_check.sh` from M0 onward.
**Architecture-only at this stage — no implementation.**

---

## 10 · How this addendum lands in each artifact

| Artifact | Update |
|---|---|
| `ODR_DATA_MODEL.md` | New `PublicAccessBlock` + `DeviceContinuityBlock` + `PreloadAttempt`; ODR envelope grows `public_access` block; new collection `odr_preload_attempts` |
| `ODR_UI_WIREFRAMES.md` | New wireframes: verified-preload (allowed), denied-preload (calm fallback), authenticated override flow inside PM/Admin portal |
| `ODR_ECOSYSTEM_INTEGRATION_MAP.md` | New public-link trust boundary diagram, no-cross-crew rule, prior-report data-exposure prevention contract |
| `ODR_MIGRATION_PLAN.md` | New M0 gate: continuity engine + audit log must be green before any "start from yesterday" surface ships |
| `ODR_SPEC_LOCK_READINESS_REVIEW.md` | New § Public-Link Device Continuity certification (9th confirmation point) |
| `_INDEX.md` | New row under § 4.A pointing to this addendum |

Each artifact carries a short "Public-Link Device Continuity
Addendum" section at the end of its file — added in this revision
pass. Original content + earlier addenda remain authoritative for
their scope; this addendum is read **alongside** the others.

---

## 11 · Doctrine anchors (O11–O20 → spec)

| Doctrine | Anchor |
|---|---|
| O11 (public-link scope) | DATA_MODEL `PublicAccessBlock` + ECOSYSTEM trust boundary |
| O12 (continuity-gated preload) | DATA_MODEL `DeviceContinuityBlock` + UI verified-preload flow |
| O13 (7 continuity signals) | this addendum § 2 + DATA_MODEL `DeviceContinuityBlock.signals` |
| O14 (pass = allow · fail = blank) | UI § failure UX + ECOSYSTEM no-leak rule |
| O15 (no prior-data exposure) | ECOSYSTEM trust boundary + § 4 above |
| O16 (manual blank always allowed) | UI § verified flow + § failure UX |
| O17 (override authenticated only) | UI authenticated override flow + ECOSYSTEM admin boundary |
| O18 (append-only log) | DATA_MODEL `PreloadAttempt` + `odr_preload_attempts` collection · trendline integrity probe extension |
| O19 (applies to every preload surface) | § 4 above enumerates all preload data classes |
| O20 (asymmetric default · blank wins) | § 5 calm copy doctrine + UI fallback |

---

## 12 · Stop condition honoured

- ✅ No implementation
- ✅ No code · no routes · no collections · no UI · no probe code
- ✅ Wave M0 NOT begun
- ✅ Architecture-only revision

Awaiting operator review before specification lock or M0.

_End of Public Link Device Continuity Addendum._
