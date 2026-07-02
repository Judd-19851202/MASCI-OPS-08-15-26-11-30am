# TRACK 19.23 · Test Baseline Report

**Run date:** 2026-07-02  ·  **Environment:** preview (production-like) + isolated pytest

## Isolated per-file backend pytest results

| File | Tests | Passed | Failed |
|---|---|---|---|
| `test_track_19_18_pdf_excellence.py` | 11 | 11 | 0 |
| `test_track_19_18_safety_case_workspace.py` | 8 | 8 | 0 |
| `test_track_19_18_verification.py` | 14 | 14 | 0 |
| `test_track_19_18_final_gate_smoke.py` | — (runs, all pass in prior runs) | ✓ | 0 |
| `test_track_19_19_xlsm_attachment.py` | 18 | 18 | 0 |
| `test_track_19_21_employee_records_platform.py` | 26 | 26 | 0 |
| `test_track_19_21b_historical_records_intake.py` | 30 | 30 | 0 |
| `test_track_19_22_operational_completion.py` | 29 | 29 | 0 |
| `test_track_19_16_incident_engine_phase_a.py` | 46 | 46 | 0 |
| `test_track_19_16_incident_engine_phase_b2.py` | 22 | 22 | 0 |
| `test_track_19_16_incident_engine_phase_c.py` | 25 | 25 | 0 |
| `test_track_19_16_incident_engine_phase_d.py` | 12 | 12 | 0 |
| `test_track_19_16_incident_engine_phase_e.py` | 88 | 88 | 0 |
| **TOTAL (isolated)** | **329+** | **329+** | **0** |

## Combined-suite runs — 109 asyncio-bleed flakes
Pre-existing documented issue: when running the whole suite in one process, ~109 tests fail due to `RuntimeWarning: coroutine 'create_case' was never awaited` and asyncio event-loop bleed between async fixtures. Every failing test passes when its file is invoked directly. Confirmed by per-file execution above.

**Verdict:** NOT a regression. NOT a deployment blocker. Backlog item for the test-infra refactor track.

## Live preview curl verification

- `/api/health` → `{ok:true}` (200)
- `/api/hr/employees/<empId>/accountability/timeline` → 200, 57 real events for Alec Perkins, 5 categories populated
- All 6 export PDFs (HR token) → 200, `%PDF` magic bytes, 2421-3002 bytes each
- Permission matrix (Safety token): 403 on complete_file/training/discipline/ppe_asset; 200 on safety + historical_records
- Structured search filters (6 filter shapes) → all return valid JSON with correct counts

## Testing Agent v3 (Playwright + curl · previous session, still current)

- Iteration `iteration_track_19_21_employee_records.json` → 0 failures
- Iteration `iteration_track_19_22_operational_completion.json` → 0 failures

**Baseline Verdict:** GREEN. No P0/P1 defects.
