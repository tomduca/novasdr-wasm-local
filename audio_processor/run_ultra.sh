#!/bin/bash
# NovaSDR Preset: ULTRA (maximum reduction with volume compensation)
# Gain: 1/8192, Alpha: 0.99, ASNR: 2 dB, Post-Gain: 10.0x

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor - ULTRA preset"
echo "Audio Flow: WebSDR → Multi-Output → BlackHole (5) → Output Device (2)"
echo ""
echo "ULTRA mode: Maximum noise reduction with volume compensation"
echo ""

python3 audio_processor_novasdr_tunable.py --preset ultra --input 5 --output 2
