# WP-17B Coaching Standard

## Exact coaching/help findings: `11`

## Named coaching/help owners audited
1. `backend/routes/guidance_routes.py`
2. `backend/routes/odr/guidance_catalog.py`
3. `backend/routes/odr/guidance_routes.py`
4. `frontend/src/components/HelpDrawer.jsx`
5. `frontend/src/components/HelpTip.jsx`
6. `frontend/src/components/operational_intelligence/GuidanceCard.jsx`
7. `frontend/src/components/operational_intelligence/guidanceMap.js`
8. `frontend/src/components/ui/HelpTip.jsx`
9. `frontend/src/components/ui/tooltip.jsx`
10. `frontend/src/pages/admin/AdminGuidanceCoverage.jsx`
11. `frontend/src/pages/guidance/OperationalGuidanceCenter.jsx`

## Findings
- KPI help is strongest where metadata-backed HelpTips already exist.
- “Training Center” is useful but not linked consistently from every portal.
- Some portals coach inline; others defer to a separate guidance center.
- Coaching tone is generally calm and operational, but placement is not standardized.

## Canonical coaching rule
- Inline help for “what this number means”
- Drawer/help center for “how to do the task”
- Guidance center for role-based learning and reference
- No mystery icons; every help affordance must declare purpose clearly

## Disposition
- Existing help primitives: `KEEP`
- Placement and label inconsistency: `STANDARDIZE`