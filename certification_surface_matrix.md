# Certification Surface Matrix

| ID | Phase | Surface | Status | Evidence |
|---|---:|---|---|---|
| LEG-001 | 1 | `POST /api/admin/login` | PASS | `iteration_31.json` |
| LEG-002 | 1 | `GET /api/hr/check` | PASS | `iteration_31.json` |
| LEG-003 | 1 | Legacy FL shared-secret auth | PASS | `iteration_31.json`, `iteration_32.json` |
| LEG-004 | 1 | Forced-password-change fixture | PASS | `iteration_31.json`, `ops8_phase2_3_4_backend_cert_results.json` |
| LEG-005 | 1 | Admin incident review contract | PASS | `iteration_30.json`, `iteration_32.json` |
| LEG-006 | 1 | PM/Safety incident review contract | PASS | `iteration_32.json` |
| LEG-007 | 1 | Backup integrity operator workflow | PASS | `iteration_31.json`, `iteration_32.json` |
| AUTH-001 | 2 | Disabled-user handling | PASS | `ops8_phase2_3_4_backend_cert_results.json` |
| AUTH-002 | 2 | Invalid credentials / no enumeration | PASS | `ops8_phase2_3_4_backend_cert_results.json` |
| AUTH-003 | 2 | Stale token handling | PASS | `ops8_phase2_3_4_backend_cert_results.json` |
| AUTH-004 | 2 | Logout revocation | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| AUTH-005 | 2 | Dual-token enforcement | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| AUTH-006 | 2 | Repeated portal switching | PASS | `ops8_phase2_3_4_backend_cert_results.json` |
| AUTH-007 | 2 | Refresh/new-tab continuity | PASS | `iteration_32.json` |
| AUTH-008 | 2 | Password-changed session handling | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_31.json` |
| AUTH-009 | 2 | Idle session expiration | NOT_YET_EXERCISED | Preview timeouts disabled |
| AUTH-010 | 2 | Absolute session expiration | NOT_YET_EXERCISED | Preview timeouts disabled |
| AUTH-011 | 2 | Portal-grant removal effect | BLOCKED | Unsafe to mutate Preview grants |
| AUTH-012 | 2 | Brute-force / lockout | DOCUMENTED | `test_track_24_1_hardening.py` |
| FILE-001 | 3 | Daily Reports | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| FILE-002 | 3 | Incidents | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| FILE-003 | 3 | Inspections | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| FILE-004 | 3 | Equipment Pre-Ops / DVIR | NOT_SUPPORTED_IN_CURRENT_PRODUCT | `ops8_phase2_3_4_backend_cert_results.json` |
| FILE-005 | 3 | JHA/JHP | NOT_SUPPORTED_IN_CURRENT_PRODUCT | `ops8_phase2_3_4_backend_cert_results.json` |
| FILE-006 | 3 | Safety Meetings endpoint workflow | NOT_SUPPORTED_IN_CURRENT_PRODUCT | `ops8_phase2_3_4_backend_cert_results.json` |
| FILE-007 | 3 | PDF rendering regressions | DOCUMENTED | `test_sm_pdf_001_meeting_layout.py` |
| FILE-008 | 3 | Upload workflows | DOCUMENTED | `test_track_24_11b_universal_upload.py` |
| TRUST-001 | 4 | Trust events logging | PASS | `ops8_phase2_3_4_backend_cert_results.json`, `iteration_32.json` |
| TRUST-002 | 4 | Notification mode / queue posture | PASS | `ops8_phase2_3_4_backend_cert_results.json` |
| TRUST-003 | 4 | Real live-recipient delivery | NOT_YET_EXERCISED | Preview SAFE_CAPTURE |
| DEV-001 | 5 | Async backup integrity workflow | PASS | `iteration_31.json`, `iteration_32.json` |
| DEV-002 | 5 | Restore drill / actual recoverability | NOT_YET_EXERCISED | Separate restore evidence required |
| DEVICE-001 | 6 | Desktop browser regression | PASS | `iteration_32.json` |
| DEVICE-002 | 6 | iPad Safari | NOT_YET_EXERCISED | Physical device required |
| DEVICE-003 | 6 | iPhone Safari | NOT_YET_EXERCISED | Physical device required |
| DEVICE-004 | 6 | Android Chrome | NOT_YET_EXERCISED | Physical device required |
| DEVICE-005 | 6 | Windows Edge | NOT_YET_EXERCISED | Physical device required |
| DEVICE-006 | 6 | Mac Safari/Chrome physical verification | NOT_YET_EXERCISED | Physical device required |