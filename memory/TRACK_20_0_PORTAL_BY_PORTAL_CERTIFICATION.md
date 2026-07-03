# TRACK 20.0 · Portal-by-Portal Certification

| Portal / Surface           | Route                            | OI Attention Strip | Guidance Card | Command Center Standard | Verdict |
|----------------------------|----------------------------------|:------------------:|:-------------:|:-----------------------:|:-------:|
| Admin Mission Control      | `/admin`                         | ✅ Corporate + Weekly Ops + Exec Brief | ✅ | ✅ | 🟢 PASS |
| Admin OI Cockpit           | `/admin/operational-intelligence`| — (this IS the Cockpit) | ✅ | ✅ + sparkline | 🟢 PASS |
| Admin Asset Admin          | `/admin/asset-admin`             | ✅ fleet_intelligence | ✅ | ✅ | 🟢 PASS |
| Safety Hub V2              | `/safety-portal`, `/safety-portal/hub_v2` | ✅ safety_morning_digest | ✅ | ✅ | 🟢 PASS |
| HR Hub V2                  | `/hr`, `/hr/hub_v2`              | ✅ hr_intelligence + training_intelligence | ✅ | ✅ | 🟢 PASS |
| PM Command Center          | `/pm` → `/pm/command-center`     | ✅ project_intelligence | ✅ | ✅ | 🟢 PASS |
| Shop Hub V2                | `/shop`, `/shop/hub_v2`          | ✅ shop_intelligence | ✅ | ✅ | 🟢 PASS |
| Fleet Visibility           | `/shop/fleet`, `/safety-portal/fleet`, `/dispatch-portal/fleet` | ✅ fleet_intelligence | ✅ | ✅ | 🟢 PASS |
| Fleet Unit Thread (pilot)  | `/fleet/unit/:unit_number`       | (thread page)      | ✅ (Section 3) | ✅ (10-section shell) | 🟢 PASS |
| Dispatch Command Center    | `/dispatch-portal/command`       | ✅ transportation_intelligence | ✅ | ✅ | 🟢 PASS |
| Field Leadership Dashboard | `/field-leadership/portal`       | ✅ "Today's focus" banner | ✅ (via strip tiles) | ✅ | 🟢 PASS |
| Guidance Center            | `/guidance`                      | n/a (guidance IS the source) | ✅ | ✅ (deferred workflow restructure recorded as Track 19.53 deferral) | 🟢 PASS |

## Common patterns verified per portal
- Every portal home follows the standard visual hierarchy: Mission → Attention → Today → Active Work → Detail → History → Archive.
- Every attention item speaks the universal 4-value vocabulary (CRITICAL / HIGH / MEDIUM / LOW).
- Every trend uses direction-first (▲/→/▼) with score + delta.
- Every deep-link routes to a real existing workflow (no dead ends).
- Every OI Attention Strip tile opens the same Guidance Card modal.
- Every mobile / iPad breakpoint verified in the Track 19.52 / 19.53 / 19.55 mobile audits.

## No portal-specific attention or guidance framework detected
Lock tests (`test_no_new_command_center_framework_added`,
`test_oi_component_directory_inventory`) enforce this at the CI level.

## Verdict
🟢 **All 12 portal surfaces PASS.**
