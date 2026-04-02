# Building NovaSDR Audio Processor - Standalone Applications

This guide covers building standalone desktop applications for macOS and Windows.

## Table of Contents

- [macOS Build](#macos-build)
- [Windows Build](#windows-build)
- [Common Prerequisites](#common-prerequisites)
- [Troubleshooting](#troubleshooting)

---

## macOS Build

### Prerequisites

1. **macOS 10.14 or higher**

2. **Xcode Command Line Tools**
   ```bash
   xcode-select --install
   ```

3. **Homebrew** (package manager)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

4. **Python 3.10 or higher**
   ```bash
   brew install python@3.14
   ```

5. **Rust** (for NovaSDR module)
   ```bash
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   source $HOME/.cargo/env
   ```

6. **BlackHole 2ch** (virtual audio device)
   ```bash
   brew install blackhole-2ch
   ```

7. **FFmpeg** (optional, for MP3 recording)
   ```bash
   brew install ffmpeg
   ```

### Build Steps

#### 1. Clone the Repository

```bash
git clone https://github.com/tomduca/novasdr-audio-processor.git
cd novasdr-audio-processor
```

#### 2. Build the Rust NovaSDR Module

```bash
cd novasdr_nr_py
pip install maturin
maturin develop --release
cd ..
```

#### 3. Set Up Python Virtual Environment

```bash
cd audio_processor
python3 -m venv venv
source venv/bin/activate
```

#### 4. Install Python Dependencies

```bash
pip install numpy scipy sounddevice PyQt5 pydub pyinstaller
```

#### 5. Build the macOS Application

```bash
./build_macos.sh
```

This creates:
```
dist/NovaSDR Audio Processor.app/
  ├── Contents/
  │   ├── MacOS/
  │   │   ├── NovaSDR Audio Processor (executable)
  │   │   ├── novasdr_nr.so (Rust module)
  │   │   └── ... (dependencies)
  │   ├── Info.plist (with microphone permissions)
  │   └── Frameworks/
  └── recordings/ (folder for recordings)
```

### Running the macOS App

**First time:**
- Right-click on `NovaSDR Audio Processor.app`
- Select **"Open"**
- Click **"Open"** in the dialog
- **Allow microphone access** when prompted

**Subsequent runs:**
- Double-click the app

### Distribution (macOS)

```bash
cd dist
zip -r NovaSDR-macOS.zip "NovaSDR Audio Processor.app"
```

Share the .zip file. Users:
1. Extract the .zip
2. Drag app to Applications folder
3. Right-click → Open (first time)
4. Allow microphone access

### macOS Code Signing (Optional)

For distribution outside the App Store:

```bash
# Ad-hoc signing (already done by build script)
codesign --force --deep --sign - "dist/NovaSDR Audio Processor.app"

# With Apple Developer certificate
codesign --force --deep --sign "Developer ID Application: Your Name" "dist/NovaSDR Audio Processor.app"

# Notarization (for Gatekeeper approval)
xcrun notarytool submit NovaSDR-macOS.zip --apple-id your@email.com --team-id TEAMID --wait
xcrun stapler staple "NovaSDR Audio Processor.app"
```

---

## Windows Build

### Prerequisites

**Note:** Windows build must be done on a Windows machine.

1. **Windows 10 or Windows 11**

2. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - **Important:** Check "Add Python to PATH" during installation

3. **Git for Windows**
   - Download from: https://git-scm.com/download/win

4. **Rust** (for NovaSDR module)
   - Download from: https://rustup.rs/
   - Run installer and follow prompts
   - Restart terminal after installation

5. **Visual Studio Build Tools** (required by Rust)
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++"
   - Or install full Visual Studio Community

6. **VB-CABLE** (virtual audio device)
   - Download from: https://vb-audio.com/Cable/
   - Install and restart

7. **FFmpeg** (optional, for MP3 recording)
   - Download from: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add bin folder to PATH

### Build Steps

#### 1. Clone the Repository

```cmd
git clone https://github.com/tomduca/novasdr-audio-processor.git
cd novasdr-audio-processor
```

#### 2. Build the Rust NovaSDR Module

```cmd
cd novasdr_nr_py
pip install maturin
maturin develop --release
cd ..
```

#### 3. Set Up Python Virtual Environment

```cmd
cd audio_processor
python -m venv venv
call venv\Scripts\activate.bat
```

#### 4. Install Python Dependencies

```cmd
pip install numpy scipy sounddevice PyQt5 pydub pyinstaller
```

#### 5. Build the Windows Application

```cmd
build_windows.bat
```

This creates:
```
dist\NovaSDR Audio Processor\
  ├── NovaSDR Audio Processor.exe
  ├── novasdr_nr.pyd (Rust module)
  ├── recordings\ (folder for recordings)
  └── ... (all dependencies)
```

### Running the Windows App

**First time:**
- Double-click `NovaSDR Audio Processor.exe`
- If Windows Defender SmartScreen appears:
  - Click "More info"
  - Click "Run anyway"
- Allow microphone access when prompted

**Subsequent runs:**
- Double-click the .exe

### Distribution (Windows)

**Option 1: ZIP Archive**
```cmd
cd dist
# Use Windows Explorer to compress "NovaSDR Audio Processor" folder to .zip
```

**Option 2: Installer with Inno Setup**

1. Download Inno Setup: https://jrsoftware.org/isdl.php
2. Create installer script (example below)
3. Compile installer

Example Inno Setup script (`installer.iss`):
```ini
[Setup]
AppName=NovaSDR Audio Processor
AppVersion=1.0.0
DefaultDirName={pf}\NovaSDR Audio Processor
DefaultGroupName=NovaSDR Audio Processor
OutputDir=installer
OutputBaseFilename=NovaSDR-Setup

[Files]
Source: "dist\NovaSDR Audio Processor\*"; DestDir: "{app}"; Flags: recursesubdirs

[Icons]
Name: "{group}\NovaSDR Audio Processor"; Filename: "{app}\NovaSDR Audio Processor.exe"
Name: "{commondesktop}\NovaSDR Audio Processor"; Filename: "{app}\NovaSDR Audio Processor.exe"
```

### Windows Code Signing (Optional)

For professional distribution:

1. Purchase code signing certificate
2. Sign the executable:
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com "NovaSDR Audio Processor.exe"
   ```

---

## Common Prerequisites

### Audio Device Setup

#### macOS
1. Install BlackHole 2ch: `brew install blackhole-2ch`
2. Open **Audio MIDI Setup** (Applications → Utilities)
3. Create **Multi-Output Device**:
   - Include: BlackHole 2ch
   - Master device: BlackHole 2ch
4. Set WebSDR to output to Multi-Output Device
5. In NovaSDR app:
   - Input: BlackHole 2ch
   - Output: Your headphones/speakers

#### Windows
1. Install VB-CABLE from https://vb-audio.com/Cable/
2. Restart computer
3. Set WebSDR to output to CABLE Input
4. In NovaSDR app:
   - Input: CABLE Output
   - Output: Your speakers/headphones

### Verify Installation

Test that everything works before building:

```bash
# macOS
cd audio_processor
./run_qt_gui.sh

# Windows
cd audio_processor
call venv\Scripts\activate.bat
python novasdr_gui_qt.py
```

---

## Build Configuration

### Key Build Parameters

Both platforms use these PyInstaller settings:

- **`--windowed`**: No console window
- **`--onedir`**: Directory mode (not single file)
  - Better for native libraries (.so, .pyd)
  - Required for macOS security
  - Easier to debug
- **`--add-binary`**: Include NovaSDR Rust module
- **`--collect-all`**: Collect all sounddevice/scipy files
- **`--hidden-import`**: Explicitly import required modules

### macOS Specific

- **Info.plist**: Includes `NSMicrophoneUsageDescription` for permissions
- **Code signing**: Automatic ad-hoc signing after build
- **Bundle identifier**: `com.lu2met.novasdr`

### Windows Specific

- **`.pyd` extension**: Windows equivalent of `.so`
- **No Info.plist**: Windows handles permissions differently
- **SmartScreen**: Users may need to approve first run

---

## Troubleshooting

### Build Errors

#### "maturin: command not found"
```bash
pip install maturin
```

#### "Rust compiler not found"
- macOS: `curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`
- Windows: Download from https://rustup.rs/

#### "PyInstaller not found"
```bash
pip install pyinstaller
```

#### macOS: "xcode-select: command not found"
```bash
xcode-select --install
```

#### Windows: "Visual Studio Build Tools required"
- Install Visual Studio Build Tools with C++ support

### Runtime Errors

#### "NovaSDR module not found"
- Verify Rust module built successfully: `maturin develop --release`
- Check that .so/.pyd file is in the app bundle

#### "No audio devices found"
- macOS: Install BlackHole 2ch
- Windows: Install VB-CABLE
- Check system audio settings

#### "Can't record in MP3"
- Install FFmpeg
- App will fallback to WAV if FFmpeg unavailable

#### macOS: "App is damaged or incomplete"
```bash
xattr -cr "dist/NovaSDR Audio Processor.app"
codesign --force --deep --sign - "dist/NovaSDR Audio Processor.app"
```

#### Windows: "DLL load failed"
- Ensure all dependencies in build
- Check that .pyd file is present

### Permission Issues

#### macOS: No audio input
- Check System Settings → Privacy & Security → Microphone
- Ensure "NovaSDR Audio Processor" is allowed
- If not listed, delete app and rebuild

#### Windows: Microphone access denied
- Check Windows Settings → Privacy → Microphone
- Enable for desktop apps

---

## File Sizes

- **macOS .app**: ~150-200 MB (compressed: ~80-100 MB)
- **Windows folder**: ~150-200 MB (compressed: ~80-100 MB)

Includes:
- Python runtime
- NumPy, SciPy libraries
- PyQt5 framework
- NovaSDR Rust module
- All dependencies

---

## Development vs Production

### Development (Run from Source)

**macOS:**
```bash
cd audio_processor
./run_qt_gui.sh
```

**Windows:**
```cmd
cd audio_processor
call venv\Scripts\activate.bat
python novasdr_gui_qt.py
```

**Advantages:**
- Faster iteration
- Easier debugging
- See all print statements

### Production (Standalone App)

**Advantages:**
- No Python installation required
- Professional appearance
- Easy distribution
- Includes all dependencies

**Disadvantages:**
- Larger file size
- Slower build process
- Harder to debug

---

## Continuous Integration (CI/CD)

### GitHub Actions Example

```yaml
name: Build Applications

on: [push, pull_request]

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: Build
        run: |
          cd audio_processor
          ./build_macos.sh
      - uses: actions/upload-artifact@v3
        with:
          name: NovaSDR-macOS
          path: audio_processor/dist/NovaSDR Audio Processor.app

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.14'
      - uses: actions-rs/toolchain@v1
        with:
          toolchain: stable
      - name: Build
        run: |
          cd audio_processor
          build_windows.bat
      - uses: actions/upload-artifact@v3
        with:
          name: NovaSDR-Windows
          path: audio_processor/dist/NovaSDR Audio Processor/
```

---

## Support

For build issues:
- Check this documentation
- Review error messages carefully
- Ensure all prerequisites installed
- Try building from clean environment

For runtime issues:
- Check audio device configuration
- Review application logs: `~/novasdr_debug.log`
- Verify permissions granted

---

## Additional Resources

- **PyInstaller Documentation**: https://pyinstaller.org/
- **Rust Installation**: https://www.rust-lang.org/tools/install
- **maturin Documentation**: https://www.maturin.rs/
- **BlackHole Audio**: https://github.com/ExistentialAudio/BlackHole
- **VB-CABLE**: https://vb-audio.com/Cable/

---

**73 de LU2MET!** 📻

Last updated: 2026-04-02
