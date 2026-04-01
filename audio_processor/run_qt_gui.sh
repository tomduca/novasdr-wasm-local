#!/bin/bash
# Run NovaSDR Audio Processor - PyQt5 Native GUI

cd "$(dirname "$0")"
source venv/bin/activate

echo "Starting NovaSDR Audio Processor (Native GUI)..."
echo ""

python3 novasdr_gui_qt.py
