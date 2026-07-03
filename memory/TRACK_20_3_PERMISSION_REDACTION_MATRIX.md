# TRACK 20.3 · Permission · Redaction Matrix

**High-risk track. Incident records are legal / OSHA / insurance evidence. The Incident Thread must never widen access.**

## Read visibility by role
| Section / field             | Admin | Safety | HR    | PM    | Executive | Fleet | Shop | Trans | Field | Public / Anonymous |
|-----------------------------|:-----:|:------:|:-----:|:-----:|:---------:|:-----:|:----:|:-----:|:-----:|:------------------:|
| Case exists (id / severity) | ✅    | ✅     | ✅ ¹  | ✅ ²  | ✅        | ✅ ³  | ✅ ³ | ✅ ³  | ❌    | ❌                 |
| Narrative                   | ✅    | ✅     | Redacted | Redacted | Redacted (summary only) | ❌ | ❌ | ❌ | ❌ | ❌ |
| Employee names (involved)   | ✅    | ✅     | ✅ ¹  | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Witness names               | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Medical info                | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Agency (police / fire)      | ✅    | ✅     | ❌    | ❌    | Summary   | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Photos                      | ✅    | ✅     | ❌    | ❌ ⁴  | ❌ ⁴      | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Evidence (files)            | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Root cause                  | ✅    | ✅     | ❌    | Summary | Summary | ❌    | ❌   | ❌    | ❌    | ❌                 |
| CAPA                        | ✅    | ✅     | ❌    | ✅ ² (project-scoped) | Summary | ❌ | ❌ | ❌ | ❌ | ❌ |
| Insurance package           | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| OSHA package                | ✅    | ✅     | ❌    | ❌    | Summary   | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Attorney work product       | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |
| Timeline (redacted)         | ✅    | ✅     | Redacted | Redacted | Summary | Redacted | Redacted | Redacted | ❌ | ❌ |
| Audit trail                 | ✅    | ✅     | ❌    | ❌    | ❌        | ❌    | ❌   | ❌    | ❌    | ❌                 |

¹ HR sees incidents involving their scope of employees only.
² PM sees incidents on their assigned projects only.
³ Fleet/Shop/Transportation see incidents involving equipment they own, and only equipment fields.
⁴ Non-Safety viewers see photo counts / thumbnails only if the case is executive-cleared.

## Redaction rules for Track 19.58 (proposed thread)
1. **Default to redacted.** The thread renders "Restricted — Safety only" placeholders for any field the current viewer cannot read, matching how `SafetyCaseWorkspace` gates today.
2. **No new visibility gain.** The promoted thread inherits the source endpoint's existing gate. If a call returns 403, the section renders an honest empty state.
3. **Witnesses are never a thread node.** They render as text pills (Safety view only).
4. **Medical is never surfaced to PM / HR / Executive by default.** Executive Case Report already redacts medical.
5. **Attorney work product / insurance package are read-only download links** gated to Safety + Admin.

## Anonymous near-miss safety
- `/api/public/near-miss` never returns identifying data on GET.
- Reporter identity is never revealed to any role except Safety + Admin, ever.

## Certification
**No role gains access via the promoted Incident Thread that they do not already have on the source endpoint. Zero permission widening. Zero data leak vectors introduced by Track 19.58 (proposed).**
