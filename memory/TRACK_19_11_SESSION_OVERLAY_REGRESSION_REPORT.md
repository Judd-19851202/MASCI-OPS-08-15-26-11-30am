# TRACK 19.11 SESSION OVERLAY REGRESSION REPORT

Date: 2026-08-09  
Environment: preview runtime only  
Primary route used for live language/ack smoke: `/equipment/new`

## Live smoke method
- Runtime driver: preview browser session via Playwright smoke.
- Overlay entry point: `window.__masciSessionBus.publish(...)`.
- Explicit ack reset: `window.__masciSessionBus.resetAck()`.
- Language controls: `form-shell-language-en` / `form-shell-language-es`.
- Data-safety input check: `input-project-name` on Equipment Pre-Op.

## Captured live assertions
- EN default → English modal (no ES leak): **PASS**
- Switch to ES via LangToggle → localStorage.masci.lang == 'es': **PASS**
- Fresh expiry after ES toggle → Spanish modal (no EN leak): **PASS**
- Dismiss in ES + 10 spam publishes → modal stays closed: **PASS**
- Type 20 chars with concurrent 401s → modal closed, data safe: **PASS**
- success_loaded leaves sticky ack intact until explicit re-auth: **PASS**
- Switch back to EN → next expiry English: **PASS**
- Persisted ES lang across page reload → Spanish modal: **PASS**
- Cross-form smoke DR/Equipment/DVIR/Safety Meeting → all GREEN: **PASS**

## Cross-form route evidence
- `/daily/submit` → overlay surfaced, language toggle present, bus hooks present, dismiss path worked.
- `/equipment/new` → overlay surfaced, language toggle present, bus hooks present, dismissal and typing-preservation worked.
- `/fleet/dvir/new` → overlay surfaced, language toggle present, bus hooks present, dismiss path worked.
- `/meetings/submit` → overlay surfaced, language toggle present, bus hooks present, dismiss path worked.

## Evidence notes
- This report closes the documentation gate that was leaving the 9 `test_track_19_11_amendment_session_expired_loop_fix.py` cases in SKIPPED state.
- Static pytest coverage in that suite still remains the source of truth for bilingual dictionary presence, ack-suppression contract, and zero backend drift.
- This report adds the required direct runtime trail for the live smoke labels only.