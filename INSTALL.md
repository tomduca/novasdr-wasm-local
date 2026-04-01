# Installation Guide

## Prerequisites

- **macOS** (tested on macOS 13+)
- **Python 3.8+** (Python 3.14 recommended)
- **Rust** (latest stable)
- **Virtual audio device** (BlackHole, Loopback, or similar)

## Step 1: Install System Dependencies

### Install Rust

```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env
```

### Install BlackHole (Virtual Audio Device)

```bash
brew install blackhole-2ch
```

Or download from: https://existential.audio/blackhole/

## Step 2: Build Rust Module

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/novasdr_nr_py

# Install maturin (PyO3 build tool)
pip3 install maturin

# Build the Rust module
maturin develop --release
```

This compiles the NovaSDR filter and makes it available to Python.

## Step 3: Setup Python Environment

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/audio_processor

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install sounddevice numpy scipy

# Verify installation
python3 -c "import sounddevice; import novasdr_nr_py; print('✓ All dependencies installed')"
```

## Step 4: Configure Audio Devices

### Create Multi-Output Device

1. Open **Audio MIDI Setup** (`/Applications/Utilities/Audio MIDI Setup.app`)
2. Click **"+"** → **"Create Multi-Output Device"**
3. Check **ONLY** your virtual audio device (e.g., BlackHole 2ch)
4. **DO NOT** check your output device (headphones/speakers) - this prevents echo

### Set System Output

1. Open **System Settings** → **Sound** → **Output**
2. Select **"Multi-Output Device"**

### Identify Device Indices

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/audio_processor
source venv/bin/activate
python3 audio_processor_novasdr_tunable.py --list-devices
```

Note the indices for:
- **Input:** Your virtual audio device (e.g., BlackHole 2ch)
- **Output:** Your headphones/speakers

### Update Scripts

Edit the run scripts (`run_ultra.sh`, etc.) with your device indices:

```bash
# Example: if BlackHole is index 5 and headphones are index 2
python3 audio_processor_novasdr_tunable.py --preset ultra --input 5 --output 2
```

## Step 5: Test

```bash
cd /Users/tomasduca/CascadeProjects/nr_filter/audio_processor
./run_ultra.sh
```

You should see:
```
✓ NovaSDR Rust module loaded successfully
✓ NovaSDR initialized: gain=0.000122, alpha=0.99, asnr=2.0
```

Open a WebSDR in your browser and you should hear processed audio through your headphones.

## Troubleshooting

### "ModuleNotFoundError: No module named 'novasdr_nr_py'"

The Rust module wasn't built. Run:
```bash
cd novasdr_nr_py
maturin develop --release
```

### "No module named 'sounddevice'"

Virtual environment not activated or dependencies not installed:
```bash
cd audio_processor
source venv/bin/activate
pip install sounddevice numpy scipy
```

### "Invalid number of channels"

Wrong device index. List devices and update scripts:
```bash
python3 audio_processor_novasdr_tunable.py --list-devices
```

### No audio output

1. Verify browser is outputting to Multi-Output Device
2. Verify Multi-Output Device includes virtual audio device
3. Verify device indices in scripts are correct
4. Check volume is not muted

## Quick Setup (All Commands)

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Install BlackHole
brew install blackhole-2ch

# Build Rust module
cd /Users/tomasduca/CascadeProjects/nr_filter/novasdr_nr_py
pip3 install maturin
maturin develop --release

# Setup Python environment
cd ../audio_processor
python3 -m venv venv
source venv/bin/activate
pip install sounddevice numpy scipy

# Test
./run_ultra.sh
```

## Next Steps

- See **`USAGE.md`** for usage instructions
- See **`README.md`** for project overview
- See **`SOLUTION_SUMMARY.md`** for technical details

---

**73 de LU2MET** 📻
