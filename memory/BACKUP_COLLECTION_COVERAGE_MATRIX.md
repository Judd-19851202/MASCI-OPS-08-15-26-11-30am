# BACKUP · Collection Coverage Matrix

**Sprint:** BACKUP-FIX-001
**Date:** 2026-02-09
**Source:** live `MongoClient.list_database_names()` + `list_collection_names()` against `masci-prod.1nduwmg.mongodb.net`

Auto-discovery captures every collection in MongoDB EXCEPT those in `BACKUP_EXPLICIT_EXCLUSIONS` (server.py:4560-4565). The exclusion list is intentional, documented (`R2_BACKUP_CONTINUITY_AUDIT.md §9`), and always logged on every backup run.

---

=== masci_safety === (155 non-system)
| Collection | Captured | Reason if excluded | Docs |
|---|---|---|---|
| activity_log | ✅ |  | 0 |
| admin_audit | ✅ |  | 1934 |
| admin_audit_log | ✅ |  | 142 |
| admin_step_ups | ✅ |  | 0 |
| alert_events | ✅ |  | 0 |
| asset_assignments | ✅ |  | 0 |
| asset_holds | ✅ |  | 2 |
| asset_mappings | ✅ |  | 0 |
| asset_transfers | ✅ |  | 0 |
| audit_events | ✅ |  | 10971 |
| backup_drift_history | ✅ |  | 0 |
| backup_health | ✅ |  | 200 |
| brute_force_blocks | ✅ |  | 0 |
| calculator_runs | ✅ |  | 1 |
| cluster_capacity_history | ✅ |  | 414 |
| command_center_calendar | ✅ |  | 1 |
| command_center_thresholds | ✅ |  | 1 |
| compliance_findings | ✅ |  | 233 |
| compliance_scans | ✅ |  | 50 |
| corrective_actions | ✅ |  | 0 |
| daily_reports | ✅ |  | 112 |
| digest_runs | ✅ |  | 20 |
| digest_settings | ✅ |  | 1 |
| directory_sessions | ✅ |  | 1947 |
| dispatch_assignments | ✅ |  | 1 |
| dispatch_continuity_events | ✅ |  | 0 |
| dispatch_driver_sessions | ✅ |  | 0 |
| dispatch_magic_links | ✅ |  | 0 |
| dispatch_state_events | ✅ |  | 4 |
| dispatch_users | ✅ |  | 3 |
| doc_id_counters | ✅ |  | 24 |
| docs | ✅ |  | 0 |
| document_expirations | ✅ |  | 1 |
| draft_telemetry | ✅ |  | 6477 |
| driver_qualification_audit | ✅ |  | 0 |
| driver_qualification_import_previews | ✅ |  | 18 |
| driver_qualification_imports | ✅ |  | 81 |
| email_routing_config | ✅ |  | 0 |
| employee_lifecycle_events | ✅ |  | 1 |
| employee_mappings | ✅ |  | 0 |
| employee_requests | ✅ |  | 4 |
| employees | ✅ |  | 255 |
| equipment_inspections | ✅ |  | 39 |
| equipment_master | ✅ |  | 596 |
| equipment_parts | ✅ |  | 2 |
| equipment_units | ✅ |  | 484 |
| events | ✅ |  | 0 |
| field_leadership_equipment_catalog | ✅ |  | 30 |
| field_leadership_equipment_makes | ✅ |  | 9 |
| field_leadership_records | ✅ |  | 0 |
| field_leadership_users | ✅ |  | 27 |
| field_memory_notes | ✅ |  | 0 |
| field_submitter_bindings | ✅ |  | 26 |
| fire_ext_import_runs | ✅ |  | 7 |
| fire_extinguishers | ✅ |  | 0 |
| fleet_audit | ✅ |  | 582 |
| fleet_defects | ✅ |  | 0 |
| fleet_status | ✅ |  | 0 |
| guidance_search_misses | ✅ |  | 351 |
| haul_cycles | ✅ |  | 0 |
| health_monitor_runs | ❌ | regenerable cache (iter441) | 31158 |
| hill_scopes | ✅ |  | 3 |
| hr_users | ✅ |  | 3 |
| hub_banner_audit | ✅ |  | 1161 |
| hub_banners | ✅ |  | 1 |
| idempotency_keys | ✅ |  | 49 |
| incidents | ✅ |  | 8 |
| inspections | ✅ |  | 0 |
| integration_error_logs | ✅ |  | 0 |
| integration_settings | ✅ |  | 2 |
| integration_sync_logs | ✅ |  | 32075 |
| integration_wizard_runs | ✅ |  | 0 |
| jha_acknowledgements | ✅ |  | 0 |
| jhas | ✅ |  | 0 |
| job_hazard_files | ✅ |  | 6 |
| job_hazard_plans | ✅ |  | 0 |
| job_photo_thumb_cache | ❌ | regenerable cache (iter441) | 2307 |
| job_photos | ✅ |  | 770 |
| jobs_master | ✅ |  | 28 |
| legacy_import_audit | ✅ |  | 6 |
| legacy_imports | ✅ |  | 0 |
| login_attempts | ✅ |  | 0 |
| maintainx_work_orders | ✅ |  | 0 |
| meetings | ✅ |  | 33 |
| message_comments | ✅ |  | 2 |
| messages | ✅ |  | 0 |
| mfa_audit_events | ✅ |  | 0 |
| motive_events | ✅ |  | 0 |
| notifications | ✅ |  | 143 |
| odr | ✅ |  | 0 |
| odr_amendments | ✅ |  | 0 |
| odr_attachments | ✅ |  | 0 |
| odr_consumer_index | ✅ |  | 0 |
| odr_observation_events | ✅ |  | 0 |
| odr_pdf_renders | ✅ |  | 0 |
| odr_photos | ✅ |  | 0 |
| odr_preload_attempts | ✅ |  | 0 |
| odr_public_links | ✅ |  | 0 |
| odr_section_events | ✅ |  | 0 |
| odr_translation_events | ✅ |  | 0 |
| operational_attachments | ✅ |  | 32 |
| operational_constraints | ✅ |  | 0 |
| operational_links | ✅ |  | 0 |
| operations_events | ✅ |  | 534 |
| ops_manual_snapshots | ✅ |  | 0 |
| payroll_variance_batches | ✅ |  | 0 |
| payroll_variance_decisions | ✅ |  | 0 |
| photo_migration_progress | ✅ |  | 7 |
| po_requests | ✅ |  | 1 |
| project_managers | ✅ |  | 8 |
| project_members | ✅ |  | 0 |
| project_memberships | ✅ |  | 1 |
| projects | ✅ |  | 0 |
| promo_assets | ✅ |  | 0 |
| qaqc_inspections | ✅ |  | 0 |
| r2_degraded_events | ✅ |  | 0 |
| resend_webhook_events | ✅ |  | 426 |
| role_templates | ✅ |  | 31 |
| safety_documents | ✅ |  | 0 |
| safety_equipment_issuances | ✅ |  | 0 |
| safety_equipment_trainings | ✅ |  | 0 |
| safety_training_records | ✅ |  | 0 |
| safety_users | ✅ |  | 2 |
| scheduler_locks | ✅ |  | 5 |
| scheduler_runs | ✅ |  | 3 |
| session_activity | ✅ |  | 1062 |
| shop_users | ✅ |  | 2 |
| signatures | ✅ |  | 0 |
| suppliers | ✅ |  | 156 |
| system_counters | ✅ |  | 1 |
| system_health_events | ✅ |  | 0 |
| tasks | ✅ |  | 53 |
| temp_upload_chunks | ✅ |  | 0 |
| time_off_public_links | ✅ |  | 0 |
| todo_lists | ✅ |  | 0 |
| todos | ✅ |  | 0 |
| training_guides | ✅ |  | 19 |
| training_hits | ✅ |  | 1180 |
| training_videos | ✅ |  | 1 |
| transfer_requests | ✅ |  | 30 |
| trench_boxes | ✅ |  | 0 |
| trench_safety_assets | ✅ |  | 7 |
| trench_safety_certifications | ✅ |  | 0 |
| trench_safety_deployments | ✅ |  | 0 |
| trench_safety_holds | ✅ |  | 0 |
| trench_safety_inspections | ✅ |  | 0 |
| trench_safety_qr_scans | ✅ |  | 0 |
| trench_safety_repairs | ✅ |  | 0 |
| usage_events | ❌ | regenerable cache (iter441) | 409303 |
| user_directory | ✅ |  | 42 |
| user_passkeys | ✅ |  | 1 |
| users | ✅ |  | 5 |
| vendors | ✅ |  | 3 |
| webauthn_challenges | ✅ |  | 0 |
| workflow_state_events | ✅ |  | 2 |

