# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for Focus Mode App.
Build: pyinstaller packaging/focus-mode-app.spec

SPECPATH is a PyInstaller built-in that points to the directory containing
this file (packaging/). We use it to build absolute paths to the project
root so PyInstaller finds the sources regardless of the working directory.
"""

import os

block_cipher = None

# Project root is one level above packaging/
ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))

# Bundle assets only if the directory exists
datas = []
assets_dir = os.path.join(ROOT, "focus_mode_app", "assets")
if os.path.isdir(assets_dir):
    datas.append((assets_dir, "focus_mode_app/assets"))

a = Analysis(
    [os.path.join(ROOT, "focus_mode_app", "main.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # uvicorn dynamic workers and protocols
        "uvicorn.lifespan.on",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.http.httptools_impl",
        "uvicorn.protocols.websockets.websockets_impl",
        "uvicorn.protocols.websockets.wsproto_impl",
        # ttkbootstrap themes (loaded dynamically)
        "ttkbootstrap.themes",
        "ttkbootstrap.themes.standard",
        "ttkbootstrap.themes.user",
        # pydantic v2 internals
        "pydantic.deprecated.class_validators",
        "pydantic.deprecated.config",
        "pydantic.deprecated.decorator",
        "pydantic.deprecated.tools",
        "pydantic_core",
        # websocket-client
        "websocket",
        "websocket._core",
        "websocket._http",
        "websocket._logging",
        # PIL tkinter bridge
        "PIL._imagingtk",
        "PIL._tkinter_finder",
        # importlib.metadata (used by updater)
        "importlib.metadata",
        "importlib_metadata",
        # focus_mode_app dynamic imports
        "focus_mode_app.core.ha_client",
        "focus_mode_app.core.ha_config",
        "focus_mode_app.core.focus_lock",
        "focus_mode_app.core.session",
        "focus_mode_app.core.restore",
        "focus_mode_app.core.updater",
        "focus_mode_app.gui.ha_settings_dialog",
        "focus_mode_app.gui.material_theme",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(ROOT, "packaging", "rthook_tcl.py")],
    excludes=[
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
        "jupyter",
        "IPython",
        "test",
        "unittest",
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="focus-mode-app",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,   # keep stdout for HA debug logging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="focus-mode-app",
)
