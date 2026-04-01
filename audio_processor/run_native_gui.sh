#!/bin/bash
# Run NovaSDR Audio Processor Web GUI
# Note: Native GUI requires PyQt5, using web interface instead

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor (Web Interface)..."
echo "Open your browser at: http://localhost:5001"
echo ""

python3 audio_processor_web.py
