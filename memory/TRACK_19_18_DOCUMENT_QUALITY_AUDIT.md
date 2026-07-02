# Track 19.18 · Document Quality Audit

For every generated document, we asked five questions:

1. **Why is this here?**
2. **Does it provide operational value?**
3. **Would an executive read it?**
4. **Would OSHA expect it?**
5. **Would an attorney appreciate it?**

## Reports audited (9 canonical + weekly digest)

| Report | Audience | Cover Story ExecSum Timeline RCA CAPA Photos | Verdict |
|---|---|---|---|
| Field Report | Superintendent | ✓ ✓ ✓ ✓ · · ✓ | Ready |
| Safety Report | Safety Director | ✓ ✓ ✓ ✓ ✓ ✓ ✓ | Ready |
| Executive Summary | Executive | ✓ ✓ ✓ · ✓ · · | Ready |
| Investigation Package | Safety + Legal | ✓ ✓ ✓ ✓ ✓ ✓ ✓ | Ready |
| Insurance Package | Adjuster | ✓ ✓ · ✓ ✓ · ✓ | Ready |
| OSHA Package | Compliance | ✓ ✓ ✓ ✓ ✓ ✓ · | Ready |
| Utility Owner Package | Utility Owner | ✓ ✓ · ✓ · · ✓ | Ready |
| Client Package | Client / Owner | ✓ ✓ ✓ · · · ✓ | Ready |
| Closeout Package | Case Closer | ✓ ✓ ✓ ✓ ✓ ✓ ✓ | Ready |
| Weekly Digest | Executive | Header only + rollup tables | Ready |

Legend: sections only appear when their data is present (empty-section suppression is a Track 19.17 lock, verified in Track 19.18 tests).

## Cover Page audit

- **Cover exists on every report** — locked by Track 19.16 phase E tests + Track 19.17 `sections[0] in {header, cover}` lock.
- **Wordmark** — new in Track 19.18. `MASCI · Incident Intelligence` in SF Mono.
- **Type + case number** — 32pt title + subtitle.
- **Slate-black banner** — audience label + case number pill.
- **8-field meta grid** — Occurred, Location, Project, Client, PM, Superintendent, Reported by, Case State.
- **Attorney Work Product stamp** — bottom of cover.

## Executive Summary audit

- **Case Story paragraph** — auto-composed narrative reading like a written brief.
- **30-second briefing** — state, SLA, readiness %, OSHA status, root-cause status.
- **Open blockers card** — bulleted, only when blockers exist.

Reads in ≤ 30 seconds. VP-of-Ops standard.

## Photograph audit

- Inline tiles, 2 columns, 2.6in height, `object-fit: cover`.
- Every tile carries a monospace metadata line (index, capture timestamp, GPS coordinate).
- Optional caption below.
- `page-break-inside: avoid` per tile.

## Table audit

- Thick slate header row (`background: #0f172a; color: #f8fafc`).
- Header letter-spacing + uppercase for legal-document look.
- Row `page-break-inside: avoid` (locked Track 19.16).
- `thead: display: table-header-group` so table headers repeat when tables span pages.

## Whitespace audit

- Page margins: 0.75in top, 0.85in bottom, 0.6in sides.
- Section headings: 22pt top margin, 8pt bottom + 1.4pt border-bottom.
- Body font-size: 10.5pt, line-height 1.5 (readable but not spacious).
- Cover minimum height: 9in (fills the page — never a short cover).

## Nothing to remove

Every section, when it renders, provides operational value. Every section not rendering is empty and correctly suppressed. Every heading has content underneath. Every row is meaningful.

## Nothing to add

- No OSHA 300 / 300A row (deferred by user).
- No compliance intelligence widget (deferred by user).
- No custom logos beyond the wordmark (customer will supply their brand asset in a later track).
- No signatures block (case closeout uses on-screen actor identity, not printed signatures — this is intentional and matches the operational model).

## Verdict

🟢 **Every generated document is executive-ready and legally defensible.**  
Nothing "looks like software." Everything reads like a professionally prepared investigation.
