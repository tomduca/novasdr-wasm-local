#!/bin/bash
# NovaSDR Audio Processor - GUI Version
# Simple graphical interface for device selection and control

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor GUI..."
python3 audio_processor_gui.py
