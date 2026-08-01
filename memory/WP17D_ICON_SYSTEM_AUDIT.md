# WP-17D Icon System Audit

Date: 2026-08-01

## Executive Scope
Executive Amendment #4 reclassifies iconography as a first-class design-system system.
Icons are now governed at the same level as headers, typography, spacing, buttons, forms, and navigation.

## Current Frontend Icon Ecosystem Inventory

### 1) Primary interactive icon library
- `lucide-react` is the dominant icon source across the product.
- It is imported widely in pages and shared components.
- Current issue is not mixed vendor packages at scale; it is inconsistent **usage** of the same library:
  - different icon sizes (`h-3`, `h-3.5`, `h-4`, `h-5`, `h-6`, etc.)
  - inconsistent semantic mapping for the same action
  - page-level color / stroke / wrapper overrides

### 2) Inline SVG survivors
Inline SVG is still present in several frontend surfaces and utilities:
- `src/pages/admin/AdminOperationalIntelligence.jsx`
- `src/pages/admin/AdminRecovery.jsx`
- `src/components/MapThumbnail.jsx`
- `src/components/odr/OdrTrustBanner.jsx`
- `src/components/OperationsTrustCenter.jsx`
- `src/components/admin/StorageObservabilityCard.jsx`
- `src/lib/operations-map/icons.js` (generated SVG / data URI map markers)
- `src/pages/TrainingQrPoster.jsx` references `/api/qr.svg` for QR generation (functional QR asset, not decorative UI iconography)

### 3) Emoji / text-icon survivors
Emoji and text-symbol iconography remain in route copy, admin helpers, and a few operator-facing flows. Examples found include:
- `⚠`, `✅`, `❌`, `📷`, `📎`, `🔒`, `🗑️`, `🛡️`, `🏗️`
- Some of these are inside training data / admin guide copy, but others appear in route-level UI and still count as icon-language drift.

### 4) External icon libraries audit
Search results found **no active imports** from:
- `react-icons`
- `@heroicons/*`
- `@fortawesome/*`
- `@mui/icons-material`

### 5) Local SVG asset inventory
- No `.svg` files are currently imported as a standalone frontend icon family.

## Governance Risks Identified
1. Shared components still import Lucide icons directly instead of a governed wrapper.
2. The same action can still appear with different glyphs or wrapper treatments.
3. Icon sizing and visual weight vary too much between shells, buttons, cards, and list rows.
4. Emoji icons bypass the design system entirely.
5. Inline SVG visuals in trust / admin / map surfaces are not yet normalized under a single icon standard.

## Governed System Introduced In This Pass
Created the first canonical icon foundation:
- `src/components/icons/AppIcon.jsx`
- `src/components/icons/semanticRegistry.js`

This system now governs:
- size tokens
- stroke weight
- semantic naming
- tone / state classes
- rounded Lucide stroke behavior

## Shared-System Adoption Completed In This Pass
The governed icon wrapper is now wired into shared header / shell primitives:
- `CanonicalHeader.jsx`
- `PortalShell.jsx`

This means shared navigation controls now inherit a single icon source instead of raw per-file Lucide styling.

## Required Next Rollout
The next WP-17D icon work must happen by **shared component family**, not random route patches:
1. Shared shells and nav primitives
2. Buttons / action bars / utility controls
3. Form helpers / progress / empty states / toast icons
4. Table row actions / dialogs / destructive controls
5. Domain-specific surfaces (safety, fleet, trench, transportation, QA/QC, HR, admin)

## Certification Rule
A route fails icon certification if it shows any of the following:
- raw legacy icon usage outside the governed wrapper where a shared component exists
- emoji used as UI iconography
- mixed icon sizes without governed reason
- inconsistent stroke weights
- inconsistent icon-to-action metaphors
- outline/filled mixing that is not part of the governed system