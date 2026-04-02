# Building NovaSDR Audio Processor for Windows

## Prerequisites

### On Windows Machine

1. **Python 3.10 or higher**
   - Download from: https://www.python.org/downloads/
   - During installation, check "Add Python to PATH"

2. **Git** (to clone the repository)
   - Download from: https://git-scm.com/download/win

3. **Rust** (to compile the NovaSDR module)
   - Download from: https://rustup.rs/
   - Run the installer and follow the prompts

4. **Visual Studio Build Tools** (required for Rust)
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++"

5. **FFmpeg** (optional, for MP3 recording)
   - Download from: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add to PATH

## Build Steps

### 1. Clone the Repository

```cmd
git clone https://github.com/tomduca/novasdr-audio-processor.git
cd novasdr-audio-processor
```

### 2. Build the Rust NovaSDR Module

```cmd
cd novasdr_nr_py
pip install maturin
maturin develop --release
cd ..
```

### 3. Set Up Python Virtual Environment

```cmd
cd audio_processor
python -m venv venv
call venv\Scripts\activate.bat
```

### 4. Install Python Dependencies

```cmd
pip install numpy scipy sounddevice PyQt5 pydub pyinstaller
```

### 5. Build the Windows Application

```cmd
build_windows.bat
```

This will create:
```
dist\NovaSDR Audio Processor\
  ├── NovaSDR Audio Processor.exe
  ├── novasdr_nr.pyd (Rust module)
  ├── recordings\ (folder for recordings)
  └── ... (all dependencies)
```

## Distribution

### Option 1: Distribute the Folder

1. Compress the entire `dist\NovaSDR Audio Processor` folder to a .zip file
2. Users extract and run `NovaSDR Audio Processor.exe`

### Option 2: Create an Installer (Optional)

Use **Inno Setup** to create a professional installer:

1. Download Inno Setup: https://jrsoftware.org/isdl.php
2. Create a script to package the application
3. Build the installer

## Running the Application

**From the build directory:**
```cmd
dist\NovaSDR Audio Processor\NovaSDR Audio Processor.exe
```

**After distribution:**
- Users simply double-click `NovaSDR Audio Processor.exe`
- No Python installation required
- All dependencies included

## Audio Device Setup on Windows

### Virtual Audio Cable

1. **Install VB-CABLE** (free virtual audio device)
   - Download from: https://vb-audio.com/Cable/
   - Install and restart

2. **Configure Audio Routing**
   - Set WebSDR output to VB-CABLE Input
   - In NovaSDR app, select:
     - Input: CABLE Output
     - Output: Your speakers/headphones

### Alternative: VoiceMeeter

VoiceMeeter provides more advanced routing options:
- Download from: https://vb-audio.com/Voicemeeter/

## Troubleshooting

### Build Errors

**"maturin: command not found"**
```cmd
pip install maturin
```

**"Rust compiler not found"**
- Install Rust from https://rustup.rs/
- Restart terminal after installation

**"Visual Studio Build Tools required"**
- Install Visual Studio Build Tools with C++ support

### Runtime Errors

**"DLL load failed"**
- Ensure all dependencies are included in the build
- Check that the Rust module (.pyd) is in the same directory

**"No audio devices found"**
- Install virtual audio cable (VB-CABLE)
- Check Windows audio settings

**"Can't record in MP3"**
- Install FFmpeg and add to PATH
- App will fallback to WAV if FFmpeg not available

## File Size

Expected application size: ~150-200 MB (includes all dependencies)

## Antivirus False Positives

Some antivirus software may flag PyInstaller executables as suspicious. This is a known issue with PyInstaller.

**Solutions:**
1. Add exception in antivirus software
2. Code sign the executable (requires certificate)
3. Submit to antivirus vendors for whitelisting

## Code Signing (Optional)

For professional distribution, consider code signing:

1. Purchase a code signing certificate
2. Use `signtool.exe` to sign the executable:
   ```cmd
   signtool sign /f certificate.pfx /p password "NovaSDR Audio Processor.exe"
   ```

## Notes

- **Windows Defender SmartScreen** may show a warning on first run
  - Users need to click "More info" → "Run anyway"
  - This is normal for unsigned applications

- **Microphone Permissions**: Windows will automatically request microphone permissions when the app tries to access audio devices

- **Compatibility**: Tested on Windows 10 and Windows 11

## Support

For issues specific to Windows builds, check:
- PyInstaller documentation: https://pyinstaller.org/
- Rust Windows setup: https://www.rust-lang.org/tools/install

---

**73 de LU2MET!** 📻
