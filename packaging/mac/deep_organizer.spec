# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for producing the Deep Organizer macOS app bundle."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules

if "__file__" in globals():
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
else:
    PROJECT_ROOT = Path.cwd()
APP_NAME = "Deep Organizer"
BUNDLE_IDENTIFIER = "com.deeporganizer.desktop"
VERSION = "1.0.0"

block_cipher = None

datas = []

hiddenimports = (
    collect_submodules("langchain")
    + collect_submodules("langgraph")
    + collect_submodules("dotenv")
)

analysis = Analysis(
    [str(PROJECT_ROOT / "main.py")],
    pathex=[str(PROJECT_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(analysis.pure, analysis.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
)

coll = COLLECT(
    exe,
    analysis.binaries,
    analysis.zipfiles,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

icon_path = PROJECT_ROOT / "packaging" / "mac" / "deep_organizer.icns"
app_icon = str(icon_path) if icon_path.exists() else None

app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=app_icon,
    bundle_identifier=BUNDLE_IDENTIFIER,
    info_plist={
        "CFBundleDisplayName": APP_NAME,
        "CFBundleName": APP_NAME,
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
    },
)
