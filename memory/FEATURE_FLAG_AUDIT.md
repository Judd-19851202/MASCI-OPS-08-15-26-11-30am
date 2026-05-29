# FEATURE FLAG AUDIT

_Phase V-Prelude · Deployment Readiness · Track 2 · 2026-05-29T00:19Z_

Inventory of every runtime flag, mount, and probe that gates behavior
across the platform. Source: live grep of `frontend/src/**` +
`backend/server.py` + `backend/routes/**`.

---

## Legend

- **Mechanism** — how the flag is read at runtime.
- **Default** — value when no operator override is present.
- **Owner** — team / surface responsible.
- **Deploy status** — what the production cutover does to this flag.
- **Removal candidate** — `Y` if it is technical debt that should
  graduate to always-on or be deleted; `N` if it is still load-bearing.

---

## 1 · Frontend sidebar V2 flags (query-param gated · iter437 IV-BETA.3B)

All five surfaces share the same pattern: legacy single-column layout
ships by default; the V2 two-column sidebar mounts ONLY when the
operator appends `?<portal>SidebarV2=1` to the URL. Comments in source:
`"iter437 IV-BETA.3B · optional Sidebar V2 mounts behind ?hrSidebarV2=1"`.

| Flag | Mechanism | Active | Default | Owner | Deploy status | Removal candidate |
|---|---|---|---|---|---|---|
| `adminSidebarV2` | `URLSearchParams` | yes | OFF | Admin UX | ships unchanged | N — still load-bearing alt layout |
| `hrSidebarV2` | `URLSearchParams` | yes | OFF | HR UX | ships unchanged | N |
| `safetySidebarV2` | `URLSearchParams` | yes | OFF | Safety UX | ships unchanged | N |
| `dispatchSidebarV2` | `URLSearchParams` | yes | OFF | Dispatch UX | ships unchanged | N |
| `pmSidebarV2` | `URLSearchParams` | yes | OFF | PM UX | ships unchanged | N |

**Notes**

- These flags are stateless per-request (URL only). No localStorage
  pollution, no cookie carry-over.
- The legacy layout is the production default; V2 is an *operator-chosen
  preview* of the eventual default. None of the V2 layouts have been
  promoted to default.
- Each flag is wired into one file pair: `Sidebar*Shell.jsx` +
  `<portal>/sidebar/SideNavV2.jsx`. Removing the flag would require
  promoting the V2 layout to default — out of scope for V-Prelude.

**Verdict**: all five sidebar V2 flags are still pre-graduation
**A/B preview switches**, not technical debt. Keep.

---

## 2 · V-Prelude Wave 1 substrates (always-on · no flag)

| Capability | Default | Owner | Deploy status | Removal candidate |
|---|---|---|---|---|
| `operational_constraints` collection + routes | ON | Operations | ships ON | N |
| `operational_links` collection + routes | ON | Operations | ships ON | N |
| `operational_timeline` collection + routes | ON | Operations | ships ON | N |
| `photo_governance` registry + routes | ON | Operations | ships ON | N |
| `operational_attachments` substrate | ON | Operations | ships ON | N |

No runtime kill-switch. Doctrine documented in
`OPERATIONAL_LINKING_RULES.md`, `OPERATIONAL_TIMELINE_FOUNDATION.md`,
`PHOTO_GOVERNANCE_STANDARD.md`. All five surfaces ship empty on prod
(no operator writes yet) and become populated organically as PMs
exercise the routes.

---

## 3 · Timeline Sidecar (Wave 1.1)

| Capability | Default | Owner | Deploy status | Removal candidate |
|---|---|---|---|---|
| `OperationalTimelineSidecar.jsx` on `/pm/projects/:projectNumber` | ON for PM-token | PM UX | ships ON | N |
| Role visibility gate (PM-token, not anonymous) | enforced | PM UX | ships ON | N |
| Mobile rendering rule (stack-below-content on `< md`) | enforced | PM UX | ships ON | N |

No flag. Calmness contract enforced by `timeline_calmness_probe.py`.

---

## 4 · Governance probes (always-on gates)

