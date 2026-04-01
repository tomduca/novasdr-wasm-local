# NovaSDR Audio Processor - Usage Guide

## ✅ Final Solution

Hybrid **Python + Rust** pipeline integrating NovaSDR Spectral Noise Reduction filter.

## 🚀 Quick Start

### Recommended Preset: ULTRA ⭐

```bash
./run_ultra.sh
```

**Features:**
- Noise reduction nearly identical to original SDR Nova
- Optimal volume (automatic +20 dB compensation)
- Ultra low latency (~43ms)
- Excellent audio quality

## Available Scripts

### 1. Ultra (Recommended) ⭐
```bash
./run_ultra.sh
```
- **Reduction:** Maximum (nearly identical to NovaSDR web)
- **Volume:** Optimal (post-gain 10.0x)
- **Use:** General use, maximum quality

### 2. Aggressive
```bash
./run_aggressive.sh
```
- **Reduction:** Strong
- **Volume:** Good (post-gain 2.5x)
- **Use:** Alternative if Ultra is too aggressive

### 3. Moderate
```bash
./run_moderate.sh
```
- **Reduction:** Moderate
- **Volume:** Normal (post-gain 1.5x)
- **Use:** Clean audio, less processing

## Audio Configuration

### Step 1: Identify Devices

Run the script to list available devices:

```bash
./run_ultra.sh
```

Look for in the output:
- **Virtual capture device** (e.g.: BlackHole, Loopback, etc.)
  - Must have input channels (X in, Y out where X > 0)
  - Note the **numeric index** (e.g.: 5)
  
- **Output device** (headphones/speakers)
  - Must have output channels (0 in, Y out where Y > 0)
  - Note the **numeric index** (e.g.: 2)

### Step 2: Configure Multi-Output Device

1. **Open Audio MIDI Setup**
   ```
   /Applications/Utilities/Audio MIDI Setup.app
   ```

2. **Create/Edit Multi-Output Device**
   - Click "+" → "Create Multi-Output Device"
   - Check **ONLY** your virtual capture device
   - DO NOT check headphones/speakers (to prevent echo)

3. **Configure system output**
   - System Settings → Sound → Output
   - Select "Multi-Output Device"

### Step 3: Configure Scripts

Edit the script you use (e.g.: `run_ultra.sh`) and adjust the indices:

```bash
python3 audio_processor_novasdr_tunable.py --preset ultra --input <CAPTURE_INDEX> --output <OUTPUT_INDEX>
```

Example:
```bash
python3 audio_processor_novasdr_tunable.py --preset ultra --input 5 --output 2
```

### Audio Flow

```
WebSDR (Safari)
    ↓
Multi-Output Device (macOS output)
    ↓
Virtual Capture Device (e.g.: BlackHole)
    ↓
Python Input (index you noted)
    ↓
NovaSDR Spectral NR (RUST)
    ↓
Post-Gain (volume compensation)
    ↓
Python Output (index you noted)
    ↓
Headphones / Speakers
```

## Preset Parameters

| Preset | Gain | Alpha | ASNR | Post-Gain | Reduction |
|--------|------|-------|------|-----------|-----------|
| Moderate | 1/1024 | 0.98 | 20 dB | 1.5x | ⭐⭐⭐ |
| Aggressive | 1/2048 | 0.98 | 10 dB | 2.5x | ⭐⭐⭐⭐ |
| Ultra | 1/8192 | 0.99 | 2 dB | 10.0x | ⭐⭐⭐⭐⭐ |

## Performance

- **Total latency:** ~43ms
- **Processing:** ~0.1-0.2ms per block
- **CPU:** Very low (Rust optimized)
- **Quality:** Equal to original NovaSDR web

## Recording Audio

The web interface includes audio recording functionality to save processed audio.

### How to Record

1. **Start audio processing** (click ▶ Start button)
2. **Click "🔴 Start Recording"** when ready
3. **Listen and record** your desired content
4. **Click "⏹️ Stop Recording"** when done

### Recording Details

- **Format:** MP3 (128kbps) or WAV (fallback)
- **Filename:** `recording_YYYYMMDD_HHMMSS.mp3`
- **Location:** `audio_processor/recordings/`
- **Audio:** Processed output (with NovaSDR filter applied)

### Requirements for MP3

MP3 recording requires `ffmpeg`:

```bash
brew install ffmpeg
```

If `ffmpeg` is not installed, recordings will automatically save as WAV format.

### Example Filenames

```
recording_20260331_233045.mp3
recording_20260331_234120.mp3
recording_20260401_081530.mp3
```

## Troubleshooting

### No audio output

**Verify:**
1. ✅ Browser is using Multi-Output Device as output
2. ✅ Processor is running without errors
3. ✅ Volume is not muted
4. ✅ Device indices are correct (verify with --list-devices)
5. ✅ Virtual capture device is included in Multi-Output Device

### Echo / Duplicated audio
- Uncheck output device from Multi-Output Device
- Only virtual capture device should be checked

### Low volume
- Use Ultra preset (post-gain 10.0x)
- Or adjust manually with `--post-gain`

### Too many artifacts
- Use Aggressive or Moderate preset
- Ultra is very aggressive for clean signals

## Manual Adjustments (Advanced)

If you want to adjust parameters manually:

```bash
source venv/bin/activate
python3 audio_processor_novasdr_tunable.py \
    --gain 0.000122 \
    --alpha 0.99 \
    --asnr 2.0 \
    --post-gain 10.0 \
    --input 5 \
    --output 2
```

## Project Files

### Essential
- `run_ultra.sh` - Main script (RECOMMENDED)
- `run_aggressive.sh` - Less aggressive alternative
- `run_moderate.sh` - Soft alternative
- `audio_processor_novasdr_tunable.py` - Python processor
- `venv/` - Virtualenv with dependencies

### Rust Module
- `../novasdr_nr_py/` - Compiled PyO3 module
- `../novasdr_nr_py/src/spectralnoisereduction.rs` - NovaSDR filter

## Technologies

- **Python:** sounddevice, numpy, scipy
- **Rust:** PyO3, rustfft
- **DSP:** NovaSDR Spectral Noise Reduction (MMSE)

## Summary

✅ **Pipeline working:** Python I/O + Rust DSP  
✅ **Quality:** Equal to original NovaSDR web  
✅ **Latency:** ~43ms (excellent)  
✅ **Volume:** Optimal with automatic compensation  
✅ **Recommended preset:** `./run_ultra.sh`  

**Ready to use with WebSDR!**