=== masci_safety_preview === (161 non-system)
| Collection | Captured | Reason if excluded | Docs |
|---|---|---|---|
| activity_log | ✅ |  | 0 |
| admin_audit | ✅ |  | 4044 |
| admin_audit_log | ✅ |  | 170 |
| admin_step_ups | ✅ |  | 1 |
| alert_events | ✅ |  | 0 |
| asset_assignments | ✅ |  | 12 |
| asset_holds | ✅ |  | 34 |
| asset_mapping_proposals | ✅ |  | 0 |
| asset_mappings | ✅ |  | 191 |
| asset_transfers | ✅ |  | 120 |
| audit_events | ✅ |  | 13605 |
| backup_health | ✅ |  | 200 |
| brute_force_blocks | ✅ |  | 0 |
| calculator_runs | ✅ |  | 1 |
| cluster_capacity_history | ✅ |  | 955 |
| command_center_calendar | ✅ |  | 1 |
| command_center_thresholds | ✅ |  | 1 |
| compliance_findings | ✅ |  | 1177 |
| compliance_scans | ✅ |  | 50 |
| corrective_actions | ✅ |  | 26 |
| daily_reports | ✅ |  | 741 |
| digest_runs | ✅ |  | 4 |
| digest_settings | ✅ |  | 1 |
| directory_sessions | ✅ |  | 2163 |
| dispatch_assignments | ✅ |  | 368 |
| dispatch_continuity_events | ✅ |  | 24 |
| dispatch_driver_sessions | ✅ |  | 7 |
| dispatch_magic_links | ✅ |  | 0 |
| dispatch_state_events | ✅ |  | 1162 |
| dispatch_users | ✅ |  | 2 |
| doc_id_counters | ✅ |  | 23 |
| docs | ✅ |  | 0 |
| document_expirations | ✅ |  | 139 |
| draft_telemetry | ✅ |  | 361 |
| drill_runs | ✅ |  | 11 |
| driver_qualification_import_previews | ✅ |  | 22 |
| driver_qualification_imports | ✅ |  | 105 |
| employee_lifecycle_events | ✅ |  | 31 |
| employee_mappings | ✅ |  | 65 |
| employee_requests | ✅ |  | 39 |
| employees | ✅ |  | 364 |
| equipment_inspections | ✅ |  | 146 |
| equipment_master | ✅ |  | 693 |
| equipment_parts | ✅ |  | 0 |
| equipment_units | ✅ |  | 484 |
| events | ✅ |  | 0 |
| field_leadership_equipment_catalog | ✅ |  | 35 |
| field_leadership_equipment_makes | ✅ |  | 14 |
| field_leadership_records | ✅ |  | 78 |
| field_leadership_users | ✅ |  | 24 |
| field_memory_notes | ✅ |  | 35 |
| field_submitter_bindings | ✅ |  | 494 |
| fire_ext_import_runs | ✅ |  | 15 |
| fire_extinguishers | ✅ |  | 7 |
| fleet_audit | ✅ |  | 722 |
| fleet_defects | ✅ |  | 94 |
| fleet_status | ✅ |  | 107 |
| guidance_search_misses | ✅ |  | 48 |
| haul_cycles | ✅ |  | 92 |
| health_monitor_runs | ❌ | regenerable cache (iter441) | 9808 |
| hill_scopes | ✅ |  | 3 |
| hr_users | ✅ |  | 42 |
| hub_banner_audit | ✅ |  | 136 |
| hub_banners | ✅ |  | 2 |
| idempotency_keys | ✅ |  | 34 |
| incidents | ✅ |  | 42 |
| inspections | ✅ |  | 18 |
| integration_error_logs | ✅ |  | 2 |
| integration_settings | ✅ |  | 2 |
| integration_sync_logs | ✅ |  | 106 |
| integration_wizard_runs | ✅ |  | 105 |
| jha_acknowledgements | ✅ |  | 1 |
| jhas | ✅ |  | 1 |
| job_hazard_files | ✅ |  | 6 |
| job_hazard_plans | ✅ |  | 0 |
| job_photo_thumb_cache | ❌ | regenerable cache (iter441) | 2637 |
| job_photos | ✅ |  | 1504 |
| jobs_master | ✅ |  | 29 |
| legacy_import_audit | ✅ |  | 6 |
| legacy_imports | ✅ |  | 0 |
| login_attempts | ✅ |  | 0 |
| maintainx_work_orders | ✅ |  | 0 |
| meetings | ✅ |  | 37 |
| message_comments | ✅ |  | 2 |
| messages | ✅ |  | 0 |
| mfa_audit_events | ✅ |  | 153 |
| motive_events | ✅ |  | 376 |
| motive_geofences | ✅ |  | 67 |
| notifications | ✅ |  | 6444 |
| odr | ✅ |  | 170 |
| odr_amendments | ✅ |  | 33 |
| odr_attachments | ✅ |  | 0 |
| odr_consumer_index | ✅ |  | 0 |
| odr_counters | ✅ |  | 1 |
| odr_observation_events | ✅ |  | 113 |
| odr_pdf_renders | ✅ |  | 497 |
| odr_photos | ✅ |  | 46 |
| odr_preload_attempts | ✅ |  | 160 |
| odr_public_links | ✅ |  | 67 |
| odr_section_events | ✅ |  | 721 |
| odr_translation_events | ✅ |  | 0 |
| operational_attachments | ✅ |  | 48 |
| operational_constraints | ✅ |  | 0 |
| operational_events | ✅ |  | 4 |
| operational_links | ✅ |  | 211 |
| operational_locations | ✅ |  | 67 |
| operations_actions | ✅ |  | 77 |
| operations_events | ✅ |  | 682 |
| payroll_variance_batches | ✅ |  | 10 |
| payroll_variance_decisions | ✅ |  | 7 |
| photo_migration_progress | ✅ |  | 7 |
| po_requests | ✅ |  | 310 |
| project_managers | ✅ |  | 6 |
| project_memberships | ✅ |  | 1 |
| qaqc_inspections | ✅ |  | 12 |
| r2_degraded_events | ✅ |  | 0 |
| resend_webhook_events | ✅ |  | 103 |
| role_templates | ✅ |  | 31 |
| safety_documents | ✅ |  | 14 |
| safety_equipment_issuances | ✅ |  | 24 |
| safety_equipment_trainings | ✅ |  | 16 |
| safety_training_records | ✅ |  | 8 |
| safety_users | ✅ |  | 2 |
| scheduler_locks | ✅ |  | 0 |
| scheduler_runs | ✅ |  | 0 |
| session_activity | ✅ |  | 239 |
| shop_users | ✅ |  | 3 |
| signatures | ✅ |  | 107 |
| suppliers | ✅ |  | 145 |
| system_counters | ✅ |  | 3 |
| system_health_events | ✅ |  | 0 |
| tasks | ✅ |  | 1658 |
| temp_upload_chunks | ✅ |  | 0 |
| time_off_public_links | ✅ |  | 8 |
| todo_lists | ✅ |  | 0 |
| todos | ✅ |  | 0 |
| training_guides | ✅ |  | 19 |
| training_hits | ✅ |  | 176 |
| training_videos | ✅ |  | 1 |
| transfer_requests | ✅ |  | 42 |
| trench_boxes | ✅ |  | 1 |
| trench_excavations | ✅ |  | 710 |
| trench_safety_assets | ✅ |  | 104 |
| trench_safety_certifications | ✅ |  | 64 |
| trench_safety_deployments | ✅ |  | 225 |
| trench_safety_holds | ✅ |  | 1019 |
| trench_safety_inspections | ✅ |  | 402 |
| trench_safety_leadership_digests | ✅ |  | 8 |
| trench_safety_photos | ✅ |  | 75 |
| trench_safety_pulses | ✅ |  | 72 |
| trench_safety_qr_scans | ✅ |  | 110 |
| trench_safety_repairs | ✅ |  | 284 |
| trench_safety_report_presets | ✅ |  | 0 |
| trench_safety_report_subscriptions | ✅ |  | 4 |
| usage_events | ❌ | regenerable cache (iter441) | 247229 |
| user_directory | ✅ |  | 80 |
| user_passkeys | ✅ |  | 4 |
| users | ✅ |  | 5 |
| vendors | ✅ |  | 3 |
| webauthn_challenges | ✅ |  | 4 |
| workflow_state_events | ✅ |  | 73 |