| Probe | Mode | Owner | Deploy status | Removal candidate |
|---|---|---|---|---|
| `authority_mismatch_probe.py` | HARD gate | Governance | runs in CI | N — baselined |
| `timestamp_doctrine_probe.py` | HARD gate | Governance | runs in CI | N — baselined |
| `operational_links_doctrine_probe.py` | HARD gate | Governance | runs in CI | N |
| `timeline_calmness_probe.py` | WARN-only (5× = hard) | Governance | runs in CI | N |
| `trendline_integrity_probe.py` | HARD gate | Governance | runs in CI | N |

None of these probes are flag-gated. They run on every deploy via
`scripts/pre_deploy_check.sh`. The two **WARNING-ONLY** governance
stages from iter437 IV-BETA.4 (`verify_coaching_sublines.py`,
`verify_admin_copy.py`, `measure_visual_loudness.py`,
`diff_doctrine_baseline.py`) are explicitly *not* deploy blockers —
they emit trendline data but `return 0`.

---

## 5 · Observation Ledger (Wave 1 follow-on)

| Asset | Default | Owner | Deploy status | Removal candidate |
|---|---|---|---|---|
| `walkthrough_capture.py` | manual-invoke only | Operator | ships ON (no UI) | N |
| `OBSERVATION_LEDGER.json` | append-only ledger | Operator | ships with 1 seed entry | N |
| Snapshot anchor `*.snapshot.json` | auto-refreshed | Probe | ships with current anchor | N |

The ledger has no UI surface and no API surface. Only the operator (or
the agent on operator command, as today) can append.

---

## 6 · Other live flags / env switches (pre-existing · for completeness)

These are inherited from earlier phases and are documented here to
provide a full inventory; none are new in V-Prelude.

| Flag / env | Mechanism | Default | Removal candidate |
|---|---|---|---|
| `APP_ENV` | env var | unset (production) or `preview` | N — protects DB selection |
| `DB_NAME` | env var | `masci_safety` (prod) / `masci_safety_preview` (preview) | N |
| `MFA_ENCRYPTION_KEY` | env var (Fernet) | per-env | N — required for super-admin MFA |
| `BACKUP_VERIFICATION_ENABLED` | env var | `true` | N |
| `BACKUP_VERIFICATION_DAY` / `_HOUR_UTC` | env var | `0` / `14` (Mon 14:00Z) | N |
| `BACKUP_VERIFICATION_MAX_AGE_HOURS` | env var | `36` | N |
| `R2_*` / `S3_*` storage env | env var | per-env | N |
| `SAFETY_EMAIL_TO`, `BACKUP_EMAIL_TO` | env var | per-env | N |
| Sentry DSN (`REACT_APP_SENTRY_DSN`) | env var | configured | N |
| Session timeouts (`ADMIN_HR`, `OPERATIONS`, `FIELD`) | server config | 15/30/60 min idle · 4/8/12h abs | N |
| `?hrSidebarV2=1` etc. (× 5 portals) | query-param | OFF | N (see § 1) |

---

## 7 · Removal candidates

After this audit, **zero flags qualify for removal in V-Prelude
Wave 2.** The five sidebar V2 flags are still pre-graduation
previews; all V-Prelude substrates are always-on by design.

The next plausible removal moment is when one of the V2 sidebars is
promoted to default — at which point its flag becomes dead and should
be deleted in the same pass.

---

## 8 · Pre-deploy verification

```
$ python3 scripts/authority_mismatch_probe.py --gate
new_violations=0 · new_warnings=2 · baselined=58 · scan_ms=426

$ python3 scripts/timestamp_doctrine_probe.py --gate
new_violations=0  new_warnings=0  baselined=81

$ python3 scripts/operational_links_doctrine_probe.py --gate
✅ operational_links doctrine clean.  scanned_rows=0

$ python3 scripts/trendline_integrity_probe.py --gate
TIMELINE_LOUDNESS_TRENDLINE  ✓ clean · entries=5
LOUDNESS_TRENDLINE           ✓ clean · entries=1
OBSERVATION_LEDGER           ✓ clean · entries=1

$ python3 scripts/timeline_calmness_probe.py --iteration "fork-stability-sweep"
score=0.0 · viewports=2 · gate breaches=0
```

All flags + probes consistent. Track 2 ✅ pass.
