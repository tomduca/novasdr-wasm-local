# TODO: Packaging Issues

## Current Status

### ✅ Working
- Native PyQt5 GUI runs perfectly from source (`./run_qt_gui.sh`)
- All features work: SSB/CW modes, presets, recording, bypass
- NovaSDR Rust module loads and processes audio correctly
- Web interface also works perfectly

### ❌ Not Working
- Compiled `.app` bundle shows interface but **no audio processing**
- NovaSDR Rust module (.so file) not loading in PyInstaller bundle

## Problem

PyInstaller onefile mode is not properly including or loading the NovaSDR Rust module (`novasdr_nr.so`).

The app shows the interface and all controls work, but when you start processing:
- Audio passes through without noise reduction
- NovaSDR module appears to not be available

## Attempted Fixes

1. **Added explicit binary inclusion:**
   ```bash
   --add-binary="$NOVASDR_MODULE/novasdr_nr*.so:."
   ```

2. **Added all hidden imports:**
   ```bash
   --hidden-import=numpy.core._multiarray_umath
   --hidden-import=scipy.signal
   --hidden-import=scipy.fft
   --hidden-import=sounddevice
   --hidden-import=_sounddevice
   ```

3. **Collected all dependencies:**
   ```bash
   --collect-all=sounddevice
   --collect-all=scipy
   ```

4. **Added diagnostic logging** to see where module loading fails

## Next Steps to Try

### Option 1: Use onedir mode (RECOMMENDED)
PyInstaller shows this warning:
```
DEPRECATION: Onefile mode in combination with macOS .app bundles (windowed mode) 
don't make sense and clashes with macOS's security. Please migrate to onedir mode.
```

**Action:**
```bash
# In build_macos.sh, change:
--onefile  # Remove this
--onedir   # Add this instead
```

This creates a directory with all files instead of a single executable, which is better for macOS .app bundles.

### Option 2: Manual .so copy
After PyInstaller build, manually copy the .so file:

```bash
# Find the .so location
NOVASDR_SO=$(find venv -name "novasdr_nr*.so")

# Copy to app bundle
cp "$NOVASDR_SO" "dist/NovaSDR Audio Processor.app/Contents/MacOS/"
```

### Option 3: Use PyInstaller spec file
Create a custom `.spec` file for more control over what gets included.

### Option 4: Check architecture
Verify the .so file architecture matches:
```bash
file venv/lib/python3.14/site-packages/novasdr_nr/novasdr_nr*.so
lipo -info venv/lib/python3.14/site-packages/novasdr_nr/novasdr_nr*.so
```

May need to compile for both x86_64 and arm64 (universal binary).

### Option 5: Alternative packaging
Consider using:
- **py2app** (macOS specific, might handle .so files better)
- **briefcase** (cross-platform, BeeWare project)
- **cx_Freeze** (alternative to PyInstaller)

## Diagnostic Commands

Run compiled app from terminal to see errors:
```bash
cd audio_processor
./dist/NovaSDR\ Audio\ Processor.app/Contents/MacOS/NovaSDR\ Audio\ Processor
```

Check what's inside the bundle:
```bash
ls -la "dist/NovaSDR Audio Processor.app/Contents/MacOS/"
find "dist/NovaSDR Audio Processor.app" -name "*.so"
```

## Workaround for Now

Users can run the app from source:
```bash
cd audio_processor
./run_qt_gui.sh
```

This works perfectly and doesn't require compilation.

## References

- PyInstaller docs: https://pyinstaller.org/
- PyInstaller + Rust: https://github.com/PyO3/pyo3/issues/1800
- macOS app bundles: https://developer.apple.com/library/archive/documentation/CoreFoundation/Conceptual/CFBundles/

---

**Last updated:** 2026-04-01
**Status:** In progress - to be resolved tomorrow
