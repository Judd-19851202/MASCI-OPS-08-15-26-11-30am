# TRACK 19.58 · Permission Certification

## Auth surfaces
- Route: `/safety/incidents/:caseId/thread`. No wrapper in App.js because
  the underlying axios client (`caseWorkspaceApi.js`) is already gated
  on the Safety JWT — identical to how `SafetyCaseWorkspace` mounts.
- Page-level: `if (!(isSafety() || isAdmin())) return <AccessDenied attemptedPortal="safety" />;`
- Request headers: Safety JWT forwarded automatically by the shared
  axios client. OI summary call additionally accepts the Admin token.

## Restricted sections (honest empty · never fetched)
| Section                    | Why not fetched?                                                                   |
|----------------------------|------------------------------------------------------------------------------------|
| Medical (`/medical`)       | Track 20.3 mandate. Medical never surfaces on the thread — full-stop.              |
| Agency (`/agency-contacts`)| Track 20.3 mandate. Agency contacts remain in the workspace only.                  |
| Communications             | Same — remain in the workspace only.                                               |
| Case audit (`/audit`)      | Track 20.3 mandate. Audit remains in the workspace only.                           |
| Executive intelligence     | Not needed for the thread — replaced by `executive-snapshot` (public-safe summary) |

## Rules
1. **403 stays 403.** If any call this thread makes returns 403, the
   corresponding section renders an honest empty state — never a
   placeholder that leaks the underlying error message.
2. **Witnesses are text-only pills.** Never a clickable thread node
   (there is no Witness Thread).
3. **Evidence Readiness never asserts legal conclusions.** Four
   qualitative buckets only.
4. **Executive Report link is enforced server-side.** The thread
   renders the deep-link unconditionally; the server enforces access.
5. **No new permission surface.** Every viewer inherits their existing
   access to each source endpoint. Zero widening.

## Certification
**The Incident Thread strictly preserves the existing Safety +
Admin permission model. Non-Safety roles see nothing they could not
already reach through `SafetyCaseWorkspace`. Track 19.58 introduces
zero data-leak vectors.**
