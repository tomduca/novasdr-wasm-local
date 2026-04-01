# NovaSDR Audio Processor - Standalone Application Guide

This guide explains how to create and distribute standalone desktop applications for macOS and Windows.

## 📦 What's Included

### Native GUI Application
- **File:** `audio_processor/audio_processor_native_gui.py`
- **Framework:** tkinter (cross-platform, no browser needed)
- **Features:**
  - Device selection (input/output)
  - Mode selector (SSB/CW)
  - Preset selection (Moderate, Aggressive, Ultra, Extreme)
  - Bypass toggle
  - Audio recording (MP3/WAV)
  - Real-time log display
  - Start/Stop controls

### Build Scripts
- **macOS:** `build_macos.sh` → Creates `.app` bundle
- **Windows:** `build_windows.bat` → Creates `.exe` executable

## 🚀 Quick Start (Development)

### Run Native GUI (Without Building)

```bash
cd audio_processor
./run_native_gui.sh
```

This runs the GUI directly from Python (requires virtual environment setup).

## 🏗️ Building Standalone Applications

### Prerequisites

1. **Python 3.10+** installed
2. **Virtual environment** set up (see INSTALL.md)
3. **NovaSDR Rust module** compiled (see INSTALL.md)
4. **PyInstaller** (installed automatically by build scripts)

### macOS Application (.app)

```bash
cd audio_processor
./build_macos.sh
```

**Output:** `dist/NovaSDR Audio Processor.app`

**To run:**
```bash
open "dist/NovaSDR Audio Processor.app"
```

**To distribute:**
- Compress the `.app` bundle: `zip -r NovaSDR.zip "dist/NovaSDR Audio Processor.app"`
- Share the `.zip` file
- Users can extract and drag to Applications folder

### Windows Application (.exe)

**Note:** Must be built on Windows machine

```batch
cd audio_processor
build_windows.bat
```

**Output:** `dist\NovaSDR Audio Processor.exe`

**To run:**
```
dist\NovaSDR Audio Processor.exe
```

**To distribute:**
- Share the `.exe` file directly
- Users can run it without Python installation

## 📋 Build Details

### What PyInstaller Does

1. **Bundles Python interpreter** - No Python installation needed
2. **Includes all dependencies** - numpy, scipy, sounddevice, etc.
3. **Packages Rust module** - NovaSDR filter included
4. **Creates single executable** - Easy to distribute

### File Sizes (Approximate)

- **macOS .app:** ~150-200 MB
- **Windows .exe:** ~100-150 MB

Sizes are large because they include:
- Python runtime
- NumPy/SciPy libraries
- Audio libraries
- NovaSDR Rust module

## 🔧 Platform-Specific Notes

### macOS

**Gatekeeper Warning:**
- First run may show "unidentified developer" warning
- Right-click → Open → Open to bypass
- Or: System Preferences → Security & Privacy → Allow

**Code Signing (Optional):**
```bash
# Sign the app (requires Apple Developer account)
codesign --deep --force --sign "Developer ID Application: Your Name" "dist/NovaSDR Audio Processor.app"
```

**Notarization (Optional):**
- Required for distribution outside App Store
- Requires Apple Developer account ($99/year)

### Windows

**Windows Defender:**
- May flag unsigned .exe as potential threat
- Users need to click "More info" → "Run anyway"

**Code Signing (Optional):**
- Purchase code signing certificate (~$100-300/year)
- Sign with `signtool.exe`

**Antivirus False Positives:**
- PyInstaller executables sometimes trigger antivirus
- Submit to VirusTotal to verify safety
- Consider code signing to reduce false positives

### Linux (Future)

To build for Linux:
```bash
pyinstaller --name="NovaSDR Audio Processor" \
    --onefile \
    --add-data="recordings:recordings" \
    --hidden-import=numpy \
    --hidden-import=scipy \
    --hidden-import=sounddevice \
    --hidden-import=novasdr_nr \
    --hidden-import=pydub \
    audio_processor_native_gui.py
```

## 🎯 Distribution Checklist

### Before Building

- [ ] Test native GUI thoroughly
- [ ] Verify NovaSDR module works
- [ ] Test on clean system (no Python installed)
- [ ] Check all features (recording, mode switching, etc.)

### macOS Distribution

- [ ] Build .app bundle
- [ ] Test on different macOS version
- [ ] (Optional) Code sign
- [ ] (Optional) Notarize
- [ ] Create DMG installer (optional)
- [ ] Write installation instructions

### Windows Distribution

- [ ] Build .exe on Windows machine
- [ ] Test on Windows 10/11
- [ ] (Optional) Code sign
- [ ] Create installer with Inno Setup (optional)
- [ ] Write installation instructions
- [ ] Test antivirus compatibility

## 📝 User Installation Instructions

### macOS Users

1. Download `NovaSDR.zip`
2. Extract the zip file
3. Drag `NovaSDR Audio Processor.app` to Applications folder
4. Right-click → Open (first time only)
5. Install BlackHole 2ch (https://existential.audio/blackhole/)
6. Configure Multi-Output Device in Audio MIDI Setup
7. Run the application

### Windows Users

1. Download `NovaSDR Audio Processor.exe`
2. Run the executable
3. If Windows Defender warns, click "More info" → "Run anyway"
4. Install VB-Cable or similar virtual audio device
5. Configure audio routing
6. Use the application

## 🐛 Troubleshooting

### "Module not found" errors

Add missing modules to build script:
```bash
--hidden-import=missing_module_name
```

### Large file size

Normal for bundled applications. To reduce:
- Use `--onefile` (already enabled)
- Exclude unnecessary packages
- Use UPX compression (may trigger antivirus)

### Audio device not detected

- Ensure virtual audio device is installed
- Check system audio settings
- Restart application

### Recording not working

- Check if ffmpeg is installed (for MP3)
- Falls back to WAV if ffmpeg unavailable
- Verify write permissions to recordings folder

## 🔄 Alternative: PyInstaller Spec File

For advanced customization, create `novasdr.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['audio_processor_native_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('recordings', 'recordings')],
    hiddenimports=['numpy', 'scipy', 'sounddevice', 'novasdr_nr', 'pydub'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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

# macOS only
app = BUNDLE(
    exe,
    name='NovaSDR Audio Processor.app',
    icon='../assets/icon.icns',
    bundle_identifier='com.novasdr.audioprocessor',
)
```

Build with:
```bash
pyinstaller novasdr.spec
```

## 📚 Additional Resources

- **PyInstaller Documentation:** https://pyinstaller.org/
- **tkinter Tutorial:** https://docs.python.org/3/library/tkinter.html
- **Code Signing (macOS):** https://developer.apple.com/support/code-signing/
- **Code Signing (Windows):** https://docs.microsoft.com/en-us/windows/win32/seccrypto/cryptography-tools

## 🎉 Success!

Once built, you have a fully standalone application that:
- ✅ Runs without Python installation
- ✅ Includes all dependencies
- ✅ Works on macOS and Windows
- ✅ Can be distributed easily
- ✅ Provides native GUI experience

**73 de LU2MET!** 📻
