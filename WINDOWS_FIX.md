# Windows Build - NovaSDR Module Not Processing

## Problem

The Windows compiled `.exe` has audio but doesn't apply NovaSDR filtering, regardless of preset or bypass settings.

## Root Cause

The NovaSDR Rust module (`.pyd` file) is being included in the build but may not be properly initialized or the module path is not correct in the PyInstaller bundle.

## Solution

### 1. Update Build Script

Add `--collect-all=novasdr_nr` to ensure all module files are collected:

```bat
--collect-all=sounddevice ^
--collect-all=scipy ^
--collect-all=novasdr_nr ^
```

### 2. Verify Module Loading

After rebuilding, check the debug log file:

**Windows log location:** `C:\Users\YourUsername\novasdr_debug.log`

Look for these lines:
```
✓ NovaSDR module loaded from: [path]
✓ NovaSDR filter initialized: [preset] mode [mode]
Audio callback: PROCESSING mode (input level: X, output level: Y)
```

If you see:
- `✗ NovaSDR module not available` - Module not loading
- `Audio callback: BYPASS mode` - Module loaded but not being used

### 3. Manual Verification

Check if the `.pyd` file is in the build:

```cmd
cd "dist\NovaSDR Audio Processor"
dir /s *.pyd
```

You should see `novasdr_nr.cp3XX-win_amd64.pyd` (where XX is your Python version)

### 4. Rebuild Steps

```cmd
cd audio_processor
call venv\Scripts\activate.bat
build_windows.bat
```

### 5. Test After Rebuild

1. Run the new `.exe`
2. Select audio devices
3. Choose a preset (e.g., "Extreme")
4. Start processing
5. Check the log file for "PROCESSING mode"
6. Verify audio is actually filtered (should sound different from bypass)

### 6. If Still Not Working

Check the log file and look for:

**Module not loading:**
```
✗ NovaSDR module not available: [error message]
```
→ The `.pyd` file is missing or incompatible

**Module loads but bypass mode:**
```
✓ NovaSDR module loaded
Audio callback: BYPASS mode
```
→ The module is available but `self.novasdr_nr` is None

**Module loads and processes but no effect:**
```
✓ NovaSDR module loaded
Audio callback: PROCESSING mode (input level: 0.5, output level: 0.5)
```
→ Module is working, but input/output levels are the same - check if filter is actually being applied

### 7. Alternative: Manual Module Copy

If `--collect-all` doesn't work, manually copy the module after build:

```cmd
REM After build completes
copy "%NOVASDR_MODULE%\novasdr_nr*.pyd" "dist\NovaSDR Audio Processor\"
```

Add this to the end of `build_windows.bat`:

```bat
echo.
echo Copying NovaSDR module manually...
copy "%NOVASDR_MODULE%\novasdr_nr*.pyd" "dist\NovaSDR Audio Processor\"
```

## Expected Behavior

When working correctly:

1. **Log shows:**
   ```
   ✓ NovaSDR module loaded from: [path]
   ✓ NovaSDR filter initialized: extreme mode SSB
   Audio callback: PROCESSING mode (input level: 0.4523, output level: 0.2156)
   ```

2. **Audio changes:**
   - With bypass OFF: Noise reduction applied, cleaner audio
   - With bypass ON: Raw audio, no processing
   - Different presets: Noticeable difference in aggressiveness

3. **No errors in log**

## Debugging Commands

**Check if module is in the right place:**
```cmd
cd "dist\NovaSDR Audio Processor"
dir novasdr_nr*.pyd
```

**Check log file:**
```cmd
type %USERPROFILE%\novasdr_debug.log
```

**Run from command line to see errors:**
```cmd
cd "dist\NovaSDR Audio Processor"
"NovaSDR Audio Processor.exe"
```

## Notes

- Windows uses `.pyd` extension (not `.so` like macOS)
- The module must match your Python version (e.g., `cp314` for Python 3.14)
- PyInstaller on Windows sometimes needs `--collect-all` for native modules
- The debug log file is created in the user's home directory

---

**Last updated:** 2026-04-03
