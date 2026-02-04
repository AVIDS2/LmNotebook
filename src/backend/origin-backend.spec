# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('core', 'core'), ('agent', 'agent'), ('services', 'services'), ('api', 'api')],
    hiddenimports=[
        'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 
        'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 
        'uvicorn.lifespan', 'uvicorn.lifespan.on', 
        'engineio.async_drivers.aiohttp',
        'langgraph.checkpoint.sqlite',
        'langgraph.checkpoint.sqlite.aio',
        'aiosqlite'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter', 'matplotlib', 'notebook', 'sphinx', 'IPython', 'pandas', 'torch', 'torchvision', 'torchaudio', 'tensorflow', 'jax', 'scipy'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='origin_backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='origin_backend',
)
