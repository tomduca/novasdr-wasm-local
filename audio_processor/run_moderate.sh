#!/bin/bash
# NovaSDR Preset: MODERATE (moderate reduction)
# Gain: 1/1024, Alpha: 0.98, ASNR: 20 dB

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor - MODERATE preset"
echo "Audio Flow: WebSDR → Multi-Output → BlackHole (5) → Jabra (2)"
echo ""

python3 audio_processor_novasdr_tunable.py --preset moderate --input 5 --output 2
