#!/bin/bash
# NovaSDR Preset: AGGRESSIVE (strong reduction with volume compensation)
# Gain: 1/2048, Alpha: 0.98, ASNR: 10 dB, Post-Gain: 2.5x

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor - AGGRESSIVE preset"
echo "Audio Flow: WebSDR → Multi-Output → BlackHole (5) → Output Device (2)"
echo ""
echo "AGGRESSIVE mode: Strong noise reduction"
echo ""

python3 audio_processor_novasdr_tunable.py --preset aggressive --input 5 --output 2
