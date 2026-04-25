# MASCI Job Site Safety Inspection — PRD

## Original Problem Statement
> "this what I have so far........ I want/need a fillable form I can send out to inspectors to do site safety inspections, then print or save as PDF..... Look at what I have see what we could add or take away to make it awesome & work flawlessly on computers or mobile devices (Phones, tablets)"

User shared the existing MASCI Job Site Safety Inspection Report PDF. Form rebuilt as a polished, mobile-first web app.

## User Choices
- (1a) Save inspections to MongoDB
- (2a) No login — anyone with the link can fill it out
- (3a) Photo uploads with attached image previews on PDF
- (4a) On-screen finger / stylus signature capture (Inspector + Foreman)

## Architecture
- **Backend:** FastAPI + Motor (MongoDB) at `/app/backend/server.py`. Routes prefixed `/api`.
- **Frontend:** React 19 + Tailwind + shadcn/ui + lucide-react + react-signature-canvas + sonner.
- **Storage:** Single `inspections` collection. Photos and signatures stored as base64 data URLs inline.
- **Design:** Swiss/industrial high-contrast aesthetic — Chivo display + IBM Plex Sans body, MASCI safety-yellow accent, no gradients, large tap targets (h-14), print-optimized stylesheet.

## Personas
- **Field Inspector** — fills out form on phone in sunlight, snaps photos, signs on screen.
- **Foreman / Supervisor** — countersigns on the same device.
- **Office / Safety Manager** — reviews dashboard, prints/saves PDFs for filing.

## Core Requirements (static)
- 13 sections matching MASCI source PDF
- YES/NO segmented toggles for PPE Compliance (9 items) + Site Hazards (8 items)
- 7 conditional sections (Equipment, Traffic Control, MOT Moving Trucks, Fall Protection, Excavation, Electrical, Concrete/Paving) — top-level Yes/No with expanding sub-checklist + notes
- Corrective Actions: Hazards Observed / Stop Work Issued / Corrected On Site + responsible party + notes + photo uploads
- Inspector + Foreman signature pads
- Print / Save-as-PDF rendering a clean branded report

## What's Implemented (2026-02-15)
- Dashboard `/` — stats pills, list of inspections, delete from row
- `/inspect/new` — full multi-section fillable form with validation
- `/inspect/:id` — read-only branded report view + Print + Delete
- Photo upload with client-side compression (≤1280px, 78% JPEG)
- Signature pads with Clear button, captured as PNG data URL
- Print stylesheet: monochrome, page-break-avoid per section, hides nav/buttons
- Backend CRUD: POST/GET list/GET id/DELETE — all tested (8/8 backend tests + full UI e2e pass)
- All interactive elements have `data-testid`

## Backlog
**P0**
- _none — MVP complete and tested_

**P1**
- Email/SMS share — auto-email PDF to project manager / client on submit (Resend/SendGrid integration)
- Server-rendered PDF (using ReportLab or weasyprint) for consistent output independent of browser
- CSV / multi-report export for monthly safety meetings

**P2**
- Switch photos to object storage (S3-compatible) once a single inspection commonly exceeds ~5 MB
- Aggregation `$size` on `photos` for the list endpoint to skip pulling base64 bytes
- Optional inspector login + per-account dashboards
- Auto-fill "Project Name" from a Projects table; QR-code per project for one-tap form access in the field
- Trend dashboard: hazards-by-section over time, top recurring findings

## Next Action Items
1. Hand the URL to a foreman, fill out one real inspection on a phone end-to-end, gather feedback.
2. If reports will be emailed, decide on Resend vs SendGrid and add a recipient list.
3. Decide PDF strategy: keep browser print (zero deps) or move to server-rendered PDF.
