# Project Handover (for next dev window)

Last updated: 2026-02-14  
Branch: `main`  
Working tree: clean

## 1. Repository Snapshot

- Recent commits (latest first):
  - `90ead5f` docs: refresh bilingual README for LmNotebook positioning
  - `effdba8` release-bug-fix
  - `02af4fd` ci: stabilize release workflow and bump app version to 1.0.4
  - `a40900e` ci: fix release version injection on windows shell
- Current app package version: `1.0.4` (`package.json`)
- Existing tags include: `v1.0.5`, `v1.0.4`, `v1.0.3`, `v1.0.2`, `v1.0.1`, `v1.0.0`

## 2. Release Status (important)

- GitHub Release assets exist for v1.0.4 (win/mac/linux), but there was at least one run with Linux job failure.
- A user-side startup popup was reported:
  - `Backend Missing`
  - expected path: `resources/backend/origin_backend.exe`
- Packaging config currently uses:
  - `extraResources.from = src/backend/dist/origin_backend`
  - runtime probe in `src/main/index.ts` expects executable under `resources/backend/...`
- Auto-update is configured via `electron-updater` and GitHub publish in `package.json`.

## 3. TODO List Status (11 items)

### P0 (release blocking)

1. Logo not replaced (`logo4.png`)  
Status: `NOT DONE`  
Notes: only `build/icon.ico` and `build/icon.png` currently exist.

2. Rename app to `LmNotebook`  
Status: `PARTIAL`  
Done: README title/positioning updated.  
Not done: `productName`, `shortcutName`, window/app strings still mainly `Origin Notes`.

3. Auto-accept button overlap with model selector when collapsed  
Status: `PENDING/VERIFY`  
Needs deterministic CSS/layout fix + regression check in narrow width.

4. Frontend entry for vector/embedding model config  
Status: `NOT DONE`  
Current `ModelSettings.vue` only handles chat providers/models.  
No explicit UI for `EMBEDDING_*`.

5. Close `X` behavior + multi-instance confusion  
Status: `PARTIAL`  
Tray/minimize logic exists in `src/main/index.ts`, but user reports:
  - close behavior not aligned with expectation
  - multiple app processes/instances observed
Requires explicit policy + single-instance verification.

6. Full zh/en switching coverage  
Status: `PARTIAL`  
`messages.json` exists and many strings are localized, but not all UI paths are guaranteed complete.

10. Undo/Redo logic anomaly (can undo to empty unexpectedly)  
Status: `NOT DONE`  
Need to audit editor history boundaries and programmatic content updates.

### P1 (next short iteration)

7. Online feature benchmarking / plugin-market direction  
Status: `NOT STARTED` (product planning)

8. Performance and package size optimization  
Status: `ONGOING` (not closed)

9. GIF and ECharts support  
Status: `NOT STARTED`

11. Agent extension with skills  
Status: `NOT STARTED` (architecture design item)

## 4. Known Gaps Confirmed in Current Code

- Embedding config is backend-env driven (`src/backend/core/config.py`, `.env`), no complete user-facing frontend workflow.
- README mentions embedding model, but onboarding is still not enough for non-technical users.
- Branding is mixed (`LmNotebook` in docs vs `Origin Notes` in app/package/runtime strings).

## 5. Execution Plan for Next Window (recommended order)

1. Stabilize release correctness first
   - fix backend packaging path contract (build -> runtime lookup)
   - ensure win/mac/linux CI all pass
   - test clean install startup (no Backend Missing popup)
2. Complete P0 UX/logic fixes
   - overlap bug (auto-accept/model select)
   - close behavior policy (minimize-to-tray vs exit toggle)
   - single-instance lock hard check
   - undo/redo history bug
3. Complete configuration completeness
   - add embedding provider/model/key section in settings
   - add validation + fallback behavior
4. Finish branding and i18n pass
   - rename visible app branding to `LmNotebook`
   - run zh/en string coverage audit
5. Then move to P1 items (perf/size, GIF/ECharts, plugin strategy)

## 6. High-Value Files Map

- Desktop lifecycle / tray / backend boot:
  - `src/main/index.ts`
- Build/package/update:
  - `package.json`
  - `.github/workflows/release.yml`
- Model settings UI:
  - `src/renderer/src/components/agent/ModelSettings.vue`
- Agent main UI:
  - `src/renderer/src/components/agent/AgentBubble.vue`
- i18n:
  - `src/renderer/src/i18n/messages.json`
- Backend config/env:
  - `src/backend/core/config.py`
  - `src/backend/.env.example`

## 7. Quick Verification Commands

```bash
# Frontend/Electron build
npm run build

# Backend tests
cd src/backend
python -m pytest -q

# Release workflow local sanity (optional)
# verify src/backend/dist/origin_backend exists before electron-builder
```

## 8. Notes for Next Engineer

- Do not assume docs branding update means runtime branding is done.
- Treat release packaging + startup backend contract as top priority.
- Keep changes incremental and testable; avoid mixing P0 bugfix with large visual refactors in same commit.
- Keep commit boundaries clear: `release-fix`, `ui-fix`, `config-entry`, `i18n-pass`.

