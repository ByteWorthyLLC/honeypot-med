# -*- mode: python ; coding: utf-8 -*-
from glob import glob
import os

PROJECT_ROOT = os.path.abspath(SPECPATH)
PACK_DATAS = [
    (path, "honeypot_med/packs")
    for path in glob(os.path.join(PROJECT_ROOT, "src", "honeypot_med", "packs", "*.json"))
]
STATIC_DATAS = [
    (path, "honeypot_med/static")
    for path in glob(os.path.join(PROJECT_ROOT, "src", "honeypot_med", "static", "*.jpg"))
]


a = Analysis(
    ['app.py'],
    pathex=[os.path.join(PROJECT_ROOT, 'src')],
    binaries=[],
    datas=PACK_DATAS + STATIC_DATAS,
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='honeypot-med',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
