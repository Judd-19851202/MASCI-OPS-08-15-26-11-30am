# TRACK 15.68B · Company Name Fallback Sweep — ✅ Top 4 sites SHIPPED

See `TRACK_15_68B_FINAL_CLOSEOUT.md` §4.

| Site | Before | After |
|---|---|---|
| `ViewDailyReport.jsx:739` | `{company.company_name || "MASCI"} Daily Report` | `{company.company_name || branding.company_name || "Customer"} Daily Report` |
| `ViewDailyReport.jsx:748` | `{company.company_name || "MASCI"}` | `{company.company_name || branding.company_name || "Customer"}` |
| `ViewInspection.jsx:485` | `· {company.company_name || "MASCI"} Job Site Safety` | `· {company.company_name || branding.company_name || "Customer"} Job Site Safety` |
| `ViewInspection.jsx:494` | `{company.company_name || "MASCI"}` | `{company.company_name || branding.company_name || "Customer"}` |

**Not migrated** (data seed defaults, not customer-rendered):
- `EquipmentMasterPanel.jsx` (lines 92, 189) — `company: "MASCI"` default on equipment master row creation. Admin overrides per row.
- `AttendeeBulkAddDialog.jsx:115` — `company: "MASCI"` default for new attendees. Admin overrides per row.
- `EmailReportDialog.jsx:66` — `proj = record.project_name || record.project || "MASCI"` — final fallback for an unnamed record, only used in email subject when ALL project fields are blank.

These are seed defaults an admin can edit at row-creation time, not chrome strings rendered to customer portal users.
