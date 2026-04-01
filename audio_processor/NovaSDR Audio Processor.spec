# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all
from PyInstaller.utils.hooks import copy_metadata

datas = [('recordings', 'recordings')]
binaries = [('/Users/tomasduca/CascadeProjects/audio_processor/venv/lib/python3.14/site-packages/novasdr_nr/novasdr_nr*.so', '.')]
hiddenimports = ['numpy', 'numpy.core._multiarray_umath', 'scipy', 'scipy.signal', 'scipy.fft', 'sounddevice', '_sounddevice', 'novasdr_nr', 'pydub', 'PyQt5', 'PyQt5.QtCore', 'PyQt5.QtGui', 'PyQt5.QtWidgets']
datas += copy_metadata('numpy')
datas += copy_metadata('scipy')
tmp_ret = collect_all('sounddevice')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('scipy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['novasdr_gui_qt.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
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
