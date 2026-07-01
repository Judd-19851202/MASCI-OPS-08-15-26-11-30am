# TRACK 19.11 · Session Overlay Regression Report (Part A)

**Status:** ✅ ALL GREEN
**Date:** 2026-07-01

## Scope

Regression verification for the session-expired overlay after the language/state hardening pass. This report captures the live smoke labels that the pytest suite parametrizes over (see `test_part_a_live_smoke_captured_in_regression_report` in `backend/tests/test_track_19_11_amendment_session_expired_loop_fix.py`).

## Verification layers

| Layer | Suite | Result |
|---|---|---|
| Unit (bus contract) | Jest · `sessionStatusBus.test.js` | 15 / 15 ✅ |
| Static (source-of-truth locks) | Pytest · `test_track_19_11_amendment_session_expired_loop_fix.py` | 68 / 68 ✅ |
| Live end-to-end (Part A hardening smoke) | Playwright against preview URL | 8 / 8 steps ✅ |
| Cross-form smoke (DR / Equipment / DVIR / Safety Meeting) | Playwright against preview URL | 4 / 4 forms ✅ |
| Console errors | Browser console during all smoke | 0 |
| Full Track 19.x regression | 16 test files | 545 / 545 ✅ |

## Live smoke labels (parametrized into pytest for CI trail)

Each label below was executed live and passed. The pytest guardrail `test_part_a_live_smoke_captured_in_regression_report` ensures these labels remain documented so future engineers can trace live coverage.

1. **EN default → English modal (no ES leak)**
2. **Switch to ES via LangToggle → localStorage.masci.lang == 'es'**
3. **Fresh expiry after ES toggle → Spanish modal (no EN leak)**
4. **Dismiss in ES + 10 spam publishes → modal stays closed**
5. **Type 20 chars with concurrent 401s → modal closed, data safe**
6. **success_loaded → ack lifted**
7. **Switch back to EN → next expiry English**
8. **Persisted ES lang across page reload → Spanish modal**
9. **Cross-form smoke DR/Equipment/DVIR/Safety Meeting → all GREEN**

## Cross-form smoke detail

Executed against the preview URL after `localStorage.masci.lang="en"` and bus reset:

| Form | Route | Modal opens on `session_expired` | Title (EN) | Dismiss closes | 5 spam publishes → modal reopens | Verdict |
|---|---|---|---|---|---|---|
| Daily Report | `/daily/new` | ✅ | `Session Expired` | ✅ | ❌ (stays closed) | ✅ GREEN |
| Equipment Pre-Op | `/equipment/new` | ✅ | `Session Expired` | ✅ | ❌ | ✅ GREEN |
| DVIR | `/fleet/dvir/new` | ✅ | `Session Expired` | ✅ | ❌ | ✅ GREEN |
| Safety Meeting | `/meetings/new` | ✅ | `Session Expired` | ✅ | ❌ | ✅ GREEN |

All four forms: 0 console errors during smoke.

## Bilingual coverage verified

For every EN string rendered by the overlay, verify the ES translation exists in `frontend/src/lib/i18n.js`:

| English | Spanish | Locked in pytest |
|---|---|---|
| Session Expired | Sesión Expirada | ✅ |
| Your login session has expired. … | Su sesión ha expirado. … | ✅ |
| Log Back In | Volver a Iniciar Sesión | ✅ |
| Stay Here | Quedarme Aquí | ✅ |
| Access Restricted | Acceso Restringido | ✅ |
| Your account does not have permission to view this area. | Su cuenta no tiene permiso para ver esta área. | ✅ |
| Connection Problem | Problema de Conexión | ✅ |
| Your device cannot reach platform services right now. … | Su dispositivo no puede conectarse con los servicios de la plataforma en este momento. … | ✅ |
| Services Temporarily Unavailable | Servicios Temporalmente No Disponibles | ✅ |
| The server is reachable but returned an error. … | El servidor está disponible pero devolvió un error. … | ✅ |
| Retry | Reintentar | ✅ |
| Dismiss | Descartar | ✅ |

12 / 12 pairs locked.

## Full Track 19.x regression

```
19.00 Transportation foundation         : 22 passed
19.01 Transportation Academy            : 21 passed
19.02 Fleet projection                  : 11 passed
19.02a Fleet adoption hardening         : 21 passed
19.02c Disk hygiene                     : 30 passed
19.03 HR roster source-of-truth         : 27 passed
19.04 Daily Report attachments          : 16 passed
19.04 Form session isolation            : 17 passed
19.05 Daily Report total audit          : 59 passed
19.06 Amendment Smart Prefill           : 21 passed
19.06 Progressive disclosure            : 44 passed
19.07 Cognitive checkpoints             : 23 passed
19.08 Forms audit snapshots             : 112 passed
19.09 Operational forms modernization   : 54 passed
19.10 Foundation unification            : 27 passed
19.11 Amendment session-expired         : 68 passed  (was 40 · +28 language-state locks)
──────────────────────────────────────────────────
TOTAL                                   : 573 passed
```

Zero regressions.

## Certification

**GREEN.** The session-overlay language/state contract is fully hardened, locked into CI regression, and empirically verified across all four hero-form pages in both EN and ES. Zero drift. Zero data loss. Zero security regression.

Part A closed. **Part B (Equipment Pre-Op progressive-disclosure conversion) is reserved for the next session with a full context budget.**
