# Platform Language Migration · Inventory (Track 18.04)

> Pre-migration baseline scan and post-migration coverage report.
> Source of truth for which user-facing surfaces speak canonical
> Platform Language and which legacy strings are intentionally
> preserved.

---

## Pre-migration baseline (frontend `*.jsx`/`*.js`)

| Legacy term | Files containing (any occurrence) | Risk | Disposition |
|---|---:|:---:|---|
| `Dispatch Portal` | 30 | M | Migrated user-facing copy; internal route names + comments preserved |
| `PM Portal` | 37 | H | Migrated user-facing copy; orphan i18n keys kept |
| `HR Portal` | 40 | H | Migrated user-facing copy; orphan i18n keys kept |
| `Safety Portal` | 47 | H | Migrated user-facing copy; orphan i18n keys kept |
| `Shop Portal` | 32 | M | Migrated user-facing copy; orphan i18n keys kept |
| `Admin Console` | 28 | M | Migrated user-facing copy; in-Transportation surfaces already locked by Track 18.02 |
| `Admin Portal` | 9 | M | Migrated user-facing copy |
| `Office Portals` | 3 | M | Migrated — `Operations` is canonical |
| `PM Hub` | 12 | L | Migrated user-facing CTA copy (`PM Home`); internal references retained |
| `Shop Hub` | 5 | L | Migrated user-facing copy |
| `MASCI Docs` | 2 | L | Reviewed — canonical platform identity is **MASCI Operations Platform**; remaining hits are in print/PDF templates and changelog |
| `Need Help?` | 4 | L | Reviewed — this is a contact card; canonical reference card kept as-is (`Operational Guidance Center` is the help directory) |

## Pre-migration baseline (backend `*.py`)

| Legacy term | Files containing (any occurrence) | Disposition |
|---|---:|---|
| `Dispatch Portal` | 19 | Migrated user-facing strings (subjects, headlines, sub-eyebrows, footer); internal identifiers/docstrings/test names preserved |
| `PM Portal` | 20 | Migrated user-facing; identifiers preserved |
| `HR Portal` | 22 | Migrated user-facing; identifiers preserved |
| `Safety Portal` | 38 | Migrated user-facing; identifiers + collection names preserved |
| `Shop Portal` | 11 | Migrated user-facing; identifiers preserved |
| `Admin Console` | 22 | Migrated user-facing; identifiers + sidebar contracts preserved |
| `Admin Portal` | 9 | Migrated user-facing; identifiers preserved |

---

## Post-migration coverage

| Surface | Compliance | Lock |
|---|:---:|---|
| Hub homepage card titles | ✅ | `test_07–test_13` |
| Hub homepage section header | ✅ | `test_06` |
| CheatSheet printed card | ✅ | (file change; tests cover Hub) |
| DispatchLogin chrome | ✅ | `test_14` |
| HrLogin chrome | ✅ | `test_15` |
| PmLogin chrome | ✅ | `test_16` |
| SafetyLogin chrome | ✅ | `test_17` |
| SafetyFormsLogin ownership banner | ✅ | `test_18` |
| AdminShell sidebar + breadcrumb | ✅ | `test_19` |
| PmShell sidebar + breadcrumb | ✅ | `test_20` |
| HrPageShell kicker | ✅ | `test_21` |
| SafetyShell back-link + kicker | ✅ | `test_22` |
| BackLink auto-resolved labels | ✅ | `test_23` |
| PortalSwitcher labels | ✅ | `test_24` |
| PortalHydratingLoader labels | ✅ | `test_25` |
| PortalLoginHelp labels | ✅ | `test_26` |
| PortalContextBanner labels (EN + ES) | ✅ | `test_27` |
| AdminDispatchUsersPanel eyebrow + toasts | ✅ | `test_28` |
| AdminHRUsersPanel eyebrow | ✅ | `test_29` |
| AdminSafetyUsersPanel eyebrow + helper copy | ✅ | `test_30` |
| AdminFieldLeadershipUsersPanel eyebrow | ✅ | `test_31` |
| branded_portal_emails sub-eyebrows | ✅ | `test_32` |
| operational_footer canonical-name mapping | ✅ | `test_33` |
| Email subjects (all 5 backend modules) | ✅ | `test_34` |
| Email welcome/reset headlines | ✅ | `test_35` |
| Guidance Center article titles | ✅ | `test_36` |
| Guidance Center workspace chips + Hub copy | ✅ | `test_37` |
| Backend admin route prefix preserved | ✅ | `test_38` |
| `X-Dispatch-Token` preserved | ✅ | `test_39` |
| `/api/dispatch/login` contract preserved | ✅ | `test_40` |
| Deployment gate wired | ✅ | `test_41` |
| Constitution registry integrity | ✅ | `test_42` |
| No empty guidance shells | ✅ | `test_43` |

---

## Intentionally deferred / out of scope for 18.04

- Per-feature deep-dive guidance articles (`Pre-Op Inspections Deep Dive`, etc.) keep their established feature names — feature names ≠ workspace names.
- Article BODY prose in `guidance/content.py` may still reference legacy terms in narrative form — Constitution governs labels/titles, not free-prose history.
- Operator-review and changelog `*.md` files preserve legacy names for provenance.
- `i18n.js` orphan keys for legacy strings remain to keep historical bookmarks/translation paths warm; safe to clean up in a later track.

---

## How to verify

```bash
python -m pytest backend/tests/test_track_18_04_platform_language_migration.py -v
python scripts/deployment_gate.py
```
