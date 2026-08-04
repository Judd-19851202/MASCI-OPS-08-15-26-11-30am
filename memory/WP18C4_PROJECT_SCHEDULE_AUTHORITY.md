# WP-18C4 Project Schedule Authority

## Status
- Date: 2026-08-04
- Result: **GO**
- Scope: additive implementation only

## What was implemented
- Versioned project schedule authority in `backend/services/project_schedule_authority.py`
- PM/admin API surface in `backend/routes/enterprise_governance.py`
- PM governed schedule workspace at `/pm/project-controls/schedule`
- Admin schedule governance workspace at `/admin/governance/project-controls/schedule`
- Sidebar and route discoverability for both PM and admin users

## Constitutional chain preserved
`Project → Phase → Work Package → Schedule Activity → Budget Line → Customer Pay Item → Enterprise Work Type → Operational Work Block → Daily Report → Actual Production`

## Governance rules implemented
- CSV is the runtime-certified import lane
- P6 / MS Project / Excel / PDF review-assisted lanes are extension-ready only
- No silent normalization
- No silent approval
- No silent activation
- Baseline versions remain preserved
- Lookahead remains an overlay, not a duplicate schedule
- Daily Reports remain actual-execution truth

## Planned assignment coverage
- Crew
- Employees
- Equipment
- Materials
- Vendors
- Subcontractors
- Production quantity
- Planned hours
- Structured constraints

## Export readiness implemented
- Master Schedule CSV
- Two-Week Lookahead CSV
- Four-Week Lookahead CSV
- Crew Plan CSV
- Equipment Plan CSV
- Material Plan CSV
- Work Package Plan CSV