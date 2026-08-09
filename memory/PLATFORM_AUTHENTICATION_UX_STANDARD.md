# PLATFORM_AUTHENTICATION_UX_STANDARD

Status: OPEN — PRE-C10 blocking standard

## Required runtime behavior

- sign-in entry points must be visible, legible, and compact.
- signed-in account state must not dominate the page chrome.
- logout must clear protected access and return the user to a usable public/home state.
- protected routes must challenge again after logout.
- signed-out confirmation must be obvious.

## Current verified progress

- preview multi-login and protected admin truth routes work with current token pair.
- screenshot-led quality gate was hardened to preserve directory + portal auth context during protected-surface certification.

## Open runtime checks

- full public-home / logout / post-logout protected-route challenge certification.
- contrast and compactness pass on all login surfaces.