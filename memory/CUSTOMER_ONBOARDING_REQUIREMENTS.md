# CUSTOMER ONBOARDING REQUIREMENTS

**Phase 11 deliverable.** What MASCI must collect to stand up Customer #2.

## Required from the customer (one-time)

### Identity
- [ ] Legal entity name (`Bob's Excavating LLC`)
- [ ] Public platform name (`Bob's Hub`, `Bob's Ops`, etc.)
- [ ] Tagline (optional)
- [ ] Logo files (3 variants: light-bg, dark-bg, full lockup) · PNG · SVG preferred
- [ ] Favicon (`.ico`) + PWA icons (180×180, 192×192, 512×512)
- [ ] Primary brand color (hex)
- [ ] Secondary brand color (hex)
- [ ] Accent color (hex)
- [ ] Preferred email sender domain (e.g. `notifications@bobsexcavating.com`)
- [ ] Preferred reply-to address
- [ ] Company physical address (legal pages)
- [ ] Company phone (help/legal pages)
- [ ] Support email (footer + help)
- [ ] Legal entity name + jurisdiction (Terms of Service · Privacy Policy)
- [ ] Operational time zone (default: customer HQ tz)
- [ ] Default language (`en` / `es`)
- [ ] Modules enabled (PM · HR · Safety · Shop · Dispatch · Field Leadership · Trench Safety · Project Staffing — defaults to all)

### Infrastructure
- [ ] Custom domain (e.g. `hub.bobsexcavating.com`) + CNAME ready
- [ ] MongoDB Atlas DB provisioned (customer-paid or MASCI-managed line-item)
- [ ] Cloudflare R2 bucket provisioned
- [ ] Resend account + verified sender domain
- [ ] Sentry project + DSN
- [ ] Optional: Motive · FleetWatcher · MaintainX credentials if customer uses them

### People & data
- [ ] Initial admin user (email + temp password method)
- [ ] Employee master (CSV import — Last, First, Preferred, Email, Phone, Hire date, Title, Project assignments)
- [ ] Active projects (CSV import — Job#, Name, Status, Address)
- [ ] Equipment master (CSV import — Unit#, Year/Make/Model, Type, Status)
- [ ] Supplier master (optional CSV)
- [ ] PM roster (Job# → PM/Co-PM email mapping)
- [ ] Existing document templates (optional)

### Terminology / settings (per customer)
- [ ] Crew terminology — "MASCI Crews" → "Bob's Crews" (or "Field Crews" generic)
- [ ] Field-leadership form list (which of the 9 standard forms applies)
- [ ] Safety meeting cadence
- [ ] Daily report required fields
- [ ] OSHA recordkeeping flags
- [ ] Sub-prime relationship (does customer subcontract? — drives `non_company` field default)

## MASCI-side onboarding tasks

1. Provision customer-specific infra (Atlas / R2 / Resend / Sentry).
2. Fork or clone MASCI repo into `customer-{slug}` branch (Model 1) OR set up customer record in BrandConfig (Model 2).
3. Drop customer assets into `frontend/public/` (Model 1) OR upload to BrandConfig store (Model 2).
4. Run search-replace from MASCI strings → customer strings using BrandConfig keys (Model 2 saves most of this work).
5. Deploy customer pod with their `.env`.
6. Run admin seed script to create their first admin user.
7. Run employee/project/equipment CSV imports.
8. Smoke test the same RC1 gate checklist (auth · roles · workflows · search · device · trust · notifications · discoverability · isolation).
9. Hand over admin credentials.
10. Schedule a 1-hour training with their primary admin.

## Onboarding deliverable bundle

- Welcome email with admin URL + credentials
- Admin Quick Start (1-pager + 5-min video)
- Field worker QR codes (printed for each project)
- Foreman Spanish/English cheat sheet
- 30-day check-in calendar invite

## Estimated time per customer (Model 2 after Phase 1-5 of roadmap)

- Provisioning: 1 day
- Branding config + asset drop: 1 day
- CSV imports + admin user: 1 day
- Smoke test + handover: 1 day
- **Total: 4 days per customer onboard**

(Model 1 today, before Phase 1 cleanup: 2-3 weeks per customer due to manual find-replace.)
