# NovaSDR Audio Processor

Hybrid **Python + Rust** pipeline integrating NovaSDR Spectral Noise Reduction filter for HF audio processing on macOS.

## ✅ Final Solution

- **Noise reduction:** Nearly identical to original NovaSDR web
- **Latency:** ~43ms (ultra low)
- **Volume:** Optimal with automatic compensation
- **Quality:** Excellent, no artifacts
- **Recording:** Save processed audio as MP3 or WAV

## 🚀 Quick Start

**First time setup:** See **[INSTALL.md](INSTALL.md)** for installation instructions.

### Native GUI (PyQt5 - Recommended)
```bash
cd audio_processor
./run_qt_gui.sh
```

### Web GUI (Browser-based)
```bash
cd audio_processor
./run_web.sh
# Open http://localhost:5001
```

See **[GUI_OPTIONS.md](GUI_OPTIONS.md)** for detailed comparison and instructions.

### Command Line Version
```bash
cd audio_processor
./run_ultra.sh
```

## Architecture

```
WebSDR → Multi-Output Device → BlackHole 2ch
              ↓
    Python (sounddevice I/O)
              ↓
    Rust (NovaSDR Filter)
              ↓
    Post-Gain Compensation
              ↓
    Jabra / Speakers
```

## Features

### Graphical Interface
- ✅ Device selection (input/output)
- ✅ Preset selection (Moderate, Aggressive, Ultra, Extreme)
- ✅ Bypass toggle (pass-through mode)
- ✅ Real-time log output
- ✅ Start/Stop control
- ✅ Audio recording (MP3/WAV with timestamp)

### Command Line Presets

- **`./run_ultra.sh`** ⭐ - Maximum reduction (RECOMMENDED)
- **`./run_aggressive.sh`** - Strong reduction
- **`./run_moderate.sh`** - Moderate reduction

## Audio Configuration

### Requirements

1. **Virtual audio capture device** (one of these):
   - BlackHole (free)
   - Loopback (paid)
   - Soundflower
   - Other virtual audio software

2. **Multi-Output Device** (Audio MIDI Setup):
   - Include ONLY the virtual capture device
   - DO NOT include headphones/speakers (prevents echo)

3. **System Settings → Sound → Output:**
   - Select "Multi-Output Device"

### Identify Device Indices

Run the script to see devices:
```bash
cd audio_processor
./run_ultra.sh
```

Look for:
- **Input:** Virtual capture device (with input channels)
- **Output:** Headphones/speakers (with output channels)

Note the numeric indices and configure in the scripts.

## 📦 Standalone Applications

Build standalone desktop applications (no Python required):

- **macOS:** `cd audio_processor && ./build_macos.sh` → Creates `.app` bundle
- **Windows:** `cd audio_processor && build_windows.bat` → Creates `.exe` file

See **[STANDALONE_APP_GUIDE.md](STANDALONE_APP_GUIDE.md)** for complete instructions.

## Documentation

- **`GUI_OPTIONS.md`** - Compare Native vs Web GUI options
- **`STANDALONE_APP_GUIDE.md`** - Build standalone apps for macOS/Windows
- **`audio_processor/USAGE.md`** - Complete usage guide
- **`SOLUTION_SUMMARY.md`** - Technical project summary

## Components

### Rust Module (`novasdr_nr_py/`)
- NovaSDR Spectral Noise Reduction filter
- Compiled with PyO3 for Python
- Performance: ~0.1-0.2ms per block

### Python Processor (`audio_processor/`)
- Audio I/O with sounddevice
- Integration with Rust module
- Automatic volume compensation

## Technologies

- **Python:** sounddevice, numpy, scipy
- **Rust:** PyO3, rustfft
- **DSP:** NovaSDR Spectral NR (MMSE)

## Results

✅ **Pipeline working**  
✅ **Quality equal to NovaSDR web**  
✅ **Latency ~43ms**  
✅ **Optimal volume**  

---
For maximum audio quality:

1. **Increase buffer_size**: 4096 or 8192 samples
2. **Adjust nr_alpha**: Higher values (0.97-0.99) for more aggressive smoothing
3. **Enable all stages**: Spectral NR + Noise Blanker + Auto Notch
4. **High sample rate**: Use 48kHz or 96kHz if possible

Recommended configuration for maximum quality:

```toml
[dsp]
buffer_size = 4096
spectral_nr_enabled = true
nr_gain = 0.001
nr_alpha = 0.98
nr_asnr = 35.0
noise_blanker_enabled = true
nb_threshold = 0.9
autonotch_enabled = true
```

## Troubleshooting

### Audio device not detected

- Verify the device is configured in Audio MIDI Setup
- Use `--list-devices` to see exact names
- Name may contain spaces, use quotes

### Choppy or glitchy audio

- Increase `buffer_size` in config.toml
- Verify no other processes are consuming too much CPU
- Reduce the number of enabled filters

### Too much noise reduction ("metallic" audio)

- Increase `nr_gain` (less aggressive)
- Reduce `nr_alpha` (less smoothing)
- Adjust `nr_asnr` according to actual SNR conditions

## License

Based on [novasdr-wasm](https://github.com/Steven9101/novasdr-wasm) which uses multiple licenses (GPL-3.0, Apache-2.0, MIT).

This project maintains compatibility with those licenses.
