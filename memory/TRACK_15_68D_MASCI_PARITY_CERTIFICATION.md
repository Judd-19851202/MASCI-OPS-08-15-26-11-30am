# TRACK 15.68D · MASCI Parity Certification

_Generated 2026-06-22_

## Objective

Prove that none of the Track 15.68D edits regressed the MASCI tenant.
MASCI must look, route, send, and read 100% identically to its
pre-Track-15.68D state.

## Probes

### 1. Email-routing parity (Track 15.65 harness, 19 routes)

```
cd /app/backend && python3 scripts/track_15_65_parity_verify.py
```

Result:

```
{
  "match": 19,
  "mismatch": 0,
  "skipped_no_legacy": 3,
  "critical_empty": 0
}
```

Persisted artefacts:

- `/app/test_reports/track_15_65_parity.json`
- `/app/memory/track_15_65_data/parity_summary.md`

All 19 production routes resolve to the same recipient set under both
`EMAIL_ROUTING_V2=false` (legacy env path) and
`EMAIL_ROUTING_V2=true` (DB-first path). Zero drift.

### 2. Visual chrome parity (MASCI default tenant, no preview)

Browser session with `sessionStorage` cleared (no `branding.previewTenant`).

| Surface | Title | Logo | Footer attribution | MASCI labels intact? |
|---|---|---|---|---|
| `/` (Hub) | `MASCI Operations Platform` | red MASCI mark | `MASCI Operations Platform · Powered by ForgedOps™` | ✅ |
| `/sign-in` | `MASCI Operations Platform` | red MASCI mark | `MASCI HUB OPERATIONS PLATFORM · MASTER SIGN-IN · POWERED BY FORGEDOPS™` | ✅ |
| `/admin/login` | `MASCI Operations Platform` | red MASCI mark | `MASCI Hub · Office Use Only` | ✅ |
| `/safety` | `MASCI Operations Platform` | red MASCI mark | (chrome present) | ✅ |
| `/field` | `MASCI Operations Platform` | red MASCI mark | (chrome present) | ✅ |

### 3. Spot-check translation parity

| Probe | MASCI tenant value |
|---|---|
| `tStr("MASCI Operations Platform")` | `"MASCI Operations Platform"` |
| `tStr("MASCI Safety Hub")` | `"MASCI Safety Hub"` |
| `tStr("MASCI Crews on Site")` (es) | `"Cuadrillas MASCI en Sitio"` |

`_brandSubst()` short-circuits when both `brand` and `company` resolve
to `"MASCI"`. The original string is returned untouched.

### 4. Admin chrome parity

Re-loaded the 5 admin tabs on the MASCI tenant — `MasciLogo` resolves to
the MASCI mark, footer attribution resolves to "MASCI Hub · Office Use
Only", and the dispatch QR card prints `MASCI · DRIVER SHIFT START`
because the default `carrierLabel` is now derived from
`branding.company_name`, which is `"MASCI"` for the masci tenant.

## Verdict

✅ **PASS** — 19/19 routes match, all chrome surfaces render the legacy
MASCI strings, document title shows `MASCI Operations Platform`. Zero
regression.
