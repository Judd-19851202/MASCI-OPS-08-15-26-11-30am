# WP-18DA Frontend Performance Report

## Route inventory

- Frontend routes inventoried from source: `462`

## Preview runtime

- Home route navigation timing:
  - `domContentLoaded 926ms`
  - `loadEventEnd 1682ms`
  - `responseEnd 117ms`
- Final frontend verification:
  - `domContentLoaded 915ms`
  - `loadEventEnd 1302ms`
- Responsive verification passed at `390`, `768`, `1440`
- No blank shell, no repeated recompilation loop, no horizontal overflow in final verification

## Production runtime comparison

- Production navigation timing:
  - `domContentLoaded 1071ms`
  - `loadEventEnd 1075ms`
  - `responseEnd 300ms`
- Final comparison agent result: preview shell is faster than production and shows **no material drift**

## Build evidence

- `yarn build` success
- Build duration: `50.53s`
- Build output total: `55,126,489` bytes including source maps + static media
