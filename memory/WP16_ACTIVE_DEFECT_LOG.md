# WP16 Active Defect Log

Date: 2026-07-30

## Phase 6 foundation checkpoint note
- Shared foundation implementation is complete on representative admin routes.
- Foundation-level responsive issue found during checkpoint verification:
  - `WP16-FND-001` — tablet landscape (`1024x768`) horizontal overflow in the authenticated shell.
  - Status: **resolved during checkpoint** by moving full desktop shell behavior to the `xl` breakpoint.
- There are **no active foundation-level P0 defects** after the fix above.
- The portal/API defects listed below remain open and must be handled during the appropriate portal migration waves unless they block future certification.

## Phase 4 checkpoint note
- No runtime fixes were attempted.
- The table below now records whether each accepted defect prevents base-screen, interaction, overlay, validation, state, or workflow-transition inspection.

| Defect ID | Affected portal | Affected routes | Current status | Screenshot refs | Prevents base-screen inspection? | Prevents interaction inspection? | Prevents overlay inspection? | Prevents validation inspection? | Prevents state inspection? | Prevents workflow-transition inspection? | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WP16-DEF-001 | HR | Exact route set unresolved; notification surfaces | Open / documented only | — | Partial | Partial | Unknown | Unknown | Partial | Partial | Notification-route scope remains unresolved from earlier evidence. |
| WP16-DEF-002 | HR | `/hr` | Open / documented only | `WP16-EVID-HR-HOME.jpeg`, `wp16_p3_hr_auth_001_home.jpeg` | Partial | Partial | No | No | Yes | No | 403 from `/api/hr/employee-completeness`; home shell still visible. |
| WP16-DEF-003 | HR | `/hr/employees` | Open / documented only | `WP16-EVID-HR-EMPLOYEES.jpeg`, `hr_employees_bucket_filter_open_desktop_21.png`, `hr_employees_add_dialog_desktop_22.png` | Partial | Partial | Partial | No | Yes | Partial | 403 employee-list failures reduce row-based interactions. |
| WP16-DEF-004 | Dispatch | `/dispatch-portal` | Open / documented only | `WP16-EVID-DISPATCH-HOME.jpeg`, `wp16_p3_dispatch_004_home_partial.jpeg` | No | No | No | N/A | Partial | No | MaintainX defect-coverage panel is partially hidden by 401. |
| WP16-DEF-005 | Dev | `/dev/login`, `/dev` | Open / documented only | `wp16_dev_01_login_page.jpeg`, `wp16_dev_02_login_blocked_error.jpeg`, `wp16_dev_03_dev_route_redirected_login.jpeg` | Partial | Yes | N/A | Partial | Yes | Yes | Preview config blocks dev token issuance; hub remains inaccessible. |
| WP16-DEF-006 | HR | `/hr/field-leadership-users`, `/hr/employee-accountability`, `/hr/time-off`, `/hr/driver-qualification`, `/hr/driver-qualification/import`, `/hr/motive-drivers`, `/hr/employee-requests` | Open / documented only | `wp16_p3_hr_auth_005_field_leadership_users.jpeg`, `wp16_p3_hr_auth_006_employee_accountability.jpeg`, `wp16_p3_hr_auth_008_time_off.jpeg`, `wp16_p3_hr_auth_012_driver_qualification.jpeg`, `wp16_p3_hr_auth_013_driver_qualification_import.jpeg`, `wp16_p3_hr_auth_015_motive_drivers.jpeg`, `wp16_p3_hr_auth_017_employee_requests.jpeg` | No | Partial | Partial | Partial | Yes | Yes | Mixed 401/403/404/405 failures degrade several HR sub-workflows after route load. |
| WP16-DEF-007 | HR | `/hr/historical-records/intake` | Open / documented only | `wp16_p3_hr_auth_018_historical_intake.jpeg` | Partial | Yes | No | Yes | Yes | Yes | 500 on `/api/employee-records/vocabulary` blocks meaningful intake progression. |
| WP16-DEF-009 | Shop | `/shop/asset-care`, `/shop/trench-safety-repairs`, `/shop/equipment` | Open / documented only | `wp16_p3_shop_006_asset_care.jpeg`, `wp16_p3_shop_018_trench_safety_repairs.jpeg`, `wp16_p3_shop_020_equipment.jpeg` | Partial | Partial | No | No | Yes | Partial | 401s degrade dashboard/panel data while leaving shell chrome visible. |
| WP16-DEF-011 | Dispatch | `/dispatch-portal/fleet` | Open / documented only | `wp16_p3_dispatch_009_fleet.jpeg` | Partial | Partial | No | No | Yes | Partial | 401 from `/api/operations/intelligence/fleet-gps` degrades live fleet content. |
| WP16-DEF-012 | Admin | `/admin/qaqc`, `/admin/trench-safety/excavations`, `/admin/equipment`, `/admin/meetings` | Open / documented only | `wp16_p3_admin_002_qaqc.jpeg`, `wp16_p3_admin_018_trench_excavations.jpeg`, `wp16_p3_admin_019_equipment.jpeg`, `wp16_p3_admin_021_meetings.jpeg` | Partial | Partial | Partial | No | Yes | Partial | 401s affect high-signal admin workspaces even under valid admin auth. |