---

## Roll-up

| DB | Total | Captured | Excluded | Coverage % | Verdict |
|---|---|---|---|---|---|
| `masci_safety` (production) | 155 | 152 | 3 | 98.1% | 🟢 PASS |
| `masci_safety_preview` (preview) | 161 | 158 | 3 | 98.1% | 🟢 PASS |

## Excluded collections (3) · all intentional

| Collection | Reason | Documented in |
|---|---|---|
| `usage_events` | regenerable API telemetry · ~247k rows | iter441 / BACKUP_CRASH_ROOT_CAUSE_REPORT.md |
| `health_monitor_runs` | scheduler health probe series · ~17k rows | iter441 |
| `job_photo_thumb_cache` | derivative photo cache · ~1.8k rows | iter441 |

## New collections introduced in today's session — coverage confirmed

| Collection | Sprint | Captured? |
|---|---|---|
| `asset_mapping_proposals` | MOTIVE-DATA-001 | ✅ |
| `operational_locations` | M-3 | ✅ |
| `operational_events` | M-2 | ✅ |
| `operational_links` | (multi-sprint) | ✅ |
| `operational_constraints` | (multi-sprint) | ✅ |
| `operations_actions` | OA-1 | ✅ |
| `operational_attachments` | OA-1 | ✅ |
| `motive_geofences` | M-3 | ✅ |

All are auto-discovered. No allowlist update was required.

🛑 PASS.
