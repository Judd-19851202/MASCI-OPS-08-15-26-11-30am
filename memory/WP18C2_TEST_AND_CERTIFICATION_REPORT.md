# WP18C2 · Test and Certification Report

## Certification Verdict

**WP18C2 certification status: PASS**

## Automated / Agent Evidence

### Backend unit tests added in WP18C2

- File: `/app/backend/tests/test_wp18c2_project_controls_authority.py`
- Result: **3 passed**
- Verified:
  - work-block derivation from cost-code rows keeps resource linkage
  - work-type suggestion logic matches keywords
  - lifecycle derivation prefers archive signal

### Prior foundational test preservation

- WP18C1 hierarchy foundation tests remained passing in previously accepted work.

### Testing agent report

- Report file: `/app/test_reports/iteration_111.json`
- Overall outcome: **PASS**
- Verified by testing agent:
  - Admin project-controls route loads
  - PM project-controls route loads
  - summary cards visible
  - PM project selector works
  - responsive design at mobile width
  - language toggle sanity check passes
  - PM authority actions and backend checks pass

## Manual Runtime Verification Performed

Using live preview/runtime credentials, the following were manually verified against the running backend:

- Admin work-type list endpoint returns **200**
- Admin work-type create endpoint returns **200**
- PM project-controls overview returns **200** for assigned project
- PM pay-item create returns **200**
- PM governed mapping approval returns **200**
- PM lookahead publish/update returns **200**
- PM lifecycle update returns **200**
- PM archive returns **200**
- PM restore returns **200**
- PM crew confirmation returns **200**
- PM unassigned-project access returns **403**

## Daily Report Compatibility Evidence

- Daily Reports with governed contract version after closeout: **3367 / 3367**
- Work ledger rows present: **178**
- Work-block preview UI added on Daily Report V3
- Governed work-block detail section added on Daily Report view

## Smoke Capture

- Preview URL loaded successfully
- Smoke screenshot captured via browser automation before QA handoff

## Non-product Note

The retired `/api/admin/login` path continued to show historical retirement behavior during deep testing. This is **not** a WP18C2 regression because the active admin authentication path for WP18C2 verification used `/api/auth/multi-login` + portal tokens.
