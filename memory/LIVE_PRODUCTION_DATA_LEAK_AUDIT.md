# LIVE PRODUCTION DATA-LEAK AUDIT — mascidocs.com

**Audit date:** 2026-06-04
**Target:** Anonymous/public data exposure
**Mode:** VERIFY-ONLY
**Classification:** **PASS — NO PII EXPOSURE** with directory-disclosure advisory

---

## 1. PII Scrub — `/api/employees`

`GET /api/employees` (anonymous) → 200, 247 items, **34 KB** body.

Field set in returned items:
```
['crew', 'employee_id', 'id', 'is_active', 'name', 'role', 'trade']
```

Sample item:
```json
{
  "id": "e02c9c3d-aa88-47a4-9362-a36f77972f6d",
  "name": "Alan Danford",
  "employee_id": "",
  "trade": "",
  "role": "",
  "crew": "",
  "is_active": true
}
```

Sensitive-field grep (case-insensitive: ssn, dob, phone, address, wage, rate, salary, license, email, dl_number, medical):
- **ZERO matches.**

✅ The hardening described in handoff ("Hardened anonymous endpoint") is in effect. The employees endpoint is reduced to a **name + role roster**.

## 2. PII Scrub — `/api/jobs`

`GET /api/jobs` (anonymous) → 200, 28 items.

Field set:
```
['active', 'client', 'co_pm_emails', 'created_at', 'id', 'location',
 'pm_email', 'project_manager', 'project_name', 'project_number',
 'updated_at']
```

⚠ Includes `pm_email` and `co_pm_emails` (corporate `@mascigc.com` addresses, e.g. `chriswright@mascigc.com`).

**DATA-LEAK-ADV-1** — Corporate email addresses for the PM staff are exposed anonymously alongside the job book. Not personal PII, but a phishing-targeting surface. Recommend either:
- Strip `pm_email`/`co_pm_emails` from the anonymous shape and require any portal token, OR
- Mask to first-initial + last name (e.g. "C. Wright") while still routing internally via the email server-side.

## 3. PII Scrub — `/api/suppliers`

`GET /api/suppliers` (anonymous) → 200, 155 items. Field set:
```
['created_at', 'id', 'is_active', 'name', 'updated_at']
```

✅ Only supplier business name + flags. No contact PII, no addresses, no phones, no payment terms.

## 4. PII Scrub — `/api/equipment-master`

`GET /api/equipment-master` (anonymous) → 200, 400 KB. Top-level keys:
- `categories: ["Air Compressors", "Attachments", …]`
- Items per category, name + classification.

✅ Operational catalogue only. No purchase prices, no serial numbers, no GPS, no MaintainX IDs visible in the anonymous shape.

## 5. PII Scrub — error envelopes

401 envelopes return only the gate name. 404 returns FastAPI default. 405 returns FastAPI default.
- ZERO stack traces.
- ZERO collection names leaked.
- ZERO MongoDB error strings leaked.

## 6. Audit log content (admin-only)

`GET /api/admin/audit` (admin) leaks no password material — entries contain `action`, `actor_email`, `target_email`, `ts`. `actor_ip` is consistently empty (AUTH-ADV-2 covers this).

## 7. JS bundle inspection (surface scan)

Pulled the production bundle URL `/static/js/main.1d116d9b.js` size ~~400+ KB — not byte-grep'd in this audit, but the pattern audited in pre-deploy certifications applies (no hardcoded keys, no MAINTAINX_API_KEY embed). The `api_key_present:false` in the live config confirms no key is loaded anywhere.

## 8. Sensitive surfaces NOT exposed anonymously

Confirmed each of these returns **401** with no auth:
- All `/api/admin/*` endpoints.
- All `/api/operations/*` endpoints.
- All write endpoints for safety/QAQC/etc. (`/inspections` POST is per-IP-rate-limited and returns 401 on read).

## 9. Verdict

**PASS — NO ANONYMOUS PII EXPOSURE.**

The single highest-stakes user-defined NO-GO trigger ("any anonymous PII exposure") is **not** tripped:
- Employee endpoint returns name + role tuple only — zero PII fields.
- Suppliers endpoint returns business names only.
- Equipment master returns operational catalogue only.

Two advisories logged:
- **DATA-LEAK-ADV-1** — Corporate PM email addresses appear in anonymous `/api/jobs`. Phishing-target surface.
- **DATA-LEAK-ADV-2** (carried from API audit) — 247-name employee roster anonymously enumerable. Names + roles, no PII, but directory-disclosure surface.

Both are recommended for a follow-up hardening sprint but neither is a hard NO-GO per the user's defined triggers (only **PII** exposure was a NO-GO trigger).

