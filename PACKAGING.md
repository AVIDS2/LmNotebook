# LmNotebook Packaging Guide

## Overview

This project ships as a hybrid app: Electron frontend + Python backend. Packaging is two steps:
1. Build the Python backend with PyInstaller
2. Build the Electron app with electron-builder

## Prerequisites

- Node.js
- Python
- Virtual environment `backend_env` at repo root

Important: use `backend_env` for PyInstaller. Do not use Anaconda base. It will massively bloat the build.

## Step 1: Package Python Backend

```powershell
# Enter backend dir
cd src/backend

# Activate dedicated venv (repo root)
..\..\backend_env\Scripts\activate

# Build backend
..\..\backend_env\Scripts\python -m PyInstaller origin-backend.spec -y
```

Output directory:
- `src/backend/dist/origin_backend/`

## Step 2: Package Electron App

```powershell
# Back to repo root
cd ../..

# Build full app
npm run build:win
```

Output:
- `dist/LmNotebook Setup 1.0.0.exe`

## Why `backend_env` is Required

| Environment | Result |
| --- | --- |
| `backend_env` | Minimal dependencies, backend ~20-30MB |
| Anaconda base | Huge bundle (often 500MB+) |

## PyInstaller Mode

This repo uses directory mode (`exclude_binaries=True` + `COLLECT`):
- Faster startup (no self-extract)
- Output: `dist/origin_backend/`

One-file mode is not used by default (`--onefile`), because it slows startup.

## electron-builder Integration

`package.json` includes:

```json
"extraResources": [
  {
    "from": "src/backend/dist/origin_backend",
    "to": "backend",
    "filter": ["**/*"]
  }
]
```

Runtime backend path:
- `resources/backend/origin_backend.exe`

## One-Command Build

```powershell
cd src/backend ; ..\..\backend_env\Scripts\activate ; ..\..\backend_env\Scripts\python -m PyInstaller origin-backend.spec -y ; cd ../.. ; npm run build:win
```


