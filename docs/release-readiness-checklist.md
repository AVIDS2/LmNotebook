# Release Readiness Checklist

## Automated

- Run `npm run verify:release`
- Confirm `node scripts/ui-hardening-contract.test.mjs` is green
- Confirm `npm run build` is green

## Manual Smoke (Desktop App)

- Window close (`X`) follows tray/minimize policy
- Only one app instance is active in release mode
- Tray icon and taskbar icon both use `LmNotebook` branding
- Composer row layout:
  - model selector caret adjacent to model label
  - no wide empty clickable model area
  - review button is clickable and positioned above send button
- i18n text has no placeholder mojibake (`????`)

## Packaging

- `npm run build:win`
- `npm run build:mac`
- `npm run build:linux`
