# Timeline Role Visibility Certification

**Phase V-Prelude · Wave 1.1**
**Status:** 🟢 **CERTIFIED · preview env**
**Date:** 2026-05-28

---

## Scope

Locks the **role-aware visibility contract** on the Operational
Timeline aggregator. The sidecar is rendered cross-portal, so the
authority boundaries MUST be enforced server-side — never inferred
from the client.

## Authority boundary (re-statement)

The `/api/timeline` endpoint accepts any portal token via
`_require_any_portal_token` (admin · pm · hr · safety · shop · dispatch
· leadership · fl). The aggregator then applies two filters:

1. **`status != "voided"`** — applied for every actor, every portal.
2. **`visibility != "audit-only"`** — applied for every actor that
   is NOT `_actor: "admin"`.

These two filters are the entire role-aware surface. There is no
client-side role gating. Doctrine: backend is the source of truth.

## Probes

### `test_sidecar_timeline_excludes_voided_links`
- Admin creates a link, then PATCHes its status to `voided`.
- Admin then calls `/api/timeline?project_id=...`.
- Asserts: the voided link's source-id substring is NOT present in
  any returned item.
- 🟢 passing.

### `test_audit_only_link_hidden_from_non_admin`
- Admin creates an `audit-only` link.
- PM logs in with seeded test PM (chriswright@mascigc.com).
- PM calls `/api/timeline?project_id=...` with `X-PM-Token`.
- Asserts: the audit-only link's source-id substring is NOT present in
  any returned item for the PM actor.
- 🟢 passing (uses `httpx` directly to bypass conftest's `requests`
  monkey-patch).

### `test_no_invalid_relationship_in_timeline`
- Every `operational_link` row surfaced by the timeline carries a
  relationship in the canonical 14-element set (or is a constraint
  chronology action which is allowed to be a verb).
- 🟢 passing.

## Capability matrix (for the sidecar surface)

The sidecar exposes ONLY a refresh control and a "Show all"
affordance. Every actor sees the same controls; what differs is the
**dataset they receive from the backend.**

| Actor / Portal | Sees voided links? | Sees audit-only links? |
|---|---|---|
| Admin (`_actor=admin`) | ❌ no | ✅ yes |
| PM (`_actor=pm`) | ❌ no | ❌ no |
| HR (`_actor=hr`) | ❌ no | ❌ no |
| Safety (`_actor=safety`) | ❌ no | ❌ no |
| Shop (`_actor=shop`) | ❌ no | ❌ no |
| Dispatch (`_actor=dispatch`) | ❌ no | ❌ no |
| Leadership (`_actor=leadership`) | ❌ no | ❌ no |
| Field Leadership (`_actor=fl`) | ❌ no | ❌ no |

## Sentinel guarantees

- **No permission inheritance through links.** A photo linked to a
  constraint does NOT inherit any extra capability — the photo's own
  visibility scope still rules every photo-specific surface. The
  timeline surfaces the link as context only.
- **No fan-out side effects.** Surfacing a row in the timeline does
  NOT trigger a notification, email, push, or DB write.
- **Cross-portal read does NOT imply cross-portal write.** The Wave 1
  capability primitive (`constraintCapabilities.js`) governs writes
  in the constraint surface; the timeline sidecar is strictly
  read-only.

## Doctrine probe coverage

`scripts/operational_links_doctrine_probe.py` continues to enforce:
- Closed-set `visibility` enum.
- `audit-only` rows present in storage with valid `created_by`.
- No drift between the enums in the code and what's stored in Mongo.

🟢 sub-second sweep · 0 violations · 0 baselined rows on the preview
database (clean substrate).

---

— certified by E1 · 2026-05-28
