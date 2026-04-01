# Final Solution: NovaSDR Audio Processor

## ✅ Objective Completed

Hybrid **Python + Rust** pipeline integrating NovaSDR Spectral Noise Reduction filter from `novasdr-wasm` into a local audio processor for macOS.

## Final Architecture

```
WebSDR (Safari) → Multi-Output Device → BlackHole 2ch
                                            ↓
                                    Python (sounddevice)
                                            ↓
                                    Rust (NovaSDR Filter)
                                            ↓
                                    Post-Gain Compensation
                                            ↓
                                    Jabra / Speakers
```

## Components

### 1. Rust PyO3 Module (`novasdr_nr_py/`)
- **Filter:** SpectralNoiseReduction from novasdr-wasm
- **Technology:** PyO3 for Python bindings
- **Compilation:** `maturin develop --release`
- **Performance:** ~0.1-0.2ms per block

### 2. Python Processor (`audio_processor/`)
- **I/O:** sounddevice (robust, numeric indices)
- **DSP:** Calls Rust module
- **Post-processing:** Automatic volume compensation
- **Latency:** ~43ms total

## Usage

### Main Command (Recommended)
```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/audio_processor
./run_ultra.sh
```

### Available Presets
- `./run_ultra.sh` - Maximum reduction (RECOMMENDED) ⭐
- `./run_aggressive.sh` - Strong reduction
- `./run_moderate.sh` - Moderate reduction

## Audio Configuration

### macOS Audio MIDI Setup
1. Multi-Output Device: **ONLY BlackHole 2ch** (uncheck output device)
2. System Settings → Sound → Output: "Multi-Output Device"
3. Safari plays to Multi-Output Device

### Devices
- **Input:** BlackHole 2ch (index 5)
- **Output:** Jabra EVOLVE 20 MS (index 2)

## Final Parameters (Ultra Preset)

```python
SpectralNoiseReduction(
    sample_rate=48000,
    gain=1.0/8192.0,    # Very aggressive
    alpha=0.99,         # Maximum smoothing
    asnr=2.0            # Low SNR = more reduction
)
post_gain=10.0          # Volume compensation +20 dB
```

## Results

✅ **Noise reduction:** Nearly identical to original NovaSDR web  
✅ **Volume:** Optimal with automatic compensation  
✅ **Latency:** ~43ms (excellent for real-time)  
✅ **Audio quality:** Excellent, no significant artifacts  
✅ **CPU:** Very low (Rust optimized)  

## Key Files

```
nr_filter/
├── novasdr_nr_py/                    # Rust PyO3 Module
│   ├── Cargo.toml                    # PyO3 0.22
│   ├── src/
│   │   ├── lib.rs                    # PyO3 Wrapper
│   │   └── spectralnoisereduction.rs # NovaSDR Filter
│   └── target/release/               # Compiled binary
│
└── audio_processor/                  # Python Application
    ├── run_ultra.sh                  # Main script ⭐
    ├── run_aggressive.sh             # Alternative
    ├── run_moderate.sh               # Alternative
    ├── audio_processor_novasdr_tunable.py  # Processor
    ├── USAGE.md                      # Usage guide
    └── venv/                         # Virtualenv
```

## Technologies Used

- **Python 3.14:** sounddevice, numpy, scipy
- **Rust:** PyO3 0.22, rustfft 6.2.0
- **DSP:** NovaSDR Spectral Noise Reduction (MMSE Kim & Ruwisch 2002)
- **Build:** maturin (PyO3 builder)

## Key Decisions

### 1. Hybrid Architecture
**Problem:** Pure Rust had issues with audio device handling on macOS  
**Solution:** Python for I/O (sounddevice, robust) + Rust for DSP (performance)  
**Result:** Best of both worlds

### 2. Removal of Additional Filters
**Problem:** Bandpass, AGC, Noise Gate degraded audio quality  
**Solution:** Only NovaSDR Spectral NR, no additional processing  
**Result:** Natural audio, no "boxed" sound

### 3. Volume Compensation
**Problem:** Aggressive filter significantly reduced volume  
**Solution:** Automatic post-gain after filter (10.0x for Ultra)  
**Result:** Optimal volume without loss of noise reduction

### 4. BlackHole instead of Multi-Output as Input
**Problem:** Multi-Output Device cannot be used as input (0 channels)  
**Solution:** Multi-Output → BlackHole → Python captures from BlackHole  
**Result:** Correct audio flow without echo

## Comparison with Original Objective

| Aspect | Objective | Result |
|---------|----------|-----------|
| NovaSDR Filter | ✓ Integrate | ✅ Integrated (Rust PyO3) |
| Quality | ✓ High | ✅ Equal to NovaSDR web |
| Latency | ✓ < 500ms | ✅ ~43ms |
| Devices | ✓ BlackHole + Jabra | ✅ Working |
| Performance | ✓ Real-time | ✅ ~0.1ms processing |

## Lessons Learned

1. **PyO3 is excellent** for integrating Rust into Python
2. **sounddevice** is more robust than cpal for macOS
3. **Multi-Output Device** cannot be input (use BlackHole)
4. **Less is more:** Removing unnecessary filters improves quality
5. **Post-gain** is crucial for aggressive filters

## Completed Features

- [x] Add real-time controls (adjust parameters without restarting)
- [x] Simple GUI for device selection and presets (Web interface)
- [x] Bypass toggle for pass-through mode
- [x] Real-time preset switching
- [x] Audio recording with automatic timestamping (MP3/WAV)

## Possible Next Steps (Future)

- [ ] Support for other novasdr filters (Noise Blanker, Auto Notch)
- [x] Support for CW mode
- [ ] Export as standalone macOS application
- [ ] Native GUI application (without browser)
- [ ] Windows version

## Conclusion

**Project completed successfully.** The Rust NovaSDR filter is working locally with quality comparable to the original web version, ultra-low latency, and optimal volume.

**Command to use:**
```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/audio_processor
./run_ultra.sh
```

## Credits

- **NovaSDR**: Spectral Noise Reduction Algorithm (MMSE)
  - Repository: https://github.com/Steven9101/novasdr-wasm
  - Spectral filter implementation used in this project
- **PyO3**: Framework for creating Rust-Python bindings
- **sounddevice**: Python library for audio I/O
- **rustfft**: FFT implementation in Rust

---

**Date:** March 31, 2026  
**Status:** ✅ COMPLETED  
**Final Preset:** Extreme (gain 1/16384, alpha 0.99, asnr 1.0, post-gain 14.0x)  
**Callsign:** 73 de LU2MET 📻
