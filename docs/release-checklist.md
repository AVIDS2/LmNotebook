# Release Checklist

## Build Preconditions

1. Ensure Node.js 18+ is installed
2. Ensure Python 3.10+ is installed
3. Ensure `backend_env` exists at repo root
4. Ensure backend deps are installed in `backend_env`
5. Ensure `src/backend/.env` is configured for your target provider
6. Run all build/check commands in a clean shell to avoid conda auto-init issues:
   `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/release_check.ps1`

## Backend Build (PyInstaller)

1. `cd src/backend`
2. `..\..\backend_env\Scripts\activate`
3. `pyinstaller origin-backend.spec -y`
4. Verify output exists: `src/backend/dist/origin_backend/`

## Electron Build

1. `cd ../..`
2. `npm run build:win`
3. Verify output exists: `dist/Origin Notes Setup 1.0.0.exe`

## Smoke Tests (Local)

1. Launch app
2. Create a note and edit content
3. Delete and restore a note
4. Run a knowledge search with `@笔记知识库`
5. Switch model provider in Model Settings
6. Confirm chat stream works and tool actions update UI

## Artifacts to Verify

1. `dist/` contains installer
2. `resources/backend/origin_backend.exe` exists in installed app
3. `models.json` and `checkpoints.db` persist in user data directory

## Optional

1. Backup user data directory before release testing
2. Tag git commit for release
