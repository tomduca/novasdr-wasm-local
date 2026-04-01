# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['novasdr_gui_qt.py'],
    pathex=[],
    binaries=[],
    datas=[('recordings', 'recordings')],
    hiddenimports=['numpy', 'scipy', 'sounddevice', 'novasdr_nr', 'pydub', 'PyQt5'],
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
    name='NovaSDR Audio Processor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
app = BUNDLE(
    exe,
    name='NovaSDR Audio Processor.app',
    icon=None,
    bundle_identifier=None,
)
