# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for CopyCat.exe (CLI)
# Build: pyinstaller CopyCat.spec

a = Analysis(
    ['CopyCat.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['xml.etree.ElementTree', 'zipfile', 'base64', 'zlib', 'struct'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'flask'],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CopyCat',
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
