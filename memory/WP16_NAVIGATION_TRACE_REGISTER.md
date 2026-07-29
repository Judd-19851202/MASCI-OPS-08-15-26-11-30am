# WP16 Navigation Trace Register

Date: 2026-07-29

## Phase 2 status
- Phase 2 used a mixed strategy: exhaustive route openings for breadth, plus representative real in-UI navigation traces for high-risk entry points, nested items, modals, drawers, tabs, and detail launches.
- The register below records the highest-signal traces gathered during the zero-evidence-family pass.

## Exact current totals
| Metric | Exact total | Note |
| --- | ---: | --- |
| Navigation elements traced from real in-UI launch points | 37 | Includes Phase 1 seed login traces plus Phase 2 in-UI launches. |
| Direct URL evidence openings recorded | 109 | Used to exhaustively reach route-backed surfaces without changing runtime code. |
| Dead-end screens documented | 5 | Includes spent magic-link, invite unavailable, certificate not found, dev-login blocked, and dev-route redirect-to-login states. |
| Screens without clear return path documented | 4 | Includes poster/packet-like dedicated surfaces and tokenized dead-end states. |

## Representative rows from Phase 2 evidence
| Trace ID | Visible label | Icon | Source screen | Destination | Role context | Opened successfully? | Destination matched label? | Duplicate destination? | Intuitive? | Return path confirmed? | Back / Close / Cancel / Home available? | Operator trap risk | Evidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| NAV-P2-001 | Field Leadership login submit | — | `/field-leadership/portal/login` | `/leadership` | Field Leadership authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_fl_03_portal_login.jpeg`, `wp16_fl_04_leadership_hub.jpeg` | Successful portal login flow. |
| NAV-P2-002 | Forgot password | — | `/leadership/login` | Forgot-password modal | Field Leadership login context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_fl_01_leadership_login.jpeg`, `wp16_fl_02_login_forgot_modal.jpeg` | Modal overlay captured without submitting a write action. |
| NAV-P2-003 | First leadership record row | — | `/leadership/records` | `/leadership/records/:id` | Field Leadership authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_fl_06_records_list.jpeg`, `wp16_fl_07_record_detail.jpeg` | First reachable record detail launched from list. |
| NAV-P2-004 | Lookup result row | — | `/field-leadership/portal/dashboard` | Lookup widget state | Field Leadership authenticated | Yes | Yes | No | Yes | Yes | Yes | Medium | `wp16_fl_10_lookup_results.jpeg`, `wp16_fl_11_lookup_widget.jpeg` | Search-driven nested state capture. |
| NAV-P2-005 | Driver qualification row | — | `/field-leadership/portal/driver-qualification` | Qualification drawer | Field Leadership authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_fl_12_driver_qualification.jpeg`, `wp16_fl_13_driver_qualification_drawer.jpeg` | Drawer-backed detail state captured. |
| NAV-P2-006 | Dispatch login submit | — | `/dispatch-portal/login` | `/transportation-operations` | Dispatch authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_dispatch_01_dispatch_login.jpeg`, `wp16_tx_dispatch_02_wrapper_mission_control.jpeg` | Wrapper-entry login trace. |
| NAV-P2-007 | New rate version | — | `rate-schedules` | Rate dialog | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_08_rate_schedules.jpeg`, `wp16_tx_admin_09_rate_new_dialog.jpeg` | Modal opened without saving. |
| NAV-P2-008 | Add carrier | — | `carriers` | Add-carrier dialog | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_12_carriers_list.jpeg`, `wp16_tx_admin_13_add_carrier_modal.jpeg` | Create modal captured without submit. |
| NAV-P2-009 | Edit carrier | — | `carriers` | Edit-carrier dialog | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_12_carriers_list.jpeg`, `wp16_tx_admin_14_edit_carrier_modal.jpeg` | Edit dialog captured without submit. |
| NAV-P2-010 | Carrier open | — | `carriers` | `carriers/:id` | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_15_carrier_workspace_overview.jpeg` | First reachable carrier workspace launched from list. |
| NAV-P2-011 | Carrier tabs | — | `carriers/:id` | Drivers / Trucks / Packet / Documents / Rates | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_16_carrier_workspace_drivers.jpeg`, `wp16_tx_admin_17_carrier_workspace_trucks.jpeg`, `wp16_tx_admin_18_carrier_workspace_packet.jpeg`, `wp16_tx_admin_19_carrier_workspace_documents.jpeg`, `wp16_tx_admin_20_carrier_workspace_rates.jpeg` | Tab strip traversed fully. |
| NAV-P2-012 | Add leased driver | — | `drivers` | Add-leased-driver modal | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_21_drivers_list.jpeg`, `wp16_tx_admin_22_add_leased_driver_modal.jpeg` | Create modal captured without submit. |
| NAV-P2-013 | Link HR driver | — | `drivers` | Link-HR dialog | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_23_link_hr_driver_modal.jpeg` | Link dialog captured without submit. |
| NAV-P2-014 | Truck open | — | `trucks` | `trucks/:id` | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Medium | `wp16_tx_admin_25_trucks_list.jpeg`, `wp16_tx_admin_27b_truck_workspace_detail.jpeg` | Truck detail route launched from list. |
| NAV-P2-015 | Start inspection | — | `trucks/:id` | Inspection wizard | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Medium | `wp16_tx_admin_28_truck_workspace_inspection_wizard.jpeg` | Wizard captured without completing write flow. |
| NAV-P2-016 | Orientation module link | — | `orientation/modules` | `modules/:mid` | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_30_orientation_modules.jpeg`, `wp16_tx_admin_31_orientation_module_detail.jpeg` | First reachable module detail opened. |
| NAV-P2-017 | Academy module link | — | `academy` | `academy/:moduleKey` | Transportation admin context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tx_admin_35_academy_catalog.jpeg`, `wp16_tx_admin_36_academy_module_detail.jpeg` | First reachable academy module opened. |
| NAV-P2-018 | Driver lookup option | — | `/shift` | Selected driver state | Driver mobile context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_driver_01_shift_start.jpeg`, `wp16_driver_02_shift_driver_lookup.jpeg` | Driver search result selected from lookup list. |
| NAV-P2-019 | Truck lookup option | — | `/shift` | Selected truck state | Driver mobile context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_driver_03_shift_truck_lookup.jpeg` | Truck search result selected from lookup list. |
| NAV-P2-020 | Shift start submit | — | `/shift` | `/driver` | Driver mobile context | Yes | Yes | No | Yes | Yes | Yes | Medium | `wp16_driver_04_driver_session_no_assignment.jpeg` | Produced no-assignment baseline driver view. |
| NAV-P2-021 | Guidance section card | — | `/guidance` | `/guidance/section/:sectionId` | Shared public context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tg_07_guidance_home_public.jpeg`, `wp16_tg_09_guidance_section_view.jpeg` | First reachable section opened from guidance home. |
| NAV-P2-022 | Guidance article row | — | `/guidance/section/:sectionId` | `/guidance/:articleId` | Shared public context | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tg_09_guidance_section_view.jpeg`, `wp16_tg_10_guidance_article_view.jpeg` | First reachable article opened from section list. |
| NAV-P2-023 | Admin login submit | — | `/admin/login` | Admin-authenticated training/executive context | Admin authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_tg_11_training_admin_track_authed.jpeg`, `wp16_exec_02_overview_canonical.jpeg` | Re-used as the authenticated entry point for multiple Phase 2 families. |
| NAV-P2-024 | Executive refresh | — | `/admin/executive-overview` | Refreshed overview KPI state | Admin authenticated | Yes | Yes | No | Yes | Yes | Yes | Low | `wp16_exec_02_overview_canonical.jpeg`, `wp16_exec_03_overview_refreshed.jpeg` | Non-mutating refresh interaction captured. |
| NAV-P2-025 | Dev login submit | — | `/dev/login` | Blocked error state | Internal/dev-only context | No | Yes | No | Yes | No | N/A | High | `wp16_dev_01_login_page.jpeg`, `wp16_dev_02_login_blocked_error.jpeg` | Login submit hit the preview-config block documented as `WP16-DEF-005`. |
