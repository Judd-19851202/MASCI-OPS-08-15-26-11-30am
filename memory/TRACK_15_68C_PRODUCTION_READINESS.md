# TRACK 15.68C · Production Readiness — Conditional
See `TRACK_15_68C_FINAL_CLOSEOUT.md` §9.
- ✅ Deploy with `EMAIL_ROUTING_V2=false` authorised (no MASCI regression).
- ❌ V2 production flip NOT authorised.
- ❌ Public C2 onboarding NOT authorised — admin tabs + body subheaders still leak MASCI for C2 admins.
Rollback: flip `EMAIL_ROUTING_V2=false` (current default).
