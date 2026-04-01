#!/bin/bash
# NovaSDR Preset: EXTREME (extreme reduction with volume compensation)
# Gain: 1/16384, Alpha: 0.99, ASNR: 1 dB, Post-Gain: 14.0x

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor - EXTREME preset"
echo "Audio Flow: WebSDR → Multi-Output → Virtual Device → Speakers"
echo ""
echo "EXTREME mode: Extreme noise reduction with volume compensation"
echo "⚠️  Warning: May introduce artifacts on very clean signals"
echo ""

python3 audio_processor_novasdr_tunable.py --preset extreme --input 5 --output 2
