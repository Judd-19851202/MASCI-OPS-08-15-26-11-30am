# WHITE-LABEL · EMAIL MATRIX

**Phase 7 deliverable.** Every email path and what would leak to Customer #2.

## Email send paths (Resend wrapper)

| Email type | Trigger | Sender today | Reply-to today | Footer | Customer-visible MASCI? |
|------------|---------|--------------|----------------|--------|--------------------------|
| Temp password (admin user creation) | admin creates a user | Resend default domain | hardcoded MASCI | "MASCI Hub" footer | 🔴 yes |
| Password reset | self-service forgot-password | same | same | same | 🔴 yes |
| Password change confirmation | self-service password rotate | same | same | same | 🔴 yes |
| Daily report — distribution | daily report submit | Resend default | hardcoded MASCI safety inbox | MASCI footer | 🔴 yes |
| Safety meeting — distribution | safety meeting submit | same | same | same | 🔴 yes |
| Incident notification | incident open | same | same | same | 🔴 yes |
| Corrective action alert | CA assigned / overdue | same | same | same | 🔴 yes |
| Staffing assignment notify | admin assigns PM to a job | same | same | same | 🔴 yes |
| Backup health email | nightly backup | `BACKUP_EMAIL_TO` env (good!) | hardcoded MASCI | MASCI footer | 🟡 recipient configurable, sender/footer not |
| Health monitor alert | system anomaly | hardcoded admin inbox | hardcoded | MASCI | 🔴 |
| Weekly digest | admin schedule | env-configurable recipient list | hardcoded | MASCI | 🟡 |
| PO digest | weekly PO summary | env-configurable | hardcoded | MASCI | 🟡 |
| Training reminders | env-gated | hardcoded MASCI sender | hardcoded | MASCI | 🔴 |

## Send-gate

🟢 **`AUTO_EMAIL_REPORTS=false` in Preview** — no Preview email ever reaches a real recipient.
🟢 **`AUTO_EMAIL_REPORTS=true` in Production** — emails fire to actual recipients from `@mascigc.com`.

## Routing defaults (`email_routing.py`)

| Surface | Default | Env override |
|---------|---------|--------------|
| Leadership recipient #1 | `jaymn.judd@mascigc.com` | `LEADERSHIP_ALWAYS_TO_1` ✅ |
| Leadership recipient #2 | `safety@mascigc.com` | `LEADERSHIP_ALWAYS_TO_2` ✅ |
| Shop manager | `shopmanager@mascigc.com` | `SHOP_MANAGER_EMAIL` ✅ |
| Always-CC | `["jaymn.judd@mascigc.com", "safety@mascigc.com"]` | ❌ NOT env-overridable — hardcoded list at `email_routing.py:83` |
| Safety inbox fallback | `["safety@mascigc.com", "jaymn.judd@mascigc.com"]` | ❌ NOT env-overridable — `email_routing.py:72` |

**Gap**: `always_cc` and `safety_to` fallbacks lack env overrides. Customer #2 would unintentionally CC MASCI on every email.

## PM-routing roster (`pm_routing.py:28+`)

| Person | Email | Note |
|--------|-------|------|
| David Jewett | `davidjewett@mascigc.com` | hardcoded as fallback |
| Chris Wright | `chriswright@mascigc.com` | hardcoded as fallback |
| (others) | various `@mascigc.com` | static dict |

DB-driven PM email lookup runs first; this dict is a fallback. Customer #2 deploy would need to either clear the dict OR replace it with their own PM roster. **Safer**: read PM roster ENTIRELY from DB (no fallback dict).

## Template wording

Every email body is rendered with copy that references "MASCI Hub" / "MASCI Safety" in subject lines, headers, and footers. None of this is templated through a BrandConfig today.

## Customer #2 implication

Without white-label work, every email Customer #2's platform sends would:
- Come from `@mascigc.com` sender domain
- CC MASCI employees by default
- Have MASCI in the subject/footer/header
- Reference MASCI Hub as the platform name

🔴 **Email is the highest-leak surface for Customer #2.** Top priority in any white-label Phase 1.

## Fix path

1. Extend `email_routing.py` env-override coverage: `ALWAYS_CC_LIST`, `SAFETY_TO_FALLBACK_LIST`.
2. Move PM roster fallback OUT of `pm_routing.py` — read from DB only.
3. Introduce `BrandConfig.email_*` (sender, reply_to, subject_prefix, footer_html, logo_url).
4. Refactor every email helper to call `brand.email_render(subject, body)` instead of hardcoding.
5. Per-customer Resend account with their own verified domain.

**Effort**: ~1 week focused work.
