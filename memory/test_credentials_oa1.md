# MASCI · Test Credentials Quick Reference (current snapshot)

For OA-1 certification, prefer the **multi-login** route which mints all portal tokens at once:

- `POST /api/auth/multi-login` body `{email:"jaymn.judd@mascigc.com", password:"Maddix123!"}`
  → returns `{ token, portal_tokens: { admin, safety, hr, dispatch, pm, shop, fl } }`
  Every OA endpoint accepts ANY of these tokens (X-Admin-Token, X-Safety-Token,
  X-HR-Token, X-Dispatch-Token, X-PM-Token, X-Shop-Token, X-FL-Token).

## Direct portal credentials (preview DB)
- Legacy admin: `MASCI1982!` → `POST /api/admin/login` body `{password}`
- Super admin multi-login: `jaymn.judd@mascigc.com` / `Maddix123!`
- HR Manager: `hrmanager@mascigc.com` / `HRTesting2026!`
- Mechanic: `testmech@mascigc.com` / `ResetWorks2026!`
- PM Chris Wright: `chriswright@mascigc.com` / `ChrisRocksThis2026`
- Dispatch (STALE per known rotation): `dispatch@mascigc.com` — prefer multi-login portal_tokens.dispatch
- Safety: prefer multi-login portal_tokens.safety
- FL: `fieldleader@mascigc.com` is DEACTIVATED — use multi-login portal_tokens.fl

See `/app/memory/test_credentials.md` for the comprehensive history.
