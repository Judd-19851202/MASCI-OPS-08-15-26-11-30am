# RESEND API KEY SEPARATION CERTIFICATION

**Date**: 2026-02-12

---

## EVIDENCE — PREVIEW

```
RESEND_API_KEY       : re_CfHQ9DjX_…U5A8kW         (last 6: U5A8kW)
SENDER_EMAIL         : noreply@mascidocs.com
REPLY_TO_EMAIL       : jaymn.judd@mascigc.com
BACKUP_EMAIL_TO      : jaymn.judd@mascigc.com
AUTO_EMAIL_REPORTS   : false
OUTAGE_ALERT_TO      : jaymn.judd@mascigc.com
ADMIN_DEAD_LETTER_EMAIL : safety@mascigc.com
```

Preview deliberately sends emails through the same real Resend account. AUTO_EMAIL_REPORTS=false reduces noise. Outage alerts and dead-letter routing target real MASCI inboxes.

---

## EVIDENCE — PRODUCTION (operator-managed)

Production Resend configuration is set in the Emergent deployment dashboard. Operator must paste below.

```
PRODUCTION RESEND_API_KEY (last 6 only) : __________________________
PRODUCTION SENDER_EMAIL                  : __________________________
PRODUCTION RESEND domain verified        : [ ] yes / [ ] no
```

---

## PASS RULES

| Rule | Pass condition |
|---|---|
| Production key separation | Production `RESEND_API_KEY` last 6 ≠ `U5A8kW` (preview last 6) |
| Production sender approved | Production `SENDER_EMAIL` domain is `mascidocs.com` (or operator-approved equivalent) AND domain is Resend-verified |
| Preview cannot mass-email production leadership | `AUTO_EMAIL_REPORTS=false` in preview · operator confirms `BACKUP_EMAIL_TO` lands in MASCI inbox not external list |
| Test email routing isolated | Reinspection notifications use `emit_notification(db, payload)` with `recipient_role` — operator confirms production routing matrix maps to real Safety / Superintendent / Admin lists, preview maps to a single test inbox or sandbox |

---

## VERDICT

# **OPERATOR-PENDING** → defaults to FAIL until cleared

Same Resend account currently used across both environments. Per directive:
> "If same key is used: FAIL unless operator explicitly approves with documented risk acceptance."

### Two acceptable remediation paths

**Path A · Create production-only Resend key**
1. Operator generates a new Resend API key in the MASCI Resend account, restricted to the production sender domain.
2. Production env sets `RESEND_API_KEY` to the new key.
3. Preview retains the current key but operator switches preview `SENDER_EMAIL` to a Resend sandbox/testing identity or operator-controlled inbox.
4. Re-issue this certification with **PASS**.

**Path B · Operator accepts shared key with documented risk**
1. Operator signs the paste-in block below acknowledging that preview reinspection notifications may reach real Safety/Superintendent inboxes during the field trial.
2. Operator confirms preview AUTO_EMAIL_REPORTS remains `false` and preview testing avoids triggering automated fan-outs unless intentional.

### Operator paste-in block

```
[ ] Path A · separate production key   key-last-6: __________
[ ] Path B · risk accepted (shared key) · reason: __________________________

Operator signature : __________________________
Date               : __________________________
```

Until paste-in: **FAIL**.
