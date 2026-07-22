# Auth Testing Playbook

- Shared-session portals must send both the portal token header and `X-Directory-Token`.
- Canonical logout endpoint: `/api/auth/multi-logout`.
- Legacy compatibility wrappers:
  - `/api/admin/logout`
  - `/api/pm/logout`
- Required proofs for C2 closeout:
  - multi-login returns directory + portal tokens
  - logout invalidates directory + portal access immediately
  - second tab loses access after first-tab logout
  - browser back cannot revive protected API access
  - fresh re-login restores only the fresh shared session
- Verified suites:
  - `/app/backend/tests/test_c2_15_16_server_side_logout.py`
  - `/app/backend/tests/test_c2_closeout_logout_reconciliation.py`
  - `/app/frontend/src/components/__tests__/c2_closeout_trust_surfaces.test.jsx`