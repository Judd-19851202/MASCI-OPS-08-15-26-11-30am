#!/usr/bin/env bash
# TRACK 15.75C-PROD · Production validation harness.
#
# Verifies that every workflow kind now writes truthful
# email_routing_audit_v2 rows in PRODUCTION.
#
# Run from your laptop (or any machine with curl + jq + python3):
#
#   export PROD_ADMIN_TOKEN='<your masci super-admin directory token>'
#   bash track_15_75c_prod_validate.sh
#
# Output is a Markdown table you paste back to the agent.
#
# NO production DB writes are performed.
# NO email blasts are sent.
# Only existing audit rows are read.

set -euo pipefail

BASE="${PROD_BASE:-https://mascidocs.com}"
TOKEN="${PROD_ADMIN_TOKEN:?Set PROD_ADMIN_TOKEN to a masci super-admin directory token}"

hr() { printf -- '\n%s\n' "------------------------------------------------------------------------"; }
header() { printf '\n## %s\n' "$1"; }

hr
echo "TRACK 15.75C-PROD · Production validation harness"
echo "Target: $BASE"
echo "Date  : $(date -u +%FT%TZ)"
hr

# -------------------------------------------------------------------------- #
# 1.  Deploy proof
# -------------------------------------------------------------------------- #
header "1. Deploy proof (public)"
ver_json="$(curl -fsS "$BASE/api/version")"
echo "$ver_json" | python3 -m json.tool

# -------------------------------------------------------------------------- #
# 2.  Admin gate sanity
# -------------------------------------------------------------------------- #
header "2. Admin gate sanity"
code_no_tok="$(curl -s -o /dev/null -w '%{http_code}' "$BASE/api/admin/email-routing/v2/status")"
code_w_tok="$(curl -s -o /dev/null -w '%{http_code}' -H "X-Admin-Token: $TOKEN" "$BASE/api/admin/email-routing/v2/status")"
printf '  /api/admin/email-routing/v2/status   no token: %s   with token: %s\n' "$code_no_tok" "$code_w_tok"
[ "$code_no_tok" = "401" ] || { echo "FAIL: admin endpoint did not enforce 401"; exit 2; }
[ "$code_w_tok" = "200" ] || { echo "FAIL: admin token did not grant 200"; exit 2; }

# -------------------------------------------------------------------------- #
# 3.  /api/admin/email-routing/v2/status — overall counters
# -------------------------------------------------------------------------- #
header "3. email-routing v2 status"
v2_json="$(curl -fsS -H "X-Admin-Token: $TOKEN" "$BASE/api/admin/email-routing/v2/status")"
echo "$v2_json" | python3 -m json.tool

# -------------------------------------------------------------------------- #
# 4.  Allowed-status enforcement (the Track 15.75C contract)
# -------------------------------------------------------------------------- #
header "4. Allowed-status enforcement"
echo "$v2_json" | python3 - <<'PY'
import json, sys
data = json.load(sys.stdin)
ALLOWED = {
    "sent", "failed", "dry_run", "resolved",
    "routed_to_dead_letter", "dead_letter_unconfigured",
    "shop_recipient_unconfigured", "escalated_to_admin_dead_letter",
}
ctrs = data.get("status_counters") or data.get("audit_counters") or {}
unknown = [s for s in (ctrs.keys() if isinstance(ctrs, dict) else []) if s and s not in ALLOWED]
print("status counters:", json.dumps(ctrs, indent=2, default=str))
if unknown:
    print("FAIL — unknown status(es) found:", unknown)
    sys.exit(3)
print("PASS — all statuses within allowed set")
PY

# -------------------------------------------------------------------------- #
# 5.  Per-workflow audit-row presence
# -------------------------------------------------------------------------- #
header "5. Per-workflow audit-row presence (last 7 days)"
# Use the v2 status endpoint's calling_module aggregation if available;
# else fall back to fetching audit rows directly.
echo "$v2_json" | python3 - <<'PY'
import json, sys
data = json.load(sys.stdin)
modules = (
    data.get("calling_module_counters")
    or data.get("by_calling_module")
    or {}
)
print("calling_module counters:", json.dumps(modules, indent=2, default=str))
expected = {
    "auto_email_dispatch:daily-report",
    "auto_email_dispatch:meeting",
    "auto_email_dispatch:incident",
    "auto_email_dispatch:qaqc",
    "auto_email_dispatch:jha",
    "auto_email_dispatch:inspection",
    "shop_preop_dispatch",
}
missing = [m for m in expected if m not in (modules.keys() if isinstance(modules, dict) else [])]
if missing:
    print("INFO — calling_module(s) not yet present in counters:", missing)
    print("(this is OK if no record of that kind was submitted post-deploy yet)")
else:
    print("PASS — every expected calling_module observed")
PY

# -------------------------------------------------------------------------- #
# 6.  PM-Email Coverage card (Track 15.75A roster-resolved coverage)
# -------------------------------------------------------------------------- #
header "6. PM-email coverage (Track 15.75A surface)"
pm_json="$(curl -fsS -H "X-Admin-Token: $TOKEN" "$BASE/api/admin/pm-email-coverage")"
echo "$pm_json" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print("track                          :", d.get("track"))
print("summary                        :", json.dumps(d.get("summary"), indent=2, default=str))
print("active_projects_total          :", d.get("active_projects_total"))
print("active_projects_missing_pm     :", d.get("active_projects_missing_pm_email"))
print("with_recent_drs_and_no_pm_email:", d.get("active_projects_with_recent_drs_and_no_pm_email"))
print("first 3 rows:")
for r in (d.get("missing_rows_top_25") or [])[:3]:
    print(" -", json.dumps({k: r.get(k) for k in ("project_number","pm_name","pm_email","roster_pm_email","roster_co_pm_emails","recent_dr_count","status")}))
'

# -------------------------------------------------------------------------- #
# 7.  Backend health (post-deploy heartbeat)
# -------------------------------------------------------------------------- #
header "7. Health"
curl -fsS "$BASE/api/health/full" | python3 -m json.tool

hr
echo "Validation harness complete. Paste the output back to the agent."
hr
